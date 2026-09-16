#!/usr/bin/env python3
"""Refreshes the public Daily Bug Comment Check dashboard for Learn\\Maintenance\\Elite.

Pulls active bugs from Azure DevOps, finds each one's most recent comment,
flags any with no comment in the last 2+ days, and writes:
  - <repo>/bug-comment-check.html  (published via GitHub Pages)
  - <repo>/data/bug_comment_check.json

Auth: reads ADO_PAT from the environment (GitHub Actions secret) first; falls
back to the local gradebook_rag config for manual/local runs.
"""
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
AREA_PATH = r"Learn\Maintenance\Elite"
STALE_DAYS_THRESHOLD = 2
ACTIVE_STATES = ["In Progress", "In Review", "Branch Testing", "Awaiting DoD", "Rejected"]
REFRESH_SECONDS = 900  # browser auto-reload interval on the published page
SCHEDULE_NOTE = "9:00 AM & 7:00 PM IST"

ORG = os.environ.get("ADO_ORG", "Blackboard-01")
PROJECT = os.environ.get("ADO_PROJECT", "Learn")
PAT = os.environ.get("ADO_PAT", "")

if not PAT:
    import importlib.util

    spec = importlib.util.spec_from_file_location("cfg", "/Users/gayathri/Documents/gradebook_rag/config.py")
    cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cfg)
    ORG = cfg.ADO_ORG
    PROJECT = cfg.ADO_PROJECT
    PAT = cfg.ADO_PAT

if not PAT:
    raise SystemExit("ERROR: ADO_PAT not set (env var or local config fallback)")

_auth = base64.b64encode(f":{PAT}".encode()).decode()
_HEADERS = {"Authorization": f"Basic {_auth}", "Content-Type": "application/json"}


def _parse_ado_datetime(raw):
    """ADO timestamps have 0-7 fractional digits; fromisoformat needs 0, 3, or 6."""
    s = raw.replace("Z", "+00:00")
    match = re.match(r"^(.*?\.)(\d+)(\+00:00)$", s)
    if match:
        prefix, frac, suffix = match.groups()
        frac = (frac + "000000")[:6]
        s = f"{prefix}{frac}{suffix}"
    return datetime.fromisoformat(s)


def _get(url):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def _post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=_HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def find_active_bugs():
    states_clause = ", ".join(f"'{s}'" for s in ACTIVE_STATES)
    wiql = f"""
    SELECT [System.Id]
    FROM WorkItems
    WHERE [System.TeamProject] = '{PROJECT}'
      AND [System.WorkItemType] = 'Bug'
      AND [System.AreaPath] = '{AREA_PATH}'
      AND [System.State] IN ({states_clause})
    ORDER BY [System.Id]
    """
    url = f"https://dev.azure.com/{ORG}/{urllib.parse.quote(PROJECT)}/_apis/wit/wiql?api-version=7.1"
    result = _post(url, {"query": wiql})
    return [wi["id"] for wi in result.get("workItems", [])]


def get_bug_fields(ids):
    if not ids:
        return {}
    url = f"https://dev.azure.com/{ORG}/_apis/wit/workitemsbatch?api-version=7.1"
    body = {
        "ids": ids,
        "fields": ["System.Id", "System.Title", "System.State", "System.AssignedTo", "System.ChangedDate"],
    }
    result = _post(url, body)
    return {wi["id"]: wi["fields"] for wi in result.get("value", [])}


def get_last_comment_date(bug_id):
    url = (
        f"https://dev.azure.com/{ORG}/{urllib.parse.quote(PROJECT)}/_apis/wit/workItems/"
        f"{bug_id}/comments?api-version=7.1-preview.3&$top=1&$order=desc"
    )
    try:
        result = _get(url)
    except urllib.error.HTTPError:
        return None
    comments = result.get("comments", [])
    if not comments:
        return None
    return comments[0]["modifiedDate"]


def build_dataset():
    ids = find_active_bugs()
    fields_by_id = get_bug_fields(ids)
    now = datetime.now(timezone.utc)
    flagged = []
    for bug_id in ids:
        fields = fields_by_id.get(bug_id, {})
        last_comment_raw = get_last_comment_date(bug_id)
        source = "comment" if last_comment_raw else "changed_date"
        last_activity_raw = last_comment_raw or fields.get("System.ChangedDate")
        if not last_activity_raw:
            continue
        last_activity = _parse_ado_datetime(last_activity_raw)
        days_since = (now - last_activity).days
        if days_since < STALE_DAYS_THRESHOLD:
            continue
        assigned_to = fields.get("System.AssignedTo", {})
        flagged.append(
            {
                "id": bug_id,
                "title": fields.get("System.Title", ""),
                "assignee": assigned_to.get("displayName", "Unassigned") if isinstance(assigned_to, dict) else str(assigned_to),
                "state": fields.get("System.State", ""),
                "last_activity_date": last_activity.strftime("%d %b %Y"),
                "last_activity_source": source,
                "days_since": days_since,
            }
        )
    flagged.sort(key=lambda b: b["days_since"], reverse=True)
    return {
        "generated_at_utc": now.isoformat(),
        "generated_at_display": now.strftime("%d %b %Y, %H:%M UTC"),
        "area_path": AREA_PATH,
        "active_states": ACTIVE_STATES,
        "stale_days_threshold": STALE_DAYS_THRESHOLD,
        "total_active_bugs": len(ids),
        "flagged": flagged,
    }


def severity(days):
    if days >= 7:
        return "critical", "Critical"
    if days >= 4:
        return "serious", "Serious"
    return "warning", "Warning"


def _escape(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html(data):
    org_url = f"https://dev.azure.com/{ORG}/{urllib.parse.quote(PROJECT)}/_workitems/edit/"
    flagged = data["flagged"]
    total_flagged = len(flagged)
    oldest_gap = flagged[0]["days_since"] if flagged else 0
    by_assignee = {}
    for b in flagged:
        by_assignee[b["assignee"]] = by_assignee.get(b["assignee"], 0) + 1
    top_assignee = max(by_assignee.items(), key=lambda kv: kv[1]) if by_assignee else ("-", 0)

    rows = []
    for b in flagged:
        sev_key, sev_label = severity(b["days_since"])
        rows.append(
            f"""
            <tr>
              <td><a class="bug-link" href="{org_url}{b['id']}" target="_blank" rel="noopener">#{b['id']}</a></td>
              <td class="title-cell">{_escape(b['title'])}</td>
              <td>{_escape(b['assignee'])}</td>
              <td>{_escape(b['state'])}</td>
              <td class="num">{_escape(b['last_activity_date'])}</td>
              <td class="num">
                <span class="status-pill status-{sev_key}">
                  <span class="status-dot"></span>{sev_label} · {b['days_since']}d
                </span>
              </td>
            </tr>"""
        )
    rows_html = "\n".join(rows) if rows else (
        '<tr><td colspan="6" class="empty-state">No stale bugs — everyone has commented within '
        f'{data["stale_days_threshold"]} days.</td></tr>'
    )
    states_label = ", ".join(data["active_states"])

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="{REFRESH_SECONDS}">
<title>Daily Bug Comment Check — {_escape(data['area_path'])}</title>
<style>
  .viz-root {{
    color-scheme: dark;
    --surface-1: #1a1a19;
    --page-plane: #0d0d0d;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted: #898781;
    --gridline: #2c2c2a;
    --border: rgba(255,255,255,0.10);
    --status-good: #0ca30c;
    --status-warning: #fab219;
    --status-serious: #ec835a;
    --status-critical: #d03b3b;
    --series-blue: #3987e5;
    --series-orange: #d95926;
    --series-aqua: #199e70;
    --series-violet: #9085e9;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    background: var(--page-plane);
    color: var(--text-primary);
  }}
  .page {{ max-width: 1080px; margin: 0 auto; padding: 32px 24px 64px; }}
  header.page-head {{ margin-bottom: 24px; }}
  h1 {{
    font-size: 22px;
    margin: 0 0 4px;
    background: linear-gradient(90deg, var(--series-blue), var(--series-violet));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    display: inline-block;
  }}
  .subhead {{ color: var(--text-secondary); font-size: 14px; margin: 0; }}
  .meta-row {{ color: var(--text-muted); font-size: 12px; margin-top: 8px; }}
  .stat-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 24px 0; }}
  .stat-tile {{
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-top: 3px solid var(--accent, var(--border));
    border-radius: 8px;
    padding: 16px;
  }}
  .stat-tile .label {{ color: var(--text-secondary); font-size: 12px; margin-bottom: 8px; font-weight: 500; }}
  .stat-tile .value {{ font-size: 30px; font-weight: 700; line-height: 1.1; color: var(--text-primary); font-variant-numeric: tabular-nums; }}
  .stat-tile .value.accent-critical {{ color: var(--status-critical); }}
  table {{
    width: 100%;
    border-collapse: collapse;
    background: var(--surface-1);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    font-size: 13px;
  }}
  thead th {{
    text-align: left;
    font-weight: 700;
    color: var(--series-blue);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 12px;
    background: rgba(57, 135, 229, 0.08);
    border-bottom: 1px solid var(--gridline);
  }}
  tbody td {{ padding: 12px; border-bottom: 1px solid var(--gridline); vertical-align: top; color: var(--text-primary); }}
  tbody tr:last-child td {{ border-bottom: none; }}
  tbody tr:hover td {{ background: rgba(255,255,255,0.03); }}
  td.num {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
  td.title-cell {{ max-width: 360px; color: var(--text-secondary); }}
  a.bug-link {{ color: var(--series-blue); text-decoration: none; font-weight: 600; }}
  a.bug-link:hover {{ text-decoration: underline; }}
  .status-pill {{ display: inline-flex; align-items: center; gap: 6px; font-weight: 600; white-space: nowrap; }}
  .status-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
  .status-warning .status-dot {{ background: var(--status-warning); }}
  .status-serious .status-dot {{ background: var(--status-serious); }}
  .status-critical .status-dot {{ background: var(--status-critical); }}
  .status-warning {{ color: var(--status-warning); }}
  .status-serious {{ color: var(--status-serious); }}
  .status-critical {{ color: var(--status-critical); }}
  .empty-state {{ text-align: center; color: var(--text-secondary); padding: 24px; }}
  footer {{ margin-top: 16px; color: var(--text-muted); font-size: 12px; }}
  a.nav-back {{ color: var(--series-blue); font-size: 13px; text-decoration: none; }}
  a.nav-back:hover {{ text-decoration: underline; }}
  @media (max-width: 720px) {{
    .stat-grid {{ grid-template-columns: repeat(2, 1fr); }}
    td.title-cell {{ max-width: 160px; }}
  }}
</style>
</head>
<body>
  <div class="viz-root page">
    <p style="margin:0 0 12px;"><a class="nav-back" href="index.html">&larr; All dashboards</a></p>
    <header class="page-head">
      <div class="head-text">
        <h1>Daily Bug Comment Check — {_escape(data['area_path'])}</h1>
        <p class="subhead">Active bugs ({_escape(states_label)}) with no comment update in the last {data['stale_days_threshold']}+ days. Please add your latest progress.</p>
        <p class="meta-row">Generated {data['generated_at_display']} · auto-refreshes {SCHEDULE_NOTE} via GitHub Actions</p>
      </div>
    </header>

    <div class="stat-grid">
      <div class="stat-tile" style="--accent: var(--series-blue);">
        <div class="label">Active bugs checked</div>
        <div class="value">{data['total_active_bugs']}</div>
      </div>
      <div class="stat-tile" style="--accent: var(--series-orange);">
        <div class="label">Flagged — stale comments</div>
        <div class="value">{total_flagged}</div>
      </div>
      <div class="stat-tile" style="--accent: {'var(--status-critical)' if oldest_gap >= 7 else 'var(--series-aqua)'};">
        <div class="label">Oldest gap</div>
        <div class="value {'accent-critical' if oldest_gap >= 7 else ''}">{oldest_gap}d</div>
      </div>
      <div class="stat-tile" style="--accent: var(--series-violet);">
        <div class="label">Most flagged assignee</div>
        <div class="value" style="font-size:18px;">{_escape(top_assignee[0])} ({top_assignee[1]})</div>
      </div>
    </div>

    <table>
      <thead>
        <tr><th>Bug</th><th>Title</th><th>Assignee</th><th>State</th><th>Last Activity</th><th>Gap</th></tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>

    <footer>Source: Azure DevOps · {ORG}/{PROJECT} · Last activity falls back to System.ChangedDate when a bug has no comments.</footer>
  </div>
</body>
</html>
"""


def main():
    data = build_dataset()
    data_dir = WORKSPACE / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "bug_comment_check.json").write_text(json.dumps(data, indent=2))
    (WORKSPACE / "bug-comment-check.html").write_text(render_html(data))
    print(f"Wrote {len(data['flagged'])} flagged bugs to bug-comment-check.html")


if __name__ == "__main__":
    main()
