#!/usr/bin/env python3
"""Static site builder — landing page and docs, English and Turkish.

No framework, no build step beyond this file, no external requests at runtime.
That is not minimalism for its own sake: the site's whole argument is that this
product does not need infrastructure to be trustworthy, and a marketing site
pulling four CDNs would contradict it on the first page load.

Design tokens are taken from BRAND_KIT.md and inlined, so the site is
theme-aware, printable, and readable with JavaScript off.

    python site/build.py          # → site/dist/{en,tr}/*.html
"""
from __future__ import annotations

import html
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "dist"
CONTENT = ROOT / "content"
LOCALES = ("en", "tr")

NAV = {
    "en": [("index", "Home"), ("quickstart", "Quickstart"), ("modules", "Modules"),
           ("ci", "CI gate"), ("honesty", "Honesty"), ("privacy", "Privacy"),
           ("pricing", "Pricing")],
    "tr": [("index", "Ana sayfa"), ("quickstart", "Hızlı başlangıç"), ("modules", "Modüller"),
           ("ci", "CI kapısı"), ("honesty", "Dürüstlük"), ("privacy", "Gizlilik"),
           ("pricing", "Fiyatlandırma")],
}

FOOTER = {
    "en": "AtherosAI B.V. · The Kit assesses and evidences. It does not certify.",
    "tr": "AtherosAI B.V. · Kit değerlendirir ve kanıtlar. Belgelendirme yapmaz.",
}

#: Phrases that must never appear on the site, in either language. The same lint
#: that guards generated reports, applied to marketing — because marketing is
#: where the temptation actually is.
BANNED = [
    "fully compliant", "certified", "guaranteed compliant", "100% compliant",
    "no further action required", "compliance in one click", "risk-free",
    "tamamen uyumlu", "belgelendirilmiş", "uyum garantisi", "%100 uyumlu",
    "tek tıkla uyum", "risksiz",
]
#: Where the banned words appear legitimately: the page that explains we do not
#: say them, and the licence text that disclaims them.
BANNED_EXEMPT = {"honesty"}

CSS = """
:root{--bg:#FBFBFD;--surface:#fff;--surface-2:#F3F4F8;--surface-3:#EAECF2;--border:#DFE2EA;
--border-strong:#C3C8D4;--text:#111726;--muted:#525A6B;--faint:#7A8296;--accent:#2563EB;
--accent-subtle:rgba(37,99,235,.08);--good:#22C55E;--watch:#EAB308;--poor:#F97316;
--critical:#DC2626;--unmeasured:#6B7488;--degraded:#A855F7;
--mono:ui-monospace,SFMono-Regular,"JetBrains Mono",Menlo,monospace;
--sans:Inter,system-ui,-apple-system,"Segoe UI",sans-serif}
@media(prefers-color-scheme:dark){:root{--bg:#0B0F17;--surface:#161B26;--surface-2:#1E2534;
--surface-3:#283041;--border:#2A3345;--border-strong:#3A4560;--text:#E6EAF2;--muted:#9AA4B8;
--faint:#6B7488;--accent:#3B82F6;--accent-subtle:rgba(59,130,246,.10)}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 var(--sans);
-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
header.site{border-bottom:1px solid var(--border);background:var(--surface);position:sticky;
top:0;z-index:10}
header.site .inner{max-width:1040px;margin:0 auto;padding:14px 24px;display:flex;
align-items:center;gap:20px;flex-wrap:wrap}
header.site .brand{font-weight:700;font-size:15px;letter-spacing:-.01em}
header.site nav{display:flex;gap:4px;flex-wrap:wrap;margin-inline-start:auto}
header.site nav a{padding:6px 10px;border-radius:6px;font-size:14px;color:var(--muted)}
header.site nav a[aria-current=page]{background:var(--accent-subtle);color:var(--accent);
font-weight:600}
.lang{font-family:var(--mono);font-size:12px;padding:5px 10px;border:1px solid var(--border);
border-radius:6px;color:var(--muted)}
main{max-width:1040px;margin:0 auto;padding:48px 24px 72px}
.narrow{max-width:760px}
h1{font-size:38px;line-height:1.2;letter-spacing:-.02em;margin:0 0 12px}
h2{font-size:26px;line-height:1.3;letter-spacing:-.01em;margin:48px 0 12px;
padding-top:24px;border-top:1px solid var(--border)}
h2:first-of-type{border-top:none;padding-top:0}
h3{font-size:18px;margin:28px 0 8px}
p,li{color:var(--text)}
p.lead{font-size:19px;color:var(--muted);line-height:1.55;max-width:62ch}
.muted{color:var(--muted)}.faint{color:var(--faint);font-size:14px}
code{font-family:var(--mono);font-size:.88em;background:var(--surface-2);
padding:2px 5px;border-radius:4px}
pre{background:var(--surface);border:1px solid var(--border);border-radius:10px;
padding:16px 18px;overflow-x:auto;font-family:var(--mono);font-size:13px;line-height:1.6}
pre code{background:none;padding:0;font-size:inherit}
table{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--border);
border-radius:10px;overflow:hidden;margin:16px 0;font-size:14px;display:block;overflow-x:auto}
th,td{text-align:start;padding:10px 14px;border-bottom:1px solid var(--border);vertical-align:top}
th{background:var(--surface-2);font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:none}
blockquote{margin:16px 0;padding:12px 18px;border-inline-start:3px solid var(--accent);
background:var(--surface-2);border-radius:0 8px 8px 0;color:var(--muted)}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin:20px 0}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px}
.card h3{margin-top:0}
.stat{font-size:34px;font-weight:700;font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.stat.good{color:var(--good)}.stat.bad{color:var(--critical)}
.cta{display:inline-block;background:var(--accent);color:#fff;padding:11px 20px;border-radius:10px;
font-weight:600;font-size:15px;margin:8px 8px 8px 0}
.cta:hover{text-decoration:none;opacity:.92}
.cta.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.pill{display:inline-block;font-family:var(--mono);font-size:11px;font-weight:600;
text-transform:uppercase;padding:2px 8px;border-radius:999px;border:1px solid currentColor}
.pill.unmeasured{color:var(--unmeasured)}.pill.good{color:var(--good)}
.pill.critical{color:var(--critical)}.pill.degraded{color:var(--degraded)}
footer.site{border-top:1px solid var(--border);color:var(--faint);font-size:13px;
padding:28px 24px;text-align:center}
@media print{header.site,footer.site{display:none}body{background:#fff;color:#000}}
"""


def render_inline(text: str) -> str:
    """Bold, code and links. Deliberately tiny — the content is prose, not a CMS."""
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def render_markdown(src: str) -> str:
    """A small, predictable subset: headings, lists, tables, code fences, quotes.

    Written rather than pulled in because the alternative is a dependency whose
    output we would then have to audit for the same claims the copy lint checks.
    """
    out: list[str] = []
    lines = src.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            i += 1
            block: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(html.escape(lines[i]))
                i += 1
            out.append("<pre><code>" + "\n".join(block) + "</code></pre>")
        elif line.startswith("|"):
            rows: list[str] = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            i -= 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            body = [r for r in cells[1:] if not all(set(c) <= set("-: ") for c in r)]
            out.append(
                "<table><thead><tr>"
                + "".join(f"<th>{render_inline(c)}</th>" for c in cells[0])
                + "</tr></thead><tbody>"
                + "".join("<tr>" + "".join(f"<td>{render_inline(c)}</td>" for c in r) + "</tr>"
                          for r in body)
                + "</tbody></table>")
        elif line.startswith("- "):
            items: list[str] = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{render_inline(lines[i][2:])}</li>")
                i += 1
            i -= 1
            out.append("<ul>" + "".join(items) + "</ul>")
        elif line.startswith("> "):
            quote: list[str] = []
            while i < len(lines) and lines[i].startswith("> "):
                quote.append(render_inline(lines[i][2:]))
                i += 1
            i -= 1
            out.append("<blockquote>" + " ".join(quote) + "</blockquote>")
        elif line.startswith("### "):
            out.append(f"<h3>{render_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{render_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{render_inline(line[2:])}</h1>")
        elif line.startswith(":::"):
            out.append(line[3:])                    # raw HTML block, used sparingly
        elif line.strip():
            out.append(f"<p>{render_inline(line)}</p>")
        i += 1
    return "\n".join(out)


def page(slug: str, locale: str, title: str, body: str, description: str) -> str:
    other = "tr" if locale == "en" else "en"
    nav = "".join(
        f'<a href="{s}.html"{" aria-current=page" if s == slug else ""}>{html.escape(label)}</a>'
        for s, label in NAV[locale])
    return f"""<!doctype html>
<html lang="{locale}">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="alternate" hreflang="{other}" href="../{other}/{slug}.html">
<style>{CSS}</style>
<header class="site"><div class="inner">
  <span class="brand">AtherosAI Compliance Kit</span>
  <nav>{nav}</nav>
  <a class="lang" href="../{other}/{slug}.html">{other.upper()}</a>
</div></header>
<main class="{'narrow' if slug != 'index' else ''}">
{body}
</main>
<footer class="site">{html.escape(FOOTER[locale])}</footer>
</html>"""


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    problems: list[str] = []

    for locale in LOCALES:
        (OUT / locale).mkdir(parents=True, exist_ok=True)
        for source in sorted((CONTENT / locale).glob("*.md")):
            slug = source.stem
            raw = source.read_text(encoding="utf-8")
            # Front matter: first line "# Title", second line "> description".
            lines = raw.split("\n")
            title = lines[0].lstrip("# ").strip()
            description = lines[1].lstrip("> ").strip() if len(lines) > 1 else title
            body = render_markdown("\n".join(lines[2:]))
            rendered = page(slug, locale, title, body, description)
            (OUT / locale / f"{slug}.html").write_text(rendered, encoding="utf-8")

            if slug not in BANNED_EXEMPT:
                low = rendered.lower()
                hits = [b for b in BANNED if b in low]
                if hits:
                    problems.append(f"{locale}/{slug}: {hits}")

    # Root redirect, honouring the browser's language.
    (OUT / "index.html").write_text(
        '<!doctype html><meta charset="utf-8">'
        '<title>AtherosAI Compliance Kit</title>'
        '<script>location.replace((navigator.language||"en")'
        '.toLowerCase().startsWith("tr")?"tr/index.html":"en/index.html")</script>'
        '<noscript><a href="en/index.html">English</a> · '
        '<a href="tr/index.html">Türkçe</a></noscript>',
        encoding="utf-8")

    pages = sorted(p.relative_to(OUT) for p in OUT.rglob("*.html"))
    print(f"built {len(pages)} pages → {OUT}")
    for p in pages:
        print(f"  {p}")

    if problems:
        # The copy lint, applied to marketing. This is where the temptation is:
        # nobody writes "guaranteed compliant" into a finding, and everybody is
        # tempted to write it into a hero.
        print("\nCOPY LINT FAILED — banned phrasing found:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("\ncopy lint: clean (both languages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
