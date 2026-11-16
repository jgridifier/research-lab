#!/usr/bin/env python3
"""Open or adopt one methods-scout feedback issue and update the state file.

    python3 docs/methods-scout/tools/open_scout_issue.py \
        --slug crqa --method CRQA --date 2026-11-14 \
        --question Q1 --page 2026-11-14.html --anchor '#crqa' \
        --top-pick engineering \
        --summary "..." \
        --found-via "..." \
        --robustness "..." \
        --engineering "Effort S. The test: ..." \
        --math "Effort M. The test: ..." \
        --new-use "Effort S. The test: ..." \
        --notes "" \
        --status proposed

Prints the issue number, URL, and the HTML respond block.
Does not open a second issue when the slug (and optional date) is
already in feedback-state.json, or when an issue with the same title
already exists. Use --adopt ISSUE to attach labels + a How-to-respond
comment to an existing issue.

Requires `gh` authenticated to jgridifier/research-lab.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scout_feedback import (  # noqa: E402
    AGENT_MARKER,
    HOW_TO_RESPOND,
    REPO,
    find_by_slug,
    issue_url,
    labels_for,
    load_state,
    page_url,
    respond_block,
    save_state,
    title_for,
)


def _gh(*args: str, input_text: str | None = None) -> str:
    cmd = ["gh", *args]
    res = subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if res.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed:\n{res.stderr.strip() or res.stdout}")
    return res.stdout


def _search_title(title: str) -> int | None:
    q = f'repo:{REPO} is:issue in:title "{title}"'
    out = _gh("issue", "list", "-R", REPO, "--state", "all", "--search", f'in:title "{title}"', "--json", "number,title", "--limit", "20")
    try:
        items = json.loads(out or "[]")
    except json.JSONDecodeError:
        return None
    for it in items:
        if it.get("title") == title:
            return int(it["number"])
    # fallback: API search
    _ = q
    return None


def build_body(args: argparse.Namespace) -> str:
    lines = [AGENT_MARKER, ""]
    lines.append(args.summary.strip())
    lines.append("")
    lines.append(f"**Found via.** {args.found_via.strip()}")
    if args.robustness and args.robustness.strip():
        lines.append("")
        lines.append(f"**Home-field robustness.** {args.robustness.strip()}")
    lines.append("")
    top = (args.top_pick or "").strip()
    def card(name: str, key: str, text: str) -> str:
        mark = " **Top pick.**" if key == top else ""
        return f"- **{name}.** {text.strip()}{mark}"
    lines.append("**Secret-sauce cards.**")
    if args.engineering:
        lines.append(card("Engineering", "engineering", args.engineering))
    if args.math:
        lines.append(card("Math", "math", args.math))
    if args.new_use:
        lines.append(card("New use", "new-use", args.new_use))
    if top == "all":
        lines.append("- All three avenues are in scope.")
    lines.append("")
    anchor = args.anchor if args.anchor.startswith("#") else f"#{args.anchor}"
    lines.append(f"**Scout page.** [{args.page}{anchor}]({page_url(args.page, anchor)})")
    lines.append("")
    lines.append(HOW_TO_RESPOND.rstrip())
    lines.append("")
    return "\n".join(lines)


def upsert_state(args: argparse.Namespace, number: int, created_at: str, labels: list[str]) -> dict:
    state = load_state()
    key = str(number)
    existing = state["issues"].get(key, {})
    history = existing.get("history") or []
    last = existing.get("last_processed_at") or created_at
    entry = {
        "issue": number,
        "slug": args.slug,
        "method": args.method,
        "scout_date": args.date,
        "page": args.page,
        "page_anchor": args.anchor if args.anchor.startswith("#") else f"#{args.anchor}",
        "question": args.question,
        "status": args.status,
        "top_pick": args.top_pick or None,
        "labels": labels,
        "last_processed_at": last,
        "notes": (args.notes or existing.get("notes") or "").strip(),
        "history": history,
    }
    state["issues"][key] = entry
    save_state(state)
    return entry


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--slug", required=True)
    p.add_argument("--method", required=True)
    p.add_argument("--date", required=True, help="Scout edition date, YYYY-MM-DD")
    p.add_argument("--question", required=True, choices=["Q1", "Q2", "Q3", "Q1-retired", "watchlist"])
    p.add_argument("--page", required=True)
    p.add_argument("--anchor", required=True)
    p.add_argument("--top-pick", default=None, choices=["engineering", "math", "new-use", "all", None])
    p.add_argument("--summary", required=True)
    p.add_argument("--found-via", required=True)
    p.add_argument("--robustness", default="")
    p.add_argument("--engineering", default="")
    p.add_argument("--math", default="")
    p.add_argument("--new-use", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--status", default="proposed", choices=["proposed", "approved", "refine", "in-progress", "parked", "dropped", "done"])
    p.add_argument("--adopt", type=int, default=None, help="Adopt this existing issue number instead of opening a new one")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if args.top_pick == "None":
        args.top_pick = None
    if not args.anchor.startswith("#"):
        args.anchor = "#" + args.anchor

    state = load_state()
    found = find_by_slug(state, args.slug, args.date) or find_by_slug(state, args.slug)
    title = title_for(args.date, args.method, args.question)
    labels = labels_for(args.question, args.status, args.top_pick)

    if found and not args.adopt:
        print(f"already in state: issue #{found['issue']} slug={args.slug} date={found.get('scout_date')}", file=sys.stderr)
        print(respond_block(found))
        print(issue_url(found["issue"]))
        return 0

    if args.dry_run:
        print("TITLE:", title)
        print("LABELS:", ", ".join(labels))
        print(build_body(args))
        return 0

    number = args.adopt
    if number is None:
        existing = _search_title(title)
        if existing:
            print(f"title already exists as issue #{existing}; adopting", file=sys.stderr)
            number = existing

    body = build_body(args)
    if number is None:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write(body)
            body_path = fh.name
        label_args = []
        for lab in labels:
            label_args.extend(["--label", lab])
        url = _gh(
            "issue", "create", "-R", REPO,
            "--title", title,
            "--body-file", body_path,
            *label_args,
        ).strip()
        data = json.loads(_gh("issue", "view", url, "-R", REPO, "--json", "number,url,createdAt"))
        number = int(data["number"])
        created_at = data.get("createdAt") or data.get("created_at")
        print(f"created issue #{number} {data.get('url') or url}", file=sys.stderr)
    else:
        # adopt: set labels (additive via gh edit --add-label) and ensure how-to-respond is present
        view = json.loads(_gh("issue", "view", str(number), "-R", REPO, "--json", "number,title,body,createdAt,labels"))
        created_at = view.get("createdAt")
        existing_labels = {l["name"] if isinstance(l, dict) else l for l in view.get("labels", [])}
        missing = [l for l in labels if l not in existing_labels]
        if missing:
            _gh("issue", "edit", str(number), "-R", REPO, *[a for l in missing for a in ("--add-label", l)])
        body_now = view.get("body") or ""
        if "How to respond" not in body_now:
            comment = f"{AGENT_MARKER}\n\nAdopting this issue for the methods-scout feedback loop.\n\n{HOW_TO_RESPOND}"
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
                fh.write(comment)
                cpath = fh.name
            _gh("issue", "comment", str(number), "-R", REPO, "--body-file", cpath)
        print(f"adopted issue #{number} {issue_url(number)}", file=sys.stderr)

    entry = upsert_state(args, number, created_at, labels)
    print(f"ISSUE={number}")
    print(issue_url(number))
    print(respond_block(entry), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
