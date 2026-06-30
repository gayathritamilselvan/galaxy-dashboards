import json, datetime, html as html_mod
from collections import Counter

with open("/tmp/galaxy_prs_detailed.json") as f:
    pr_details = json.load(f)

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

TEAM_ORDER = ["Celeste", "Mars", "Pallavas", "Pandias", "Cholas", "Supernova", "Starlite", "Elite", "Nayakas", "Oxygen"]
TEAM_COLORS = {
    "Celeste": ("#1a2a3d", "#79c0ff"),
    "Mars": ("#3d1a1a", "#f97583"),
    "Pallavas": ("#1a3d2a", "#7ee787"),
    "Pandias": ("#3d2a1a", "#f0883e"),
    "Cholas": ("#2a1a3d", "#d2a8ff"),
    "Supernova": ("#3d3d1a", "#f2cc60"),
    "Starlite": ("#1a3d3d", "#56d4dd"),
    "Elite": ("#3d1a3d", "#ff7b72"),
    "Nayakas": ("#1a1a3d", "#a5d6ff"),
    "Oxygen": ("#2a3d1a", "#aff5b4"),
}

STATE_BADGE = {
    "Open": ("#238636", "Open"),
    "Draft": ("#8b949e", "Draft"),
    "Merged": ("#a371f7", "Merged"),
    "Closed": ("#f85149", "Closed"),
}

# Summary stats
total_prs = len(pr_details)
open_prs = sum(1 for p in pr_details if p["state"] == "Open")
merged_prs = sum(1 for p in pr_details if p["state"] == "Merged")
draft_prs = sum(1 for p in pr_details if p["state"] == "Draft")
closed_prs = sum(1 for p in pr_details if p["state"] == "Closed")

def esc(s):
    return html_mod.escape(s) if s else ""

def truncate(s, maxlen=80):
    if len(s) > maxlen:
        return s[:maxlen-3] + "..."
    return s

def approval_badges(approvals):
    if not approvals:
        return '<span class="no-approval">None yet</span>'
    badges = []
    for a in approvals:
        if a == "team":
            badges.append('<span class="approval-badge team">Team \u2713</span>')
        elif a == "tech":
            badges.append('<span class="approval-badge tech">Tech Lead \u2713</span>')
        elif a == "ces":
            badges.append('<span class="approval-badge ces">CES \u2713</span>')
        elif a == "vs":
            badges.append('<span class="approval-badge vs">VS \u2713</span>')
    return "".join(badges)

def pending_html(pending):
    if not pending:
        return '<span class="all-approved">All approved \u2713</span>'
    return ", ".join(f'<span class="pending">{p}</span>' for p in pending)

def changes_html(changes_by):
    if not changes_by:
        return "\u2014"
    return ", ".join(f'<span class="changes-by">{esc(c)}</span>' for c in changes_by)

def addressed_html(status):
    if status == "yes":
        return '<span class="addressed-yes">\u2713 Yes</span>'
    elif status == "partial":
        return '<span class="addressed-partial">\u25d0 Partially</span>'
    elif status == "no":
        return '<span class="addressed-no">\u2717 No</span>'
    else:
        return '<span class="addressed-na">\u2014</span>'

def pr_row(pr):
    state = pr["state"]
    state_class = f"state-{state.lower()}"
    has_changes = "has-changes" if pr["changes_requested_by"] else "no-changes"
    badge_color, badge_text = STATE_BADGE[state]
    repo_label = pr["repo"]
    
    title_full = esc(pr["title"])
    title_short = esc(truncate(pr["title"]))
    
    merged_col = pr["merged_at"] if pr["merged_at"] else "\u2014"
    closed_col = pr["closed_at"] if pr["closed_at"] else "\u2014"
    
    return f'''                        <tr class="{state_class}" data-state="{state}" data-date="{pr["created_at"]}" data-changes="{has_changes}">
                            <td><a href="{pr["html_url"]}" target="_blank">#{pr["number"]}</a><br><span class="git-id">{esc(pr["author_login"])}</span></td>
                            <td class="title-cell" title="{title_full}">{title_short}</td>
                            <td>{esc(pr["author_name"])}</td>
                            <td><span class="badge" style="background:{badge_color}">{badge_text}</span><br><span class="repo-badge">{repo_label}</span></td>
                            <td>{pr["created_at"]}</td>
                            <td>{merged_col}</td>
                            <td>{closed_col}</td>
                            <td>{approval_badges(pr["approvals"])}</td>
                            <td>{pending_html(pr["pending"])}</td>
                            <td>{changes_html(pr["changes_requested_by"])}</td>
                            <td>{addressed_html(pr["changes_addressed"])}</td>
                        </tr>'''

# Group PRs by team
team_grouped = {}
for team in TEAM_ORDER:
    team_grouped[team] = sorted(
        [p for p in pr_details if p["team"] == team],
        key=lambda x: x["created_at"],
        reverse=True
    )

# Build HTML
sections = []
for team in TEAM_ORDER:
    prs = team_grouped[team]
    bg, border = TEAM_COLORS[team]
    
    t_total = len(prs)
    t_open = sum(1 for p in prs if p["state"] == "Open")
    t_draft = sum(1 for p in prs if p["state"] == "Draft")
    t_merged = sum(1 for p in prs if p["state"] == "Merged")
    t_closed = sum(1 for p in prs if p["state"] == "Closed")
    
    rows = "\n".join(pr_row(p) for p in prs)
    
    section = f'''
        <div class="team-section" data-team="{team}">
            <h2 class="team-header" style="background: linear-gradient(90deg, {bg}, #0d1117); border-left: 4px solid {border};">{team} Team
                <span class="team-stats">
                    Total: {t_total} | Open: {t_open} | Draft: {t_draft} | Merged: {t_merged} | Closed: {t_closed}
                </span>
            </h2>
            <div class="filter-bar">
                <label>State: <select class="filter-select" data-col="3" onchange="applyFilters(this)"><option value="">All</option><option value="Open">Open</option><option value="Draft">Draft</option><option value="Merged">Merged</option><option value="Closed">Closed</option></select></label>
                <label>Changes Requested By: <select class="filter-select" data-col="9" onchange="applyFilters(this)"><option value="">All</option><option value="has-changes">Has Changes Requested</option><option value="no-changes">No Changes Requested</option></select></label>
                <label>Time Range: <select class="filter-select" data-col="date" onchange="applyFilters(this)"><option value="">All (30 days)</option><option value="7">Last 7 days</option><option value="14">Last 14 days</option><option value="21">Last 21 days</option></select></label>
            </div>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th>PR #</th>
                            <th>Title</th>
                            <th>Author</th>
                            <th>State</th>
                            <th>Opened</th>
                            <th>Merged</th>
                            <th>Closed</th>
                            <th>Approvals</th>
                            <th>Pending</th>
                            <th>Changes Requested By</th>
                            <th>Changes Addressed</th>
                        </tr>
                    </thead>
                    <tbody>
{rows}
                    </tbody>
                </table>
            </div>
        </div>'''
    sections.append(section)

team_options = "".join(f'<option value="{t}">{t}</option>' for t in TEAM_ORDER)

full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Galaxy PR Metrics Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 20px 24px;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            margin-bottom: 24px;
        }}
        h1 {{ color: #f0f6fc; font-size: 20px; margin-bottom: 4px; }}
        .meta {{ color: #8b949e; font-size: 12px; margin-top: 4px; }}
        .summary-bar {{
            display: flex;
            gap: 20px;
            margin-top: 12px;
        }}
        .summary-item {{
            background: #21262d;
            padding: 6px 14px;
            border-radius: 16px;
            font-size: 13px;
            border: 1px solid #30363d;
        }}
        .refresh-btn {{
            background: #238636;
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            margin-top: 8px;
        }}
        .refresh-btn:hover {{ background: #2ea043; }}

        .team-section {{ margin-bottom: 32px; }}
        .team-header {{
            padding: 12px 16px;
            border-radius: 6px 6px 0 0;
            font-size: 16px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .team-stats {{
            font-size: 12px;
            font-weight: 400;
            color: #8b949e;
        }}

        .table-wrapper {{
            overflow-x: auto;
            border: 1px solid #30363d;
            border-top: none;
            border-radius: 0 0 6px 6px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th {{
            background: #161b22;
            padding: 8px 10px;
            text-align: left;
            font-weight: 600;
            color: #8b949e;
            border-bottom: 1px solid #30363d;
            white-space: nowrap;
        }}
        td {{
            padding: 8px 10px;
            border-bottom: 1px solid #21262d;
            vertical-align: top;
        }}
        tr:hover {{ background: #161b22; }}
        tr.state-merged {{ opacity: 0.75; }}
        tr.state-closed {{ opacity: 0.6; }}

        a {{ color: #58a6ff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}

        .title-cell {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .git-id {{
            font-size: 10px;
            color: #8b949e;
            font-style: italic;
        }}

        .repo-badge {{
            display: inline-block;
            padding: 1px 6px;
            border-radius: 8px;
            font-size: 10px;
            font-weight: 500;
            color: #fff;
            background: #1f6feb;
            margin-top: 3px;
        }}

        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            color: #fff;
        }}

        .approval-badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            margin: 1px 2px;
            font-weight: 500;
        }}
        .approval-badge.team {{ background: #1a5c2e; color: #7ee787; }}
        .approval-badge.tech {{ background: #3d1a6e; color: #d2a8ff; }}
        .approval-badge.ces {{ background: #5c4a1a; color: #f2cc60; }}
        .approval-badge.vs {{ background: #1a4a5c; color: #79c0ff; }}
        .no-approval {{ color: #8b949e; font-style: italic; font-size: 11px; }}
        .all-approved {{ color: #7ee787; font-size: 11px; font-weight: 600; }}
        .pending {{ color: #f0883e; font-size: 11px; }}
        .changes-by {{ color: #f85149; font-size: 11px; font-weight: 500; }}
        .addressed-yes {{ color: #7ee787; font-size: 11px; font-weight: 600; }}
        .addressed-partial {{ color: #f0883e; font-size: 11px; font-weight: 600; }}
        .addressed-no {{ color: #f85149; font-size: 11px; font-weight: 600; }}
        .addressed-na {{ color: #8b949e; font-size: 11px; }}
        .no-data {{ text-align: center; color: #8b949e; padding: 20px; }}

        .filter-bar {{
            padding: 10px 16px;
            background: #161b22;
            border: 1px solid #30363d;
            border-top: none;
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .filter-bar label {{
            font-size: 12px;
            color: #8b949e;
        }}
        .filter-select {{
            background: #0d1117;
            color: #c9d1d9;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
            margin-left: 4px;
        }}

        .legend {{
            margin-top: 16px;
            padding: 12px 16px;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            font-size: 12px;
            color: #8b949e;
        }}
        .legend span {{ margin-right: 16px; }}
        .global-filter-bar {{
            padding: 12px 24px;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            margin-bottom: 24px;
            display: flex;
            gap: 20px;
            align-items: center;
        }}
        .global-filter-bar label {{
            font-size: 14px;
            color: #c9d1d9;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>Galaxy Teams \u2014 PR Metrics Dashboard</h1>
            <div class="meta">Celeste \u2022 Mars \u2022 Pallavas \u2022 Pandias \u2022 Cholas \u2022 Supernova \u2022 Starlite \u2022 Elite \u2022 Nayakas \u2022 Oxygen | blackboard-learn/ultra | Last 30 days</div>
            <div class="summary-bar">
                <div class="summary-item"><strong>{total_prs}</strong> Total PRs</div>
                <div class="summary-item"><strong>{open_prs}</strong> Open</div>
                <div class="summary-item"><strong>{draft_prs}</strong> Draft</div>
                <div class="summary-item"><strong>{merged_prs}</strong> Merged</div>
                <div class="summary-item"><strong>{closed_prs}</strong> Closed</div>
            </div>
        </div>
        <div style="text-align:right">
            <div class="meta" id="lastUpdated">Last refresh: {NOW}</div>
            <div class="meta">Auto refresh schedule: 09:00 and 19:00</div>
            <button class="refresh-btn" onclick="refreshDashboard()">&#x21bb; Refresh</button>
        </div>
    </div>

    <div class="global-filter-bar">
        <label>Filter by Team: <select id="teamFilter" class="filter-select" onchange="filterByTeam(this.value)">
            <option value="">All Teams</option>
            {team_options}
        </select></label>
    </div>

    {"".join(sections)}

    <div class="legend">
        <strong>Approval Labels:</strong>
        <span class="approval-badge team">Team \u2713</span> = has-team-approval
        <span class="approval-badge tech">Tech Lead \u2713</span> = has-tech-lead-review
        <span class="approval-badge ces">CES \u2713</span> = has-ces-approval
        <span class="approval-badge vs">VS \u2713</span> = has-value-stream-approval
    </div>

    <script>
    function refreshDashboard() {{
        const btn = document.querySelector('.refresh-btn');
        btn.disabled = true;
        btn.textContent = 'Refreshing...';
        fetch('/api/refresh/galaxy-pr')
            .then(r => r.json())
            .then(d => {{
                btn.textContent = '\u2713 Done';
                setTimeout(() => location.reload(), 1000);
            }})
            .catch(e => {{
                btn.textContent = '\u2717 Error';
                btn.disabled = false;
                setTimeout(() => {{ btn.textContent = '\u21bb Refresh'; }}, 3000);
            }});
    }}

    function filterByTeam(team) {{
        const sections = document.querySelectorAll('.team-section');
        sections.forEach(s => {{
            if (!team || s.dataset.team === team) {{
                s.style.display = '';
            }} else {{
                s.style.display = 'none';
            }}
        }});
    }}

    function applyFilters(el) {{
        const section = el.closest('.team-section');
        const filters = section.querySelectorAll('.filter-select');
        const rows = section.querySelectorAll('tbody tr');

        let stateFilter = '';
        let changesFilter = '';
        let dateFilter = '';

        filters.forEach(f => {{
            if (f.dataset.col === '3') stateFilter = f.value;
            else if (f.dataset.col === '9') changesFilter = f.value;
            else if (f.dataset.col === 'date') dateFilter = f.value;
        }});

        const now = new Date();
        const cutoff = dateFilter ? new Date(now - dateFilter * 86400000) : null;

        rows.forEach(row => {{
            if (row.querySelector('.no-data')) return;
            let show = true;

            if (stateFilter && row.dataset.state !== stateFilter) show = false;
            if (changesFilter && row.dataset.changes !== changesFilter) show = false;
            if (cutoff) {{
                const rowDate = new Date(row.dataset.date);
                if (rowDate < cutoff) show = false;
            }}

            row.style.display = show ? '' : 'none';
        }});
    }}
    </script>
</body>
</html>'''

output_path = "/Users/gayathri/Library/CloudStorage/OneDrive-AnthologyInc/Documents/Power Bi/Galaxy PR Metrics Dashboard.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"Dashboard written to: {output_path}")
print(f"Total PRs: {total_prs} | Open: {open_prs} | Draft: {draft_prs} | Merged: {merged_prs} | Closed: {closed_prs}")
print(f"Teams: {len(TEAM_ORDER)}")
for team in TEAM_ORDER:
    t_prs = team_grouped[team]
    print(f"  {team}: {len(t_prs)} PRs")
