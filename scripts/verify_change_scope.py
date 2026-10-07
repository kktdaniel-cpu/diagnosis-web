#!/usr/bin/env python3
import os
import subprocess
import sys

base = os.environ.get("BASE_SHA")
head = os.environ.get("HEAD_SHA", "HEAD")
if not base:
    print("BASE_SHA is required")
    sys.exit(2)

changed = [
    x.strip()
    for x in subprocess.check_output(
        ["git", "diff", "--name-only", base, head], text=True
    ).splitlines()
    if x.strip()
]

print("Changed files:")
for p in changed:
    print(" -", p)

# Product patch allowlist for diagnosis-web.
# Automation-policy files are intentionally NOT in this list.
allowed_exact = {
    "index.html",
    "early/index.html",
}
allowed_prefixes = (
    "pro/tests/",
    "tests/",
)

# Files that govern the gate itself. General product PRs must not touch them.
policy_exact = {
    ".github/workflows/diagnosis-verify.yml",
    ".github/workflows/policy-guard.yml",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/diagnosis-change.yml",
    "scripts/verify_change_scope.py",
    "scripts/verify_static_contracts.py",
    "docs/GOVERNANCE.md",
    "docs/RELEASE_CHECKLIST.md",
}

# Bootstrap/maintenance PRs may contain only policy files and no product files.
policy_changed = [p for p in changed if p in policy_exact or p.startswith(".github/")]
product_changed = [p for p in changed if p not in policy_changed]

if policy_changed and product_changed:
    print("\nBLOCKED: automation-policy files and product files are mixed in one PR.")
    print("Split automation maintenance from product patch work.")
    sys.exit(1)

if policy_changed:
    print("\nAutomation-maintenance change detected.")
    print("This PR requires separate owner review and must not be treated as a normal product patch.")
else:
    violations = [
        p for p in product_changed
        if p not in allowed_exact and not any(p.startswith(prefix) for prefix in allowed_prefixes)
    ]
    if violations:
        print("\nBLOCKED: changed files are outside the committed product allowlist:")
        for p in violations:
            print(" -", p)
        sys.exit(1)

for required in ("index.html", "early/index.html"):
    if not os.path.isfile(required) or os.path.getsize(required) == 0:
        print(f"Missing or empty operational file: {required}")
        sys.exit(1)

print("Governed change scope: PASS")
