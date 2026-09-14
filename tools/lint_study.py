#!/usr/bin/env python3
"""Sanity checks for study/src/*.md before building."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "study" / "src"
REQUIRED_H2 = ["What the course is about", "Lecture notes", "Key equations at a glance", "Common mistakes", "Related courses"]
REQUIRED_META = ["code", "title", "kicker", "summary", "official", "order", "tone"]
SLUGS = {p.stem for p in SRC.glob("*.md") if p.stem != "SPEC"}

problems = 0
for path in sorted(SRC.glob("*.md")):
    if path.stem == "SPEC":
        continue
    text = path.read_text()
    errs = []
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l) if m else {}
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    for k in REQUIRED_META:
        if not meta.get(k):
            errs.append(f"missing frontmatter key: {k}")
    if len(meta.get("summary", "")) > 170:
        errs.append(f"summary too long ({len(meta['summary'])} chars)")
    h2s = re.findall(r"^## (.+)$", text, re.M)
    if h2s != REQUIRED_H2:
        errs.append(f"H2 sequence is {h2s}")
    h3s = re.findall(r"^### (.+)$", text, re.M)
    if not 12 <= len(h3s) <= 18:
        errs.append(f"{len(h3s)} lecture subsections (want 12-18)")
    bad = [h for h in h3s if not re.match(r"\d{2} · ", h)]
    if bad:
        errs.append(f"h3 without 'NN · ' prefix: {bad[:3]}")
    body_no_code = re.sub(r"```.*?```", "", text, flags=re.S)
    if body_no_code.count("$$") % 2:
        errs.append("unbalanced $$")
    for i, line in enumerate(body_no_code.splitlines(), 1):
        stripped = re.sub(r"\$\$.*?\$\$", "", line)
        if stripped.count("$") % 2:
            errs.append(f"line {i}: odd number of $ delimiters")
    if re.search(r"<[a-zA-Z/][^>]*>", body_no_code):
        errs.append("raw HTML tag found")
    for link in re.findall(r"\]\(([^)]+)\)", text):
        if link.endswith(".html") and link[:-5] not in SLUGS:
            errs.append(f"link to unknown course page: {link}")
    words = len(re.sub(r"\$[^$]*\$", "", body_no_code).split())
    print(f"{path.name}: {len(h3s)} lectures, ~{words} words" + (" — OK" if not errs else ""))
    for e in errs:
        print("   !", e)
    problems += len(errs)
sys.exit(1 if problems else 0)
