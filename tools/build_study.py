#!/usr/bin/env python3
"""Build the Study section: study/src/*.md -> study/*.html + study.html + sitemap entries.

Usage: python3 tools/build_study.py
Requires the `markdown` package (pip install markdown).
"""

from pathlib import Path
import html
import re

import markdown

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "study" / "src"
OUT = ROOT / "study"
BASE = "https://nightandweather.github.io"
AUTHOR = "Kanghoun Lee"

TONES = {
    "blue": "#dff4ff",
    "lime": "#e8f5cf",
    "orange": "#fff0dc",
    "violet": "#f0e8ff",
    "sand": "#f3ead8",
    "mint": "#dcf3ea",
    "rose": "#fbe3e3",
    "slate": "#e3e6ea",
}

KATEX_VERSION = "0.16.11"

HEAD_SCRIPTS = '''  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-3HGZPVGV9N"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag("js", new Date());
    gtag("config", "G-3HGZPVGV9N");
  </script>
  <meta name="google-adsense-account" content="ca-pub-4242632384470714">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4242632384470714" crossorigin="anonymous"></script>'''

FONTS = '''  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap" rel="stylesheet">'''

DISCLAIMER = (
    "Personal study notes written in my own words from publicly available lectures and course pages. "
    "Not affiliated with or endorsed by Stanford University. No assignment solutions are published here."
)


def nav(prefix: str) -> str:
    home = prefix or "./"
    return (
        f'<header class="nav wrap"><a class="wordmark" href="{home}" aria-label="Kanghoun Lee, home">KANGHOUN LEE</a>'
        f'<nav aria-label="Primary navigation"><a href="{prefix}work.html">Work</a><a href="{prefix}experiments.html">Experiments</a>'
        f'<a href="{prefix}field-notes.html">Field Notes</a><a href="{prefix}study.html" aria-current="page">Study</a>'
        f'<a href="{prefix}opportunities.html">Calendar</a><a href="{prefix}rejections.html">Rejections</a></nav></header>'
    )


def footer(prefix: str) -> str:
    home = prefix or "./"
    return (
        f'<footer class="footer"><div class="wrap"><span>&copy; 2026 {AUTHOR} &middot; Seoul</span>'
        f'<nav aria-label="Footer navigation"><a href="{home}#about">About</a><a href="{prefix}study.html">Study</a>'
        f'<a href="https://github.com/nightandweather">GitHub &#8599;</a></nav></div></footer>'
    )


def meta_block(title: str, desc: str, url: str, prefix: str, og_type: str) -> str:
    t = html.escape(title, quote=True)
    d = html.escape(desc, quote=True)
    return f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="description" content="{d}">
  <title>{t} &mdash; {AUTHOR}</title>
  <link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
  <link rel="canonical" href="{url}">
{FONTS}
  <meta property="og:type" content="{og_type}">
  <meta property="og:title" content="{t}">
  <meta property="og:description" content="{d}">
  <meta property="og:image" content="{BASE}/assets/orcaton.jpg">
  <meta property="og:url" content="{url}">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="stylesheet" href="{prefix}styles.css"><link rel="stylesheet" href="{prefix}study.css">'''


def parse_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("missing frontmatter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


# --- math and code protection ---------------------------------------------

def protect(text: str):
    """Swap code fences, $$...$$ and $...$ spans for placeholders so Markdown leaves them alone."""
    store = []

    def stash(kind: str, s: str):
        store.append((kind, s))
        return f"\n\nXPROTECT{len(store) - 1}X\n\n" if kind in ("fence", "display") else f"XPROTECT{len(store) - 1}X"

    text = re.sub(r"```.*?```", lambda m: stash("fence", m.group(0)), text, flags=re.S)
    text = re.sub(r"\$\$(.+?)\$\$", lambda m: stash("display", m.group(1)), text, flags=re.S)
    text = re.sub(r"(?<![\\$\w])\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\w)", lambda m: stash("inline", m.group(1)), text)
    return text, store


def restore(rendered: str, store):
    def put(m):
        kind, body = store[int(m.group(1))]
        if kind == "fence":
            # Render the fence on its own through Markdown so highlighting classes match.
            return markdown.markdown(body, extensions=["fenced_code"])
        body = html.escape(body.strip(), quote=False)
        if kind == "display":
            return f'<div class="math-display">$${body}$$</div>'
        return f"${body}$"

    # Placeholders that landed inside <p> tags on their own line should not keep the <p>.
    rendered = re.sub(r"<p>XPROTECT(\d+)X</p>", put, rendered)
    return re.sub(r"XPROTECT(\d+)X", put, rendered)


def render_markdown(body: str) -> str:
    protected, store = protect(body)
    md = markdown.Markdown(
        extensions=["tables", "toc", "smarty"],
        extension_configs={"toc": {"toc_depth": "2-3"}},
    )
    rendered = md.convert(protected)
    return restore(rendered, store)


def lecture_index(rendered_html: str):
    """Return [(id, label)] for each h3 inside the rendered body."""
    out = []
    for m in re.finditer(r'<h3 id="([^"]+)">(.*?)</h3>', rendered_html, re.S):
        label = re.sub(r"<[^>]+>", "", m.group(2))
        out.append((m.group(1), html.unescape(label)))
    return out


def build_course(path: Path):
    meta, body = parse_frontmatter(path.read_text())
    slug = path.stem
    code = meta["code"]
    title = meta["title"]
    summary = meta.get("summary", "")
    tone = TONES.get(meta.get("tone", "blue"), TONES["blue"])
    rendered = render_markdown(body)
    lectures = lecture_index(rendered)
    url = f"{BASE}/study/{slug}.html"

    jump = "".join(f'<li><a href="#{i}">{html.escape(l)}</a></li>' for i, l in lectures)
    facts = []
    if meta.get("instructors"):
        facts.append(f"<dt>Taught by</dt><dd>{html.escape(meta['instructors'])}</dd>")
    if meta.get("based_on"):
        facts.append(f"<dt>Notes based on</dt><dd>{html.escape(meta['based_on'])}</dd>")
    facts.append(f"<dt>Lectures covered</dt><dd>{len(lectures)}</dd>")
    if meta.get("official"):
        facts.append(
            f'<dt>Official page</dt><dd><a href="{html.escape(meta["official"])}" rel="noopener">{html.escape(code)} &#8599;</a></dd>'
        )

    katex = (
        f'  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.css" crossorigin="anonymous">\n'
        f'  <script defer src="https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.js" crossorigin="anonymous"></script>\n'
        f'  <script defer src="https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/contrib/auto-render.min.js" crossorigin="anonymous" '
        'onload="renderMathInElement(document.body,{delimiters:[{left:\'$$\',right:\'$$\',display:true},{left:\'$\',right:\'$\',display:false}],throwOnError:false});"></script>'
    )

    page = f'''<!doctype html>
<html lang="en"><head>
{HEAD_SCRIPTS}
  {meta_block(f"{code} {title}", summary or f"Study notes for Stanford {code}: {title}.", url, "../", "article")}
{katex}
</head>
<body><a class="skip-link" href="#main-content">Skip to content</a>
{nav("../")}
<main id="main-content" class="study-page">
  <section class="study-hero study-hero-tinted" style="--tone:{tone}"><div class="wrap"><p class="kicker">Stanford {html.escape(code)} &middot; {html.escape(meta.get("kicker", "Study notes"))}</p><h1>{html.escape(title)}</h1><p class="lead">{html.escape(summary)}</p></div></section>
  <div class="study-layout wrap">
    <aside class="study-side">
      <dl class="study-facts">{"".join(facts)}</dl>
      <nav class="study-jump" aria-label="Lectures"><p class="eyebrow">Lectures</p><ol>{jump}</ol></nav>
    </aside>
    <article class="study-body note-body">
      <p class="study-disclaimer">{DISCLAIMER}</p>
{rendered}
      <a class="back" href="../study.html">&larr; All courses</a>
    </article>
  </div>
</main>
{footer("../")}
</body></html>
'''
    (OUT / f"{slug}.html").write_text(page)
    return {
        "slug": slug,
        "code": code,
        "title": title,
        "kicker": meta.get("kicker", ""),
        "summary": summary,
        "tone": tone,
        "order": int(meta.get("order", 99)),
        "lectures": len(lectures),
        "url": url,
    }


def build_index(courses):
    courses = sorted(courses, key=lambda c: c["order"])
    cards = "".join(
        f'<a class="study-card" href="study/{c["slug"]}.html" style="--tone:{c["tone"]}">'
        f'<span>{html.escape(c["code"])} &middot; {html.escape(c["kicker"])}</span>'
        f'<h2>{html.escape(c["title"])}</h2><p>{html.escape(c["summary"])}</p>'
        f'<b>{c["lectures"]} lectures &rarr;</b></a>'
        for c in courses
    )
    desc = (
        "Lecture-by-lecture study notes on Stanford computer science courses: machine learning, deep learning, "
        "vision, NLP, graphs, reinforcement learning, data mining, and language modeling."
    )
    page = f'''<!doctype html>
<html lang="en"><head>
{HEAD_SCRIPTS}
  {meta_block("Study", desc, f"{BASE}/study.html", "", "website")}
</head>
<body><a class="skip-link" href="#main-content">Skip to content</a>
{nav("")}
<main id="main-content">
  <section class="study-hero"><div class="wrap"><p class="kicker">Lecture notes, written to be reread</p><h1>Study</h1><p class="lead">Stanford computer science courses worked through from the public lectures. One page per course, one section per lecture. Equations included, assignment solutions not.</p></div></section>
  <section class="study-grid wrap">{cards}</section>
  <section class="wrap study-about"><p>{DISCLAIMER} Course names and lecture order follow the official course pages, linked from each note. If you spot an error, <a href="https://github.com/nightandweather/nightandweather.github.io/issues">open an issue</a>.</p></section>
</main>
{footer("")}
</body></html>
'''
    (ROOT / "study.html").write_text(page)


def update_sitemap(courses):
    sm = ROOT / "sitemap.xml"
    text = sm.read_text()
    text = re.sub(r"\s*<url><loc>https://nightandweather\.github\.io/study(?:\.html|/[^<]+)</loc></url>", "", text)
    entries = [f"  <url><loc>{BASE}/study.html</loc></url>"] + [
        f"  <url><loc>{c['url']}</loc></url>" for c in sorted(courses, key=lambda c: c["order"])
    ]
    text = text.replace("</urlset>", "\n".join(entries) + "\n</urlset>")
    text = re.sub(r"\n{2,}</urlset>", "\n</urlset>", text)
    sm.write_text(text)


def main():
    courses = []
    for path in sorted(SRC.glob("*.md")):
        if path.name.upper() == "SPEC.MD":
            continue
        courses.append(build_course(path))
        print(f"built study/{path.stem}.html ({courses[-1]['lectures']} lectures)")
    build_index(courses)
    update_sitemap(courses)
    print(f"built study.html with {len(courses)} courses; sitemap updated")


if __name__ == "__main__":
    main()
