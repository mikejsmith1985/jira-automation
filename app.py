"""
Jira Hygiene Assistant - Python Edition
A self-contained desktop app that automates Jira hygiene checks via browser automation
Uses Selenium WebDriver with Chrome (no additional browser installation needed)
"""
import os
import sys
import webbrowser
import threading
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Global state
driver = None
current_results = []

class JiraHandler(BaseHTTPRequestHandler):
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
        elif self.path == '/api/query':
            response = self.handle_query(data)
        elif self.path == '/api/bulk-comment':
            response = self.handle_bulk_comment(data)
        else:
            response = {'success': False, 'error': 'Unknown endpoint'}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_init(self, data):
        """Initialize browser and navigate to Jira"""
        global driver
        
        try:
            jira_url = data.get('jiraUrl', '')
            if not jira_url:
                return {'success': False, 'error': 'Jira URL required'}
            
            # Initialize Chrome WebDriver if not already done
            if driver is None:
                chrome_options = Options()
                # Don't run headless - user needs to see and login
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                driver = webdriver.Chrome(options=chrome_options)
            
            # Navigate to Jira
            driver.get(jira_url)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_query(self, data):
        """Execute JQL query via browser automation"""
        global driver, current_results
        
        if driver is None:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            jql = data.get('jql', '')
            
            # Navigate to issue search
            current_url = driver.current_url
            base_url = current_url.split('/jira')[0] if '/jira' in current_url else current_url.split('/browse')[0]
            search_url = f"{base_url}/issues/?jql={jql}"
            
            driver.get(search_url)
            time.sleep(3)  # Wait for page load
            
            # Extract ticket information - try multiple selectors
            results = []
            try:
                # Strategy 1: Look for data-issue-key attributes
                issue_links = driver.find_elements(By.CSS_SELECTOR, 'a[data-issue-key]')
                seen_keys = set()
                
                for link in issue_links[:20]:  # Limit to 20
                    try:
                        key = link.get_attribute('data-issue-key')
                        if key and key not in seen_keys:
                            seen_keys.add(key)
                            try:
                                summary = link.text.strip()
                                if not summary:
                                    summary = key
                            except:
                                summary = key
                            results.append({'key': key, 'summary': summary})
                    except:
                        continue
                
                # Strategy 2: If no results, try finding issue keys in links
                if not results:
                    all_links = driver.find_elements(By.TAG_NAME, 'a')
                    for link in all_links:
                        try:
                            href = link.get_attribute('href')
                            if href and '/browse/' in href:
                                key = href.split('/browse/')[-1].split('?')[0]
                                if key and '-' in key and key not in seen_keys:
                                    seen_keys.add(key)
                                    summary = link.text.strip() or key
                                    results.append({'key': key, 'summary': summary})
                                    if len(results) >= 20:
                                        break
                        except:
                            continue
                            
            except Exception as e:
                print(f"Error extracting results: {e}")
            
            current_results = results
            return {'success': True, 'results': results}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_bulk_comment(self, data):
        """Add comment to multiple tickets"""
        global driver
        
        if driver is None:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            tickets = data.get('tickets', [])
            comment = data.get('comment', '')
            
            success_count = 0
            
            for ticket in tickets:
                try:
                    # Navigate to ticket
                    current_url = driver.current_url
                    base_url = current_url.split('/jira')[0] if '/jira' in current_url else current_url.split('/browse')[0]
                    ticket_url = f"{base_url}/browse/{ticket['key']}"
                    driver.get(ticket_url)
                    
                    time.sleep(2)
                    
                    # Try multiple strategies to add comment
                    try:
                        # Strategy 1: Look for comment textarea
                        comment_field = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[placeholder*="comment" i]'))
                        )
                        comment_field.click()
                        time.sleep(0.5)
                        comment_field.send_keys(comment)
                        
                        # Try to submit with Ctrl+Enter (Jira shortcut)
                        from selenium.webdriver.common.keys import Keys
                        comment_field.send_keys(Keys.CONTROL, Keys.ENTER)
                        
                    except:
                        # Strategy 2: Click comment button first
                        try:
                            comment_btn = driver.find_element(By.ID, 'footer-comment-button')
                            comment_btn.click()
                            time.sleep(1)
                            
                            comment_field = driver.find_element(By.CSS_SELECTOR, 'textarea')
                            comment_field.send_keys(comment)
                            
                            from selenium.webdriver.common.keys import Keys
                            comment_field.send_keys(Keys.CONTROL, Keys.ENTER)
                        except:
                            print(f"Could not add comment to {ticket['key']}")
                            continue
                    
                    time.sleep(1)
                    success_count += 1
                    
                except Exception as e:
                    print(f"Error commenting on {ticket['key']}: {e}")
                    continue
            
            return {'success': True, 'success_count': success_count}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# HTML Template (embedded) - Same as before
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jira Hygiene Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
        }
        h1 {
            color: #172B4D;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .subtitle {
            color: #5E6C84;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .section {
            background: #F4F5F7;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .section h2 {
            color: #172B4D;
            font-size: 18px;
            margin-bottom: 15px;
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
        input, textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #DFE1E6;
            border-radius: 4px;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #0052CC;
        }
        textarea {
            min-height: 80px;
            font-family: 'Courier New', monospace;
            resize: vertical;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #0052CC;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover {
            background: #0747A6;
        }
        .btn-secondary {
            background: #42526E;
        }
        .btn-secondary:hover {
            background: #344563;
        }
        #status {
            padding: 12px;
            border-radius: 4px;
            margin-top: 15px;
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
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        #results {
            margin-top: 20px;
            display: none;
        }
        .result-item {
            background: white;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 4px;
            border-left: 4px solid #0052CC;
        }
        .result-key {
            font-weight: 600;
            color: #0052CC;
            margin-bottom: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Jira Hygiene Assistant</h1>
        <p class="subtitle">Automated Jira ticket hygiene checks via browser automation</p>

        <div class="section">
            <h2>⚙️ Configuration</h2>
            <div class="input-group">
                <label>Jira URL</label>
                <input type="text" id="jiraUrl" placeholder="https://your-company.atlassian.net">
            </div>
            <button onclick="initializeBrowser()">Connect to Jira</button>
        </div>

        <div class="section">
            <h2>🚀 Quick Actions</h2>
            <div class="quick-actions">
                <button onclick="findStaleTickets()">Find Stale Tickets</button>
                <button onclick="findMissingDesc()">Missing Descriptions</button>
                <button onclick="findNoDueDate()">No Due Dates</button>
            </div>
        </div>

        <div class="section">
            <h2>🔧 Custom Query</h2>
            <div class="input-group">
                <label>JQL Query</label>
                <textarea id="customJql" placeholder="project = PROJ AND status = Open"></textarea>
            </div>
            <button onclick="runCustomQuery()">Run Custom Query</button>
        </div>

        <div class="section">
            <h2>📝 Bulk Actions</h2>
            <div class="input-group">
                <label>Comment Text</label>
                <textarea id="commentText" placeholder="Enter comment to add to all found tickets..."></textarea>
            </div>
            <button onclick="bulkAddComments()" class="btn-secondary">Add Comment to All</button>
        </div>

        <div id="status"></div>
        <div id="results"></div>
    </div>

    <script>
        let currentResults = [];

        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status-' + type;
            status.style.display = 'block';
            if (type === 'success') {
                setTimeout(() => status.style.display = 'none', 5000);
            }
        }

        async function initializeBrowser() {
            const jiraUrl = document.getElementById('jiraUrl').value.trim();
            if (!jiraUrl) {
                showStatus('Please enter a Jira URL', 'error');
                return;
            }

            showStatus('Connecting to Jira...', 'info');
            try {
                const response = await fetch('/api/init', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({jiraUrl})
                });
                const data = await response.json();
                
                if (data.success) {
                    showStatus('Connected! Please log in to Jira in the Chrome window.', 'success');
                } else {
                    showStatus('Error: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('Connection failed: ' + error.message, 'error');
            }
        }

        async function findStaleTickets() {
            await runQuery('updated < -7d AND status != Closed AND status != Done ORDER BY updated ASC');
        }

        async function findMissingDesc() {
            await runQuery('description is EMPTY AND status != Closed AND status != Done ORDER BY created DESC');
        }

        async function findNoDueDate() {
            await runQuery('duedate is EMPTY AND status != Closed AND status != Done ORDER BY created DESC');
        }

        async function runCustomQuery() {
            const jql = document.getElementById('customJql').value.trim();
            if (!jql) {
                showStatus('Please enter a JQL query', 'error');
                return;
            }
            await runQuery(jql);
        }

        async function runQuery(jql) {
            showStatus('Running query: ' + jql, 'info');
            try {
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({jql})
                });
                const data = await response.json();
                
                if (data.success) {
                    currentResults = data.results;
                    displayResults(data.results);
                    showStatus(`Found ${data.results.length} ticket(s)`, 'success');
                } else {
                    showStatus('Error: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('Query failed: ' + error.message, 'error');
            }
        }

        function displayResults(results) {
            const resultsDiv = document.getElementById('results');
            if (results.length === 0) {
                resultsDiv.style.display = 'none';
                return;
            }

            resultsDiv.innerHTML = '<h3 style="margin-bottom: 10px;">Results:</h3>';
            results.forEach(result => {
                const item = document.createElement('div');
                item.className = 'result-item';
                item.innerHTML = `
                    <div class="result-key">${result.key}</div>
                    <div class="result-summary">${result.summary}</div>
                `;
                resultsDiv.appendChild(item);
            });
            resultsDiv.style.display = 'block';
        }

        async function bulkAddComments() {
            const comment = document.getElementById('commentText').value.trim();
            if (!comment) {
                showStatus('Please enter a comment', 'error');
                return;
            }
            if (currentResults.length === 0) {
                showStatus('No tickets found. Run a query first.', 'error');
                return;
            }

            showStatus(`Adding comment to ${currentResults.length} ticket(s)...`, 'info');
            try {
                const response = await fetch('/api/bulk-comment', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        tickets: currentResults,
                        comment: comment
                    })
                });
                const data = await response.json();
                
                if (data.success) {
                    showStatus(`Added comment to ${data.success_count} ticket(s)`, 'success');
                } else {
                    showStatus('Error: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('Failed: ' + error.message, 'error');
            }
        }
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
    httpd = HTTPServer(server_address, JiraHandler)
    print("🚀 Jira Hygiene Assistant starting...")
    print("📡 Server: http://localhost:5000")
    print("🌐 Opening browser...")
    httpd.serve_forever()

if __name__ == '__main__':
    # Start browser opener in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run server
    run_server()
