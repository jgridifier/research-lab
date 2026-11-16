#!/usr/bin/env python3
"""Shared helpers for the methods-scout feedback loop.

See docs/methods-scout/FEEDBACK.md for the contract.
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

SCOUT_DIR = Path(__file__).resolve().parent.parent
STATE_PATH = SCOUT_DIR / "feedback-state.json"
BOARD_PATH = SCOUT_DIR / "board.html"
REPO = "jgridifier/research-lab"
PAGES_BASE = "https://jgridifier.github.io/research-lab/methods-scout"
ISSUE_BASE = f"https://github.com/{REPO}/issues"
AGENT_MARKER = "<!-- quant-scout-bot -->"

STATUSES = [
    "proposed",
    "approved",
    "refine",
    "in-progress",
    "parked",
    "dropped",
    "done",
]
STATUS_LABEL = {
    "proposed": "Proposed",
    "approved": "Approved",
    "refine": "Refine",
    "in-progress": "In progress",
    "parked": "Parked",
    "dropped": "Dropped",
    "done": "Done",
}
QUESTION_LABEL = {
    "Q1": "scout:Q1",
    "Q2": "scout:Q2",
    "Q3": "scout:Q3",
    "Q1-retired": "scout:Q1-retired",
    "watchlist": None,
}
PICKS = ("engineering", "math", "new-use", "all")

RESPOND_HINT = (
    "👍 go ahead with the top pick · 👎 drop it · 👀 park for later · "
    "or comment <code>go engineering</code>, <code>go math</code>, "
    "<code>go new use</code>, <code>go all</code>, "
    "<code>refine: &lt;what to change&gt;</code>, "
    "<code>promote</code>, <code>park</code>, <code>drop</code>."
)

HOW_TO_RESPOND = """## How to respond

React on this issue (do not comment just to vote):

- 👍 = go ahead with the top pick
- 👎 = drop it
- 👀 = park for later

Or comment one of:

- `go engineering` · `go math` · `go new use` · `go all`
- `refine: <what to change>`
- `promote` (move into analysis-skills)
- `park`
- `drop`

Free-text comments are read as refinement notes. A daily scanner picks this up; you do not need to @-mention anyone.
"""


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"version": 1, "repo": REPO, "updated_at": None, "issues": {}}
    data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    data.setdefault("version", 1)
    data.setdefault("repo", REPO)
    data.setdefault("issues", {})
    return data


def save_state(state: dict) -> None:
    state["version"] = 1
    state["repo"] = REPO
    state["updated_at"] = now_utc()
    STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def issue_url(number: int | str) -> str:
    return f"{ISSUE_BASE}/{number}"


def page_url(page: str, anchor: str = "") -> str:
    return f"{PAGES_BASE}/{page}{anchor or ''}"


def title_for(scout_date: str, method: str, question: str) -> str:
    suffix = "watchlist" if question == "watchlist" else question
    return f"[Scout {scout_date}] {method} — {suffix}"


def labels_for(question: str, status: str, top_pick: str | None) -> list[str]:
    labels = ["scout"]
    q = QUESTION_LABEL.get(question)
    if q:
        labels.append(q)
    if question == "watchlist":
        labels.append("watchlist")
    labels.append(f"status:{status}")
    if top_pick == "all":
        labels.extend(["pick:engineering", "pick:math", "pick:new-use"])
    elif top_pick in ("engineering", "math", "new-use"):
        labels.append(f"pick:{top_pick}")
    return labels


def find_by_slug(state: dict, slug: str, scout_date: str | None = None) -> dict | None:
    for entry in state.get("issues", {}).values():
        if entry.get("slug") != slug:
            continue
        if scout_date is None or entry.get("scout_date") == scout_date:
            return entry
    return None


def respond_block(entry: dict) -> str:
    """Static HTML for the Respond-on-GitHub control, rendered from state."""
    number = entry["issue"]
    status = entry.get("status", "proposed")
    chip = STATUS_LABEL.get(status, status)
    href = html.escape(issue_url(number), quote=True)
    return (
        f'<aside class="scout-respond" data-issue="{html.escape(str(number))}" data-slug="{html.escape(entry.get("slug", ""))}">\n'
        f'  <span class="scout-chip status-{html.escape(status)}">{html.escape(chip)}</span>\n'
        f'  <a class="scout-respond-btn" href="{href}">Respond on GitHub</a>\n'
        f'  <p class="scout-respond-hint">{RESPOND_HINT}</p>\n'
        f"</aside>\n"
    )


def stylesheet_tag() -> str:
    return '<link rel="stylesheet" href="feedback.css">'
