"""Static site generator for Ohagi Kinako Kobo.

Usage (from the repo root):
    python tools/build.py            # writes HTML pages
Content lives in content/sitedata.py. No third-party packages are needed to build pages.
Images and the font subset are prepared by tools/assets.py (needs Pillow and fontTools).
"""
from __future__ import annotations

import html
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "content"))
import sitedata as C  # noqa: E402  (content/sitedata.py)

BASE = C.BASE_URL

CSP = ("default-src 'none'; img-src 'self'; style-src 'self'; font-src 'self'; "
       "script-src 'none'; connect-src 'none'; object-src 'none'; frame-src 'none'; "
       "base-uri 'none'; form-action 'none'; manifest-src 'self'; upgrade-insecure-requests")

ICONS = {
    "appstore": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M16.4 12.6c0-2.6 2.1-3.8 2.2-3.9-1.2-1.8-3.1-2-3.7-2-1.6-.2-3.1.9-3.9.9-.8 0-2-.9-3.4-.9-1.7 0-3.3 1-4.2 2.6-1.8 3.1-.5 7.7 1.3 10.2.9 1.2 1.9 2.6 3.2 2.6 1.3-.1 1.8-.8 3.3-.8 1.6 0 2 .8 3.4.8 1.4 0 2.3-1.3 3.1-2.5 1-1.4 1.4-2.8 1.4-2.9 0 0-2.7-1-2.7-4.1zM13.9 5c.7-.9 1.2-2 1-3.2-1 0-2.3.7-3 1.6-.7.8-1.2 2-1.1 3.1 1.2.1 2.3-.6 3.1-1.5z"/></svg>',
    "browser": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M3 5h18v14H3zM3 9h18"/><circle cx="6" cy="7" r=".9" fill="currentColor"/><circle cx="9" cy="7" r=".9" fill="currentColor"/></svg>',
    "pc": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M3 4h18v12H3zM8 20h8M12 16v4"/></svg>',
    "x": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M17.8 3h3.1l-6.8 7.7L22 21h-6.2l-4.9-6.4L5.3 21H2.2l7.2-8.3L2 3h6.4l4.4 5.8zm-1.1 16.2h1.7L7.4 4.7H5.6z"/></svg>',
    "instagram": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.3" cy="6.7" r="1.2" fill="currentColor"/></svg>',
    "note": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M6 3h9l4 4v14H6zM14 3v5h5M9 12h7M9 16h7"/></svg>',
    "youtube": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="4" fill="none" stroke="currentColor" stroke-width="2"/><path fill="currentColor" d="M10 9v6l5-3z"/></svg>',
    "itch": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M4 9 6 4h12l2 5v2a3 3 0 0 1-5 0 3 3 0 0 1-6 0 3 3 0 0 1-5 0zM5 12v8h14v-8M10 20v-4h4v4"/></svg>',
    "tiktok": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" d="M14 3v11.5a3.5 3.5 0 1 1-3.5-3.5M14 3c.4 2.6 2.2 4.4 5 4.6"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M3 5h18v14H3zM3 6l9 7 9-7"/></svg>',
    "form": '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M4 4h16v13H8l-4 4zM8 9h8M8 13h5"/></svg>',
}

LOGO = ('<svg viewBox="0 0 40 40" aria-hidden="true"><ellipse cx="20" cy="22" rx="17" ry="15" fill="#6b3f3a"/>'
        '<ellipse cx="15" cy="17" rx="6" ry="3.4" fill="#8a5650" opacity=".7"/>'
        '<path d="M5 26c4 6 26 6 30 0" fill="none" stroke="#c9a46a" stroke-width="3" stroke-linecap="round"/></svg>')


def e(s: str) -> str:
    return html.escape(s, quote=True)


def rich(s: str) -> str:
    """Escape, then allow paragraphs separated by blank lines and line breaks."""
    paras = [p.strip() for p in s.strip().split("\n\n") if p.strip()]
    return "".join("<p>" + "<br>".join(e(line) for line in p.split("\n")) + "</p>" for p in paras)


def ext(url: str, label: str, cls: str = "", icon: str = "", sub: str = "") -> str:
    ic = ICONS.get(icon, "")
    s = f"<small>{e(sub)}</small>" if sub else ""
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{e(url)}" target="_blank" rel="noopener noreferrer">{ic}<span>{e(label)}{(" " + s) if s else ""}</span></a>'


class Page:
    def __init__(self, lang: str, path: str):
        self.lang = lang          # "ja" or "en"
        self.path = path          # site path without language prefix, e.g. "games/chiwachiku-run/"

    def url(self, path: str, lang: str | None = None) -> str:
        """Relative link from this page to another site path."""
        lang = lang or self.lang
        target = ("en/" if lang == "en" else "") + path
        here = ("en/" if self.lang == "en" else "") + self.path
        depth = here.count("/")
        rel = "../" * depth + target
        return rel or "./"

    def asset(self, p: str) -> str:
        here = ("en/" if self.lang == "en" else "") + self.path
        return "../" * here.count("/") + "assets/" + p

    def abs(self, path: str | None = None, lang: str | None = None) -> str:
        lang = lang or self.lang
        return BASE + "/" + ("en/" if lang == "en" else "") + (self.path if path is None else path)


def head(pg: Page, title: str, desc: str, og_image: str) -> str:
    S = C.STRINGS[pg.lang]
    full = title if title == S["site_name"] else f"{title} | {S['site_name']}"
    alt_lang = "en" if pg.lang == "ja" else "ja"
    return f"""<!doctype html>
<html lang="{pg.lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{e(full)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(pg.abs())}">
<link rel="alternate" hreflang="ja" href="{e(pg.abs(lang='ja'))}">
<link rel="alternate" hreflang="en" href="{e(pg.abs(lang='en'))}">
<link rel="alternate" hreflang="x-default" href="{e(pg.abs(lang='ja'))}">
<meta name="theme-color" content="#6b3f3a">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(S['site_name'])}">
<meta property="og:title" content="{e(full)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(pg.abs())}">
<meta property="og:image" content="{e(BASE + '/assets/img/' + og_image)}">
<meta property="og:locale" content="{'ja_JP' if pg.lang == 'ja' else 'en_US'}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{pg.asset('img/favicon.png')}" type="image/png">
<link rel="apple-touch-icon" href="{pg.asset('img/apple-touch-icon.png')}">
<link rel="preload" href="{pg.asset('fonts/mplus-rounded-bold-subset.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{pg.asset('css/site.css')}?v={C.ASSET_VERSION}">
</head>
<body>
<a class="skip" href="#main">{e(S['skip'])}</a>
"""


def header(pg: Page, current: str, small_noren: bool = False) -> str:
    S = C.STRINGS[pg.lang]
    other = "en" if pg.lang == "ja" else "ja"

    def nav(key: str, path: str) -> str:
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{pg.url(path)}"{cur}>{e(S["nav_" + key])}</a>'

    noren = "".join(f"<span>{e(ch)}</span>" for ch in S["noren"])
    return f"""<header class="site-head">
<div class="wrap">
<a class="logo" href="{pg.url('')}">{LOGO}<span>{e(S['site_name'])}</span></a>
<nav class="site-nav" aria-label="{e(S['nav_label'])}">
<a href="{pg.url('')}#games">{e(S['nav_games'])}</a>
{nav('ohagi', 'about/')}
{nav('press', 'press/')}
<a class="lang" href="{pg.url(pg.path, other)}" hreflang="{other}" lang="{other}">{e(S['other_lang'])}</a>
</nav>
</div>
<div class="noren{' small' if small_noren else ''}" aria-hidden="true">{noren}</div>
</header>
<main id="main">
"""


def footer(pg: Page) -> str:
    S = C.STRINGS[pg.lang]
    games = "".join(f'<li><a href="{pg.url("games/" + g["slug"] + "/")}">{e(g[pg.lang]["name"])}</a></li>' for g in C.GAMES)
    sns = "".join(f'<li>{ext(s["url"], s.get("label_" + pg.lang, s["label"]))}</li>' for s in C.SNS)
    return f"""</main>
<footer class="site-foot">
<div class="wrap">
<div class="cols">
<div><h2>{e(S['foot_games'])}</h2><ul>{games}</ul></div>
<div><h2>{e(S['foot_studio'])}</h2><ul>
<li><a href="{pg.url('about/')}">{e(S['nav_ohagi'])}</a></li>
<li><a href="{pg.url('press/')}">{e(S['nav_press'])}</a></li>
<li><a href="{pg.url('privacy/')}">{e(S['privacy_site'])}</a></li>
<li><a href="mailto:{e(C.EMAIL)}">{e(S['contact'])}</a></li>
</ul></div>
<div><h2>SNS</h2><ul>{sns}</ul></div>
</div>
<p class="copy">{e(S['copyright'])}<br>{e(S['trademark'])}</p>
</div>
</footer>
</body>
</html>
"""


def store_buttons(pg: Page, g: dict, big: bool = True) -> str:
    S = C.STRINGS[pg.lang]
    out = []
    for i, l in enumerate(g["links"]):
        label = S["link_" + l["kind"]]
        sub = l.get("sub_" + pg.lang, "")
        url = l["url_" + pg.lang] if ("url_" + pg.lang) in l else l["url"]
        out.append(ext(url, label, "btn" if i == 0 else "btn sub", l["icon"], sub))
    return '<div class="btns">' + "".join(out) + "</div>"


def game_card(pg: Page, g: dict) -> str:
    t = g[pg.lang]
    return f"""<li class="card">
<img src="{pg.asset('img/' + g['slug'] + '/icon-256.webp')}" width="104" height="104" alt="" loading="lazy">
<h3><a href="{pg.url('games/' + g['slug'] + '/')}">{e(t['name'])}</a></h3>
<p>{e(t['card'])}</p>
<div class="price">{e(t['price'])}</div>
<div class="plat">{e(t['platforms'])}</div>
</li>"""


def sns_list(pg: Page) -> str:
    return '<ul class="sns">' + "".join(f'<li>{ext(s["url"], s.get("label_" + pg.lang, s["label"]), icon=s["icon"])}</li>' for s in C.SNS) + "</ul>"


def write(pg: Page, content: str) -> None:
    out = ROOT / (("en/" if pg.lang == "en" else "") + pg.path) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- pages

def page_home(lang: str) -> None:
    pg = Page(lang, "")
    S = C.STRINGS[lang]
    H = C.HOME[lang]
    cards = "\n".join(game_card(pg, g) for g in C.GAMES)
    tags = "".join(f"<li>{e(t)}</li>" for t in H["tags"])
    promises = "".join(f"<li><h3>{e(p['t'])}</h3><p>{e(p['d'])}</p></li>" for p in H["promises"])
    body = f"""<div class="wrap">
<section class="hero">
<div>
<h1>{H['title_html']}</h1>
<div class="lead">{rich(H['lead'])}</div>
<ul class="tags">{tags}</ul>
<div class="btns"><a class="btn" href="#games">{e(H['cta'])}</a><a class="btn sub" href="{pg.url('about/')}">{e(H['cta2'])}</a></div>
</div>
<picture><source srcset="{pg.asset('img/home/kv-960.webp')} 960w, {pg.asset('img/home/kv-1600.webp')} 1600w" sizes="(max-width: 820px) 92vw, 640px" type="image/webp">
<img class="kv" src="{pg.asset('img/home/kv-960.jpg')}" width="960" height="540" alt="{e(H['kv_alt'])}" fetchpriority="high"></picture>
</section>
</div>
<section class="sec" id="games" aria-labelledby="games-h">
<div class="wrap">
<h2 class="sec-title" id="games-h">{e(S['oshinagaki'])}</h2>
<p class="sec-sub">{e(H['games_sub'])}</p>
<ul class="games">
{cards}
</ul>
</div>
</section>
<section class="sec band" aria-labelledby="ohagi-h">
<div class="wrap about">
<img class="ohagi" src="{pg.asset('img/home/ohagi-640.webp')}" width="640" height="640" alt="{e(H['about_alt'])}" loading="lazy">
<div>
<h2 id="ohagi-h" class="about-title">{e(H['about_title'])}</h2>
{rich(H['about'])}
<div class="btns"><a class="btn sub" href="{pg.url('about/')}">{e(H['about_more'])}</a></div>
</div>
</div>
</section>
<section class="sec" aria-labelledby="promise-h">
<div class="wrap">
<h2 class="sec-title" id="promise-h">{e(H['promise_title'])}</h2>
<p class="sec-sub">{e(H['promise_sub'])}</p>
<ul class="promises">{promises}</ul>
</div>
</section>
<section class="sec" aria-labelledby="sns-h">
<div class="wrap">
<h2 class="sec-title" id="sns-h">{e(H['sns_title'])}</h2>
<p class="sec-sub">{e(H['sns_sub'])}</p>
{sns_list(pg)}
</div>
</section>
"""
    write(pg, head(pg, S["site_name"], H["desc"], "home/og.jpg") + header(pg, "") + body + footer(pg))


def page_game(lang: str, g: dict) -> None:
    pg = Page(lang, f"games/{g['slug']}/")
    S = C.STRINGS[lang]
    t = g[lang]
    slug = g["slug"]
    facts = "".join(f"<li><b>{e(k)}</b>{e(v)}</li>" for k, v in t["facts"])
    feats = "".join(f'<li><span class="num">{i}</span><h3>{e(f["t"])}</h3><p>{e(f["d"])}</p></li>' for i, f in enumerate(t["features"], 1))
    shots_list = g["shots"].get(lang) or g["shots"]["ja"]
    shots = "".join(
        f'<li><img src="{pg.asset("img/" + slug + "/" + s + ".webp")}" alt="{e(a)}" loading="lazy" width="{g["shot_w"]}" height="{g["shot_h"]}"></li>'
        for s, a in shots_list)
    howto = "".join(f"<li>{e(h)}</li>" for h in t["howto"])
    dogs = ""
    if t.get("dogs"):
        items = []
        for d in t["dogs"]:
            img = f'<img src="{pg.asset("img/dogs/" + d["img"] + ".webp")}" width="160" height="160" alt="" loading="lazy">' if d.get("img") else ""
            items.append(f'<li>{img}<h3>{e(d["name"])}</h3><p class="breed">{e(d["breed"])}</p><p>{e(d["desc"])}</p></li>')
        dogs = f"""<section class="sec" aria-labelledby="dogs-h"><div class="wrap">
<h2 class="sec-title" id="dogs-h">{e(S['dogs_title'])}</h2>
<p class="sec-sub">{e(t.get('dogs_sub', ''))}</p>
<ul class="dogs">{''.join(items)}</ul></div></section>"""
    faq = "".join(f"<details><summary>{e(q['q'])}</summary><div class=\"ans\">{rich(q['a'])}</div></details>" for q in t["faq"])
    priv = "".join(f"<li>{e(p)}</li>" for p in t["privacy"])
    others = "\n".join(game_card(pg, o) for o in C.GAMES if o["slug"] != slug)
    tall = " tall" if g["shot_h"] > g["shot_w"] else ""
    body = f"""<div class="wrap">
<p class="crumb"><a href="{pg.url('')}">{e(S['home'])}</a> › {e(t['name'])}</p>
<section class="g-hero">
<div>
<div class="ttl"><img src="{pg.asset('img/' + slug + '/icon-256.webp')}" width="84" height="84" alt="">
<div><h1>{e(t['name'])}</h1><p class="subt">{e(t['subtitle'])}</p></div></div>
{rich(t['lead'])}
{store_buttons(pg, g)}
<ul class="facts">{facts}</ul>
</div>
<picture><source srcset="{pg.asset('img/' + slug + '/kv-960.webp')} 960w, {pg.asset('img/' + slug + '/kv-1600.webp')} 1600w" sizes="(max-width: 820px) 92vw, 520px" type="image/webp">
<img class="kv" src="{pg.asset('img/' + slug + '/kv-960.jpg')}" width="960" height="{g['kv_h']}" alt="{e(t['kv_alt'])}" fetchpriority="high"></picture>
</section>
</div>
<section class="sec band" aria-labelledby="feat-h"><div class="wrap">
<h2 class="sec-title" id="feat-h">{e(S['features'])}</h2>
<ul class="features">{feats}</ul>
</div></section>
<section class="sec" aria-labelledby="shots-h"><div class="wrap">
<h2 class="sec-title" id="shots-h">{e(S['screens'])}</h2>
<ul class="shots{tall}">{shots}</ul>
<p class="shots-hint">{e(S['swipe'])}</p>
</div></section>
<section class="sec band" aria-labelledby="how-h"><div class="wrap">
<h2 class="sec-title" id="how-h">{e(S['howto'])}</h2>
<ol class="howto">{howto}</ol>
</div></section>
{dogs}
<section class="sec" aria-labelledby="faq-h"><div class="wrap">
<h2 class="sec-title" id="faq-h">{e(S['faq'])}</h2>
<div class="faq">{faq}</div>
</div></section>
<section class="sec" aria-labelledby="priv-h" id="privacy"><div class="wrap">
<div class="note-box">
<h3 id="priv-h">{e(S['privacy'])}</h3>
<ul>{priv}</ul>
<p>{ext(t['privacy_url'], S['privacy_full'])}</p>
</div>
</div></section>
<section class="sec" aria-labelledby="play-h"><div class="wrap center">
<h2 class="sec-title" id="play-h">{e(S['play_now'])}</h2>
{store_buttons(pg, g).replace('class="btns"', 'class="btns center"', 1)}
</div></section>
<section class="sec band" aria-labelledby="other-h"><div class="wrap">
<h2 class="sec-title" id="other-h">{e(S['other_games'])}</h2>
<ul class="games">{others}</ul>
</div></section>
"""
    write(pg, head(pg, t["name"], t["desc"], f"{slug}/og.jpg") + header(pg, "games", True) + body + footer(pg))


def page_about(lang: str) -> None:
    pg = Page(lang, "about/")
    S = C.STRINGS[lang]
    A = C.ABOUT[lang]
    sections = "".join(f"<h2>{e(s['t'])}</h2>{rich(s['d'])}" for s in A["sections"])
    body = f"""<div class="wrap">
<p class="crumb"><a href="{pg.url('')}">{e(S['home'])}</a> › {e(A['title'])}</p>
<section class="sec">
<div class="prose">
<h1>{e(A['title'])}</h1>
<img class="ohagi-float" src="{pg.asset('img/home/ohagi-640.webp')}" width="640" height="640" alt="{e(C.HOME[lang]['about_alt'])}">
{sections}
</div>
</section>
<section class="sec"><h2 class="sec-title">{e(C.HOME[lang]['sns_title'])}</h2>{sns_list(pg)}</section>
</div>
"""
    write(pg, head(pg, A["title"], A["desc"], "home/og.jpg") + header(pg, "ohagi", True) + body + footer(pg))


def page_privacy(lang: str) -> None:
    pg = Page(lang, "privacy/")
    S = C.STRINGS[lang]
    P = C.SITE_PRIVACY[lang]
    sections = "".join(f"<h2>{e(s['t'])}</h2>{rich(s['d'])}" for s in P["sections"])
    games = "".join(f'<li><a href="{pg.url("games/" + g["slug"] + "/")}#privacy">{e(g[lang]["name"])}</a></li>' for g in C.GAMES)
    body = f"""<div class="wrap">
<p class="crumb"><a href="{pg.url('')}">{e(S['home'])}</a> › {e(P['title'])}</p>
<section class="sec"><div class="prose">
<h1>{e(P['title'])}</h1>
{sections}
<h2>{e(P['games_title'])}</h2>
<ul>{games}</ul>
</div></section>
</div>
"""
    write(pg, head(pg, P["title"], P["desc"], "home/og.jpg") + header(pg, "", True) + body + footer(pg))


def page_press(lang: str) -> None:
    pg = Page(lang, "press/")
    S = C.STRINGS[lang]
    P = C.PRESS[lang]
    toc = "".join(f'<li><a href="#{g["slug"]}">{e(g[lang]["name"])}</a></li>' for g in C.GAMES)
    studio_rows = "".join(f"<tr><th>{e(k)}</th><td>{v}</td></tr>" for k, v in P["studio_rows"])
    blocks = []
    for g in C.GAMES:
        t = g[lang]
        slug = g["slug"]
        rows = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in t["press_rows"])
        links = "".join(
            f'<tr><th>{e(S["link_" + l["kind"]])}</th><td>{ext(l.get("url_" + lang, l["url"]), l.get("url_" + lang, l["url"]))}</td></tr>'
            for l in g["links"])
        imgs = []
        for f, label in g["press_images"]:
            sq = " sq" if "icon" in f else ""
            imgs.append(f'<li><a href="{pg.asset("press/" + slug + "/" + f)}" download><img class="{sq.strip()}" src="{pg.asset("press/" + slug + "/thumb-" + f.rsplit(".", 1)[0] + ".webp")}" alt="" loading="lazy">{e(label)}</a></li>')
        blocks.append(f"""<article class="press-game" id="{slug}">
<header><img src="{pg.asset('img/' + slug + '/icon-256.webp')}" width="72" height="72" alt=""><div><h2>{e(t['name'])}</h2><p class="press-subt">{e(t['subtitle'])}</p></div></header>
<div class="press-grid">
<div>
<h3>{e(S['press_short'])}</h3><div class="copybox">{e(t['press_short'])}</div>
<h3>{e(S['press_long'])}</h3><div class="copybox">{e(t['press_long'])}</div>
</div>
<div>
<h3>{e(S['press_facts'])}</h3>
<table class="fact-table">{rows}{links}</table>
</div>
</div>
<h3>{e(S['press_images'])}</h3>
<ul class="dl">{''.join(imgs)}</ul>
</article>""")
    body = f"""<div class="wrap">
<p class="crumb"><a href="{pg.url('')}">{e(S['home'])}</a> › {e(P['title'])}</p>
<section class="sec">
<h1 class="sec-title">{e(P['title'])}</h1>
<p class="sec-sub">{e(P['sub'])}</p>
<ul class="toc"><li><a href="#studio">{e(P['studio'])}</a></li>{toc}</ul>
<article class="press-game" id="studio">
<header><div><h2>{e(P['studio'])}</h2></div></header>
<table class="fact-table">{studio_rows}</table>
<h3>{e(P['rules_title'])}</h3>
{rich(P['rules'])}
</article>
{''.join(blocks)}
</section>
</div>
"""
    write(pg, head(pg, P["title"], P["desc"], "home/og.jpg") + header(pg, "press", True) + body + footer(pg))


def page_404() -> None:
    pg = Page("ja", "")
    S = C.STRINGS["ja"]
    body = f"""<div class="wrap"><section class="sec"><div class="prose center">
<h1>ページが見つかりません</h1><p>Page not found.</p>
<p>おはぎがどこかへ持っていってしまったようです。</p>
<div class="btns center"><a class="btn" href="/">トップへ</a><a class="btn sub" href="/en/">English home</a></div>
</div></section></div>
"""
    # 404 is served from any path, so it uses absolute (root-relative) asset paths.
    doc = head(pg, "404", "Page not found", "home/og.jpg") + header(pg, "", True) + body + footer(pg)
    doc = doc.replace('href="assets/', 'href="/assets/').replace('src="assets/', 'src="/assets/')
    doc = doc.replace('href="en/', 'href="/en/').replace('href="about/', 'href="/about/').replace('href="press/', 'href="/press/')
    doc = doc.replace('href="games/', 'href="/games/').replace('href="privacy/', 'href="/privacy/').replace('href="./"', 'href="/"')
    (ROOT / "404.html").write_text(doc, encoding="utf-8", newline="\n")


def main() -> None:
    for lang in ("ja", "en"):
        page_home(lang)
        page_about(lang)
        page_privacy(lang)
        page_press(lang)
        for g in C.GAMES:
            page_game(lang, g)
    page_404()
    print("built", sum(1 for _ in ROOT.rglob("index.html")), "pages")


if __name__ == "__main__":
    main()
