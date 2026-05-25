/**
 * AI Security Tracker Dashboard
 * Light theme + minimalist design
 */

class SecurityTracker {
  constructor() {
    this.data = null;
    this.filteredByLabel = null;
    this.init();
  }

  async init() {
    this.setupTabNavigation();
    await this.loadData();
    if (this.data) {
      this.renderDashboard();
    }
  }

  setupTabNavigation() {
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => {
      button.addEventListener('click', () => {
        const tabName = button.getAttribute('data-tab');
        this.switchTab(tabName);
      });
    });
  }

  switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
      tab.classList.remove('active');
    });

    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(button => {
      button.classList.remove('active');
    });

    // Show selected tab
    const tab = document.getElementById(`${tabName}-tab`);
    if (tab) {
      tab.classList.add('active');
    }

    // Add active class to clicked button
    const button = document.querySelector(`[data-tab="${tabName}"]`);
    if (button) {
      button.classList.add('active');
    }
  }

  async loadData() {
    try {
      const response = await fetch('data.json');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      this.data = await response.json();
      console.log('✅ Dashboard data loaded successfully');
    } catch (error) {
      console.error('Error loading data:', error);
      this.showError(`Failed to load data: ${error.message}`);
    }
  }

  renderDashboard() {
    if (!this.data) return;

    this.renderOverviewTab();
    this.renderIssuesTab();
    this.renderPullRequestsTab();
    this.renderRepositoriesTab();
    this.renderLabelsTab();
  }

  // ===== OVERVIEW TAB =====
  renderOverviewTab() {
    const summary = this.data.summary;

    // Update metrics
    document.getElementById('lastUpdated').textContent = this.formatDate(this.data.generated_at);
    document.getElementById('footerTime').textContent = this.formatDate(this.data.generated_at);
    document.getElementById('totalRepos').textContent = summary.total_repos_tracked.toLocaleString();
    document.getElementById('totalIssues').textContent = summary.total_security_issues.toLocaleString();
    document.getElementById('openIssues').textContent = (summary.issues_by_state.open || 0).toLocaleString();
    document.getElementById('closedIssues').textContent = (summary.issues_by_state.closed || 0).toLocaleString();

    // Render top issues by engagement
    const topIssues = this.data.top_issues_by_engagement || [];
    const topIssuesHtml = topIssues.slice(0, 10).map(issue => this.createIssueCard(issue)).join('');
    document.getElementById('topIssues').innerHTML = topIssuesHtml || '<div class="empty-state"><p>No issues found</p></div>';
  }

  // ===== ISSUES TAB =====
  renderIssuesTab() {
    const issues = (this.data.issues || []).filter(issue => issue.type === 'Issue');
    const filteredIssues = this.filteredByLabel
      ? issues.filter(issue => issue.labels && issue.labels.includes(this.filteredByLabel))
      : issues;

    const html = filteredIssues.length > 0
      ? filteredIssues.map(issue => this.createIssueCard(issue)).join('')
      : '<div class="empty-state"><h3>No issues found</h3><p>Check back later for updates</p></div>';

    document.getElementById('issuesList').innerHTML = html;
  }

  // ===== PULL REQUESTS TAB =====
  renderPullRequestsTab() {
    const prs = (this.data.pull_requests || []).filter(pr => pr.type === 'PR');
    const filteredPRs = this.filteredByLabel
      ? prs.filter(pr => pr.labels && pr.labels.includes(this.filteredByLabel))
      : prs;

    const html = filteredPRs.length > 0
      ? filteredPRs.map(pr => this.createIssueCard(pr)).join('')
      : '<div class="empty-state"><h3>No pull requests found</h3><p>Check back later for updates</p></div>';

    document.getElementById('prList').innerHTML = html;
  }

  // ===== ALL REPOS TAB =====
  renderRepositoriesTab() {
    const repos = this.data.all_repos || [];

    if (repos.length === 0) {
      document.getElementById('reposTable').innerHTML = '<tr><td colspan="5" class="empty-state">No repositories found</td></tr>';
      return;
    }

    const rows = repos.map(repo => `
      <tr>
        <td><strong><a href="https://github.com/${repo.owner}/${repo.repo}" target="_blank">${repo.name}</a></strong></td>
        <td><span class="tag">${repo.category || 'uncategorized'}</span></td>
        <td style="text-align: center;"><strong>${repo.issue_count || 0}</strong></td>
        <td style="text-align: center;"><strong>${repo.pr_count || 0}</strong></td>
        <td><small>${repo.last_activity ? this.formatDate(repo.last_activity) : 'Unknown'}</small></td>
      </tr>
    `).join('');

    document.getElementById('reposTable').innerHTML = rows;
  }

  // ===== LABELS TAB =====
  renderLabelsTab() {
    const labels = this.data.labels_distribution || [];

    if (labels.length === 0) {
      document.getElementById('labelsList').innerHTML = '<div class="empty-state"><p>No labels found</p></div>';
      return;
    }

    const html = labels.map(([label, count]) => `
      <div class="card" style="padding: 12px 16px; cursor: pointer; transition: all 0.2s ease;" onclick="tracker.filterByLabel('${label}')">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <strong>${label}</strong>
          <span style="background: #e5e7eb; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">${count}</span>
        </div>
      </div>
    `).join('');

    document.getElementById('labelsList').innerHTML = html;
  }

  // ===== HELPER: CREATE ISSUE CARD =====
  createIssueCard(issue) {
    if (!issue) return '';

    const severity = this.detectSeverity(issue);
    const severityClass = `issue-card ${severity}`;
    const issueBadgeClass = issue.type === 'PR' ? 'badge-pr' : 'badge-issue';
    const typeBadge = issue.type === 'PR' ? 'PR' : 'Issue';
    const stateBadgeClass = issue.state === 'open' ? 'badge-open' : 'badge-closed';
    const stateText = issue.state === 'open' ? 'OPEN' : 'CLOSED';

    return `
      <div class="${severityClass}">
        <a href="${issue.url}" target="_blank" class="issue-title">#${issue.number} ${this.escapeHtml(issue.title)}</a>
        <div class="issue-tags">
          <span class="badge ${issueBadgeClass}">${typeBadge}</span>
          <span class="badge ${stateBadgeClass}">${stateText}</span>
          <span class="tag">${this.escapeHtml(issue.repo)}</span>
        </div>
        <div class="issue-meta">
          <span>💬 ${issue.comments || 0}</span>
          <span>❤️ ${issue.reactions || 0}</span>
          <span>Updated: ${this.formatDate(issue.updated_at)}</span>
        </div>
      </div>
    `;
  }

  // ===== HELPER: DETECT SEVERITY =====
  detectSeverity(issue) {
    // Check for critical signals
    if (issue.signals) {
      if (issue.signals.has_vulnerability_label) return 'critical';
      if (issue.signals.credential_keywords_found && issue.signals.credential_keywords_found.length > 0) return 'high';
    }

    // Check labels for severity keywords
    if (issue.labels) {
      const labelsStr = issue.labels.join(' ').toLowerCase();
      if (labelsStr.includes('critical') || labelsStr.includes('cve')) return 'critical';
      if (labelsStr.includes('high') || labelsStr.includes('vulnerability')) return 'high';
      if (labelsStr.includes('medium')) return 'medium';
    }

    // Check title for severity keywords
    const title = (issue.title || '').toLowerCase();
    if (title.includes('critical') || title.includes('cve')) return 'critical';
    if (title.includes('vulnerability') || title.includes('exploit')) return 'high';

    return 'medium'; // Default to medium
  }

  // ===== HELPER: FORMAT DATE =====
  formatDate(dateString) {
    if (!dateString) return 'Unknown';

    try {
      const date = new Date(dateString);
      const now = new Date();
      const diff = now - date;

      // Less than a minute
      if (diff < 60000) return 'just now';

      // Less than an hour
      if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}m ago`;
      }

      // Less than a day
      if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
      }

      // Less than a week
      if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}d ago`;
      }

      // Less than a month
      if (diff < 2592000000) {
        const weeks = Math.floor(diff / 604800000);
        return `${weeks}w ago`;
      }

      // Default: show date
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch (e) {
      return 'Unknown';
    }
  }

  // ===== HELPER: ESCAPE HTML =====
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // ===== HELPER: SHOW ERROR =====
  showError(message) {
    const main = document.querySelector('.main');
    const error = document.createElement('div');
    error.className = 'error-message';
    error.textContent = message;
    main.prepend(error);
  }

  // ===== LABEL FILTERING =====
  filterByLabel(label) {
    this.filteredByLabel = label;
    this.renderIssuesTab();
    this.renderPullRequestsTab();
    this.switchTab('issues');
  }
}

// Initialize on page load
const tracker = new SecurityTracker();
