#!/usr/bin/env python3
"""Quick refresh of Galaxy PR data - fetches latest PRs from GitHub."""

import json, urllib.request, urllib.parse, ssl, time, datetime, os
from collections import Counter

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
    "Supernova": ["Anshu972438", "Hariharan-r-k", "bhuvaneswarisbb", "kesavanazhagarsamy", "manoharan100", "tsyed-bbdn"],
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

TECH_LEADS = {"tbednarekbb", "johntrianat", "stormojm", "priceld", "rpetersonbb", "davtohbb", "varju", "ftclausen", "ewpreston", "alwongbb", "kkuppula", "lanceneumannblackboard", "sathyamoorthy612"}
CES_REVIEWERS = {"covertcj", "stormojm", "priceld", "bbnkamper", "bbmnatarajan", "johntrianat", "davtohbb", "dsoto-bb", "jkhan07"}
VS_REVIEWERS = {"amyers-blackboard", "kapalanisamy", "hariharanmohanakrishnan"}
APPROVAL_LABELS = {
    "team": "has-team-approval",
    "tech": "has-tech-lead-review",
    "ces": "has-ces-approval",
    "vs": "has-value-stream-approval",
}

user_to_team = {}
for team, members in TEAM_MEMBERS.items():
    for m in members:
        user_to_team[m.lower()] = team

def gh_get(url, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": "token " + TOKEN,
        "Accept": "application/vnd.github.v3+json"
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            else:
                print(f"  Error: {e}", flush=True)
                return None

print("Fetching latest PRs from GitHub...", flush=True)
since_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")  # Last 30 days

all_prs = []
for org, repo in REPO_SOURCES:
    page = 1
    while True:
        data = gh_get(f"https://api.github.com/repos/{org}/{repo}/pulls", {
            "state": "all", "sort": "created", "direction": "desc",
            "per_page": 100, "page": page
        })
        if not data:
            break
        too_old = False
        for pr in data:
            if pr["created_at"][:10] < since_date:
                too_old = True
                break
            author = pr["user"]["login"].lower()
            if author in user_to_team:
                pr["_org"] = org
                pr["_repo"] = repo
                all_prs.append(pr)
        if too_old or len(data) < 100:
            break
        page += 1
        time.sleep(0.2)
    print(f"  {org}/{repo}: {page} pages", flush=True)

print(f"Total team PRs: {len(all_prs)}", flush=True)

# Now fetch reviews for each PR
print("Fetching reviews...", flush=True)
pr_details = []

for i, pr in enumerate(all_prs):
    if (i+1) % 50 == 0:
        print(f"  {i+1}/{len(all_prs)}...", flush=True)
    
    repo = pr["_repo"]
    org = pr["_org"]
    pr_number = pr["number"]
    login = pr["user"]["login"]
    team = user_to_team[login.lower()]
    
    # Fetch PR detail
    pr_detail = gh_get(f"https://api.github.com/repos/{org}/{repo}/pulls/{pr_number}")
    if pr_detail:
        is_draft = pr_detail.get("draft", False)
        merged_at = pr_detail.get("merged_at")
        closed_at = pr_detail.get("closed_at")
    else:
        is_draft = False
        merged_at = None
        closed_at = pr.get("closed_at")
    
    # Fetch reviews
    reviews_data = gh_get(f"https://api.github.com/repos/{org}/{repo}/pulls/{pr_number}/reviews") or []
    
    # Determine state
    if merged_at:
        state = "Merged"
    elif pr["state"] == "closed":
        state = "Closed"
    elif is_draft:
        state = "Draft"
    else:
        state = "Open"
    
    # Analyze reviews (latest state per reviewer)
    reviewer_states = {}
    for rev in reviews_data:
        if not rev.get("user"):
            continue
        reviewer = rev["user"]["login"].lower()
        rev_state = rev["state"]
        if rev_state in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            reviewer_states[reviewer] = rev_state
    
    approvals_from_reviews = set()
    changes_requested_by = set()
    
    for reviewer, rev_state in reviewer_states.items():
        if rev_state == "APPROVED":
            matched = False
            if reviewer in TECH_LEADS:
                approvals_from_reviews.add("tech")
                matched = True
            if reviewer in CES_REVIEWERS:
                approvals_from_reviews.add("ces")
                matched = True
            if reviewer in VS_REVIEWERS:
                approvals_from_reviews.add("vs")
                matched = True
            if not matched:
                approvals_from_reviews.add("team")
        elif rev_state == "CHANGES_REQUESTED":
            changes_requested_by.add(reviewer)

    # Use current GitHub labels as source of truth for approval columns.
    # Fallback to review-role inference only when approval labels are absent.
    label_names = {
        (label.get("name") or "").strip().lower()
        for label in (pr_detail.get("labels") if pr_detail else pr.get("labels", []))
        if isinstance(label, dict)
    }
    approvals = {
        key for key, label_name in APPROVAL_LABELS.items() if label_name in label_names
    }
    if not approvals:
        approvals = set(approvals_from_reviews)
    
    pending = []
    if "team" not in approvals:
        pending.append("Team Approval")
    if "tech" not in approvals:
        pending.append("Tech Lead Review")
    if "ces" not in approvals:
        pending.append("CES Approval")
    if "vs" not in approvals:
        pending.append("Value Stream Approval")
    
    if changes_requested_by:
        all_addressed = all(reviewer_states.get(r) == "APPROVED" for r in changes_requested_by)
        some_addressed = any(reviewer_states.get(r) == "APPROVED" for r in changes_requested_by)
        changes_addressed = "yes" if all_addressed else ("partial" if some_addressed else "no")
    else:
        changes_addressed = "na"
    
    # Friendly repo display name
    if org == "blackboard-foundations":
        repo_display = f"Foundations/{repo}"
    else:
        repo_display = repo.capitalize()

    pr_details.append({
        "number": pr_number,
        "title": pr["title"],
        "author_login": login,
        "author_name": DISPLAY_NAMES.get(login.lower(), DISPLAY_NAMES.get(login, login)),
        "state": state,
        "repo": repo_display,
        "team": team,
        "created_at": pr["created_at"][:10],
        "merged_at": merged_at[:10] if merged_at else None,
        "closed_at": closed_at[:10] if closed_at else None,
        "approvals": sorted(approvals),
        "pending": pending,
        "changes_requested_by": sorted(changes_requested_by),
        "changes_addressed": changes_addressed,
        "html_url": pr["html_url"],
    })
    
    time.sleep(0.12)

# Save
with open("/tmp/galaxy_prs_detailed.json", "w") as f:
    json.dump(pr_details, f, indent=2)

states = Counter(p["state"] for p in pr_details)
teams_count = Counter(p["team"] for p in pr_details)
print(f"\nDone! {len(pr_details)} PRs")
print(f"States: {dict(states)}")
print(f"Teams: {dict(sorted(teams_count.items()))}")
