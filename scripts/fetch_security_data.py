#!/usr/bin/env python3
"""
Fetch ALL GitHub issues and PRs from tracked repos (no keyword filtering).
Will be categorized by TinyLlama in next step.

Output: Raw JSON with all issues/PRs for analysis.
"""

import json
import os
import sys
from datetime import datetime, timedelta
import subprocess

def get_github_token():
    """Get GitHub token from environment or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        try:
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
            token = result.stdout.strip()
        except:
            pass
    return token

def load_manifest():
    """Load manifest.json to get all repos."""
    try:
        with open("manifest.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"curated_repos": {}}

def fetch_repo_issues_and_prs(owner, repo, token, days=180):
    """Fetch ALL issues and PRs from a repo (last N days)."""
    if not token:
        sys.stderr.write(f"⚠️  No GitHub token, skipping {owner}/{repo}\n")
        return []

    since_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
    results = []

    try:
        # Get issues
        cmd = ["gh", "api", "search/issues", "-f", f"q=repo:{owner}/{repo} is:issue created:>{since_date}", "-f", "per_page=100", "--paginate"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            for item in data.get("items", []):
                results.append({
                    "repo": f"{owner}/{repo}",
                    "number": item["number"],
                    "title": item["title"],
                    "body": item.get("body", ""),
                    "url": item["html_url"],
                    "type": "Issue",
                    "state": item["state"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                    "labels": [l["name"] for l in item.get("labels", [])],
                    "comments": item.get("comments", 0),
                    "reactions": item.get("reactions", {}).get("total_count", 0)
                })

        # Get PRs
        cmd = ["gh", "api", "search/issues", "-f", f"q=repo:{owner}/{repo} is:pr created:>{since_date}", "-f", "per_page=100", "--paginate"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            data = json.loads(result.stdout)
            for item in data.get("items", []):
                results.append({
                    "repo": f"{owner}/{repo}",
                    "number": item["number"],
                    "title": item["title"],
                    "body": item.get("body", ""),
                    "url": item["html_url"],
                    "type": "PR",
                    "state": item["state"],
                    "created_at": item["created_at"],
                    "updated_at": item["updated_at"],
                    "labels": [l["name"] for l in item.get("labels", [])],
                    "comments": item.get("comments", 0),
                    "reactions": item.get("reactions", {}).get("total_count", 0)
                })

    except subprocess.TimeoutExpired:
        sys.stderr.write(f"⚠️  Timeout fetching {owner}/{repo}\n")
    except Exception as e:
        sys.stderr.write(f"⚠️  Error fetching {owner}/{repo}: {e}\n")

    return results

def main():
    """Fetch ALL issues and PRs from all tracked repos."""
    manifest = load_manifest()
    token = get_github_token()

    if not token:
        sys.stderr.write("❌ No GitHub token found. Set GITHUB_TOKEN or run 'gh auth login'\n")
        sys.exit(1)

    all_items = []
    total_repos = 0

    # Iterate through all repos in manifest
    for category, repos in manifest.get("curated_repos", {}).items():
        for repo_info in repos:
            owner = repo_info.get("owner")
            repo = repo_info.get("repo")

            if not owner or not repo:
                continue

            total_repos += 1
            sys.stderr.write(f"Fetching {owner}/{repo}... ")

            items = fetch_repo_issues_and_prs(owner, repo, token)
            all_items.extend(items)

            sys.stderr.write(f"✅ {len(items)} items\n")

    # Output
    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_repos_scanned": total_repos,
        "total_items_found": len(all_items),
        "time_window_days": 180,
        "items": all_items
    }

    sys.stdout.write(json.dumps(output, indent=2))
    sys.stderr.write(f"\n✅ Fetched {len(all_items)} total items from {total_repos} repos\n")
    sys.stderr.write(f"Next: Run analyze_with_tinyllama.py to categorize by security relevance\n")

if __name__ == "__main__":
    main()
