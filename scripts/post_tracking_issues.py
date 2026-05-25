#!/usr/bin/env python3
"""
Post tracking reports to GitHub issues.

Reads generated issue reports and creates GitHub issues with tracking data.
"""

import os
import sys
import glob
import subprocess

try:
    import json
except ImportError:
    pass


def post_issue_to_github(title, body, labels):
    """Post an issue to GitHub using gh CLI."""
    try:
        cmd = [
            "gh",
            "issue",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--label",
            ",".join(labels),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # Extract issue URL from output
            issue_url = result.stdout.strip().split("\n")[-1]
            return issue_url
        else:
            sys.stderr.write(f"Error creating issue: {result.stderr}\n")
            return None

    except Exception as e:
        sys.stderr.write(f"Error posting issue: {e}\n")
        return None


def main():
    """Main entry point."""
    # Find all issue report files
    issue_files = sorted(glob.glob("issues/*-report.md"))

    if not issue_files:
        sys.stderr.write("No issue report files found.\n")
        sys.exit(1)

    sys.stderr.write(f"Found {len(issue_files)} issue reports\n")
    sys.stderr.write(f"Checking for existing issues in repository...\n\n")

    # Check if gh is available
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--label", "security-ecosystem"],
            capture_output=True,
            text=True
        )
        existing_issues = result.stdout.count("\n")
    except:
        sys.stderr.write("Error: gh CLI not available. Install GitHub CLI to post issues.\n")
        sys.exit(1)

    sys.stderr.write(f"Found {existing_issues} existing tracking issues\n\n")

    # Post each report
    posted_count = 0
    for issue_file in issue_files[-4:]:  # Start with recent weeks only
        with open(issue_file, "r") as f:
            content = f.read()

        # Extract title
        lines = content.split("\n")
        title = lines[0].lstrip("# ").strip()

        # Rest is body
        body = "\n".join(lines[1:]).strip()

        sys.stderr.write(f"Posting: {title}... ")

        # Post to GitHub
        url = post_issue_to_github(
            title,
            body,
            ["tracking", "security-ecosystem", "weekly-report"]
        )

        if url:
            sys.stderr.write(f"✓ {url}\n")
            posted_count += 1
        else:
            sys.stderr.write(f"✗ Failed\n")

    sys.stderr.write(f"\n✅ Posted {posted_count} issues\n")


if __name__ == "__main__":
    main()
