#!/usr/bin/env python3
"""
Historical data backfill for AI Security Tracker.

Fetches security-related issues/PRs from the past 180 days and groups by week.
Generates weekly JSON snapshots for historical tracking.
"""

import json
import os
import sys
from datetime import datetime, timedelta
import time

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


class HistoricalBackfill:
    """Backfills historical security data from GitHub API."""

    def __init__(self, token=None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})
        self.session.headers.update({"Accept": "application/vnd.github.v3+json"})

    def get_week_range(self, date):
        """Get Monday and Sunday for a given date."""
        monday = date - timedelta(days=date.weekday())
        sunday = monday + timedelta(days=6)
        return monday, sunday

    def fetch_issues_for_period(self, owner, repo, start_date, end_date):
        """Fetch issues/PRs between two dates."""
        issues = []

        try:
            url = f"{self.base_url}/search/issues"
            query = (
                f"repo:{owner}/{repo} "
                f"(label:security OR label:vulnerability OR label:cve OR "
                f"security OR vulnerability OR cve) "
                f"created:{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}"
            )

            params = {
                "q": query,
                "per_page": 30,
                "sort": "created",
                "order": "desc"
            }

            resp = self.session.get(url, params=params, timeout=10)

            if resp.status_code == 429:  # Rate limited
                return issues

            resp.raise_for_status()
            data = resp.json()

            if data.get("items"):
                issues.extend(data["items"][:50])

            time.sleep(0.3)  # Rate limit mitigation

        except Exception as e:
            sys.stderr.write(f"  Error fetching {owner}/{repo}: {str(e)[:50]}\n")

        return issues

    def format_issue_for_display(self, issue):
        """Format issue for tracking display."""
        return {
            "number": issue.get("number"),
            "title": issue.get("title", "")[:80],  # Truncate for display
            "url": issue.get("html_url"),
            "state": issue.get("state"),
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "comments": issue.get("comments", 0),
        }


def main():
    """Main entry point."""
    # Load manifest
    try:
        with open("manifest.json", "r") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        sys.stderr.write("Error: manifest.json not found\n")
        sys.exit(1)

    backfill = HistoricalBackfill()

    # Collect all repos
    all_repos = []
    for category in ["ai_cli_tools", "ml_frameworks", "agent_frameworks", "security_tools", "security_references"]:
        if category in manifest["curated_repos"]:
            all_repos.extend(manifest["curated_repos"][category])

    sys.stderr.write(f"=== Historical Backfill (180 days) ===\n")
    sys.stderr.write(f"Repos to process: {len(all_repos)}\n\n")

    # Generate weeks for past 180 days
    now = datetime.utcnow()
    weeks = []
    for days_back in range(0, 180, 7):
        week_end = now - timedelta(days=days_back)
        week_start = week_end - timedelta(days=7)
        weeks.append((week_start, week_end))

    # Reverse so we start from oldest
    weeks.reverse()

    sys.stderr.write(f"Processing {len(weeks)} weeks of data...\n\n")

    # Create data directory
    os.makedirs("data", exist_ok=True)

    # Process each week
    for week_num, (week_start, week_end) in enumerate(weeks, 1):
        week_key = week_end.strftime("%Y-W%V")
        sys.stderr.write(f"[{week_num}/{len(weeks)}] {week_key} ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})... ")

        weekly_data = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "week": week_key,
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat(),
            "repos_tracked": len(all_repos),
            "repositories": {}
        }

        total_issues = 0

        # Fetch data for each repo
        for repo_info in all_repos:
            owner = repo_info["owner"]
            repo = repo_info["repo"]
            name = repo_info["name"]

            issues = backfill.fetch_issues_for_period(owner, repo, week_start, week_end)

            if issues:
                weekly_data["repositories"][name] = {
                    "owner": owner,
                    "repo": repo,
                    "issue_count": len(issues),
                    "open_count": sum(1 for i in issues if i["state"] == "open"),
                    "closed_count": sum(1 for i in issues if i["state"] == "closed"),
                    "top_issues": [backfill.format_issue_for_display(i) for i in issues[:3]]
                }
                total_issues += len(issues)

        # Save weekly snapshot
        output_file = f"data/week-{week_key}.json"
        with open(output_file, "w") as f:
            json.dump(weekly_data, f, indent=2)

        sys.stderr.write(f"found {total_issues} issues\n")

    sys.stderr.write(f"\n✅ Backfill complete\n")
    sys.stderr.write(f"Generated {len(weeks)} weekly snapshots in data/\n")


if __name__ == "__main__":
    main()
