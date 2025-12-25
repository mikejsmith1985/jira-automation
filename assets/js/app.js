/* Waypoint - Modern JavaScript */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initNavigation();
    initForms();
});

// Theme Toggle
function initTheme() {
    const toggle = document.getElementById('themeToggle');
    const theme = localStorage.getItem('theme') || 'light';
    
    document.documentElement.setAttribute('data-theme', theme);
    
    toggle.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
    });
}

// Navigation
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = item.dataset.tab;
            
            // Update active nav
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            
            // Update active tab
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            const tabEl = document.getElementById(tab);
            if (tabEl) {
                tabEl.classList.add('active');
                
                // Update header
                const titles = {
                    dashboard: 'Dashboard',
                    rules: 'Automation Rules',
                    integrations: 'Integrations',
                    settings: 'Settings'
                };
                document.getElementById('page-title').textContent = titles[tab] || tab;
            }
        });
    });
}

// Forms
function initForms() {
    const saveBtn = document.getElementById('save-rules');
    const resetBtn = document.getElementById('reset-rules');
    const addRuleBtn = document.getElementById('add-rule');
    
    if (saveBtn) saveBtn.addEventListener('click', saveRules);
    if (resetBtn) resetBtn.addEventListener('click', loadRules);
    if (addRuleBtn) addRuleBtn.addEventListener('click', addBranchRule);
    
    loadRules();
}

function addBranchRule() {
    const container = document.getElementById('branch-rules');
    if (!container) return;
    
    const rule = document.createElement('div');
    rule.className = 'branch-rule';
    rule.innerHTML = `
        <input type="text" placeholder="e.g., DEV" value="">
        <div style="display: grid; gap: 8px;">
            <input type="text" placeholder="Move to Status" value="">
            <input type="text" placeholder="Add Label" value="">
        </div>
        <button class="btn btn-secondary" style="width: fit-content;">Delete</button>
    `;
    
    rule.querySelector('.btn').addEventListener('click', () => rule.remove());
    container.appendChild(rule);
}

async function loadRules() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        if (config.automation) {
            const auto = config.automation;
            
            // Load PR Opened
            if (auto.pr_opened) {
                document.getElementById('pr-opened-status').value = auto.pr_opened.set_status || '';
                document.getElementById('pr-opened-label').value = auto.pr_opened.add_label || '';
                document.getElementById('pr-opened-comment').checked = auto.pr_opened.add_comment !== false;
                document.getElementById('pr-opened-template').value = auto.pr_opened.comment_template || '';
            }
            
            // Load PR Closed
            if (auto.pr_closed) {
                document.getElementById('pr-closed-label').value = auto.pr_closed.add_label || '';
                document.getElementById('pr-closed-comment').checked = auto.pr_closed.add_comment !== false;
            }
            
            // Load branch rules
            const container = document.getElementById('branch-rules');
            if (container && auto.pr_merged?.branch_rules) {
                container.innerHTML = '';
                auto.pr_merged.branch_rules.forEach(rule => {
                    if (rule.branch !== 'default') {
                        const el = document.createElement('div');
                        el.className = 'branch-rule';
                        el.innerHTML = `
                            <input type="text" value="${rule.branch}" placeholder="e.g., DEV">
                            <div style="display: grid; gap: 8px;">
                                <input type="text" value="${rule.set_status || ''}" placeholder="Move to Status">
                                <input type="text" value="${rule.add_label || ''}" placeholder="Add Label">
                            </div>
                            <button class="btn btn-secondary" style="width: fit-content;">Delete</button>
                        `;
                        el.querySelector('.btn').addEventListener('click', () => el.remove());
                        container.appendChild(el);
                    }
                });
            }
        }
    } catch (error) {
        console.error('Error loading rules:', error);
    }
}

async function saveRules() {
    try {
        const branches = [];
        document.querySelectorAll('#branch-rules .branch-rule').forEach(el => {
            const inputs = el.querySelectorAll('input[type="text"]');
            const branch = inputs[0].value.trim();
            const status = inputs[1].value.trim();
            const label = inputs[2].value.trim();
            
            if (branch) {
                branches.push({
                    branch: branch.toUpperCase(),
                    set_status: status,
                    add_label: label,
                    add_comment: true,
                    comment_template: ''
                });
            }
        });
        
        branches.push({
            branch: 'default',
            set_status: '',
            add_label: 'merged',
            add_comment: true,
            comment_template: ''
        });
        
        const config = {
            automation: {
                pr_opened: {
                    enabled: true,
                    set_status: document.getElementById('pr-opened-status').value,
                    add_label: document.getElementById('pr-opened-label').value,
                    add_comment: document.getElementById('pr-opened-comment').checked,
                    comment_template: document.getElementById('pr-opened-template').value,
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
                    enabled: true,
                    branch_rules: branches
                },
                pr_closed: {
                    enabled: true,
                    add_comment: document.getElementById('pr-closed-comment').checked,
                    comment_template: '❌ PR closed: {pr_url}',
                    update_pr_field: false,
                    add_label: document.getElementById('pr-closed-label').value,
                    set_status: ''
                }
            }
        };
        
        const response = await fetch('/api/save-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        if (response.ok) {
            showNotification('✅ Rules saved successfully!');
        } else {
            showNotification('❌ Failed to save');
        }
    } catch (error) {
        console.error('Error saving:', error);
        showNotification('❌ Error saving rules');
    }
}

function showNotification(message) {
    const notif = document.createElement('div');
    notif.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 20px;
        background: #10b981;
        color: white;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.2s ease;
    `;
    notif.textContent = message;
    document.body.appendChild(notif);
    
    setTimeout(() => notif.remove(), 3000);
}
