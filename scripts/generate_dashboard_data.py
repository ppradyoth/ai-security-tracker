#!/usr/bin/env python3
"""
Generate optimized dashboard data from security collection results.

Transforms raw security issues into dashboard-friendly JSON with:
- Summary statistics
- All 22 tracked repositories
- Separated issues and pull requests
- Top issues by engagement
- Label distribution
"""

import json
import sys
import os
from datetime import datetime
from collections import defaultdict


def load_manifest():
    """Load manifest.json to get all tracked repos."""
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "manifest.json")
    try:
        with open(manifest_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"curated_repos": {}}


def main():
    """Generate dashboard data from security collection results."""
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: generate_dashboard_data.py <security_data.json>\n")
        sys.exit(1)

    try:
        with open(sys.argv[1], "r") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        sys.stderr.write(f"Error: {sys.argv[1]} not found\n")
        sys.exit(1)
    except json.JSONDecodeError:
        sys.stderr.write(f"Error: Invalid JSON in {sys.argv[1]}\n")
        sys.exit(1)

    # Load manifest to get all repos
    manifest = load_manifest()
    all_repos_manifest = []
    for category_name, repos in manifest.get("curated_repos", {}).items():
        for repo in repos:
            repo_copy = repo.copy()
            repo_copy["category"] = category_name
            all_repos_manifest.append(repo_copy)

    issues = raw_data.get("issues", [])

    # Separate issues and pull requests
    issue_items = [i for i in issues if i.get("type") == "Issue"]
    pr_items = [i for i in issues if i.get("type") == "PR"]

    # Group by repo for counting
    by_repo = defaultdict(lambda: {"issues": 0, "prs": 0, "issue_list": []})
    by_label = defaultdict(int)

    for issue in issue_items:
        repo = issue.get("repo", "Unknown")
        by_repo[repo]["issues"] += 1
        by_repo[repo]["issue_list"].append(issue)
        for label in issue.get("labels", []):
            by_label[label] += 1

    for pr in pr_items:
        repo = pr.get("repo", "Unknown")
        by_repo[repo]["prs"] += 1
        for label in pr.get("labels", []):
            by_label[label] += 1

    # Build all_repos array with complete metadata
    all_repos = []
    for repo_info in all_repos_manifest:
        repo_name = repo_info.get("name")
        repo_data = by_repo.get(repo_name, {"issues": 0, "prs": 0, "issue_list": []})

        all_repos.append({
            "name": repo_name,
            "owner": repo_info.get("owner"),
            "repo": repo_info.get("repo"),
            "category": repo_info.get("category"),
            "url": f"https://github.com/{repo_info.get('owner')}/{repo_info.get('repo')}",
            "issue_count": repo_data["issues"],
            "pr_count": repo_data["prs"],
            "last_activity": repo_info.get("last_activity", "Unknown")
        })

    # Calculate statistics
    total_issues = len(issue_items)
    total_prs = len(pr_items)
    issues_by_state = defaultdict(int)

    for issue in issue_items:
        state = issue.get("state", "unknown")
        issues_by_state[state] += 1

    # Find top repos by issue count
    top_repos = sorted(
        [(name, counts["issues"]) for name, counts in by_repo.items()],
        key=lambda x: x[1],
        reverse=True
    )[:10]

    # Find top issues by engagement
    top_by_engagement = sorted(
        issue_items,
        key=lambda x: x.get("comments", 0) + x.get("reactions", 0),
        reverse=True
    )[:20]

    # Build dashboard data
    dashboard_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_repos_tracked": len(all_repos),
            "repos_with_issues": len([r for r in all_repos if r["issue_count"] > 0]),
            "total_security_issues": total_issues + total_prs,
            "time_window_days": raw_data.get("time_window_days", 180),
            "issues_by_state": dict(issues_by_state),
            "issues_by_type": {
                "Issue": total_issues,
                "PR": total_prs
            }
        },
        "all_repos": sorted(all_repos, key=lambda x: x["issue_count"] + x["pr_count"], reverse=True),
        "issues": [
            {
                "repo": issue["repo"],
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["url"],
                "type": issue["type"],
                "state": issue["state"],
                "comments": issue.get("comments", 0),
                "reactions": issue.get("reactions", 0),
                "engagement": issue.get("comments", 0) + issue.get("reactions", 0),
                "updated_at": issue["updated_at"],
                "labels": issue.get("labels", []),
                "signals": issue.get("signals", {})
            }
            for issue in issue_items
        ],
        "pull_requests": [
            {
                "repo": pr["repo"],
                "number": pr["number"],
                "title": pr["title"],
                "url": pr["url"],
                "type": pr["type"],
                "state": pr["state"],
                "comments": pr.get("comments", 0),
                "reactions": pr.get("reactions", 0),
                "engagement": pr.get("comments", 0) + pr.get("reactions", 0),
                "updated_at": pr["updated_at"],
                "labels": pr.get("labels", []),
                "signals": pr.get("signals", {})
            }
            for pr in pr_items
        ],
        "top_issues_by_engagement": [
            {
                "repo": issue["repo"],
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["url"],
                "type": issue["type"],
                "state": issue["state"],
                "comments": issue.get("comments", 0),
                "reactions": issue.get("reactions", 0),
                "engagement": issue.get("comments", 0) + issue.get("reactions", 0),
                "updated_at": issue["updated_at"],
                "labels": issue.get("labels", []),
                "signals": issue.get("signals", {})
            }
            for issue in top_by_engagement
        ],
        "labels_distribution": sorted(
            [(label, count) for label, count in by_label.items()],
            key=lambda x: x[1],
            reverse=True
        )[:20]
    }

    # Output JSON
    sys.stdout.write(json.dumps(dashboard_data, indent=2))
    sys.stderr.write(f"✅ Dashboard data generated: {len(all_repos)} repos, {total_issues} issues, {total_prs} PRs\n")

    return dashboard_data


if __name__ == "__main__":
    main()
