#!/usr/bin/env python3
"""
Build the localized home pages from one template.

    python3 tools/build.py            # writes index.html, pt/index.html, es/index.html
    python3 tools/build.py --preview OUT_DIR   # flat preview: index.html, pt.html, es.html

Source of truth:
    assets/data/products.json every product (game or app): one entry drives its card, its row in
                              the policies list and its schema.org data (see the _readme in it)
    src/index.template.html   markup with {{placeholders}}
    src/i18n/en.json          English strings  (also the fallback language)
    src/i18n/pt.json          Portuguese (Brazil)
    src/i18n/es.json          Spanish (Latin America)

Every language file must define exactly the same keys; the build stops if one is missing.
No dependencies beyond the Python 3 standard library.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
PRODUCTS = ROOT / "assets" / "data" / "products.json"

LANGS = {
    #     html lang   og:locale  Play hl     label
    "en": ("en",      "en_US",   "",         "English"),
    "pt": ("pt-BR",   "pt_BR",   "pt_BR",    "Português"),
    "es": ("es-419",  "es_LA",   "es_419",   "Español"),
}
ORDER = ["en", "pt", "es"]
SITE = "https://solevia.app/"


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flatten(v, f"{prefix}{k}."))
        else:
            out[f"{prefix}{k}"] = v
    return out


def load_strings():
    data = {code: json.loads((SRC / "i18n" / f"{code}.json").read_text(encoding="utf-8")) for code in ORDER}
    keys = {code: set(flatten(d)) for code, d in data.items()}
    for code in ORDER[1:]:
        missing, extra = keys["en"] - keys[code], keys[code] - keys["en"]
        if missing or extra:
            sys.exit(f"[i18n] {code}.json is out of sync with en.json\n  missing: {sorted(missing)}\n  extra: {sorted(extra)}")
    return data


# ---------------------------------------------------------------------------------------
# Products (assets/data/products.json)
# ---------------------------------------------------------------------------------------
def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def load_products():
    data = json.loads(PRODUCTS.read_text(encoding="utf-8"))["products"]
    seen = set()
    for p in data:
        pid = p["id"]
        if pid in seen:
            sys.exit(f"[products] duplicate id {pid}")
        seen.add(pid)
        for field in ("name", "kicker", "pitch", "shot_alt"):
            missing = [c for c in ORDER if not (p.get(field) or {}).get(c)]
            if missing:
                sys.exit(f"[products] {pid}: {field} missing for {missing}")
        if "en" not in p["shot"]:
            sys.exit(f"[products] {pid}: shot needs an 'en' image (fallback)")
        if p["kind"] not in ("game", "app"):
            sys.exit(f"[products] {pid}: kind must be game or app")
        if p["status"] not in ("live", "coming-soon"):
            sys.exit(f"[products] {pid}: status must be live or coming-soon")
        stores = bool(p.get("apple") or p.get("play"))
        if p["status"] == "live" and not stores:
            sys.exit(f"[products] {pid}: status live needs an apple id and/or a play package")
        if p["status"] == "coming-soon" and stores:
            sys.exit(f"[products] {pid}: coming-soon must not carry store ids (flip status to live)")
        for f in [p["icon"], *p["shot"].values()]:
            if not (ROOT / f).exists():
                sys.exit(f"[products] {pid}: missing file {f}")
    return data


def pick(d, code):
    return d.get(code) or d["en"]


CARD = """      <article class="pcard" id="{id}" aria-labelledby="{id}-title" data-status="{status}">
        <div class="pshot"><img class="pshot-img" src="{shot}" alt="{shot_alt}" width="{w}" height="{h}" loading="lazy"></div>
        <div class="pbody">
          <div class="pid">
            <img class="app-icon" src="{icon}" alt="" width="64" height="64" loading="lazy">
            <div>
              <p class="pkicker">{kicker}</p>
              <h4 class="pname" id="{id}-title">{name}</h4>
            </div>
          </div>
          <p class="ppitch">{pitch}</p>
          <div class="stores">{badges}</div>
        </div>
      </article>"""

GROUP = """    <div class="wrap pgroup">
      <h3 class="pgroup-title">{title}</h3>
      <div class="pgrid">
{cards}
      </div>
    </div>"""

ROW = """          <div class="legal-row">
            <img src="{icon}" alt="" width="40" height="40" loading="lazy">
            <span class="legal-name">{name}</span>
            <nav class="legal-links" aria-label="{label} {name}">
              <a href="{prefix}privacy/{slug}/">{privacy}</a>
              <a href="{prefix}terms/{slug}/">{terms}</a>
              {third}
            </nav>
          </div>"""


def product_cards(products, strings, code, spec):
    s = flatten(strings)
    play_hl = LANGS[code][2]
    root = spec["root"]
    groups = []
    for kind, title_key in (("game", "products.games"), ("app", "products.apps")):
        items = [p for p in products if p["kind"] == kind]
        if not items:
            continue
        cards = []
        for p in items:
            name = esc(p["name"][code])
            w, h = p.get("shot_size", [640, 1138])
            badges = []
            if p.get("apple"):
                badges.append(
                    f'<a class="store-badge" href="https://apps.apple.com/app/id{p["apple"]}" target="_blank" rel="noopener">'
                    f'<img src="{root}assets/badges/app-store-{code}.svg" alt="{esc(s["stores.apple_alt"])} · {name}" width="144" height="48"></a>')
            if p.get("play"):
                hl = f"&amp;hl={play_hl}" if play_hl else ""
                badges.append(
                    f'<a class="store-badge" href="https://play.google.com/store/apps/details?id={p["play"]}{hl}" target="_blank" rel="noopener">'
                    f'<img src="{root}assets/badges/google-play-{code}.svg" alt="{esc(s["stores.google_alt"])} · {name}" width="162" height="48"></a>')
            if p["status"] == "coming-soon":
                badges.append(f'<span class="soon-pill">{s["products.soon"]}</span>')
            elif not p.get("apple"):
                badges.append(f'<span class="soon-note">{s["products.soon_ios"]}</span>')
            elif not p.get("play"):
                badges.append(f'<span class="soon-note">{s["products.soon_android"]}</span>')
            cards.append(CARD.format(
                id=p["id"], status=p["status"], name=name, w=w, h=h,
                shot=root + pick(p["shot"], code), shot_alt=esc(p["shot_alt"][code]),
                icon=root + p["icon"], kicker=esc(p["kicker"][code]), pitch=esc(p["pitch"][code]),
                badges="".join(badges)))
        groups.append(GROUP.format(title=s[title_key], cards="\n".join(cards)))
    return "\n".join(groups)


def policy_rows(products, strings, code, spec):
    s = flatten(strings)
    rows = []
    for p in products:
        name = esc(p["name"][code])
        if p.get("about"):
            third = f'<a href="{spec["legal"]}{p["about"]}" hreflang="en">{s["support.support"]}</a>'
        else:
            subject = esc(p["name"]["en"]).replace(" ", "%20")
            third = f'<a href="mailto:support@solevia.app?subject={subject}%20support">{s["support.support"]}</a>'
        rows.append(ROW.format(
            icon=spec["root"] + p["icon"], name=name, label=s["support.row_label"], slug=p["slug"],
            prefix=spec["legal_prefix"], privacy=s["support.privacy"], terms=s["support.terms"], third=third))
    return "\n".join(rows)


def products_jsonld(products):
    out = []
    for p in products:
        if p["status"] != "live":
            continue
        same, systems = [], []
        if p.get("apple"):
            same.append(f'https://apps.apple.com/app/id{p["apple"]}')
            systems.append("iOS")
        if p.get("play"):
            same.append(f'https://play.google.com/store/apps/details?id={p["play"]}')
            systems.append("Android")
        out.append({
            "@type": "MobileApplication",
            "name": p["name"]["en"],
            "applicationCategory": "GameApplication" if p["kind"] == "game" else "LifestyleApplication",
            "operatingSystem": ", ".join(systems),
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "publisher": {"@id": "https://solevia.app/#org"},
            "sameAs": same,
        })
    return "".join(",\n    " + json.dumps(o, ensure_ascii=False) for o in out)


HUB_ROW = """        <a class="hub-row" href="/{kind}/{slug}/">
          <img src="/{icon}" alt="" width="56" height="56">
          <span class="hub-name">{name}<small>{label}</small></span>
          <span class="hub-go" aria-hidden="true">→</span>
        </a>
"""


def build_hubs(products):
    """Keep the English /privacy/ and /terms/ hubs in step with products.json (one row per product)."""
    for kind, label in (("privacy", "Privacy policy"), ("terms", "Terms of use")):
        path = ROOT / kind / "index.html"
        html = path.read_text(encoding="utf-8")
        a = html.index('<div class="hub-list">') + len('<div class="hub-list">\n')
        b = html.index("  </div>\n\n</main>")
        rows = "".join(HUB_ROW.format(kind=kind, slug=p["slug"], icon=p["icon"], name=esc(p["name"]["en"]), label=label)
                       for p in products)
        html = html[:a] + rows + html[b:]
        html = html.replace('<a href="/#games">Games</a>', '<a href="/#products">Products</a>')
        path.write_text(html, encoding="utf-8")
        print(f"  hub: {kind}/index.html")


def page_plan(preview):
    """Where each language lives and how pages link to each other."""
    if preview:
        files = {"en": "index.html", "pt": "pt.html", "es": "es.html"}
        return {
            code: {
                "out": files[code],
                "root": "",
                "legal": SITE,                       # legal pages are not part of the preview bundle
                "legal_prefix": SITE + ("" if code == "en" else f"{code}/"),
                "urls": dict(files),
                "is_root": code == "en",
            }
            for code in ORDER
        }
    plan = {}
    for code in ORDER:
        sub = code != "en"
        root = "../" if sub else ""
        plan[code] = {
            "out": f"{code}/index.html" if sub else "index.html",
            "root": root,
            "legal": root,
            "legal_prefix": root + (f"{code}/" if sub else ""),
            "urls": {c: (root + (f"{c}/" if c != "en" else "")) or "./" for c in ORDER},
            "is_root": not sub,
        }
    return plan


def lang_links(current, urls):
    rows = []
    for code in ORDER:
        label = code.upper()
        full = LANGS[code][3]
        current_attr = ' aria-current="true"' if code == current else ""
        rows.append(
            f'      <a href="{urls[code]}" hreflang="{LANGS[code][0]}" lang="{LANGS[code][0]}" '
            f'data-lang="{code}" title="{full}"{current_attr}><abbr title="{full}">{label}</abbr></a>'
        )
    return "\n".join(rows)


def render(template, strings, code, spec, products):
    flat = flatten(strings)
    html_lang, og_locale, play_hl, _ = LANGS[code]
    values = dict(flat)
    values.update({
        "lang": code,
        "html_lang": html_lang,
        "og_locale": og_locale,
        "root": spec["root"],
        "legal": spec["legal"],
        "canonical": SITE + ("" if code == "en" else f"{code}/"),
        "is_root": "true" if spec["is_root"] else "false",
        "lang_urls": json.dumps(spec["urls"]),
        "lang_links": lang_links(code, spec["urls"]),
        "play_hl": f"&amp;hl={play_hl}" if play_hl else "",
        "og_image": "og.png" if code == "en" else f"og-{code}.png",
        "products_html": product_cards(products, strings, code, spec),
        "policy_rows": policy_rows(products, strings, code, spec),
        "products_jsonld": products_jsonld(products),
        "live_games": sum(1 for p in products if p["kind"] == "game" and p["status"] == "live"),
        "js_strings": json.dumps(strings["js"], ensure_ascii=False).replace("</", "<\\/"),
    })

    def sub(m):
        key = m.group(1)
        if key not in values:
            sys.exit(f"[build] unknown placeholder {{{{{key}}}}} ({code})")
        return str(values[key])

    out = re.sub(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}", sub, template)
    return out


def main():
    preview = "--preview" in sys.argv
    out_dir = Path(sys.argv[sys.argv.index("--preview") + 1]) if preview else ROOT
    template = (SRC / "index.template.html").read_text(encoding="utf-8")
    strings = load_strings()
    products = load_products()
    for code, spec in page_plan(preview).items():
        target = out_dir / spec["out"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(template, strings[code], code, spec, products), encoding="utf-8")
        print(f"  {code}: {target.relative_to(out_dir) if preview else target.relative_to(ROOT)}")
    if not preview:
        build_hubs(products)


if __name__ == "__main__":
    main()
