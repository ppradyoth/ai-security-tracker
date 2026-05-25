#!/usr/bin/env python3
"""
Generate dashboard data from classified items.
Only includes items marked as security_related=true.
"""

import json
import sys
import os
from datetime import datetime
from collections import defaultdict

def load_manifest():
    """Load manifest.json."""
    try:
        with open("manifest.json", "r") as f:
            return json.load(f)
    except:
        return {"curated_repos": {}}

def main():
    """Generate dashboard data from classified items."""
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: generate_dashboard_data.py <classified_items.json>\n")
        sys.exit(1)

    try:
        with open(sys.argv[1], "r") as f:
            raw_data = json.load(f)
    except Exception as e:
        sys.stderr.write(f"Error reading {sys.argv[1]}: {e}\n")
        sys.exit(1)

    manifest = load_manifest()

    # Build all repos from manifest
    all_repos_manifest = []
    for category, repos in manifest.get("curated_repos", {}).items():
        for repo in repos:
            r = repo.copy()
            r["category"] = category
            all_repos_manifest.append(r)

    # Get all items and filter to security-related only
    all_items = raw_data.get("items", [])
    security_items = [i for i in all_items if i.get("is_security_related", False)]

    sys.stderr.write(f"Total items fetched: {len(all_items)}\n")
    sys.stderr.write(f"Security-related items: {len(security_items)}\n")

    # Separate issues and PRs
    issues = [i for i in security_items if i.get("type") == "Issue"]
    prs = [i for i in security_items if i.get("type") == "PR"]

    # Group by repo
    by_repo = defaultdict(lambda: {"issues": 0, "prs": 0, "issue_list": [], "pr_list": []})
    by_label = defaultdict(int)

    for issue in issues:
        repo_key = issue.get("repo", "Unknown")
        by_repo[repo_key]["issues"] += 1
        by_repo[repo_key]["issue_list"].append(issue)
        for label in issue.get("labels", []):
            by_label[label] += 1

    for pr in prs:
        repo_key = pr.get("repo", "Unknown")
        by_repo[repo_key]["prs"] += 1
        by_repo[repo_key]["pr_list"].append(pr)
        for label in pr.get("labels", []):
            by_label[label] += 1

    # Build all_repos array with ALL repos from manifest
    all_repos = []
    for repo_info in all_repos_manifest:
        repo_name = repo_info.get("name")
        repo_full = f"{repo_info.get('owner')}/{repo_info.get('repo')}"
        repo_data = by_repo.get(repo_full, {"issues": 0, "prs": 0, "issue_list": [], "pr_list": []})

        all_repos.append({
            "name": repo_name,
            "owner": repo_info.get("owner"),
            "repo": repo_info.get("repo"),
            "category": repo_info.get("category"),
            "url": f"https://github.com/{repo_info.get('owner')}/{repo_info.get('repo')}",
            "issue_count": repo_data["issues"],
            "pr_count": repo_data["prs"],
            "security_items_count": repo_data["issues"] + repo_data["prs"]
        })

    # Statistics
    total_issues = len(issues)
    total_prs = len(prs)

    # Top issues by engagement
    top_by_engagement = sorted(
        security_items,
        key=lambda x: x.get("comments", 0) + x.get("reactions", 0),
        reverse=True
    )[:20]

    # Build dashboard
    dashboard_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_repos_tracked": len(all_repos),
            "repos_with_security_items": len([r for r in all_repos if r["security_items_count"] > 0]),
            "total_security_issues": total_issues,
            "total_security_prs": total_prs,
            "total_security_items": total_issues + total_prs,
            "all_items_scanned": raw_data.get("total_items_found", 0),
            "security_percentage": round(100 * (total_issues + total_prs) / max(1, raw_data.get("total_items_found", 0)), 1)
        },
        "all_repos": sorted(all_repos, key=lambda x: x["security_items_count"], reverse=True),
        "issues": [
            {
                "repo": issue["repo"],
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["url"],
                "type": "Issue",
                "state": issue["state"],
                "comments": issue.get("comments", 0),
                "reactions": issue.get("reactions", 0),
                "updated_at": issue["updated_at"],
                "labels": issue.get("labels", []),
                "security_category": issue.get("security_category", "other")
            }
            for issue in issues
        ],
        "pull_requests": [
            {
                "repo": pr["repo"],
                "number": pr["number"],
                "title": pr["title"],
                "url": pr["url"],
                "type": "PR",
                "state": pr["state"],
                "comments": pr.get("comments", 0),
                "reactions": pr.get("reactions", 0),
                "updated_at": pr["updated_at"],
                "labels": pr.get("labels", []),
                "security_category": pr.get("security_category", "other")
            }
            for pr in prs
        ],
        "top_items_by_engagement": [
            {
                "repo": item["repo"],
                "number": item["number"],
                "title": item["title"],
                "url": item["url"],
                "type": item["type"],
                "state": item["state"],
                "comments": item.get("comments", 0),
                "engagement": item.get("comments", 0) + item.get("reactions", 0),
                "updated_at": item["updated_at"],
                "security_category": item.get("security_category", "other")
            }
            for item in top_by_engagement
        ],
        "labels_distribution": sorted(
            [(label, count) for label, count in by_label.items()],
            key=lambda x: x[1],
            reverse=True
        )[:30]
    }

    sys.stdout.write(json.dumps(dashboard_data, indent=2))
    sys.stderr.write(f"✅ Dashboard data generated\n")
    sys.stderr.write(f"   Repos: {len(all_repos)}\n")
    sys.stderr.write(f"   Security issues: {total_issues}\n")
    sys.stderr.write(f"   Security PRs: {total_prs}\n")

if __name__ == "__main__":
    main()
