/* Modern UI JavaScript */

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

function getBranchRulesFromUI(container) {
    const rules = [];
    // If no container provided, default to document (backwards compatibility or global search)
    // But better to scope it.
    const root = container || document;
    const ruleElements = root.querySelectorAll('.branch-rule');
    
    ruleElements.forEach(el => {
        const branchInput = el.querySelector('.branch-name-input');
        const statusInput = el.querySelector('.status-input');
        const labelInput = el.querySelector('.label-input');
        const commentInput = el.querySelector('.comment-input');
        
        if (branchInput.value.trim()) {
            rules.push({
                branch: branchInput.value.trim(), // removed toUpperCase to allow flexibility
                set_status: statusInput.value || '',
                add_label: labelInput.value || '',
                add_comment: commentInput.checked,
                comment_template: '' // Template not exposed in branch UI currently
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
        const container = document.getElementById('rules-container');
        
        if (container && config.automation) {
            container.innerHTML = ''; // Clear loading/static content
            
            // Sort keys to ensure consistent order (Opened, Updated, Merged, Closed)
            const order = ['pr_opened', 'pr_updated', 'pr_merged', 'pr_closed'];
            const keys = Object.keys(config.automation).sort((a, b) => {
                const idxA = order.indexOf(a);
                const idxB = order.indexOf(b);
                if (idxA !== -1 && idxB !== -1) return idxA - idxB;
                if (idxA !== -1) return -1;
                if (idxB !== -1) return 1;
                return a.localeCompare(b);
            });

            keys.forEach(key => {
                const rule = config.automation[key];
                container.appendChild(createRuleElement(key, rule));
            });
        }
    } catch (error) {
        console.error('Error loading config:', error);
        showNotification('Error loading configuration', 'error');
    }
}

function createRuleElement(key, rule) {
    const card = document.createElement('div');
    card.className = 'rule-card';
    card.dataset.key = key;

    const titleMap = {
        pr_opened: '🆕 When PR is Opened',
        pr_merged: '✅ When PR is Merged',
        pr_closed: '❌ When PR is Closed',
        pr_updated: '🔄 When PR is Updated'
    };
    const title = titleMap[key] || `When ${key.replace(/_/g, ' ')}`;
    
    // Common Enable
    const enabled = rule.enabled !== false;
    const enabledHtml = `
        <div class="form-group">
            <label class="checkbox-label">
                <input type="checkbox" class="rule-enabled" ${enabled ? 'checked' : ''}>
                <span>Enable this rule</span>
            </label>
        </div>
    `;

    let bodyHtml = '';
    
    if (rule.branch_rules) {
        // Branch rules
        bodyHtml = `
            ${enabledHtml}
            <div class="branch-rules-container"></div>
            <button class="btn btn-secondary add-branch-rule" style="margin-top:10px">+ Add branch rule</button>
        `;
    } else {
        // Standard rule
        const status = rule.set_status || '';
        const label = rule.add_label || '';
        const comment = rule.add_comment !== false;
        const template = rule.comment_template || '';

        bodyHtml = `
            ${enabledHtml}
            <div class="form-group">
                <label>Move to Status</label>
                <input type="text" class="input-field rule-status" value="${status}" placeholder="e.g., In Review">
                <p class="form-hint">Leave empty to skip</p>
            </div>
            <div class="form-group">
                <label>Add Label</label>
                <input type="text" class="input-field rule-label" value="${label}" placeholder="e.g., has-pr">
            </div>
            <div class="form-group">
                <label class="checkbox-label">
                    <input type="checkbox" class="rule-comment" ${comment ? 'checked' : ''}>
                    <span>Add comment to ticket</span>
                </label>
            </div>
            <div class="form-group">
                <label>Comment Template</label>
                <textarea class="rule-template" placeholder="Comment text...">${template}</textarea>
            </div>
        `;
    }

    card.innerHTML = `
        <div class="rule-title">
            <h4>${title}</h4>
        </div>
        <div class="rule-body">
            ${bodyHtml}
        </div>
    `;

    // Hydrate branch rules
    if (rule.branch_rules) {
        const brContainer = card.querySelector('.branch-rules-container');
        rule.branch_rules.forEach(br => {
            brContainer.appendChild(createBranchRuleElement(br));
        });
        
        card.querySelector('.add-branch-rule').addEventListener('click', () => {
            brContainer.appendChild(createBranchRuleElement({branch: 'NEW'}));
        });
    }

    return card;
}

function initSaveRules() {
    const saveBtn = document.getElementById('save-rules');
    const resetBtn = document.getElementById('reset-rules');
    
    if (saveBtn) saveBtn.addEventListener('click', saveRules);
    if (resetBtn) resetBtn.addEventListener('click', loadRulesFromConfig);
}

async function saveRules() {
    try {
        const container = document.getElementById('rules-container');
        const cards = container.querySelectorAll('.rule-card');
        const automation = {};
        
        cards.forEach(card => {
            const key = card.dataset.key;
            const enabled = card.querySelector('.rule-enabled').checked;
            
            if (card.querySelector('.branch-rules-container')) {
                // Branch rule
                const brContainer = card.querySelector('.branch-rules-container');
                const branchRules = getBranchRulesFromUI(brContainer);
                
                automation[key] = {
                    enabled: enabled,
                    branch_rules: branchRules
                };
            } else {
                // Standard rule
                automation[key] = {
                    enabled: enabled,
                    set_status: card.querySelector('.rule-status').value,
                    add_label: card.querySelector('.rule-label').value,
                    add_comment: card.querySelector('.rule-comment').checked,
                    comment_template: card.querySelector('.rule-template').value,
                    update_pr_field: key === 'pr_opened' // Preserve logic or make dynamic?
                    // Better to preserve update_pr_field default if not exposed in UI.
                    // Or scrape it if we exposed it. We didn't expose it.
                    // We'll rely on merging with existing config in backend or here.
                };
            }
        });
        
        // Get current config to merge hidden fields (like update_pr_field)
        const response = await fetch('/api/config');
        const currentConfig = await response.json();
        
        // Merge
        Object.keys(automation).forEach(key => {
            if (currentConfig.automation && currentConfig.automation[key]) {
                // Keep properties we didn't edit
                automation[key] = { ...currentConfig.automation[key], ...automation[key] };
            }
        });

        currentConfig.automation = automation;
        
        // Save
        const saveResponse = await fetch('/api/save-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentConfig)
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

let mediaRecorder = null;
let recordedChunks = [];
let recordingTimer = null;
let screenshotData = null;
let videoData = null;

function initFeedback() {
    const feedbackBtn = document.getElementById('feedbackBtn');
    if (feedbackBtn) {
        feedbackBtn.addEventListener('click', openFeedbackModal);
    }
}

function openFeedbackModal() {
    const modal = document.getElementById('feedback-modal');
    const controller = document.getElementById('feedback-controller');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.remove('minimized');
        if (controller) {
            controller.style.display = 'none';
        }
        // Reset attachments only if opening fresh
        if (!screenshotData && !videoData) {
            document.getElementById('feedback-attachments').innerHTML = '';
        }
    }
}

function closeFeedbackModal() {
    const modal = document.getElementById('feedback-modal');
    const controller = document.getElementById('feedback-controller');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('minimized');
    }
    if (controller) {
        controller.style.display = 'none';
    }
    // Stop recording if active
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
    // Clear data
    screenshotData = null;
    videoData = null;
    document.getElementById('feedback-title').value = '';
    document.getElementById('feedback-description').value = '';
    document.getElementById('feedback-attachments').innerHTML = '';
}

function minimizeFeedbackModal() {
    console.log('[Waypoint] Minimizing feedback modal...');
    const modal = document.getElementById('feedback-modal');
    const controller = document.getElementById('feedback-controller');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.add('minimized');
        console.log('[Waypoint] Modal hidden');
    }
    if (controller) {
        controller.style.display = 'block';
        updateControllerStatus();
        console.log('[Waypoint] Controller shown');
    }
}

function restoreFeedbackModal() {
    console.log('[Waypoint] Restoring feedback modal...');
    const modal = document.getElementById('feedback-modal');
    const controller = document.getElementById('feedback-controller');
    if (modal) {
        modal.style.display = 'flex';
        modal.classList.remove('minimized');
    }
    if (controller) {
        controller.style.display = 'none';
    }
}

function updateControllerStatus() {
    const controllerAttachments = document.getElementById('controller-attachments');
    if (!controllerAttachments) return;
    
    const items = [];
    if (screenshotData) items.push('📸 Screenshot');
    if (videoData) items.push('🎥 Video');
    
    if (items.length > 0) {
        controllerAttachments.textContent = items.join(' + ');
    } else {
        controllerAttachments.textContent = 'No media captured yet';
    }
}

function updateLogIndicator() {
    const checkbox = document.getElementById('feedback-include-logs');
    const indicator = document.getElementById('log-indicator');
    if (!indicator) return;
    
    if (checkbox.checked) {
        indicator.textContent = '✓ Logs will be included';
        indicator.style.color = '#00875a';
    } else {
        indicator.textContent = '✗ Logs will not be included';
        indicator.style.color = '#de350b';
    }
}

async function captureScreenshot() {
    try {
        console.log('[Waypoint] Capturing screenshot...');
        
        // Use native browser API if available
        if (navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) {
            const stream = await navigator.mediaDevices.getDisplayMedia({
                video: { mediaSource: 'screen' }
            });
            
            const video = document.createElement('video');
            video.srcObject = stream;
            video.play();
            
            // Wait for video to be ready
            await new Promise(resolve => {
                video.onloadedmetadata = resolve;
            });
            
            // Capture frame
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            
            // Stop stream
            stream.getTracks().forEach(track => track.stop());
            
            // Convert to blob
            canvas.toBlob(blob => {
                screenshotData = blob;
                displayAttachment('screenshot', 'Screenshot captured', blob.size);
                updateControllerStatus();
                showNotification('✓ Screenshot captured');
            }, 'image/png');
        } else {
            showNotification('Screenshot API not available', 'error');
        }
    } catch (error) {
        console.error('[Waypoint] Screenshot error:', error);
        if (error.name === 'NotAllowedError') {
            showNotification('Screenshot cancelled', 'error');
        } else {
            showNotification('Failed to capture screenshot', 'error');
        }
    }
}

async function toggleVideoRecording() {
    console.log('[Waypoint] toggleVideoRecording called, state:', mediaRecorder?.state);
    const btn = document.getElementById('record-video-btn');
    const controllerBtn = document.getElementById('controller-record-btn');
    const indicator = document.getElementById('recording-indicator');
    const controllerIndicator = document.getElementById('controller-recording-indicator');
    
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        // Stop recording
        console.log('[Waypoint] Stopping recording...');
        mediaRecorder.stop();
        if (btn) btn.textContent = '🎥 Record Video (60s)';
        if (controllerBtn) controllerBtn.textContent = '🎥 Record';
        if (indicator) indicator.style.display = 'none';
        if (controllerIndicator) controllerIndicator.style.display = 'none';
        if (recordingTimer) {
            clearInterval(recordingTimer);
            recordingTimer = null;
        }
        return;
    }
    
    // Minimize modal FIRST before starting recording
    const modal = document.getElementById('feedback-modal');
    if (modal && modal.style.display !== 'none') {
        console.log('[Waypoint] Minimizing modal before recording...');
        minimizeFeedbackModal();
        // Wait a moment for modal to hide
        await new Promise(resolve => setTimeout(resolve, 300));
    }
    
    try {
        console.log('[Waypoint] Starting video recording...');
        
        const stream = await navigator.mediaDevices.getDisplayMedia({
            video: { mediaSource: 'screen' },
            audio: false
        });
        
        console.log('[Waypoint] Display media stream obtained');
        
        recordedChunks = [];
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'video/webm;codecs=vp8'
        });
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            console.log('[Waypoint] Recording stopped');
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            videoData = blob;
            displayAttachment('video', 'Video recorded', blob.size);
            updateControllerStatus();
            // Properly close all tracks to dismiss share dialog
            stream.getTracks().forEach(track => {
                track.stop();
                console.log('[Waypoint] Track stopped:', track.kind);
            });
            showNotification('✓ Video recorded');
            
            // Reset button states
            if (btn) btn.textContent = '🎥 Record Video (60s)';
            if (controllerBtn) controllerBtn.textContent = '🎥 Record';
            if (indicator) indicator.style.display = 'none';
            if (controllerIndicator) controllerIndicator.style.display = 'none';
        };
        
        mediaRecorder.start();
        console.log('[Waypoint] MediaRecorder started');
        if (btn) btn.textContent = '⏹ Stop Recording';
        if (controllerBtn) controllerBtn.textContent = '⏹ Stop';
        if (indicator) indicator.style.display = 'flex';
        if (controllerIndicator) controllerIndicator.style.display = 'flex';
        
        // Timer
        let seconds = 0;
        const timerEl = document.getElementById('recording-timer');
        const controllerTimerEl = document.getElementById('controller-recording-timer');
        recordingTimer = setInterval(() => {
            seconds++;
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            const timeStr = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            if (timerEl) timerEl.textContent = timeStr;
            if (controllerTimerEl) controllerTimerEl.textContent = timeStr;
            
            // Auto-stop at 60 seconds
            if (seconds >= 60) {
                console.log('[Waypoint] 60 second limit reached, stopping...');
                toggleVideoRecording();
            }
        }, 1000);
        
    } catch (error) {
        console.error('[Waypoint] Video recording error:', error);
        if (error.name === 'NotAllowedError') {
            showNotification('Recording cancelled', 'error');
        } else {
            showNotification('Failed to start recording', 'error');
        }
    }
}

function displayAttachment(type, label, size) {
    const container = document.getElementById('feedback-attachments');
    const sizeText = (size / 1024).toFixed(1) + ' KB';
    
    const attachment = document.createElement('div');
    attachment.style.cssText = 'padding: 8px 12px; background: var(--bg-secondary); border-radius: 6px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;';
    attachment.innerHTML = `
        <span>${type === 'screenshot' ? '📸' : '🎥'} ${label} (${sizeText})</span>
        <button onclick="removeAttachment('${type}')" style="background: none; border: none; color: #de350b; cursor: pointer; font-size: 18px;">&times;</button>
    `;
    
    container.appendChild(attachment);
}

function removeAttachment(type) {
    if (type === 'screenshot') {
        screenshotData = null;
    } else if (type === 'video') {
        videoData = null;
    }
    document.getElementById('feedback-attachments').innerHTML = '';
}

async function submitFeedback() {
    const title = document.getElementById('feedback-title').value;
    const description = document.getElementById('feedback-description').value;
    const includeLogs = document.getElementById('feedback-include-logs').checked;
    
    if (!title || !description) {
        alert('❌ Please fill in title and description');
        showNotification('❌ Please fill in title and description', 'error');
        return;
    }
    
    const submitBtn = document.getElementById('submit-feedback-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    
    try {
        console.log('[Waypoint] Submitting feedback...');
        
        // Create form data
        const formData = new FormData();
        formData.append('title', title);
        formData.append('description', description);
        formData.append('include_logs', includeLogs);
        
        if (screenshotData) {
            console.log('[Waypoint] Attaching screenshot:', screenshotData.size, 'bytes');
            formData.append('screenshot', screenshotData, 'screenshot.png');
        }
        
        if (videoData) {
            console.log('[Waypoint] Attaching video:', videoData.size, 'bytes');
            formData.append('video', videoData, 'recording.webm');
        }
        
        console.log('[Waypoint] Sending feedback to /api/feedback/submit...');
        const response = await fetch('/api/feedback/submit', {
            method: 'POST',
            body: formData
        });
        
        console.log('[Waypoint] Response status:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('[Waypoint] HTTP error response:', errorText);
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            try {
                const errorJson = JSON.parse(errorText);
                errorMessage = errorJson.error || errorMessage;
            } catch (e) {
                // Not JSON, use status text
            }
            alert(`❌ Failed to submit feedback:\n\n${errorMessage}\n\nCheck console for details.`);
            showNotification('❌ ' + errorMessage, 'error');
            return;
        }
        
        const result = await response.json();
        console.log('[Waypoint] Feedback result:', result);
        
        if (result.success) {
            alert(`✅ Feedback submitted successfully!\n\nIssue #${result.issue_number}\n${result.issue_url}`);
            showNotification('✅ Feedback submitted!');
            closeFeedbackModal();
            // Clear form
            document.getElementById('feedback-title').value = '';
            document.getElementById('feedback-description').value = '';
            screenshotData = null;
            videoData = null;
            document.getElementById('feedback-attachments').innerHTML = '';
        } else {
            const errorMsg = result.error || 'Unknown error occurred';
            console.error('[Waypoint] Feedback submission failed:', errorMsg);
            alert(`❌ Failed to submit feedback:\n\n${errorMsg}\n\nCheck console for details.`);
            showNotification('❌ ' + errorMsg, 'error');
        }
    } catch (error) {
        console.error('[Waypoint] Feedback submission exception:', error);
        const errorMsg = error.message || error.toString();
        alert(`❌ Failed to submit feedback:\n\n${errorMsg}\n\nCheck console for details.`);
        showNotification('❌ Network error: ' + errorMsg, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Feedback';
    }
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
    const feedbackRepoInput = document.getElementById('feedback-repo-input');
    
    if (githubOrgInput && status.github.organization) {
        githubOrgInput.value = status.github.organization;
    }
    if (jiraUrlInput && status.jira.base_url && !status.jira.base_url.includes('your-company')) {
        jiraUrlInput.value = status.jira.base_url;
    }
    if (jiraProjectsInput && status.jira.project_keys) {
        jiraProjectsInput.value = status.jira.project_keys.join(', ');
    }
    if (feedbackRepoInput && status.feedback.repo && !status.feedback.repo.includes('owner/repository')) {
        feedbackRepoInput.value = status.feedback.repo;
    }
    
    // Show indicator if feedback is configured
    if (status.feedback.configured) {
        const feedbackStatus = document.getElementById('feedback-save-status');
        if (feedbackStatus) {
            feedbackStatus.textContent = '✓ Configured';
            feedbackStatus.style.color = '#00875A';
        }
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

async function saveFeedbackSettings() {
    const token = document.getElementById('feedback-token-input').value;
    const repo = document.getElementById('feedback-repo-input').value;
    const statusEl = document.getElementById('feedback-save-status');
    
    if (!token || !repo) {
        statusEl.textContent = '❌ Both token and repository are required';
        statusEl.style.color = '#DE350B';
        return;
    }
    
    statusEl.textContent = 'Saving...';
    statusEl.style.color = 'var(--text-secondary)';
    
    try {
        const response = await fetch('/api/integrations/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                feedback: {
                    github_token: token,
                    repo: repo
                }
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusEl.textContent = '✓ Saved successfully';
            statusEl.style.color = '#00875A';
            showNotification('Feedback settings saved! You can now submit bug reports.');
            setTimeout(() => statusEl.textContent = '', 3000);
        } else {
            statusEl.textContent = `❌ ${result.error}`;
            statusEl.style.color = '#DE350B';
        }
    } catch (error) {
        statusEl.textContent = '❌ Failed to save';
        statusEl.style.color = '#DE350B';
    }
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
            const debugInfo = result.debug ? `<br><small style="color: var(--text-secondary);">${result.debug}</small>` : '';
            if (resultEl) resultEl.innerHTML = `<span style="color: #00875a;">✓ Logged in${result.user ? ' as ' + result.user : ''}</span>${debugInfo}`;
            showNotification('Jira login confirmed!');
        } else if (result.success) {
            const debugInfo = result.debug ? `<br><small style="color: var(--text-secondary);">${result.debug}</small>` : '';
            if (resultEl) resultEl.innerHTML = `<span style="color: #FF991F;">⚠ Not logged in - please login in the browser window</span>${debugInfo}`;
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
    // Update metric cards with visible vs hidden breakdown
    const totalEl = document.getElementById('sm-total-issues');
    if (totalEl) {
        const visibleCount = metrics.visible_issues || metrics.total_issues || 0;
        const hiddenCount = metrics.hidden_issues || 0;
        
        if (hiddenCount > 0) {
            totalEl.innerHTML = `${visibleCount} <span style="color: #de350b; font-size: 0.8em;">(+${hiddenCount} hidden)</span>`;
        } else {
            totalEl.textContent = visibleCount;
        }
    }
    
    // Display scraped issues with visibility indicator
    const listContainer = document.getElementById('sm-issues-list');
    if (listContainer && metrics.issues_scraped) {
        let html = '';
        
        // Show visible issues first
        const visibleIssues = metrics.issues_scraped.filter(i => i.visible !== false);
        const hiddenIssues = metrics.issues_scraped.filter(i => i.visible === false);
        
        // Visible issues
        if (visibleIssues.length > 0) {
            html += '<h4 style="margin: 15px 0 10px 0; color: #00875A;">✓ Visible in Jira (' + visibleIssues.length + ')</h4>';
            visibleIssues.forEach(issue => {
                html += `
                    <div class="integration-item" style="border-left: 3px solid #00875A;">
                        <div class="integration-info">
                            <h4>${issue.key || issue}</h4>
                            <p class="text-secondary">${issue.url || ''}</p>
                        </div>
                    </div>
                `;
            });
        }
        
        // Hidden issues (phantom entries)
        if (hiddenIssues.length > 0) {
            html += '<h4 style="margin: 20px 0 10px 0; color: #de350b;">⚠ Hidden/Phantom Issues (' + hiddenIssues.length + ')</h4>';
            html += '<p style="font-size: 0.9em; color: #6B778C; margin-bottom: 10px;">These exist in HTML DOM but are not visible in Jira UI (archived, filtered, collapsed, or stale)</p>';
            hiddenIssues.forEach(issue => {
                html += `
                    <div class="integration-item" style="border-left: 3px solid #de350b; background: #FFEBE6;">
                        <div class="integration-info">
                            <h4>${issue.key || issue} <span style="color: #de350b; font-size: 0.8em;">HIDDEN</span></h4>
                            <p class="text-secondary">${issue.url || ''}</p>
                        </div>
                    </div>
                `;
            });
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


// Make all functions globally accessible for onclick handlers
window.captureScreenshot = captureScreenshot;
window.toggleVideoRecording = toggleVideoRecording;
window.submitFeedback = submitFeedback;
window.removeAttachment = removeAttachment;
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
window.minimizeFeedbackModal = minimizeFeedbackModal;
window.restoreFeedbackModal = restoreFeedbackModal;
window.updateLogIndicator = updateLogIndicator;
