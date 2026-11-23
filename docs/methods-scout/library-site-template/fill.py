#!/usr/bin/env python3
"""Copy the library site template into a repo's docs/ folder and fill its tokens.

    python3 fill.py --config site.json --out ../../../../my-lib/docs

site.json maps token names (without braces) to text or HTML, e.g.
{"LIB_NAME": "proprlite", "REPO_URL": "https://github.com/jgridifier/proprlite", ...}.
Unfilled tokens are listed at the end; the exit code is 1 if any remain, so CI can
catch a half-filled site. Existing files in --out are overwritten only with --force.
"""
import argparse, json, pathlib, re, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
PAGES = ["index.html", "how-it-works.html", "quickstart.html", "example.html", "judging.html",
         "benchmarks.html", "api.html", "provenance.html", "cite.html"]
TOKEN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="JSON file of token -> value")
    ap.add_argument("--out", required=True, help="target docs/ folder")
    ap.add_argument("--force", action="store_true", help="overwrite existing pages")
    a = ap.parse_args()
    values = json.loads(pathlib.Path(a.config).read_text())
    out = pathlib.Path(a.out)
    (out / "assets").mkdir(parents=True, exist_ok=True)
    for name in ("site.css", "site.js"):
        shutil.copy2(HERE / "assets" / name, out / "assets" / name)
    left = set()
    for page in PAGES:
        dst = out / page
        if dst.exists() and not a.force:
            print(f"skip {dst} (exists; use --force)")
            continue
        text = TOKEN.sub(lambda m: str(values.get(m.group(1), m.group(0))), (HERE / page).read_text())
        left |= set(TOKEN.findall(text))
        dst.write_text(text)
        print(f"wrote {dst}")
    if not (out / ".nojekyll").exists():
        (out / ".nojekyll").write_text("")
    if left:
        print("unfilled tokens:", ", ".join(sorted(left)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
