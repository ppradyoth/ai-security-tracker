# AI Security Tracker

Comprehensive security monitoring across the AI/ML ecosystem. Track security issues, vulnerabilities, and initiatives across 50+ repositories.

**Dashboard:** [https://ppradyoth.github.io/ai-security-tracker](https://ppradyoth.github.io/ai-security-tracker)

## Overview

The AI Security Tracker provides ecosystem-wide visibility into security practices and vulnerabilities across:

- **7+ AI CLI Tools** — Claude Code, OpenAI Codex, Gemini, GitHub Copilot, etc.
- **6+ ML Frameworks** — TensorFlow, PyTorch, JAX, Hugging Face, LLaMA, etc.
- **4+ Agent Frameworks** — LangChain, AutoGen, CrewAI, LlamaIndex
- **5+ Security Tools** — Bandit, Safety, Snyk, GitGuardian, TruffleHog
- **2+ Security References** — OWASP, Awesome Security

**Tracking 50+ repositories daily for security signals:**
- CVEs and reported vulnerabilities
- GitHub security labels
- Security-related keywords
- Vulnerability patterns
- Active security initiatives

## Features

✨ **Real-time Monitoring**
- Daily security data collection from 50+ repos
- GitHub API integration (no external services needed)
- Automated workflow runs at 08:00 UTC daily

📊 **Comprehensive Dashboard**
- Overview: Total issues, trends, engagement metrics
- By Repository: Per-repo issue counts and recent activity
- Top Issues: Most active security discussions
- Label Distribution: Popular security topics

🎨 **Minimalist Design**
- Apple/Google-inspired aesthetic
- Light theme with dark mode support
- Responsive design (desktop, tablet, mobile)
- Fast client-side rendering (no backend)

📈 **Historical Data**
- 180-day time window
- Daily snapshots stored in Git
- Easy trend analysis
- Full audit trail

## Quick Start

### View the Dashboard

Open [https://ppradyoth.github.io/ai-security-tracker](https://ppradyoth.github.io/ai-security-tracker) in your browser.

### Run Locally

```bash
# Clone the repo
git clone https://github.com/ppradyoth/ai-security-tracker.git
cd ai-security-tracker

# Install dependencies
pip install requests

# Collect security data
export GITHUB_TOKEN=your_token_here
python scripts/fetch_security_data.py > /tmp/security.json

# Generate dashboard data
python scripts/generate_dashboard_data.py /tmp/security.json > docs/data.json

# Serve locally
python -m http.server 8000
# Visit http://localhost:8000/docs/
```

## Architecture

### Data Collection (`scripts/fetch_security_data.py`)

1. Reads repository manifest from `manifest.json`
2. Queries GitHub API for security-related issues/PRs
3. Extracts security signals:
   - Labels: "security", "vulnerability", "cve"
   - Keywords: "credential", "exploit", "injection", etc.
4. Outputs structured JSON with 180-day history

### Dashboard Generation (`scripts/generate_dashboard_data.py`)

1. Takes raw security data
2. Aggregates by repository, issue type, engagement
3. Calculates metrics and trends
4. Generates optimized JSON for frontend

### Frontend (`docs/`)

- **index.html** — Semantic HTML structure
- **style.css** — Minimalist Apple/Google styling
- **script.js** — Client-side data loading and rendering
- **data.json** — Generated dashboard data (committed daily)

### Automation (`.github/workflows/`)

- **fetch-security-data.yml** — Daily data collection at 08:00 UTC
  - Runs metrics collection
  - Commits daily snapshot
  - Generates and deploys dashboard

## Configuration

### Adding Repositories

Edit `manifest.json` to add repos to track:

```json
"ai_cli_tools": [
  {
    "name": "Your Tool Name",
    "owner": "github-owner",
    "repo": "repo-name",
    "focus": "Brief description of security focus"
  }
]
```

### Customizing Security Signals

Edit security keywords and patterns in `manifest.json`:

```json
"security_labels": ["security", "vulnerability", ...],
"vulnerability_keywords": ["vulnerability", "exploit", ...],
"credential_keywords": ["credential", "secret", ...]
```

## Data Structure

### Raw Security Data (`data/YYYY-MM-DD.json`)

```json
{
  "generated_at": "2026-05-25T08:00:00Z",
  "total_repos_tracked": 50,
  "total_security_issues": 1234,
  "issues": [
    {
      "repo": "Repository Name",
      "number": 12345,
      "title": "Issue Title",
      "url": "https://...",
      "type": "Issue|PR",
      "state": "open|closed",
      "created_at": "2026-05-20T...",
      "updated_at": "2026-05-25T...",
      "labels": ["security", "cve"],
      "comments": 5,
      "reactions": 2,
      "signals": {
        "has_security_label": true,
        "security_keywords_found": ["vulnerability"],
        "credential_keywords_found": []
      }
    }
  ]
}
```

### Dashboard Data (`docs/data.json`)

```json
{
  "generated_at": "...",
  "summary": {
    "total_repos_tracked": 50,
    "total_security_issues": 1234,
    "issues_by_state": { "open": 800, "closed": 434 },
    "issues_by_type": { "Issue": 900, "PR": 334 }
  },
  "top_repos": [...],
  "top_issues_by_engagement": [...],
  "labels_distribution": [...]
}
```

## Development

### Phase 1: MVP ✅
- [x] Repository manifest with 50+ curated repos
- [x] GitHub API security data collection
- [x] Dashboard with 4 primary views
- [x] Daily automation workflow
- [x] GitHub Pages deployment

### Phase 2: Expansion (Planned)
- [ ] Trend analysis (velocity, response time)
- [ ] CVE data integration (NVD API)
- [ ] Weekly and monthly reports
- [ ] Tool comparison features
- [ ] Auto-discovery of new repos

### Phase 3: Advanced (Future)
- [ ] Visualization with charts (Chart.js, D3)
- [ ] Machine learning anomaly detection
- [ ] Community features (annotations, discussions)
- [ ] Email/Slack alerts
- [ ] Metrics export API

## Troubleshooting

**Dashboard shows no data?**
1. Check `docs/data.json` exists and is not empty
2. Run `python scripts/fetch_security_data.py` locally
3. Verify GitHub token has proper permissions

**Workflow fails with permission error?**
1. Ensure workflow has `permissions: { contents: write }`
2. Check GitHub Actions is enabled in repo settings
3. Verify token in secrets

**Repos not showing results?**
1. Check repo names are correct in `manifest.json`
2. Verify repos exist and have public issues
3. Check GitHub API rate limits: `gh api rate_limit`

## Resources

- **Setup Guide:** See [SETUP.md](SETUP.md)
- **GitHub API Docs:** https://docs.github.com/en/rest
- **Inspiration:** [Big Model Radar](https://github.com/gsscsd/big_model_radar)

## License

MIT License — See LICENSE file

## Questions?

Open an issue or visit the [GitHub repository](https://github.com/ppradyoth/ai-security-tracker).
