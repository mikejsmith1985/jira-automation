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
    try {
        const prbNumber = document.getElementById('prb-number-input').value.trim();
        const resultEl = document.getElementById('prb-validation-result');
        const createBtn = document.getElementById('create-jira-btn');
        
        console.log('[Waypoint] PRB Number:', prbNumber);
        console.log('[Waypoint] Elements found:', {
            prbInput: !!document.getElementById('prb-number-input'),
            resultEl: !!resultEl,
            createBtn: !!createBtn
        });
        
        // Null checks for DOM elements
        if (!resultEl) {
            console.error('[Waypoint] prb-validation-result element not found!');
            showNotification('UI error: validation result element not found', 'error');
            return;
        }
        
        if (!prbNumber) {
            showNotification('Please enter a PRB number', 'error');
            return;
        }
        
        // Show loading
        resultEl.style.display = 'block';
        resultEl.innerHTML = '<div style="text-align: center; padding: 20px;"><span>Validating PRB...</span></div>';
        createBtn.disabled = true;
    
    try {
        const response = await fetch('/api/snow-jira/validate-prb', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prb_number: prbNumber })
        });
        const result = await response.json();
        
        if (result.success) {
            currentPRBData = result.data;
            
            // Display PRB details
            const detailsHTML = `
                <p><strong>PRB:</strong> ${result.data.prb_number || 'N/A'}</p>
                <p><strong>Summary:</strong> ${result.data.short_description || 'N/A'}</p>
                <p><strong>Priority:</strong> ${result.data.priority || 'N/A'}</p>
            `;
            document.getElementById('prb-details').innerHTML = detailsHTML;
            
            // Handle incident selection
            const incSelection = document.getElementById('inc-selection');
            const incList = document.getElementById('inc-list');
            
            if (result.incidents && result.incidents.length > 0) {
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
                createBtn.disabled = false;
                
            } else {
                incSelection.style.display = 'block';
                incList.innerHTML = '<span style="color: #FF991F;">⚠️ No incidents found in Incidents tab</span>';
                createBtn.disabled = true;
            }
            
            showNotification('PRB validated successfully!');
            
        } else {
            console.error('[Waypoint] PRB validation failed:', result.error);
            if (resultEl) {
                resultEl.innerHTML = `<div style="color: #de350b; text-align: center; padding: 20px;">${result.error}</div>`;
            }
            if (createBtn) createBtn.disabled = true;
            showNotification(result.error, 'error');
        }
    } catch (error) {
        console.error('[Waypoint] validatePRB() exception:', error);
        console.error('[Waypoint] Error stack:', error.stack);
        if (resultEl) {
            resultEl.innerHTML = `<div style="color: #de350b; text-align: center; padding: 20px;">Failed to validate PRB: ${error.message}</div>`;
        }
        if (createBtn) createBtn.disabled = true;
        showNotification('Failed to validate PRB: ' + error.message, 'error');
    }
    } catch (error) {
        console.error('[Waypoint] validatePRB() outer exception:', error);
        console.error('[Waypoint] Error stack:', error.stack);
        showNotification('Critical error in validatePRB: ' + error.message, 'error');
    }
}

function selectIncident(incNumber) {
    selectedIncident = incNumber;
    document.getElementById('create-jira-btn').disabled = false;
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
