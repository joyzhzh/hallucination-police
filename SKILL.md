---
name: hallucination-police
description: Audit a document or an agent's return for hallucinated content — fabricated citations, invented identifiers (sha256/commit/DOI), numbers that appear nowhere in the evidence, quotes that aren't in the source, unsupported self-reports ("suite 640 OK"), and overclaims. Use before sending, publishing, or landing anything; use on any seat return, REPORT.md, handoff, or summary another Claude/Codex session produced; and use when the user says "check this for hallucinations", "did it make this up", "police this", "verify these claims", "is this grounded", "fact-check my draft", or "audit this agent's return". Produces a per-claim verdict ledger with an explicit action per finding, and applies repairs where authorized.
---

# Hallucination Police

An independent checker. It never wrote the thing it inspects, and it does not
trust the thing it inspects. Its job is to convert prose into a ledger of
checkable claims, bind each one to evidence, issue a verdict, and take a named
action.

**The governing rule, from the research this skill is built on:** a detector
score without a calibrated threshold and an explicit block/retry/abstain/
escalate path *observes* risk — it does not reduce it. Every finding here
terminates in an action, or it is not a finding.

Design provenance: `references/LEADS.md` (55 deep-coded repositories, from a
private repository-scouting campaign frozen 2026-07-30).

---

## 0. Refuse to grade your own work

If **you** wrote the target text in this same session, say so and stop. Ask the
Operator to fire a fresh session, or run the audit through a subagent that has
not seen your reasoning. A checker sharing the author's context shares the
author's errors. The research this is built on says checker models *can* share
errors and biases with generators; the same-session prohibition is a prudent
reading of that caution, not something the research establishes. It is still the
most load-bearing constraint here — it is what caught the largest error in this
skill's own documentation.

Exception: the mechanical tier (§3) is deterministic and may run on your own
output. Its findings stand; the judgment tiers (§5) do not.

---

## 1. Two entry modes

**Mode A — DOCUMENT.** Target is a file: `.md`, `.txt`, `.docx`, `.pdf`,
`.html`, `.json`. The Operator is about to send, publish, land, or submit it.

**Mode B — RETURN.** Target is what an agent just claimed: a `REPORT.md`,
`FINDINGS.md`, seat return, handoff memo, verification record, or a pasted
summary. Mode B additionally checks **self-reports** — claims about work the
agent says it did — which Mode A usually has none of.

Both modes produce the same ledger. Mode B raises the risk tier on self-report
and identifier claims by one level: those are the claims an agent has the
strongest incentive and the easiest opportunity to confabulate.

---

## 2. Declare the target before checking anything

"Hallucination" is not one thing. Five operational targets, and **they
disagree** — a passage can be perfectly faithful to a wrong document, or
factually correct with a fabricated citation attached. Declare which you are
checking in the ledger header. Never report one target's result as another's.

| ID | Target | The question it answers |
|----|--------|------------------------|
| T1 | Parametric truthfulness | Is this unsourced world-knowledge claim true? |
| T2 | Contextual faithfulness | Is this supported by the evidence actually supplied? |
| T3 | World-verifiable factuality | Can this atomic claim be supported by external evidence? |
| T4 | Attribution / citation support | Does the cited source exist, say this, and get identified correctly? |
| T5 | Selective behavior | Should this have been asserted at all, or abstained from? |

Default for Mode A: T2 + T4, plus T3 for any claim with no supplied evidence.
Default for Mode B: T2 + T4 + T5, plus the self-report class.

**Ask the Operator for the evidence set** if none is obvious: source files,
corpus, transcript, folder. If there genuinely is none, say so — you are then
running T3 alone, which is weaker, and the ledger header must record it.

---

## 3. Mechanical tier — run first, run whole

Deterministic, offline, no model judgment, cheap. It catches a specific set of
failure *shapes* — the ones catchable without reading for meaning. How large a
share of real defects that is has never been measured, and an independent review
built a document of pure fabrication that this tier scored at zero. It is a
floor, not a filter. §§4–8 are where the actual checking happens.

**It fails closed.** With no usable evidence it refuses to run rather than
return a quiet result, because "no findings" and "nothing could be checked" look
identical in a report and only one of them is safe.

```bash
python3 "$SKILL_DIR/scripts/mechanical_pass.py" --target FILE --evidence DIR --mode return --out ledger.jsonl
```

`$SKILL_DIR` is this skill's own directory — resolve it from where `SKILL.md`
was loaded, not from a hard-coded install path.

`--evidence` repeats. `--mode` is `document` or `return`. Add `--json` for the
machine summary, `--quiet` to suppress the human table.

What it flags, each with line number and exact span:

- `UNGROUNDED_IDENTIFIER` — a sha256, git sha, DOI, arXiv ID, or ISBN present in
  the prose and in **none** of the evidence. (Issue and PR numbers are NOT
  covered — there is no pattern for them.) This is the
  confabulated-hash failure. Every hit is guilty until traced.
- `UNGROUNDED_NUMBER` — a *measured* figure — percentage, money, decimal, or a
  number carrying a unit — appearing in no evidence file, under numeric
  normalization (`1,234`≡`1234`). Also fires on dates, at `medium`.
- `DERIVED_OR_UNGROUNDED_COUNT` — a bare integer absent from evidence. Usually a
  count someone derived by counting rows rather than copied from a source, so
  the action is `RECOMPUTE`, not `REPAIR`. Do not repair it from memory: a
  derived count is right or wrong by arithmetic, and the arithmetic is cheap.
- `QUOTE_NOT_FOUND` — quoted text of ≥4 words, not present verbatim in evidence.
  `high` when an attribution cue precedes it ("X writes that…"); `medium`
  without one, since quotation marks also do term-mention and scare quotes and
  those are not claims about a source.
- `UNCITED_CHECKABLE_CLAIM` — a sentence carrying a statistic or quote with no
  locator, footnote marker, or citation anywhere in it.
- `SELF_REPORT_UNBACKED` — "suite 640 OK", "tests pass", "verified", "I ran",
  "we executed", "CI green" with no captured command output in evidence. Also
  fires at `low` when output IS present and the figures reconcile, as a prompt
  to confirm the output came from this run.
- `OVERCLAIM` — "proves", "guarantees", "always", "never", "the first", "the
  only", "state of the art", "comprehensive", "exhaustive", "saturated".
- `LOCATOR_SUSPECT` — malformed URL or placeholder host.
- `INTERNAL_CONTRADICTION` — one identifier prefix bound to two different full
  values in the same document.

Do not skip categories because they look noisy. Report noisy ones at `low`
severity; never drop them silently.

---

## 4. Decompose into claim units

Split the target into atomic, independently checkable claims. Finer units
localize the defect and enable targeted repair — but **decomposition is itself
a source of distortion and omission**, so:

- Keep the original sentence and its line span attached to every unit.
- Never let a unit assert more than its source sentence did.
- If a sentence resists atomization, keep it whole and mark
  `decomposition: verbatim`.

Classify each unit — `references/CLAIM_TAXONOMY.md` says what counts as support
for each type. The types are not interchangeable: a quote needs verbatim match;
a statistic needs the number *and* its denominator, universe, and period; an
identifier needs byte-level provenance; an attribution-of-position needs the
cited author to actually hold that position.

Uncheckable content — opinion, recommendation, plan, hedged speculation — gets
`type: non-claim` and drops out. Report how many dropped.

---

## 5. Bind evidence, then verify

For each checkable unit, gather evidence in this order and record which tier
you reached:

1. **Supplied evidence** — the files, corpus, or transcript the Operator named.
2. **Filesystem / repo ground truth** — for identifier, path, and status claims:
   does the commit exist (`git cat-file -t`), does the file exist, does the hash
   match (`shasum -a 256`)? Run the check; do not reason about it.
3. **Fetched locator** — network fetch is authorized. Open the URL or DOI and
   confirm three separate things, never collapsed: (a) the source **exists**,
   (b) it **is** the source claimed — right title, author, venue, year, since a
   real source misidentified is its own defect, (c) it **supports** the claim.
4. **Nothing available** → `UNVERIFIABLE_HERE`. This is *not* a synonym for
   unsupported and must never be reported as one.

Then issue exactly one verdict per unit:

`SUPPORTED` · `PARTIALLY_SUPPORTED` (source supports a weaker version) ·
`UNSUPPORTED` (evidence found, does not support) · `CONTRADICTED` ·
`SOURCE_NOT_FOUND` (locator dead or fabricated) · `SOURCE_MISIDENTIFIED` ·
`NO_EVIDENCE_OFFERED` (asserted bare) · `UNVERIFIABLE_HERE`.

**Second pass on high-risk units.** Any unit that is `CONTRADICTED`,
`SOURCE_NOT_FOUND`, or `SOURCE_MISIDENTIFIED`, plus every unit of class
`identifier` or `self-report`, gets re-checked by a differently-framed pass
instructed *to refute the finding*. Agreement between two identically prompted
passes is not evidence — one checker agreeing with itself is one checker.
Record both verdicts when they differ.

Tag every verdict `high` / `moderate` / `low` / `unknown` confidence.

---

## 6. Every verdict terminates in an action

Look the action up in `references/VERDICTS_AND_ACTIONS.md`. It is a function of
**verdict × claim type × destination risk**, not of verdict alone. Destination
risk runs `private-note` < `internal-landing` < `sent-to-a-person` <
`published`. Ask which if it is not obvious.

Actions: `PASS` · `SOFTEN` (rewrite down to exactly what the evidence supports)
· `REPAIR` (replace with the correct value) · `RECOMPUTE` (derive the count from
evidence already in hand) · `RETRIEVE` (go get evidence you do not have) ·
`CUT` (the claim cannot stand) · `ESCALATE` (Operator ruling required).

---

## 7. Applying repairs — authorized, but fenced

The Operator has authorized this skill to apply fixes. Guards, all mandatory:

1. **Preserve the original first.** If the file is not in a clean git tree, copy
   it to `<name>.prepolice-<UTC-timestamp>` beside it before the first edit.
   Never overwrite without a recoverable prior version. Never delete anything.
2. **Confidence bar.** Apply only `high`-confidence `REPAIR` and `SOFTEN` where
   the replacement is fully determined by evidence you actually read. Everything
   else is reported, not applied.
3. **Never apply `CUT`.** Removing a claim changes what the document argues.
   Propose the deletion with paste-ready text; the Operator makes the cut.
4. **Governing documents are off-limits.** `CLAUDE.md`, anything under
   `protocols/`, any `SKILL.md`, ratified specs, and acceptance or verdict
   records are Operator-edited. Report only — do not touch, even at high
   confidence.
5. **Never invent a replacement.** A repair's new value must be copied from
   evidence you opened. If you cannot copy it, the action is `RETRIEVE` or
   `ESCALATE`, not `REPAIR`.
6. **Report every applied edit** with before, after, and the evidence locator
   that licensed it.

---

## 8. Deliver

Write `REPORT.md` beside the target from `templates/REPORT.md`, plus the
machine ledger as JSONL. The report leads with:

- target, mode, declared targets (T1–T5), evidence set, destination risk;
- counts: units checked, by verdict, by action, applied vs proposed;
- **defects ordered by severity, not by document order**;
- what was *not* checkable and why — mandatory, and may not be empty without a
  stated reason;
- a calibrated coverage line. You may write "no defect found in N units under
  targets X". You may **never** write "accurate", "verified", or "clean".
  Absence of a detected defect is not proof of grounding, and the campaign's own
  coverage limitation applies to this skill too.

Then log the run: one line with target, counts, and applied-edit count.

---

## 9. What this skill will not do

- Certify a document as true.
- Collapse the five targets into one "hallucination score".
- Treat repeated model agreement as evidence — samples agree on falsehoods.
- Treat a present citation as a supported claim.
- Treat retrieval as grounding: retrieved evidence can be wrong, stale, or
  irrelevant, and a claim faithfully grounded in a bad source is still a defect.
  Check the evidence's own standing when it matters.
- Write a hash, ID, count, or metric it did not read from displayed output.
