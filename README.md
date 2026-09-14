# nightandweather.github.io

Personal project and research hub for Kanghoun Lee.

Static HTML/CSS, deployed through GitHub Pages. The site presents buildable product
research, medical imaging work, and live tools. Patient-result pages are hosted and
governed separately by their respective services.

## Study notes

`study.html` and `study/*.html` are generated. Edit the Markdown sources in
`study/src/` (format described in `study/src/SPEC.md`), then run:

```
python3 tools/build_study.py
```

The script rebuilds every course page, the `study.html` index, and the study
entries in `sitemap.xml`. Math uses `$...$` / `$$...$$` and is rendered by KaTeX
in the browser. Requires the `markdown` Python package.
