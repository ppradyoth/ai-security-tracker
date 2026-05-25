#!/usr/bin/env python3
"""
Classify ALL issues and PRs as security-related or not using TinyLlama.

Input: Raw JSON with all issues/PRs
Output: Same JSON with added 'is_security_related' field + 'security_category' for those that are
"""

import json
import sys
import subprocess
from datetime import datetime

def classify_with_ollama(title, body=""):
    """Use Ollama+TinyLlama to classify if issue/PR is security-related."""
    try:
        # Limit body to first 300 chars to avoid huge prompts
        body_snippet = body[:300] if body else ""

        prompt = f"""Is this GitHub issue or pull request related to SECURITY (vulnerability, bug fix, authentication, authorization, encryption, credential management, security feature, etc.)?

Title: {title}
Description: {body_snippet}

Respond with ONLY one word: YES or NO

Then on the next line, provide the security category if YES (CVE, vulnerability, credential, injection, auth, dos, dependency, encryption, other), or leave blank if NO."""

        result = subprocess.run(
            ["ollama", "run", "tinyllama", prompt],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            lines = output.split('\n')

            is_security = "YES" in lines[0].upper()
            category = "other"

            if is_security and len(lines) > 1:
                cat = lines[1].lower().strip()
                valid_cats = ["cve", "vulnerability", "credential", "injection", "auth", "dos", "dependency", "encryption", "other"]
                if cat in valid_cats:
                    category = cat

            return {"is_security": is_security, "category": category}
        else:
            return None

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

def fallback_classify(title, body=""):
    """Fallback heuristic classification."""
    combined = (title + " " + body).lower()

    # Security keywords (comprehensive)
    security_keywords = [
        "security", "vulnerability", "cve", "cvss", "exploit", "rce",
        "credential", "secret", "api_key", "token", "password", "auth",
        "authorization", "injection", "sql", "xss", "csrf", "ddos", "dos",
        "encryption", "decrypt", "tlv", "ssl", "tls", "hash",
        "vulnerability disclosure", "bug bounty", "sec", "penetration",
        "privilege escalation", "bypass", "attack", "threat", "vulnerability",
        "patch", "security fix", "security update", "secure", "unsafe"
    ]

    is_security = any(keyword in combined for keyword in security_keywords)

    # Categorize if security-related
    category = "other"
    if is_security:
        if any(x in combined for x in ["cve", "vulnerability"]):
            category = "vulnerability"
        elif any(x in combined for x in ["credential", "secret", "key", "password", "token"]):
            category = "credential"
        elif any(x in combined for x in ["injection", "xss", "sql"]):
            category = "injection"
        elif any(x in combined for x in ["auth", "authorization"]):
            category = "auth"
        elif any(x in combined for x in ["dos", "ddos"]):
            category = "dos"
        elif any(x in combined for x in ["encrypt", "decrypt", "tls", "ssl"]):
            category = "encryption"

    return {"is_security": is_security, "category": category}

def classify_item(item):
    """Classify a single issue/PR."""
    title = item.get("title", "")
    body = item.get("body", "")

    # Try Ollama first
    result = classify_with_ollama(title, body)

    # Fallback to heuristics if Ollama unavailable
    if not result:
        result = fallback_classify(title, body)

    item["is_security_related"] = result.get("is_security", False)
    if result.get("is_security"):
        item["security_category"] = result.get("category", "other")

    return item

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: analyze_with_tinyllama.py <raw_items.json>\n")
        sys.exit(1)

    try:
        with open(sys.argv[1], "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        sys.stderr.write(f"Error reading {sys.argv[1]}: {e}\n")
        sys.exit(1)

    items = data.get("items", [])
    security_count = 0

    sys.stderr.write(f"Classifying {len(items)} issues/PRs with TinyLlama...\n")
    sys.stderr.write(f"(Falls back to heuristics if Ollama unavailable)\n\n")

    for idx, item in enumerate(items, 1):
        # Show progress
        if idx % 10 == 0:
            sys.stderr.write(f"  [{idx}/{len(items)}] classified\n")

        # Classify
        classified = classify_item(item)
        items[idx - 1] = classified

        if classified.get("is_security_related"):
            security_count += 1

    # Update data
    data["items"] = items
    data["classification_completed_at"] = datetime.utcnow().isoformat() + "Z"
    data["security_items_count"] = security_count
    data["security_percentage"] = round(100 * security_count / len(items), 1) if items else 0

    # Output
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stderr.write(f"\n✅ Classification complete\n")
    sys.stderr.write(f"   Total items: {len(items)}\n")
    sys.stderr.write(f"   Security-related: {security_count} ({data['security_percentage']}%)\n")
    sys.stderr.write(f"   Each item now includes: is_security_related, security_category (if relevant)\n")

if __name__ == "__main__":
    main()
