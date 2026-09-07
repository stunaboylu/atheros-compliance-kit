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


def package_present() -> bool:
    """Whether the Python package is complete enough to be measured.

    Every file `collect_facts.py` opens, not just the directory it lives in. A
    hosting provider's ignore rules removed `pyproject.toml` while leaving `src/`
    behind, so a check for the directory alone said yes and the collector then
    died on the missing file — a guard that passes on a half-present tree is
    worse than none, because it turns a clean fallback into a crash.
    """
    pkg = ROOT / "atheros-compliance-kit"
    return all((pkg / part).exists() for part in
               ("pyproject.toml", "src/atheros_kit/__init__.py", "tests"))


def run(cmd: list[str], cwd: pathlib.Path) -> None:
    print(f"$ {' '.join(cmd)}  (in {cwd.relative_to(ROOT)})", flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main(site_only: bool = False, out: str | None = None) -> int:
    global OUT
    if out:
        OUT = pathlib.Path(out).resolve()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # ── measured facts → the site's numbers ──────────────────────────────────
    # Before the site, not after: build.py refuses to publish a page carrying an
    # unresolved placeholder, and every figure on those pages comes from here.
    #
    # site/facts.json is COMMITTED, so a deploy that does not ship the Python
    # package (the hosting build only needs the site and the console) still
    # publishes measured numbers. Where the package IS present the file is
    # regenerated, and CI fails if the committed copy has gone stale — the same
    # arrangement SELF_ASSESSMENT.md uses.
    committed = ROOT / "site" / "facts.json"
    if package_present():
        # The package is here, so the numbers must come from it. A measurement
        # that fails while the source is available is a real breakage, not a
        # reason to reach for the committed copy — falling back there would let
        # a broken collector ship stale figures indefinitely.
        run([sys.executable, "scripts/collect_facts.py"], ROOT)
    elif committed.exists():
        print("note: the Python package is not in this checkout; using the committed "
              "site/facts.json rather than remeasuring.", flush=True)
    else:
        sys.exit("neither the package nor site/facts.json is present — the site states "
                 "measured numbers and will not publish guessed ones")

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
    ap.add_argument("--out", help="output directory (default: <repo>/public). Hosting "
                                  "providers run the build from their own working "
                                  "directory and expect the output beside it.")
    raise SystemExit(main(**vars(ap.parse_args())))
