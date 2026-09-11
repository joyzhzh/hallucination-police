# Verdicts and actions

A verdict without an action observes risk. This file is the policy that turns
one into the other. It is a **stated table, not a learned threshold** —
deliberately, because detector thresholds do not transfer across domains, and a
table the Operator can read and edit is honest about being a judgment call.

Edit this file when the policy is wrong. That is what it is for.

---

## The eight verdicts

| Verdict | Means | Does **not** mean |
|---------|-------|-------------------|
| `SUPPORTED` | Evidence found and it entails the claim at the stated strength. | The claim is true. The evidence could be wrong. |
| `PARTIALLY_SUPPORTED` | Evidence supports a weaker version — narrower universe, softer verb, smaller scope. | Close enough. |
| `UNSUPPORTED` | Evidence was found and inspected; it does not entail the claim. | The claim is false. |
| `CONTRADICTED` | Evidence asserts something incompatible with the claim. | — |
| `SOURCE_NOT_FOUND` | The locator does not resolve, or resolves to nothing matching. | The source does not exist — it may have moved. Say which you established. |
| `SOURCE_MISIDENTIFIED` | The source resolves, but is not the source claimed. | A citation-format nit. The reader would land on the wrong object. |
| `NO_EVIDENCE_OFFERED` | The claim is asserted bare, with no locator at all. | Unsupported. Nothing was checked. |
| `UNVERIFIABLE_HERE` | Checking needs access this session does not have. | Unsupported. **Never** report it as one. |

`UNVERIFIABLE_HERE` must carry what access would settle it. "Needs the raw
corpus, which is on the other machine" is a finding. "Could not verify" is not.

---

## The seven actions

| Action | What you do |
|--------|-------------|
| `PASS` | Nothing. Record it. |
| `SOFTEN` | Rewrite the claim down to exactly what the evidence supports. Narrow the universe, hedge the verb, restore the denominator. |
| `REPAIR` | Replace a wrong value with the right one, **copied from evidence you opened**. |
| `RECOMPUTE` | Derive the count from evidence already in hand, then compare. The evidence is present; only the arithmetic is missing. |
| `RETRIEVE` | Go get evidence you do not have, then re-verdict. |
| `CUT` | The claim cannot stand and cannot be softened into one that can. |
| `ESCALATE` | Operator ruling required. Stop here. |

`RECOMPUTE` earns its own slot because derived counts are the single most
common "absent from evidence" hit in a well-kept document, and they are usually
*correct*. Checked against a real research document during this build: five
summary counts appeared in none of its evidence files, and **all five recompute
exactly** — four by counting rows, the fifth by summing a per-row field.
Treating that class as `REPAIR` would invite a model to overwrite correct
arithmetic with a guess.

> An earlier version of this file said the fifth count was "not derivable from
> the committed files at all" and called that a finding about the document.
> That was false, and it was produced the way hallucinations usually are: the
> author checked four counts, failed to find the fifth by the same method, and
> asserted a negative it had never tested. The correct verdict on an unlocated
> count is `RECOMPUTE`, not a claim that it cannot be computed.

---

## Destination risk

Ask, or infer from where the file lives. When genuinely unclear, assume
`sent-to-a-person` — it is the common case and errs toward strictness.

| Tier | Meaning |
|------|---------|
| `private-note` | Scratch, working memo, notes to self. Nobody else reads it. |
| `internal-landing` | Committed to a repo, entered into a record, handed to a successor session. **Persists, and later work will trust it.** |
| `sent-to-a-person` | Email, DM, review return, anything a named human receives. |
| `published` | Website, paper, case, submission, anything with an audience. |

`internal-landing` is stricter than it looks. A confabulated hash in a landed
handoff is read as fact by every session after it.

---

## Policy table

Read as: verdict × type → action, at the given destination tier. Where one cell
lists two actions, the first applies at `private-note`/`internal-landing`, the
second at `sent-to-a-person`/`published`.

| Verdict | `identifier` | `self-report` | `statistic` / `date` | `quote` | `citation` | `attribution-of-position` | `causal` | `status` |
|---|---|---|---|---|---|---|---|---|
| `SUPPORTED` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| `PARTIALLY_SUPPORTED` | ESCALATE | RETRIEVE | SOFTEN | REPAIR | SOFTEN | SOFTEN | SOFTEN | SOFTEN |
| `UNSUPPORTED` | RETRIEVE | RETRIEVE | SOFTEN / CUT | CUT | SOFTEN / CUT | SOFTEN / CUT | SOFTEN | SOFTEN / CUT |
| `CONTRADICTED` | REPAIR | ESCALATE | REPAIR | REPAIR | REPAIR | ESCALATE | ESCALATE | REPAIR |
| `SOURCE_NOT_FOUND` | RETRIEVE | RETRIEVE | RETRIEVE / CUT | CUT | RETRIEVE / CUT | RETRIEVE / CUT | RETRIEVE | RETRIEVE |
| `SOURCE_MISIDENTIFIED` | REPAIR | ESCALATE | REPAIR | REPAIR | REPAIR | REPAIR | REPAIR | REPAIR |
| `NO_EVIDENCE_OFFERED` | RETRIEVE | RETRIEVE | RETRIEVE / SOFTEN | RETRIEVE / CUT | RETRIEVE | SOFTEN | SOFTEN | RETRIEVE |
| `UNVERIFIABLE_HERE` | ESCALATE | ESCALATE | ESCALATE | ESCALATE | ESCALATE | ESCALATE | SOFTEN | SOFTEN |

The `overclaim` modifier always yields `SOFTEN`, on top of whatever the
underlying type's action is.

### Why the identifier column is harsh

Two reasons. An identifier is either exactly right or useless — there is no
weaker version to soften to, so `SOFTEN` never applies. And a wrong identifier
propagates silently: it looks correct forever, and every downstream session
inherits it. `PARTIALLY_SUPPORTED` on an identifier means the prefix matched
but the full value did not, which is a prefix collision or a truncation error —
either way, an Operator ruling, not a guess.

### Why `self-report` never gets `REPAIR`

Repairing a self-report means writing a *different* claim about work you did not
witness. The only honest moves are: fetch the captured output (`RETRIEVE`), or
hand it to the Operator (`ESCALATE`). If the output cannot be produced, the
claim is not repairable — it is unsupported, and the author has to re-run the
work, which is a decision above this skill's authority.

---

## What may be applied automatically

Ruled by the Operator: this skill may apply fixes. Fenced to:

- `REPAIR` and `SOFTEN` only.
- `high` confidence only.
- Replacement text **copied from evidence actually opened**, never composed.
- Never `CUT` — deleting a claim changes the argument. Propose it.
- Never in a governing document — `CLAUDE.md`, `protocols/`, any `SKILL.md`,
  ratified specs, acceptance and verdict records. Report only.
- Never without a recoverable prior version (clean git tree, or a
  `.prepolice-<timestamp>` copy written first).
- Every applied edit reported with before, after, and the licensing locator.

`RECOMPUTE` is auto-runnable — count the rows — but its *result* re-enters the
table as a fresh verdict. Recomputing is not repairing: if the recount differs
from the document, that is a `CONTRADICTED` statistic, and the repair follows
the normal rules.

`RETRIEVE` and `ESCALATE` are by definition not auto-applicable: one needs more
evidence, the other needs the Operator.

---

## Severity, for ordering the report

Severity orders what the Operator reads first. It is not the action.

| Severity | Which findings |
|----------|----------------|
| `high` | Any `identifier` or `self-report` defect · `CONTRADICTED` anything · `SOURCE_NOT_FOUND` · `SOURCE_MISIDENTIFIED` · `QUOTE_NOT_FOUND` · a statistic absent from evidence |
| `medium` | `PARTIALLY_SUPPORTED` · `NO_EVIDENCE_OFFERED` on a checkable claim · date drift · uncited checkable claims |
| `low` | `overclaim` · style-level hedging · `UNVERIFIABLE_HERE` where the access gap is expected and stated |

At `published`, promote every `medium` to `high` for `citation` and `quote`
types. A reader who follows a citation and finds it does not say the thing is
the reputational failure this whole skill exists to prevent.
