#!/usr/bin/env python3
from pathlib import Path
import re
import sys

FILES = [Path("index.html"), Path("early/index.html")]
errors = []

for path in FILES:
    if not path.exists():
        errors.append(f"{path}: missing")
        continue

    text = path.read_text(encoding="utf-8", errors="strict")

    # #41/#45: stale keep90 label/value combinations must not reappear.
    if "90세까지 버틴 시나리오" in text:
        errors.append(f"{path}: stale keep90 label found")
    if "null / 3" in text:
        errors.append(f"{path}: forbidden null / 3 literal found")
    if re.search(r"keep\s*\+\s*['\"]\s*/\s*3", text):
        errors.append(f"{path}: direct keep + '/ 3' composition found")

    # Canonical helper presence.
    for needle in ("l2pKeep90Label()", "l2pKeep90Txt(R)", "l2pScenTxt(R,'p')", "l2pScenTxt(R,'a')", "l2pScenTxt(R,'o')"):
        if needle not in text:
            errors.append(f"{path}: expected canonical helper call missing: {needle}")

    # #46: scenAges must not use coercive isFinite-based age formatting.
    m = re.search(r"function\s+scenAges\s*\([^)]*\)\s*\{(.*?)\n\s*\}", text, flags=re.S)
    if m and "isFinite(" in m.group(1):
        errors.append(f"{path}: scenAges contains coercive isFinite() formatting")

    # #50: page1 must not contain the old undeclared dep comparison/string use.
    page1 = re.search(r"function\s+page1\s*\([^)]*\)\s*\{(.*?)(?=\n\s*function\s+page2\b)", text, flags=re.S)
    if page1:
        body = page1.group(1)
        if "dep>=85" in body:
            errors.append(f"{path}: stale page1 dep>=85 reference found")
        if re.search(r"['\"]\+dep\+['\"]세", body):
            errors.append(f"{path}: stale page1 dep age interpolation found")

if errors:
    print("STATIC NEGATIVE CONTRACT: FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("STATIC NEGATIVE CONTRACT: PASS")
print("LEVEL A only — diagnostic validity/LEVEL B is not assessed.")
