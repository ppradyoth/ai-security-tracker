#!/usr/bin/env python3
"""
Generate comprehensive GitHub issue reports (Big Model Radar format).

Creates richly detailed weekly security tracking reports with:
- Executive summary with trend analysis
- Detailed repository breakdown with severity metrics
- Security category analysis
- Top issues by engagement with context
- Week-over-week trend analysis
- Key findings and recommendations
"""

import json
import os
import sys
from datetime import datetime, timedelta
import glob
from collections import defaultdict

def detect_severity(item):
    """Detect item severity from labels and signals."""
    labels = item.get("labels", [])
    title = item.get("title", "").lower()
    category = item.get("security_category", "").lower()

    # Check for critical signals
    if any("critical" in label.lower() for label in labels):
        return "critical"
    if any("cve" in label.lower() for label in labels):
        return "critical"
    if category == "cve":
        return "critical"
    if any(x in title for x in ["rce", "remote code execution", "critical vulnerability"]):
        return "critical"

    # Check for high severity
    if any("high" in label.lower() for label in labels):
        return "high"
    if any("vulnerability" in label.lower() for label in labels):
        return "high"
    if any("exploit" in label.lower() for label in labels):
        return "high"
    if any(x in category for x in ["injection", "credential", "auth"]):
        return "high"

    # Check for medium
    if any("medium" in label.lower() for label in labels):
        return "medium"
    if any(x in category for x in ["dos", "dependency"]):
        return "medium"

    return "low"

def get_emoji(severity):
    """Get emoji for severity."""
    return {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }.get(severity, "⚪")

def categorize_repos(repos_data):
    """Group repos by category."""
    categorized = defaultdict(list)
    for repo_name, data in repos_data.items():
        category = data.get("category", "other")
        categorized[category].append((repo_name, data))
    return categorized

def calculate_trends(current_week, previous_week):
    """Calculate trend metrics."""
    curr_total = sum(r.get("issue_count", 0) for r in current_week.values())
    prev_total = sum(r.get("issue_count", 0) for r in previous_week.values()) if previous_week else 0

    if prev_total == 0:
        return {"change": curr_total, "percent": 100 if curr_total > 0 else 0, "direction": "→"}

    change = curr_total - prev_total
    percent = abs(round(100 * change / prev_total, 1))

    if change > 0:
        return {"change": change, "percent": percent, "direction": "↑"}
    elif change < 0:
        return {"change": abs(change), "percent": percent, "direction": "↓"}
    else:
        return {"change": 0, "percent": 0, "direction": "→"}

def create_detailed_report(week_data, previous_week_data=None):
    """Create comprehensive markdown report."""
    week = week_data.get("week", "Unknown")
    start_date = week_data.get("start_date", "")
    end_date = week_data.get("end_date", "")
    repos = week_data.get("repositories", {})

    # Calculate metrics
    total_issues = sum(r.get("issue_count", 0) for r in repos.values())
    total_prs = sum(r.get("pr_count", 0) for r in repos.values())
    open_count = sum(r.get("open_count", 0) for r in repos.values())
    closed_count = sum(r.get("closed_count", 0) for r in repos.values())

    # Severity breakdown across all issues
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    category_counts = defaultdict(int)
    all_items = []

    for repo_name, repo_data in repos.items():
        for item in repo_data.get("top_issues", []):
            severity = detect_severity(item)
            severity_counts[severity] += 1
            category = item.get("security_category", "other")
            category_counts[category] += 1
            all_items.append({
                "repo": repo_name,
                "title": item.get("title", ""),
                "number": item.get("number", ""),
                "url": item.get("url", ""),
                "severity": severity,
                "category": category,
                "type": item.get("type", "Issue"),
                "comments": item.get("comments", 0),
                "reactions": item.get("reactions", 0),
                "state": item.get("state", "open")
            })

    # Calculate trends
    trends = calculate_trends(repos, previous_week_data.get("repositories", {}) if previous_week_data else {})

    lines = []

    # ========== HEADER ==========
    lines.append(f"# 🔒 {week} — AI Security Ecosystem Report")
    lines.append("")
    lines.append(f"**Full monitoring of security issues across 22+ AI/ML repositories**")
    lines.append("")

    # ========== EXECUTIVE SUMMARY ==========
    lines.append("## 📊 Executive Summary")
    lines.append("")
    lines.append(f"**Period:** {start_date.split('T')[0]} → {end_date.split('T')[0]} (7 days)")
    lines.append("")
    lines.append("### Key Metrics")
    lines.append("")
    lines.append(f"| Metric | Count | Status |")
    lines.append("|--------|-------|--------|")
    lines.append(f"| **Repos Tracked** | {len(repos)} | ✅ Active |")
    lines.append(f"| **Security Issues** | {total_issues} | {trends['direction']} {'+' if trends['change'] >= 0 else ''}{trends['change']} ({trends['percent']}%) |")
    lines.append(f"| **Security PRs** | {total_prs} | 🔧 Fixes |")
    lines.append(f"| **Open Items** | {open_count} | ⏳ Pending |")
    lines.append(f"| **Closed Items** | {closed_count} | ✓ Resolved |")
    lines.append("")

    # ========== SEVERITY DISTRIBUTION ==========
    lines.append("## 🎯 Severity Distribution")
    lines.append("")
    lines.append("This week's security issues breakdown by severity level:")
    lines.append("")

    total_issues_all = sum(severity_counts.values())
    for severity in ["critical", "high", "medium", "low"]:
        count = severity_counts[severity]
        pct = round(100 * count / total_issues_all, 1) if total_issues_all > 0 else 0
        bar_length = max(1, round(count / 2)) if count > 0 else 0
        bar = "█" * bar_length
        lines.append(f"- {get_emoji(severity)} **{severity.upper()}** ({count} issues, {pct}%) {bar}")

    lines.append("")

    # ========== SECURITY CATEGORY BREAKDOWN ==========
    lines.append("## 🏷️ Security Category Analysis")
    lines.append("")
    lines.append("Issues and PRs grouped by security type:")
    lines.append("")

    for category in sorted(category_counts.keys(), key=lambda x: category_counts[x], reverse=True):
        count = category_counts[category]
        pct = round(100 * count / total_issues_all, 1) if total_issues_all > 0 else 0
        emoji = {
            "cve": "🚨",
            "vulnerability": "⚠️",
            "credential": "🔑",
            "injection": "💉",
            "auth": "🔐",
            "dos": "💥",
            "dependency": "📦",
            "encryption": "🔒",
            "other": "❓"
        }.get(category, "❓")
        lines.append(f"{emoji} **{category.upper()}** — {count} issues ({pct}%)")

    lines.append("")

    # ========== REPOSITORY BREAKDOWN ==========
    lines.append("## 📦 Security Issues by Repository")
    lines.append("")

    # Group repos by category
    categorized = categorize_repos(repos)

    for repo_category in sorted(categorized.keys()):
        category_repos = categorized[repo_category]
        category_total = sum(r[1].get("issue_count", 0) for r in category_repos)

        if category_total == 0:
            continue

        lines.append(f"### {repo_category.upper()} ({len(category_repos)} repos)")
        lines.append("")
        lines.append("| Repository | Issues | PRs | Critical | High | State | Top Issue |")
        lines.append("|---|---:|---:|---:|---:|---|---|")

        for repo_name, data in sorted(category_repos, key=lambda x: x[1].get("issue_count", 0), reverse=True):
            owner = data.get("owner", "")
            repo = data.get("repo", "")
            issue_count = data.get("issue_count", 0)
            pr_count = data.get("pr_count", 0)
            open_count = data.get("open_count", 0)

            # Count severity for this repo
            critical_count = 0
            high_count = 0
            for item in data.get("top_issues", []):
                severity = detect_severity(item)
                if severity == "critical":
                    critical_count += 1
                elif severity == "high":
                    high_count += 1

            # Top issue
            top_item = data.get("top_issues", [{}])[0] if data.get("top_issues") else None
            if top_item:
                issue_title = top_item.get("title", "No issues")
                if len(issue_title) > 40:
                    issue_title = issue_title[:37] + "..."
                issue_link = top_item.get("url", "#")
                issue_num = top_item.get("number", "")
                top_issue_cell = f"[#{issue_num}]({issue_link})"
            else:
                top_issue_cell = "—"

            state_emoji = "🟢" if open_count == 0 else "🟡" if open_count < 3 else "🔴"
            repo_link = f"https://github.com/{owner}/{repo}"

            lines.append(
                f"| [{repo_name}]({repo_link}) | {issue_count} | {pr_count} | {critical_count} | {high_count} | "
                f"{state_emoji} ({open_count} open) | {top_issue_cell} |"
            )

        lines.append("")

    # ========== TOP ISSUES BY ENGAGEMENT ==========
    if all_items:
        lines.append("## 💬 Top Issues by Engagement")
        lines.append("")

        top_engaged = sorted(all_items, key=lambda x: x["comments"] + x["reactions"], reverse=True)[:10]

        for idx, item in enumerate(top_engaged, 1):
            severity_emoji = get_emoji(item["severity"])
            type_badge = "📄 Issue" if item["type"] == "Issue" else "🔧 PR"
            state_badge = "🟢 Open" if item["state"] == "open" else "✓ Closed"

            lines.append(f"**{idx}. {severity_emoji} [{item['repo']} #{item['number']}]({item['url']})**")
            lines.append(f"   - **Title:** {item['title']}")
            lines.append(f"   - **Type:** {type_badge} | **State:** {state_badge} | **Category:** {item['category'].upper()}")
            lines.append(f"   - **Engagement:** 💬 {item['comments']} comments | ❤️ {item['reactions']} reactions")
            lines.append("")

    # ========== NEWLY OPENED THIS WEEK ==========
    lines.append("## 🆕 Newly Opened This Week")
    lines.append("")

    new_issues = [i for i in all_items if i["state"] == "open"]
    if new_issues:
        lines.append(f"**{len(new_issues)} new security issues/PRs discovered:**")
        lines.append("")

        for item in new_issues[:5]:  # Show top 5
            lines.append(f"- {get_emoji(item['severity'])} **[{item['repo']}]** {item['title']}")

        if len(new_issues) > 5:
            lines.append(f"- ... and {len(new_issues) - 5} more")

        lines.append("")

    # ========== RECENTLY RESOLVED ==========
    resolved_issues = [i for i in all_items if i["state"] == "closed"]
    if resolved_issues:
        lines.append("## ✅ Recently Resolved")
        lines.append("")
        lines.append(f"**{len(resolved_issues)} security issues/PRs were closed this week.**")
        lines.append("")

    # ========== TREND ANALYSIS ==========
    lines.append("## 📈 Trend Analysis")
    lines.append("")

    if previous_week_data:
        prev_repos = previous_week_data.get("repositories", {})
        prev_total = sum(r.get("issue_count", 0) for r in prev_repos.values())
        prev_prs = sum(r.get("pr_count", 0) for r in prev_repos.values())

        issue_trend = "↑ Increased" if total_issues > prev_total else "↓ Decreased" if total_issues < prev_total else "→ Stable"
        pr_trend = "↑ More fixes" if total_prs > prev_prs else "↓ Fewer fixes" if total_prs < prev_prs else "→ Same"

        lines.append(f"- **Issue Velocity:** {issue_trend} ({total_issues} vs {prev_total} last week)")
        lines.append(f"- **Fix Velocity:** {pr_trend} ({total_prs} vs {prev_prs} PRs last week)")
    else:
        lines.append(f"- **Issue Discovery:** {total_issues} security issues detected")
        lines.append(f"- **Fix Rate:** {total_prs} PRs to address them")

    lines.append("")

    # ========== KEY FINDINGS ==========
    lines.append("## 🔍 Key Findings")
    lines.append("")

    # Auto-generated findings
    findings = []

    if severity_counts["critical"] > 0:
        findings.append(f"⚠️ **{severity_counts['critical']} CRITICAL issue(s)** require immediate attention")

    if total_issues > (previous_week_data.get("repositories", {}) if previous_week_data else {}):
        findings.append(f"📈 Security issue discovery rate is trending upward")

    most_active_repo = max(repos.items(), key=lambda x: x[1].get("issue_count", 0), default=None)
    if most_active_repo:
        findings.append(f"🔥 **{most_active_repo[0]}** is the most active repo ({most_active_repo[1].get('issue_count', 0)} issues)")

    if category_counts:
        top_category = max(category_counts.items(), key=lambda x: x[1])[0]
        findings.append(f"🏷️ **{top_category.upper()}** is the most common security issue type")

    if closed_count > open_count:
        findings.append(f"✅ Strong resolution momentum: more issues closed ({closed_count}) than open ({open_count})")
    elif open_count > closed_count:
        findings.append(f"⏳ Backlog building: {open_count} open items awaiting resolution")

    if findings:
        for finding in findings:
            lines.append(f"- {finding}")
    else:
        lines.append("- No critical findings this week")

    lines.append("")

    # ========== RECOMMENDATIONS ==========
    lines.append("## 💡 Recommendations")
    lines.append("")

    if severity_counts["critical"] > 0:
        lines.append("1. **Prioritize Critical Issues** — Allocate resources to resolve critical vulnerabilities immediately")

    if open_count > 5:
        lines.append("2. **Reduce Backlog** — Many open issues need attention; consider triaging by severity")

    if closed_count > 0:
        lines.append("3. **Maintain Momentum** — Continue closing issues at current pace")

    lines.append("4. **Monitor Trends** — Track issue velocity to catch spikes early")
    lines.append("")

    # ========== FOOTER ==========
    lines.append("---")
    lines.append("")
    lines.append(f"*Generated by [AI Security Tracker](https://github.com/ppradyoth/ai-security-tracker) at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*")
    lines.append(f"*Using TinyLlama-based security classification for comprehensive coverage*")

    return "\n".join(lines)

def main():
    """Generate reports from all weekly snapshots."""
    week_files = sorted(glob.glob("data/week-*.json"))

    if not week_files:
        sys.stderr.write("No week data files found in data/\n")
        sys.exit(1)

    sys.stderr.write(f"Found {len(week_files)} weekly snapshots\n")
    sys.stderr.write(f"Generating comprehensive reports...\n\n")

    os.makedirs("issues", exist_ok=True)

    previous_data = None
    for weekly_file in week_files:
        try:
            with open(weekly_file, "r") as f:
                week_data = json.load(f)
        except Exception as e:
            sys.stderr.write(f"⚠️  Error reading {weekly_file}: {e}\n")
            continue

        week = week_data.get("week", "unknown")
        sys.stderr.write(f"Generating {week}... ")

        body = create_detailed_report(week_data, previous_data)

        report_file = f"issues/{week}-security-report.md"
        with open(report_file, "w") as f:
            f.write(body)

        sys.stderr.write(f"✅ saved to {report_file}\n")
        previous_data = week_data

    sys.stderr.write(f"\n✅ All {len(week_files)} reports generated in issues/ directory\n")

if __name__ == "__main__":
    main()
