#!/usr/bin/env python3
"""Mechanical tier of the hallucination-police skill.

Deterministic, offline, no model judgment. Extracts every mechanically
checkable assertion from a target document and tests it against a supplied
evidence corpus. Emits JSONL findings plus a human-readable table.

Stdlib only. Python 3.8+.

  python3 mechanical_pass.py --target FILE --evidence DIR [--evidence F] \
      --mode document|return --out ledger.jsonl

Exit status is 0 whether or not defects are found; a non-zero status means the
pass itself could not run. "No findings" is never a claim of accuracy.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

MAX_EVIDENCE_BYTES = 64 * 1024 * 1024
MAX_TARGET_CHARS = 2 * 1024 * 1024
TEXT_EXTS = {
    ".md", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".yaml", ".yml",
    ".py", ".js", ".ts", ".sh", ".log", ".out", ".xml", ".rst", ".tex",
    ".ini", ".cfg", ".toml", ".patch", ".diff", ".html", ".htm", ".docx",
    ".pdf",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             ".mypy_cache", ".pytest_cache", "dist", "build", ".astro"}


# --------------------------------------------------------------------------
# text extraction
# --------------------------------------------------------------------------

def _strip_xml(blob):
    blob = re.sub(rb"<w:p[ >]", b"\n<w:p ", blob)
    blob = re.sub(rb"<[^>]+>", b" ", blob)
    return blob.decode("utf-8", "replace")


def read_docx(path):
    parts = []
    with zipfile.ZipFile(path) as z:
        for name in ("word/document.xml", "word/footnotes.xml",
                     "word/endnotes.xml", "word/comments.xml"):
            if name in z.namelist():
                parts.append(_strip_xml(z.read(name)))
    return "\n".join(parts)


def read_pdf(path):
    exe = shutil.which("pdftotext")
    if not exe:
        raise RuntimeError("pdftotext not installed; PDF text not extractable")
    res = subprocess.run([exe, "-layout", path, "-"], capture_output=True)
    if res.returncode != 0:
        raise RuntimeError("pdftotext failed: %s" % res.stderr[:200])
    return res.stdout.decode("utf-8", "replace")


def read_html(path):
    raw = open(path, "rb").read()
    raw = re.sub(rb"(?is)<(script|style).*?</\1>", b" ", raw)
    return _strip_xml(raw)


def read_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return read_docx(path)
    if ext == ".pdf":
        return read_pdf(path)
    if ext in (".html", ".htm"):
        return read_html(path)
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def collect_evidence(paths, target_path=None):
    """Return (blob, files_read, unreadable, excluded).

    `target_path` is excluded if it turns up in the evidence set. Auditing a
    document against itself grounds every fabricated value in it — the defects
    ground themselves and the run comes back quiet. Silently allowing that is
    worse than refusing to run.
    """
    chunks, read_ok, unreadable, excluded = [], [], [], []
    tgt = os.path.realpath(target_path) if target_path else None
    total = 0
    queue = list(paths)
    seen = set()
    while queue:
        p = os.path.abspath(os.path.expanduser(queue.pop(0)))
        if p in seen:
            continue
        seen.add(p)
        if tgt and os.path.realpath(p) == tgt:
            excluded.append(p)
            continue
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS
                           and not d.startswith(".")]
                for f in sorted(files):
                    if os.path.splitext(f)[1].lower() in TEXT_EXTS:
                        queue.append(os.path.join(root, f))
            continue
        if not os.path.isfile(p):
            unreadable.append((p, "not found"))
            continue
        if total >= MAX_EVIDENCE_BYTES:
            unreadable.append((p, "evidence size cap reached"))
            continue
        try:
            txt = read_text(p)
        except Exception as exc:                       # noqa: BLE001
            unreadable.append((p, str(exc)[:160]))
            continue
        if "\x00" in txt[:4096]:
            unreadable.append((p, "looks binary; not decoded as text"))
            continue
        total += len(txt)
        chunks.append(txt)
        read_ok.append(p)
    return "\n".join(chunks), read_ok, unreadable, excluded


# --------------------------------------------------------------------------
# normalization
# --------------------------------------------------------------------------

DASHES = dict.fromkeys(map(ord, "‐‑‒–—―"), "-")
QUOTES = {0x2018: "'", 0x2019: "'", 0x201c: '"', 0x201d: '"', 0x2032: "'",
          0x00a0: " ", 0x2026: "..."}


def norm(text):
    text = text.translate(DASHES).translate(QUOTES)
    return re.sub(r"\s+", " ", text).lower()


NUM_RE = re.compile(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)(?![\w])")


def norm_number(tok):
    tok = tok.replace(",", "")
    if "." in tok:
        tok = tok.rstrip("0").rstrip(".")
    return tok or "0"


def number_set(text):
    return {norm_number(m.group(1)) for m in NUM_RE.finditer(text)}


# --------------------------------------------------------------------------
# patterns
# --------------------------------------------------------------------------

SHA256_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])")
# Case-insensitive (DEADBEEF is a commit too), and requires BOTH a hex letter
# and a digit. All-letter runs are English words -- "defaced", "feedface" and
# "deadbeef" are seven-plus hex letters each and were being accused as commits.
GITSHA_RE = re.compile(r"(?<![0-9a-zA-Z])"
                       r"(?=[0-9a-fA-F]*[a-fA-F])(?=[0-9a-fA-F]*\d)"
                       r"[0-9a-fA-F]{7,40}(?![0-9a-zA-Z])")
# An all-letter hex run (DEADBEEF, feedface) is usually an English word, so it
# counts as an identifier only when something nearby says it is one.
GITSHA_WORDY_RE = re.compile(
    r"(?i)\b(?:commit|sha|revision|rev|hash|object|tag|at)\b[\s:=]+"
    r"`?((?![0-9a-fA-F]*\d)[0-9a-fA-F]{7,40})`?(?![0-9a-zA-Z])")
ISO_DATE_RE = re.compile(r"(?<!\d)(?:19|20)\d\d-\d{2}-\d{2}(?!\d)")
PERCENT_WORD_RE = re.compile(r"\s*(?:%|percent\b|pct\b)")
# Allows the speaker's name between the quote and the verb: the common English
# form is `"...," Alice said.`, not `"..." said`.
ATTRIB_POST_RE = re.compile(
    r"[,.]?\s*(?:[A-Z][\w.'-]*\s+){0,4}"
    r"(?:said|says|wrote|writes|noted|notes|argued|argues|"
    r"observed|observes|reported|reports|added|adds|explained|explains|"
    r"put it|concluded|concludes|told|testified)\b")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
ARXIV_RE = re.compile(r"(?i)\barxiv[:/ ]\s*(\d{4}\.\d{4,5}(?:v\d+)?)")
ISBN_RE = re.compile(r"(?i)\bisbn(?:-1[03])?:?\s*((?:\d[- ]?){9,16}[\dxX])")
URL_RE = re.compile(r"https?://[^\s<>()\[\]\"'`]+")
QUOTE_RE = re.compile(r"[\"“]([^\"“”\n]{12,600})[\"”]")

# Every branch is length-bounded. The previous author-year branch used an
# unbounded `[^)]*` inside an optional group and backtracked polynomially on
# input like "(Smith and X" repeated -- 7.7 KB took over three seconds.
CITE_MARKERS = re.compile(
    r"(https?://"
    r"|\[\^?\d{1,4}\]"
    r"|\([^)\n]{0,60}(?:19|20)\d\d[a-z]?\s*\)"
    r"|\bdoi[: ]|\barxiv[: ]"
    r"|\bfig(?:ure)?\.?\s*\d|\btable\s*\d"
    r"|\b[\w~-]{1,60}(?:[./][\w~-]{1,60}){0,8}"
    r"\.(?:md|py|json|jsonl|csv|txt|docx|pdf|ya?ml|ts|js|xml)\b"
    r"|\bexhibit\s|\bappendix\s|`[^`\n]{1,120}`)", re.I)

SELF_REPORT_RE = re.compile(
    r"(?i)\b("
    r"(?:test\s*suite|suite|tests?|checks?|assertions?)\s*(?:of\s*)?\d*\s*"
    r"(?:ok|pass(?:ed|ing)?|green|all\s+pass)"
    r"|\d+\s*(?:tests?|checks?)\s*(?:ok|pass(?:ed|ing)?|green)"
    r"|all\s+tests?\s+pass"
    r"|\b(?:i|we)\s+(?:also\s+|then\s+|already\s+|successfully\s+)?"
    r"(?:ran|executed|verified|confirmed|checked|reproduced|pushed|"
    r"landed|merged|committed|validated|benchmarked|measured|tested)\b"
    r"|\bci\s+(?:is\s+|has\s+)?(?:green|succeeded|passed)\b"
    r"|\bbuild\s+(?:stayed|is|was|remained)\s+green\b"
    r"|\b(?:pytest|the\s+suite|the\s+build|the\s+run)\s+"
    r"(?:reported\s+)?(?:succeeded|passed|reported\s+success)\b"
    r"|\bevery\s+(?:test|check|case|benchmark)\s+"
    r"(?:passed|succeeded|ran\s+clean)\b"
    r"|\b(?:hash|byte|spot)[- ]verified\b"
    r"|\bverified\s+(?:exact|identical|byte-for-byte|\d)"
    r"|\bpushed\s+(?:at|to)\b"
    r"|\bconfirmed\s+(?:exact|reproduced|identical)\b"
    r")")

OVERCLAIM_RE = re.compile(
    r"(?i)(?<![\w-])("
    r"prove[ns]?|proves|proved|guarantee[sd]?|exhaustive(?:ly)?|"
    r"saturat(?:ed|ion)|comprehensive(?:ly)?|state[- ]of[- ]the[- ]art|"
    r"world[- ]class|unprecedented|first[- ]of[- ]its[- ]kind|"
    r"the (?:world's |industry's )?first|the only|always|never fails?|"
    r"cannot fail|infallible|flawless|perfect|zero errors?|no errors?|"
    r"100(?:\.0+)?\s*%|eliminat\w*\s+\w{0,12}\s*entirely|"
    r"entirely eliminat|completely eliminat|fully verified|"
    r"definitiv(?:e|ely)|conclusiv(?:e|ely)|beyond doubt|no defects?"
    r")(?![\w-])")

PLACEHOLDER_RE = re.compile(
    r"(?i)(example\.(?:com|org|net)|localhost|127\.0\.0\.1|foo\.bar|"
    r"your-?(?:domain|org|repo)|TODO|XXX|PLACEHOLDER|\.\.\.|<[a-z-]+>)")

ATTRIB_CUE_RE = re.compile(
    r"(?i)\b(wrote|writes|written|said|says|state[sd]?|argue[sd]?|argues|"
    r"note[sd]?|notes|observe[sd]?|report(?:s|ed)?|claim(?:s|ed)?|"
    r"conclude[sd]?|according to|per\s|quote[sd]?|quoting|put it|"
    r"describe[sd]?|characteri[sz]e[sd]?|call(?:s|ed)?\s+it|"
    r"comment(?:s|ed)?|remark(?:s|ed)?|testif|reads?)\b[^.]{0,80}$")

# Wider window and intervening words allowed: "not necessarily comprehensive"
# and "do not use the word comprehensive" were both being flagged as
# overclaims, which is the careful phrasing, not the failure.
NEGATION_RE = re.compile(
    r"(?i)\b(not|never|no|nor|n't|without|avoid|far from|rather than|"
    r"instead of|non)\b[\w\s,'\"-]{0,24}$")
CMD_OUTPUT_RE = re.compile(
    r"(?m)(^\s*[$#>]\s*\S|\b\d+\s+(?:passed|failed|error|ok)\b|"
    r"\b(?:PASS|FAIL|OK)\b|\bexit(?:ed|\s+code)?\s+\d|"
    r"={3,}.{0,40}(?:passed|failed)|\btraceback\b)", re.I)

MONEY_RE = re.compile(r"[$€£¥]")
UNIT_RE = re.compile(
    r"(?i)\s*(%|percent|pp|bps|x\b|×|k\b|m\b|bn\b|"
    r"(?:milli|micro|nano|kilo|mega|giga|tera)?"
    r"(?:second|minute|hour|day|week|month|year|byte|b|kb|mb|gb|tb|"
    r"word|token|page|line|char)s?\b)")

SENT_SPLIT = re.compile(r"(?<=[.!?;:])\s+(?=[A-Z\"“(\[`])|\n")


# --------------------------------------------------------------------------
# the pass
# --------------------------------------------------------------------------

class Finding(dict):
    pass


def make(code, severity, line, span, excerpt, detail, claim_type, action):
    return Finding(code=code, severity=severity, line=line, span=span,
                   excerpt=excerpt.strip()[:300], detail=detail,
                   claim_type=claim_type, suggested_action=action)


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def _in_quotes(sent, idx):
    """True if position idx sits inside a quotation.

    A word quoted or mentioned is not the author asserting it: 'do not use the
    word "comprehensive"' was being reported as an overclaim.
    """
    return sent.count('"', 0, idx) % 2 == 1 or \
        sent.count("“", 0, idx) > sent.count("”", 0, idx)


def excerpt_at(text, idx, width=140):
    lo = max(0, idx - width // 2)
    hi = min(len(text), idx + width // 2)
    return re.sub(r"\s+", " ", text[lo:hi])


def run(target_text, ev_blob, mode, have_evidence=True):
    findings = []
    ev_norm = norm(ev_blob)
    ev_lower = ev_blob.lower()
    ev_nums = number_set(ev_blob)
    ret = (mode == "return")
    # With no evidence, a grounding check cannot fail honestly -- it would
    # accuse every value in the document. Skip those checks; run only the ones
    # that read the target alone.
    ground = have_evidence

    # Mask URLs so their digits and hex do not become claims.
    masked = list(target_text)
    url_spans = []
    for m in URL_RE.finditer(target_text):
        url_spans.append((m.start(), m.end(), m.group(0)))
        for i in range(m.start(), m.end()):
            masked[i] = "\x00"

    # An ISO date is one claim, not three. Masked whole and checked whole;
    # otherwise 2026-07-30 emits a date finding plus bare counts for 07 and 30.
    iso_hits = []
    for m in ISO_DATE_RE.finditer("".join(masked)):
        iso_hits.append((m.start(), m.group(0)))
        for i in range(m.start(), m.end()):
            masked[i] = "\x00"
    masked = "".join(masked)

    for pos, datestr in iso_hits:
        if ground and datestr not in ev_blob:
            findings.append(make(
                "UNGROUNDED_NUMBER", "medium", line_of(target_text, pos),
                [pos, pos + len(datestr)], excerpt_at(target_text, pos),
                "Date %s appears in no evidence file." % datestr,
                "date", "REPAIR"))

    # ---- identifiers -----------------------------------------------------
    id_hits = []
    consumed = [False] * len(target_text)

    def claim_span(a, b):
        for i in range(a, b):
            consumed[i] = True

    for rx, kind in ((SHA256_RE, "sha256"), (DOI_RE, "doi")):
        for m in rx.finditer(masked):
            if any(consumed[m.start():m.end()]):
                continue          # one locator, one finding
            val = m.group(0)
            if kind == "doi":     # DOI_RE swallows sentence punctuation
                val = val.rstrip(".,;:)]}'\"")
            id_hits.append((m.start(), val, kind))
            claim_span(m.start(), m.start() + len(val))
    for m in ARXIV_RE.finditer(masked):
        id_hits.append((m.start(1), m.group(1), "arxiv"))
        claim_span(m.start(), m.end())
    for m in ISBN_RE.finditer(masked):
        id_hits.append((m.start(1), m.group(1), "isbn"))
        claim_span(m.start(), m.end())
    for m in GITSHA_RE.finditer(masked):
        if any(consumed[m.start():m.end()]):
            continue
        id_hits.append((m.start(), m.group(0), "git-sha"))
        claim_span(m.start(), m.end())
    for m in GITSHA_WORDY_RE.finditer(masked):
        s, e = m.span(1)
        if any(consumed[s:e]):
            continue
        id_hits.append((s, m.group(1), "git-sha"))
        claim_span(s, e)

    prefix_map = {}
    for pos, val, kind in id_hits:
        low = val.lower()
        if ground:
            grounded = low in ev_lower
            if not grounded and kind == "git-sha":
                # A short sha is grounded when evidence carries a longer sha
                # with the same prefix. (The raw substring test above already
                # covers the equal-length case.)
                grounded = bool(re.search(
                    r"(?<![0-9a-z])" + re.escape(low) + r"[0-9a-f]+",
                    ev_lower))
            if not grounded:
                findings.append(make(
                    "UNGROUNDED_IDENTIFIER", "high",
                    line_of(target_text, pos), [pos, pos + len(val)],
                    excerpt_at(target_text, pos),
                    "%s %r appears in no evidence file. Trace it to displayed "
                    "output or treat it as fabricated. (Presence check only: "
                    "a value found beside an unrelated object still passes.)"
                    % (kind, val),
                    "identifier", "REPAIR"))
        if kind in ("sha256", "git-sha"):
            prefix_map.setdefault(low[:7], []).append((pos, low))

    # Two ids sharing a 7-char prefix conflict only when neither is a prefix of
    # the other -- "abc1234" and "abc1234def" are the same object abbreviated.
    for pre, hits in prefix_map.items():
        vals = {v for _, v in hits}
        if len(vals) < 2:
            continue
        clashing = {v for v in vals
                    if not any(w != v and w.startswith(v) for w in vals)}
        if len(clashing) < 2:
            continue
        pos = min(p for p, v in hits if v in clashing)
        findings.append(make(
            "INTERNAL_CONTRADICTION", "high", line_of(target_text, pos),
            [pos, pos + 7], excerpt_at(target_text, pos),
            "Prefix %s is bound to %d incompatible values in this document: "
            "%s. If these identify different objects the collision is "
            "coincidental; if they identify the same one, at most one is "
            "right." % (pre, len(clashing), ", ".join(sorted(clashing))),
            "identifier", "ESCALATE"))

    # ---- quotes ----------------------------------------------------------
    # Quotation marks do three jobs: attributed quotation, term-mention, and
    # scare quotes. Only the first is a claim. Attribution is what separates
    # them, so require a cue -- otherwise a document that discusses the word
    # "hallucination" gets audited for saying it.
    for m in QUOTE_RE.finditer(target_text):
        q = m.group(1)
        words = len(q.split())
        if words < 4:
            continue
        attributed = bool(
            ATTRIB_CUE_RE.search(target_text[max(0, m.start() - 140):m.start()])
            or ATTRIB_POST_RE.match(target_text[m.end():m.end() + 60]))
        if not attributed and words <= 10:
            # Term-mention or scare quotes: not a claim about a source. Leave
            # the span unconsumed so any statistic inside it is still checked.
            continue
        claim_span(m.start(), m.end())
        if not ground or norm(q) in ev_norm:
            continue
        findings.append(make(
            "QUOTE_NOT_FOUND", "high" if attributed else "medium",
            line_of(target_text, m.start()), [m.start(), m.end()], q,
            "Quoted passage of %d words is not present verbatim in the "
            "evidence.%s" % (words, "" if attributed else
                             " No attribution cue nearby - may be the "
                             "author's own phrasing in quotation marks."),
            "quote", "REPAIR" if attributed else "ESCALATE"))

    # ---- numbers ---------------------------------------------------------
    for m in NUM_RE.finditer(masked):
        s, e = m.span(1)
        if any(consumed[s:e]) or not ground:
            continue
        raw = m.group(1)
        val = norm_number(raw)
        tail = masked[e:e + 2]
        head = masked[max(0, s - 24):s]
        pct = tail.startswith("%") or tail.startswith(" %") or \
            bool(PERCENT_WORD_RE.match(masked[e:e + 10]))
        # list markers, headings, section numbers
        if re.search(r"(?:^|\n)\s*[-*#>|]*\s*$", head) and \
           re.match(r"^[.)]\s", masked[e:e + 2]):
            continue
        if not pct and len(val.replace(".", "")) < 2:
            continue
        if val in ev_nums:
            continue
        if pct:
            # Exact decimal, not "%.10f" -- that rounded 12.345678904% and
            # 0.1234567890 onto the same string, and flattened tiny values to
            # zero so any zero in evidence grounded them.
            try:
                ratio = (Decimal(val) / Decimal(100)).normalize()
                if norm_number(format(ratio, "f")) in ev_nums:
                    continue
            except (InvalidOperation, ValueError):
                pass
        year = re.fullmatch(r"(?:19|20)\d\d", val)
        measured = pct or "." in val or MONEY_RE.search(head[-3:]) or \
            UNIT_RE.match(masked[e:e + 24])
        if year:
            code, sev, ctype, act = ("UNGROUNDED_NUMBER", "medium", "date",
                                     "REPAIR")
            detail = "Date %s appears in no evidence file." % raw
        elif measured:
            code, sev, ctype, act = ("UNGROUNDED_NUMBER", "high", "statistic",
                                     "REPAIR")
            detail = ("Figure %s appears in no evidence file."
                      % (raw + ("%" if pct else "")))
        else:
            # A bare integer absent from evidence is usually a count derived
            # by counting rows, not a figure copied from a source. Verified
            # against the campaign's own accounting table: every such count
            # was correct and none appeared literally in the evidence.
            code, sev, ctype, act = ("DERIVED_OR_UNGROUNDED_COUNT", "medium",
                                     "statistic", "RECOMPUTE")
            detail = ("Count %s appears in no evidence file. Recompute it "
                      "from the evidence before trusting it; do not repair "
                      "it from memory." % raw)
        findings.append(make(code, sev, line_of(target_text, s), [s, e],
                             excerpt_at(target_text, s), detail, ctype, act))
        claim_span(s, e)

    # ---- sentence-level checks ------------------------------------------
    offset = 0
    for sent in SENT_SPLIT.split(target_text):
        start = target_text.find(sent, offset)
        if start < 0:
            start = offset
        offset = start + max(1, len(sent))
        stripped = sent.strip()
        if not stripped or stripped.startswith("|") or stripped.startswith("```"):
            continue
        ln = line_of(target_text, start)

        # A date is not an uncited statistic. Coverage labels ("as of
        # 2026-07-30") are the commonest false positive without this. Strip
        # whole ISO dates first -- otherwise 07 and 30 survive as bare counts.
        sent_nodate = ISO_DATE_RE.sub(" ", sent)
        has_number = any(
            not re.fullmatch(r"(?:19|20)\d\d", norm_number(m.group(1)))
            and len(norm_number(m.group(1)).replace(".", "")) >= 2
            for m in NUM_RE.finditer(sent_nodate))
        has_quote = any(len(m.group(1).split()) >= 4 and ATTRIB_CUE_RE.search(
            sent[:m.start()]) for m in QUOTE_RE.finditer(sent))
        cited = bool(CITE_MARKERS.search(sent))
        if (has_number or has_quote) and not cited:
            findings.append(make(
                "UNCITED_CHECKABLE_CLAIM", "medium", ln,
                [start, start + len(sent)], stripped,
                "Sentence carries a %s but names no source, locator, or file."
                % ("quotation" if has_quote else "figure"),
                "quote" if has_quote else "statistic", "RETRIEVE"))

        sr = SELF_REPORT_RE.search(sent)
        if sr:
            # Previously this never consulted the evidence, yet its message
            # asserted captured output was absent -- it accused "147 tests
            # passed" while the evidence held "147 passed in 12.03s".
            nums = {norm_number(x.group(1)) for x in NUM_RE.finditer(sent)}
            nums_ok = bool(nums) and nums <= ev_nums
            has_output = ground and bool(CMD_OUTPUT_RE.search(ev_blob))
            if nums_ok and has_output:
                findings.append(make(
                    "SELF_REPORT_UNBACKED", "low", ln,
                    [start, start + len(sent)], stripped,
                    "Claim about work performed (%r). The evidence does hold "
                    "command output and every figure here reconciles with it, "
                    "so this is a prompt to confirm the output is from THIS "
                    "run -- same command, path, and commit -- not a defect."
                    % sr.group(0).strip(),
                    "self-report", "RETRIEVE"))
            else:
                harsh = any(f["severity"] == "high" and
                            start <= f["span"][0] < start + len(sent)
                            for f in findings)
                findings.append(make(
                    "SELF_REPORT_UNBACKED",
                    "high" if (harsh or ret) else "low",
                    ln, [start, start + len(sent)], stripped,
                    "Claim about work performed (%r). %s Narration is not "
                    "evidence." % (
                        sr.group(0).strip(),
                        "No command output found in the evidence at all."
                        if not has_output else
                        "Command output is present but the figures in this "
                        "sentence do not reconcile with it."),
                    "self-report", "RETRIEVE"))

        # "not saturated" is the opposite of an overclaim. Negation flips it.
        ocs = [m.group(0) for m in OVERCLAIM_RE.finditer(sent)
               if not NEGATION_RE.search(sent[max(0, m.start() - 40):m.start()])
               and not _in_quotes(sent, m.start())]
        if ocs:
            findings.append(make(
                "OVERCLAIM", "low", ln, [start, start + len(sent)], stripped,
                "Absolute or coverage-claiming language (%s). Downgrade to "
                "what the evidence bounds."
                % ", ".join(repr(o) for o in dict.fromkeys(ocs)),
                "overclaim", "SOFTEN"))

    # ---- locators --------------------------------------------------------
    for s, e, url in url_spans:
        bad = PLACEHOLDER_RE.search(url)
        if bad:
            findings.append(make(
                "LOCATOR_SUSPECT", "high", line_of(target_text, s), [s, e],
                url, "Locator contains a placeholder or non-public host (%r)."
                % bad.group(0), "citation", "REPAIR"))
        elif re.search(r"[\s<>]|\.\.$|\)\)$", url):
            findings.append(make(
                "LOCATOR_SUSPECT", "medium", line_of(target_text, s), [s, e],
                url, "Locator is malformed or truncated.", "citation",
                "REPAIR"))

    findings.sort(key=lambda f: ({"high": 0, "medium": 1, "low": 2}[f["severity"]],
                                 f["line"]))
    for i, f in enumerate(findings, 1):
        f["finding_id"] = "M%03d" % i
    return findings


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", required=True)
    ap.add_argument("--evidence", action="append", default=[])
    ap.add_argument("--mode", choices=("document", "return"),
                    default="document")
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--allow-no-evidence", action="store_true",
                    help="run without an evidence corpus. Only the "
                         "evidence-free checks apply; every grounding check "
                         "is skipped rather than silently passing.")
    args = ap.parse_args()

    target_path = os.path.abspath(os.path.expanduser(args.target))
    try:
        target_text = read_text(target_path)
    except Exception as exc:                            # noqa: BLE001
        print("FATAL: cannot read target: %s" % exc, file=sys.stderr)
        return 2
    if "\x00" in target_text[:4096]:
        print("FATAL: target looks binary, not text. Refusing to emit "
              "findings over decoded noise.", file=sys.stderr)
        return 2
    if len(target_text) > MAX_TARGET_CHARS:
        print("FATAL: target is %d chars, over the %d cap. Split it; the "
              "sentence-level patterns are not bounded for inputs this large."
              % (len(target_text), MAX_TARGET_CHARS), file=sys.stderr)
        return 2

    # Never write over what you are auditing. --out is opened "w"; pointed at
    # the target it truncates the document before anyone reads the findings.
    if args.out:
        out_real = os.path.realpath(os.path.abspath(
            os.path.expanduser(args.out)))
        if out_real == os.path.realpath(target_path):
            print("FATAL: --out is the target file; refusing to truncate it.",
                  file=sys.stderr)
            return 2
        for ev in args.evidence:
            ev_abs = os.path.abspath(os.path.expanduser(ev))
            if os.path.isfile(ev_abs) and \
                    os.path.realpath(ev_abs) == out_real:
                print("FATAL: --out is an evidence file; refusing to "
                      "overwrite it.", file=sys.stderr)
                return 2

    ev_blob, ev_files, unreadable, excluded = collect_evidence(
        args.evidence, target_path)

    # Fail closed. A run with no usable evidence cannot ground anything, so its
    # quiet result would be indistinguishable from a clean document. That is
    # the most dangerous output this tool can produce, so it is not produced.
    if not ev_blob.strip():
        why = "no --evidence given" if not args.evidence else (
            "every evidence path was empty, unreadable, or excluded")
        print("FATAL: %s. Nothing can be grounded, so no finding would be "
              "meaningful.\n       Supply evidence, or pass "
              "--allow-no-evidence to run the evidence-free checks only "
              "(self-report, overclaim, locator shape)." % why,
              file=sys.stderr)
        for p, r in unreadable:
            print("       unreadable: %s (%s)" % (p, r), file=sys.stderr)
        for p in excluded:
            print("       excluded (same file as target): %s" % p,
                  file=sys.stderr)
        if not args.allow_no_evidence:
            return 3

    findings = run(target_text, ev_blob, args.mode,
                   have_evidence=bool(ev_blob.strip()))

    header = {
        "tool": "hallucination-police/mechanical_pass",
        "tier": "mechanical-deterministic",
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": target_path,
        "target_chars": len(target_text),
        "mode": args.mode,
        "evidence_files": len(ev_files),
        "evidence_chars": len(ev_blob),
        "evidence_unreadable": [{"path": p, "reason": r}
                                for p, r in unreadable],
        "evidence_excluded_as_target": excluded,
        "evidence_present": bool(ev_blob.strip()),
        "counts": {
            "total": len(findings),
            "high": sum(1 for f in findings if f["severity"] == "high"),
            "medium": sum(1 for f in findings if f["severity"] == "medium"),
            "low": sum(1 for f in findings if f["severity"] == "low"),
        },
        "coverage_note": (
            "Mechanical tier only. Absence of a finding is not evidence of "
            "grounding: this tier cannot judge whether a located source "
            "supports the claim made of it."),
    }

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"record": "header", **header}) + "\n")
            for f in findings:
                fh.write(json.dumps({"record": "finding", **f}) + "\n")

    if args.json:
        print(json.dumps({"header": header, "findings": findings}, indent=2))
        return 0

    if args.quiet:
        return 0

    print("target      : %s" % target_path)
    print("mode        : %s" % args.mode)
    print("evidence    : %d files, %d chars" % (len(ev_files), len(ev_blob)))
    if unreadable:
        print("unreadable  : %d (%s)" % (
            len(unreadable), "; ".join("%s: %s" % (os.path.basename(p), r)
                                       for p, r in unreadable[:4])))
    print("findings    : %d  (high %d / medium %d / low %d)" % (
        header["counts"]["total"], header["counts"]["high"],
        header["counts"]["medium"], header["counts"]["low"]))
    print("-" * 78)
    for f in findings:
        print("[%s] %-24s %-6s line %-5s %s" % (
            f["finding_id"], f["code"], f["severity"], f["line"], f["detail"]))
        print("      %s" % f["excerpt"][:150])
    print("-" * 78)
    print(header["coverage_note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
