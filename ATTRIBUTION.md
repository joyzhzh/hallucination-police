# Attribution

This skill is a design synthesis. Its ideas come from published research
projects; its code does not.

## What was and was not taken

**No code was copied.** `scripts/mechanical_pass.py` and `tests/run_fixture.py`
were written from scratch for this build, in Python, using only the standard
library. Nothing was cloned, downloaded, installed, or executed from any project
below.

That is the author's account of how the files came to exist, and this
repository has no development history that could prove it to you. What *has*
been checked, by an independent reviewer with access to the source material: a
long-phrase overlap scan found no indicator that the Python files or the prose
copied third-party source or prompt text. That scan compared against the
material available to the reviewer — it did not compare against the 26 projects
themselves, so it cannot prove originality, only fail to contradict it. The
reviewer's own words: this is **not license clearance**. Treat the statement as
a claim with a bounded check behind it, not as a guarantee.

**What was taken is conceptual**, and it is the part worth crediting: the idea
of decomposing an answer into atomic checkable claims; the separation of
citation *presence* from citation *support* from source *identity*; the
insistence that a detector signal must terminate in an action; the observation
that a checker sharing the generator's context shares its errors. These are
other people's insights. This build rearranges them for one narrow purpose and
claims no novelty in them.

**No effectiveness claim is transferred.** Nothing here was benchmarked against
these projects or validated using them. Listing a project below says only that
its published approach informed a design decision — never that this skill
performs comparably, or that the project endorses this use.

## How these projects were identified

Through a private repository-scouting campaign run on **2026-07-30**, which
catalogued 55 public repositories implementing hallucination-related mechanisms.
That campaign's own coverage label was *"high-coverage, effort-bounded, not
saturated"* — it stopped at a ceiling while still finding new work, so this is
not a complete or representative census of the field, and absence from this list
means nothing.

The campaign's evidence is predominantly project-authored repository pages. It
established that these mechanisms are *publicly described*, not that they work.

## Projects credited

Locators as recorded **2026-07-30**. They have not been re-verified since, and
repositories move, rename, and archive.

### Claim decomposition and verification

| Project | Locator |
|---|---|
| FActScore | https://github.com/shmsw25/FActScore |
| VeriScore | https://github.com/Yixiao-Song/VeriScore |
| SAFE / long-form-factuality | https://github.com/google-deepmind/long-form-factuality |
| RefChecker | https://github.com/amazon-science/RefChecker |
| Factcheck-GPT | https://github.com/yuxiaw/Factcheck-GPT |
| KnowHalu | https://github.com/javyduck/KnowHalu |
| OpenFactCheck | https://github.com/mbzuai-nlp/openfactcheck |
| MiniCheck | https://github.com/Liyan06/MiniCheck |

### Citation and attribution

| Project | Locator |
|---|---|
| ALCE | https://github.com/princeton-nlp/ALCE |
| AttrScore | https://github.com/OSU-NLP-Group/AttrScore |
| AttributionBench | https://github.com/OSU-NLP-Group/AttributionBench |
| AIS | https://github.com/google-research-datasets/AIS |
| LongCite | https://github.com/THUDM/LongCite |
| ContextCite | https://github.com/MadryLab/context-cite |
| refchecker (scholarly references) | https://github.com/markrussinovich/refchecker |

### Consistency and entailment scoring

| Project | Locator |
|---|---|
| AlignScore | https://github.com/yuh-zha/AlignScore |
| SummaC | https://github.com/tingofurro/summac |
| QAFactEval | https://github.com/salesforce/QAFactEval |
| LettuceDetect | https://github.com/KRLabsOrg/LettuceDetect |

### Uncertainty and abstention — cited as a prohibition

These informed a decision *not* to build something. See `references/LEADS.md`.

| Project | Locator |
|---|---|
| SelfCheckGPT | https://github.com/potsawee/selfcheckgpt |
| semantic_uncertainty | https://github.com/jlko/semantic_uncertainty |
| semantic-entropy-probes | https://github.com/OATML/semantic-entropy-probes |
| UQLM | https://github.com/cvs-health/uqlm |

### Runtime guardrails

| Project | Locator |
|---|---|
| NeMo Guardrails | https://github.com/NVIDIA-NeMo/Guardrails |
| Granite Guardian | https://github.com/ibm-granite/granite-guardian |
| LLM Guard | https://github.com/protectai/llm-guard |

## Licensing

**Licenses were not verified for any project listed above.** The source campaign
recorded license status as `not_coded` for every one of the 55 works, by design
— it was mapping mechanisms, not clearing reuse.

This creates no obligation for *this* repository, because no material from those
projects is redistributed here. It does create an obligation for you: **if you
copy code, weights, datasets, or prompts from any project above, read its
license first.** Do not infer a license from this file, from a sibling project,
from an organization, or from a paper. Several are corporate or lab
repositories where the terms are not the ones you would guess.

## This repository's own licence

**MIT.** See [LICENSE](LICENSE) for the full terms. The author selected this
licence for public distribution on 2026-09-12. Earlier private snapshots had
no licence; the historical review records that earlier state.

This licence covers this repository's material. It does not license any
third-party code, models, datasets, or prompts linked from the attribution
tables above.

## Quoted material

`references/LEADS.md` quotes short passages from the private campaign's own
synthesis document. Those are the campaign author's words, quoted with
attribution, and reproduced here with permission — the author of this
repository is the author of that campaign. `VERDICTS_AND_ACTIONS.md` quotes
only an earlier version of itself.

No text is quoted from any third-party project. Project names, mechanism
summaries, and repository locators are factual references, not reproductions.

## Corrections

If you maintain a project listed here and the characterization is wrong, or you
would rather not be listed, that is a defect in this file and it will be fixed.
