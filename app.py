"""
GitHub-Jira Sync Tool
A self-contained desktop app that syncs GitHub PRs with Jira tickets
Uses Selenium WebDriver with Chrome (no additional browser installation needed)
"""
import os
import sys
import webbrowser
import threading
import time
import json
import yaml
from http.server import HTTPServer, BaseHTTPRequestHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sync_engine import SyncEngine

# Global state
driver = None
sync_engine = None
sync_thread = None
is_syncing = False

class SyncHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the web UI"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        elif self.path == '/api/status':
            self._handle_status()
        elif self.path == '/api/config':
            self._handle_get_config()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests (API endpoints)"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
        except:
            data = {}
        
        if self.path == '/api/init':
            response = self.handle_init(data)
        elif self.path == '/api/sync-now':
            response = self.handle_sync_now()
        elif self.path == '/api/start-scheduler':
            response = self.handle_start_scheduler()
        elif self.path == '/api/stop-scheduler':
            response = self.handle_stop_scheduler()
        elif self.path == '/api/config':
            response = self.handle_save_config(data)
        else:
            response = {'success': False, 'error': 'Unknown endpoint'}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def _handle_status(self):
        """Return current sync status"""
        global is_syncing
        status = {
            'is_syncing': is_syncing,
            'has_driver': driver is not None,
            'has_engine': sync_engine is not None
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status).encode())
    
    def _handle_get_config(self):
        """Return current configuration"""
        try:
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(config).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def handle_init(self, data):
        """Initialize browser"""
        global driver, sync_engine
        
        try:
            # Initialize Chrome WebDriver if not already done
            if driver is None:
                chrome_options = Options()
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                driver = webdriver.Chrome(options=chrome_options)
            
            # Initialize sync engine
            if sync_engine is None:
                sync_engine = SyncEngine(driver)
            
            # Navigate to Jira for authentication
            jira_url = data.get('jiraUrl', sync_engine.config['jira']['base_url'])
            driver.get(jira_url)
            
            return {'success': True, 'message': 'Browser initialized. Please log in to Jira.'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_sync_now(self):
        """Run sync immediately"""
        global sync_engine, is_syncing
        
        if sync_engine is None:
            return {'success': False, 'error': 'Please initialize browser first'}
        
        if is_syncing:
            return {'success': False, 'error': 'Sync already in progress'}
        
        try:
            is_syncing = True
            sync_engine.sync_once()
            is_syncing = False
            return {'success': True, 'message': 'Sync completed'}
        except Exception as e:
            is_syncing = False
            return {'success': False, 'error': str(e)}
    
    def handle_start_scheduler(self):
        """Start scheduled sync"""
        global sync_engine, sync_thread, is_syncing
        
        if sync_engine is None:
            return {'success': False, 'error': 'Please initialize browser first'}
        
        if sync_thread and sync_thread.is_alive():
            return {'success': False, 'error': 'Scheduler already running'}
        
        try:
            sync_thread = threading.Thread(target=sync_engine.start_scheduled, daemon=True)
            sync_thread.start()
            return {'success': True, 'message': 'Scheduler started'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_stop_scheduler(self):
        """Stop scheduled sync"""
        # Note: Can't easily stop schedule thread, would need to implement stop flag
        return {'success': False, 'error': 'Scheduler stop not implemented yet. Restart app to stop.'}
    
    def handle_save_config(self, data):
        """Save configuration changes"""
        try:
            with open('config.yaml', 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            return {'success': True, 'message': 'Configuration saved'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# HTML Template (embedded)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub-Jira Sync Tool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
        }
        .header p {
            opacity: 0.9;
            font-size: 16px;
        }
        .tabs {
            display: flex;
            background: #F4F5F7;
            border-bottom: 2px solid #DFE1E6;
        }
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            background: transparent;
            border: none;
            font-size: 15px;
            font-weight: 600;
            color: #5E6C84;
            transition: all 0.3s;
        }
        .tab:hover {
            background: #EBECF0;
        }
        .tab.active {
            background: white;
            color: #0052CC;
            border-bottom: 3px solid #0052CC;
        }
        .tab-content {
            display: none;
            padding: 30px;
        }
        .tab-content.active {
            display: block;
        }
        .card {
            background: #F4F5F7;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .card h2 {
            color: #172B4D;
            font-size: 20px;
            margin-bottom: 15px;
        }
        .card h3 {
            color: #172B4D;
            font-size: 16px;
            margin-bottom: 10px;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #0052CC;
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #172B4D;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #5E6C84;
            font-size: 14px;
        }
        .workflow-item {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .workflow-info {
            flex: 1;
        }
        .workflow-name {
            font-size: 18px;
            font-weight: 600;
            color: #172B4D;
            margin-bottom: 5px;
        }
        .workflow-desc {
            color: #5E6C84;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .workflow-schedule {
            color: #0052CC;
            font-size: 13px;
            font-weight: 500;
        }
        .workflow-actions {
            display: flex;
            gap: 10px;
        }
        .input-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            color: #5E6C84;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        input, textarea, select {
            width: 100%;
            padding: 10px;
            border: 2px solid #DFE1E6;
            border-radius: 4px;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #0052CC;
        }
        textarea {
            min-height: 80px;
            font-family: 'Courier New', monospace;
            resize: vertical;
        }
        button {
            padding: 10px 20px;
            background: #0052CC;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover {
            background: #0747A6;
        }
        button:disabled {
            background: #B3D4FF;
            cursor: not-allowed;
        }
        .btn-secondary {
            background: #42526E;
        }
        .btn-secondary:hover {
            background: #344563;
        }
        .btn-success {
            background: #00875A;
        }
        .btn-success:hover {
            background: #006644;
        }
        .btn-danger {
            background: #DE350B;
        }
        .btn-danger:hover {
            background: #BF2600;
        }
        .btn-small {
            padding: 6px 12px;
            font-size: 13px;
        }
        .toggle {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }
        .toggle input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 24px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #0052CC;
        }
        input:checked + .slider:before {
            transform: translateX(26px);
        }
        #status {
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 13px;
            display: none;
        }
        .status-info {
            background: #DEEBFF;
            color: #0747A6;
            border-left: 4px solid #0052CC;
        }
        .status-success {
            background: #E3FCEF;
            color: #006644;
            border-left: 4px solid #00875A;
        }
        .status-error {
            background: #FFEBE6;
            color: #BF2600;
            border-left: 4px solid #DE350B;
        }
        .log-viewer {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
        }
        .log-entry {
            margin-bottom: 5px;
        }
        .log-info { color: #4FC3F7; }
        .log-warn { color: #FFB74D; }
        .log-error { color: #E57373; }
        .log-success { color: #81C784; }
        .favorite-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #00875A;
        }
        .favorite-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .favorite-name {
            font-size: 16px;
            font-weight: 600;
            color: #172B4D;
        }
        .favorite-desc {
            color: #5E6C84;
            font-size: 13px;
            margin-bottom: 8px;
        }
        .favorite-jql {
            background: #F4F5F7;
            padding: 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #172B4D;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 GitHub-Jira Sync Tool</h1>
            <p>Automated synchronization between GitHub Pull Requests and Jira tickets</p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('dashboard')">📊 Dashboard</button>
            <button class="tab" onclick="switchTab('workflows')">⚙️ Workflows</button>
            <button class="tab" onclick="switchTab('favorites')">⭐ Favorites</button>
            <button class="tab" onclick="switchTab('logs')">📋 Logs</button>
            <button class="tab" onclick="switchTab('settings')">🔧 Settings</button>
        </div>

        <div id="status"></div>

        <!-- DASHBOARD TAB -->
        <div id="dashboard" class="tab-content active">
            <div class="card">
                <h2>System Status</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="stat-status">●</div>
                        <div class="stat-label">System Status</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-updated">0</div>
                        <div class="stat-label">Tickets Updated Today</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-last-run">Never</div>
                        <div class="stat-label">Last Sync</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="stat-workflows">0</div>
                        <div class="stat-label">Active Workflows</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Quick Actions</h2>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="initializeBrowser()" class="btn-success">
                        🚀 Initialize Browser
                    </button>
                    <button onclick="syncNow()" id="btn-sync-now">
                        🔄 Sync Now
                    </button>
                    <button onclick="startScheduler()" id="btn-start-scheduler" class="btn-secondary">
                        ⏰ Start Scheduler
                    </button>
                    <button onclick="stopScheduler()" id="btn-stop-scheduler" class="btn-danger">
                        ⏹️ Stop Scheduler
                    </button>
                </div>
            </div>

            <div class="card">
                <h2>Recent Activity</h2>
                <div id="recent-activity" class="log-viewer">
                    <div class="log-entry log-info">Waiting for first sync...</div>
                </div>
            </div>
        </div>

        <!-- WORKFLOWS TAB -->
        <div id="workflows" class="tab-content">
            <div class="card">
                <h2>Configured Workflows</h2>
                <p style="color: #5E6C84; margin-bottom: 20px;">
                    Workflows run automatically on schedule. Toggle to enable/disable.
                </p>
                <div id="workflows-list">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
        </div>

        <!-- FAVORITES TAB -->
        <div id="favorites" class="tab-content">
            <div class="card">
                <h2>Saved Favorites</h2>
                <p style="color: #5E6C84; margin-bottom: 20px;">
                    Quick-run saved tasks for common operations.
                </p>
                <div id="favorites-list">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
        </div>

        <!-- LOGS TAB -->
        <div id="logs" class="tab-content">
            <div class="card">
                <h2>System Logs</h2>
                <div style="margin-bottom: 15px; display: flex; gap: 10px;">
                    <button onclick="refreshLogs()" class="btn-small">🔄 Refresh</button>
                    <button onclick="clearLogs()" class="btn-small btn-secondary">🗑️ Clear</button>
                    <select id="log-level" onchange="filterLogs()" style="width: auto;">
                        <option value="all">All Levels</option>
                        <option value="info">INFO</option>
                        <option value="warn">WARN</option>
                        <option value="error">ERROR</option>
                    </select>
                </div>
                <div id="logs-viewer" class="log-viewer">
                    <div class="log-entry log-info">System initialized. Waiting for actions...</div>
                </div>
            </div>
        </div>

        <!-- SETTINGS TAB -->
        <div id="settings" class="tab-content">
            <div class="card">
                <h2>Configuration</h2>
                <div class="input-group">
                    <label>Jira Base URL</label>
                    <input type="text" id="setting-jira-url" placeholder="https://your-company.atlassian.net">
                </div>
                <div class="input-group">
                    <label>GitHub Organization</label>
                    <input type="text" id="setting-github-org" placeholder="your-org">
                </div>
                <div class="input-group">
                    <label>GitHub Repositories (comma-separated)</label>
                    <input type="text" id="setting-github-repos" placeholder="repo1, repo2, repo3">
                </div>
                <button onclick="saveSettings()" class="btn-success">💾 Save Settings</button>
                <button onclick="testJiraConnection()" class="btn-secondary" style="margin-left: 10px;">
                    🔗 Test Jira Connection
                </button>
            </div>

            <div class="card">
                <h2>Advanced</h2>
                <button onclick="editConfig()" class="btn-secondary">📝 Edit config.yaml</button>
                <button onclick="viewLogs()" class="btn-secondary" style="margin-left: 10px;">
                    📄 View Log File
                </button>
            </div>
        </div>
    </div>

    <script>
        let currentConfig = {};
        let logs = [];

        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            
            // Load data when switching to tabs
            if (tabName === 'workflows') loadWorkflows();
            if (tabName === 'favorites') loadFavorites();
            if (tabName === 'logs') refreshLogs();
            if (tabName === 'settings') loadSettings();
        }

        // Status message display
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status-' + type;
            status.style.display = 'block';
            if (type === 'success') {
                setTimeout(() => status.style.display = 'none', 5000);
            }
        }

        // Initialize browser
        async function initializeBrowser() {
            const jiraUrl = document.getElementById('setting-jira-url').value || 
                           'https://your-company.atlassian.net';
            
            showStatus('Initializing browser...', 'info');
            try {
                const response = await fetch('/api/init', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({jiraUrl})
                });
                const data = await response.json();
                
                if (data.success) {
                    showStatus('✅ Browser initialized! Please log in to Jira.', 'success');
                    updateStatus('initialized');
                    addLog('info', 'Browser initialized successfully');
                } else {
                    showStatus('❌ Error: ' + data.error, 'error');
                    addLog('error', 'Failed to initialize: ' + data.error);
                }
            } catch (error) {
                showStatus('❌ Connection failed: ' + error.message, 'error');
                addLog('error', 'Connection error: ' + error.message);
            }
        }

        // Sync now
        async function syncNow() {
            showStatus('Running sync...', 'info');
            addLog('info', 'Manual sync started');
            
            try {
                const response = await fetch('/api/sync-now', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const data = await response.json();
                
                if (data.success) {
                    showStatus('✅ Sync completed successfully!', 'success');
                    addLog('success', 'Sync completed: ' + data.message);
                    updateLastRun();
                } else {
                    showStatus('❌ Error: ' + data.error, 'error');
                    addLog('error', 'Sync failed: ' + data.error);
                }
            } catch (error) {
                showStatus('❌ Sync failed: ' + error.message, 'error');
                addLog('error', 'Sync error: ' + error.message);
            }
        }

        // Start scheduler
        async function startScheduler() {
            showStatus('Starting scheduler...', 'info');
            try {
                const response = await fetch('/api/start-scheduler', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    showStatus('✅ Scheduler started!', 'success');
                    addLog('success', 'Scheduler started');
                    updateStatus('running');
                } else {
                    showStatus('❌ Error: ' + data.error, 'error');
                    addLog('error', 'Scheduler error: ' + data.error);
                }
            } catch (error) {
                showStatus('❌ Failed: ' + error.message, 'error');
            }
        }

        // Stop scheduler
        async function stopScheduler() {
            showStatus('Stopping scheduler...', 'info');
            try {
                const response = await fetch('/api/stop-scheduler', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    showStatus('✅ Scheduler stopped!', 'success');
                    addLog('info', 'Scheduler stopped');
                    updateStatus('stopped');
                } else {
                    showStatus('⚠️ ' + data.error, 'info');
                    addLog('warn', data.error);
                }
            } catch (error) {
                showStatus('❌ Failed: ' + error.message, 'error');
            }
        }

        // Load workflows
        async function loadWorkflows() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                currentConfig = config;
                
                const workflowsList = document.getElementById('workflows-list');
                workflowsList.innerHTML = '';
                
                const workflows = config.workflows || {};
                let count = 0;
                
                for (const [key, workflow] of Object.entries(workflows)) {
                    if (workflow.enabled) count++;
                    
                    const item = document.createElement('div');
                    item.className = 'workflow-item';
                    item.innerHTML = `
                        <div class="workflow-info">
                            <div class="workflow-name">${workflow.description || key}</div>
                            <div class="workflow-desc">${key}</div>
                            <div class="workflow-schedule">
                                📅 ${workflow.schedule.frequency} 
                                ${workflow.schedule.time || ''}
                            </div>
                        </div>
                        <div class="workflow-actions">
                            <label class="toggle">
                                <input type="checkbox" ${workflow.enabled ? 'checked' : ''} 
                                       onchange="toggleWorkflow('${key}', this.checked)">
                                <span class="slider"></span>
                            </label>
                            <button class="btn-small" onclick="runWorkflow('${key}')">
                                ▶️ Run Now
                            </button>
                        </div>
                    `;
                    workflowsList.appendChild(item);
                }
                
                document.getElementById('stat-workflows').textContent = count;
                
            } catch (error) {
                showStatus('Failed to load workflows: ' + error.message, 'error');
            }
        }

        // Load favorites
        async function loadFavorites() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                
                const favoritesList = document.getElementById('favorites-list');
                favoritesList.innerHTML = '';
                
                const favorites = config.favorites || {};
                
                for (const [key, favorite] of Object.entries(favorites)) {
                    const item = document.createElement('div');
                    item.className = 'favorite-item';
                    item.innerHTML = `
                        <div class="favorite-header">
                            <div class="favorite-name">${favorite.name}</div>
                            <button class="btn-small btn-success" onclick="runFavorite('${key}')">
                                ▶️ Run
                            </button>
                        </div>
                        <div class="favorite-desc">${favorite.description}</div>
                        <div class="favorite-jql">JQL: ${favorite.jql_query}</div>
                    `;
                    favoritesList.appendChild(item);
                }
                
            } catch (error) {
                showStatus('Failed to load favorites: ' + error.message, 'error');
            }
        }

        // Run favorite
        async function runFavorite(key) {
            showStatus('Running favorite: ' + key, 'info');
            addLog('info', 'Running favorite: ' + key);
            
            // TODO: Implement favorite execution
            showStatus('⚠️ Favorite execution not yet implemented', 'info');
        }

        // Run workflow
        async function runWorkflow(key) {
            showStatus('Running workflow: ' + key, 'info');
            addLog('info', 'Running workflow: ' + key);
            
            // TODO: Implement workflow execution
            showStatus('⚠️ Workflow execution not yet implemented', 'info');
        }

        // Toggle workflow
        async function toggleWorkflow(key, enabled) {
            addLog('info', `Workflow ${key} ${enabled ? 'enabled' : 'disabled'}`);
            // TODO: Save to config
        }

        // Load settings
        async function loadSettings() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                
                document.getElementById('setting-jira-url').value = 
                    config.jira?.base_url || '';
                document.getElementById('setting-github-org').value = 
                    config.github?.organization || '';
                document.getElementById('setting-github-repos').value = 
                    (config.github?.repositories || []).join(', ');
                    
            } catch (error) {
                showStatus('Failed to load settings: ' + error.message, 'error');
            }
        }

        // Save settings
        async function saveSettings() {
            const jiraUrl = document.getElementById('setting-jira-url').value;
            const githubOrg = document.getElementById('setting-github-org').value;
            const repos = document.getElementById('setting-github-repos').value
                .split(',').map(r => r.trim());
            
            currentConfig.jira = currentConfig.jira || {};
            currentConfig.jira.base_url = jiraUrl;
            currentConfig.github = currentConfig.github || {};
            currentConfig.github.organization = githubOrg;
            currentConfig.github.repositories = repos;
            
            showStatus('Saving settings...', 'info');
            
            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(currentConfig)
                });
                const data = await response.json();
                
                if (data.success) {
                    showStatus('✅ Settings saved!', 'success');
                    addLog('success', 'Configuration updated');
                } else {
                    showStatus('❌ Error: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('❌ Failed to save: ' + error.message, 'error');
            }
        }

        // Test Jira connection
        async function testJiraConnection() {
            const jiraUrl = document.getElementById('setting-jira-url').value;
            if (!jiraUrl) {
                showStatus('Please enter Jira URL first', 'error');
                return;
            }
            
            await initializeBrowser();
        }

        // Log management
        function addLog(level, message) {
            const timestamp = new Date().toLocaleTimeString();
            logs.push({timestamp, level, message});
            
            const entry = document.createElement('div');
            entry.className = `log-entry log-${level}`;
            entry.textContent = `[${timestamp}] ${level.toUpperCase()}: ${message}`;
            
            const viewer = document.getElementById('logs-viewer');
            viewer.insertBefore(entry, viewer.firstChild);
            
            // Keep only last 100 logs
            if (viewer.children.length > 100) {
                viewer.removeChild(viewer.lastChild);
            }
            
            // Also add to recent activity
            const activity = document.getElementById('recent-activity');
            const activityEntry = entry.cloneNode(true);
            activity.insertBefore(activityEntry, activity.firstChild);
            if (activity.children.length > 10) {
                activity.removeChild(activity.lastChild);
            }
        }

        function refreshLogs() {
            addLog('info', 'Logs refreshed');
        }

        function clearLogs() {
            document.getElementById('logs-viewer').innerHTML = '';
            logs = [];
            addLog('info', 'Logs cleared');
        }

        function filterLogs() {
            const level = document.getElementById('log-level').value;
            // TODO: Implement log filtering
            addLog('info', 'Filter set to: ' + level);
        }

        // Status updates
        function updateStatus(status) {
            const statusElem = document.getElementById('stat-status');
            if (status === 'initialized' || status === 'running') {
                statusElem.textContent = '🟢';
                statusElem.style.color = '#00875A';
            } else if (status === 'stopped') {
                statusElem.textContent = '🟡';
                statusElem.style.color = '#FFAB00';
            } else {
                statusElem.textContent = '🔴';
                statusElem.style.color = '#DE350B';
            }
        }

        function updateLastRun() {
            document.getElementById('stat-last-run').textContent = 
                new Date().toLocaleTimeString();
        }

        function editConfig() {
            alert('Config editor coming soon! For now, edit config.yaml directly.');
        }

        function viewLogs() {
            alert('Log viewer coming soon! For now, check jira-sync.log file.');
        }

        // Initialize on load
        window.addEventListener('load', () => {
            addLog('info', 'UI initialized');
            loadWorkflows();
            loadSettings();
        });
    </script>
</body>
</html>
"""

def open_browser():
    """Open default browser to the app"""
    time.sleep(1.5)
    webbrowser.open('http://localhost:5000')

def run_server():
    """Run the HTTP server"""
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, SyncHandler)
    print("🚀 GitHub-Jira Sync Tool starting...")
    print("📡 Server: http://localhost:5000")
    print("🌐 Opening browser...")
    httpd.serve_forever()

if __name__ == '__main__':
    # Start browser opener in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run server
    run_server()
