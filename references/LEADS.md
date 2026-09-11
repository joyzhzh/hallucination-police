# Leads — where every part of this skill comes from

Source: a private repository-scouting campaign on LLM hallucination reduction,
frozen **2026-07-30**, read for this build on 2026-09-02. Public credit for the
projects it catalogued is in [`../ATTRIBUTION.md`](../ATTRIBUTION.md).

**What that campaign established, exactly:** that 55 stable public repository
identities exist and *publicly describe* mechanisms that detect, prevent,
mitigate, or evaluate factual hallucination. Its own coverage label is
**"high-coverage, effort-bounded, not saturated as of 2026-07-30"** — it
stopped at a frozen ceiling of 55 while the recency pass was still yielding.
Its evidence is dominated by project-authored repository pages.

**What it did not establish, and this skill must not imply:** that any of these
mechanisms works, transfers, or beats any other. Nothing was cloned, run, or
benchmarked. No score was normalized across projects. Repository presence,
popularity, and citation counts are not effectiveness.

So: these are **leads**, in the campaign's own sense. They tell us what shape a
control should have. They do not tell us it will work here.

---

## The three findings that set this skill's architecture

**1. The repositories cluster into a layered control loop, not into rival
algorithms.** (FINDINGS §1.) The 55 sort into stages — decide whether to answer,
bind generation to evidence, control the decoder, decompose and verify after
generation, attach and validate attribution, gate and recover at runtime,
measure. No stage is the winner, and none is shown to beat another: this is an
observation about how the field is organised, not a comparative result. Nothing
in the campaign was executed or benchmarked.

→ Became: the pipeline in `SKILL.md` §§3–8. Stages 3 (control the decoder) and
the training/editing cell C8 are **out of scope for this skill** — they need
model access we do not have. This skill occupies the post-generation and
runtime-gate portion of the loop, which is the portion available to an
Operator inspecting finished text.

**2. The load-bearing sentence.** From FINDINGS §1:

> "A detector score without a calibrated threshold and explicit block/retry/
> abstain/escalate path observes risk but does not reduce it."

→ Became: `SKILL.md` §6 and `VERDICTS_AND_ACTIONS.md`. Every verdict must
terminate in a named action, and the action depends on destination risk, not on
the verdict alone. This is the rule that stops the skill from being a
noise generator.

**3. "Hallucination" is five non-equivalent targets that disagree.** (FINDINGS
§2.) Parametric truthfulness, contextual faithfulness, world-verifiable
factuality, attribution support, selective behavior. "A response can be
faithful to an incorrect document, factually correct but uncited, consistently
wrong across samples, or appropriately uncertain but still forced to answer."

→ Became: `SKILL.md` §2, the T1–T5 declaration, and the prohibition on a single
"hallucination score" (§9).

---

## Mechanism cells → what this skill takes from each

The campaign's ten frozen cells (`SCOPE.md`), and this skill's disposition.

| Cell | Family | Disposition here |
|------|--------|------------------|
| C1 | Retrieval / evidence grounding | **Adopted as evidence binding** (§5). With the campaign's warning attached: retrieval is not grounding, and a claim faithful to a bad source is still a defect. |
| C2 | Citation / attribution | **Adopted whole** — the three-part citation check (§5) is this cell's central lesson. |
| C3 | Claim decomposition / verification | **Adopted as the core** (§4). Largest cell, 29 repositories. |
| C4 | Constrained / structured generation | **Out of scope.** Needs decoder access. |
| C5 | Uncertainty / abstention | **Adopted narrowly** as target T5 and the `CUT`/`ESCALATE` actions. Sampling-based uncertainty is deliberately excluded — see below. |
| C6 | Tool / graph / database grounding | **Adopted** as evidence tier 2 (filesystem/repo ground truth) and tier 3 (fetch). |
| C7 | Self / cross-model verification | **Adopted as a constraint, not a feature** — §0 and the refutation second pass in §5. |
| C8 | Training / editing / data | **Out of scope.** |
| C9 | Runtime guardrails and recovery | **Adopted** as the action policy and the apply-with-guards rules (§§6–7). |
| C10 | Benchmarks / evaluators | **Not adopted as machinery.** Used only as the source of failure-mode knowledge. This skill is not a benchmark and must not report a score. |

---

## Specific works, and what each one contributed

Cited by the campaign's work IDs. Locators are the campaign's canonical
locators; status is as observed **2026-07-30**, not re-verified today.

### Claim decomposition — the shape of §4

- `W007` **FActScore** (`shmsw25/FActScore`) — atomic-fact decomposition plus
  evidence-based factual *precision*. The precision framing is why this skill
  scores per-claim and never per-document.
- `W009` **VeriScore** (`Yixiao-Song/VeriScore`) — extract only *verifiable*
  claims, then retrieve, then verify. Source of the `type: non-claim` drop-out
  in §4 and the requirement to report how many dropped.
- `W008` **SAFE / long-form-factuality** (`google-deepmind/long-form-factuality`)
  — search-augmented evaluation of long-form output. The long-form assumption
  matches the Operator's actual artifacts (memos, cases, seat returns).
- `W006` **RefChecker** (`amazon-science/RefChecker`) — claim *triplets* as the
  unit. Considered and not adopted: triplets lose the denominator/universe/
  period that the Operator's statistics carry. `CLAIM_TAXONOMY.md` keeps those
  fields instead.
- `W055` **KnowHalu** (`javyduck/KnowHalu`) — a staged pipeline that runs an
  explicit query-relevance check *before* decomposed retrieval. Source of the
  "declare the target first" ordering.
- `W054` **Factcheck-GPT** (`yuxiaw/Factcheck-GPT`) — staged annotation,
  benchmark, and model-assisted checking. *(Correction: an earlier version of
  this file attributed the pre-decomposition relevance check jointly to W054
  and W055. The ledger records that step only for W055.)*
- FINDINGS §3's warning is carried verbatim into §4: decomposition is *itself*
  a model-dependent source of omission and distortion, so the original sentence
  and span stay attached to every unit.

### Attribution — the shape of the three-part citation check in §5

The campaign's §5 separates five questions that are routinely collapsed:
was a source cited · does the passage support the statement · did the model use
it · is the source correctly identified · is the source itself true.

- `W041` **ALCE** (`princeton-nlp/ALCE`) — citation-supported generation and
  automatic citation evaluation.
- `W042` **AttrScore** / `W043` **AttributionBench** (`OSU-NLP-Group`) —
  validating claim↔reference support as a task distinct from citation presence.
- `W045` **AIS** (`google-research-datasets/AIS`) — attributable-to-identified-
  sources; the "identified" half is why `SOURCE_MISIDENTIFIED` is its own
  verdict rather than a flavor of unsupported.
- `W053` **refchecker** (`markrussinovich/refchecker`) — scholarly reference
  resolution and *fabrication* checking. This is the closest existing thing to
  what the Operator needs for citation-bearing academic drafts, and the direct
  ancestor of the `SOURCE_NOT_FOUND` verdict.
- `W044` **LongCite** (`THUDM/LongCite`) — fine-grained citation at long
  context. Relevant to case-length documents.
- `W049` **ContextCite** (`MadryLab/context-cite`) — which context actually
  *influenced* a statement. Noted as a lead not taken: it requires running a
  model over the generation, which this skill does not do. *(Correction: an
  earlier version said it "needs model internals". The ledger records no such
  limitation, and that stronger wording was not supported.)*

### Verification without a model in the loop — the shape of §3

Nothing in the 55 does the deterministic tier the way this skill does, because
the campaign's corpus is research machinery and this is a personal control. The
nearest neighbours:

- `W012` **MiniCheck** (`Liyan06/MiniCheck`) — cheap document-grounded
  factuality classification. Establishes that a cheap tier before an expensive
  one is a real design, not a shortcut.
- `W050` **LettuceDetect** (`KRLabsOrg/LettuceDetect`) — lightweight RAG
  hallucination detection and triplet checking. Reporting a line *and span* in
  §3 was inspired by span-level detectors of this class; note the campaign
  ledger records only "lightweight detection models and triplet checking" for
  this work, so the span attribution is not traceable to the cited row.
- `W047` **AlignScore** (`yuh-zha/AlignScore`), `W048` **SummaC**
  (`tingofurro/summac`), `W046` **QAFactEval** (`salesforce/QAFactEval`) —
  entailment/QA-based consistency scoring. Available if a local model tier is
  ever added; not required for the mechanical tier.

The mechanical tier's actual content — ungrounded identifiers, ungrounded
numbers, missing quotes, unbacked self-reports — does not come from the campaign
at all. It comes from a handful of defect shapes the author had repeatedly seen
in long agent-written documents: a hash or commit id written from memory rather
than read from output, a figure that drifts from its source, a denominator
quietly dropped, and a claim about work performed with no captured output
behind it. Those shapes are what the tier targets. Nothing here measures how
often they occur relative to other defects, so this is a starting hypothesis,
not a calibration.

### Self-checking — adopted as a prohibition

- `W013` **SelfCheckGPT** (`potsawee/selfcheckgpt`) — black-box resampling
  consistency.
- `W014` **semantic_uncertainty** (`jlko/semantic_uncertainty`), `W015`
  **semantic-entropy-probes** (`OATML/semantic-entropy-probes`).
- `W016` **UQLM** (`cvs-health/uqlm`) — uncertainty scoring, ensembles,
  calibration, score-guided selection.

**Deliberately not adopted as a signal.** FINDINGS §4: "No signal is a truth
oracle. Repeated samples can agree on the same falsehood; probes may not
transfer; thresholds drift." Resampling agreement would make this skill *feel*
more confident without making it more correct — precisely the failure the
Operator's "don't grade your own work" doctrine exists to prevent. What survives
is the cell's *negative* lesson: §0 (no self-audit), and the refutation-framed
second pass in §5, which is a diversity mechanism rather than a consensus one.

### Runtime gating — the shape of §§6–7

- `W039` **Granite Guardian** (`ibm-granite/granite-guardian`) and `W040`
  **NeMo Guardrails** (`NVIDIA-NeMo/Guardrails`) — detectors wired to rails.
- `W038` **LLM Guard** (`protectai/llm-guard`) — factual-consistency scanner
  inside a guardrail stack.
- `W011` **OpenFactCheck** (`mbzuai-nlp/openfactcheck`) — modular fact-checking
  with pluggable stages; the modular framing is why §3 and §5 are separable
  tiers rather than one monolith.

### Adverse evidence — why this skill refuses to certify

Campaign Pass A (`Q038`–`Q041`) upgraded the limitations, and those upgrades
are load-bearing here:

- LLM-as-judge shows position, verbosity, self-preference, prompt, and variance
  effects → §5's second pass is framed to refute, and §9 forbids a score.
- Public benchmarks can be contaminated or tuned against → this skill reports
  no benchmark number about itself.
- RAG detector thresholds and labels fail to transfer across domains → the
  action policy is a stated table the Operator can edit, not a learned
  threshold.
- Source attribution and factual truth must be evaluated separately → the
  three-part citation check.
- Abstention requires scenario-specific, utility-aware calibration → the
  destination-risk axis in `VERDICTS_AND_ACTIONS.md`.

---

## Leads left on the table

Recorded so a later session does not re-derive them.

- **Pass B tail** (campaign FINDINGS, "thin cells and recency"): MARCH,
  AbstentionBench, HalluEditBench, VeriFastScore, SelfCite, HALoGEN. Surfaced
  after the 55-identity ceiling, so they were never deep-coded. If this skill
  needs a local scoring model, that list is the first place to look — and it
  needs its own verification pass, since the campaign only saw them as names.
- **Nine unresolved leads** in the campaign that never had repository identity
  confirmed.
- **A local entailment tier.** MiniCheck/AlignScore/LettuceDetect-class models
  could sit between §3 and §5 and cut token cost on long documents. Not built:
  it adds a dependency and an install, and the observed failure distribution is
  dominated by the mechanical tier's categories.
- **Adjacent campaigns not read for this build.** Several exist on neighbouring
  topics and each likely carries usable machinery. This build read one campaign,
  as instructed.
- **An existing domain-specific citation checker** already covers
  registry-backed citation verification for one particular document pipeline.
  It was not merged in. If this skill is ever pointed at material that pipeline
  owns, reconcile the two rather than running both.
