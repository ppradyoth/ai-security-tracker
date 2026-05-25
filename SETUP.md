# AI Security Tracker — Setup Guide

## Overview

The AI Security Tracker monitors security issues, vulnerabilities, and initiatives across 50+ AI/ML and security repositories. It provides comprehensive visibility into the security landscape of the AI ecosystem.

**Key Features:**
- ✅ Daily security data collection from 50+ repos
- ✅ Multiple dashboard views (Overview, Repos, Issues, Labels)
- ✅ Trend analysis and engagement metrics
- ✅ Minimalist Apple/Google-inspired design
- ✅ Real-time updates via GitHub Actions
- ✅ No backend required (GitHub Pages + client-side JS)

## Quick Start

### Prerequisites
- GitHub account with repo access
- Python 3.8+
- `requests` library: `pip install requests`

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ppradyoth/ai-security-tracker.git
   cd ai-security-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install requests
   ```

3. **Run metrics collection locally**
   ```bash
   export GITHUB_TOKEN=your_token_here
   python scripts/fetch_security_data.py > /tmp/security.json
   python scripts/generate_dashboard_data.py /tmp/security.json > docs/data.json
   ```

4. **View the dashboard**
   - Open `docs/index.html` in a browser
   - Or serve locally: `python -m http.server 8000` then visit `http://localhost:8000/docs/`

## Repository Structure

```
ai-security-tracker/
├── .github/workflows/
│   └── fetch-security-data.yml      # Daily data collection (08:00 UTC)
├── scripts/
│   ├── fetch_security_data.py       # Core GitHub API queries
│   └── generate_dashboard_data.py   # Transform data for dashboard
├── docs/
│   ├── index.html                   # Dashboard UI
│   ├── style.css                    # Minimalist styling
│   ├── script.js                    # Client-side rendering
│   └── data.json                    # Generated daily (committed to repo)
├── data/
│   ├── YYYY-MM-DD.json             # Daily snapshots
│   └── latest.json                  # Current data
├── manifest.json                    # Repository configuration
├── README.md                        # Main documentation
└── SETUP.md                         # This file
```

## Configuration

### Adding Repos to Track

Edit `manifest.json`:

```json
"ai_cli_tools": [
  {
    "name": "Your Tool",
    "owner": "github-owner",
    "repo": "repo-name",
    "focus": "Description"
  }
]
```

Categories available:
- `ai_cli_tools` — Terminal-based AI assistants
- `ml_frameworks` — Deep learning & ML libraries
- `agent_frameworks` — Multi-agent orchestration
- `security_tools` — Security scanners & detectors
- `security_references` — Best practices & guidelines

### Customizing Security Signals

Edit `security_signals` in `manifest.json`:

```json
"security_labels": ["security", "vulnerability", ...],
"credential_keywords": ["credential", "secret", ...],
"vulnerability_keywords": ["vulnerability", "exploit", ...]
```

## GitHub Actions Workflows

### Daily Data Collection (`fetch-security-data.yml`)

**Trigger:** Every day at 08:00 UTC

**What it does:**
1. Fetches security-related issues/PRs from all repos
2. Extracts security signals (labels, keywords, patterns)
3. Saves daily snapshot to `data/YYYY-MM-DD.json`
4. Generates dashboard-optimized JSON
5. Commits and pushes to repo

**Manual Trigger:**
```bash
gh workflow run fetch-security-data.yml --repo ppradyoth/ai-security-tracker
```

## Dashboard

### Hosted on GitHub Pages

**URL:** `https://ppradyoth.github.io/ai-security-tracker`

**Features:**
- **Overview Tab** — Summary metrics, trending issues
- **Repositories Tab** — All tracked repos with issue counts
- **Issues Tab** — Top security issues by engagement
- **Labels Tab** — Distribution of security labels

### Data Source

Dashboard data comes from `docs/data.json` (generated daily by workflow). The JSON structure:

```json
{
  "generated_at": "ISO timestamp",
  "summary": {
    "total_repos_tracked": number,
    "total_security_issues": number,
    "issues_by_state": { "open": number, "closed": number },
    "issues_by_type": { "PR": number, "Issue": number }
  },
  "top_repos": [
    {
      "repo": "name",
      "issue_count": number,
      "issues": [...]
    }
  ],
  "top_issues_by_engagement": [...]
}
```

## Enabling GitHub Pages

1. Go to **Settings** → **Pages**
2. Set **Source** to "Deploy from a branch"
3. Select **Branch:** `main`, **Folder:** `/docs`
4. Click **Save**
5. Dashboard will be live at: `https://ppradyoth.github.io/ai-security-tracker`

## API Rate Limits

GitHub API has rate limits:
- **Authenticated:** 5,000 requests/hour
- **Per-repo search:** ~30 results per search

The current implementation:
- Fetches 50 issues per repo (max)
- Batches across 50+ repos
- Completes in ~2-3 minutes per run

To increase limits:
- Use a Personal Access Token with `repo` scope
- Or: Implement response caching

## Troubleshooting

### "Workflow Failed: Permission Denied"

**Issue:** Workflow can't commit/push to repo

**Solution:** Ensure `permissions: { contents: write }` is set in `.github/workflows/fetch-security-data.yml`

### "No Data in Dashboard"

**Issue:** Dashboard shows no issues

**Cause:** 
- `docs/data.json` is empty or missing
- GitHub API returned no results

**Solution:**
1. Run locally: `python scripts/fetch_security_data.py`
2. Check GitHub API token is valid: `gh auth status`
3. Check repos in `manifest.json` are correct

### "Rate Limited"

**Issue:** Too many GitHub API requests

**Solution:**
1. Add delay between requests
2. Increase cron schedule to run less frequently
3. Use a GitHub App instead of Personal Access Token

## Next Steps

### Phase 2 (Planned)
- [ ] CVE data integration (NVD API)
- [ ] Trend analysis (issues per week, velocity)
- [ ] Tool comparison features
- [ ] Weekly/monthly reports
- [ ] Auto-discovery of new repos

### Phase 3 (Future)
- [ ] Visualization (Charts.js, D3)
- [ ] Anomaly detection
- [ ] Community annotations
- [ ] Alert system

## Contributing

To improve the tracker:

1. Open an issue with suggestions
2. Submit PRs for new features
3. Add repos to monitor
4. Help improve patterns/keywords

## License

MIT — See LICENSE file

## Resources

- **GitHub API Docs:** https://docs.github.com/en/rest
- **Related Projects:**
  - Big Model Radar: https://github.com/gsscsd/big_model_radar
  - OWASP Top 10: https://owasp.org/Top10/

---

**Questions?** Open an issue on GitHub or check the main README.md
