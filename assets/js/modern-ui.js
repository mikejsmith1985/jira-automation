/* Modern UI JavaScript */

// Make functions globally accessible
window.openJiraBrowser = openJiraBrowser;
window.checkJiraLogin = checkJiraLogin;
window.saveJiraSettings = saveJiraSettings;
window.saveGitHubSettings = saveGitHubSettings;
window.testGitHubConnection = testGitHubConnection;
window.loadPODataFromUrl = loadPODataFromUrl;
window.loadPODataFromJson = loadPODataFromJson;
window.exportPOData = exportPOData;
window.scrapeMetrics = scrapeMetrics;
window.refreshMetrics = refreshMetrics;
window.runHygieneCheck = runHygieneCheck;
window.exportReport = exportReport;
window.syncNow = syncNow;
window.showSyncLog = showSyncLog;
window.toggleTeamMode = toggleTeamMode;
window.saveAppSettings = saveAppSettings;
window.openFeedbackModal = openFeedbackModal;
window.closeFeedbackModal = closeFeedbackModal;
window.captureScreenshot = captureScreenshot;
window.toggleVideoRecording = toggleVideoRecording;
window.submitFeedback = submitFeedback;

document.addEventListener('DOMContentLoaded', function() {
    console.log('[Waypoint] Initializing...');
    
    try {
        // Initialize theme
        initTheme();
        initTabNavigation();
        initBranchRules();
        initSaveRules();
        loadRulesFromConfig();
        initFeedback();
        
        // Load real data from APIs
        loadIntegrationStatus();
        loadAutomationRules();
        loadDashboardData();
        
        console.log('[Waypoint] Initialization complete');
    } catch (error) {
        console.error('[Waypoint] Initialization error:', error);
    }
});

/* ============================================================================
   Theme Management
   ============================================================================ */

function initTheme() {
    const toggle = document.getElementById('themeToggle');
    const html = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Set initial theme
    html.setAttribute('data-theme', savedTheme);
    
    // Toggle handler
    toggle.addEventListener('click', () => {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

/* ============================================================================
   Tab Navigation
   ============================================================================ */

function initTabNavigation() {
    const tabs = document.querySelectorAll('.nav-item');
    const contents = document.querySelectorAll('.tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const tabName = tab.dataset.tab;
            
            // Remove active from all
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            
            // Add active to clicked
            tab.classList.add('active');
            const targetTab = document.getElementById(tabName);
            if (targetTab) {
                targetTab.classList.add('active');
            }
        });
    });
}

/* ============================================================================
   Branch Rules Management
   ============================================================================ */

function initBranchRules() {
    const addBtn = document.getElementById('add-rule');
    if (addBtn) {
        addBtn.addEventListener('click', addBranchRule);
    }
}

function addBranchRule() {
    const container = document.getElementById('branch-rules');
    if (container) {
        const branchRule = createBranchRuleElement();
        container.appendChild(branchRule);
    }
}

function createBranchRuleElement(data = {}) {
    const div = document.createElement('div');
    div.className = 'branch-rule';
    
    const branchName = data.branch || 'NEW';
    const status = data.set_status || '';
    const label = data.add_label || '';
    const comment = data.add_comment !== false;
    
    div.innerHTML = `
        <div class="branch-rule-header">
            <input type="text" class="input-field branch-name-input" value="${branchName}" placeholder="e.g., DEV, INT, PVS">
            <button class="branch-rule-delete">Delete</button>
        </div>
        <div class="form-group">
            <label>Move to Status:</label>
            <input type="text" class="input-field status-input" value="${status}" placeholder="e.g., Ready for QA">
        </div>
        <div class="form-group">
            <label>Add Label:</label>
            <input type="text" class="input-field label-input" value="${label}" placeholder="e.g., merged-int">
        </div>
        <div class="form-group checkbox">
            <input type="checkbox" class="toggle-input comment-input" ${comment ? 'checked' : ''}>
            <label>Add Comment</label>
        </div>
    `;
    
    // Delete handler
    const deleteBtn = div.querySelector('.branch-rule-delete');
    deleteBtn.addEventListener('click', () => div.remove());
    
    return div;
}

function getBranchRulesFromUI() {
    const rules = [];
    const ruleElements = document.querySelectorAll('.branch-rule');
    
    ruleElements.forEach(el => {
        const branchInput = el.querySelector('.branch-name-input');
        const statusInput = el.querySelector('.status-input');
        const labelInput = el.querySelector('.label-input');
        const commentInput = el.querySelector('.comment-input');
        
        if (branchInput.value.trim()) {
            rules.push({
                branch: branchInput.value.trim().toUpperCase(),
                set_status: statusInput.value || '',
                add_label: labelInput.value || '',
                add_comment: commentInput.checked,
                comment_template: ''
            });
        }
    });
    
    return rules;
}

/* ============================================================================
   Configuration Management
   ============================================================================ */

async function loadRulesFromConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        if (config.automation) {
            const auto = config.automation;
            
            // Load PR Opened rules
            if (auto.pr_opened) {
                document.getElementById('pr-opened-enabled').checked = auto.pr_opened.enabled !== false;
                document.getElementById('pr-opened-status').value = auto.pr_opened.set_status || '';
                document.getElementById('pr-opened-label').value = auto.pr_opened.add_label || '';
                document.getElementById('pr-opened-comment').checked = auto.pr_opened.add_comment !== false;
                document.getElementById('pr-opened-comment-text').value = auto.pr_opened.comment_template || '';
            }
            
            // Load PR Closed rules
            if (auto.pr_closed) {
                document.getElementById('pr-closed-enabled').checked = auto.pr_closed.enabled !== false;
                document.getElementById('pr-closed-label').value = auto.pr_closed.add_label || '';
                document.getElementById('pr-closed-comment').checked = auto.pr_closed.add_comment !== false;
            }
            
            // Load branch rules
            if (auto.pr_merged && auto.pr_merged.branch_rules) {
                const container = document.getElementById('branch-rules');
                if (container) {
                    container.innerHTML = '';
                    auto.pr_merged.branch_rules.forEach(rule => {
                        if (rule.branch !== 'default') {
                            container.appendChild(createBranchRuleElement(rule));
                        }
                    });
                }
            }
        }
    } catch (error) {
        console.error('Error loading config:', error);
        showNotification('Error loading configuration', 'error');
    }
}

function initSaveRules() {
    const saveBtn = document.getElementById('save-rules');
    const resetBtn = document.getElementById('reset-rules');
    
    saveBtn.addEventListener('click', saveRules);
    resetBtn.addEventListener('click', loadRulesFromConfig);
}

async function saveRules() {
    try {
        const automation = {
            pr_opened: {
                enabled: document.getElementById('pr-opened-enabled').checked,
                set_status: document.getElementById('pr-opened-status').value,
                add_label: document.getElementById('pr-opened-label').value,
                add_comment: document.getElementById('pr-opened-comment').checked,
                comment_template: document.getElementById('pr-opened-comment-text').value,
                update_pr_field: true
            },
            pr_updated: {
                enabled: true,
                add_comment: true,
                comment_template: '🔄 Pull Request updated: {pr_url}',
                update_pr_field: false,
                add_label: '',
                set_status: ''
            },
            pr_merged: {
                enabled: document.getElementById('pr-merged-enabled').checked,
                branch_rules: getBranchRulesFromUI().concat([{
                    branch: 'default',
                    add_comment: true,
                    comment_template: '✅ Pull Request merged: {pr_url}',
                    set_status: '',
                    add_label: 'merged'
                }])
            },
            pr_closed: {
                enabled: document.getElementById('pr-closed-enabled').checked,
                add_comment: document.getElementById('pr-closed-comment').checked,
                comment_template: '❌ Pull Request closed without merging: {pr_url}',
                update_pr_field: false,
                add_label: document.getElementById('pr-closed-label').value,
                set_status: ''
            }
        };
        
        // Get current config and merge
        const response = await fetch('/api/config');
        const config = await response.json();
        config.automation = automation;
        
        // Save
        const saveResponse = await fetch('/api/save-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        if (saveResponse.ok) {
            showNotification('✅ Rules saved successfully!');
        } else {
            showNotification('❌ Failed to save rules', 'error');
        }
    } catch (error) {
        console.error('Error saving rules:', error);
        showNotification('❌ Error saving rules', 'error');
    }
}

/* ============================================================================
   Notifications
   ============================================================================ */

function showNotification(message, type = 'success') {
    const notif = document.getElementById('notification');
    notif.textContent = message;
    notif.style.background = type === 'error' ? '#de350b' : '#00875a';
    notif.classList.add('show');
    
    setTimeout(() => {
        notif.classList.remove('show');
    }, 3000);
}

/* ============================================================================
   Persona Views - PO Team Mode Toggle
   ============================================================================ */

function toggleTeamMode(mode) {
    const scrumMetrics = document.getElementById('scrum-metrics');
    const kanbanMetrics = document.getElementById('kanban-metrics');
    
    if (mode === 'scrum') {
        scrumMetrics.style.display = 'block';
        kanbanMetrics.style.display = 'none';
    } else {
        scrumMetrics.style.display = 'none';
        kanbanMetrics.style.display = 'block';
    }
    
    // Save preference
    localStorage.setItem('teamMode', mode);
}

// Initialize team mode on load
document.addEventListener('DOMContentLoaded', function() {
    const savedMode = localStorage.getItem('teamMode') || 'kanban';
    const radio = document.querySelector(`input[name="team-mode"][value="${savedMode}"]`);
    if (radio) {
        radio.checked = true;
        toggleTeamMode(savedMode);
    }
});

/* ============================================================================
   Feedback Modal
   ============================================================================ */

function initFeedback() {
    const feedbackBtn = document.getElementById('feedbackBtn');
    if (feedbackBtn) {
        feedbackBtn.addEventListener('click', openFeedbackModal);
    }
}

function openFeedbackModal() {
    const modal = document.getElementById('feedback-modal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeFeedbackModal() {
    const modal = document.getElementById('feedback-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function captureScreenshot() {
    showNotification('Screenshot capture coming soon');
}

function toggleVideoRecording() {
    showNotification('Video recording coming soon');
}

function submitFeedback() {
    const title = document.getElementById('feedback-title').value;
    const description = document.getElementById('feedback-description').value;
    
    if (!title || !description) {
        showNotification('❌ Please fill in title and description', 'error');
        return;
    }
    
    showNotification('✅ Feedback submitted!');
    closeFeedbackModal();
    
    // Clear form
    document.getElementById('feedback-title').value = '';
    document.getElementById('feedback-description').value = '';
}

/* ============================================================================
   Integration Status - Real Data from API
   ============================================================================ */

async function loadIntegrationStatus() {
    console.log('[Waypoint] Loading integration status...');
    try {
        const response = await fetch('/api/integrations/status');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const status = await response.json();
        console.log('[Waypoint] Integration status:', status);
        
        // Update GitHub status
        const githubBadge = document.getElementById('github-status-badge');
        const githubInfo = document.getElementById('github-org-info');
        if (githubBadge) {
            if (status.github && status.github.configured) {
                githubBadge.textContent = 'Connected';
                githubBadge.className = 'badge badge-success';
                if (githubInfo) {
                    githubInfo.textContent = `Organization: ${status.github.organization || 'Not set'}`;
                }
            } else {
                githubBadge.textContent = 'Not Configured';
                githubBadge.className = 'badge badge-warning';
                if (githubInfo) {
                    githubInfo.textContent = 'Add your GitHub token below';
                }
            }
        }
        
        // Update Jira status - REAL Selenium browser state
        const jiraBadge = document.getElementById('jira-status-badge');
        const jiraInfo = document.getElementById('jira-url-info');
        const jiraBrowserStatus = document.getElementById('jira-browser-status');
        if (jiraBadge) {
            const jiraStatus = status.jira && status.jira.status || 'Not Configured';
            
            if (status.jira && status.jira.logged_in) {
                jiraBadge.textContent = 'Connected';
                jiraBadge.className = 'badge badge-success';
            } else if (status.jira && status.jira.browser_open) {
                jiraBadge.textContent = 'Browser Open';
                jiraBadge.className = 'badge badge-warning';
            } else if (status.jira && status.jira.configured) {
                jiraBadge.textContent = 'URL Set';
                jiraBadge.className = 'badge badge-secondary';
            } else {
                jiraBadge.textContent = 'Not Configured';
                jiraBadge.className = 'badge badge-warning';
            }
            
            if (jiraInfo && status.jira) {
                jiraInfo.textContent = status.jira.base_url ? `URL: ${status.jira.base_url}` : 'No URL configured';
            }
            if (jiraBrowserStatus && status.jira) {
                if (status.jira.logged_in) {
                    jiraBrowserStatus.textContent = '✅ Logged in and ready';
                } else if (status.jira.browser_open) {
                    jiraBrowserStatus.textContent = '⚠️ Browser open - please login';
                } else {
                    jiraBrowserStatus.textContent = '🔌 Click "Open Jira Browser" to start';
                }
            }
        }
        
        // Update Feedback status
        const feedbackBadge = document.getElementById('feedback-status-badge');
        const feedbackInfo = document.getElementById('feedback-repo-info');
        if (feedbackBadge) {
            if (status.feedback.configured) {
                feedbackBadge.textContent = 'Configured';
                feedbackBadge.className = 'badge badge-success';
                if (feedbackInfo) {
                    feedbackInfo.textContent = `Repo: ${status.feedback.repo}`;
                }
            } else {
                feedbackBadge.textContent = 'Not Configured';
                feedbackBadge.className = 'badge badge-warning';
                if (feedbackInfo) {
                    feedbackInfo.textContent = 'Configure via the bug button';
                }
            }
        }
        
        // Update dashboard integration status
        updateDashboardIntegrationStatus(status);
        
        // Pre-fill integration form fields
        prefillIntegrationForms(status);
        
        console.log('[Waypoint] Integration status loaded successfully');
    } catch (error) {
        console.error('[Waypoint] Error loading integration status:', error);
        // Set badges to error state
        const badges = ['github-status-badge', 'jira-status-badge', 'feedback-status-badge'];
        badges.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = 'Error';
                el.className = 'badge badge-warning';
            }
        });
    }
}

function updateDashboardIntegrationStatus(status) {
    const container = document.getElementById('dashboard-integration-status');
    if (!container) return;
    
    let html = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">';
    
    // GitHub
    html += `<div class="stat-card" style="text-align: center;">
        <span class="badge ${status.github.configured ? 'badge-success' : 'badge-warning'}" style="font-size: 12px;">
            ${status.github.configured ? '✓ GitHub Connected' : '⚠ GitHub Not Set'}
        </span>
    </div>`;
    
    // Jira
    html += `<div class="stat-card" style="text-align: center;">
        <span class="badge ${status.jira.configured ? 'badge-success' : 'badge-warning'}" style="font-size: 12px;">
            ${status.jira.configured ? '✓ Jira Configured' : '⚠ Jira Not Set'}
        </span>
    </div>`;
    
    // Feedback
    html += `<div class="stat-card" style="text-align: center;">
        <span class="badge ${status.feedback.configured ? 'badge-success' : 'badge-warning'}" style="font-size: 12px;">
            ${status.feedback.configured ? '✓ Feedback Ready' : '⚠ Feedback Not Set'}
        </span>
    </div>`;
    
    html += '</div>';
    container.innerHTML = html;
}

function prefillIntegrationForms(status) {
    const githubOrgInput = document.getElementById('github-org-input');
    const jiraUrlInput = document.getElementById('jira-url-input');
    const jiraProjectsInput = document.getElementById('jira-projects-input');
    
    if (githubOrgInput && status.github.organization) {
        githubOrgInput.value = status.github.organization;
    }
    if (jiraUrlInput && status.jira.base_url && !status.jira.base_url.includes('your-company')) {
        jiraUrlInput.value = status.jira.base_url;
    }
    if (jiraProjectsInput && status.jira.project_keys) {
        jiraProjectsInput.value = status.jira.project_keys.join(', ');
    }
}

/* ============================================================================
   Automation Rules - Real Data from API
   ============================================================================ */

async function loadAutomationRules() {
    try {
        const response = await fetch('/api/automation/rules');
        const data = await response.json();
        
        // Update the stat card
        const activeRulesEl = document.getElementById('stat-active-rules');
        if (activeRulesEl) {
            activeRulesEl.textContent = data.active_count || 0;
        }
        
        // Update the dev tab automation rules display
        const devRulesContainer = document.getElementById('dev-automation-rules');
        if (devRulesContainer) {
            let html = '';
            const rules = data.rules;
            
            if (rules.pr_opened && rules.pr_opened.enabled) {
                html += `<div class="integration-item">
                    <div class="integration-info">
                        <h4>PR Opened → ${rules.pr_opened.set_status || 'Add Comment'}</h4>
                        <p class="text-secondary">${rules.pr_opened.description}</p>
                    </div>
                    <span class="badge badge-success">Active</span>
                </div>`;
            }
            
            if (rules.pr_merged && rules.pr_merged.enabled) {
                const branchCount = rules.pr_merged.branch_rules ? rules.pr_merged.branch_rules.length : 0;
                html += `<div class="integration-item">
                    <div class="integration-info">
                        <h4>PR Merged → Branch-Specific Rules</h4>
                        <p class="text-secondary">${branchCount} branch rules configured</p>
                    </div>
                    <span class="badge badge-success">Active</span>
                </div>`;
            }
            
            if (rules.pr_closed && rules.pr_closed.enabled) {
                html += `<div class="integration-item">
                    <div class="integration-info">
                        <h4>PR Closed → ${rules.pr_closed.add_label || 'Add Comment'}</h4>
                        <p class="text-secondary">${rules.pr_closed.description}</p>
                    </div>
                    <span class="badge badge-success">Active</span>
                </div>`;
            }
            
            if (rules.pr_updated && rules.pr_updated.enabled) {
                html += `<div class="integration-item">
                    <div class="integration-info">
                        <h4>PR Updated → Add Comment</h4>
                        <p class="text-secondary">${rules.pr_updated.description}</p>
                    </div>
                    <span class="badge badge-success">Active</span>
                </div>`;
            }
            
            if (!html) {
                html = '<p class="text-secondary">No automation rules are currently active. Configure rules in the Automation tab.</p>';
            }
            
            devRulesContainer.innerHTML = html;
        }
        
    } catch (error) {
        console.error('Error loading automation rules:', error);
    }
}

/* ============================================================================
   Dashboard Data
   ============================================================================ */

async function loadDashboardData() {
    // For now, set to 0 since we don't have sync history yet
    const prsSynced = document.getElementById('stat-prs-synced');
    const ticketsUpdated = document.getElementById('stat-tickets-updated');
    
    if (prsSynced) prsSynced.textContent = '0';
    if (ticketsUpdated) ticketsUpdated.textContent = '0';
}

/* ============================================================================
   Integration Settings Actions
   ============================================================================ */

async function testGitHubConnection() {
    const token = document.getElementById('github-token-input').value;
    const resultEl = document.getElementById('github-test-result');
    
    if (!token) {
        resultEl.innerHTML = '<span style="color: #de350b;">Please enter a token first</span>';
        return;
    }
    
    resultEl.innerHTML = '<span>Testing connection...</span>';
    
    try {
        const response = await fetch('/api/integrations/test-github', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });
        const result = await response.json();
        
        if (result.success) {
            resultEl.innerHTML = `<span style="color: #00875a;">✓ Connected as ${result.user}</span>`;
        } else {
            resultEl.innerHTML = `<span style="color: #de350b;">✗ ${result.error}</span>`;
        }
    } catch (error) {
        resultEl.innerHTML = `<span style="color: #de350b;">✗ Connection failed: ${error.message}</span>`;
    }
}

async function saveGitHubSettings() {
    const token = document.getElementById('github-token-input').value;
    const org = document.getElementById('github-org-input').value;
    
    try {
        const response = await fetch('/api/integrations/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                github: {
                    api_token: token,
                    organization: org
                }
            })
        });
        const result = await response.json();
        
        if (result.success) {
            showNotification('✓ GitHub settings saved');
            loadIntegrationStatus(); // Refresh status
        } else {
            showNotification('✗ Failed to save: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('✗ Error saving settings', 'error');
    }
}

async function saveJiraSettings() {
    const url = document.getElementById('jira-url-input').value;
    const projects = document.getElementById('jira-projects-input').value;
    
    const projectKeys = projects.split(',').map(p => p.trim()).filter(p => p);
    
    try {
        const response = await fetch('/api/integrations/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jira: {
                    base_url: url,
                    project_keys: projectKeys
                }
            })
        });
        const result = await response.json();
        
        if (result.success) {
            showNotification('✓ Jira settings saved');
            loadIntegrationStatus(); // Refresh status
        } else {
            showNotification('✗ Failed to save: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('✗ Error saving settings', 'error');
    }
}

/* ============================================================================
   Sync Actions
   ============================================================================ */

async function initBrowser() {
    const statusEl = document.getElementById('sync-status');
    statusEl.innerHTML = '<span>Opening browser...</span>';
    
    try {
        const response = await fetch('/api/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const result = await response.json();
        
        if (result.success) {
            statusEl.innerHTML = '<span style="color: #00875a;">✓ ' + result.message + '</span>';
        } else {
            statusEl.innerHTML = '<span style="color: #de350b;">✗ ' + result.error + '</span>';
        }
    } catch (error) {
        statusEl.innerHTML = '<span style="color: #de350b;">✗ Failed to open browser</span>';
    }
}

async function syncNow() {
    const statusEl = document.getElementById('sync-status');
    statusEl.innerHTML = '<span>Syncing...</span>';
    
    try {
        const response = await fetch('/api/sync-now', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const result = await response.json();
        
        if (result.success) {
            statusEl.innerHTML = '<span style="color: #00875a;">✓ ' + result.message + '</span>';
            loadDashboardData(); // Refresh stats
        } else {
            statusEl.innerHTML = '<span style="color: #de350b;">✗ ' + result.error + '</span>';
        }
    } catch (error) {
        statusEl.innerHTML = '<span style="color: #de350b;">✗ Sync failed</span>';
    }
}

function showSyncLog() {
    showNotification('Sync log viewer coming soon');
}

function saveAppSettings() {
    showNotification('Settings saved');
}

/* ============================================================================
   Selenium Browser Controls
   ============================================================================ */

async function openJiraBrowser() {
    console.log('[Waypoint] openJiraBrowser() called');
    const url = document.getElementById('jira-url-input').value;
    console.log('[Waypoint] Jira URL:', url);
    const resultEl = document.getElementById('jira-action-result') || document.getElementById('sync-status');
    
    if (resultEl) resultEl.innerHTML = '<span>Opening Jira browser...</span>';
    
    try {
        console.log('[Waypoint] Sending request to /api/selenium/open-jira');
        const response = await fetch('/api/selenium/open-jira', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jiraUrl: url })
        });
        const result = await response.json();
        console.log('[Waypoint] Response:', result);
        
        if (result.success) {
            if (resultEl) resultEl.innerHTML = `<span style="color: #00875a;">✓ ${result.message}</span>`;
            showNotification('Browser opened - please login to Jira');
            // Refresh status after a delay
            setTimeout(loadIntegrationStatus, 2000);
        } else {
            if (resultEl) resultEl.innerHTML = `<span style="color: #de350b;">✗ ${result.error}</span>`;
            showNotification(result.error, 'error');
        }
    } catch (error) {
        console.error('[Waypoint] Error opening browser:', error);
        if (resultEl) resultEl.innerHTML = `<span style="color: #de350b;">✗ Failed to open browser</span>`;
        showNotification('Failed to open browser', 'error');
    }
}

async function checkJiraLogin() {
    const resultEl = document.getElementById('jira-action-result');
    if (resultEl) resultEl.innerHTML = '<span>Checking login status...</span>';
    
    try {
        const response = await fetch('/api/selenium/check-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const result = await response.json();
        
        if (result.logged_in) {
            if (resultEl) resultEl.innerHTML = `<span style="color: #00875a;">✓ Logged in${result.user ? ' as ' + result.user : ''}</span>`;
            showNotification('Jira login confirmed!');
        } else if (result.success) {
            if (resultEl) resultEl.innerHTML = `<span style="color: #FF991F;">⚠ Not logged in - please login in the browser window</span>`;
        } else {
            if (resultEl) resultEl.innerHTML = `<span style="color: #de350b;">✗ ${result.error}</span>`;
        }
        loadIntegrationStatus();
    } catch (error) {
        if (resultEl) resultEl.innerHTML = `<span style="color: #de350b;">✗ Check failed</span>`;
    }
}

/* ============================================================================
   PO Data Functions
   ============================================================================ */

async function loadPODataFromUrl() {
    const url = document.getElementById('po-data-url').value;
    const resultEl = document.getElementById('po-load-result');
    
    if (!url) {
        resultEl.innerHTML = '<span style="color: #de350b;">Please enter a URL</span>';
        return;
    }
    
    resultEl.innerHTML = '<span>Loading data from URL...</span>';
    
    try {
        const response = await fetch('/api/po/load-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_type: 'url', url: url })
        });
        const result = await response.json();
        
        if (result.success) {
            resultEl.innerHTML = `<span style="color: #00875a;">✓ ${result.message}</span>`;
            displayPOData(result.data);
            showNotification('Data loaded successfully');
        } else {
            resultEl.innerHTML = `<span style="color: #de350b;">✗ ${result.error}</span>`;
        }
    } catch (error) {
        resultEl.innerHTML = `<span style="color: #de350b;">✗ Failed to load: ${error.message}</span>`;
    }
}

async function loadPODataFromJson() {
    const jsonText = document.getElementById('po-data-json').value;
    const resultEl = document.getElementById('po-load-result');
    
    if (!jsonText) {
        resultEl.innerHTML = '<span style="color: #de350b;">Please paste JSON data</span>';
        return;
    }
    
    let data;
    try {
        data = JSON.parse(jsonText);
    } catch (e) {
        resultEl.innerHTML = '<span style="color: #de350b;">Invalid JSON format</span>';
        return;
    }
    
    resultEl.innerHTML = '<span>Processing data...</span>';
    
    try {
        const response = await fetch('/api/po/load-data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_type: 'data', data: data })
        });
        const result = await response.json();
        
        if (result.success) {
            resultEl.innerHTML = `<span style="color: #00875a;">✓ ${result.message}</span>`;
            displayPOData(result.data);
            showNotification('Data loaded successfully');
        } else {
            resultEl.innerHTML = `<span style="color: #de350b;">✗ ${result.error}</span>`;
        }
    } catch (error) {
        resultEl.innerHTML = `<span style="color: #de350b;">✗ Failed to load: ${error.message}</span>`;
    }
}

function displayPOData(data) {
    const container = document.getElementById('po-feature-tree');
    if (!container || !data) return;
    
    const features = data.features || [];
    
    if (features.length === 0) {
        container.innerHTML = '<p class="text-secondary">No features found in data</p>';
        return;
    }
    
    let html = '';
    features.forEach(feature => {
        const children = feature.children || [];
        html += `
            <div class="integration-item" style="border-left: 4px solid #0052CC;">
                <div class="integration-info">
                    <h4>${feature.key || 'Feature'}: ${feature.summary || 'Unnamed'}</h4>
                    <p class="text-secondary">${children.length} child issues</p>
                </div>
                <span class="badge badge-secondary">${feature.status || 'Unknown'}</span>
            </div>
        `;
        
        children.forEach(child => {
            html += `
                <div class="integration-item" style="margin-left: 24px; border-left: 2px solid #ddd;">
                    <div class="integration-info">
                        <h4 style="font-size: 13px;">${child.key}: ${child.summary || 'Unnamed'}</h4>
                        <p class="text-secondary" style="font-size: 11px;">${child.type || 'Issue'}</p>
                    </div>
                    <span class="badge ${child.status === 'Done' ? 'badge-success' : 'badge-secondary'}" style="font-size: 10px;">${child.status || 'Unknown'}</span>
                </div>
            `;
        });
    });
    
    container.innerHTML = html;
    
    // Update metrics
    updatePOMetrics(data);
}

function updatePOMetrics(data) {
    const features = data.features || [];
    const allChildren = features.flatMap(f => f.children || []);
    
    const wip = allChildren.filter(c => c.status === 'In Progress').length;
    const blocked = allChildren.filter(c => c.status === 'Blocked').length;
    const done = allChildren.filter(c => c.status === 'Done').length;
    
    const wipEl = document.getElementById('po-wip');
    const blockedEl = document.getElementById('po-blocked');
    const throughputEl = document.getElementById('po-throughput');
    
    if (wipEl) wipEl.textContent = wip;
    if (blockedEl) blockedEl.textContent = blocked;
    if (throughputEl) throughputEl.textContent = done;
}

function exportPOData() {
    showNotification('Export coming soon');
}

/* ============================================================================
   SM Metrics Functions
   ============================================================================ */

async function scrapeMetrics() {
    const jql = document.getElementById('sm-jql-query').value;
    const boardUrl = document.getElementById('sm-board-url').value;
    const resultEl = document.getElementById('sm-scrape-result');
    
    if (!jql && !boardUrl) {
        resultEl.innerHTML = '<span style="color: #de350b;">Please enter a JQL query or board URL</span>';
        return;
    }
    
    resultEl.innerHTML = '<span>Scraping data from Jira...</span>';
    
    try {
        const response = await fetch('/api/sm/scrape-metrics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jql: jql, board_url: boardUrl })
        });
        const result = await response.json();
        
        if (result.success) {
            resultEl.innerHTML = `<span style="color: #00875a;">✓ ${result.message}</span>`;
            displaySMMetrics(result.metrics);
            showNotification('Metrics scraped successfully');
        } else {
            resultEl.innerHTML = `<span style="color: #de350b;">✗ ${result.error}</span>`;
            showNotification(result.error, 'error');
        }
    } catch (error) {
        resultEl.innerHTML = `<span style="color: #de350b;">✗ Failed to scrape: ${error.message}</span>`;
    }
}

function displaySMMetrics(metrics) {
    // Update metric cards
    const totalEl = document.getElementById('sm-total-issues');
    if (totalEl) totalEl.textContent = metrics.total_issues || 0;
    
    // Display scraped issues
    const listContainer = document.getElementById('sm-issues-list');
    if (listContainer && metrics.issues_scraped) {
        let html = '';
        metrics.issues_scraped.forEach(issue => {
            html += `
                <div class="integration-item">
                    <div class="integration-info">
                        <h4>${issue.key}</h4>
                        <p class="text-secondary">${issue.url || ''}</p>
                    </div>
                </div>
            `;
        });
        
        if (metrics.total_issues > metrics.issues_scraped.length) {
            html += `<p class="text-secondary">... and ${metrics.total_issues - metrics.issues_scraped.length} more</p>`;
        }
        
        listContainer.innerHTML = html || '<p class="text-secondary">No issues found</p>';
    }
}

function refreshMetrics() {
    loadIntegrationStatus();
    showNotification('Status refreshed');
}

function runHygieneCheck() {
    showNotification('Hygiene check requires scraped data first');
}

function exportReport() {
    showNotification('Export report coming soon');
}
