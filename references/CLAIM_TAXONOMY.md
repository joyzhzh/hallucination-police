# Claim taxonomy — what counts as support, per type

A claim type is a contract about what evidence would settle it. Applying the
wrong contract is the most common way a check passes something it should have
caught: a citation is *present*, so the statistic is waved through; a number
*appears somewhere* in the corpus, so it is treated as sourced.

Every unit in the ledger carries exactly one `claim_type`.

---

## `identifier`
A hash, git sha, DOI, arXiv ID, ISBN, issue/PR number, run ID, file path,
version tag, or any other string whose whole purpose is to point at one exact
thing.

**Support means:** the string was read from displayed output or from the object
itself. Not recalled, not reconstructed, not inferred from a pattern.

**Check:** `shasum -a 256 <file>` · `git cat-file -t <sha>` · `git rev-parse` ·
`ls` the path · resolve the DOI. Run the command. Never reason about whether a
hash "looks right" — hashes always look right.

**Fails when:** absent from evidence · present but attached to a different
object · truncated inconsistently · two full values sharing a prefix.

**Never repairable from memory.** If the true value cannot be read from
evidence, the action is `RETRIEVE`, never `REPAIR`.

---

## `statistic`
Any count, proportion, percentage, money figure, duration, rate, or score.

**Support means all five, together:**

| Field | Question |
|-------|----------|
| value | the number itself |
| denominator | out of what |
| universe | over which population or corpus |
| unit | counting what, exactly |
| period | as of when |

A number that matches evidence while its denominator, universe, or period does
not is **not supported** — it is `PARTIALLY_SUPPORTED` at best, and in practice
usually `CONTRADICTED`. "88 of 240 rows" is a different claim from "88 rows",
which is a different claim from "88 of 240 rows *resolved*".

**Fails when:** the number is absent from evidence · the denominator is dropped ·
the universe silently widens ("in the corpus" → "in the literature") · the
period drifts · a rate is recomputed rather than quoted.

Withholding a denominator that the source states is a defect in its own right,
not a stylistic choice.

---

## `quote`
Text presented as someone's words, in quotation marks or block quote.

**Support means:** verbatim presence in the named source, under whitespace and
typographic normalization only. Curly vs straight quotes, en vs em dash, and
line wrapping may differ. **Nothing else may differ** — not a word, not a tense,
not an ellipsis that removes a qualifier.

**Fails when:** not found in the source · found but in a different source than
the one cited · found but the ellipsis or bracket changes the meaning · found in
a quotation *of* the source rather than the source (check the chain).

An ellipsis that removes a hedge is a fabrication with a real substring.

---

## `citation`
An assertion that source S says or supports proposition P.

**Support means three separate things, checked separately and never collapsed:**

1. **Existence** — the locator resolves to a real object.
2. **Identity** — that object is the source claimed: title, author, venue, year,
   version. A real source misidentified is its own defect (`SOURCE_MISIDENTIFIED`),
   and it is the failure mode that survives casual checking, because the link
   works.
3. **Support** — the passage actually entails P, at P's stated strength.

Passing 1 and 2 while failing 3 is the ordinary case, not the rare one.

**Fails when:** dead or fabricated locator · right link, wrong bibliographic
record · source supports a weaker claim · source is a secondary summary being
cited as primary · source is real, correct, and simply does not discuss P.

---

## `attribution-of-position`
"X argues that…", "the reviewer noted…", "per the Operator's ruling…".

**Support means:** the named party actually holds that position, in the cited
place, at the cited strength. Attributing a stronger, cleaner, or more useful
version of someone's position than they stated is the failure here — it is
almost never caught by keyword matching, because the words are all present.

**Fails when:** the party said it hypothetically, in objection, or as a
concession · the position is a synthesis across sources presented as one
person's · the ruling was proposed and never ruled.

For Operator rulings specifically: a ruling is supported only by a record of the
ruling. A proposal, a recommendation, or a prior session's assumption is not a
ruling, however reasonable.

---

## `status`
"X is deprecated", "the repo is private", "CI is green", "the branch is merged",
"that file no longer exists".

**Support means:** observed at a stated time. Status claims decay. A status
claim with no observation timestamp is unsupported by construction.

**Fails when:** no observation time · observation is stale relative to the
document's own use of it · status inferred from a proxy (a README badge is not
CI state).

---

## `self-report`
A claim about work the author says it performed. Mode B's characteristic type,
and the one with the weakest natural evidence.

Examples: "suite 640 OK" · "I verified every row byte-for-byte" · "pushed at
`0b44ad4`" · "all tests pass" · "reproduced the headline number".

**Support means:** captured command output, in the evidence set, showing the
claimed result. Narration is not evidence. An agent stating that it ran
something is exactly as much evidence as an agent stating anything else.

**Fails when:** no captured output · output present but from a different
invocation, path, or commit · the claimed count differs from the output's count
· the command was run but its exit status was not checked · a partial run is
reported as a full one.

This type is why Mode B exists. Treat it at the same severity as `identifier`.

---

## `date`
A date, version date, or temporal ordering.

**Support means:** present in evidence, and consistent with every other date in
the document. A one-day drift is still a defect. A retrieval date that moves by
a single day while quote, locator, citation, and hash all stay correct is the
hardest defect class to see and one of the easiest to introduce, because
everything around it looks right.

---

## `causal` / `mechanism`
"X caused Y", "the fix resolved the failure", "the defect stems from Z".

**Support means:** evidence for the mechanism, not merely for X and Y both
being present. Two grounded facts joined by an ungrounded "because" is an
ungrounded claim wearing two citations.

**Fails when:** the causal link is the author's inference and is not marked as
one · correlation in evidence is reported as cause · a plausible mechanism is
supplied where the source states only an association.

---

## `overclaim` (modifier, not a type)
Applies *on top of* another type when the claim's strength exceeds what its
evidence bounds: "proves", "guarantees", "comprehensive", "exhaustive",
"saturated", "the only", "always", "state of the art", "fully verified".

Action is `SOFTEN`: rewrite to the strength the evidence actually supports.
This is usually a small edit and almost always the right one — the campaign
this skill is built on labels its own coverage "high-coverage, effort-bounded,
not saturated", and that is the register to aim for.

---

## `non-claim`
Opinion, recommendation, plan, question, hedged speculation explicitly marked as
such, and framing prose.

Drops out of verification. **Report the count.** A document that is 90%
non-claim by unit is telling you something, and silently dropping those units
would let a report claim broad coverage of a document it barely checked.

Careful: "I recommend X because Y" contains a `causal` claim about Y. Split it.
