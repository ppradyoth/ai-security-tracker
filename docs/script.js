/**
 * AI Security Tracker Dashboard
 * Client-side data loading and rendering
 */

class SecurityTracker {
    constructor() {
        this.data = null;
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
        this.renderRepositoriesTab();
        this.renderIssuesTab();
        this.renderLabelsTab();
    }

    renderOverviewTab() {
        const summary = this.data.summary;

        // Update metrics
        document.getElementById('lastUpdated').textContent = this.formatDate(this.data.generated_at);
        document.getElementById('totalRepos').textContent = summary.total_repos_tracked.toLocaleString();
        document.getElementById('totalIssues').textContent = summary.total_security_issues.toLocaleString();
        document.getElementById('openIssues').textContent = (summary.issues_by_state.open || 0).toLocaleString();
        document.getElementById('closedIssues').textContent = (summary.issues_by_state.closed || 0).toLocaleString();

        // Render issues by type
        const typeContainer = document.getElementById('issuesByType');
        typeContainer.innerHTML = '';

        for (const [type, count] of Object.entries(summary.issues_by_type)) {
            const card = document.createElement('div');
            card.className = 'type-card';
            card.innerHTML = `
                <div class="type-card-label">${type}</div>
                <div class="type-card-value">${count}</div>
            `;
            typeContainer.appendChild(card);
        }

        // Render top issues by engagement
        const engagementContainer = document.getElementById('topEngagement');
        engagementContainer.innerHTML = '';

        if (this.data.top_issues_by_engagement && this.data.top_issues_by_engagement.length > 0) {
            this.data.top_issues_by_engagement.slice(0, 10).forEach(issue => {
                const card = this.createIssueCard(issue);
                engagementContainer.appendChild(card);
            });
        } else {
            engagementContainer.innerHTML = '<div class="empty">No security issues found yet.</div>';
        }
    }

    renderRepositoriesTab() {
        const container = document.getElementById('repositoriesList');
        container.innerHTML = '';

        if (this.data.top_repos && this.data.top_repos.length > 0) {
            this.data.top_repos.forEach(repo => {
                const card = document.createElement('div');
                card.className = 'repo-card';
                card.innerHTML = `
                    <div class="repo-name">${repo.repo}</div>
                    <div class="repo-stat">
                        <span class="repo-stat-label">Security Issues</span>
                        <span class="repo-stat-value">${repo.issue_count}</span>
                    </div>
                    ${repo.issues && repo.issues.length > 0 ? `
                        <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border);">
                            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">Recent Issues:</div>
                            ${repo.issues.slice(0, 3).map(issue => `
                                <div style="font-size: 11px; margin: 2px 0;">
                                    <a href="${issue.url}" target="_blank" style="word-break: break-word;">#${issue.number} ${issue.title.substring(0, 30)}...</a>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                `;
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<div class="empty">No repositories data available.</div>';
        }
    }

    renderIssuesTab() {
        const container = document.getElementById('allIssues');
        container.innerHTML = '';

        if (this.data.top_issues_by_engagement && this.data.top_issues_by_engagement.length > 0) {
            this.data.top_issues_by_engagement.forEach(issue => {
                const card = this.createIssueCard(issue);
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<div class="empty">No security issues found.</div>';
        }
    }

    renderLabelsTab() {
        const container = document.getElementById('labelsList');
        container.innerHTML = '';

        if (this.data.labels_distribution && this.data.labels_distribution.length > 0) {
            this.data.labels_distribution.forEach(([label, count]) => {
                const card = document.createElement('div');
                card.className = 'label-card';
                card.innerHTML = `
                    <span class="label-name">${this.escapeHtml(label)}</span>
                    <span class="label-count">${count}</span>
                `;
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<div class="empty">No labels data available.</div>';
        }
    }

    createIssueCard(issue) {
        const card = document.createElement('div');
        const isCritical = issue.labels && (
            issue.labels.some(l => l.toLowerCase().includes('critical')) ||
            issue.signals?.has_vulnerability_label
        );

        card.className = `issue-card ${isCritical ? 'critical' : ''}`;

        const badges = [];
        if (issue.type) badges.push(issue.type);
        if (issue.state === 'open') badges.push('OPEN');
        else badges.push('CLOSED');

        const engagementStr = `${issue.comments || 0} comments, ${issue.reactions || 0} reactions`;

        card.innerHTML = `
            <div class="issue-header">
                <div class="issue-title">
                    <a href="${issue.url}" target="_blank">${this.escapeHtml(issue.title)}</a>
                </div>
                <div class="issue-badges">
                    ${badges.map(b => `<span class="badge ${b.toLowerCase()}">${b}</span>`).join('')}
                </div>
            </div>
            <div class="issue-meta">
                <div class="meta-item">
                    <span class="meta-label">Repo:</span>
                    <span>${this.escapeHtml(issue.repo)}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">#${issue.number}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Engagement:</span>
                    <span>${engagementStr}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Updated:</span>
                    <span>${this.formatDate(issue.updated_at)}</span>
                </div>
            </div>
        `;

        return card;
    }

    formatDate(isoString) {
        if (!isoString) return '—';
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diffMs = now - date;
            const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

            if (diffDays === 0) {
                return 'today';
            } else if (diffDays === 1) {
                return 'yesterday';
            } else if (diffDays < 7) {
                return `${diffDays} days ago`;
            } else if (diffDays < 30) {
                const weeks = Math.floor(diffDays / 7);
                return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
            } else {
                return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
            }
        } catch {
            return isoString;
        }
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    showError(message) {
        const main = document.querySelector('.main');
        main.innerHTML = `<div class="error">⚠️ ${message}</div>`;
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new SecurityTracker();
});
