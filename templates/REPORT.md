# Hallucination audit — <TARGET FILENAME>

| | |
|---|---|
| Target | `<absolute path>` |
| Target hash | `<sha256 of the file as audited>` |
| Mode | DOCUMENT / RETURN |
| Declared targets | T2 contextual faithfulness · T4 attribution support · … |
| Destination risk | private-note / internal-landing / sent-to-a-person / published |
| Evidence set | `<paths>` — N files, M chars |
| Evidence not readable | `<path>: <reason>` — or `none` |
| Auditor | `<session/model>` — did not author the target |
| Run at | `<UTC>` |

## Verdict counts

| Verdict | N |
|---|---:|
| SUPPORTED | |
| PARTIALLY_SUPPORTED | |
| UNSUPPORTED | |
| CONTRADICTED | |
| SOURCE_NOT_FOUND | |
| SOURCE_MISIDENTIFIED | |
| NO_EVIDENCE_OFFERED | |
| UNVERIFIABLE_HERE | |
| **checkable units** | |
| non-claim units dropped | |

| Action | Proposed | Applied |
|---|---:|---:|
| PASS | | — |
| SOFTEN | | |
| REPAIR | | |
| RECOMPUTE | | |
| RETRIEVE | | — |
| CUT | | 0 (never auto-applied) |
| ESCALATE | | — |

## Defects — severity order

> One block per defect. Highest severity first, **not** document order.

### <ID> · <CODE> · <severity> · line <N>

**Claim.** <the unit, as decomposed>
**As written.** <verbatim span from the target>
**Type.** <claim_type>
**Verdict.** <VERDICT> — confidence <high/moderate/low/unknown>
**Evidence.** <what was opened, tier 1–4, exact locator, what it says>
**Second pass.** <refutation-framed re-check result, for high-risk units — or `not required`>
**Action.** <ACTION>
**Repair.** <paste-ready replacement text, value copied from the evidence above>
**Applied.** yes / no — <if no, why: below confidence bar · CUT · governing doc · needs Operator>

---

## Applied edits

| ID | Line | Before | After | Licensed by |
|---|---|---|---|---|

Prior version preserved at: `<path>.prepolice-<UTC>` — or `clean git tree at <sha>`.

*Nothing was deleted.*

## Not checked, and why

> Mandatory. If this section is empty, state the reason it is empty.

- <unit or region> — <why: no evidence access · paywalled · the source is not on this machine · PDF not text-extractable · out of declared targets>

> Name what access would settle it, not where it lives. A report may be shared;
> do not write machine names, absolute paths, or private project names here.

## Coverage

Checked N units under targets <T…> against the evidence set above.
<K> defects found, <J> at high severity.

Mechanical tier ran whole. Judgment tier covered <scope>.

**This is not a certification.** Absence of a detected defect is not proof of
grounding: units marked SUPPORTED are supported *by the evidence supplied*,
which may itself be wrong, stale, or incomplete. Claims marked
UNVERIFIABLE_HERE were not checked at all. No score is reported, and none of
the five targets stands in for the others.

## Rulings owed

- <anything ESCALATE'd, phrased as a question the Operator can answer>
