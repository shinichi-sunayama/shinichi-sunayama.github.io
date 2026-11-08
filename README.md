# Ohagi Kinako Kobo — website

Static site for Ohagi Kinako Kobo (おはぎきなこ工房), served by GitHub Pages.
Plain HTML and CSS only: no JavaScript, no forms, no cookies, no analytics, nothing loaded from other sites.

- `app-ads.txt` — authorised sellers file for AdMob. **Do not change or move it.**
- `index.html`, `games/`, `about/`, `press/`, `privacy/`, `404.html` — Japanese pages; `en/` — English pages.
  These are generated: edit `content/sitedata.py` (text and links) or `tools/build.py` (templates), then rebuild.
- `assets/css/site.css` — styles. `assets/img/`, `assets/press/` — images (re-encoded, no metadata).
- `assets/fonts/` — subset of M PLUS Rounded 1c Bold (SIL OFL 1.1, see `OFL.txt`), used for headings.

## Build and check

```
python tools/build.py
python tools/check.py   # needs Pillow for the image metadata check
```

`check.py` must print `all checks passed` before every push. It checks the Content-Security-Policy,
inline scripts and styles, external resources, broken links, `rel="noopener noreferrer"`,
image metadata, secret-looking strings, `app-ads.txt` and colour contrast.

If new characters appear in headings, regenerate the font subset from the full font with
`pyftsubset MPLUSRounded1c-Bold.ttf --text-file=<all characters used> --flavor=woff2 --layout-features='*'`
and save it as `assets/fonts/mplus-rounded-bold-subset.woff2`.
