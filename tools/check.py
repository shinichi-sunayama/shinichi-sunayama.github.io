"""Pre-publish checks for the static site. Run from the repo root: python tools/check.py
Checks: CSP meta on every page, no inline scripts/styles, no external resources, internal links and
images resolve, external links carry rel="noopener noreferrer", image files carry no metadata,
no secret-looking strings, app-ads.txt unchanged, and text/background contrast."""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent.parent
problems: list[str] = []
APP_ADS = "google.com, pub-3932059719829600, DIRECT, f08c47fec0942fa0"


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags: list[tuple[str, dict]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append((tag, a))
        if "id" in a:
            self.ids.add(a["id"])


pages = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
ext_links: set[str] = set()
parsed = {}
for page in pages:
    text = page.read_text(encoding="utf-8")
    p = P()
    p.feed(text)
    parsed[page] = p
    rel = page.relative_to(ROOT)
    metas = [a for t, a in p.tags if t == "meta" and a.get("http-equiv", "").lower() == "content-security-policy"]
    if not metas:
        problems.append(f"{rel}: no CSP meta")
    elif "script-src 'none'" not in metas[0]["content"] or "default-src 'none'" not in metas[0]["content"]:
        problems.append(f"{rel}: CSP is weaker than expected")
    for t, a in p.tags:
        if t in ("script", "style", "iframe", "object", "embed", "form", "input"):
            problems.append(f"{rel}: <{t}> found")
        if "style" in a:
            problems.append(f"{rel}: inline style attribute on <{t}>")
        if any(k.startswith("on") for k in a):
            problems.append(f"{rel}: inline event handler on <{t}>")
        for attr in ("src", "href", "srcset"):
            v = a.get(attr)
            if not v:
                continue
            for url in ([s.strip().split(" ")[0] for s in v.split(",")] if attr == "srcset" else [v]):
                u = urlparse(url)
                if u.scheme in ("http", "https"):
                    if t in ("img", "source", "script", "link") and not (t == "link" and a.get("rel") in ("canonical", "alternate")):
                        problems.append(f"{rel}: external resource {url}")
                    if t == "a":
                        ext_links.add(url)
                        if a.get("rel") != "noopener noreferrer" or a.get("target") != "_blank":
                            problems.append(f"{rel}: external link without noopener noreferrer: {url}")
                        if u.scheme != "https":
                            problems.append(f"{rel}: non-https link {url}")
                elif u.scheme in ("mailto",):
                    continue
                elif u.scheme:
                    problems.append(f"{rel}: unexpected scheme {url}")
                else:
                    path = unquote(u.path)
                    if not path:
                        continue
                    base = ROOT if path.startswith("/") else page.parent
                    target = (base / path.lstrip("/")).resolve()
                    if target.is_dir():
                        target = target / "index.html"
                    if not target.exists():
                        problems.append(f"{rel}: broken link {url}")
                    elif u.fragment and target.suffix == ".html":
                        pass

# in-page anchors
for page, p in parsed.items():
    for t, a in p.tags:
        h = a.get("href", "")
        if t == "a" and h.startswith("#") and len(h) > 1 and h[1:] not in p.ids:
            problems.append(f"{page.relative_to(ROOT)}: missing anchor {h}")

# image metadata: re-encoded files should carry no EXIF/XMP/text chunks
try:
    from PIL import Image
    for img in (ROOT / "assets").rglob("*"):
        if img.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        with Image.open(img) as im:
            info = {k for k in im.info if k not in ("dpi", "jfif", "jfif_version", "jfif_unit", "jfif_density", "progressive", "progression", "loop", "background", "transparency", "gamma", "srgb", "duration", "timestamp", "lossless")}
            exif = im.getexif()
            if info or len(exif):
                problems.append(f"{img.relative_to(ROOT)}: metadata {sorted(info)} exif={len(exif)}")
except ImportError:
    print("(Pillow not installed: image metadata check skipped)")

# secrets and private strings
SECRET = re.compile(r"(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|github_pat_|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{30,}|-----BEGIN|ca-app-pub-\d+~\d+|hmac|password|C:\\Users|/Users/)", re.I)
for f in ROOT.rglob("*"):
    if ".git" in f.parts or not f.is_file() or f.suffix.lower() in (".png", ".jpg", ".webp", ".woff2"):
        continue
    if f.name == "check.py":
        continue
    for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if SECRET.search(line):
            problems.append(f"{f.relative_to(ROOT)}:{i}: secret-like text: {line.strip()[:80]}")

# app-ads.txt must stay exactly as AdMob expects
ads = (ROOT / "app-ads.txt").read_text(encoding="utf-8").strip()
if ads != APP_ADS:
    problems.append("app-ads.txt changed")


# contrast (WCAG): main text/background pairs from site.css
def lum(hex_: str) -> float:
    c = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a: str, b: str) -> float:
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


PAIRS = {  # (fg, bg, minimum)
    "light text on paper": ("#3f281e", "#f6efe2", 7), "light soft text on card": ("#6a5244", "#fffaf0", 4.5),
    "light soft text on paper": ("#6a5244", "#f6efe2", 4.5), "light button": ("#fffaf0", "#6b3f3a", 4.5),
    "light link on paper": ("#6b3f3a", "#f6efe2", 4.5), "light price (matcha) on card": ("#6f8a4f", "#fffaf0", 3.0),
    "light footer": ("#fffaf0", "#6b3f3a", 4.5),
    "dark text": ("#f4e8d8", "#241a16", 7), "dark soft text on card": ("#d4c2ae", "#2f241f", 4.5),
    "dark button": ("#fffaf0", "#b5675e", 3.0), "dark link": ("#b5675e", "#241a16", 3.0),
}
contrast = []
for name, (fg, bg, need) in PAIRS.items():
    r = ratio(fg, bg)
    contrast.append(f"  {name}: {r:.2f}:1 (need {need})")
    if r < need:
        problems.append(f"contrast too low: {name} {r:.2f}")

size = sum(f.stat().st_size for f in ROOT.rglob("*") if f.is_file() and ".git" not in f.parts)
print(f"pages: {len(pages)}   external links: {len(ext_links)}   total size: {size / 1e6:.1f} MB")
print("contrast:\n" + "\n".join(contrast))
print("external links:\n  " + "\n  ".join(sorted(ext_links)))
if problems:
    print(f"\n{len(problems)} problem(s):")
    print("\n".join("  - " + p for p in problems))
    sys.exit(1)
print("\nall checks passed")
