#!/usr/bin/env python3
"""
Fetch ALL GitHub issues and PRs from tracked repos (no keyword filtering).
Uses gh issue list / gh pr list — more reliable than search API.
Will be categorized by TinyLlama in next step.

Output: Raw JSON with all issues/PRs for analysis.
"""

import json
import os
import sys
from datetime import datetime, timedelta
import subprocess

def load_manifest():
    """Load manifest.json to get all repos."""
    try:
        with open("manifest.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"curated_repos": {}}

def fetch_repo_issues(owner, repo, days=180):
    """Fetch ALL issues from a repo using gh issue list."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    results = []

    try:
        cmd = [
            "gh", "issue", "list",
            "--repo", f"{owner}/{repo}",
            "--state", "all",
            "--limit", "500",
            "--json", "number,title,body,url,state,createdAt,updatedAt,labels,comments"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and result.stdout.strip():
            items = json.loads(result.stdout)
            for item in items:
                created = datetime.strptime(item["createdAt"][:10], "%Y-%m-%d")
                if created >= cutoff:
                    results.append({
                        "repo": f"{owner}/{repo}",
                        "number": item["number"],
                        "title": item["title"],
                        "body": item.get("body") or "",
                        "url": item["url"],
                        "type": "Issue",
                        "state": item["state"],
                        "created_at": item["createdAt"],
                        "updated_at": item["updatedAt"],
                        "labels": [l["name"] for l in item.get("labels", [])],
                        "comments": item.get("comments", 0),
                        "reactions": 0
                    })
        elif result.returncode != 0:
            sys.stderr.write(f"  issue list error: {result.stderr[:100]}\n")

    except subprocess.TimeoutExpired:
        sys.stderr.write(f"⚠️  Timeout on issues for {owner}/{repo}\n")
    except Exception as e:
        sys.stderr.write(f"⚠️  Error on issues for {owner}/{repo}: {e}\n")

    return results

def fetch_repo_prs(owner, repo, days=180):
    """Fetch ALL PRs from a repo using gh pr list."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    results = []

    try:
        cmd = [
            "gh", "pr", "list",
            "--repo", f"{owner}/{repo}",
            "--state", "all",
            "--limit", "500",
            "--json", "number,title,body,url,state,createdAt,updatedAt,labels,comments"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0 and result.stdout.strip():
            items = json.loads(result.stdout)
            for item in items:
                created = datetime.strptime(item["createdAt"][:10], "%Y-%m-%d")
                if created >= cutoff:
                    results.append({
                        "repo": f"{owner}/{repo}",
                        "number": item["number"],
                        "title": item["title"],
                        "body": item.get("body") or "",
                        "url": item["url"],
                        "type": "PR",
                        "state": item["state"],
                        "created_at": item["createdAt"],
                        "updated_at": item["updatedAt"],
                        "labels": [l["name"] for l in item.get("labels", [])],
                        "comments": item.get("comments", 0),
                        "reactions": 0
                    })
        elif result.returncode != 0:
            sys.stderr.write(f"  pr list error: {result.stderr[:100]}\n")

    except subprocess.TimeoutExpired:
        sys.stderr.write(f"⚠️  Timeout on PRs for {owner}/{repo}\n")
    except Exception as e:
        sys.stderr.write(f"⚠️  Error on PRs for {owner}/{repo}: {e}\n")

    return results

def main():
    """Fetch ALL issues and PRs from all tracked repos."""
    manifest = load_manifest()

    all_items = []
    total_repos = 0

    sys.stderr.write(f"=== Fetching ALL issues & PRs (last 180 days) ===\n\n")

    for category, repos in manifest.get("curated_repos", {}).items():
        for repo_info in repos:
            owner = repo_info.get("owner")
            repo = repo_info.get("repo")

            if not owner or not repo:
                continue

            total_repos += 1
            sys.stderr.write(f"[{total_repos}] {owner}/{repo}... ")

            issues = fetch_repo_issues(owner, repo)
            prs = fetch_repo_prs(owner, repo)
            items = issues + prs
            all_items.extend(items)

            sys.stderr.write(f"✅ {len(issues)} issues, {len(prs)} PRs\n")

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_repos_scanned": total_repos,
        "total_items_found": len(all_items),
        "time_window_days": 180,
        "items": all_items
    }

    sys.stdout.write(json.dumps(output, indent=2))
    sys.stderr.write(f"\n✅ Fetched {len(all_items)} total items from {total_repos} repos\n")
    sys.stderr.write(f"Next: Run analyze_with_tinyllama.py to classify security relevance\n")

if __name__ == "__main__":
    main()
