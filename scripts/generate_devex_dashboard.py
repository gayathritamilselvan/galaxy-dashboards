#!/usr/bin/env python3
"""Generate the DevEx Metrics Dashboard HTML from fetched data."""

import json, datetime, html as html_mod

with open("/tmp/devex_metrics_data.json") as f:
    data = json.load(f)

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
total_prs = data["total_prs"]

# Get unique members count
rev_members = set(r["member"] for r in data["reviewer_rows"])
auth_members = set(r["member"] for r in data["author_rows"])
all_members = rev_members | auth_members
total_members = len(all_members)

# Get all teams
teams = sorted(set(r["team"] for r in data["reviewer_rows"]))

# Get all periods
periods = sorted(set(r["period"] for r in data["reviewer_rows"] if r["period"] != "ALL"))

def esc(s):
    return html_mod.escape(str(s)) if s else ""

# Build reviewer rows HTML
reviewer_rows_html = []
# Sort by team, then display_name
sorted_reviewer = sorted(data["reviewer_rows"], key=lambda r: (r["team"], r["display_name"].lower(), r["period"]))

for row in sorted_reviewer:
    member = row["member"]
    display = esc(row["display_name"])
    team = row["team"]
    period = row["period"]
    
    # Match the original case for display in sub
    original_case = member
    for k in ["kalimuthupalraj", "manojchandrashekar29", "ranjith-r-anthology", "ravi-anthology", "sindhu-nagarajan",
              "AshwinArumugamMani", "BavithraM", "Saimanimaran", "gulshan-antho", "manoharan100",
              "pradeep-prasath123", "rag-bbdn", "sharmilahameed", "smurugasan-bbdn",
              "DineshRajendranBB", "LalithBB", "MartinRodgers0007", "Vignesh440-ai", "VigneshwaranSaravanan",
              "aarthirajaram", "nishavijayakumar", "Prasannajayasankar", "PrasannakumarG32",
              "Subbalakshmi-bb", "arunkumaranth", "gowthamanpalani", "rajeshblackboard",
              "AnmolGupta-Anthology", "Ram-G-BB", "SuryaMadhanlal-5252", "arunkumarkosna", "sudharsanm",
              "Anshu972438", "Hariharan-r-k", "bhuvaneswarisbb", "kesavanazhagarsamy", "tsyed-bbdn",
              "BharathiKannaa", "MohamedTharik8883", "akash05-bb", "nravikumar-bbdn", "mjaifank",
              "AsmirKhan7", "Gandipavankumar", "KirubakaranRBB", "PriyadarshiniSaravanan",
              "TejaAnthology", "ramanidharanr", "subashree-b", "vasan1990",
              "AdhithiyaHBB", "Dinesh-Chandra832", "jsalomi", "pkumarr07", "vakrams",
              "AnbalaganGanesan", "Ashish-Anthology", "harshitha786", "omswarooprk",
              "saanthology", "seshadrichowdary", "srujankusuma3232", "vijay-8421"]:
        if k.lower() == member.lower():
            original_case = k
            break
    
    avg_resp = f"{row['avg_response_time']}" if row['avg_response_time'] is not None else "\u2014"
    
    reviewer_rows_html.append(f'''        <tr data-team="{team}" data-member="{member}" data-period="{period}">
            <td>{display}<div class="sub">{original_case}</div></td>
            <td>{team}</td>
            <td>{row["reviews_submitted"]}</td>
            <td>{row["reviews_submitted"]}</td>
            <td>{row["prs_reviewed"]}</td>
            <td>{row["prs_reviewed"]}</td>
            <td>{row["approval_rate"]}%</td>
            <td>{avg_resp}</td>
            <td>{row["comment_count"]}</td>
            <td>{row["prs_commented_on"]}</td>
            <td>{row["comments_on_reviewed"]}</td>
            <td>{row["avg_comments_on_reviewed"]:.2f}</td>
        </tr>''')

# Build author rows HTML
author_rows_html = []
sorted_author = sorted(data["author_rows"], key=lambda r: (r["team"], r["display_name"].lower(), r["period"]))

for row in sorted_author:
    member = row["member"]
    display = esc(row["display_name"])
    team = row["team"]
    period = row["period"]
    
    original_case = member
    for k in ["kalimuthupalraj", "manojchandrashekar29", "ranjith-r-anthology", "ravi-anthology", "sindhu-nagarajan",
              "AshwinArumugamMani", "BavithraM", "Saimanimaran", "gulshan-antho", "manoharan100",
              "pradeep-prasath123", "rag-bbdn", "sharmilahameed", "smurugasan-bbdn",
              "DineshRajendranBB", "LalithBB", "MartinRodgers0007", "Vignesh440-ai", "VigneshwaranSaravanan",
              "aarthirajaram", "nishavijayakumar", "Prasannajayasankar", "PrasannakumarG32",
              "Subbalakshmi-bb", "arunkumaranth", "gowthamanpalani", "rajeshblackboard",
              "AnmolGupta-Anthology", "Ram-G-BB", "SuryaMadhanlal-5252", "arunkumarkosna", "sudharsanm",
              "Anshu972438", "Hariharan-r-k", "bhuvaneswarisbb", "kesavanazhagarsamy", "tsyed-bbdn",
              "BharathiKannaa", "MohamedTharik8883", "akash05-bb", "nravikumar-bbdn", "mjaifank",
              "AsmirKhan7", "Gandipavankumar", "KirubakaranRBB", "PriyadarshiniSaravanan",
              "TejaAnthology", "ramanidharanr", "subashree-b", "vasan1990",
              "AdhithiyaHBB", "Dinesh-Chandra832", "jsalomi", "pkumarr07", "vakrams",
              "AnbalaganGanesan", "Ashish-Anthology", "harshitha786", "omswarooprk",
              "saanthology", "seshadrichowdary", "srujankusuma3232", "vijay-8421"]:
        if k.lower() == member.lower():
            original_case = k
            break
    
    avg_age = f"{row['avg_pr_age']}" if row['avg_pr_age'] is not None else "\u2014"
    avg_size = f"{row['avg_pr_size']}" if row['avg_pr_size'] is not None else "\u2014"
    
    author_rows_html.append(f'''        <tr data-team="{team}" data-member="{member}" data-period="{period}">
            <td>{display}<div class="sub">{original_case}</div></td>
            <td>{team}</td>
            <td>{row["prs_authored"]}</td>
            <td>{avg_age}</td>
            <td>{avg_size}</td>
            <td>{row["avg_review_cycle"]:.2f}</td>
        </tr>''')

# Build team options
team_options = "".join(f'<option value="{t}">{t}</option>' for t in teams)

# Build period options  
period_options = "".join(f'<option value="{p}">{p}</option>' for p in periods)

# Full HTML
html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Galaxy DevEx Metrics Dashboard</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 20px; background: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    .header {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px; display: flex; justify-content: space-between; gap: 12px; align-items: center; }}
    .meta {{ color: #8b949e; font-size: 13px; }}
    .summary {{ display: flex; gap: 18px; margin-top: 8px; font-size: 13px; }}
    .summary strong {{ color: #f0f6fc; }}
    .refresh-btn {{ background: #238636; border: none; color: white; border-radius: 6px; padding: 8px 14px; cursor: pointer; }}
    .filters {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 16px; align-items: center; }}
    label {{ font-size: 13px; color: #c9d1d9; }}
    select, input {{ margin-left: 6px; background: #0d1117; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; padding: 4px 8px; }}
    .tabs {{ display: flex; gap: 8px; margin-bottom: 10px; }}
    .tab-btn {{ background: #21262d; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; padding: 8px 12px; cursor: pointer; }}
    .tab-btn.active {{ background: #1f6feb; color: #fff; border-color: #1f6feb; }}
    .panel {{ display: none; }}
    .panel.active {{ display: block; }}
    .table-wrap {{ overflow-x: auto; border: 1px solid #30363d; border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
    th, td {{ padding: 8px 10px; border-bottom: 1px solid #21262d; text-align: left; white-space: nowrap; }}
    th {{ background: #161b22; color: #8b949e; position: sticky; top: 0; }}
    tr:hover {{ background: #161b22; }}
    .sub {{ color: #8b949e; font-size: 10px; margin-top: 2px; }}
    .legend {{ margin-top: 12px; color: #8b949e; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="header">
    <div>
      <h1>Galaxy Team \u2014 DevEx Metrics Dashboard</h1>
      <div class="meta">Repository: blackboard-learn/ultra &amp; learn | Scope: Sprint 06 onward</div>
      <div class="summary">
        <div><strong>{total_prs}</strong> PRs analyzed</div>
        <div><strong>{total_members}</strong> Galaxy members</div>
      </div>
    </div>
    <div style="text-align:right">
      <div class="meta">Last refresh: {NOW}</div>
      <button class="refresh-btn" onclick="refreshDashboard()">\u21bb Refresh</button>
    </div>
  </div>

  <div class="filters">
    <label>Team:
      <select id="teamFilter" onchange="applyFilters()">
        <option value="">All Teams</option>
        {team_options}
      </select>
    </label>
    <label>Sprint:
      <select id="periodFilter" onchange="applyFilters()">
        <option value="ALL">All (S06+)</option>{period_options}<option value="POST_S12">Post S12</option>
      </select>
    </label>
    <label>Member:
      <input id="memberFilter" type="text" placeholder="Git ID or name" oninput="applyFilters()" />
    </label>
  </div>

  <div class="tabs">
    <button class="tab-btn active" data-target="reviewerPanel" onclick="switchTab(this)">Reviewer Metrics</button>
    <button class="tab-btn" data-target="authorPanel" onclick="switchTab(this)">Author Metrics</button>
  </div>

  <div id="reviewerPanel" class="panel active">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Member</th>
            <th>Team(s)</th>
            <th>Reviews Requested On</th>
            <th>Reviews Submitted</th>
            <th>PRs Requested On</th>
            <th>PRs Reviewed</th>
            <th>Approval Rate</th>
            <th>Avg Response Time (hrs)</th>
            <th>Comment Count</th>
            <th>PRs Comment On</th>
            <th>Comments on Reviewed PRs</th>
            <th>Avg Comment Count on Reviewed PRs</th>
          </tr>
        </thead>
        <tbody id="reviewerBody">
          
{"".join(reviewer_rows_html)}
        </tbody>
      </table>
    </div>
  </div>

  <div id="authorPanel" class="panel">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Member</th>
            <th>Team(s)</th>
            <th>PRs Authored</th>
            <th>Average PR Age (hrs)</th>
            <th>Average PR Size</th>
            <th>Average Review Cycle</th>
          </tr>
        </thead>
        <tbody id="authorBody">
          
{"".join(author_rows_html)}
        </tbody>
      </table>
    </div>
  </div>

  <div class="legend">
    <p><strong>Reviewer Metrics:</strong> Reviews Submitted = total review actions (approve/request changes/comment). PRs Reviewed = unique PRs where reviews were submitted. Approval Rate = approvals / total reviews. Avg Response Time = hours from PR creation to review submission.</p>
    <p><strong>Author Metrics:</strong> PR Age = hours from creation to merge/close. PR Size = additions + deletions. Review Cycle = number of change request rounds before merge.</p>
    <p><em>Data fetched: {NOW} | Source: GitHub API (blackboard-learn/ultra, blackboard-learn/learn)</em></p>
  </div>

  <script>
    document.getElementById('periodFilter').value = 'ALL';

    function switchTab(btn) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.target).classList.add('active');
      applyFilters();
    }}

    function applyFilters() {{
      const team = document.getElementById('teamFilter').value;
      const period = document.getElementById('periodFilter').value;
      const memberQ = document.getElementById('memberFilter').value.trim().toLowerCase();
      const rows = document.querySelectorAll('tbody tr');

      rows.forEach(row => {{
        const rowTeams = row.dataset.team || '';
        const rowPeriod = row.dataset.period || '';
        const rowMember = row.dataset.member || '';
        const displayText = row.textContent.toLowerCase();

        let show = true;
        if (team && !rowTeams.split('|').includes(team)) show = false;
        if (period && rowPeriod !== period) show = false;
        if (memberQ && !(rowMember.includes(memberQ) || displayText.includes(memberQ))) show = false;

        row.style.display = show ? '' : 'none';
      }});
    }}

    function refreshDashboard() {{
      const btn = document.querySelector('.refresh-btn');
      btn.disabled = true;
      btn.textContent = 'Refreshing...';
      fetch('http://localhost:8787/api/refresh/devex')
        .then(r => r.json())
        .then(() => {{
          btn.textContent = '\u2713 Done';
          setTimeout(() => location.reload(), 1000);
        }})
        .catch(() => {{
          btn.textContent = '\u2717 Error';
          btn.disabled = false;
          setTimeout(() => {{ btn.textContent = '\u21bb Refresh'; }}, 3000);
        }});
    }}

    applyFilters();
  </script>
</body>
</html>
'''

output_path = "/Users/gayathri/Library/CloudStorage/OneDrive-AnthologyInc/Documents/Power Bi/DevEx Metrics Dashboard.html"
with open(output_path, "w") as f:
    f.write(html)

print(f"Dashboard written to: {output_path}")
print(f"Total lines: {html.count(chr(10))}")
print(f"Reviewer rows: {len(reviewer_rows_html)}")
print(f"Author rows: {len(author_rows_html)}")
print(f"PRs analyzed: {total_prs}")
print(f"Members: {total_members}")
