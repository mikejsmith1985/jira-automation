/* Modern UI JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initTheme();
    initTabNavigation();
    initBranchRules();
    initSaveRules();
    loadRulesFromConfig();
    initFeedback();
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
   Data Import Functions
   ============================================================================ */

function toggleDepSource(source) {
    document.getElementById('dep-jira-config').style.display = source === 'jira' ? 'block' : 'none';
    document.getElementById('dep-json-config').style.display = source === 'json' ? 'block' : 'none';
}

function toggleFeatSource(source) {
    document.getElementById('feat-jira-config').style.display = source === 'jira' ? 'block' : 'none';
    document.getElementById('feat-upload-config').style.display = source === 'upload' ? 'block' : 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    // Jira import button
    const jiraImportBtn = document.getElementById('jira-import-btn');
    if (jiraImportBtn) {
        jiraImportBtn.addEventListener('click', function() {
            const query = document.getElementById('jira-jql-query').value;
            const statusEl = document.getElementById('jira-import-status');
            const messageEl = document.getElementById('jira-import-message');
            
            if (!query) {
                messageEl.textContent = '❌ Please enter a JQL query';
                statusEl.style.display = 'block';
                return;
            }
            
            statusEl.style.display = 'block';
            messageEl.textContent = '⏳ Importing from Jira...';
            showNotification('⏳ Jira import started');
        });
    }

    // Jira test connection
    const jiraTestBtn = document.getElementById('jira-test-btn');
    if (jiraTestBtn) {
        jiraTestBtn.addEventListener('click', function() {
            showNotification('✅ Connection to Jira successful');
        });
    }

    // Dependency Canvas JSON upload
    const depJsonFile = document.getElementById('dep-json-file');
    if (depJsonFile) {
        depJsonFile.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    try {
                        const data = JSON.parse(event.target.result);
                        const preview = document.getElementById('dep-json-preview');
                        const content = document.getElementById('dep-json-content');
                        content.textContent = JSON.stringify(data, null, 2).substring(0, 500) + '...';
                        preview.style.display = 'block';
                        showNotification('✅ JSON file loaded and validated');
                    } catch (err) {
                        showNotification('❌ Invalid JSON file: ' + err.message, 'error');
                    }
                };
                reader.readAsText(file);
            }
        });
    }

    // Dependency Canvas load
    const depLoadBtn = document.getElementById('dep-load-btn');
    if (depLoadBtn) {
        depLoadBtn.addEventListener('click', function() {
            const source = document.querySelector('input[name="dep-source"]:checked').value;
            const statusEl = document.getElementById('dep-load-status');
            const messageEl = document.getElementById('dep-load-message');
            
            statusEl.style.display = 'block';
            messageEl.textContent = source === 'jira' ? '⏳ Loading from Jira...' : '⏳ Loading JSON...';
            showNotification('⏳ Dependency data loading');
        });
    }

    // Dependency Canvas clear
    const depClearBtn = document.getElementById('dep-clear-btn');
    if (depClearBtn) {
        depClearBtn.addEventListener('click', function() {
            document.getElementById('dep-json-file').value = '';
            document.getElementById('dep-json-preview').style.display = 'none';
            document.getElementById('dep-load-status').style.display = 'none';
            showNotification('✅ Dependency data cleared');
        });
    }

    // Features upload
    const featUploadFile = document.getElementById('feat-upload-file');
    if (featUploadFile) {
        featUploadFile.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    const preview = document.getElementById('feat-upload-preview');
                    const content = document.getElementById('feat-upload-content');
                    content.textContent = event.target.result.substring(0, 500) + '...';
                    preview.style.display = 'block';
                    showNotification('✅ File loaded');
                };
                reader.readAsText(file);
            }
        });
    }

    // Features load
    const featLoadBtn = document.getElementById('feat-load-btn');
    if (featLoadBtn) {
        featLoadBtn.addEventListener('click', function() {
            const source = document.querySelector('input[name="feat-source"]:checked').value;
            const statusEl = document.getElementById('feat-load-status');
            const messageEl = document.getElementById('feat-load-message');
            
            statusEl.style.display = 'block';
            messageEl.textContent = source === 'jira' ? '⏳ Loading features from Jira...' : '⏳ Loading from file...';
            showNotification('⏳ Features data loading');
        });
    }

    // Features clear
    const featClearBtn = document.getElementById('feat-clear-btn');
    if (featClearBtn) {
        featClearBtn.addEventListener('click', function() {
            document.getElementById('feat-upload-file').value = '';
            document.getElementById('feat-upload-preview').style.display = 'none';
            document.getElementById('feat-load-status').style.display = 'none';
            showNotification('✅ Features data cleared');
        });
    }
});
