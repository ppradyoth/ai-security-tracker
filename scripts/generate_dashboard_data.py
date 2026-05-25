#!/usr/bin/env python3
"""
Generate optimized dashboard data from security collection results.

Transforms raw security issues into dashboard-friendly JSON with:
- Summary statistics
- Grouped by repo and issue type
- Trend data
- Top issues by engagement
"""

import json
import sys
from datetime import datetime
from collections import defaultdict


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

    issues = raw_data.get("issues", [])

    # Group by repo
    by_repo = defaultdict(list)
    by_type = defaultdict(list)
    by_label = defaultdict(int)

    for issue in issues:
        repo = issue.get("repo", "Unknown")
        issue_type = issue.get("type", "Unknown")
        signals = issue.get("signals", {})

        by_repo[repo].append(issue)
        by_type[issue_type].append(issue)

        for label in issue.get("labels", []):
            by_label[label] += 1

    # Calculate statistics
    total_issues = len(issues)
    issues_by_state = defaultdict(int)
    top_repos = sorted(
        [(repo, len(issues_list)) for repo, issues_list in by_repo.items()],
        key=lambda x: x[1],
        reverse=True
    )[:10]

    for issue in issues:
        state = issue.get("state", "unknown")
        issues_by_state[state] += 1

    # Find top issues by engagement
    top_by_engagement = sorted(
        issues,
        key=lambda x: x.get("comments", 0) + x.get("reactions", 0),
        reverse=True
    )[:20]

    # Build dashboard data
    dashboard_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "total_repos_tracked": raw_data.get("total_repos_tracked", 0),
            "total_security_issues": total_issues,
            "time_window_days": raw_data.get("time_window_days", 180),
            "issues_by_state": dict(issues_by_state),
            "issues_by_type": {
                issue_type: len(issues_list)
                for issue_type, issues_list in by_type.items()
            }
        },
        "top_repos": [
            {
                "repo": repo_name,
                "issue_count": count,
                "issues": [
                    {
                        "number": issue["number"],
                        "title": issue["title"],
                        "url": issue["url"],
                        "state": issue["state"],
                        "type": issue["type"],
                        "updated_at": issue["updated_at"],
                        "engagement": issue.get("comments", 0) + issue.get("reactions", 0)
                    }
                    for issue in sorted(
                        by_repo[repo_name],
                        key=lambda x: x.get("updated_at", ""),
                        reverse=True
                    )[:5]
                ]
            }
            for repo_name, count in top_repos
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
    sys.stderr.write("✅ Dashboard data generated\n")

    return dashboard_data


if __name__ == "__main__":
    main()
