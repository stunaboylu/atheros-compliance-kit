#!/usr/bin/env python3
"""Measure the product, so no surface has to remember a number.

Three surfaces carried three different test counts — 102, 146 and 177 — because
each was typed by hand at a different moment. A generative engine quoting the
wrong one spreads it under the brand's name, and a reader who notices the
contradiction discounts everything else on the page.

Every number the site or the READMEs state about the product is produced here,
at build time, from the thing it describes. `site/build.py` substitutes them and
fails the build on an unresolved placeholder — so a new claim has to be measured
before it can be published.

    python scripts/collect_facts.py            # → site/facts.json
    python scripts/collect_facts.py --print
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PKG = ROOT / "atheros-compliance-kit"
SRC = PKG / "src" / "atheros_kit"
OUT = ROOT / "site" / "facts.json"


def _python() -> str:
    """The package's own interpreter if there is one, else this one."""
    venv = PKG / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def count_tests() -> int:
    """From pytest itself. A hand-written count is wrong by the next commit."""
    proc = subprocess.run(
        [_python(), "-m", "pytest", "--collect-only", "-q"],
        cwd=PKG, capture_output=True, text=True, check=False,
    )
    combined = proc.stdout + proc.stderr
    if "No module named pytest" in combined:
        sys.exit(
            "pytest is not installed for "
            f"{_python()}, so the test count cannot be measured.\n"
            "Install it:  pip install -e 'atheros-compliance-kit[dev]'\n"
            "Refusing to fall back to a hand-written number — a figure nobody measured "
            "is exactly what this script exists to remove."
        )
    match = re.search(r"(\d+) tests? collected", combined)
    if not match:
        sys.exit("could not read a test count from pytest "
                 f"(exit {proc.returncode}):\n{combined[-1200:]}")
    return int(match.group(1))


def count_source() -> tuple[int, int]:
    files = sorted(SRC.rglob("*.py"))
    lines = sum(len(f.read_text(encoding="utf-8").splitlines()) for f in files)
    return len(files), lines


def introspect() -> dict:
    """Ask the package, rather than counting entries in a file by eye."""
    code = (
        "import sys, json; sys.path.insert(0, 'src')\n"
        "from atheros_kit.vendor import CRITERIA\n"
        "from atheros_kit.guard import injection\n"
        "from atheros_kit.rag import DIMENSIONS\n"
        "from atheros_kit.euact.vocabulary import ANNEX_III_CATEGORIES, REGULATION_VERSION\n"
        "from atheros_kit.euact.dossier import SECTIONS\n"
        "from atheros_kit.rag.connectors import _REGISTRY\n"
        "from atheros_kit.iso.clauses import CLAUSES, NOT_COVERED, TR\n"
        "print(json.dumps({\n"
        "  'vendor_criteria': len(CRITERIA),\n"
        "  'injection_signatures': len(injection.SIGNATURES),\n"
        "  'bias_dimensions': len(DIMENSIONS),\n"
        "  'annex_iii_categories': len(ANNEX_III_CATEGORIES),\n"
        "  'annex_iv_sections': len(SECTIONS),\n"
        "  'vector_stores': len(_REGISTRY) - 1,\n"
        "  'regulation_version': REGULATION_VERSION,\n"
        "  'iso_clause_count': len(CLAUSES),\n"
        "  'iso_clauses': [{'number': c.number, 'kind': c.kind, 'title': c.title,\n"
        "                   'title_tr': TR[c.number][0]} for c in CLAUSES],\n"
        "  'iso_not_covered': {k: list(v) for k, v in NOT_COVERED.items()},\n"
        "}))\n"
    )
    proc = subprocess.run([_python(), "-c", code], cwd=PKG,
                          capture_output=True, text=True, check=False)
    if proc.returncode:
        sys.exit(f"introspection failed:\n{proc.stderr[-800:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def version() -> str:
    text = (PKG / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version = "([^"]+)"', text, re.M).group(1)


def last_modified(path: pathlib.Path) -> str:
    """The file's last commit date — a real freshness signal rather than the
    build clock, which would mark every page as updated on every deploy."""
    proc = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", str(path.relative_to(ROOT))],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    return proc.stdout.strip() or subprocess.run(
        ["git", "log", "-1", "--format=%cs"], cwd=ROOT,
        capture_output=True, text=True, check=False).stdout.strip()


def collect() -> dict:
    modules, lines = count_source()
    facts = {
        "version": version(),
        "tests": count_tests(),
        "modules": modules,
        "source_lines": lines,
        "runtime_dependencies": 0,
        "languages": 2,
        **introspect(),
    }
    # Deliberately NOT recorded here: the commit SHA and the build date.
    #
    # They describe the build rather than the product, and including them made
    # this file impossible to keep fresh — it cannot record the SHA of the commit
    # that contains it, so the CI staleness gate failed on every push whether or
    # not anything about the product had changed. The site derives both from git
    # at render time instead.
    return facts


def main(show: bool = False) -> int:
    facts = collect()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(facts, indent=2) + "\n", encoding="utf-8")
    if show:
        for k, v in facts.items():
            print(f"  {k:24} {v}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="show", action="store_true")
    raise SystemExit(main(**vars(ap.parse_args())))
