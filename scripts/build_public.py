#!/usr/bin/env python3
"""Build the public deployment: marketing site at `/`, console demo at `/demo`.

One output tree, one domain, one deploy. The console is the demo rather than a
separate product surface, so a relative link from the site reaches it and there
is no second certificate, second domain, or second thing to forget to renew.

Everything published here is static and synthetic:

  * the site is generated from `site/content/**` by `site/build.py`, which fails
    the build on certification language in either language;
  * the console renders `console/data/`, which is real toolkit output over an
    invented corpus, and says so in an unmissable banner and inside every file
    it exports.

    python scripts/build_public.py            # → public/
    python scripts/build_public.py --site-only
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "public"


def run(cmd: list[str], cwd: pathlib.Path) -> None:
    print(f"$ {' '.join(cmd)}  (in {cwd.relative_to(ROOT)})", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main(site_only: bool = False) -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # ── measured facts → the site's numbers ──────────────────────────────────
    # Before the site, not after: build.py refuses to publish a page carrying an
    # unresolved placeholder, and every figure on those pages comes from here.
    run([sys.executable, "scripts/collect_facts.py"], ROOT)

    # ── marketing site → / ───────────────────────────────────────────────────
    run([sys.executable, "site/build.py"], ROOT)
    site_dist = ROOT / "site" / "dist"
    if not site_dist.is_dir():
        sys.exit("site/build.py produced no dist/")
    shutil.copytree(site_dist, OUT, dirs_exist_ok=True)

    if site_only:
        print(f"\nsite only → {OUT}")
        return 0

    # ── console demo → /demo ─────────────────────────────────────────────────
    console = ROOT / "console"
    # `npm ci` rather than `npm install`: the lockfile is the deployment's
    # contract, and a build that silently resolves a different tree than the one
    # tested is a build whose output nobody has actually seen.
    run(["npm", "ci", "--no-audit", "--no-fund"], console)
    run(["npx", "expo", "export", "--platform", "web"], console)

    console_dist = console / "dist"
    if not console_dist.is_dir():
        sys.exit("expo export produced no dist/")
    shutil.copytree(console_dist, OUT / "demo", dirs_exist_ok=True)

    # A static export written for `/` has absolute asset paths, so serving it
    # from `/demo` would 404 on every script and stylesheet. Rewrite them.
    rewritten = 0
    for page in (OUT / "demo").rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        fixed = text.replace('="/_expo/', '="/demo/_expo/').replace('="/assets/', '="/demo/assets/')
        if fixed != text:
            page.write_text(fixed, encoding="utf-8")
            rewritten += 1

    pages = sorted(p.relative_to(OUT) for p in OUT.rglob("*.html"))
    print(f"\nbuilt {len(pages)} pages → {OUT}  ({rewritten} rebased under /demo)")
    for name in ("robots.txt", "sitemap.xml", "llms.txt"):
        if not (OUT / name).exists():
            sys.exit(f"{name} is missing from the deployment — an engine that cannot find "
                     f"the sitemap crawls what it happens to stumble on")
        print(f"  {name}")
    for p in pages:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-only", action="store_true",
                    help="skip the console (no npm install needed)")
    raise SystemExit(main(**vars(ap.parse_args())))
