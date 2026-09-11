# Build notes — hallucination-police

Built 2026-09-02. **Not installed.** This is a build directory, not a live
skill. Operator instruction: "do not install it. we are just building this
skill."

It was briefly created under the user-level skills directory during this session
and moved out at 00:34 local. That directory now contains exactly what it did
before. Nothing was deleted.

## What is here

| Path | What it is | State |
|---|---|---|
| `SKILL.md` | The operating instructions — modes, targets, tiers, action rules, apply guards | drafted, unreviewed |
| `scripts/mechanical_pass.py` | Deterministic offline detector | drafted, **exercised on one fixture** — see below |
| `ATTRIBUTION.md` | Public credit for the 26 projects whose ideas this borrows; licensing position | drafted 09-02 |
| `references/LEADS.md` | Traceability from the campaign to every design decision, plus leads not taken | drafted |
| `references/CLAIM_TAXONOMY.md` | Claim types and what counts as support for each | drafted, unreviewed |
| `references/VERDICTS_AND_ACTIONS.md` | The 8 verdicts, 7 actions, and the policy table | drafted, unreviewed |
| `templates/REPORT.md` | Output shape | drafted, unreviewed |
| `tests/run_fixture.py` | Span- and code-anchored regression checks over the fixture | 10 planted defects caught, 6 controls unaccused, 3 fail-closed checks held |
| `tests/fixture/` | Adversarial target + evidence corpus | checked in |

## Verification status — read this before trusting anything above

**This build was rejected for trusted use by an independent adversarial review
(Codex, `gpt-5.6-sol`, ultra) on 2026-09-02.** `CODEX_REVIEW.md` is that review,
unedited. The revision pass below addresses part of it. Read the review's
"Minimum release blockers" before trusting anything here.

**Run 1 — adversarial fixture.** `tests/run_fixture.py`, checked in. Ten
planted defects and six grounded controls; six of the ten are paired against a
near-identical control (a fabricated hash beside a grounded one, invented
figures beside grounded ones, a fabricated quote beside a verbatim one). The
remaining four — the overclaim cluster, the placeholder locator, and the two
self-reports — have no paired control.

The earlier version of this file reported "10/10 recall, 7/7 precision". **That
was a false metric claim.** The oracle concatenated finding *messages* and
searched for substrings; it never checked whether a finding's span covered the
control it declared untouched. Span-aware, four of the seven controls sat
inside emitted findings. The test now anchors every check to a document span
and a specific finding code, and calls itself what it is: a regression check,
not a measurement. It reports 10 planted defects caught, 6 controls unaccused
by any *grounding* finding, and 3 fail-closed behaviours held.

**Run 2 — false-positive floor on a genuinely grounded document.**
`FINDINGS.md` from this build's own source campaign, audited against its four
evidence files. This run is the one that changed the design.

First pass: 15 findings, **6 at high severity** — on a document that is in fact
well-grounded. Inspecting them found four distinct detector defects, all fixed:

| What fired wrongly | Why it was wrong | Fix |
|---|---|---|
| `UNGROUNDED_NUMBER` high, ×5 | Derived counts (47 search rows, 27 context, 56 manifestations, 40 in cell C10). Verified against the ledger: **all four checkable ones recompute exactly.** Real class, wrong action — repairing a correct count from memory would corrupt it. | New code `DERIVED_OR_UNGROUNDED_COUNT`, medium, action `RECOMPUTE` |
| `QUOTE_NOT_FOUND` high, ×1 | The author's own rhetorical question in quotation marks. Quotation marks also do term-mention and scare quotes. | Attribution cue required for `high`; short unattributed quotes skipped |
| `UNCITED_CHECKABLE_CLAIM` ×4 | Triggered by the date inside a coverage label. A date is not an uncited statistic. | Dates excluded from the trigger |
| `OVERCLAIM` ×2 | Fired on "**not** saturated" — the negation of an overclaim, i.e. the careful phrasing. | Negation check |

After the first four fixes: 10 findings, 0 at high severity. After the
post-review fixes below: **8 findings, 0 high** — 5 `RECOMPUTE`s, 2
uncited-claim notices, 1 downgraded quote.

**Correction, and it is the important one on this page.** This file previously
said the fifth derived count — 672 "recorded screening events" — "is not
derivable from the committed files at all", and called that a real finding
about the source document. **That was false.** The count is the sum of a
per-row field across the 47 search-log rows. All five counts recompute exactly.

The way that error was produced is worth recording, because it is the failure
this whole skill exists to catch: four counts were verified by one method, the
fifth was not found by that same method, and the author asserted a negative it
had never tested. `NO_EVIDENCE_OFFERED` on a status claim, written into two
files as a load-bearing example. It was caught by the independent review, not
by the author, which is the argument for §0 in a sentence.

**Not done:**

- **No independent verification.** Codex or a fresh session should run
  `tests/run_fixture.py` and read `scripts/mechanical_pass.py`.
- **No run against an Operator artifact.** Both test documents are research
  records. Real seat returns, case drafts, and manuscripts are the actual test,
  and the `UNCITED_CHECKABLE_CLAIM` noise rate on a footnoted case is unknown.
- **The judgment tiers have never run.** §§4–8 of `SKILL.md` are prose, not
  tested behaviour. Everything verified above is the mechanical tier only.
- **The action policy is untested.** `VERDICTS_AND_ACTIONS.md` is a stated
  judgment, not a calibrated one.
- **Apply-mode has never been exercised.** No file has been edited by this
  skill.

## Known limitations in the detector

- **PDF** needs `pdftotext` on PATH; absent, PDF evidence is reported unreadable
  rather than silently skipped.
- **DOCX** extraction is regex tag-stripping — body, footnotes, endnotes, and
  comments only. Tracked changes and text boxes are not read.
- **Number grounding is presence-only.** A figure found *anywhere* in the
  evidence blob counts as grounded, even if it appears in an unrelated context.
  This is a deliberate floor: it makes false negatives possible and false
  positives rare. The judgment tier is what closes that gap, and the taxonomy's
  denominator/universe/period contract is what it closes it with.
- **A bare integer absent from evidence is reported at `medium`, not `high`.**
  Run 2 showed that class is dominated by correct derived counts. The cost is
  that a genuinely fabricated bare integer — the fixture's invented "1180
  documents" — also lands at `medium`. Its action, `RECOMPUTE`, still surfaces
  the defect, but it will not shout. Accepted deliberately; revisit if a real
  document proves it wrong.
- **Short git shas** are grounded by prefix match against evidence, so a
  colliding prefix would pass.
- **Sentence splitting** is regex-based and will mis-split on abbreviations and
  inline code.
- Structural false positives are expected in tables (sentence-level checks
  skipped, values still checked) and in reference lists (not skipped — a
  bibliography will produce `UNCITED_CHECKABLE_CLAIM` noise). **Fenced code is
  NOT skipped** — only lines that begin with the fence marker are, so code
  inside a block is still scanned. An earlier version of this file claimed
  otherwise. Not yet addressed.

## Privacy scrub — 2026-09-02

Swept for personal, host, and internal-project identifiers on the assumption
this directory may be shared. Seven removed:

| Where | What | Why it mattered |
|---|---|---|
| `LEADS.md` header | Owner/repo name of the source campaign + local checkout path | The repo returns **HTTP 404** — it is private. Naming it leaked a private repo and the owner's handle. |
| `LEADS.md` calibration passage | A private unpublished file named by filename, with its contents summarised | **Integrity leak, not just privacy.** That file is meant to stay unread by agents; one reading this skill could have been influenced by it. |
| `CLAIM_TAXONOMY.md` `date` section | A specific defect record from that file, with exact before/after values | Same problem. Replaced with the generic lesson, which is the part that was actually useful. |
| `VERDICTS_AND_ACTIONS.md` | A machine name from the author's estate | Host identifier |
| `LEADS.md` leads section | Four internal campaign directory names + an internal tool path | Reveals private project structure |
| `BUILD_NOTES.md` | Absolute skills-directory paths, vault name, internal tool path | Host and project structure |
| `tests/fixture/TARGET.md` | The private repo URL, used as a benign-locator control | Replaced with a public one; fixture still passes |

The word "Operator" remains throughout as a role noun. It is not an identifier,
but it is idiosyncratic — swap it for "user" if that matters.

## Attribution — 2026-09-02

`ATTRIBUTION.md` credits the 26 projects whose published approaches informed the
design, with repository locators as recorded 2026-07-30.

Three things it states, all verified rather than assumed:

- **No code was copied.** Both Python files were written from scratch for this
  build, standard library only. Nothing was cloned, installed, or executed.
- **Licenses are unverified for every project listed.** The source campaign
  recorded `not_coded` for all 55 works by design — it mapped mechanisms, not
  reuse terms. No license is stated or inferred here, and the file says plainly
  that anyone copying from those projects must read their terms first.
- **The only quoted text** is from the author's own campaign synthesis. No
  third-party text is reproduced; project names and mechanism summaries are
  factual references.

Not done: the six post-ceiling projects named in `LEADS.md` (MARCH,
AbstentionBench, HalluEditBench, VeriFastScore, SelfCite, HALoGEN) have **no
locators** — the campaign only ever saw them as names. They are named as leads,
not cited as sources, and no locator was invented for them.

## Independent review and revision — 2026-09-02

`CODEX_REVIEW.md` is an unedited adversarial review by Codex (`gpt-5.6-sol`,
ultra), run scoped to this directory with read access to the source campaign.
Its verdict: **reject for installation or trusted use.** It is right, and the
build should be read as pre-alpha until its blockers are closed.

Its sharpest catches, all reproduced independently before acting on them:

- A document of pure fabrication scored **zero findings**.
- The advertised "7/7 precision" was not precision. The review counted seven
  named controls and found four of them inside emitted finding spans.
- The self-report check never consulted the evidence, and accused a claim the
  evidence supported.
- **672 is derivable.** The claim that it was not was the author's own
  hallucination, in two files.
- `CITE_MARKERS` backtracked polynomially: 7.7 KB took over 3 seconds.

### Fixed in this pass

| Review ref | Fix |
|---|---|
| C1/H1 | **Fails closed.** No usable evidence → exit 3, not a quiet zero. `--allow-no-evidence` runs only the evidence-free checks, explicitly. |
| C2 | Target is excluded from its own evidence set; a binary evidence file is rejected rather than decoded to noise. |
| H7 | `--out` pointing at the target or an evidence file is refused. Binary and oversized targets refused. |
| H2 | `INTERNAL_CONTRADICTION` reports a real line and span; prefix-collision logic no longer suppresses real conflicts nor invents fake ones. |
| H3 | Unattributed short quotes no longer consume the span, so statistics inside them are still checked. Postposed attribution (`"…," Alice said`) now recognised. |
| H4 | Fixture oracle rewritten: span-aware, code-aware, and it no longer calls itself recall or precision. Adds three fail-closed assertions. |
| H5 | Self-report consults the evidence and reports which of the two failures applies. Verb list widened ("we executed", "CI succeeded", "build stayed green"). |
| H6 | Every `CITE_MARKERS` branch length-bounded. 7.7 KB probe: 3+ s → 0.005 s. |
| M1 | Uppercase shas caught via commit-context; all-letter hex words ("defaced", "feedface") no longer accused; DOI no longer swallows sentence punctuation; one locator emits one finding. |
| M2 | ISO dates masked and checked whole (no more 07/30 as bare counts); percentage↔ratio comparison uses exact `Decimal`, not `%.10f`; "25 percent" activates the ratio check. |
| M5 | Absolutes widened ("perfect", "cannot fail", "zero errors"); negation window widened; a quoted or mentioned term is no longer an overclaim. |
| D1 | Three traceability overclaims corrected in `LEADS.md` (W054/W055 relevance ordering, W050 span output, W049 model internals); "beats any single algorithm" and the C7 "states this directly" wording downgraded. |
| D2 | `ATTRIBUTION.md` no longer states "no code copied" as a guarantee, and now records that this repository itself carries no licence. |

A 12-case regression set drawn from the review's counterexamples now behaves
correctly — those cases are enumerated in the fixed table above, one per row of
M1/M2/M5/H3/H5. **That is a sample, not the whole review:** C2 alone tables six
more pairs, M3 five and M4 six, and those remain broken by design or by
omission. On the grounded reference document the noise floor fell 10 → 8
findings, 0 high.

### NOT fixed — still open from the review

- **C2 core.** Grounding is still context-free *presence*: a value found
  anywhere in the evidence blob counts as grounded, regardless of what it was
  attached to. Every pair in the review's C2 table still passes. This is the
  central false-negative path and closing it needs claim-scoped comparison, not
  a patch.
- **C1 core.** Plain factual assertions are still not claim-extracted at all.
  With evidence supplied, most of the fabricated document still scores low.
- **H8.** One verdict per unit cannot express T1–T5 disagreement, and the JSONL
  is still only a finding stream, not the per-claim ledger `SKILL.md` promises.
- **H9.** Action-table incoherences unresolved: `UNSUPPORTED → SOFTEN` can
  preserve an unsupported claim; `SOURCE_MISIDENTIFIED → REPAIR` assumes a
  correct source is known; severity rules overlap without precedence.
- **H7 remainder.** No resolved-path/allowed-root check, no atomicity, no
  post-edit verification; the governing-document denylist omits `AGENTS.md`,
  config files, case variants, and symlink aliases.
- **H7 authority.** `SKILL.md` still says network fetch is "authorized" — a
  skill cannot grant that, and there is no rule treating fetched text as
  untrusted data rather than instructions. Should be fixed before any fetch.
- **P2.** Outputs still embed absolute paths and verbatim spans; no redaction
  or minimisation rule. Do not publish a generated report unreviewed.
- **The "first pass" run** described above is not reproducible — no pre-fix
  executable was retained. Treat that narrative as testimony, not evidence.

## Open rulings

1. **Where does this live if it is ever installed?** The user-level skills
   directory (live in every project on this machine) vs a project-scoped one vs
   the skills vault. Not decided; not acted on.
2. **Reconcile with the existing domain-specific citation checker.** That tool
   already does registry-backed citation checking for one document pipeline. If
   this skill is ever pointed at material that pipeline owns, one of them should
   defer to the other.
3. **Apply-mode authority.** The Operator ruled "report + apply fixes". The
   guards in `SKILL.md` §7 (never CUT, never a governing doc, always a
   recoverable prior version, never an invented replacement) are this session's
   reading of that ruling against standing doctrine, not something the Operator
   ruled directly. Worth confirming.
4. **Does `OVERCLAIM` earn its place?** It is the noisiest category and the only
   one that is a style judgment rather than a grounding check.

## If installing later

Copy the directory to the chosen skills root. `SKILL.md` refers to
`$SKILL_DIR/scripts/mechanical_pass.py` rather than a hard-coded path, so the
directory relocates without edits. Note that a `SKILL.md` under a skills root
is auto-registered and its description becomes live trigger surface — that is
what "installed" means here, and it is why it was moved out.
