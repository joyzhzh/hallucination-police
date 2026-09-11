# Hallucination Police

An experimental workflow for auditing claims in documents and AI agent output,
with a small, offline Python checker for suspicious identifiers, numbers,
quotations, self-reports, and citation patterns.

**Status: pre-alpha, published for inspection and development.** An adversarial
review on 2026-09-02 rejected this build for installation or trusted use. Some
findings were addressed afterward; substantial blockers remain. Read the
[original review](CODEX_REVIEW.md) and the
[revision record](BUILD_NOTES.md#independent-review-and-revision--2026-09-02).
Publication does not change that assessment.

## What is here

- [Mechanical checker](scripts/mechanical_pass.py): deterministic pattern and
  evidence-presence checks, with line/span findings and JSON output. It does
  not call a model or fetch sources from the network.
- [Skill draft](SKILL.md): an agent workflow for decomposing claims, examining
  evidence, recording verdicts, and proposing actions. Its judgment and repair
  stages have not been validated end to end. Do not install it as a trusted
  auditing skill or enable automatic repairs.
- [Claim taxonomy](references/CLAIM_TAXONOMY.md),
  [action policy](references/VERDICTS_AND_ACTIONS.md), and
  [report template](templates/REPORT.md): design material with unresolved
  issues described in the review.
- [Regression fixture](tests/run_fixture.py): invented inputs that exercise
  known detector behavior.

## Try the fixture

From a local checkout, using Python 3.8 or later:

```bash
python3 tests/run_fixture.py
```

The current fixture checks 10 planted defects, 6 grounded controls, and 3
fail-closed behaviors. These checks are regression tests, not measurements of
precision, recall, or real-world effectiveness.

To inspect the mechanical findings for the same fixture:

```bash
python3 scripts/mechanical_pass.py \
  --target tests/fixture/TARGET.md \
  --evidence tests/fixture/evidence \
  --mode return \
  --json
```

The checker uses Python's standard library. PDF extraction additionally needs
`pdftotext` on PATH; the bundled text fixture does not require it. Document
extraction is limited, and input/resource limits are incomplete. Use small,
non-sensitive local samples while experimenting.

Exit code `0` means the mechanical pass ran, even when it found defects. It is
not a passing audit. Missing usable evidence normally produces exit code `3`;
`--allow-no-evidence` explicitly opts into only evidence-free checks. Other
input failures produce a nonzero exit code.

## Known limits

- **Presence is not support.** A number or identifier found anywhere in the
  evidence can pass despite belonging to an unrelated claim. The checker does
  not establish semantic support, source identity, or truth.
- **Important claims can be missed.** Plain factual assertions and some common
  numeric, citation, and quotation forms fall outside the implemented patterns.
  Zero findings can coexist with fabricated content.
- **The full audit remains a design.** Mechanical JSON contains findings, not
  the complete per-claim, per-target judgment ledger described by the skill.
  The action policy still contains inconsistencies.
- **File-writing safeguards are incomplete.** The CLI's `--out` option can
  overwrite existing files, including evidence discovered through a directory.
  The examples above print to the terminal. The skill's report-writing and
  repair instructions also need collision and authorization fixes.
- **Outputs can disclose input data.** JSON and proposed reports include local
  paths and verbatim document excerpts. Review and redact them before sharing.
  The draft skill's claims of edit or network permission do not confer user
  authorization.

The [release blockers in the review](CODEX_REVIEW.md#minimum-release-blockers)
describe the work needed before trusted installation. The review records an
earlier executable; consult the revision record to distinguish historical
findings from issues still open. No later acceptance review is claimed here.

## Contributing

Useful contributions include small, non-sensitive counterexamples with target
text, evidence text, the command run, expected behavior, and actual findings.
Keep regression results separate from effectiveness claims. Do not include
credentials, private documents, or unredacted audit output in issues or pull
requests.

## License and attribution

This repository is licensed under the [MIT License](LICENSE).
[ATTRIBUTION.md](ATTRIBUTION.md) credits the research projects that informed
the design and describes the limits of the provenance checks. Those projects
retain their own licenses; this repository's license does not cover their
code, models, or datasets.
