#!/usr/bin/env python3
"""CI Refresh Script - orchestrates dashboard refresh in GitHub Actions.
Uses GITHUB_TOKEN_PAT env var for authentication.
All intermediate files stored in workspace directory."""

import os, sys, re, datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(WORKSPACE, "scripts")
DATA_DIR = os.path.join(WORKSPACE, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Get token from environment
TOKEN = os.environ.get("GITHUB_TOKEN_PAT", "")
if not TOKEN:
    print("ERROR: GITHUB_TOKEN_PAT environment variable not set")
    sys.exit(1)

print(f"Workspace: {WORKSPACE}")
print(f"Token: ...{TOKEN[-4:]}")
print()

# ============================================================
# Step 1: Patch scripts to use env token and workspace paths
# ============================================================

def patch_script(filename, replacements):
    """Read script, apply replacements, return modified content."""
    path = os.path.join(SCRIPTS_DIR, filename)
    with open(path) as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    return content

# Patch and exec refresh_galaxy_prs.py
print("=" * 60)
print("Step 1: Fetching Galaxy PR data...")
print("=" * 60)

galaxy_script = patch_script("refresh_galaxy_prs.py", [
    ('TOKEN = os.environ.get("GITHUB_TOKEN_PAT", "ghp_PLACEHOLDER")', f'TOKEN = "{TOKEN}"'),
    ('/tmp/galaxy_prs_detailed.json', f'{DATA_DIR}/galaxy_prs_detailed.json'),
])

exec(compile(galaxy_script, "refresh_galaxy_prs.py", "exec"), {"__name__": "__run__"})

# Patch and exec generate_dashboard.py
print("\n" + "=" * 60)
print("Step 2: Generating Galaxy PR Dashboard...")
print("=" * 60)

NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S")
galaxy_output = os.path.join(WORKSPACE, "index.html")

gen_dashboard_script = patch_script("generate_dashboard.py", [
    ('/tmp/galaxy_prs_detailed.json', f'{DATA_DIR}/galaxy_prs_detailed.json'),
    ('output_path = "/Users/gayathri/Library/CloudStorage/OneDrive-AnthologyInc/Documents/Power Bi/Galaxy PR Metrics Dashboard.html"',
     f'output_path = "{galaxy_output}"'),
])

exec(compile(gen_dashboard_script, "generate_dashboard.py", "exec"), {"__name__": "__run__"})

# Patch and exec fetch_devex_incremental.py
print("\n" + "=" * 60)
print("Step 3: Fetching DevEx metrics (incremental)...")
print("=" * 60)

devex_cache = f'{DATA_DIR}/devex_metrics_data.json'
devex_script = patch_script("fetch_devex_incremental.py", [
    ('TOKEN = os.environ.get("GITHUB_TOKEN_PAT", "ghp_PLACEHOLDER")', f'TOKEN = "{TOKEN}"'),
    ('CACHE_FILE = "/tmp/devex_metrics_data.json"', f'CACHE_FILE = "{devex_cache}"'),
])

exec(compile(devex_script, "fetch_devex_incremental.py", "exec"), {"__name__": "__run__"})

# Patch and exec generate_devex_dashboard.py
print("\n" + "=" * 60)
print("Step 4: Generating DevEx Dashboard...")
print("=" * 60)

devex_output = os.path.join(WORKSPACE, "devex-metrics.html")
gen_devex_script = patch_script("generate_devex_dashboard.py", [
    ('/tmp/devex_metrics_data.json', devex_cache),
    ('output_path = "/Users/gayathri/Library/CloudStorage/OneDrive-AnthologyInc/Documents/Power Bi/DevEx Metrics Dashboard.html"',
     f'output_path = "{devex_output}"'),
])

exec(compile(gen_devex_script, "generate_devex_dashboard.py", "exec"), {"__name__": "__run__"})

# ============================================================
# Step 5: Post-process HTML files (remove refresh button, clean up)
# ============================================================
print("\n" + "=" * 60)
print("Step 5: Post-processing HTML files...")
print("=" * 60)

for filepath in [galaxy_output, devex_output]:
    with open(filepath) as f:
        content = f.read()

    # Replace refresh button with static text
    content = re.sub(
        r'<button class="refresh-btn" onclick="refreshDashboard\(\)">.*?</button>',
        '<span class="refresh-btn" style="cursor:default;background:#30363d;">Data refreshed by admin</span>',
        content
    )

    # Remove refreshDashboard function properly
    lines = content.split('\n')
    new_lines = []
    skip = False
    brace_depth = 0
    for line in lines:
        if not skip and 'function refreshDashboard()' in line:
            skip = True
            brace_depth = 0
        if skip:
            brace_depth += line.count('{') - line.count('}')
            if brace_depth <= 0 and brace_depth + line.count('}') > 0:
                skip = False
            continue
        new_lines.append(line)
    content = '\n'.join(new_lines)

    # Update timestamp
    content = re.sub(
        r'Last refresh: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
        f'Last refresh: {NOW}',
        content
    )

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"  {os.path.basename(filepath)}: {len(new_lines)} lines")

print(f"\n{'=' * 60}")
print(f"All done! Timestamp: {NOW}")
print(f"{'=' * 60}")
