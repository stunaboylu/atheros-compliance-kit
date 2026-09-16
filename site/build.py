#!/usr/bin/env python3
"""Static site builder — landing page and docs, English and Turkish.

No framework, no build step beyond this file, no external requests at runtime.
That is not minimalism for its own sake: the site's whole argument is that this
product does not need infrastructure to be trustworthy, and a marketing site
pulling four CDNs would contradict it on the first page load.

WHY THIS FILE DOES SO MUCH HEAD WORK

A generative engine can only cite a URL it can fetch and parse without running
JavaScript. Everything below the markdown renderer exists for that reader:
absolute canonicals, self-referencing hreflang with x-default, Open Graph,
JSON-LD, a real root page rather than a script redirect, and sitemap / robots /
llms.txt as actual files. A page missing a canonical or a JSON-LD block FAILS
the build, in the same way banned phrasing does — a requirement that is only a
convention is one that decays.

Every number the pages state about the product is substituted from
`facts.json`, which `scripts/collect_facts.py` measures from the product itself.
Three surfaces once carried three different test counts because each was typed
by hand; an unresolved or hand-written figure now breaks the build.

    python scripts/collect_facts.py && python site/build.py
"""
from __future__ import annotations

import html
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from datetime import date
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent
OUT = ROOT / "dist"
CONTENT = ROOT / "content"
FACTS_FILE = ROOT / "facts.json"
LOCALES = ("en", "tr")

#: Where the site will actually live. The canonical URL must be the one that
#: serves the page: pointing it at a domain that does not yet resolve tells every
#: engine to attribute the content to a 404.
#:
#: `SITE_URL` wins; the default is where the site lives in production — a path
#: under the company domain, served by the same Firebase Hosting site as the
#: rest of atherosai.com. The output is copied there by that site's build.
_DEFAULT_SITE = "https://atherosai.com/compliance-kit"
SITE_URL = (os.environ.get("SITE_URL") or _DEFAULT_SITE).rstrip("/")

#: The path component of SITE_URL: "/compliance-kit" in production, "" when the
#: site is served from a domain root. Pages link to each other relatively and
#: never need it; it exists for the two things that cannot be relative — the
#: console's asset and router base, and robots.txt's Disallow line.
BASE_PATH = urlparse(SITE_URL).path.rstrip("/")

ORG = {
    "name": "AtherosAI B.V.",
    "legal": "AtherosAI B.V.",
    "country": "NL",
    "email": "info@atherosai.com",
    "repo": "https://github.com/stunaboylu/atherosai_compliance_kit",
    "pypi": "https://pypi.org/project/atheros-compliance-kit/",
}
PRODUCT = "AtherosAI Compliance Kit"

NAV = {
    "en": [("index", "Home"), ("quickstart", "Quickstart"), ("modules", "Modules"),
           ("ci", "CI gate"), ("honesty", "Honesty"), ("faq", "FAQ"),
           ("self-assessment", "Our own report"),
           ("privacy", "Privacy"), ("pricing", "Pricing")],
    "tr": [("index", "Ana sayfa"), ("quickstart", "Hızlı başlangıç"), ("modules", "Modüller"),
           ("ci", "CI kapısı"), ("honesty", "Dürüstlük"), ("faq", "SSS"),
           ("self-assessment", "Kendi raporumuz"),
           ("privacy", "Gizlilik"), ("pricing", "Fiyatlandırma")],
}

#: Which schema.org type each page is. An engine answering "which tool does X"
#: wants SoftwareApplication; one answering "how do I" wants HowTo; one answering
#: a question wants FAQPage. Getting this wrong is worse than omitting it.
PAGE_TYPE = {
    "index": "SoftwareApplication",
    "quickstart": "HowTo",
    "ci": "HowTo",
    "modules": "TechArticle",
    "honesty": "TechArticle",
    "privacy": "TechArticle",
    "pricing": "Offer",
    "faq": "FAQPage",
    # A dated report about a named product, authored by its publisher — a Report
    # rather than an article, so an engine can tell it is primary data.
    "self-assessment": "Report",
}

LANG_NAME = {"en": "English", "tr": "Türkçe"}

#: Pages that need the full column. Prose reads better at 760px, but three
#: side-by-side cards do not fit there — they wrap to two-and-one, which is the
#: layout a reader has to work around rather than read.
WIDE_PAGES = {"index", "pricing"}

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
    # Naming a framework without naming the clauses is the same false assurance in
    # a different register. The Kit covers four ISO/IEC 42001 clauses; a page that
    # says "ISO 42001 compliance" invites a buyer to read that as all of them.
    "iso/iec 42001 compliance", "iso 42001 compliance",
    "iso/iec 42001 compliant", "iso 42001 compliant",
    "iso/iec 42001 uyumluluğu", "iso 42001 uyumluluğu",
    "iso/iec 42001 uyumlu", "iso 42001 uyumlu",
    "42001 internal audit", "42001 iç denetim",
]
#: Where the banned words appear legitimately: the pages whose SUBJECT is that we
#: do not say them.
#:
#: The exemption is conditional. An exempt page must itself carry the
#: non-certification statement — otherwise "add it to BANNED_EXEMPT" becomes the
#: way any page gets to say "fully compliant", and the lint quietly stops being a
#: control on exactly the pages most tempted to break it.
BANNED_EXEMPT = {"honesty", "faq"}
#: Checked against the page's own MARKDOWN, not the rendered HTML. Every page
#: carries the statement in its footer, so testing the render would have passed
#: for any page at all — a check that cannot fail is not a check.
#: Both statements are required, because there are two ways to overstate coverage:
#: claiming a verdict the Kit does not issue ("certified"), and claiming a scope it
#: does not have ("ISO 42001 compliance"). A page exempt from one must answer both.
EXEMPT_REQUIRES = {
    "en": ("it does not certify", "internal audit"),
    "tr": ("belgelendirme yapmaz", "iç denetim"),
}

CSS = """
:root{--bg:#FBFBFD;--surface:#fff;--surface-2:#F3F4F8;--surface-3:#EAECF2;--border:#DFE2EA;
--border-strong:#C3C8D4;--text:#111726;--muted:#525A6B;--faint:#7A8296;--accent:#2563EB;
--accent-hover:#1D4ED8;--accent-subtle:rgba(37,99,235,.08);--good:#22C55E;--watch:#EAB308;--poor:#F97316;
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

/* ── pricing ─────────────────────────────────────────────────────────────── */
.eyebrow{display:inline-flex;align-items:center;gap:8px;background:var(--accent-subtle);
border:1px solid var(--accent-border);border-radius:999px;padding:6px 14px;color:var(--accent);
font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px}
/* Three explicit columns, and `stretch` rather than `start`: the tiers are read
   by comparison, so unequal card heights make the rows stop lining up and the
   eye has to re-find each feature. `1fr` keeps them identical in width whatever
   the longest line is. */
.tiers{display:grid;gap:20px;grid-template-columns:repeat(3,1fr);
margin:36px 0 8px;align-items:stretch}
@media(max-width:900px){.tiers{grid-template-columns:1fr;max-width:420px;margin-inline:auto}}
.tier{position:relative;display:flex;flex-direction:column;background:var(--surface);
border:1px solid var(--border);border-radius:16px;padding:28px 24px}
.tier.featured{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-subtle)}
.tier .flag{position:absolute;top:-12px;left:50%;transform:translateX(-50%);
background:var(--accent);color:#fff;font-size:10px;font-weight:800;text-transform:uppercase;
letter-spacing:.14em;padding:5px 12px;border-radius:999px;white-space:nowrap}
.tier h3{margin:0 0 4px;font-size:17px}
.tier .who{color:var(--faint);font-size:13px;line-height:1.5;margin:0 0 18px}
@media(min-width:901px){.tier .who{min-height:60px}}
.tier .price{display:flex;align-items:baseline;gap:6px;flex-wrap:wrap;margin-bottom:4px}
.tier .amount{font-size:34px;font-weight:800;letter-spacing:-.03em;line-height:1.1}
.tier .unit{color:var(--muted);font-size:13px}
.tier .sub{color:var(--faint);font-size:12px;line-height:1.5;margin:0 0 20px}
@media(min-width:901px){.tier .sub{min-height:36px}}
.tier ul{list-style:none;padding:0;margin:0 0 22px;flex:1}
.tier li{position:relative;padding-left:24px;margin-bottom:9px;font-size:13.5px;
line-height:1.5;color:var(--text)}
.tier li::before{content:"✓";position:absolute;left:0;top:0;color:var(--good);
font-weight:700;font-size:13px}
.tier li.no{color:var(--faint)}
.tier li.no::before{content:"–";color:var(--faint)}
/* `background` is reset explicitly: the hero `.cta` class sets a solid accent
   fill, and this rule only overrode the colour — so the outlined button rendered
   accent text on an accent fill and the label disappeared. */
.tier .cta{display:block;text-align:center;padding:12px 16px;border-radius:10px;
font-weight:600;font-size:14px;border:1px solid var(--accent);color:var(--accent);
background:transparent;margin:0}
.tier .cta:hover{text-decoration:none;background:var(--accent-subtle);color:var(--accent)}
.tier.featured .cta{background:var(--accent);color:#fff;border-color:var(--accent)}
.tier.featured .cta:hover{background:var(--accent-hover);color:#fff;opacity:.94}
.tier code{background:var(--surface-2);font-size:.85em}
.note{background:var(--surface-2);border-radius:12px;padding:16px 20px;margin:24px 0;
color:var(--muted);font-size:14px;line-height:1.6}
@media print{.tier{break-inside:avoid}}
.updated{margin-top:48px;padding-top:16px;border-top:1px solid var(--border);
color:var(--faint);font-size:13px}
header.site .brand{color:var(--text);text-decoration:none}
header.site .brand:hover{text-decoration:none}
@media print{header.site,footer.site{display:none}body{background:#fff;color:#000}}
"""


def load_facts() -> dict:
    if not FACTS_FILE.exists():
        sys.exit("site/facts.json is missing — run scripts/collect_facts.py first. "
                 "The site states measured numbers and will not publish guessed ones.")
    return json.loads(FACTS_FILE.read_text(encoding="utf-8"))


_PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


def iso_facts(facts: dict, locale: str) -> dict:
    """The ISO/IEC 42001 clause table and the not-covered list, from the package.

    Both were hand-written on the FAQ and the honesty page, in two languages, and
    a fifth clause appearing in `atheros_kit.iso` would have left four copies
    saying "four clauses" with nothing to notice it. They are measured into
    facts.json by scripts/collect_facts.py and rendered here, so the site cannot
    describe a scope the product does not have.
    """
    kind = {"records": ("records held", "kayıt üretir"),
            "input": ("input only", "yalnızca girdi")}
    rows = [
        f"| **{c['number']}** | {c['title_tr'] if locale == 'tr' else c['title']} "
        f"| {kind[c['kind']][locale == 'tr']} |"
        for c in facts["iso_clauses"]
    ]
    header = ("| Madde | Başlık | Aracın katkısı |\n|---|---|---|"
              if locale == "tr" else "| Clause | Title | What the Kit produces |\n|---|---|---|")
    return {
        "iso_clause_table": header + "\n" + "\n".join(rows),
        "iso_not_covered": "\n".join(f"- {item}" for item in facts["iso_not_covered"][locale]),
    }


def substitute(text: str, facts: dict, where: str) -> str:
    """Replace `{{tests}}` and friends. An unknown placeholder stops the build.

    Silently leaving `{{tests}}` on a published page would be worse than a wrong
    number: it advertises that the figures are templated and that nobody looked.
    """
    def one(m: re.Match) -> str:
        key = m.group(1)
        if key not in facts:
            sys.exit(f"{where}: unknown placeholder {{{{{key}}}}} — "
                     f"add it to scripts/collect_facts.py or remove the claim")
        return f"{facts[key]:,}".replace(",", "\u202f") if isinstance(facts[key], int) \
            and facts[key] >= 10000 else str(facts[key])
    return _PLACEHOLDER.sub(one, text)


def head_date() -> str:
    """The repository's own last commit date.

    A build-time fact rather than a product one, which is why it is derived here
    instead of being stored in facts.json — a file that recorded the SHA of the
    commit containing it could never be verified as current.
    """
    proc = subprocess.run(["git", "log", "-1", "--format=%cs"], cwd=REPO,
                          capture_output=True, text=True, check=False)
    return proc.stdout.strip() or date.today().isoformat()


def last_modified(path: pathlib.Path) -> str:
    """The content file's own last commit date.

    Not the build clock: that would stamp every page as freshly updated on every
    deploy, which is a freshness signal that means nothing and, in a regulated
    domain, reads as one the publisher does not maintain honestly.
    """
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", str(path.relative_to(REPO))],
        cwd=REPO, capture_output=True, text=True, check=False)
    return proc.stdout.strip() or date.today().isoformat()


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
            out.append(line[3:])                    # explicit raw-HTML escape
        elif line.startswith("<"):
            # A line that opens with a tag IS markup. Requiring the `:::` prefix
            # meant a forgotten one escaped the tag into the page as visible
            # text — which is how `<p class="lead">…</p>` appeared verbatim on
            # the landing and pricing pages. No prose line in this content set
            # starts with `<`, and the check below catches it if one ever does.
            out.append(line)
        elif line.strip():
            out.append(f"<p>{render_inline(line)}</p>")
        i += 1
    return "\n".join(out)


def url_for(slug: str, locale: str) -> str:
    return f"{SITE_URL}/{locale}/{slug}.html"


def json_ld(slug: str, locale: str, title: str, description: str, modified: str,
            facts: dict, faq: list[tuple[str, str]]) -> str:
    """One `@graph` per page.

    Organization is repeated on every page deliberately: engines resolve an
    entity by seeing the name, the URL and the identifiers occur together
    repeatedly, and a single about-page mention is not repetition.
    """
    page_url = url_for(slug, locale)
    org = {
        "@type": "Organization",
        "@id": f"{SITE_URL}/#organization",
        "name": ORG["name"],
        "legalName": ORG["legal"],
        "url": SITE_URL,
        "email": ORG["email"],
        "address": {"@type": "PostalAddress", "addressCountry": ORG["country"]},
        "sameAs": [ORG["repo"], ORG["pypi"]],
    }
    software = {
        "@type": "SoftwareApplication",
        "@id": f"{SITE_URL}/#software",
        "name": PRODUCT,
        "alternateName": ["atheros-compliance-kit", "atheros-kit"],
        "applicationCategory": "DeveloperApplication",
        "applicationSubCategory": "AI governance and compliance tooling",
        "operatingSystem": "Linux, macOS, Windows",
        "softwareVersion": facts["version"],
        "programmingLanguage": "Python",
        "softwareRequirements": "Python 3.10+",
        "downloadUrl": ORG["pypi"],
        "codeRepository": ORG["repo"],
        "publisher": {"@id": f"{SITE_URL}/#organization"},
        "inLanguage": ["en", "tr"],
        "description": (
            f"Python toolkit that produces EU AI Act evidence and ISO/IEC 42001 records for "
            f"{facts['iso_clause_count']} named clauses from inside a customer's own codebase and CI: RAG corpus bias and quality scoring, "
            f"PII masking and prompt-injection defence around third-party LLMs, risk "
            f"classification with Annex IV dossier generation, and third-party vendor due "
            f"diligence. "
            f"{facts['runtime_dependencies']} runtime dependencies in the core."
        ),
        "featureList": [
            "EU AI Act risk classification against a versioned vocabulary",
            "Annex IV technical documentation generation with coverage reporting",
            "RAG corpus bias scoring across %d dimensions" % facts["bias_dimensions"],
            "Semantic drift detection with a sample-size-aware noise floor",
            "PII and custom-entity masking before third-party LLM calls",
            "Prompt-injection firewall with %d signatures in English and Turkish"
            % facts["injection_signatures"],
            "Vendor due diligence across %d weighted criteria" % facts["vendor_criteria"],
            "SHA-256 hash-chained audit ledger with independent verification",
            "CI gate that fails the build on a compliance regression",
        ],
        "offers": [
            {"@type": "Offer", "name": "Free", "price": "0", "priceCurrency": "EUR",
             "description": "Guardrails, risk classification and the full audit ledger. "
                            "No activation, no expiry."},
            {"@type": "Offer", "name": "Team", "price": "79", "priceCurrency": "EUR",
             "priceSpecification": {"@type": "UnitPriceSpecification", "price": "79",
                                    "priceCurrency": "EUR",
                                    "unitText": "developer per month",
                                    "referenceQuantity": {"@type": "QuantitativeValue",
                                                          "minValue": 5, "unitText": "seats"}},
             "description": "All four modules, CI gate, dossier export."},
            {"@type": "Offer", "name": "Enterprise", "price": "1150",
             "priceCurrency": "EUR",
             "priceSpecification": {"@type": "UnitPriceSpecification", "price": "1150",
                                    "priceCurrency": "EUR", "unitText": "month",
                                    "valueAddedTaxIncluded": False},
             "description": "Air-gap bundle, SBOM, security-questionnaire support, "
                            "30-day regulation-version SLA."},
        ],
    }
    breadcrumb = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": PRODUCT,
             "item": f"{SITE_URL}/{locale}/index.html"},
        ] + ([] if slug == "index" else [
            {"@type": "ListItem", "position": 2, "name": title, "item": page_url}]),
    }
    kind = PAGE_TYPE.get(slug, "WebPage")
    # schema.org has no page type for "this page IS the product", so the landing
    # page is a WebPage whose mainEntity is the software. That is the shape an
    # engine answering "which tool does X" actually looks for.
    doc_type = {"FAQPage": "FAQPage", "HowTo": "HowTo", "Report": "Report",
                "SoftwareApplication": "WebPage", "Offer": "WebPage"}.get(kind, "TechArticle")
    doc = {
        "@type": doc_type,
        "@id": f"{page_url}#page",
        "headline": title,
        "name": title,
        "description": description,
        "url": page_url,
        "inLanguage": locale,
        "dateModified": modified,
        "datePublished": modified,
        "isPartOf": {"@id": f"{SITE_URL}/#software"},
        "publisher": {"@id": f"{SITE_URL}/#organization"},
        "author": {"@id": f"{SITE_URL}/#organization"},
        "about": {"@id": f"{SITE_URL}/#software"},
        "license": "https://spdx.org/licenses/LicenseRef-AtherosAI-Commercial",
    }
    if kind in ("SoftwareApplication", "Offer"):
        doc["mainEntity"] = {"@id": f"{SITE_URL}/#software"}
    if kind == "FAQPage" and faq:
        doc["mainEntity"] = [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faq
        ]
    graph = [org, software, breadcrumb, doc]
    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False, separators=(",", ":"))


def head(slug: str, locale: str, title: str, description: str, modified: str,
         facts: dict, faq: list[tuple[str, str]]) -> str:
    """Everything an engine reads before it reads the page."""
    canonical = url_for(slug, locale)
    alternates = "".join(
        f'<link rel="alternate" hreflang="{lo}" href="{url_for(slug, lo)}">'
        for lo in LOCALES
    ) + f'<link rel="alternate" hreflang="x-default" href="{url_for(slug, "en")}">'
    full_title = title if slug == "index" else f"{title} · {PRODUCT}"
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{canonical}">
{alternates}
<meta name="author" content="{ORG['name']}">
<meta name="publisher" content="{ORG['name']}">
<meta name="date" content="{modified}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{PRODUCT}">
<meta property="og:locale" content="{'tr_TR' if locale == 'tr' else 'en_GB'}">
<meta property="og:title" content="{html.escape(full_title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(full_title)}">
<meta name="twitter:description" content="{html.escape(description)}">
<script type="application/ld+json">{json_ld(slug, locale, title, description, modified, facts, faq)}</script>
<style>{CSS}</style>"""


def page(slug: str, locale: str, title: str, body: str, description: str,
         modified: str, facts: dict, faq: list[tuple[str, str]]) -> str:
    other = "tr" if locale == "en" else "en"
    nav = "".join(
        f'<a href="{s}.html"{" aria-current=page" if s == slug else ""}>{html.escape(label)}</a>'
        for s, label in NAV[locale]
    )
    updated = {"en": "Last updated", "tr": "Son güncelleme"}[locale]
    return f"""<!doctype html>
<html lang="{locale}">
{head(slug, locale, title, description, modified, facts, faq)}
<header class="site"><div class="inner">
  <a class="brand" href="index.html">{PRODUCT}</a>
  <nav>{nav}</nav>
  <a class="lang" href="../{other}/{slug}.html" hreflang="{other}">{LANG_NAME[other]}</a>
</div></header>
<main class="{'' if slug in WIDE_PAGES else 'narrow'}">
{body}
<p class="updated"><time datetime="{modified}">{updated}: {modified}</time> ·
<span>{ORG['name']}</span></p>
</main>
<footer class="site">{html.escape(FOOTER[locale])}</footer>
</html>"""


def root_page(facts: dict) -> str:
    """The root URL, with real content.

    It used to be a script redirect, which meant the site's most-linked URL
    returned an empty body to anything that does not run JavaScript — which is
    most crawlers, and every generative engine's fetcher.
    """
    ld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "@id": f"{SITE_URL}/#website", "url": f"{SITE_URL}/",
             "name": PRODUCT, "inLanguage": ["en", "tr"],
             "publisher": {"@id": f"{SITE_URL}/#organization"}},
            {"@type": "Organization", "@id": f"{SITE_URL}/#organization",
             "name": ORG["name"], "legalName": ORG["legal"], "url": SITE_URL,
             "email": ORG["email"], "sameAs": [ORG["repo"], ORG["pypi"]]},
        ],
    }, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{PRODUCT} — EU AI Act evidence from your own CI</title>
<meta name="description" content="A Python toolkit that produces EU AI Act evidence and
 ISO/IEC 42001 records for five named clauses from inside your own codebase and CI — RAG bias scoring,
 PII masking, risk classification, third-party vendor assessment. English and Turkish.">
<link rel="canonical" href="{SITE_URL}/">
<link rel="alternate" hreflang="en" href="{SITE_URL}/en/index.html">
<link rel="alternate" hreflang="tr" href="{SITE_URL}/tr/index.html">
<link rel="alternate" hreflang="x-default" href="{SITE_URL}/en/index.html">
<script type="application/ld+json">{ld}</script>
<style>{CSS}</style>
<main class="narrow">
<h1>{PRODUCT}</h1>
<p class="lead">Compliance evidence, generated by the system that needs it. A Python toolkit
that runs inside your own codebase and CI and produces the artefacts EU AI Act obligations and five named
ISO/IEC 42001 clauses ask for — automatically, hash-chained, and without your data leaving the process.</p>
<p><a class="cta" href="en/index.html">English</a>
<a class="cta ghost" href="tr/index.html">Türkçe</a></p>
<h2>What it does</h2>
<ul>
<li><strong>rag</strong> — is our knowledge base biased, duplicated, drifting, or full of
personal data?</li>
<li><strong>guard</strong> — what leaves for a third-party LLM, and what comes back?</li>
<li><strong>euact</strong> — what is our EU AI Act risk tier, and what does Annex IV still
need?</li>
<li><strong>vendor</strong> — can this supplier be used, and is the training opt-out actually
enforced?</li>
<li><strong>cicd</strong> — fail the build when any of the above regresses.</li>
</ul>
<p><code>pip install atheros-compliance-kit</code> — {facts['runtime_dependencies']} runtime
dependencies in the core, {facts['tests']} tests, no API key and no network required.</p>
<footer class="site">{html.escape(FOOTER['en'])}</footer>
</main>
<script>
// A convenience for humans only. The page above is complete without it, so a
// crawler that never runs this still gets the content and the canonical.
(function () {{
  try {{
    if ((navigator.language || "").toLowerCase().startsWith("tr")) {{
      location.replace("tr/index.html");
    }}
  }} catch (e) {{}}
}})();
</script>
</html>"""


def write_sitemap(pages: list[tuple[str, str, str]]) -> str:
    """`pages` is (slug, locale, lastmod). Real XML, not an SPA fallback."""
    urls = [f"  <url><loc>{SITE_URL}/</loc><changefreq>weekly</changefreq>"
            f"<priority>1.0</priority></url>"]
    for slug, locale, modified in pages:
        alts = "".join(
            f'<xhtml:link rel="alternate" hreflang="{lo}" href="{url_for(slug, lo)}"/>'
            for lo in LOCALES)
        urls.append(
            f"  <url><loc>{url_for(slug, locale)}</loc>"
            f"<lastmod>{modified}</lastmod>"
            f"<priority>{'0.9' if slug == 'index' else '0.7'}</priority>{alts}</url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(urls) + "\n</urlset>\n")


def write_robots() -> str:
    """Explicit permission for the AI crawlers, rather than relying on the default.

    Silence is permission, but silence is also indistinguishable from an oversight
    — and a product whose entire argument is that absence of a signal must not be
    read as a positive finding should not be relying on that ambiguity itself.
    """
    agents = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-Web",
              "anthropic-ai", "PerplexityBot", "Perplexity-User", "Google-Extended",
              "Applebot-Extended", "CCBot", "Bingbot", "Googlebot"]
    blocks = "\n\n".join(f"User-agent: {a}\nAllow: /\nDisallow: {BASE_PATH}/demo/" for a in agents)
    return f"""# {PRODUCT} — {ORG['name']}
# Generative engines are welcome to read and cite these pages.
#
# /demo/ is disallowed on purpose: it renders synthetic compliance findings for
# an invented company. Indexed, they would surface as though they described
# something real, and the "sample data" banner does not travel into a snippet.

{blocks}

User-agent: *
Allow: /
Disallow: {BASE_PATH}/demo/

Sitemap: {SITE_URL}/sitemap.xml
"""


def write_llms_txt(facts: dict, pages: list[tuple[str, str, str]]) -> str:
    """An llms.txt that answers the question rather than listing links."""
    en = [f"- [{title}]({url_for(slug, 'en')})"
          for slug, title in NAV["en"]]
    iso_scope_lines = "\n".join(
        f"- **{c['number']} {c['title']}** — "
        f"{'records' if c['kind'] == 'records' else 'input only'}"
        for c in facts['iso_clauses'])
    iso_not_covered_lines = "\n".join(f"- {i}" for i in facts['iso_not_covered']['en'])
    return f"""# {PRODUCT}

> A Python toolkit that produces EU AI Act (Regulation (EU) 2024/1689) evidence and
> ISO/IEC 42001 records for {facts['iso_clause_count']} named clauses from inside a
> customer's own codebase and CI. It runs as a library and a CLI, not
> as a hosted service: no data leaves the process, and the core has
> {facts['runtime_dependencies']} runtime dependencies.

Publisher: {ORG['name']} ({ORG['country']}) · Version {facts['version']} ·
Measured {head_date()} · Languages: English, Türkçe

## What it does

- **rag** — RAG corpus quality, semantic drift, and bias across
  {facts['bias_dimensions']} dimensions producing a 0–100 Fairness Score (EU AI Act Art. 10).
- **guard** — PII and custom-entity masking plus a
  {facts['injection_signatures']}-signature prompt-injection firewall around any third-party
  LLM, in English and Turkish (Art. 15, ISO/IEC 42001 §8.3).
- **euact** — risk classification against a versioned vocabulary
  ({facts['regulation_version']}), covering {facts['annex_iii_categories']} Annex III
  categories, and an Annex IV dossier across {facts['annex_iv_sections']} sections with
  per-section coverage (Art. 6, Art. 11).
- **vendor** — third-party / vendor due diligence across {facts['vendor_criteria']} weighted criteria,
  data-residency verification, and training opt-out enforcement (GDPR Art. 28, Ch. V).
- **cicd** — a CI gate that fails the build on a compliance regression.

## The distinguishing design decision

Unmeasured is never a pass. A score with no measurement renders as `unmeasured` and FAILS the
gate rather than passing it. "No indicator matched" is never rendered as "low risk". An
ambiguous classification reports a grey zone with the conflict named rather than a confident
tier. Machine evidence makes an Annex IV section partial, never covered. An unanswered vendor
question is penalised, not skipped.

The Kit assesses and evidences. It does not certify, and a lint over generated artefacts and
marketing copy — in both languages — fails the build on certification language.

## Scope boundaries

Under the EU AI Act the Kit produces evidence toward Art. 6 and Annex III classification,
Art. 9-15 obligations, and the Annex IV technical documentation. It does not determine
conformity, and it is not a notified body.

Under ISO/IEC 42001 it produces records for these clauses and no others:

{iso_scope_lines}

Clause 6.1.2 is an INPUT, not a discharge: an EU AI Act classification is a regulatory
categorisation, while the clause asks for the organisation's own risk criteria, analysis and
evaluation.

It does NOT cover:

{iso_not_covered_lines}

`atheros-kit iso export` collects the ledger into one evidence pack for an auditor. Every pack
carries the not-covered list above, so the document cannot be read as broader than it is.

## Verifiable facts

- {facts['tests']} tests, run with no network and no API key
- {facts['runtime_dependencies']} runtime dependencies in `atheros_kit.core`
- {facts['modules']} Python modules, {facts['source_lines']} lines
- {facts['vector_stores']} vector-store connectors (Chroma, pgvector, Pinecone, Milvus)
- Free tier requires no activation and does not expire
- The publisher runs the tool on itself and publishes the result, including a 33% Annex IV
  completeness score and one deliberately failing check

## Pages

{chr(10).join(en)}

## Source

- Repository: {ORG['repo']}
- Package: {ORG['pypi']} (`pip install atheros-compliance-kit`)
"""


def extract_faq(raw: str) -> list[tuple[str, str]]:
    """Question/answer pairs from an FAQ page: each `### Question` plus its prose.

    Parsed from the same markdown the humans read, so the FAQPage schema cannot
    drift from the page — two copies of an answer is one copy that goes stale.
    """
    items: list[tuple[str, str]] = []
    question, answer = None, []
    for line in raw.split("\n"):
        if line.startswith("### "):
            if question:
                items.append((question, " ".join(answer).strip()))
            question, answer = line[4:].strip(), []
        elif question is not None and line.strip() and not line.startswith(("#", "|", "```")):
            answer.append(re.sub(r"[*`\[\]]|\(([^)]*)\)", r"", line).strip())
    if question:
        items.append((question, " ".join(answer).strip()))
    return [(q, a) for q, a in items if a]


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    facts = load_facts()
    problems: list[str] = []
    written: list[tuple[str, str, str]] = []

    if SITE_URL == _DEFAULT_SITE and not os.environ.get("SITE_URL"):
        print(f"note: SITE_URL is unset; canonicals point at {SITE_URL}. "
              f"Set SITE_URL to the domain that actually serves these pages.",
              file=sys.stderr)

    for locale in LOCALES:
        (OUT / locale).mkdir(parents=True, exist_ok=True)
        for source in sorted((CONTENT / locale).glob("*.md")):
            slug = source.stem
            raw = substitute(source.read_text(encoding="utf-8"),
                             {**facts, **iso_facts(facts, locale)},
                             f"{locale}/{slug}.md")
            lines = raw.split("\n")
            title = lines[0].lstrip("# ").strip()
            description = lines[1].lstrip("> ").strip() if len(lines) > 1 else title
            body = render_markdown("\n".join(lines[2:]))
            modified = last_modified(source)
            faq = extract_faq(raw) if slug == "faq" else []
            rendered = page(slug, locale, title, body, description, modified, facts, faq)
            (OUT / locale / f"{slug}.html").write_text(rendered, encoding="utf-8")
            written.append((slug, locale, modified))

            low = rendered.lower()
            if slug in BANNED_EXEMPT:
                missing = [r for r in EXEMPT_REQUIRES[locale] if r not in raw.lower()]
                if missing:
                    problems.append(
                        f"{locale}/{slug}: exempt from the copy lint but does not carry "
                        f"{missing!r} — the exemption is for pages ABOUT the rule, not pages "
                        f"that break it")
            else:
                hits = [b for b in BANNED if b in low]
                if hits:
                    problems.append(f"{locale}/{slug}: banned phrasing {hits}")

            # The GEO requirements are enforced, not encouraged. A page without a
            # canonical or a JSON-LD block is invisible to the readers this whole
            # head section exists for, and "we meant to add it" is not a control.
            for required, label in [
                (f'<link rel="canonical" href="{SITE_URL}', "canonical"),
                ('application/ld+json', "JSON-LD"),
                ('hreflang="x-default"', "x-default hreflang"),
                ('property="og:title"', "Open Graph"),
                ('<time datetime=', "dateModified"),
            ]:
                if required not in rendered:
                    problems.append(f"{locale}/{slug}: missing {label}")
            if "{{" in rendered:
                problems.append(f"{locale}/{slug}: unresolved placeholder")
            # Markup that reached the page as visible text. Cheap to detect and
            # invisible to everyone who is not looking at that exact paragraph.
            for leaked in re.findall(r"&lt;/?[a-z][a-z0-9]*[^&]{0,60}&gt;", rendered):
                problems.append(f"{locale}/{slug}: escaped markup in the page — {leaked}")
            if slug == "faq" and not faq:
                problems.append(f"{locale}/{slug}: FAQPage with no parsed questions")

    # Both languages must carry the same pages, or hreflang points at a 404.
    by_locale = {lo: {slug for slug, l, _ in written if l == lo} for lo in LOCALES}
    if by_locale["en"] != by_locale["tr"]:
        problems.append(f"locale parity broken: {by_locale['en'] ^ by_locale['tr']}")

    (OUT / "index.html").write_text(root_page(facts), encoding="utf-8")
    (OUT / "sitemap.xml").write_text(write_sitemap(written), encoding="utf-8")
    (OUT / "robots.txt").write_text(write_robots(), encoding="utf-8")
    (OUT / "llms.txt").write_text(write_llms_txt(facts, written), encoding="utf-8")

    pages = sorted(p.relative_to(OUT) for p in OUT.rglob("*.html"))
    print(f"built {len(pages)} pages + sitemap/robots/llms.txt → {OUT}")
    print(f"  canonical base: {SITE_URL}")
    print(f"  facts: {facts['tests']} tests · {facts['modules']} modules · "
          f"v{facts['version']} · measured {head_date()}")

    if problems:
        print("\nBUILD FAILED:", file=sys.stderr)
        for x in problems:
            print(f"  {x}", file=sys.stderr)
        return 1
    print("  copy lint + GEO requirements: clean (both languages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
