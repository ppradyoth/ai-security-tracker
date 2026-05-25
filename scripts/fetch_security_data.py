#!/usr/bin/env python3
"""
Comprehensive security data collection across AI/ML ecosystem.

Fetches security-related issues and PRs from GitHub API for all curated repos.
Detects security signals: labels, keywords, vulnerability patterns.
Outputs structured JSON for dashboard and analysis.
"""

import json
import os
import sys
from datetime import datetime, timedelta
import re

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


class GitHubSecurityTracker:
    """Fetches and analyzes security data from GitHub."""

    def __init__(self, token=None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})
        self.session.headers.update({"Accept": "application/vnd.github.v3+json"})

    def fetch_repo_security_issues(self, owner, repo, days=180):
        """Fetch security-related issues and PRs from a repository."""
        import time
        issues = []

        # Calculate date range
        since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        # Multiple search strategies to find security issues
        search_queries = [
            f"repo:{owner}/{repo} (label:security OR label:vulnerability OR label:cve) updated:>={since_date}",
            f"repo:{owner}/{repo} (security OR vulnerability OR cve) updated:>={since_date}",
        ]

        for query in search_queries:
            try:
                url = f"{self.base_url}/search/issues"
                params = {
                    "q": query,
                    "per_page": 30,
                    "sort": "updated",
                    "order": "desc"
                }

                resp = self.session.get(url, params=params, timeout=10)

                if resp.status_code == 429:  # Rate limit
                    sys.stderr.write(f"  (rate limited, skipping)\n")
                    return issues

                resp.raise_for_status()
                data = resp.json()

                if data.get("items"):
                    # Deduplicate
                    existing_numbers = {issue["number"] for issue in issues}
                    for item in data["items"]:
                        if item["number"] not in existing_numbers:
                            issues.append(item)

                    if len(issues) >= 20:
                        break

                time.sleep(0.5)  # Rate limit mitigation
            except Exception as e:
                if "422" in str(e):
                    continue  # Try next query
                sys.stderr.write(f"  (error: {str(e)[:50]})\n")
                break

        return issues[:50]  # Limit to 50 per repo

    def extract_security_signals(self, issue, security_signals):
        """Extract security signals from an issue/PR."""
        signals = {
            "has_security_label": False,
            "has_vulnerability_label": False,
            "security_keywords_found": [],
            "vulnerability_keywords_found": [],
            "credential_keywords_found": []
        }

        title = (issue.get("title") or "").lower()
        body = (issue.get("body") or "").lower()
        text = f"{title} {body}"

        labels = [label.get("name", "").lower() for label in issue.get("labels", [])]

        # Check labels
        for label in labels:
            if label in security_signals["security_labels"]:
                signals["has_security_label"] = True
            if "vulnerability" in label or "cve" in label:
                signals["has_vulnerability_label"] = True

        # Check keywords
        for keyword in security_signals["credential_keywords"]:
            if keyword.lower() in text:
                signals["credential_keywords_found"].append(keyword)

        for keyword in security_signals["vulnerability_keywords"]:
            if keyword.lower() in text:
                signals["vulnerability_keywords_found"].append(keyword)

        for keyword in security_signals["security_labels"]:
            if keyword.lower() in text and keyword not in signals["security_keywords_found"]:
                signals["security_keywords_found"].append(keyword)

        return signals

    def format_issue(self, issue, repo_name, security_signals):
        """Format issue data for storage."""
        signals = self.extract_security_signals(issue, security_signals)

        # Only include if has security signals
        if not (
            signals["has_security_label"]
            or signals["has_vulnerability_label"]
            or signals["security_keywords_found"]
            or signals["vulnerability_keywords_found"]
            or signals["credential_keywords_found"]
        ):
            return None

        return {
            "repo": repo_name,
            "number": issue.get("number"),
            "title": issue.get("title"),
            "url": issue.get("html_url"),
            "type": "PR" if issue.get("pull_request") else "Issue",
            "state": issue.get("state"),
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "labels": [label.get("name") for label in issue.get("labels", [])],
            "comments": issue.get("comments"),
            "reactions": issue.get("reactions", {}).get("total_count", 0),
            "signals": signals
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

    tracker = GitHubSecurityTracker()
    security_signals = manifest["security_signals"]

    all_issues = []
    all_repos = []

    # Collect all repos from manifest
    for category in ["ai_cli_tools", "ml_frameworks", "agent_frameworks", "security_tools", "security_references"]:
        if category in manifest["curated_repos"]:
            all_repos.extend(manifest["curated_repos"][category])

    sys.stderr.write(f"=== AI Security Tracker — Phase 1 Data Collection ===\n")
    sys.stderr.write(f"Tracking {len(all_repos)} repositories\n")
    sys.stderr.write(f"Time window: {manifest['data_collection']['time_window_days']} days\n\n")

    # Fetch issues for each repo
    for idx, repo_info in enumerate(all_repos, 1):
        owner = repo_info["owner"]
        repo = repo_info["repo"]
        name = repo_info["name"]

        sys.stderr.write(f"[{idx}/{len(all_repos)}] {name} ({owner}/{repo})... ")

        issues = tracker.fetch_repo_security_issues(
            owner,
            repo,
            days=manifest["data_collection"]["time_window_days"]
        )

        formatted_issues = []
        for issue in issues:
            formatted = tracker.format_issue(issue, name, security_signals)
            if formatted:
                formatted_issues.append(formatted)

        all_issues.extend(formatted_issues)
        sys.stderr.write(f"found {len(formatted_issues)} security issues\n")

    # Compile results
    results = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_repos_tracked": len(all_repos),
        "total_security_issues": len(all_issues),
        "time_window_days": manifest["data_collection"]["time_window_days"],
        "issues": sorted(all_issues, key=lambda x: x["updated_at"], reverse=True)
    }

    # Output JSON
    sys.stdout.write(json.dumps(results, indent=2))
    sys.stderr.write(f"\n✅ Collection complete\n")
    sys.stderr.write(f"Total security issues found: {len(all_issues)}\n")

    return results


if __name__ == "__main__":
    main()
