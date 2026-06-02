#!/usr/bin/env python3
"""Incremental DevEx metrics fetch - only refreshes current sprint (S11+).
Loads cached data for completed sprints (S06-S10) from /tmp/devex_metrics_data.json
and only fetches new data for the active/future sprints."""

import json, urllib.request, urllib.parse, datetime, ssl, time, sys, os
from collections import defaultdict

TOKEN = os.environ.get("GITHUB_TOKEN_PAT", "ghp_PLACEHOLDER")
# List of (org, repo) tuples to fetch PRs from
REPO_SOURCES = [
    ("blackboard-learn", "ultra"),
    ("blackboard-learn", "learn"),
    ("blackboard-foundations", "bb-home-ui"),
    ("blackboard-foundations", "bb-home-oug-metrics"),
]
ssl_ctx = ssl.create_default_context()

TEAM_MEMBERS = {
    "Celeste": ["kalimuthupalraj", "manojchandrashekar29", "ranjith-r-anthology", "ravi-anthology", "sindhu-nagarajan"],
    "Mars": ["AshwinArumugamMani", "BavithraM", "Saimanimaran", "gulshan-antho", "manoharan100", "pradeep-prasath123", "rag-bbdn", "sharmilahameed", "smurugasan-bbdn"],
    "Pallavas": ["DineshRajendranBB", "LalithBB", "MartinRodgers0007", "Vignesh440-ai", "VigneshwaranSaravanan", "aarthirajaram", "nishavijayakumar"],
    "Pandias": ["Prasannajayasankar", "PrasannakumarG32", "Subbalakshmi-bb", "arunkumaranth", "gowthamanpalani", "rajeshblackboard"],
    "Cholas": ["AnmolGupta-Anthology", "Ram-G-BB", "SuryaMadhanlal-5252", "arunkumarkosna", "sudharsanm"],
    "Supernova": ["Anshu972438", "Hariharan-r-k", "bhuvaneswarisbb", "kesavanazhagarsamy", "tsyed-bbdn"],
    "Starlite": ["BharathiKannaa", "MohamedTharik8883", "akash05-bb", "nravikumar-bbdn", "mjaifank"],
    "Elite": ["AsmirKhan7", "Gandipavankumar", "KirubakaranRBB", "PriyadarshiniSaravanan", "TejaAnthology", "ramanidharanr", "subashree-b", "vasan1990"],
    "Nayakas": ["AdhithiyaHBB", "Dinesh-Chandra832", "jsalomi", "pkumarr07", "vakrams"],
    "Oxygen": ["AnbalaganGanesan", "Ashish-Anthology", "harshitha786", "omswarooprk", "saanthology", "seshadrichowdary", "srujankusuma3232", "vijay-8421"],
}

DISPLAY_NAMES = {
    "kalimuthupalraj": "Kalimuthu Palraj",
    "manojchandrashekar29": "Manoj C",
    "ranjith-r-anthology": "Ranjith Ramasamy",
    "ravi-anthology": "Ravi Prakash Tiwari",
    "sindhu-nagarajan": "Sindhu Nagarajan",
    "AshwinArumugamMani": "Ashwin Arumugam Mani",
    "BavithraM": "Bavithra M",
    "Saimanimaran": "Sai Manimaran",
    "gulshan-antho": "Gulshan Kumar",
    "manoharan100": "Manoharan",
    "pradeep-prasath123": "Pradeep Prasath",
    "rag-bbdn": "Ragavendran",
    "sharmilahameed": "Sharmila Begam Hameed",
    "smurugasan-bbdn": "Sounder Murugasan",
    "DineshRajendranBB": "Dinesh Rajendran",
    "LalithBB": "Lalith",
    "MartinRodgers0007": "Martin Rodgers",
    "Vignesh440-ai": "Vignesh",
    "VigneshwaranSaravanan": "Vigneshwaran S",
    "aarthirajaram": "Aarthi Rajaram",
    "nishavijayakumar": "Nisha Vijayakumar",
    "Prasannajayasankar": "Prasanna Jayasankar",
    "PrasannakumarG32": "Prasanna Kumar G",
    "Subbalakshmi-bb": "Subbalakshmi",
    "arunkumaranth": "Arunkumar",
    "gowthamanpalani": "Gowthaman Palani",
    "rajeshblackboard": "Rajesh",
    "AnmolGupta-Anthology": "Anmol Gupta",
    "Ram-G-BB": "Ram G",
    "SuryaMadhanlal-5252": "Surya Madhanlal",
    "arunkumarkosna": "Arun Kumar Kosna",
    "sudharsanm": "Sudharsan M",
    "Anshu972438": "Anshu",
    "Hariharan-r-k": "Hariharan R K",
    "bhuvaneswarisbb": "Bhuvaneswari S",
    "kesavanazhagarsamy": "Kesavan Azhagarsamy",
    "tsyed-bbdn": "Tausif Syed",
    "BharathiKannaa": "Bharathi Kanna",
    "MohamedTharik8883": "Mohamed Tharik",
    "akash05-bb": "Akash M",
    "nravikumar-bbdn": "Ravi Kumar N",
    "mjaifank": "Mjaifan K",
    "AsmirKhan7": "Asmir Khan",
    "Gandipavankumar": "Pavan Kumar G",
    "KirubakaranRBB": "Kirubakaran R",
    "PriyadarshiniSaravanan": "Priyadarshini S",
    "TejaAnthology": "Teja",
    "ramanidharanr": "Ramanidharan R",
    "subashree-b": "Subashree B",
    "vasan1990": "Vasan",
    "AdhithiyaHBB": "Adhithiya H",
    "Dinesh-Chandra832": "Dinesh Chandra",
    "jsalomi": "Jeba Salomi",
    "pkumarr07": "Pradeep Kumar R",
    "vakrams": "Vakram S",
    "AnbalaganGanesan": "Anbalagan Ganesan",
    "Ashish-Anthology": "Ashish Sah",
    "harshitha786": "Mogveera Harshitha Manjunath",
    "omswarooprk": "Om Swaroop R K",
    "saanthology": "Sai Anthro",
    "seshadrichowdary": "Seshadri Chowdary",
    "srujankusuma3232": "Srujan Kusuma",
    "vijay-8421": "Vijaya Sekhar P",
}

# Sprint date ranges for 2026
SPRINT_RANGES = {
    "S06": ("2026-03-12", "2026-03-25"),
    "S07": ("2026-03-26", "2026-04-08"),
    "S08": ("2026-04-09", "2026-04-22"),
    "S09": ("2026-04-23", "2026-05-06"),
    "S10": ("2026-05-07", "2026-05-20"),
    "S11": ("2026-05-21", "2026-06-03"),
    "S12": ("2026-06-04", "2026-06-17"),
}

# Completed sprints - data is frozen, no need to re-fetch
COMPLETED_SPRINTS = {"S06", "S07", "S08", "S09", "S10"}
# Active/future sprints - must fetch fresh data
ACTIVE_SPRINTS = {"S11", "S12"}

CACHE_FILE = "/tmp/devex_metrics_data.json"

# Build team lookup
user_to_team = {}
all_members_lower = set()
for team, members in TEAM_MEMBERS.items():
    for m in members:
        user_to_team[m.lower()] = team
        all_members_lower.add(m.lower())


def get_sprint(date_str):
    if not date_str:
        return None
    d = date_str[:10]
    for sprint, (start, end) in SPRINT_RANGES.items():
        if start <= d <= end:
            return sprint
    if d > "2026-06-17":
        return "POST_S12"
    return None


api_calls = 0


def gh_get(url, params=None):
    global api_calls
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": "token " + TOKEN,
        "Accept": "application/vnd.github.v3+json"
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=20) as resp:
                api_calls += 1
                remaining = resp.headers.get("X-RateLimit-Remaining", "?")
                if api_calls % 100 == 0:
                    print(f"    [API calls: {api_calls}, remaining: {remaining}]", flush=True)
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                reset_time = int(e.headers.get("X-RateLimit-Reset", "0"))
                wait = max(reset_time - int(time.time()), 60)
                print(f"  Rate limited! Waiting {wait}s...", flush=True)
                time.sleep(wait)
            elif attempt < 2:
                time.sleep(2)
            else:
                return None
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                return None


def load_cached_data():
    """Load cached data and extract completed sprint rows."""
    if not os.path.exists(CACHE_FILE):
        print("  No cache found - will do full fetch")
        return None, None
    
    with open(CACHE_FILE) as f:
        cached = json.load(f)
    
    # Keep only rows from completed sprints (not ALL, not active sprints)
    cached_reviewer = [r for r in cached["reviewer_rows"] if r["period"] in COMPLETED_SPRINTS]
    cached_author = [r for r in cached["author_rows"] if r["period"] in COMPLETED_SPRINTS]
    
    print(f"  Loaded cache: {len(cached_reviewer)} reviewer rows, {len(cached_author)} author rows (S06-S10)")
    return cached_reviewer, cached_author


print("=" * 60)
print("DevEx Metrics - Incremental Refresh")
print("=" * 60)
print(f"Strategy: Keep cached S06-S10, only fetch S11+ from API")
print(f"Teams: {len(TEAM_MEMBERS)}, Members: {sum(len(v) for v in TEAM_MEMBERS.values())}")
print()

# Load cached completed sprint data
cached_reviewer, cached_author = load_cached_data()

# Determine since_date: start of first active sprint
since_date = SPRINT_RANGES["S11"][0]  # 2026-05-21
print(f"\nFetching PRs created since {since_date} (S11 onward)...")

# Step 1: Fetch PRs from active sprints only
print("\nStep 1: Fetching team member PRs from S11 onward...", flush=True)
team_prs = []

for org, repo in REPO_SOURCES:
    page = 1
    while True:
        data = gh_get(f"https://api.github.com/repos/{org}/{repo}/pulls", {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": 100,
            "page": page
        })
        if not data:
            break
        
        too_old = False
        for pr in data:
            created = pr["created_at"][:10]
            if created < since_date:
                too_old = True
                break
            author = pr["user"]["login"].lower()
            if author in all_members_lower:
                pr["_org"] = org
                pr["_repo"] = repo
                team_prs.append(pr)
        
        if too_old or len(data) < 100:
            break
        page += 1
        time.sleep(0.2)
    
    print(f"  {org}/{repo}: pages={page}, team PRs so far: {len(team_prs)}", flush=True)

print(f"  Total team member PRs (S11+): {len(team_prs)}", flush=True)

# Step 2: Fetch reviews/comments/details for these PRs only
print("\nStep 2: Fetching reviews, comments, and PR details...", flush=True)

reviewer_data = defaultdict(lambda: defaultdict(lambda: {
    "reviews_submitted": 0,
    "prs_reviewed": set(),
    "approvals": 0,
    "response_times": [],
    "comment_count": 0,
    "prs_commented_on": set(),
    "comments_on_reviewed": 0,
}))

author_data = defaultdict(lambda: defaultdict(lambda: {
    "prs_authored": 0,
    "pr_ages": [],
    "pr_sizes": [],
    "review_cycles": [],
}))

total = len(team_prs)
for i, pr in enumerate(team_prs):
    if (i + 1) % 25 == 0:
        print(f"  {i+1}/{total}...", flush=True)
    
    repo = pr["_repo"]
    org = pr["_org"]
    pr_number = pr["number"]
    author = pr["user"]["login"].lower()
    created_at = pr["created_at"]
    sprint = get_sprint(created_at[:10])
    
    if not sprint or sprint in COMPLETED_SPRINTS:
        continue
    
    created_dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    
    # Author metrics
    am = author_data[author][sprint]
    am["prs_authored"] += 1
    
    pr_detail = gh_get(f"https://api.github.com/repos/{org}/{repo}/pulls/{pr_number}")
    if pr_detail:
        size = pr_detail.get("additions", 0) + pr_detail.get("deletions", 0)
        am["pr_sizes"].append(size)
        merged_at = pr_detail.get("merged_at")
        closed_at = pr_detail.get("closed_at")
        
        if merged_at:
            end_dt = datetime.datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
            am["pr_ages"].append((end_dt - created_dt).total_seconds() / 3600)
        elif closed_at:
            end_dt = datetime.datetime.fromisoformat(closed_at.replace("Z", "+00:00"))
            am["pr_ages"].append((end_dt - created_dt).total_seconds() / 3600)
    
    time.sleep(0.1)
    
    # Fetch reviews
    reviews = gh_get(f"https://api.github.com/repos/{org}/{repo}/pulls/{pr_number}/reviews")
    if not reviews:
        reviews = []
    
    review_cycle_count = 0
    for rev in reviews:
        if not rev.get("user"):
            continue
        reviewer = rev["user"]["login"].lower()
        rev_state = rev["state"]
        rev_time = rev.get("submitted_at", "")
        
        if rev_state in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED"):
            rev_sprint = get_sprint(rev_time[:10]) if rev_time else sprint
            if not rev_sprint or rev_sprint in COMPLETED_SPRINTS:
                rev_sprint = sprint
            
            rd = reviewer_data[reviewer][rev_sprint]
            rd["reviews_submitted"] += 1
            rd["prs_reviewed"].add(pr_number)
            
            if rev_state == "APPROVED":
                rd["approvals"] += 1
            
            if rev_time:
                rev_dt = datetime.datetime.fromisoformat(rev_time.replace("Z", "+00:00"))
                response_hrs = (rev_dt - created_dt).total_seconds() / 3600
                if 0 <= response_hrs < 5000:
                    rd["response_times"].append(response_hrs)
        
        if rev_state == "CHANGES_REQUESTED":
            review_cycle_count += 1
    
    am["review_cycles"].append(review_cycle_count)
    
    time.sleep(0.1)
    
    # Fetch comments
    comments = gh_get(f"https://api.github.com/repos/{org}/{repo}/pulls/{pr_number}/comments")
    if not comments:
        comments = []
    
    for comment in comments:
        if not comment.get("user"):
            continue
        commenter = comment["user"]["login"].lower()
        comment_time = comment.get("created_at", "")
        c_sprint = get_sprint(comment_time[:10]) if comment_time else sprint
        if not c_sprint or c_sprint in COMPLETED_SPRINTS:
            c_sprint = sprint
        
        rd = reviewer_data[commenter][c_sprint]
        rd["comment_count"] += 1
        rd["prs_commented_on"].add(pr_number)
        
        if pr_number in rd["prs_reviewed"]:
            rd["comments_on_reviewed"] += 1
    
    time.sleep(0.1)

print(f"\n  API calls made: {api_calls}", flush=True)

# Step 3: Build fresh rows for active sprints
print("\nStep 3: Building output...", flush=True)

new_reviewer_rows = []
new_author_rows = []

# Build reviewer rows for active sprints
for member, sprint_map in reviewer_data.items():
    team = user_to_team.get(member, "")
    if not team:
        continue
    
    display_name = ""
    for k, v in DISPLAY_NAMES.items():
        if k.lower() == member:
            display_name = v
            break
    if not display_name:
        display_name = member
    
    for sp in sorted(sprint_map.keys()):
        if sp in COMPLETED_SPRINTS:
            continue
        d = sprint_map[sp]
        prs_reviewed = len(d["prs_reviewed"])
        prs_commented = len(d["prs_commented_on"])
        avg_resp = round(sum(d["response_times"]) / len(d["response_times"]), 1) if d["response_times"] else None
        approval_rate = round(d["approvals"] / d["reviews_submitted"] * 100, 1) if d["reviews_submitted"] > 0 else 0
        avg_comments_reviewed = round(d["comments_on_reviewed"] / prs_reviewed, 1) if prs_reviewed > 0 else 0
        
        new_reviewer_rows.append({
            "member": member,
            "display_name": display_name,
            "team": team,
            "period": sp,
            "reviews_submitted": d["reviews_submitted"],
            "prs_reviewed": prs_reviewed,
            "approval_rate": approval_rate,
            "avg_response_time": avg_resp,
            "comment_count": d["comment_count"],
            "prs_commented_on": prs_commented,
            "comments_on_reviewed": d["comments_on_reviewed"],
            "avg_comments_on_reviewed": avg_comments_reviewed,
        })

# Build author rows for active sprints
for member, sprint_map in author_data.items():
    team = user_to_team.get(member, "")
    if not team:
        continue
    
    display_name = ""
    for k, v in DISPLAY_NAMES.items():
        if k.lower() == member:
            display_name = v
            break
    if not display_name:
        display_name = member
    
    for sp in sorted(sprint_map.keys()):
        if sp in COMPLETED_SPRINTS:
            continue
        d = sprint_map[sp]
        new_author_rows.append({
            "member": member,
            "display_name": display_name,
            "team": team,
            "period": sp,
            "prs_authored": d["prs_authored"],
            "avg_pr_age": round(sum(d["pr_ages"]) / len(d["pr_ages"]), 1) if d["pr_ages"] else None,
            "avg_pr_size": round(sum(d["pr_sizes"]) / len(d["pr_sizes"]), 1) if d["pr_sizes"] else None,
            "avg_review_cycle": round(sum(d["review_cycles"]) / len(d["review_cycles"]), 2) if d["review_cycles"] else 0,
        })

# Step 4: Merge cached + fresh data and recompute ALL aggregates
print("\nStep 4: Merging cached + fresh data...", flush=True)

all_reviewer_rows = (cached_reviewer or []) + new_reviewer_rows
all_author_rows = (cached_author or []) + new_author_rows

print(f"  Cached reviewer rows (S06-S10): {len(cached_reviewer or [])}")
print(f"  Fresh reviewer rows (S11+): {len(new_reviewer_rows)}")
print(f"  Cached author rows (S06-S10): {len(cached_author or [])}")
print(f"  Fresh author rows (S11+): {len(new_author_rows)}")

# Recompute ALL aggregates from the per-sprint rows
def compute_all_aggregates(rows, row_type):
    """Compute ALL period aggregates for each member."""
    from collections import defaultdict as dd
    member_data = dd(list)
    for row in rows:
        member_data[row["member"]].append(row)
    
    all_rows = []
    for member, sprint_rows in member_data.items():
        if not sprint_rows:
            continue
        team = sprint_rows[0]["team"]
        display_name = sprint_rows[0]["display_name"]
        
        if row_type == "reviewer":
            total_reviews = sum(r["reviews_submitted"] for r in sprint_rows)
            total_prs_reviewed = sum(r["prs_reviewed"] for r in sprint_rows)
            total_comments = sum(r["comment_count"] for r in sprint_rows)
            total_prs_commented = sum(r["prs_commented_on"] for r in sprint_rows)
            total_comments_reviewed = sum(r["comments_on_reviewed"] for r in sprint_rows)
            all_resp_times = []
            total_approvals = 0
            for r in sprint_rows:
                if r.get("avg_response_time") is not None and r["prs_reviewed"] > 0:
                    # Weight by number of reviews
                    all_resp_times.extend([r["avg_response_time"]] * r["prs_reviewed"])
                approval_count = int(r["approval_rate"] * r["reviews_submitted"] / 100) if r["reviews_submitted"] > 0 else 0
                total_approvals += approval_count
            
            avg_resp = round(sum(all_resp_times) / len(all_resp_times), 1) if all_resp_times else None
            approval_rate = round(total_approvals / total_reviews * 100, 1) if total_reviews > 0 else 0
            avg_comments_rev = round(total_comments_reviewed / total_prs_reviewed, 1) if total_prs_reviewed > 0 else 0
            
            all_rows.append({
                "member": member,
                "display_name": display_name,
                "team": team,
                "period": "ALL",
                "reviews_submitted": total_reviews,
                "prs_reviewed": total_prs_reviewed,
                "approval_rate": approval_rate,
                "avg_response_time": avg_resp,
                "comment_count": total_comments,
                "prs_commented_on": total_prs_commented,
                "comments_on_reviewed": total_comments_reviewed,
                "avg_comments_on_reviewed": avg_comments_rev,
            })
        else:  # author
            total_authored = sum(r["prs_authored"] for r in sprint_rows)
            all_ages = []
            all_sizes = []
            all_cycles = []
            for r in sprint_rows:
                if r.get("avg_pr_age") is not None and r["prs_authored"] > 0:
                    all_ages.extend([r["avg_pr_age"]] * r["prs_authored"])
                if r.get("avg_pr_size") is not None and r["prs_authored"] > 0:
                    all_sizes.extend([r["avg_pr_size"]] * r["prs_authored"])
                if r.get("avg_review_cycle") is not None and r["prs_authored"] > 0:
                    all_cycles.extend([r["avg_review_cycle"]] * r["prs_authored"])
            
            all_rows.append({
                "member": member,
                "display_name": display_name,
                "team": team,
                "period": "ALL",
                "prs_authored": total_authored,
                "avg_pr_age": round(sum(all_ages) / len(all_ages), 1) if all_ages else None,
                "avg_pr_size": round(sum(all_sizes) / len(all_sizes), 1) if all_sizes else None,
                "avg_review_cycle": round(sum(all_cycles) / len(all_cycles), 2) if all_cycles else 0,
            })
    
    return all_rows

reviewer_all = compute_all_aggregates(all_reviewer_rows, "reviewer")
author_all = compute_all_aggregates(all_author_rows, "author")

# Final output
output = {
    "reviewer_rows": all_reviewer_rows + reviewer_all,
    "author_rows": all_author_rows + author_all,
    "total_prs": total,
    "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}

# Save
with open(CACHE_FILE, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nDone!")
print(f"  Reviewer rows: {len(output['reviewer_rows'])}")
print(f"  Author rows: {len(output['author_rows'])}")
print(f"  Fresh PRs processed: {total}")
print(f"  API calls: {api_calls}")
print(f"  Saved to: {CACHE_FILE}")
