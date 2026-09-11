# Adversarial review — hallucination-police

## Verdict

**Reject this build for installation or trusted use.** The mechanical tier can
return zero findings for a document packed with fabricated facts, identifiers,
statistics, quotations, self-reports, and locators. Its evidence test is global
string/number presence rather than claim support. The fixture's advertised
“7/7 precision” is not a precision measurement and passes while four of its
seven grounded controls are inside emitted finding spans.

The executable reviewed was
scripts/mechanical_pass.py SHA-256
**d24840b72ca28e943ca57613af3d6f145ff8fa5dc9b70af1dd5010066cb1fe68**.
That file remained byte-identical throughout this review.

Severity below is my assessment of harm to this build, not the severity value
the detector happens to emit. “Certain” means reproduced or directly implied
by the shipped bytes. Confidence is stated on every finding.

## Snapshot-integrity warning

The directory was **not stable during the review**. After my opening hash
inventory, an external process added ATTRIBUTION.md, rewrote BUILD_NOTES.md,
three reference files, and the fixture target, and briefly created a
BUILD_NOTES.md.tmp.* replacement file. None of my review agents wrote those
files. The most important transitions were:

| File | Opening SHA-256 | Later stable SHA-256 |
|---|---|---|
| BUILD_NOTES.md | 9ae0ba0d… | 3c733bf9… |
| references/LEADS.md | 71f0fc76… | dc2c16c4… |
| references/CLAIM_TAXONOMY.md | 6052db5d… | 415a81ea… |
| references/VERDICTS_AND_ACTIONS.md | 87d9d2c9… | 7a2757cc… |
| tests/fixture/TARGET.md | b6270af3… | 3b4bea20… |
| ATTRIBUTION.md | absent | e4a06f7e… |

SKILL.md, the executable, test harness, template, and fixture evidence stayed
unchanged. Findings about changed prose use the later stable line numbers unless
explicitly marked “opening snapshot.” This was not an audit of one frozen
bundle, and no claim that only CODEX_REVIEW.md changed during the overall
review interval would be true.

## Critical findings

### C1. A claim-rich fabricated return scores zero

**Severity: critical. Certainty: certain. Confidence: high.**

The following exact target, run in return mode against an empty evidence
string, produced **zero findings**:

~~~markdown
# Mission report

Professor Quill discovered the moon Virelia beneath Paris and dated it to the Bronze Age.
Its population is nine hundred million, and ninety-nine percent speak Martian.
The reactor delivered 9e99 joules while latency held at 25ms and failure probability stayed below .000001.
Commit DEADBEEF contains the flight software.
“Virelia has oceans made entirely of liquid diamond,” Quill said.
We executed every benchmark case successfully; CI succeeded and the build stayed green.
The system is perfect, cannot fail, has zero errors, and is the world’s first flawless reasoner.
The full study is at https://research-virelia.invalid/results/2026 and https://arxiv.org/abs/9999.99999.
Twelve independent laboratories reproduced every result, while five governments adopted it.
All underlying samples were collected on the far side of Neptune by the private Zephyr Institute.
~~~

Observed result:

~~~text
mode=return
evidence=""
finding_count=0
~~~

This is not an exotic encoding trick. It uses ordinary prose plus common
representations the patterns omit: spelled-out quantities, scientific
notation, a leading-dot decimal, attached units, uppercase hexadecimal, a
postposed attribution, ordinary self-report verbs, ordinary absolute language,
and identifiers inside URLs. Plain factual assertions—most of the document—are
not claim-extracted at all.

This directly disproves the executable docstring's “extracts every mechanically
checkable assertion” and leaves SKILL.md lines 78–80 (“in long agent-written
documents ... most of them”) without empirical support. BUILD_NOTES.md itself
says no real Operator artifact and no judgment tier were tested.

### C2. “Grounding” is context-free presence and is trivially poisoned

**Severity: critical. Certainty: certain. Confidence: high.**

At mechanical_pass.py lines 244–246 and 283–290, evidence is collapsed into:

- one normalized text blob;
- one global set of number spellings; and
- raw lowercase substring membership for every identifier.

No filename, claim span, unit, sign, denominator, universe, period, cited
source, or semantic context participates. Reproduced zero-finding pairs:

| Target | Evidence | Wrong result |
|---|---|---|
| The payload weighed 50 GB (source.md). | The study enrolled 50 patients. | 0 findings |
| Temperature was -42 degrees (source.md). | The control cohort contained 42 people. | 0 findings |
| Mortality was 99%; see nothing. | See page 99. | 0 findings |
| Accuracy was 12.345678904% (source.md). | An unrelated coefficient was 0.123456789. | 0 findings |
| Commit deadbee was deployed (source.md). | The unrelated token is deadbeezebra. | 0 findings |
| The budget was $1,2,3 (source.md). | The appendix has 123 pages. | 0 findings |

The short-Git-prefix fallback is dead logic: if a longer token contains the
short prefix, the earlier raw substring test has already returned true.

There is also no guard against including the target in its own evidence. With
the shipped fixture as target and tests/fixture as the evidence directory, the
target is collected as evidence. All planted identifier, number, and quotation
defects then ground themselves. The run dropped from 15 findings to 9 and
retained only self-report, citation-shape, and overclaim categories.

This limitation is partly admitted in BUILD_NOTES.md lines 83–87, but calling
it deliberate does not make the detector correct. It is the central
false-negative path, and the judgment tier cannot reliably “close” it when the
mechanical output has already represented a fabricated value as grounded.

## High-severity findings

### H1. Empty, missing, binary, and wrong-encoding evidence fail open

**Severity: high. Certainty: certain. Confidence: high.**

The CLI accepts no evidence arguments. Missing or unreadable evidence is placed
in header metadata but does not affect exit status or create a finding.

Concrete run:

~~~text
target=/dev/null
evidence=/definitely/not/here
evidence_files=0
evidence_unreadable=[{"reason":"not found"}]
counts.total=0
exit=0
~~~

An empty target with no evidence also exits zero with zero findings. An explicit
binary path is decoded as UTF-8 with replacement rather than rejected:

~~~text
target=/bin/ls
evidence=/bin/cp
target_chars=153743
evidence_files=1
evidence_chars=136290
evidence_unreadable=[]
~~~

The binary target emitted 43 meaningless text findings. A UTF-16LE target
containing “Fabricated rate 91.4%.” became NUL-interleaved text and produced
zero findings. Directory evidence with an unlisted or extensionless filename is
silently omitted; os.walk errors are not reported.

The evidence “cap” is also fail-open for size. collect_evidence checks the
running total **before** reading the next entire file, measures decoded
characters rather than bytes, and uses “greater than” rather than “greater than
or equal.” Thus an arbitrarily large first file is fully read, and a second file
is still read when the first lands exactly on the advertised 64 MiB cap.
Targets, HTML, DOCX members, and PDF subprocesses have no cap; pdftotext has no
timeout. A DOCX zip bomb or one huge target can exhaust memory before any
finding exists.

### H2. INTERNAL_CONTRADICTION is wrong in both directions and corrupts severity

**Severity: high. Certainty: certain. Confidence: high.**

The prefix logic at lines 298–312 removes a value from the conflict set if it
has *any* prefix-compatible peer. A common short alias therefore suppresses the
conflict it should expose:

~~~python
target = "abcdef1 abcdef1aaaaaaa abcdef1bbbbbbb"
evidence = target
# observed: []
~~~

Conversely, two unrelated grounded commits from different repositories that
happen to share seven characters are called a contradiction without any claim
that they identify the same object:

~~~python
target = "Repo A is at abcdef1a. Repo B is at abcdef1b."
evidence = "abcdef1a abcdef1b"
# observed: INTERNAL_CONTRADICTION, high, line 0, span [0,0]
~~~

The fake line 0/span [0,0] violates SKILL.md's promise of a line number and
exact span. It also changes other results. In a document beginning “I ran
checks.”, the self-report harshness test treats the unrelated contradiction at
span zero as a high finding inside the first sentence and promotes that
self-report from low to high.

The grouping is itself overbroad: SHA-256 values and Git commits are mixed, and
repository/object identity is ignored.

### H3. Quote masking silently drops the statistic it decided not to check

**Severity: high. Certainty: certain. Confidence: high.**

At lines 319–328, a four-to-ten-word quotation is marked consumed **before** an
unattributed short quote is skipped. The number pass then refuses to inspect
the consumed span.

Exact zero-finding input with empty evidence:

~~~text
Metric is “99 percent across five invented trials”; see nothing.
~~~

The quote detector also misses:

- postposed attribution: “These six invented words never appeared,” Alice said;
- multiline quotations;
- quotations longer than 600 characters;
- single-quoted passages; and
- attributed passages shorter than four words.

ATTRIB_CUE_RE's dollar anchor is not an accidental whole-line anchor; it anchors
to the end of the preceding slice. The defect is that only a preceding,
period-free, roughly 80-character cue is considered. Attribution after the
quote cannot match.

SHA-256 and DOI extraction has the opposite masking defect: both initial loops
record an overlapping match without consulting consumed. This exact text
emits two high identifier findings for one locator:

~~~text
doi:10.1234/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
~~~

### H4. The fixture's “precision” is rigged and its recall is circular

**Severity: high. Certainty: certain. Confidence: high.**

The shipped command still prints:

~~~text
findings: 15 (high 7)
recall   : 10/10 planted defects caught
precision: 7/7  grounded controls left alone
PASS
~~~

But tests/run_fixture.py lines 68–72 concatenate only each finding's generic
detail string and search hand-picked substrings. They never check finding code,
line, span, uniqueness, claim-to-finding correspondence, or whether a grounded
control lies within another finding.

Raw output shows:

- UNCITED_CHECKABLE_CLAIM at fixture line 7 spans all three grounded controls
  43, 153, and 28.1%;
- UNCITED_CHECKABLE_CLAIM at line 15 spans grounded control 147; and
- SELF_REPORT_UNBACKED also accuses line 15 even though the evidence contains
  the pytest command and “147 passed.”

Therefore only **3 of the 7** named grounded controls have no overlapping
finding, not 7 of 7. Whether an uncited notice is useful is irrelevant to the
test's own assertion that the control was “left alone.”

The oracle cannot detect some false positives at all. Its quote negative
control searches for quote text in detail, but QUOTE_NOT_FOUND detail contains
only “Quoted passage of N words”; the quote is stored in excerpt. Conversely,
the recall oracle's generic “Quoted passage of 8 words” could be satisfied by a
different eight-word quotation. Multiple findings may satisfy one planted
substring, and one finding may satisfy more than one label. This is not recall
or precision in their standard senses; it is a regression check tailored to
the current messages.

The target also says “I also verified the corpus byte-for-byte,” but the regex
does not match “I also verified” and MUST_CATCH omits it. The tests were written
by the code's author, exercise exactly the syntax the regexes recognize, and
do not challenge the documented limitations. “Rigged” is justified in the
technical sense: the data and oracle are circular and structurally unable to
falsify the advertised precision claim.

### H5. Self-report checking ignores the supplied evidence

**Severity: high. Certainty: certain. Confidence: high.**

SELF_REPORT_RE is searched at lines 419–430, but ev_blob is never consulted.
The finding message nevertheless asserts that captured output is absent.

~~~python
target = "I ran the suite and 147 tests passed."
evidence = "$ python -m pytest\n147 passed"
~~~

Observed: SELF_REPORT_UNBACKED is high in return mode, plus an uncited notice.
The same false accusation is in the shipped fixture. In the other direction,
common unsupported forms—“we executed,” “CI succeeded,” “the build stayed
green,” “pytest reported success,” and passive constructions—are missed.

The code therefore does not implement the documented question “with no
captured command output in evidence.” It implements “did one of these phrases
appear in the target?”

### H6. CITE_MARKERS has exploitable polynomial backtracking

**Severity: high. Certainty: certain. Confidence: high.**

The author-year branch repeatedly scans an unclosed parenthetical, and the
generic filename branch backtracks over long word runs without a dot.
CITE_MARKERS.search is executed for every sentence whether or not that
sentence contains a number or quotation.

Measured direct probe:

~~~python
s = ("(Smith and X" * n) + " end"
CITE_MARKERS.search(s)
~~~

~~~text
n=320, 3844 characters: 1.571 seconds
n=640, 7684 characters: exceeded 3 seconds
~~~

A separate long all-letter probe held the process beyond the tool's normal
10-second yield. This is polynomial rather than proven exponential
catastrophic backtracking, but the absence of a target-size cap makes it a
practical denial of service on adversarial input.

I found no comparable exponential behavior in GITSHA_RE, QUOTE_RE,
SELF_REPORT_RE, OVERCLAIM_RE, ATTRIB_CUE_RE, UNIT_RE, or SENT_SPLIT. The
confirmed complexity defect is CITE_MARKERS.

### H7. Output and apply rules can overwrite the audited file or governing files

**Severity: high. Certainty: certain. Confidence: high.**

There are two certain clobber paths:

1. Mode B explicitly permits a target named REPORT.md (SKILL.md line 41), while
   line 219 requires writing REPORT.md beside the target. The output path is
   then the target itself.
2. mechanical_pass.py lines 510–514 opens any --out path with mode "w" without
   checking target/evidence identity, existence, symlinks, or prior output. For
   example, --target report.md --out report.md reads and then truncates the
   target.

I did not execute these destructive probes. The control flow is unambiguous.
The section 7 backup guard covers “repairs,” not report or ledger creation.

Apply authority is also contradictory. SKILL.md line 195 and
VERDICTS_AND_ACTIONS.md line 111 claim blanket Operator authorization, while
BUILD_NOTES.md lines 151–155 says this is the author session's interpretation
and is worth confirming. The frontmatter triggers on ordinary requests such as
“fact-check my draft,” so a capable model could treat a review request as
permission to mutate.

Other missing guards:

- AGENTS.md, .codex policy, configuration, case variants, and symlink aliases
  are absent from the governing-document denylist;
- no resolved-path or allowed-root check;
- “clean Git tree” does not prove an ignored target is tracked;
- no pre-edit hash/re-read or concurrent-change check;
- no atomic replacement, scoped-diff check, render check, or post-edit audit;
- a “soften” edit can change an argument just as materially as a cut; and
- backup creation is not read back or hashed.

SKILL.md line 154 also declares network fetch “authorized.” A skill cannot grant
user or system authority. There is no private/local URL rule and no instruction
to treat fetched text as untrusted evidence rather than task instructions,
despite the source campaign having exactly that boundary.

### H8. The judgment schema cannot represent the distinctions it requires

**Severity: high. Certainty: certain. Confidence: high.**

SKILL.md lines 54–68 says T1–T5 can disagree, then line 161 demands exactly one
verdict per unit. The report has no per-target verdict field. An externally
true claim absent from supplied context needs T2=NO_EVIDENCE_OFFERED or
UNSUPPORTED and T3=SUPPORTED; the ledger cannot express both.

Likewise, CLAIM_TAXONOMY.md lines 78–85 says citation existence, identity, and
support must be checked separately and never collapsed, but one verdict loses
simultaneous defects. “Every unit has exactly one claim_type” also cannot
represent an attributed, cited quotation containing a statistic and an
identifier.

The second-pass rule contradicts the schema again: line 161 says one verdict,
line 173 says record both when two passes differ, and nothing says which result
controls counts, action, severity, or automatic editing.

The executable JSONL is only a mechanical finding stream. It contains no full
claim-unit inventory, T1–T5 results, judgment verdict, confidence, evidence
tier/locator, second-pass result, or non-claim count. No schema or merge
procedure turns it into the promised per-claim machine ledger.

### H9. The action table can preserve or create unsupported claims

**Severity: high. Certainty: certain. Confidence: high.**

VERDICTS_AND_ACTIONS.md defines UNSUPPORTED as evidence inspected and not
entailing the claim. A weaker entailed version already has its own verdict,
PARTIALLY_SUPPORTED. Nevertheless, the policy maps unsupported statistics,
citations, attributions, causal claims, and status claims to SOFTEN in at least
one destination tier. A softer claim for which there is still no entailment is
still unsupported.

Other incoherent cells and rules:

- UNVERIFIABLE_HERE causal/status → SOFTEN, inviting an evidence-free hedge;
- SOURCE_MISIDENTIFIED → REPAIR even when the correct source is unknown;
- an overclaim “always” adds SOFTEN on top of CUT or ESCALATE despite the
  one-action contract;
- PARTIALLY_SUPPORTED quote conflicts with the exact-verbatim quote contract;
- SOURCE_NOT_FOUND overlaps SOURCE_MISIDENTIFIED as worded;
- NO_EVIDENCE_OFFERED overlaps UNVERIFIABLE_HERE;
- automatic SOFTEN must be “copied” from evidence and “never composed,” even
  though softening is a rewrite; and
- the statistic contract requires denominator, universe, unit, and period for
  every count, duration, money figure, or file size, making ordinary claims
  such as “the file is 12 bytes” impossible to support.

Severity rules also overlap without precedence. An UNVERIFIABLE identifier is
both high (“any identifier defect”) and low (“UNVERIFIABLE_HERE where expected”);
a PARTIALLY_SUPPORTED identifier is both high and medium.

The report template omits RECOMPUTE from its action-count table even though the
prose defines seven actions. BUILD_NOTES.md line 20 incorrectly says six.

## Medium-severity detector findings

### M1. Identifier regexes miss real forms and accuse ordinary words

**Severity: medium. Certainty: certain. Confidence: high.**

- GITSHA_RE is lowercase-only. “Commit DEADBEEF was deployed.” yields zero.
- An all-numeric 40-character Git object is treated as a medium bare count, not
  a high identifier.
- Ordinary “The statue was defaced.” emits a high UNGROUNDED_IDENTIFIER because
  defaced consists of seven hexadecimal letters. deadbeef and feedface behave
  similarly.
- SKILL.md line 94 says issue/PR numbers are covered, but there is no issue/PR
  identifier regex. “Issue #7 was merged.” yields zero; larger values are
  generic counts, not identifiers.
- DOI_RE consumes sentence punctuation. Target “doi:10.1234/valid.” against
  evidence “10.1234/valid” emits a high false positive.
- Identifier grounding uses raw substring membership for DOI, arXiv, ISBN,
  SHA-256, and Git SHA alike, so a value attached to a different object passes.

### M2. Number normalization is lossy and UNIT_RE is often unreachable

**Severity: medium. Certainty: certain. Confidence: high.**

NUM_RE misses leading-dot decimals, scientific notation, and digits directly
attached to letter units:

~~~text
Failure probability was .98765.
The system processed 9e99 records.
Latency was 25ms; see nothing.
Accuracy was 91percent; see nothing.
~~~

Each produced zero findings with empty evidence in the direct probe. The
post-number word boundary makes much of UNIT_RE unreachable for attached units.
NUM_RE also excludes signs, so -75 is grounded by unrelated +75. norm_number
blindly removes every comma, making malformed 10,00 equivalent to 1000.

The percentage fallback formats float(value/100) with %.10f. Different values
therefore collapse:

~~~text
target:   The rate was 12.345678904% (source.md).
evidence: Observed fraction: 0.1234567890
result:   0 findings
~~~

At very small values, 0.000000001% formats to zero and can be grounded by any
evidence zero. Conversely, “25 percent” does not activate ratio equivalence;
evidence 0.25 produces a high false positive because only a literal percent
sign in the next two characters sets pct.

ISO dates are split:

~~~text
target: Coverage is current as of 2026-07-30.
evidence: empty
~~~

Observed: Date 2026, Count 07, Count 30, and UNCITED_CHECKABLE_CLAIM—four
findings for one date.

### M3. Citation markers are syntactic noise, not citations

**Severity: medium. Certainty: certain. Confidence: high.**

With unrelated evidence containing 99, all of these suppress
UNCITED_CHECKABLE_CLAIM:

~~~text
Accuracy was 99, see nothing.
Accuracy was 99, per nothing.
Accuracy was 99 (imaginary.md).
~~~

Any URL—including a reserved .invalid URL—also counts. URL masking prevents
DOI, arXiv, SHA, and number checks inside it. Thus a fabricated, syntactically
ordinary DOI or arXiv URL receives no mechanical scrutiny.

Sentence splitting makes citation association capitalization-dependent:

~~~text
According to source.md: Accuracy was 99.
~~~

The colon plus uppercase A splits away the locator and emits an uncited
finding. Lowercase accuracy does not split and passes. Conversely,
“Mortality was 99. source.md says nothing.” stays one sentence and lets the
irrelevant later filename cite the claim; capitalizing Source splits it.

The target_text.find(sent, offset) bookkeeping itself stayed synchronized for
leading blank lines, repeated identical sentences, CRLF input, and punctuation
whitespace. I found no concrete offset desynchronization. The confirmed
line-number defect is the deliberately fabricated line 0 contradiction.

### M4. List, table, fence, and locator handling contradict the documentation

**Severity: medium. Certainty: certain. Confidence: high.**

- “12. Apples” is skipped by the number pass as a list marker, then emitted as
  UNCITED_CHECKABLE_CLAIM by the sentence pass.
- “Grounded prose [42].” treats the citation label 42 as an ungrounded count.
- A line whose stripped text begins with a table pipe skips every sentence-level
  self-report/overclaim/citation check.
- Only lines beginning with a code fence are skipped; content inside a fenced
  block is still checked. BUILD_NOTES.md's “fenced code (skipped)” statement is
  false.
- PLACEHOLDER_RE is unbounded: https://todotxt.org/docs is flagged because the
  legitimate hostname contains the substring TODO.
- https://real.invalid/report,. gets no locator finding despite a reserved
  non-public TLD and malformed trailing punctuation.

### M5. OVERCLAIM_RE and negation logic miss absolutes and flag disclaimers

**Severity: medium. Certainty: certain. Confidence: high.**

The following emits no overclaim:

~~~text
It is perfect, cannot fail, has zero errors, and is the world’s first system.
~~~

The regex also misses proved, exhaustively, first-of-its-kind, 100.0%, and
reversed “eliminates hallucinations entirely.” These careful disclaimers emit
OVERCLAIM:

~~~text
Do not use the word “comprehensive” in this report.
This is not necessarily comprehensive.
~~~

Negation is recognized only when a listed token ends immediately before the
match inside a 14-character slice. This is lexical proximity, not negation.

## Verification-claim reproduction

### Fixture

**Finding status: materially false metric claim. Certainty: certain.
Confidence: high.**

The command reproduces the printed 10/10 and 7/7 strings, but H4 shows why those
strings are not recall and precision. Raw detector output is 15 findings, 7
high. Four named grounded controls overlap findings, so “grounded controls left
alone” is false.

### Campaign “after” run

**Finding status: reproduced. Certainty: certain. Confidence: high.**

Using FINDINGS.md as target and exactly SCOPE.md, EVIDENCE_LEDGER.jsonl,
SCREENING.jsonl, and SEARCH_LOG.jsonl as evidence reproduced:

~~~text
total 10 / high 0 / medium 10 / low 0
5 DERIVED_OR_UNGROUNDED_COUNT: 47, 672, 27, 56, 40
4 UNCITED_CHECKABLE_CLAIM: FINDINGS lines 5, 7, 130, 143
1 QUOTE_NOT_FOUND: line 71
~~~

### Campaign “first pass”

**Finding status: not reproducible. Certainty: certain about missing evidence;
confidence: high.**

No pre-fix executable or raw output is shipped. Therefore BUILD_NOTES.md's
“Two runs, both reproducible” is false for the historical 15-total/6-high run.
The narrative is also internally suspect: its listed erroneous classes account
for 5 number + 1 quote + 4 uncited + 2 overclaim = 12 events, while removing
four uncited and two overclaims from 15 should leave 9, not the reported 10.
An in-memory reversal of the four documented code changes produced 12 total /
6 high, not 15 / 6. That does not prove what unretained code once did; it proves
the claimed historical run cannot be independently reproduced from this build.

### Derived counts

**Finding status: the four requested counts are sound; the 672 claim is false.
Certainty: certain. Confidence: high.**

I parsed every nonblank JSONL row and checked identity uniqueness:

| Claim | Independent recomputation | Result |
|---|---:|---|
| search rows | 47 parsed rows, 47 unique query IDs Q001–Q047 | exact |
| context | 27 SCREENING rows with decision=context | exact |
| manifestations | sum of manifestation arrays = 56; 55 works, W033 has two | exact |
| works in C10 | 40 ledger works whose cell_ids contains C10 | exact |
| recorded screening events | sum of SEARCH_LOG results_screened = **672** | exact |

BUILD_NOTES.md lines 59–61 and VERDICTS_AND_ACTIONS.md lines 47–49 say 672 is
not derivable from committed files and is a real campaign finding. That is
plainly wrong: it is the direct sum of a named integer field over all 47 search
rows, exactly matching FINDINGS.md's definition of repeated recorded events.
All five counts, not four, recompute.

### The advertised date fix is still broken

**Finding status: false verification claim. Certainty: certain. Confidence:
high.**

Two of the four remaining campaign UNCITED notices (FINDINGS lines 5 and 143)
are coverage labels whose only Arabic figures are ISO date components.
NUM_RE excludes the four-digit year from sentence-level has_number, but still
sees 07 and 30 as ordinary two-digit counts. These are precisely the date
false positives BUILD_NOTES.md line 52 says were fixed. The statement that all
four remaining uncited notices are defensible is not supportable.

## Design, attribution, and licensing

### D1. Provenance names are accurate, but several adopted-from claims exceed the ledger

**Severity: medium. Certainty: mixed as stated below. Confidence: high unless
noted.**

All 26 W-IDs and repository identities named as specific contributors in
LEADS.md match EVIDENCE_LEDGER.jsonl. The campaign totals and cell assignments
used here also reconcile.

The mechanism traceability is less reliable:

- **W054/W055 relevance ordering — certain.** LEADS.md lines 98–100 jointly
  attributes an explicit relevance check before decomposition to Factcheck-GPT
  and KnowHalu. Ledger W054 records claim extraction, evidence collection, and
  verification but no relevance check; only W055 records an off-target
  relevance check. The official Factcheck-GPT README describes decomposition,
  decontextualization, then check-worthiness—not a relevance check before
  decomposition:
  [official Factcheck-GPT repository](https://github.com/yuxiaw/Factcheck-GPT)
- **W050 span output — traceability failure, not a factual error.** Ledger W050
  does not state span-level output, so LEADS.md lines 137–139 cannot derive that
  claim from the cited ledger row. The current official repository does in fact
  document token/span output in the
  [official LettuceDetect repository](https://github.com/KRLabsOrg/LettuceDetect).
- **W049 model internals — unsupported by the campaign; moderate confidence on
  factual falsity.** Ledger W049 contains no model-internals limitation. The
  current official README demonstrates loading and querying a model, but does
  not by itself establish the stronger wording “needs model internals”:
  [official ContextCite repository](https://github.com/MadryLab/context-cite).
- **“A layered control loop beats any single algorithm” — certain overclaim.**
  LEADS.md line 26 asserts comparative superiority while its own lines 14–17
  and campaign FINDINGS.md say nothing was executed or comparatively tested.
- **C7 “states this directly” — certain overstatement.** SKILL.md lines 27–29
  turns the campaign's caution that checker models *can* share errors/biases
  into a categorical same-session proposition. The operational independence
  rule may be prudent, but the campaign does not establish it directly.
- **“Calibrated actions” and dominant failure distribution — certain unearned
  claims.** The frontmatter says calibrated; LEADS.md says these categories
  dominate long agent-written documents. BUILD_NOTES.md lines 67–73 says the
  real artifact noise rate is unknown and the action policy is untested.

The source campaign supports conceptual leads, not those stronger causal,
comparative, or calibrated claims.

### D2. No specific third-party copying or license violation was established

**Severity: no defect established. Certainty: bounded. Confidence: moderate.**

All 56 campaign manifestations have license_evidence.status=not_coded. A local
long-phrase overlap scan found only three campaign passages in LEADS.md, each
visibly quoted or attributed. I found no indicator that mechanical_pass.py,
run_fixture.py, or prompt text was copied from a third-party project. Ideas,
project names, and repository locators alone do not establish a code-license
obligation.

This is **not license clearance**. The build has no development history or
source-to-source comparison capable of proving the new ATTRIBUTION.md's
categorical “written from scratch/no code copied” statements. The campaign
deliberately did not inspect third-party licenses, and this build itself has no
LICENSE/COPYING/NOTICE file. The current attribution file is useful credit, but
it appeared during this audit and cannot retroactively make the opening
snapshot stable.

## Privacy and unpublished-work exposure

### P1. The opening snapshot leaked private and blind-test information

**Severity: high at opening; partly remediated concurrently. Certainty:
certain. Confidence: high.**

The opening files exposed an author handle, an absolute home checkout, a
private repository identity, a machine label, exact blind-sentinel defect
details, internal campaign names, an internal tool path, and a private
repository URL in the fixture. I am deliberately not reproducing those values
here because this directory may be shared publicly.

The concurrent rewrite removed most exact values and added a privacy-scrub
record. It also proves the initial issue was real. Current files still disclose
that the build derives from a private/unpublished campaign, tie the same author
to both works, describe internal workflow roles and artifact classes, and
describe the existence/nature of a blind sentinel. Decide whether those facts
are intended for public disclosure; they are not necessary to operate the
detector.

### P2. Generated outputs are designed to leak local context

**Severity: high. Certainty: certain. Confidence: high.**

The risk remains in unchanged code and template:

- JSON output records the absolute target path and absolute unreadable evidence
  paths;
- templates/REPORT.md requests absolute target, evidence, and backup paths;
- it requests session/model identity, verbatim target spans, exact evidence
  locators, and even a machine name in the access-gap example;
- section 8 says to log the target but gives no redaction or retention rule; and
- prepolice backups duplicate potentially sensitive material beside the source.

There is no public-output scrub, path relativization, secret/PII review,
minimization rule, or separation between a private evidence ledger and a
shareable report.

## What was genuinely sound

- The executable's SHA-256 stayed stable during the audit.
- The sentence offset/find loop did not desynchronize in concrete probes; line
  0 is a separate explicit bug.
- No exponential defect was established outside CITE_MARKERS's confirmed
  polynomial behavior.
- The requested counts 47, 27, 56, and 40 recompute exactly.
- All specific W-IDs and repository names in LEADS.md resolve to the stated
  campaign ledger identities.
- No specific third-party code/prompt copying or license breach was found in
  the bounded evidence available.
- The prose repeatedly warns that no-finding is not certification. That warning
  is correct, but it does not cure incorrect findings or support the stronger
  “most defects”/“calibrated” claims.

## Minimum release blockers

This is a report-only review; I changed no implementation. Before installation,
at minimum:

1. replace global presence tests with source-scoped, claim-scoped comparisons
   and reject target/evidence overlap;
2. fail closed when the evidence contract is empty, unreadable, binary, or
   wrong-encoding;
3. redesign identifier, number, quote, citation, and self-report tests around
   the counterexamples above;
4. remove CITE_MARKERS's polynomial branches and impose target/extraction
   resource limits;
5. replace the substring fixture oracle with span/code-aware independent tests,
   including the zero-finding fabricated return;
6. define a multi-target, multi-contract judgment ledger and resolve the action
   table contradictions;
7. remove all implicit edit/network authority and add collision, path,
   concurrency, atomicity, and post-edit guards; and
8. freeze a new review candidate, scrub private output fields, and rerun this
   review independently against those exact hashes.
