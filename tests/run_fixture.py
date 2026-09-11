#!/usr/bin/env python3
"""Behaviour tests for the mechanical tier.

These are **regression checks, not measurements.** An earlier version of this
file printed "10/10 recall, 7/7 precision" over a substring search of finding
messages. Those were not recall and precision:

  - the oracle concatenated only each finding's `detail` string and searched
    for hand-picked substrings, so one finding could satisfy two labels and a
    label could be satisfied by an unrelated finding;
  - its "grounded control left alone" test never checked whether a finding's
    span *contained* the control. Four of seven controls sat inside emitted
    findings while the test reported all seven untouched.

The checks below are span-aware and code-aware. They still do not measure
recall or precision, because the fixture is small, adversarial by construction,
and written by the same author as the detector. Read them as "the known
failures stay fixed", nothing more.

  python3 tests/run_fixture.py

Exit 0 = all checks pass.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "mechanical_pass.py")
TARGET = os.path.join(HERE, "fixture", "TARGET.md")
EVIDENCE = os.path.join(HERE, "fixture", "evidence")

# Planted defect -> (substring locating it in the target, expected code).
# Anchored to a span in the document, so a finding elsewhere cannot satisfy it.
PLANTED = [
    ("fabricated sha256",
     "2fdf44ccd24597f7199f797fe6a3810314eb343b101d6bde4f23a03135c15476",
     "UNGROUNDED_IDENTIFIER"),
    ("fabricated git sha", "bceb4b2", "UNGROUNDED_IDENTIFIER"),
    ("fabricated percentage", "74.2%", "UNGROUNDED_NUMBER"),
    ("fabricated count 1180", "1180", "DERIVED_OR_UNGROUNDED_COUNT"),
    ("fabricated count 640", "640 OK", "DERIVED_OR_UNGROUNDED_COUNT"),
    ("quote absent from source",
     "this pipeline eliminates hallucination", "QUOTE_NOT_FOUND"),
    ("self-report 'I ran'", "I ran the suite", "SELF_REPORT_UNBACKED"),
    ("self-report 'Suite 640 OK'", "Suite 640 OK", "SELF_REPORT_UNBACKED"),
    ("placeholder locator", "example.com", "LOCATOR_SUSPECT"),
    ("overclaim cluster", "comprehensive map", "OVERCLAIM"),
]

# Grounded controls: present in the evidence, so no *grounding* finding may
# accuse them. An UNCITED_CHECKABLE_CLAIM over the sentence is allowed - it is
# a claim about missing citation, not about the value being wrong.
GROUNDING_CODES = {
    "UNGROUNDED_IDENTIFIER", "UNGROUNDED_NUMBER",
    "DERIVED_OR_UNGROUNDED_COUNT", "QUOTE_NOT_FOUND",
    "INTERNAL_CONTRADICTION", "LOCATOR_SUSPECT",
}
CONTROLS = [
    ("grounded sha256 from run_output.txt",
     "44b734e5c6fd8d5e51c0c5b2b19a4c7dbd1400f228ff325693193147ad85e697"),
    ("grounded git sha 0b44ad4", "0b44ad4"),
    ("grounded figure 88", "88 of 240"),
    ("grounded figure 36.7%", "36.7%"),
    ("grounded figure 312", "312 tests"),
    ("verbatim quote from source.md", "omission and distortion"),
]


def detect(target, evidence, mode="return", extra=None):
    cmd = [sys.executable, SCRIPT, "--target", target, "--mode", mode,
           "--json"]
    for e in (evidence if isinstance(evidence, list) else [evidence]):
        cmd += ["--evidence", e]
    cmd += extra or []
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res


def main():
    failures = []
    res = detect(TARGET, EVIDENCE)
    if res.returncode != 0:
        print("FAIL: detector exited %d\n%s" % (res.returncode, res.stderr))
        return 1
    findings = json.loads(res.stdout)["findings"]
    text = open(TARGET).read()

    def covering(idx, codes=None):
        return [f for f in findings
                if f["span"][0] <= idx < f["span"][1]
                and (codes is None or f["code"] in codes)]

    print("== planted defects: each must be caught by a span-covering finding "
          "of the right code ==")
    for label, needle, code in PLANTED:
        i = text.find(needle)
        if i < 0:
            failures.append("fixture no longer contains %r" % needle)
            print("  ERROR   fixture missing: %s" % label)
            continue
        hits = covering(i, {code})
        if not hits:
            near = [f["code"] for f in covering(i)]
            failures.append("missed %s" % label)
            print("  MISSED  %-34s expected %s%s" % (
                label, code,
                (" (got %s)" % ", ".join(near)) if near else " (nothing)"))
        else:
            print("  caught  %-34s %s" % (label, hits[0]["finding_id"]))

    print("\n== grounded controls: no GROUNDING finding may cover them ==")
    for label, needle in CONTROLS:
        i = text.find(needle)
        if i < 0:
            failures.append("fixture no longer contains %r" % needle)
            continue
        bad = covering(i, GROUNDING_CODES)
        if bad:
            failures.append("false positive on %s" % label)
            print("  ACCUSED %-34s by %s" % (
                label, ", ".join(f["finding_id"] + ":" + f["code"]
                                 for f in bad)))
        else:
            other = covering(i)
            note = ("  [non-grounding: %s]"
                    % ", ".join(sorted({f["code"] for f in other}))
                    ) if other else ""
            print("  clean   %-34s%s" % (label, note))

    print("\n== fail-closed behaviour ==")
    some_evidence = os.path.join(HERE, "fixture", "evidence", "run_output.txt")
    r = detect(TARGET, "/nonexistent/path/xyz")
    if r.returncode == 3:
        print("  ok      missing evidence exits 3 rather than reporting clean")
    else:
        failures.append("no-evidence run did not fail closed")
        print("  FAIL    missing evidence exited %d" % r.returncode)

    r = detect(TARGET, some_evidence, extra=["--out", TARGET])
    if r.returncode == 2 and "refusing" in r.stderr:
        print("  ok      --out pointed at the target is refused")
    else:
        failures.append("--out collision not refused")
        print("  FAIL    --out collision exited %d" % r.returncode)

    r = detect(TARGET, TARGET)
    hdr = json.loads(r.stdout)["header"] if r.returncode == 0 else {}
    if r.returncode == 3 or hdr.get("evidence_excluded_as_target"):
        print("  ok      target excluded from its own evidence set")
    else:
        failures.append("target not excluded from own evidence")
        print("  FAIL    target was accepted as its own evidence")

    print("\n" + "-" * 70)
    if failures:
        print("FAIL — %d check(s):" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("PASS — %d planted defects caught, %d controls unaccused, "
          "3 fail-closed behaviours held." % (len(PLANTED), len(CONTROLS)))
    print("Regression checks only. Not a recall or precision measurement, and "
          "not evidence the detector\nfinds defects outside these shapes — see "
          "BUILD_NOTES.md for what it demonstrably misses.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
