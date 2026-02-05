/* ============================================================================
   ServiceNow → Jira Automation Functions
   ============================================================================ */

// ServiceNow Configuration
async function copySnowConfig() {
    const config = {
        url: document.getElementById('snow-url-input').value,
        jira_project: document.getElementById('snow-jira-project-input').value,
        field_mapping: {}
    };
    
    try {
        const mappingText = document.getElementById('snow-field-mapping-input').value;
        if (mappingText.trim()) {
            config.field_mapping = JSON.parse(mappingText);
        }
    } catch (e) {
        showNotification('Invalid JSON in field mapping', 'error');
        return;
    }
    
    const jsonText = JSON.stringify(config, null, 2);
    
    try {
        await navigator.clipboard.writeText(jsonText);
        showNotification('Configuration copied to clipboard!');
    } catch (e) {
        showNotification('Failed to copy to clipboard', 'error');
    }
}

async function testSnowConnection() {
    const resultEl = document.getElementById('snow-config-result');
    const url = document.getElementById('snow-url-input').value.trim();
    
    // Check if URL is configured
    if (!url) {
        if (resultEl) resultEl.innerHTML = '<span style="color: #de350b;">✗ Please enter a ServiceNow URL first</span>';
        showNotification('Please enter a ServiceNow URL first', 'error');
        document.getElementById('snow-url-input').focus();
        return;
    }
    
    if (resultEl) resultEl.innerHTML = '<span>Testing connection...</span>';
    
    try {
        const response = await fetch('/api/snow-jira/test-connection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const result = await response.json();
        
        if (result.success) {
            if (resultEl) resultEl.innerHTML = `<span style="color: #00875a;">✓ ${result.message}</span>`;
            showNotification('ServiceNow connection successful!');
        } else {
            if (resultEl) resultEl.innerHTML = `<span style="color: #de350b;">✗ ${result.error}</span>`;
            showNotification(result.error, 'error');
        }
    } catch (error) {
        if (resultEl) resultEl.innerHTML = `<span style="color: #de350b;">✗ Connection failed</span>`;
        showNotification('Connection test failed', 'error');
    }
}

async function saveSnowConfig() {
    const resultEl = document.getElementById('snow-config-result');
    if (resultEl) resultEl.innerHTML = '<span>Saving configuration...</span>';
    
    const url = document.getElementById('snow-url-input').value.trim();
    const jiraProject = document.getElementById('snow-jira-project-input').value.trim();
    
    // Frontend validation
    if (!url) {
        if (resultEl) resultEl.innerHTML = '<span style="color: #de350b;">✗ ServiceNow URL is required</span>';
        showNotification('ServiceNow URL is required', 'error');
        document.getElementById('snow-url-input').focus();
        return;
    }
    
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        if (resultEl) resultEl.innerHTML = '<span style="color: #de350b;">✗ URL must start with http:// or https://</span>';
        showNotification('URL must start with http:// or https://', 'error');
        document.getElementById('snow-url-input').focus();
        return;
    }
    
    if (!jiraProject) {
        if (resultEl) resultEl.innerHTML = '<span style="color: #de350b;">✗ Jira Project Key is required</span>';
        showNotification('Jira Project Key is required', 'error');
        document.getElementById('snow-jira-project-input').focus();
        return;
    }
    
    let fieldMapping = {};
    try {
        const mappingText = document.getElementById('snow-field-mapping-input').value;
        if (mappingText.trim()) {
            fieldMapping = JSON.parse(mappingText);
        }
    } catch (e) {
        if (resultEl) resultEl.innerHTML = '<span style="color: #de350b;">✗ Invalid JSON in field mapping</span>';
        showNotification('Invalid JSON in field mapping', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/snow-jira/save-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                jira_project: jiraProject,
                field_mapping: fieldMapping
            })
        });
        const result = await response.json();
        
        if (result.success) {
            if (resultEl) resultEl.innerHTML = `<span style="color: #00875a;">✓ ${result.message}</span>`;
            showNotification('ServiceNow configuration saved successfully!');
            console.log('[SNOW] Configuration saved:', { url, jiraProject });
        } else {
            if (resultEl) resultEl.innerHTML = `<span style="color: #de350b;">✗ ${result.error}</span>`;
            showNotification(result.error, 'error');
        }
    } catch (error) {
        if (resultEl) resultEl.innerHTML = `<span style="color: #de350b;">✗ Failed to save</span>`;
        showNotification('Failed to save configuration', 'error');
    }
}

// Load ServiceNow config on page load
async function loadSnowConfig() {
    try {
        const response = await fetch('/api/snow-jira/config');
        const result = await response.json();
        
        if (result.success && result.config) {
            const config = result.config;
            document.getElementById('snow-url-input').value = config.url || '';
            document.getElementById('snow-jira-project-input').value = config.jira_project || '';
            
            if (config.field_mapping) {
                document.getElementById('snow-field-mapping-input').value = JSON.stringify(config.field_mapping, null, 2);
            }
        }
    } catch (e) {
        console.error('[Waypoint] Failed to load ServiceNow config:', e);
    }
}

// PO Tab - ServiceNow to Jira Automation
let currentPRBData = null;
let selectedIncident = null;

async function validatePRB() {
    console.log('[Waypoint] validatePRB() called');
    
    const prbNumber = document.getElementById('prb-number-input').value.trim();
    const step1 = document.getElementById('workflow-step-1');
    const step2 = document.getElementById('workflow-step-2');
    const createBtn = document.getElementById('create-jira-btn');
    
    if (!prbNumber) {
        showNotification('Please enter a PRB number', 'error');
        return;
    }
    
    // Show step 2 with loading state
    step1.style.display = 'none';
    step2.style.display = 'block';
    
    const resultEl = document.getElementById('prb-validation-result');
    resultEl.innerHTML = '<div style="text-align: center; padding: 20px;"><span>Validating PRB...</span></div>';
    if (createBtn) createBtn.disabled = true;
    
    try {
        const response = await fetch('/api/snow-jira/validate-prb', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prb_number: prbNumber })
        });
        const result = await response.json();
        
        if (result.success) {
            console.log('[Waypoint] ✅ PRB validation SUCCESS');
            console.log('[Waypoint] Result data:', JSON.stringify(result.data, null, 2));
            console.log('[Waypoint] Incidents found:', result.incidents ? result.incidents.length : 0);
            
            currentPRBData = result.data;
            
            // Display PRB details
            const prbDetails = document.getElementById('prb-details');
            if (prbDetails) {
                const detailsHTML = `
                    <div style="background: var(--bg-primary); padding: 15px; border-radius: 8px; border-left: 4px solid var(--accent-green);">
                        <h4 style="margin: 0 0 10px 0; color: var(--accent-green);">✅ PRB Data Retrieved</h4>
                        <p><strong>PRB:</strong> ${result.data.prb_number || 'N/A'}</p>
                        <p><strong>Summary:</strong> ${result.data.short_description || 'N/A'}</p>
                        <p><strong>Priority:</strong> ${result.data.priority || 'N/A'}</p>
                        ${result.data.category ? `<p><strong>Category:</strong> ${result.data.category}</p>` : ''}
                        ${result.data.problem_owner ? `<p><strong>Owner:</strong> ${result.data.problem_owner}</p>` : ''}
                        <p style="margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-color); color: var(--text-secondary); font-size: 12px;">
                            <strong>Fields extracted:</strong> ${Object.keys(result.data).length} fields
                        </p>
                    </div>
                `;
                prbDetails.innerHTML = detailsHTML;
                console.log('[Waypoint] ✓ PRB details displayed');
            } else {
                console.error('[Waypoint] ✗ prb-details element not found!');
            }
            
            // Handle incident selection
            const incSelection = document.getElementById('inc-selection');
            const incList = document.getElementById('inc-list');
            
            if (incSelection && incList) {
                if (result.incidents && result.incidents.length > 0) {
                    console.log('[Waypoint] Displaying', result.incidents.length, 'incidents');
                    incSelection.style.display = 'block';
                    incList.innerHTML = '';
                    
                    result.incidents.forEach((inc, idx) => {
                        const radio = document.createElement('label');
                        radio.style.cssText = 'display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 8px; background: var(--bg-primary); border-radius: 4px;';
                        radio.innerHTML = `
                            <input type="radio" name="incident-select" value="${inc.number}" ${idx === 0 ? 'checked' : ''} onchange="selectIncident('${inc.number}')">
                            <span style="font-weight: 600;">${inc.number}</span>
                            <span style="color: var(--text-secondary); font-size: 12px;">${inc.summary || 'No summary'}</span>
                        `;
                        incList.appendChild(radio);
                    });
                    
                    // Auto-select first one
                    selectedIncident = result.incidents[0].number;
                    if (createBtn) {
                        createBtn.disabled = false;
                        console.log('[Waypoint] ✓ Create button enabled');
                    }
                    
                } else {
                    console.log('[Waypoint] ⚠️ No incidents found');
                    incSelection.style.display = 'block';
                    incList.innerHTML = '<span style="color: #FF991F;">⚠️ No incidents found in Incidents tab</span>';
                    if (createBtn) createBtn.disabled = true;
                }
            } else {
                console.error('[Waypoint] ✗ inc-selection or inc-list elements not found!');
            }
            
            // Clear loading message and show success
            resultEl.innerHTML = `<div style="color: var(--accent-green); text-align: center; padding: 10px;">✅ PRB validated successfully! ${Object.keys(result.data).length} fields extracted.</div>`;
            showNotification(`✅ PRB validated! ${Object.keys(result.data).length} fields extracted, ${result.incidents ? result.incidents.length : 0} incidents found.`);
            
        } else {
            console.error('[Waypoint] PRB validation failed:', result.error);
            resultEl.innerHTML = `<div style="color: #de350b; text-align: center; padding: 20px;">${result.error}</div>`;
            if (createBtn) createBtn.disabled = true;
            showNotification(result.error, 'error');
        }
    } catch (error) {
        console.error('[Waypoint] validatePRB() exception:', error);
        resultEl.innerHTML = `<div style="color: #de350b; text-align: center; padding: 20px;">Failed to validate PRB: ${error.message}</div>`;
        if (createBtn) createBtn.disabled = true;
        showNotification('Failed to validate PRB: ' + error.message, 'error');
    }
}

function selectIncident(incNumber) {
    selectedIncident = incNumber;
    document.getElementById('create-jira-btn').disabled = false;
}

function resetPRBWorkflow() {
    // Reset state
    currentPRBData = null;
    selectedIncident = null;
    
    // Reset UI
    document.getElementById('workflow-step-1').style.display = 'block';
    document.getElementById('workflow-step-2').style.display = 'none';
    document.getElementById('workflow-step-3').style.display = 'none';
    
    // Clear input
    document.getElementById('prb-number-input').value = '';
    document.getElementById('prb-number-input').focus();
}

async function createJiraIssues() {
    console.log('[Waypoint] createJiraIssues() called');
    try {
        const prbNumber = document.getElementById('prb-number-input').value.trim();
        const statusEl = document.getElementById('snow-sync-status');
        const resultEl = document.getElementById('snow-sync-result');
    const createBtn = document.getElementById('create-jira-btn');
    
    if (!selectedIncident) {
        showNotification('Please select an incident', 'error');
        return;
    }
    
    // Show progress
    statusEl.innerHTML = `
        <div style="text-align: center; padding: 15px; background: var(--bg-secondary); border-radius: 8px;">
            <div style="margin-bottom: 10px;">Creating Jira issues...</div>
            <div style="color: var(--text-secondary); font-size: 12px;">This may take 30-60 seconds</div>
        </div>
    `;
    resultEl.style.display = 'none';
    createBtn.disabled = true;
    
    try {
        const response = await fetch('/api/snow-jira/sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prb_number: prbNumber,
                selected_inc: selectedIncident
            })
        });
        const result = await response.json();
        
        statusEl.innerHTML = '';
        
        if (result.success) {
            const jiraBaseUrl = document.getElementById('snow-url-input').value || 'https://your-jira.atlassian.net';
            
            const issuesHTML = `
                <p>✅ Defect created: <a href="${jiraBaseUrl}/browse/${result.defect_key}" target="_blank" style="color: var(--accent); font-weight: 600;">${result.defect_key}</a></p>
                <p>✅ Story created: <a href="${jiraBaseUrl}/browse/${result.story_key}" target="_blank" style="color: var(--accent); font-weight: 600;">${result.story_key}</a></p>
                <p style="margin-top: 10px; font-size: 12px; color: var(--text-secondary);">
                    ${result.prb_updated ? '✅ ServiceNow PRB updated' : '⚠️ ' + (result.warning || 'Note: PRB update may have failed')}
                </p>
            `;
            document.getElementById('created-issues').innerHTML = issuesHTML;
            resultEl.style.display = 'block';
            
            showNotification('Jira issues created successfully!');
            
            // Reset form
            setTimeout(() => {
                document.getElementById('prb-number-input').value = '';
                document.getElementById('prb-validation-result').style.display = 'none';
                resultEl.style.display = 'none';
                createBtn.disabled = true;
                currentPRBData = null;
                selectedIncident = null;
            }, 10000);
            
        } else {
            console.error('[Waypoint] Create Jira issues failed:', result.error);
            statusEl.innerHTML = `<div style="color: #de350b; text-align: center; padding: 15px; background: var(--bg-secondary); border-radius: 8px;">${result.error}</div>`;
            showNotification(result.error, 'error');
            createBtn.disabled = false;
        }
    } catch (error) {
        console.error('[Waypoint] createJiraIssues() exception:', error);
        console.error('[Waypoint] Error stack:', error.stack);
        statusEl.innerHTML = `<div style="color: #de350b; text-align: center; padding: 15px; background: var(--bg-secondary); border-radius: 8px;">Failed to create Jira issues: ${error.message}</div>`;
        showNotification('Failed to create Jira issues', 'error');
        createBtn.disabled = false;
    }
    } catch (error) {
        console.error('[Waypoint] createJiraIssues() outer exception:', error);
        console.error('[Waypoint] Error stack:', error.stack);
        showNotification('Critical error in createJiraIssues: ' + error.message, 'error');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Waypoint] ServiceNow module initializing...');
    try {
        // Check if PRB section exists
        const prbSection = document.getElementById('prb-number-input');
        if (prbSection) {
            console.log('[Waypoint] ✓ PRB section found in DOM');
        } else {
            console.error('[Waypoint] ✗ PRB section NOT found in DOM');
        }
        
        // Check if functions are defined
        console.log('[Waypoint] Function check:', {
            validatePRB: typeof validatePRB,
            createJiraIssues: typeof createJiraIssues,
            loadSnowConfig: typeof loadSnowConfig,
            testSnowConnection: typeof testSnowConnection
        });
        
        loadSnowConfig();
        console.log('[Waypoint] ✓ ServiceNow module initialized successfully');
    } catch (error) {
        console.error('[Waypoint] ✗ ServiceNow module initialization FAILED:', error);
        console.error('[Waypoint] Error stack:', error.stack);
    }
});
// Export logs for debugging
window.exportLogs = async function exportLogs() {
    console.log('[ServiceNow] Exporting logs...');
    
    const resultEl = document.getElementById('snow-config-result');
    if (resultEl) {
        resultEl.textContent = 'Exporting logs...';
        resultEl.className = '';
    }
    
    try {
        const response = await fetch('/api/export-logs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Create downloadable file
            const blob = new Blob([result.log_data], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
            a.download = `waypoint-logs-${timestamp}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            if (resultEl) {
                resultEl.textContent = `✓ Logs exported (${result.lines} lines)`;
                resultEl.className = 'text-success';
            }
            
            console.log('[ServiceNow] Logs exported successfully');
        } else {
            if (resultEl) {
                resultEl.textContent = `✗ Export failed: ${result.error}`;
                resultEl.className = 'text-error';
            }
            console.error('[ServiceNow] Export failed:', result.error);
        }
    } catch (error) {
        if (resultEl) {
            resultEl.textContent = `✗ Export error: ${error.message}`;
            resultEl.className = 'text-error';
        }
        console.error('[ServiceNow] Export error:', error);
    }
};

/* ============================================================================
   Bookmarklet Workflow Functions
   ============================================================================ */

let workflowPollingInterval = null;
let workflowPRBNumber = null;

// Start PRB workflow - opens SNOW page and waits for bookmarklet data
async function startPRBWorkflow() {
    const prbNumber = document.getElementById('prb-number-input').value.trim();
    
    if (!prbNumber) {
        showNotification('Please enter a PRB number', 'error');
        return;
    }
    
    workflowPRBNumber = prbNumber;
    
    console.log('[Workflow] Starting PRB workflow for:', prbNumber);
    
    try {
        // Start the workflow on backend
        const response = await fetch('/api/bookmarklet/start-workflow', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'prb-extract', prb_number: prbNumber })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showNotification('Failed to start workflow: ' + result.error, 'error');
            return;
        }
        
        // Show step 2 (waiting for bookmarklet)
        document.getElementById('workflow-step-1').style.display = 'none';
        document.getElementById('workflow-step-2').style.display = 'block';
        document.getElementById('prb-number-display').textContent = prbNumber;
        
        // Set up the "open again" link
        const link = document.getElementById('snow-page-link');
        if (result.prb_url) {
            link.href = result.prb_url;
            link.style.display = 'inline';
            link.onclick = null;  // Clear any override
            
            // Open SNOW page in new tab
            window.open(result.prb_url, '_blank');
        } else {
            // No URL - disable link and show error
            link.href = 'javascript:void(0)';
            link.style.display = 'none';
            link.onclick = (e) => { e.preventDefault(); showNotification('No ServiceNow URL configured', 'error'); };
            showNotification('No ServiceNow URL configured. Please configure it in Integrations tab.', 'error');
        }
        
        // Start polling for bookmarklet data
        startBookmarkletPolling();
        
    } catch (error) {
        console.error('[Workflow] Error starting workflow:', error);
        showNotification('Error starting workflow: ' + error.message, 'error');
    }
}

function startBookmarkletPolling() {
    // Clear any existing polling
    if (workflowPollingInterval) {
        clearInterval(workflowPollingInterval);
    }
    
    const statusEl = document.getElementById('bookmarklet-status');
    let dots = 0;
    
    workflowPollingInterval = setInterval(async () => {
        dots = (dots + 1) % 4;
        const dotStr = '.'.repeat(dots);
        
        try {
            const response = await fetch('/api/bookmarklet/status');
            const result = await response.json();
            
            if (result.has_data && result.data) {
                // Data received! Stop polling and advance workflow
                clearInterval(workflowPollingInterval);
                workflowPollingInterval = null;
                
                console.log('[Workflow] Data received from bookmarklet:', result.data);
                
                // Process the received data
                handleBookmarkletData(result.data);
            } else {
                // Still waiting
                statusEl.innerHTML = `<span style="color: #6b778c;">⏳ Waiting for data${dotStr}</span>`;
            }
        } catch (error) {
            console.error('[Workflow] Polling error:', error);
        }
    }, 1500);
}

function handleBookmarkletData(data) {
    console.log('[Workflow] Processing bookmarklet data');
    
    // Store as current PRB data
    currentPRBData = data.prb || {};
    
    // Populate Step 3
    const prbDetails = document.getElementById('prb-details');
    if (prbDetails) {
        prbDetails.innerHTML = `
            <div style="display: grid; grid-template-columns: 120px 1fr; gap: 8px;">
                <strong>Number:</strong> <span>${currentPRBData.number || 'N/A'}</span>
                <strong>Description:</strong> <span>${currentPRBData.short_description || 'N/A'}</span>
                <strong>State:</strong> <span>${currentPRBData.state || 'N/A'}</span>
                <strong>Priority:</strong> <span>${currentPRBData.priority || 'N/A'}</span>
                <strong>Assigned To:</strong> <span>${currentPRBData.assigned_to || 'N/A'}</span>
            </div>
        `;
    }
    
    // Populate incidents list
    const incList = document.getElementById('inc-list');
    const incidents = data.incidents || [];
    
    if (incList) {
        if (incidents.length > 0) {
            incList.innerHTML = incidents.map((inc, i) => `
                <label style="display: flex; align-items: center; gap: 8px; padding: 8px; background: var(--surface); border-radius: 4px; cursor: pointer;">
                    <input type="radio" name="incident-select" value="${inc.number}" onchange="selectIncident('${inc.number}')" ${i === 0 ? 'checked' : ''}>
                    <span><strong>${inc.number}</strong> - ${inc.short_description || 'No description'}</span>
                </label>
            `).join('');
            
            // Auto-select first incident
            if (incidents.length > 0) {
                selectedIncident = incidents[0].number;
                document.getElementById('create-jira-btn').disabled = false;
            }
        } else {
            incList.innerHTML = '<p style="color: var(--text-secondary); font-style: italic;">No related incidents found</p>';
        }
    }
    
    // Show Step 3, hide Step 2
    document.getElementById('workflow-step-2').style.display = 'none';
    document.getElementById('workflow-step-3').style.display = 'block';
    
    showNotification('PRB data received successfully!');
}

function cancelPRBWorkflow() {
    // Stop polling
    if (workflowPollingInterval) {
        clearInterval(workflowPollingInterval);
        workflowPollingInterval = null;
    }
    
    // Reset to step 1
    document.getElementById('workflow-step-1').style.display = 'block';
    document.getElementById('workflow-step-2').style.display = 'none';
    document.getElementById('workflow-step-3').style.display = 'none';
    document.getElementById('workflow-step-4').style.display = 'none';
    
    workflowPRBNumber = null;
    currentPRBData = null;
    selectedIncident = null;
}

function resetPRBWorkflow() {
    cancelPRBWorkflow();
    document.getElementById('prb-number-input').value = '';
}

async function createJiraFromPRB() {
    console.log('[Workflow] Creating Jira issues from PRB data');
    
    if (!currentPRBData || !selectedIncident) {
        showNotification('Missing PRB data or incident selection', 'error');
        return;
    }
    
    const createBtn = document.getElementById('create-jira-btn');
    createBtn.disabled = true;
    createBtn.textContent = 'Creating...';
    
    try {
        // For now, show success with mock data since Jira creation via bookmarklet is Phase 2
        // In Phase 2, this would open Jira and use bookmarklet to fill the form
        
        // Show Step 4 with instructions
        document.getElementById('workflow-step-3').style.display = 'none';
        document.getElementById('workflow-step-4').style.display = 'block';
        
        const jiraStatus = document.getElementById('jira-creation-status');
        jiraStatus.innerHTML = `
            <p style="margin: 0 0 15px 0; color: #006644; font-weight: 600;">
                ✅ PRB data ready for Jira!
            </p>
            <p style="margin: 0 0 10px 0;">
                <strong>PRB:</strong> ${currentPRBData.number}<br>
                <strong>Incident:</strong> ${selectedIncident}
            </p>
            <p style="margin: 0 0 15px 0; font-size: 13px; color: var(--text-secondary);">
                The Jira issue creation via bookmarklet is coming soon.
                For now, manually create issues with the extracted data above.
            </p>
            <button class="btn btn-secondary" onclick="resetPRBWorkflow()">↩ Start Over</button>
        `;
        
        showNotification('PRB data extracted! Manual Jira creation required.', 'info');
        
    } catch (error) {
        console.error('[Workflow] Jira creation error:', error);
        showNotification('Error: ' + error.message, 'error');
        createBtn.disabled = false;
        createBtn.textContent = '✨ Create Jira Issues';
    }
}

// Export new workflow functions
window.startPRBWorkflow = startPRBWorkflow;
window.cancelPRBWorkflow = cancelPRBWorkflow;
window.resetPRBWorkflow = resetPRBWorkflow;
window.createJiraFromPRB = createJiraFromPRB;
