#!/usr/bin/env python3
"""
Generate comprehensive GitHub issue reports (Big Model Radar format).

Creates richly detailed weekly security tracking reports with:
- Executive summary with trends
- Detailed repository table
- Severity breakdown
- Category analysis
- Top issues by engagement
"""

import json
import os
import sys
from datetime import datetime, timedelta
import glob


def detect_severity(issue):
    """Detect issue severity from labels and signals."""
    labels = issue.get("labels", [])
    signals = issue.get("signals", {})
    title = issue.get("title", "").lower()

    # Check for critical signals
    if signals.get("has_vulnerability_label"):
        return "critical"
    if any("cve" in label.lower() for label in labels):
        return "critical"
    if any("critical" in label.lower() for label in labels):
        return "critical"

    # Check for high severity
    if any("vulnerability" in label.lower() for label in labels):
        return "high"
    if any("exploit" in label.lower() for label in labels):
        return "high"
    if "vulnerability" in title or "exploit" in title:
        return "high"

    # Check for medium
    if any("medium" in label.lower() for label in labels):
        return "medium"

    return "low"


def get_severity_emoji(severity):
    """Get emoji for severity level."""
    return {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }.get(severity, "⚪")


def create_issue_body(weekly_data, previous_week_data=None):
    """Create comprehensive markdown body for GitHub issue."""
    week = weekly_data.get("week", "Unknown")
    start_date = weekly_data.get("start_date", "")
    end_date = weekly_data.get("end_date", "")
    repos_tracked = weekly_data.get("repos_tracked", 0)

    # Calculate total issues
    repos = weekly_data.get("repositories", {})
    total_issues = sum(r.get("issue_count", 0) for r in repos.values())
    open_issues = sum(r.get("open_count", 0) for r in repos.values())
    closed_issues = sum(r.get("closed_count", 0) for r in repos.values())

    # Calculate severity distribution
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    all_top_issues = []

    for repo_name, repo_data in repos.items():
        for issue in repo_data.get("top_issues", []):
            severity = detect_severity(issue)
            severity_counts[severity] += 1
            all_top_issues.append({
                "repo": repo_name,
                "title": issue.get("title", ""),
                "number": issue.get("number", ""),
                "url": issue.get("url", ""),
                "severity": severity,
                "comments": issue.get("comments", 0)
            })

    lines = []

    # Header
    lines.append(f"# [Tracking] {week} — AI Security Ecosystem Report")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append(f"- **Period**: {start_date.split('T')[0]} to {end_date.split('T')[0]} (7 days)")
    lines.append(f"- **Repos Tracked**: {repos_tracked}")
    lines.append(f"- **Total Issues**: {total_issues}")
    lines.append(f"- **Open Issues**: {open_issues}")
    lines.append(f"- **Closed Issues**: {closed_issues}")

    # Trends vs previous week
    if previous_week_data:
        prev_total = sum(r.get("issue_count", 0) for r in previous_week_data.get("repositories", {}).values())
        trend = total_issues - prev_total
        if trend > 0:
            lines.append(f"- **Trend**: ↑ +{trend} issues since last week")
        elif trend < 0:
            lines.append(f"- **Trend**: ↓ {trend} issues since last week")
        else:
            lines.append(f"- **Trend**: → No change since last week")

    lines.append("")

    # Severity Distribution
    lines.append("## Severity Distribution")
    lines.append(f"- {get_severity_emoji('critical')} **Critical**: {severity_counts['critical']} issues")
    lines.append(f"- {get_severity_emoji('high')} **High**: {severity_counts['high']} issues")
    lines.append(f"- {get_severity_emoji('medium')} **Medium**: {severity_counts['medium']} issues")
    lines.append(f"- {get_severity_emoji('low')} **Low**: {severity_counts['low']} issues")
    lines.append("")

    # Main Repository Table
    lines.append("## Security Issues by Repository")
    lines.append("")
    lines.append("| Repository | Category | Total | Open | Closed | Critical | High | Top Issue |")
    lines.append("|---|---|:---:|:---:|:---:|:---:|:---:|---|")

    for repo_name, data in sorted(
        repos.items(),
        key=lambda x: x[1].get("issue_count", 0),
        reverse=True
    ):
        owner = data.get("owner", "")
        repo = data.get("repo", "")
        repo_link = f"https://github.com/{owner}/{repo}"

        issue_count = data.get("issue_count", 0)
        open_count = data.get("open_count", 0)
        closed_count = data.get("closed_count", 0)

        # Count severities for this repo
        critical_count = 0
        high_count = 0
        for issue in data.get("top_issues", []):
            severity = detect_severity(issue)
            if severity == "critical":
                critical_count += 1
            elif severity == "high":
                high_count += 1

        top_issue = data.get("top_issues", [{}])[0] if data.get("top_issues") else None
        issue_title = top_issue.get("title", "No issues") if top_issue else "No issues"
        issue_link = top_issue.get("url", "#") if top_issue else "#"
        issue_num = top_issue.get("number", "") if top_issue else ""

        # Truncate title
        if len(issue_title) > 50:
            issue_title = issue_title[:47] + "..."

        if issue_num:
            top_issue_cell = f"[#{issue_num}]({issue_link}) {issue_title}"
        else:
            top_issue_cell = "No issues"

        repo_cell = f"[{repo_name}]({repo_link})"

        lines.append(
            f"| {repo_cell} | Security | {issue_count} | {open_count} | {closed_count} | "
            f"{critical_count} | {high_count} | {top_issue_cell} |"
        )

    lines.append("")

    # Top Issues by Engagement
    if all_top_issues:
        lines.append("## Top Issues by Engagement")
        lines.append("")

        top_engaged = sorted(all_top_issues, key=lambda x: x["comments"], reverse=True)[:5]
        for idx, issue in enumerate(top_engaged, 1):
            emoji = get_severity_emoji(issue["severity"])
            lines.append(f"{idx}. {emoji} **[{issue['repo']} #{issue['number']}]({issue['url']})** — {issue['title']}")
            lines.append(f"   - Comments: {issue['comments']}")

        lines.append("")

    # Category Summary
    categories = {}
    for repo_name, data in repos.items():
        # Infer category from repo name (this is a simple heuristic)
        if any(x in repo_name.lower() for x in ["tensor", "pytorch", "jax", "hugging", "llama", "ollama"]):
            cat = "ML Frameworks"
        elif any(x in repo_name.lower() for x in ["claude", "copilot", "gemini", "kimi"]):
            cat = "AI CLI Tools"
        elif any(x in repo_name.lower() for x in ["bandit", "safety", "snyk", "trufflehog"]):
            cat = "Security Tools"
        else:
            cat = "Other"

        if cat not in categories:
            categories[cat] = {"repos": 0, "issues": 0}
        categories[cat]["repos"] += 1
        categories[cat]["issues"] += data.get("issue_count", 0)

    if categories:
        lines.append("## By Category")
        lines.append("")
        for category, stats in sorted(categories.items(), key=lambda x: x[1]["issues"], reverse=True):
            lines.append(f"- **{category}**: {stats['repos']} repos, {stats['issues']} issues")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*Generated by [AI Security Tracker](https://github.com/ppradyoth/ai-security-tracker)*")
    lines.append(f"*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*")

    return "\n".join(lines)


def main():
    """Main entry point."""
    # Find all issue report files
    issue_files = sorted(glob.glob("data/week-*.json"))

    if not issue_files:
        sys.stderr.write("No week data files found.\n")
        sys.exit(1)

    sys.stderr.write(f"Found {len(issue_files)} week snapshots\n")
    sys.stderr.write(f"Generating comprehensive reports...\n\n")

    # Create issues directory
    os.makedirs("issues", exist_ok=True)

    # Process each week
    previous_data = None
    for idx, weekly_file in enumerate(issue_files):
        try:
            with open(weekly_file, "r") as f:
                weekly_data = json.load(f)
        except Exception as e:
            sys.stderr.write(f"Error reading {weekly_file}: {e}\n")
            continue

        week = weekly_data.get("week", "unknown")
        sys.stderr.write(f"Processing week {week}... ")

        # Create markdown report
        body = create_issue_body(weekly_data, previous_data)

        # Save to file
        issue_title = f"[Tracking] {week} — AI Security Ecosystem Report"
        issue_file = f"issues/{week}-report.md"

        with open(issue_file, "w") as f:
            f.write(f"# {issue_title}\n\n")
            f.write(body)

        sys.stderr.write(f"✅ created {issue_file}\n")

        previous_data = weekly_data

    sys.stderr.write(f"\n✅ All reports generated\n")
    sys.stderr.write(f"Files saved in issues/ directory\n")


if __name__ == "__main__":
    main()
