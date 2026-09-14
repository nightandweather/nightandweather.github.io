# Study note source spec

One Markdown file per course: `study/src/<slug>.md` (slug = lowercase course code, e.g. `cs231n.md`).
The build script (`tools/build_study.py`) turns each file into `study/<slug>.html` and regenerates `study.html`.

## Frontmatter (required, YAML-like, simple `key: value` lines only)

```
---
code: CS231n
title: Deep Learning for Computer Vision
kicker: Computer vision
summary: One sentence, under 160 characters, for the index card and meta description.
official: https://cs231n.stanford.edu/
instructors: Names as listed on the public course website (leave blank if unsure)
based_on: Public lecture sequence, Spring 2024
order: 3
tone: blue
---
```

`tone` is one of: blue, lime, orange, violet, sand, mint, rose, slate.

## Body structure (use exactly these H2 headings, in this order)

1. `## What the course is about` — two or three paragraphs: what problem the course solves, what the reader should know first, how the lectures fit together.
2. `## Lecture notes` — one `### NN · Lecture title` subsection per lecture (12 to 18 lectures), in course order. Each subsection is 150 to 320 words and covers: the core idea in plain words, the one or two equations that matter, what typically goes wrong when applying it, and a bridge to the next lecture. Use a table when comparing two or more methods. Include a short Python/NumPy snippet (under 12 lines) only when it makes the idea concrete.
3. `## Key equations at a glance` — a Markdown table with three columns: Concept | Equation | When it applies.
4. `## Common mistakes` — five to eight bullets, each a concrete mistake and its fix.
5. `## Related courses` — bullets linking to other notes on this site as `[CS229](cs229.html)` style links, one line each on how they connect. Only link to these slugs: cs229, cs230, cs231n, cs224n, cs224w, cs234, cs246, cs336.

## Formatting rules

- Inline math: `$ ... $`. Display math: `$$ ... $$` on its own lines. KaTeX renders it. Never put `*`, `_`-based emphasis, or Markdown links inside math. Use `\_` only if you must write a literal underscore outside math.
- Fenced code blocks with a language tag (` ```python `).
- No raw HTML. No images. No footnotes.
- Plain ASCII quotes are fine. Em dashes are fine.
- Write in English. Plain, direct sentences. Avoid "in this lecture we will".

## Content rules (non-negotiable)

- Original prose written from your own understanding. Do not reproduce slide text, lecture transcripts, or course-note passages. Do not quote the course materials.
- Do not include assignment solutions, problem-set answers, exam questions, or project code from the course. Stanford's Honor Code prohibits publishing them.
- Accuracy over coverage. If you are unsure of a specific fact (a year, a name, a number), leave it out or state it generally. Do not invent citations.
- These are personal study notes, not affiliated with Stanford. The build adds that disclaimer automatically; do not add your own.
- No first-person claims about the author's life, work, or experience. "You" and neutral phrasing only.
