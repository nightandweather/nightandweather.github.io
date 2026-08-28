#!/usr/bin/env python3
"""Normalize page chrome and social metadata for this static site."""

from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://nightandweather.github.io"


def image_size(path: Path):
    data = path.read_bytes()[:32]
    if data.startswith(b"\x89PNG"):
        return struct.unpack(">II", data[16:24])
    if data.startswith(b"\xff\xd8"):
        data = path.read_bytes()
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in range(0xC0, 0xC4):
                return struct.unpack(">HH", data[i + 5:i + 9])[::-1]
            if marker == 0xD9 or marker == 0xDA:
                break
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def page_url(path: Path):
    rel = path.relative_to(ROOT).as_posix()
    return BASE + ("/" if rel == "index.html" else "/" + rel)


def relative_prefix(path: Path):
    return "../" if path.parent != ROOT else ""


def description(html: str):
    match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html, re.I)
    return match.group(1) if match else "Projects, reviews, experiments, and field notes by Kanghoun Lee."


def title(html: str):
    match = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else "Kanghoun Lee"


def first_image(html: str, path: Path):
    match = re.search(r'<img[^>]+src="([^"]+)"', html, re.I)
    if match:
        src = match.group(1)
        if not src.startswith(("http://", "https://")):
            resolved = (path.parent / src).resolve()
            try:
                rel = resolved.relative_to(ROOT).as_posix()
                if resolved.is_file():
                    return f"{BASE}/{rel}"
            except ValueError:
                pass
    return f"{BASE}/assets/orcaton.jpg"


def normalized_header(prefix: str):
    home = prefix or "./"
    return f'''<header class="nav wrap">
    <a class="wordmark" href="{home}" aria-label="Kanghoun Lee, home">KANGHOUN LEE</a>
    <nav aria-label="Primary navigation"><a href="{home}#work">Work</a><a href="{home}#topics">Topics</a><a href="{prefix}opportunities.html">Calendar</a><a href="{prefix}hf-radar.html">HF Radar</a><a href="{prefix}rejections.html">Rejections</a></nav>
  </header>'''


def normalized_footer(prefix: str):
    home = prefix or "./"
    return f'''<footer class="footer">
    <div class="wrap"><span>© 2026 Kanghoun Lee · Seoul</span><nav aria-label="Footer navigation"><a href="{home}#about">About</a><a href="https://github.com/nightandweather">GitHub ↗</a><a href="https://www.linkedin.com/in/%EA%B0%95%ED%9B%88-%EC%9D%B4-aa7ba618a/" rel="me noopener">LinkedIn ↗</a></nav></div>
  </footer>'''


for path in sorted(ROOT.glob("*.html")) + sorted(ROOT.glob("topics/*.html")) + sorted(ROOT.glob("projects/*.html")):
    html = path.read_text()
    prefix = relative_prefix(path)
    url = page_url(path)
    page_title = title(html)
    desc = description(html)
    image = first_image(html, path)

    # Remove metadata this script owns so reruns are idempotent.
    owned = [
        r'\s*<link rel="(?:icon|canonical|preconnect)"[^>]*>',
        r'\s*<link href="https://fonts\.googleapis\.com[^>]*>',
        r'\s*<meta property="og:[^"]+"[^>]*>',
        r'\s*<meta name="twitter:[^"]+"[^>]*>',
    ]
    for pattern in owned:
        html = re.sub(pattern, "", html, flags=re.I)

    meta = f'''
  <link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
  <link rel="canonical" href="{url}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap" rel="stylesheet">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{page_title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="{image}">
  <meta property="og:url" content="{url}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{page_title}">
  <meta name="twitter:description" content="{desc}">
  <meta name="twitter:image" content="{image}">'''
    html = re.sub(r"(</title>)", r"\1" + meta, html, count=1, flags=re.I)

    html = re.sub(r'<header class="nav wrap">.*?</header>', normalized_header(prefix), html, count=1, flags=re.I | re.S)
    if 'class="skip-link"' not in html:
        html = re.sub(r"(<body[^>]*>)", r'\1\n  <a class="skip-link" href="#main-content">Skip to content</a>', html, count=1, flags=re.I)
    html = re.sub(r"<main(?![^>]*\bid=)([^>]*)>", r'<main id="main-content"\1>', html, count=1, flags=re.I)

    if re.search(r'<footer class="footer">.*?</footer>', html, re.I | re.S):
        html = re.sub(r'<footer class="footer">.*?</footer>', normalized_footer(prefix), html, count=1, flags=re.I | re.S)
    else:
        html = re.sub(r"</body>", normalized_footer(prefix) + "\n</body>", html, count=1, flags=re.I)

    # Reserve image space to avoid cumulative layout shift.
    def add_dimensions(match):
        tag = match.group(0)
        if re.search(r"\bwidth=|\bheight=", tag, re.I):
            return tag
        src_match = re.search(r'src="([^"]+)"', tag, re.I)
        if not src_match or src_match.group(1).startswith(("http://", "https://")):
            return tag
        asset = (path.parent / src_match.group(1)).resolve()
        if not asset.is_file():
            return tag
        size = image_size(asset)
        if not size:
            return tag
        width, height = size
        return tag[:-1].rstrip() + f' width="{width}" height="{height}">'

    html = re.sub(r"<img\b[^>]*>", add_dimensions, html, flags=re.I)
    path.write_text(html)
