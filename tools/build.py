#!/usr/bin/env python3
"""
Build the localized home pages from one template.

    python3 tools/build.py            # writes index.html, pt/index.html, es/index.html
    python3 tools/build.py --preview OUT_DIR   # flat preview: index.html, pt.html, es.html

Source of truth:
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


def page_plan(preview):
    """Where each language lives and how pages link to each other."""
    if preview:
        files = {"en": "index.html", "pt": "pt.html", "es": "es.html"}
        return {
            code: {
                "out": files[code],
                "root": "",
                "legal": SITE,                       # legal pages are not part of the preview bundle
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


def render(template, strings, code, spec):
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
    for code, spec in page_plan(preview).items():
        target = out_dir / spec["out"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(template, strings[code], code, spec), encoding="utf-8")
        print(f"  {code}: {target.relative_to(out_dir) if preview else target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
