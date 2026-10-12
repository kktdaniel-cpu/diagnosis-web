"""Permit only the two explicitly approved index UI edits; reject all others."""
import subprocess
from pathlib import Path
base = subprocess.check_output(["git", "show", "origin/main:index.html"]).decode()
current = Path("index.html").read_text()
old = "지금 생활비를 줄인 경우입니다. 소진 나이는 65세 이후 목표 생활비 기준으로 계산하므로 이 변경만으로는 소진 시점이 달라지지 않습니다."
new = "현재 생활비를 변경해 같은 채점 엔진으로 다시 계산한 결과입니다. 65세 이후 목표 생활비는 그대로 유지합니다."
entry = '<!-- Approved precision output UI: existing scoring and print engine unchanged. -->\n<script src="life2-web/review/precision-output/proposal.js"></script>\n'
if base != current:
    assert base.count(old) == 1, "Unexpected production baseline"
    assert entry not in base, "Output entry already installed in baseline"
    expected = base.replace(old, new).replace("</body>", entry + "</body>")
    assert current == expected, "Unapproved production index change"
print("Approved precision UI scope verified")
