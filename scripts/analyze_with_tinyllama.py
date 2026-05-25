#!/usr/bin/env python3
"""
Analyze security issues with TinyLlama for categorization and severity detection.

Uses a local TinyLlama model (via Ollama) to:
- Categorize issues by type (CVE, credential, injection, auth, DoS, etc.)
- Detect severity level (critical, high, medium, low)
- Extract key risk signals
- Generate brief analysis

Requirements: ollama CLI tool with tinyllama model installed
Installation: curl https://ollama.ai/install.sh | sh && ollama pull tinyllama
"""

import json
import sys
import subprocess
from datetime import datetime


def detect_severity(text):
    """Heuristic-based severity detection as fallback."""
    text_lower = text.lower()

    # Critical indicators
    if any(x in text_lower for x in ["cve-", "critical", "exploit", "rce", "remote code"]):
        return "critical"

    # High indicators
    if any(x in text_lower for x in ["vulnerability", "injection", "authentication bypass", "privilege escalation"]):
        return "high"

    # Medium indicators
    if any(x in text_lower for x in ["information disclosure", "denial of service", "dos"]):
        return "medium"

    return "low"


def detect_category(text):
    """Heuristic-based category detection as fallback."""
    text_lower = text.lower()

    if any(x in text_lower for x in ["cve", "vulnerability"]):
        return "cve"
    if any(x in text_lower for x in ["credential", "secret", "key", "token", "password", "api_key"]):
        return "credential"
    if any(x in text_lower for x in ["injection", "xss", "sql", "command"]):
        return "injection"
    if any(x in text_lower for x in ["authentication", "authorization", "bypass"]):
        return "auth"
    if any(x in text_lower for x in ["dos", "denial", "ddos"]):
        return "dos"
    if any(x in text_lower for x in ["dependency", "component"]):
        return "dependency"

    return "other"


def analyze_with_ollama(issue_title, issue_description=""):
    """Use Ollama+TinyLlama to analyze issue."""
    try:
        prompt = f"""Analyze this security issue briefly:

Title: {issue_title}
Description: {issue_description[:200]}

Respond with exactly:
- Category: (cve|credential|injection|auth|dos|dependency|other)
- Severity: (critical|high|medium|low)
- Risk: (one short sentence)"""

        result = subprocess.run(
            ["ollama", "run", "tinyllama", prompt],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            output = result.stdout.strip()

            # Parse response
            lines = output.split('\n')
            category = "other"
            severity = "medium"
            risk = ""

            for line in lines:
                if "Category:" in line:
                    cat = line.split("Category:")[-1].strip().split('|')[0].lower()
                    if cat in ["cve", "credential", "injection", "auth", "dos", "dependency", "other"]:
                        category = cat
                elif "Severity:" in line:
                    sev = line.split("Severity:")[-1].strip().split('|')[0].lower()
                    if sev in ["critical", "high", "medium", "low"]:
                        severity = sev
                elif "Risk:" in line:
                    risk = line.split("Risk:")[-1].strip()

            return {"category": category, "severity": severity, "risk": risk[:100]}
        else:
            return None

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def enhance_issue_with_analysis(issue):
    """Enhance issue data with AI analysis."""
    title = issue.get("title", "")
    description = issue.get("body", "")

    # Try Ollama analysis first
    analysis = analyze_with_ollama(title, description)

    # Fall back to heuristics
    if not analysis:
        analysis = {
            "category": detect_category(title + " " + description),
            "severity": detect_severity(title + " " + description),
            "risk": "Analysis unavailable"
        }

    # Update issue with analysis
    issue["analysis"] = analysis
    return issue


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: analyze_with_tinyllama.py <security_data.json>\n")
        sys.exit(1)

    try:
        with open(sys.argv[1], "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        sys.stderr.write(f"Error reading {sys.argv[1]}: {e}\n")
        sys.exit(1)

    issues = data.get("issues", [])
    analyzed_count = 0

    sys.stderr.write(f"Analyzing {len(issues)} security issues with TinyLlama...\n")

    for idx, issue in enumerate(issues, 1):
        # Show progress every 10 issues
        if idx % 10 == 0:
            sys.stderr.write(f"  [{idx}/{len(issues)}] analyzed\n")

        # Enhance with analysis
        enhanced = enhance_issue_with_analysis(issue)
        issues[idx - 1] = enhanced
        analyzed_count += 1

    # Update data
    data["issues"] = issues
    data["analysis_completed_at"] = datetime.utcnow().isoformat() + "Z"

    # Output enhanced data
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stderr.write(f"\n✅ Analysis complete: {analyzed_count} issues analyzed\n")
    sys.stderr.write(f"Each issue now includes: category, severity, risk assessment\n")


if __name__ == "__main__":
    main()
