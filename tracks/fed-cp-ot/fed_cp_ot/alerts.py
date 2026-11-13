"""CI alerting: ::error annotations and a de-duplicated GitHub issue via the gh CLI."""
import json
import os
import subprocess


def error_annotation(message):
    text = message.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    print(f'::error title=fed-cp-ot::{text}', flush=True)


def run_url(env=os.environ):
    if env.get('GITHUB_RUN_ID') and env.get('GITHUB_REPOSITORY'):
        return f"{env.get('GITHUB_SERVER_URL', 'https://github.com')}/{env['GITHUB_REPOSITORY']}/actions/runs/{env['GITHUB_RUN_ID']}"
    return '(local run)'


def open_or_update_issue(title, body, runner=subprocess.run):
    """Comment on the open issue with this exact title, else open one. Returns 'commented' or 'created'."""
    listed = runner(['gh', 'issue', 'list', '--state', 'open', '--search', f'"{title}" in:title',
                     '--json', 'number,title'], capture_output=True, text=True, check=True)
    match = next((i for i in json.loads(listed.stdout or '[]') if i['title'] == title), None)
    if match:
        runner(['gh', 'issue', 'comment', str(match['number']), '--body', body], check=True)
        return 'commented'
    runner(['gh', 'issue', 'create', '--title', title, '--body', body], check=True)
    return 'created'


def alert(title, message, issue=False, runner=subprocess.run):
    """Annotate the failure; with `issue`, also open/update the issue. A failing issue call never hides the error."""
    error_annotation(f'{title}: {message}')
    if not issue:
        return None
    try:
        return open_or_update_issue(title, f'{message}\n\nRun: {run_url()}', runner=runner)
    except (subprocess.CalledProcessError, OSError, ValueError) as exc:
        print(f'::warning title=fed-cp-ot::could not open issue: {exc}', flush=True)
        return None
