#!/usr/bin/env python3
import os
import subprocess
import sys

base = os.environ.get("BASE_SHA")
head = os.environ.get("HEAD_SHA", "HEAD")
if not base:
    print("BASE_SHA is required")
    sys.exit(2)

out = subprocess.check_output(["git", "diff", "--name-only", base, head], text=True)
changed = [x.strip() for x in out.splitlines() if x.strip()]
print("Changed files:")
for p in changed:
    print(" -", p)

# Phase-1 automation may add/update governance, CI, tests and scripts.
# Product files are allowed to be proposed in PRs, but protected semantic files
# below require explicit opt-in via PR label/owner process and are blocked here.
protected_exact = {
    "api/main.py",
    "DIAGNOSIS_SPEC.md",
    "DIAGNOSIS_SPEC_v1.5_LOCK.md",
}
violations = [p for p in changed if p in protected_exact]

if violations:
    print("\nBLOCKED protected files changed without a dedicated approved workflow:")
    for p in violations:
        print(" -", p)
    sys.exit(1)

# Basic operational-file sanity.
for required in ("index.html", "early/index.html"):
    if not os.path.isfile(required) or os.path.getsize(required) == 0:
        print(f"Missing or empty operational file: {required}")
        sys.exit(1)

print("Phase-1 governance scope check: PASS")
