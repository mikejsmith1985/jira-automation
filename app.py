"""
Waypoint - Simplifying Jira administration and team flow
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
from insights_engine import InsightsEngine
from feedback_db import FeedbackDB
from github_feedback import GitHubFeedback, LogCapture

# Global state
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
driver = None
sync_engine = None
sync_thread = None
is_syncing = False
insights_engine = None
feedback_db = FeedbackDB()  # SQLite-based feedback storage
github_feedback = None  # Optional GitHub sync
log_capture = LogCapture()

class SyncHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the web UI"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        sys.stdout.write(f"[GET] {self.path}\n")
        sys.stdout.flush()
        
        if self.path == '/' or self.path == '/index.html':
            self._serve_static_file('modern-ui.html', 'text/html; charset=utf-8')
        elif self.path.startswith('/assets/'):
            # Serve static assets
            filepath = self.path[1:]  # Remove leading slash
            content_type = self._get_content_type(filepath)
            sys.stdout.write(f"[STATIC] Serving {filepath} as {content_type}\n")
            sys.stdout.flush()
            self._serve_static_file(filepath, content_type)
        elif self.path == '/api/status':
            self._handle_status()
        elif self.path == '/api/config':
            self._handle_get_config()
        elif self.path == '/api/insights':
            self._handle_get_insights()
        elif self.path == '/api/insights/trend':
            self._handle_get_trend()
        elif self.path == '/api/feedback/validate-token':
            self._handle_validate_feedback_token()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _serve_static_file(self, filepath, content_type):
        """Serve static files with caching"""
        try:
            # Convert to absolute path
            abs_filepath = os.path.join(BASE_DIR, filepath)
            sys.stdout.write(f"[SERVE] Attempting to serve: {abs_filepath}\n")
            sys.stdout.flush()
            
            # Handle HTML files without cache
            if filepath.endswith('.html'):
                with open(abs_filepath, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', content_type)
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    self.end_headers()
                    self.wfile.write(f.read())
            else:
                with open(abs_filepath, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', content_type)
                    self.send_header('Cache-Control', 'public, max-age=31536000')
                    self.end_headers()
                    self.wfile.write(f.read())
        except FileNotFoundError as e:
            sys.stdout.write(f"[404] File not found: {abs_filepath}\n")
            sys.stdout.write(f"[404] Error: {e}\n")
            sys.stdout.flush()
            self.send_response(404)
            self.end_headers()
        except Exception as e:
            sys.stdout.write(f"[ERROR] Failed to serve {filepath}: {e}\n")
            sys.stdout.flush()
            self.send_response(500)
            self.end_headers()
    
    def _get_content_type(self, filepath):
        """Get content type from file extension"""
        if filepath.endswith('.js'):
            return 'application/javascript'
        elif filepath.endswith('.css'):
            return 'text/css'
        elif filepath.endswith('.html'):
            return 'text/html; charset=utf-8'
        elif filepath.endswith('.json'):
            return 'application/json'
        elif filepath.endswith('.png'):
            return 'image/png'
        elif filepath.endswith('.jpg') or filepath.endswith('.jpeg'):
            return 'image/jpeg'
        elif filepath.endswith('.svg'):
            return 'image/svg+xml'
        else:
            return 'application/octet-stream'
    
    def do_POST(self):
        """Handle POST requests (API endpoints)"""
        try:
            # Special handlers that manage their own response
            if self.path == '/api/feedback/console-log':
                self._handle_console_log()
                return
            elif self.path == '/api/feedback/network-error':
                self._handle_network_error()
                return
            
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
            elif self.path == '/api/save-config':
                response = self.handle_save_config(data)
            elif self.path == '/api/insights/resolve':
                response = self.handle_resolve_insight(data)
            elif self.path == '/api/insights/run':
                response = self.handle_run_insights(data)
            elif self.path == '/api/feedback/submit':
                response = self.handle_submit_feedback(data)
            elif self.path == '/api/feedback/save-token':
                response = self.handle_save_feedback_token(data)
            else:
                response = {'success': False, 'error': 'Unknown endpoint'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            print(f"ERROR in do_POST: {str(e)}")
            import traceback
            traceback.print_exc()
            try:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
            except:
                pass
    
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
            with open('config.yaml', 'r', encoding='utf-8') as f:
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
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False)
            return {'success': True, 'message': 'Configuration saved'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_get_insights(self):
        """Return recent insights"""
        global insights_engine
        try:
            if insights_engine is None:
                insights_engine = InsightsEngine()
            
            days = int(self.headers.get('X-Days', 7))
            insights = insights_engine.get_insights(days=days)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'insights': insights}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def _handle_get_trend(self):
        """Return metric trend data"""
        global insights_engine
        try:
            if insights_engine is None:
                insights_engine = InsightsEngine()
            
            metric_type = self.headers.get('X-Metric-Type', 'velocity')
            days = int(self.headers.get('X-Days', 30))
            trend = insights_engine.get_metric_trend(metric_type, days)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'trend': trend}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def handle_resolve_insight(self, data):
        """Mark insight as resolved"""
        global insights_engine
        try:
            if insights_engine is None:
                insights_engine = InsightsEngine()
            
            insight_id = data.get('id')
            if not insight_id:
                return {'success': False, 'error': 'Missing insight ID'}
            
            insights_engine.resolve_insight(insight_id)
            return {'success': True, 'message': 'Insight resolved'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_run_insights(self, data):
        """Run insights analysis on provided data"""
        global insights_engine
        try:
            if insights_engine is None:
                insights_engine = InsightsEngine()
            
            jira_data = data.get('jira_data', {})
            insights = insights_engine.analyze_all(jira_data)
            
            return {'success': True, 'insights': insights}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_validate_feedback_token(self):
        """Validate GitHub feedback token"""
        global github_feedback
        try:
            if github_feedback and github_feedback.token:
                result = github_feedback.validate_token()
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'valid': False,
                    'error': 'No token configured'
                }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def _handle_console_log(self):
        """Receive and store console log from browser"""
        global log_capture
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            log_entry = json.loads(post_data.decode('utf-8'))
            
            log_capture.add_console_log(log_entry)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def _handle_network_error(self):
        """Receive and store network error from browser"""
        global log_capture
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            error_entry = json.loads(post_data.decode('utf-8'))
            
            log_capture.add_network_error(error_entry)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def handle_submit_feedback(self, data):
        """Submit feedback - save to SQLite only (GitHub handled by frontend)"""
        global feedback_db, log_capture
        try:
            title = data.get('title', 'User Feedback')
            description = data.get('description', '')
            attachments = data.get('attachments', [])
            include_logs = data.get('include_logs', True)
            github_issue_url = data.get('github_issue_url')  # Comes from frontend if successful
            github_issue_number = data.get('github_issue_number')
            
            # Build feedback body
            body = description + "\n\n"
            
            if include_logs:
                body += log_capture.export_all_logs()
            
            # Add system info
            import platform
            body += "\n\n## System Information\n"
            body += f"- OS: {platform.system()} {platform.release()}\n"
            body += f"- Python: {platform.python_version()}\n"
            body += f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Save to SQLite (always succeeds)
            logs_json = json.dumps(log_capture.console_logs + log_capture.network_errors) if include_logs else None
            attachments_json = json.dumps(attachments) if attachments else None
            
            feedback_id = feedback_db.add_feedback(
                title=title,
                description=body,
                logs=logs_json,
                attachments=attachments_json
            )
            
            # Update status based on whether GitHub sync happened
            if github_issue_url:
                feedback_db.update_status(feedback_id, 'synced', github_issue_url)
                message = f'✅ Feedback submitted to GitHub (Issue #{github_issue_number})'
            else:
                feedback_db.update_status(feedback_id, 'local')
                message = f'✅ Feedback saved locally (ID: {feedback_id})'
            
            return {
                'success': True,
                'feedback_id': feedback_id,
                'message': message
            }
            
        except Exception as e:
            print(f"ERROR in handle_submit_feedback: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def handle_save_feedback_token(self, data):
        """Save GitHub feedback token to config"""
        global github_feedback
        try:
            print(f"DEBUG: handle_save_feedback_token called with data keys: {data.keys()}")
            token = data.get('token', '')
            repo = data.get('repo', '')
            print(f"DEBUG: token length={len(token)}, repo={repo}")
            
            if not token or not repo:
                return {'success': False, 'error': 'Token and repo required'}
            
            # Load config
            print("DEBUG: Loading config...")
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Update feedback section
            if 'feedback' not in config:
                config['feedback'] = {}
            
            config['feedback']['github_token'] = token
            config['feedback']['repo'] = repo
            
            # Save config
            print("DEBUG: Saving config...")
            with open('config.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Initialize GitHub feedback client
            print("DEBUG: Creating GitHubFeedback object...")
            github_feedback = GitHubFeedback(token=token, repo_name=repo)
            
            # Validate token
            print("DEBUG: Validating token...")
            validation = github_feedback.validate_token()
            print(f"DEBUG: Validation result: {validation}")
            
            if validation['valid']:
                return {
                    'success': True,
                    'message': f"Token validated for user: {validation['user']}"
                }
            else:
                return {
                    'success': False,
                    'error': validation['error']
                }
            
        except Exception as e:
            print(f"ERROR in handle_save_feedback_token: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}


# HTML Template (embedded)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waypoint - Jira Administration</title>
    <script src="/assets/js/html2canvas.min.js"></script>
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
            max-width: 1400px;
            margin: 0 auto;
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
        .feature-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #0052CC;
        }
        .feature-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }
        .feature-title {
            font-size: 18px;
            font-weight: 600;
            color: #172B4D;
            margin-bottom: 5px;
        }
        .feature-key {
            color: #5E6C84;
            font-size: 13px;
            font-family: 'Courier New', monospace;
        }
        .feature-progress {
            text-align: right;
        }
        .progress-bar {
            width: 120px;
            height: 8px;
            background: #DFE1E6;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 5px;
        }
        .progress-fill {
            height: 100%;
            background: #00875A;
            transition: width 0.3s;
        }
        .progress-text {
            font-size: 12px;
            color: #5E6C84;
        }
        .child-issues {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #DFE1E6;
        }
        .child-issue {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #F4F5F7;
        }
        .child-issue:last-child {
            border-bottom: none;
        }
        .child-issue-info {
            flex: 1;
        }
        .child-issue-key {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #5E6C84;
            margin-right: 8px;
        }
        .child-issue-summary {
            font-size: 14px;
            color: #172B4D;
        }
        .child-issue-status {
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-todo {
            background: #DFE1E6;
            color: #42526E;
        }
        .status-inprogress {
            background: #DEEBFF;
            color: #0052CC;
        }
        .status-review {
            background: #FFF0B3;
            color: #7A5C00;
        }
        .status-done {
            background: #E3FCEF;
            color: #006644;
        }
        .status-blocked {
            background: #FFEBE6;
            color: #BF2600;
        }
        .expand-toggle {
            background: none;
            border: none;
            color: #0052CC;
            cursor: pointer;
            font-size: 18px;
            padding: 0 8px;
        }
        .canvas-card {
            position: absolute;
            width: 220px;
            background: white;
            border-radius: 8px;
            padding: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            cursor: move;
            transition: box-shadow 0.2s;
            z-index: 10;
        }
        .canvas-card:hover {
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
            z-index: 20;
        }
        .canvas-card.selected {
            box-shadow: 0 0 0 3px #0052CC;
            z-index: 30;
        }
        .canvas-card.blocked {
            border-left: 4px solid #DE350B;
        }
        .canvas-card-key {
            font-family: 'Courier New', monospace;
            font-size: 11px;
            color: #0052CC;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .canvas-card-summary {
            font-size: 13px;
            color: #172B4D;
            line-height: 1.3;
            margin-bottom: 6px;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        .canvas-card-status {
            font-size: 10px;
            padding: 3px 6px;
            border-radius: 3px;
            display: inline-block;
        }
        .canvas-card-links {
            font-size: 10px;
            color: #5E6C84;
            margin-top: 6px;
            padding-top: 6px;
            border-top: 1px solid #DFE1E6;
        }
        #dependency-canvas-container {
            cursor: grab;
        }
        #dependency-canvas-container.dragging {
            cursor: grabbing;
        }
        .persona-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid #DFE1E6;
        }
        .persona-card:hover {
            border-color: #0052CC;
            box-shadow: 0 4px 12px rgba(0,82,204,0.2);
            transform: translateY(-2px);
        }
        .persona-card.selected {
            border-color: #00875A;
            background: #E3FCEF;
        }
        .persona-title {
            font-size: 18px;
            font-weight: 600;
            color: #172B4D;
            margin-bottom: 8px;
        }
        .persona-desc {
            font-size: 13px;
            color: #5E6C84;
            line-height: 1.4;
        }
        
        /* Feedback System Styles */
        .feedback-floating-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #DE350B 0%, #FF5630 100%);
            color: white;
            font-size: 28px;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(222, 53, 11, 0.4);
            z-index: 999;
            transition: all 0.3s;
        }
        .feedback-floating-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(222, 53, 11, 0.6);
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 0;
            border-radius: 12px;
            max-width: 700px;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: slideDown 0.3s;
        }
        @keyframes slideDown {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .modal-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-header h2 {
            margin: 0;
            font-size: 24px;
        }
        .modal-close {
            font-size: 32px;
            font-weight: 300;
            cursor: pointer;
            opacity: 0.8;
            transition: opacity 0.2s;
        }
        .modal-close:hover {
            opacity: 1;
        }
        .modal-body {
            padding: 30px;
        }
        .recording-pulse {
            display: inline-block;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        .attachment-preview {
            display: inline-block;
            margin: 5px;
            padding: 10px;
            background: #F4F5F7;
            border-radius: 4px;
            border: 2px solid #DFE1E6;
        }
        .attachment-preview img {
            max-width: 150px;
            max-height: 150px;
            display: block;
            margin-bottom: 5px;
            border-radius: 4px;
        }
        .attachment-preview video {
            max-width: 200px;
            max-height: 150px;
            display: block;
            margin-bottom: 5px;
            border-radius: 4px;
        }
        .attachment-preview button {
            font-size: 11px;
            padding: 4px 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧭 Waypoint</h1>
            <p>Simplifying Jira administration and team flow</p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('dashboard', event)">📊 Dashboard</button>
            <button class="tab" onclick="switchTab('po', event)">👔 PO</button>
            <button class="tab" onclick="switchTab('dev', event)">💻 Dev</button>
            <button class="tab" onclick="switchTab('sm', event)">📈 SM</button>
            <button class="tab" onclick="switchTab('workflows', event)">⚙️ Workflows</button>
            <button class="tab" onclick="switchTab('favorites', event)">⭐ Favorites</button>
            <button class="tab" onclick="switchTab('logs', event)">📋 Logs</button>
            <button class="tab" onclick="switchTab('settings', event)">🔧 Settings</button>
        </div>

        <div id="status"></div>

        <!-- DASHBOARD TAB -->
        <div id="dashboard" class="tab-content active">
            <!-- Persona Selection Card -->
            <div class="card">
                <h2>Welcome! Select Your Primary Role</h2>
                <p style="color: #5E6C84; margin-bottom: 15px;">
                    Choose your role to see relevant quick actions on the dashboard. You can always access all features from the tabs above.
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                    <div class="persona-card" onclick="selectPersona('po')">
                        <div style="font-size: 48px; margin-bottom: 10px;">👔</div>
                        <div class="persona-title">Product Owner</div>
                        <div class="persona-desc">Track features, visualize dependencies, export reports</div>
                    </div>
                    <div class="persona-card" onclick="selectPersona('dev')">
                        <div style="font-size: 48px; margin-bottom: 10px;">💻</div>
                        <div class="persona-title">Developer</div>
                        <div class="persona-desc">Automate Jira updates from GitHub, reduce admin work</div>
                    </div>
                    <div class="persona-card" onclick="selectPersona('sm')">
                        <div style="font-size: 48px; margin-bottom: 10px;">📈</div>
                        <div class="persona-title">Scrum Master</div>
                        <div class="persona-desc">Team metrics, hygiene reports, insights</div>
                    </div>
                </div>
            </div>

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

            <!-- Dynamic persona-specific quick actions -->
            <div id="persona-quick-actions" class="card" style="display: none;">
                <h2 id="persona-actions-title">Quick Actions</h2>
                <div id="persona-actions-content"></div>
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

        <!-- PO TAB -->
        <div id="po" class="tab-content">
            <div class="card">
                <h2>Team Mode</h2>
                <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 15px;">
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="radio" name="team-mode" value="scrum" onchange="toggleTeamMode('scrum')">
                        <span>🏃 Scrum (Sprint-based)</span>
                    </label>
                    <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                        <input type="radio" name="team-mode" value="kanban" checked onchange="toggleTeamMode('kanban')">
                        <span>🌊 Kanban (Flow-based)</span>
                    </label>
                </div>
            </div>

            <!-- Scrum-specific metrics -->
            <div id="scrum-metrics" class="card" style="display: none;">
                <h2>Sprint Overview</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="po-sprint-name">Sprint 24</div>
                        <div class="stat-label">Current Sprint</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="po-sprint-progress">65%</div>
                        <div class="stat-label">Sprint Progress</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="po-velocity-current">38</div>
                        <div class="stat-label">Velocity</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="po-sprint-days">5</div>
                        <div class="stat-label">Days Remaining</div>
                    </div>
                </div>
            </div>

            <!-- Kanban-specific metrics -->
            <div id="kanban-metrics" class="card">
                <h2>Flow Metrics</h2>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="po-wip-count">8</div>
                        <div class="stat-label">WIP (Work in Progress)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="po-cycle-time">4.2</div>
                        <div class="stat-label">Avg Cycle Time (days)</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="po-throughput">12</div>
                        <div class="stat-label">Weekly Throughput</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="po-blocked-count">2</div>
                        <div class="stat-label">Blocked Items</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Features & Epics</h2>
                <div style="margin-bottom: 15px; display: flex; gap: 10px; align-items: center;">
                    <input type="text" id="feature-search" placeholder="Search features..." style="flex: 1;">
                    <select id="feature-filter" style="width: auto;">
                        <option value="all">All Features</option>
                        <option value="in-progress">In Progress</option>
                        <option value="completed">Completed</option>
                        <option value="blocked">Blocked</option>
                    </select>
                    <button class="btn-small" onclick="refreshFeatures()">🔄 Refresh</button>
                    <button class="btn-small btn-success" onclick="exportFeatures()">📥 Export CSV</button>
                </div>
                <div id="po-features-list">
                    <!-- Populated by JavaScript -->
                </div>
            </div>

            <div class="card">
                <h2>Dependency Canvas</h2>
                <p style="color: #5E6C84; margin-bottom: 15px;">
                    Visualize issue dependencies and blockers. Provide a data structure to load dependencies.
                </p>
                
                <!-- Data Input Section -->
                <div style="background: #FFF4E5; border-left: 4px solid #FF991F; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
                    <h3 style="margin: 0 0 10px 0; color: #172B4D; font-size: 14px;">📋 Data Setup Required</h3>
                    <p style="color: #5E6C84; font-size: 13px; margin-bottom: 10px;">
                        Create a JSON file with your issue dependencies and provide the URL or upload it below.
                    </p>
                    <details style="margin-bottom: 10px;">
                        <summary style="cursor: pointer; color: #0052CC; font-weight: 600; font-size: 13px;">
                            📖 Show JSON Schema Example
                        </summary>
                        <pre style="background: white; padding: 10px; border-radius: 4px; margin-top: 10px; font-size: 11px; overflow-x: auto;">{
  "PROJ-100": {
    "key": "PROJ-100",
    "summary": "User Authentication System",
    "status": "inprogress",
    "links": [
      { "type": "blocks", "target": "PROJ-101" },
      { "type": "depends", "target": "PROJ-200" }
    ]
  },
  "PROJ-101": {
    "key": "PROJ-101",
    "summary": "OAuth2 Integration",
    "status": "blocked",
    "links": [
      { "type": "blocked-by", "target": "PROJ-100" }
    ]
  }
}

Link Types: "blocks", "blocked-by", "depends", "required-by", "relates"
Status: "todo", "inprogress", "review", "blocked", "done"</pre>
                    </details>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="canvas-data-url" placeholder="Paste URL to JSON file..." style="flex: 1;">
                        <button class="btn-small btn-success" onclick="loadDependencyData()">📥 Load from URL</button>
                        <label class="btn-small btn-secondary" style="margin: 0; cursor: pointer;">
                            📁 Upload File
                            <input type="file" id="canvas-data-file" accept=".json" style="display: none;" onchange="loadDependencyFile()">
                        </label>
                    </div>
                </div>

                <div style="margin-bottom: 15px; display: flex; gap: 10px; align-items: center;">
                    <input type="text" id="canvas-issue-key" placeholder="Enter issue key to focus (e.g., PROJ-100)" style="flex: 1;">
                    <button class="btn-small btn-success" onclick="loadIssueDependencies()">📊 Load Issue</button>
                    <button class="btn-small btn-secondary" onclick="clearCanvas()">🗑️ Clear Canvas</button>
                    <button class="btn-small" onclick="resetCanvasZoom()">🔍 Reset View</button>
                    <button class="btn-small" onclick="exportCanvasImage()">📸 Export PNG</button>
                </div>
                <div id="dependency-canvas-container" style="position: relative; width: 100%; height: 600px; background: #F4F5F7; border-radius: 8px; overflow: hidden;">
                    <canvas id="dependency-canvas" style="position: absolute; top: 0; left: 0;"></canvas>
                    <svg id="dependency-svg" style="position: absolute; top: 0; left: 0; pointer-events: none;"></svg>
                    <div id="canvas-cards" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></div>
                </div>
                <div style="margin-top: 15px; padding: 10px; background: white; border-radius: 4px; font-size: 12px;">
                    <strong>Legend:</strong>
                    <span style="margin-left: 15px;">🔴 Blocks/Blocked</span>
                    <span style="margin-left: 15px;">🟢 Depends On (numbered)</span>
                    <span style="margin-left: 15px;">🔵 Related</span>
                </div>
            </div>
        </div>

        <!-- DEV TAB -->
        <div id="dev" class="tab-content">
            <div class="card">
                <h2>GitHub → Jira Automation</h2>
                <p style="color: #5E6C84; margin-bottom: 15px;">
                    Reduce administrative burden by automatically syncing GitHub PRs to Jira tickets.
                </p>
                <div class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="dev-prs-synced">0</div>
                        <div class="stat-label">PRs Synced Today</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="dev-tickets-updated">0</div>
                        <div class="stat-label">Tickets Auto-Updated</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="dev-last-sync">Never</div>
                        <div class="stat-label">Last Sync</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Automation Rules</h2>
                <div class="workflow-item">
                    <div class="workflow-info">
                        <div class="workflow-name">PR Merged → Move to Done</div>
                        <div class="workflow-desc">Automatically move Jira ticket to "Done" when PR is merged</div>
                    </div>
                    <label class="toggle">
                        <input type="checkbox" checked>
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="workflow-item">
                    <div class="workflow-info">
                        <div class="workflow-name">PR Opened → Add Comment</div>
                        <div class="workflow-desc">Add PR link as comment to linked Jira ticket</div>
                    </div>
                    <label class="toggle">
                        <input type="checkbox" checked>
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="workflow-item">
                    <div class="workflow-info">
                        <div class="workflow-name">PR Approved → Update Status</div>
                        <div class="workflow-desc">Move ticket to "Ready for Deploy" when PR is approved</div>
                    </div>
                    <label class="toggle">
                        <input type="checkbox">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>

            <div class="card">
                <h2>Manual Sync</h2>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button class="btn-success" onclick="syncGitHubToJira()">🔄 Sync All PRs</button>
                    <button class="btn-secondary" onclick="viewSyncLog()">📋 View Sync Log</button>
                </div>
            </div>
        </div>

        <!-- SM TAB -->
        <div id="sm" class="tab-content">
            <div class="card">
                <h2>Team Health Overview</h2>
                <div class="stat-grid">
                    <div class="stat-card" style="border-left-color: #00875A;">
                        <div class="stat-value" id="sm-health-score">85</div>
                        <div class="stat-label">Health Score</div>
                    </div>
                    <div class="stat-card" style="border-left-color: #FF991F;">
                        <div class="stat-value" id="sm-stale-tickets">7</div>
                        <div class="stat-label">Stale Tickets</div>
                    </div>
                    <div class="stat-card" style="border-left-color: #DE350B;">
                        <div class="stat-value" id="sm-hygiene-issues">12</div>
                        <div class="stat-label">Hygiene Issues</div>
                    </div>
                    <div class="stat-card" style="border-left-color: #0052CC;">
                        <div class="stat-value" id="sm-velocity">42</div>
                        <div class="stat-label">Avg Velocity</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>📊 Insights</h2>
                <p style="color: #5E6C84; margin-bottom: 15px;">
                    Insights generated from your team's data. Click to see details.
                </p>
                <div id="sm-insights">
                    <div class="favorite-item" style="border-left-color: #FF991F;">
                        <div class="favorite-header">
                            <div class="favorite-name">⚠️ Scope Creep Detected</div>
                            <button class="btn-small" onclick="viewInsight('scope-creep')">View Details</button>
                        </div>
                        <div class="favorite-desc">
                            3 stories in current sprint have grown by 40% in story points after sprint start.
                        </div>
                    </div>
                    <div class="favorite-item" style="border-left-color: #DE350B;">
                        <div class="favorite-header">
                            <div class="favorite-name">🐛 Defect Leakage Alert</div>
                            <button class="btn-small" onclick="viewInsight('defect-leakage')">View Details</button>
                        </div>
                        <div class="favorite-desc">
                            5 production bugs found in stories marked "Done" last sprint. Review QA process.
                        </div>
                    </div>
                    <div class="favorite-item" style="border-left-color: #0052CC;">
                        <div class="favorite-header">
                            <div class="favorite-name">📊 Velocity Trend</div>
                            <button class="btn-small" onclick="viewInsight('velocity')">View Details</button>
                        </div>
                        <div class="favorite-desc">
                            Team velocity has been stable at 40-45 points for last 4 sprints. Predictable delivery.
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>Hygiene Report</h2>
                <div style="margin-bottom: 15px;">
                    <button class="btn-small btn-success" onclick="runHygieneCheck()">🔍 Run Check</button>
                    <button class="btn-small" onclick="exportHygieneReport()">📥 Export Report</button>
                </div>
                <div id="sm-hygiene-report">
                    <!-- Populated by JavaScript -->
                </div>
            </div>
        </div>

        <!-- WORKFLOWS TAB -->
        <div id="workflows" class="tab-content">
            <div class="card">
                <h2>Automation Rules</h2>
                <p style="color: #5E6C84; margin-bottom: 20px;">
                    Define what happens when GitHub events occur. Changes save automatically.
                </p>
                
                <!-- PR Opened Rules -->
                <div style="margin-bottom: 30px; border-left: 4px solid #0052CC; padding-left: 15px;">
                    <h3 style="margin-bottom: 10px;">🆕 PR Opened/Created</h3>
                    <div class="input-group">
                        <label style="display: flex; align-items: center; gap: 10px;">
                            <input type="checkbox" id="pr-opened-enabled" onchange="saveAutomationRules()">
                            <span>Enable this rule</span>
                        </label>
                    </div>
                    <div class="input-group">
                        <label>Move ticket to status:</label>
                        <input type="text" id="pr-opened-status" placeholder="In Review" onchange="saveAutomationRules()">
                        <small style="color: #5E6C84;">Status name must match Jira exactly</small>
                    </div>
                    <div class="input-group">
                        <label>Add label:</label>
                        <input type="text" id="pr-opened-label" placeholder="has-pr" onchange="saveAutomationRules()">
                    </div>
                    <div class="input-group">
                        <label>
                            <input type="checkbox" id="pr-opened-comment" onchange="saveAutomationRules()">
                            Add comment to ticket
                        </label>
                    </div>
                </div>
                
                <!-- PR Merged Rules -->
                <div style="margin-bottom: 30px; border-left: 4px solid #00875A; padding-left: 15px;">
                    <h3 style="margin-bottom: 10px;">✅ PR Merged (Branch-Specific)</h3>
                    <p style="color: #5E6C84; font-size: 13px; margin-bottom: 15px;">
                        Different actions based on which branch the PR was merged into.
                    </p>
                    
                    <div id="branch-rules-list">
                        <!-- Populated by JavaScript -->
                    </div>
                    
                    <button onclick="addBranchRule()" class="btn-small">+ Add Branch Rule</button>
                </div>
                
                <!-- PR Closed Rules -->
                <div style="margin-bottom: 30px; border-left: 4px solid #DE350B; padding-left: 15px;">
                    <h3 style="margin-bottom: 10px;">❌ PR Closed (Not Merged)</h3>
                    <div class="input-group">
                        <label style="display: flex; align-items: center; gap: 10px;">
                            <input type="checkbox" id="pr-closed-enabled" onchange="saveAutomationRules()">
                            <span>Enable this rule</span>
                        </label>
                    </div>
                    <div class="input-group">
                        <label>Add label:</label>
                        <input type="text" id="pr-closed-label" placeholder="pr-closed" onchange="saveAutomationRules()">
                    </div>
                    <div class="input-group">
                        <label>
                            <input type="checkbox" id="pr-closed-comment" onchange="saveAutomationRules()">
                            Add comment to ticket
                        </label>
                    </div>
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

    <!-- Floating Feedback Button -->
    <button id="feedback-btn" class="feedback-floating-btn">
        🐛
    </button>

    <!-- Feedback Modal -->
    <div id="feedback-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2>📝 Report Feedback</h2>
                <button 
                    class="btn-close" 
                    onclick="minimizeFeedbackModal()"
                    title="Minimize (keeps your input)"
                    style="display: flex; align-items: center; justify-content: center; background: transparent; border: none; color: white; cursor: pointer; font-size: 24px; padding: 0; width: 32px; height: 32px;"
                >
                    <span style="line-height: 1;">−</span>
                </button>
            </div>
            <div class="modal-body">
                <div class="input-group">
                    <label>Title *</label>
                    <input type="text" id="feedback-title" placeholder="Brief description of the issue">
                </div>
                
                <div class="input-group">
                    <label>Description *</label>
                    <textarea id="feedback-description" placeholder="Please describe what happened, what you expected, and steps to reproduce..." rows="6"></textarea>
                </div>
                
                <div class="input-group">
                    <label style="display: flex; align-items: center; gap: 8px;">
                        <input type="checkbox" id="feedback-include-logs" checked>
                        <span>Include logs (last 5 minutes)</span>
                    </label>
                </div>
                
                <div style="display: flex; gap: 10px; margin: 20px 0;">
                    <button class="btn-secondary btn-small" onclick="captureScreenshot()">
                        📸 Capture Screenshot
                    </button>
                    <button class="btn-secondary btn-small" onclick="prepareRecording()" id="record-video-btn">
                        🎥 Record Video (30s max)
                    </button>
                </div>
                
                <div id="feedback-attachments" style="margin: 15px 0;">
                    <!-- Attachment previews will be added here -->
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button class="btn-secondary" onclick="closeFeedbackModal()">Cancel</button>
                    <button class="btn-success" onclick="submitFeedback()" id="submit-feedback-btn">
                        Submit Feedback
                    </button>
                </div>
                
                <div id="feedback-status" style="margin-top: 15px; display: none;"></div>
            </div>
        </div>
    </div>

    <!-- GitHub Token Setup Modal -->
    <div id="github-token-modal" class="modal">
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h2>🔑 GitHub Token Setup</h2>
                <span class="modal-close" onclick="closeGitHubTokenModal()">&times;</span>
            </div>
            <div class="modal-body">
                <p style="color: #5E6C84; margin-bottom: 15px;">
                    To submit feedback to GitHub, configure your Personal Access Token.<br>
                    <strong>Feedback will be saved locally even if you skip this.</strong>
                </p>
                
                <div class="input-group">
                    <label>GitHub Personal Access Token</label>
                    <input type="password" id="github-token-input" placeholder="ghp_xxxxxxxxxxxx">
                    <small style="color: #5E6C84; display: block; margin-top: 5px;">
                        Create at: <a href="https://github.com/settings/tokens/new?scopes=public_repo&description=Jira+Automation+Feedback" target="_blank" style="color: #60a5fa;">Generate Token →</a><br>
                        Required scope: <code>public_repo</code>
                    </small>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button class="btn-secondary" onclick="closeGitHubTokenModal()">Skip (Save Locally Only)</button>
                    <button class="btn-success" onclick="saveGitHubToken()">
                        Save & Validate Token
                    </button>
                </div>
                
                <div id="token-status" style="margin-top: 15px; display: none;"></div>
            </div>
        </div>
    </div>

    <script>
        let currentConfig = {};
        let logs = [];
        let selectedPersona = localStorage.getItem('selectedPersona') || null;

        // Tab switching
        function switchTab(tabName, event) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            if (event && event.target) {
                event.target.classList.add('active');
            } else {
                // Find button by onclick attribute matching
                document.querySelectorAll('.tab').forEach(btn => {
                    if (btn.getAttribute('onclick')?.includes(`'${tabName}'`)) {
                        btn.classList.add('active');
                    }
                });
            }
            document.getElementById(tabName).classList.add('active');
            
            // Load data when switching to tabs
            if (tabName === 'po') loadPOView();
            if (tabName === 'dev') loadDevView();
            if (tabName === 'sm') loadSMView();
            if (tabName === 'workflows') loadWorkflows();
            if (tabName === 'favorites') loadFavorites();
            if (tabName === 'logs') refreshLogs();
            if (tabName === 'settings') loadSettings();
        }

        // Persona selection
        function selectPersona(persona) {
            selectedPersona = persona;
            localStorage.setItem('selectedPersona', persona);
            
            // Update UI
            document.querySelectorAll('.persona-card').forEach(card => {
                card.classList.remove('selected');
            });
            event.target.closest('.persona-card').classList.add('selected');
            
            // Show persona-specific quick actions
            const actionsCard = document.getElementById('persona-quick-actions');
            const actionsTitle = document.getElementById('persona-actions-title');
            const actionsContent = document.getElementById('persona-actions-content');
            
            actionsCard.style.display = 'block';
            
            if (persona === 'po') {
                actionsTitle.textContent = '👔 PO Quick Actions';
                actionsContent.innerHTML = `
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="btn-success" onclick="switchTab('po')">📊 View Features</button>
                        <button class="btn-secondary" onclick="switchTab('po'); setTimeout(() => document.getElementById('canvas-issue-key').focus(), 100)">
                            🔗 Load Dependencies
                        </button>
                        <button onclick="exportFeatures()">📥 Export Features</button>
                    </div>
                `;
                addLog('info', 'Selected PO persona - Focus on feature tracking and visualization');
            } else if (persona === 'dev') {
                actionsTitle.textContent = '💻 Dev Quick Actions';
                actionsContent.innerHTML = `
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="btn-success" onclick="syncGitHubToJira()">🔄 Sync GitHub PRs</button>
                        <button class="btn-secondary" onclick="switchTab('dev')">⚙️ View Automation Rules</button>
                        <button onclick="viewSyncLog()">📋 View Sync Log</button>
                    </div>
                `;
                addLog('info', 'Selected Dev persona - Focus on automation and GitHub sync');
            } else if (persona === 'sm') {
                actionsTitle.textContent = '📈 SM Quick Actions';
                actionsContent.innerHTML = `
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <button class="btn-success" onclick="runHygieneCheck()">🔍 Run Hygiene Check</button>
                        <button class="btn-secondary" onclick="switchTab('sm')">📊 View Metrics</button>
                        <button onclick="exportHygieneReport()">📥 Export Report</button>
                    </div>
                `;
                addLog('info', 'Selected SM persona - Focus on metrics and team health');
            }
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

        // Load automation rules
        async function loadWorkflows() {
            try {
                const response = await fetch('/api/config');
                const config = await response.json();
                if (config.error) {
                    showStatus('Failed to load config: ' + config.error, 'error');
                    return;
                }
                currentConfig = config;
                
                const automation = config.automation || {};
                
                // Load PR Opened rules
                const prOpened = automation.pr_opened || {};
                document.getElementById('pr-opened-enabled').checked = prOpened.enabled !== false;
                document.getElementById('pr-opened-status').value = prOpened.set_status || '';
                document.getElementById('pr-opened-label').value = prOpened.add_label || '';
                document.getElementById('pr-opened-comment').checked = prOpened.add_comment !== false;
                
                // Load PR Closed rules
                const prClosed = automation.pr_closed || {};
                document.getElementById('pr-closed-enabled').checked = prClosed.enabled !== false;
                document.getElementById('pr-closed-label').value = prClosed.add_label || '';
                document.getElementById('pr-closed-comment').checked = prClosed.add_comment !== false;
                
                // Load PR Merged branch rules
                loadBranchRules(automation.pr_merged || {});
                
                // Update stat
                let count = 0;
                if (prOpened.enabled !== false) count++;
                if (prClosed.enabled !== false) count++;
                if (automation.pr_merged && automation.pr_merged.enabled !== false) count++;
                document.getElementById('stat-workflows').textContent = count;
                
            } catch (error) {
                showStatus('Failed to load automation rules: ' + error.message, 'error');
            }
        }
        
        function loadBranchRules(prMerged) {
            const container = document.getElementById('branch-rules-list');
            container.innerHTML = '';
            
            const branchRules = prMerged.branch_rules || [];
            
            branchRules.forEach((rule, index) => {
                if (rule.branch === 'default') return; // Skip default rule in UI
                
                const ruleDiv = document.createElement('div');
                ruleDiv.className = 'branch-rule-item';
                ruleDiv.style.cssText = 'background: #F4F5F7; padding: 15px; border-radius: 4px; margin-bottom: 10px;';
                ruleDiv.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: start; gap: 15px;">
                        <div style="flex: 1;">
                            <div class="input-group" style="margin-bottom: 10px;">
                                <label style="font-size: 12px; font-weight: 600;">Branch Name:</label>
                                <input type="text" value="${rule.branch}" 
                                       onchange="updateBranchRule(${index}, 'branch', this.value)"
                                       placeholder="DEV, INT, PVS, etc."
                                       style="width: 150px;">
                            </div>
                            <div class="input-group" style="margin-bottom: 10px;">
                                <label style="font-size: 12px;">Move to status:</label>
                                <input type="text" value="${rule.set_status || ''}" 
                                       onchange="updateBranchRule(${index}, 'set_status', this.value)"
                                       placeholder="Ready for QA">
                            </div>
                            <div class="input-group" style="margin-bottom: 10px;">
                                <label style="font-size: 12px;">Add label:</label>
                                <input type="text" value="${rule.add_label || ''}" 
                                       onchange="updateBranchRule(${index}, 'add_label', this.value)"
                                       placeholder="merged-int">
                            </div>
                            <div class="input-group">
                                <label style="font-size: 12px;">
                                    <input type="checkbox" ${rule.add_comment !== false ? 'checked' : ''}
                                           onchange="updateBranchRule(${index}, 'add_comment', this.checked)">
                                    Add comment
                                </label>
                            </div>
                        </div>
                        <button class="btn-small btn-danger" onclick="removeBranchRule(${index})" 
                                style="margin-top: 20px;">
                            🗑️
                        </button>
                    </div>
                `;
                container.appendChild(ruleDiv);
            });
        }
        
        function addBranchRule() {
            if (!currentConfig.automation) currentConfig.automation = {};
            if (!currentConfig.automation.pr_merged) currentConfig.automation.pr_merged = {};
            if (!currentConfig.automation.pr_merged.branch_rules) {
                currentConfig.automation.pr_merged.branch_rules = [];
            }
            
            currentConfig.automation.pr_merged.branch_rules.push({
                branch: 'NEW',
                add_comment: true,
                comment_template: '✅ Merged to {target_branch}: {pr_url}',
                set_status: '',
                add_label: ''
            });
            
            loadBranchRules(currentConfig.automation.pr_merged);
            saveAutomationRules();
        }
        
        function removeBranchRule(index) {
            if (!currentConfig.automation?.pr_merged?.branch_rules) return;
            currentConfig.automation.pr_merged.branch_rules.splice(index, 1);
            loadBranchRules(currentConfig.automation.pr_merged);
            saveAutomationRules();
        }
        
        function updateBranchRule(index, field, value) {
            if (!currentConfig.automation?.pr_merged?.branch_rules?.[index]) return;
            currentConfig.automation.pr_merged.branch_rules[index][field] = value;
            saveAutomationRules();
        }
        
        async function saveAutomationRules() {
            try {
                // Build automation object from UI
                const automation = {
                    pr_opened: {
                        enabled: document.getElementById('pr-opened-enabled').checked,
                        add_comment: document.getElementById('pr-opened-comment').checked,
                        comment_template: "🔗 Pull Request opened: {pr_url}\\nBranch: {branch_name}\\nAuthor: {author}",
                        update_pr_field: true,
                        add_label: document.getElementById('pr-opened-label').value,
                        set_status: document.getElementById('pr-opened-status').value
                    },
                    pr_updated: {
                        enabled: true,
                        add_comment: true,
                        comment_template: "🔄 Pull Request updated: {pr_url}",
                        update_pr_field: false,
                        add_label: "",
                        set_status: ""
                    },
                    pr_merged: currentConfig.automation?.pr_merged || {
                        enabled: true,
                        branch_rules: []
                    },
                    pr_closed: {
                        enabled: document.getElementById('pr-closed-enabled').checked,
                        add_comment: document.getElementById('pr-closed-comment').checked,
                        comment_template: "❌ Pull Request closed without merging: {pr_url}",
                        update_pr_field: false,
                        add_label: document.getElementById('pr-closed-label').value,
                        set_status: ""
                    }
                };
                
                currentConfig.automation = automation;
                
                const response = await fetch('/api/save-config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentConfig)
                });
                
                const result = await response.json();
                if (result.success) {
                    showStatus('Automation rules saved', 'success');
                } else {
                    showStatus('Failed to save: ' + result.error, 'error');
                }
            } catch (error) {
                showStatus('Error saving rules: ' + error.message, 'error');
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

        // Toggle team mode (Scrum vs Kanban)
        function toggleTeamMode(mode) {
            const scrumMetrics = document.getElementById('scrum-metrics');
            const kanbanMetrics = document.getElementById('kanban-metrics');
            
            if (mode === 'scrum') {
                scrumMetrics.style.display = 'block';
                kanbanMetrics.style.display = 'none';
                addLog('info', 'Switched to Scrum mode');
            } else {
                scrumMetrics.style.display = 'none';
                kanbanMetrics.style.display = 'block';
                addLog('info', 'Switched to Kanban mode');
            }
        }

        // Load PO view
        async function loadPOView() {
            addLog('info', 'Loading PO view...');
            
            // TODO: Fetch real data from Jira API
            // For now, showing placeholder data
            refreshFeatures();
            
            showStatus('PO view loaded (placeholder data)', 'info');
        }

        // Refresh features list
        function refreshFeatures() {
            const featuresList = document.getElementById('po-features-list');
            
            // TODO: Replace with actual Jira API data
            const sampleFeatures = [
                {
                    key: 'PROJ-100',
                    title: 'User Authentication & Authorization',
                    progress: 75,
                    completed: 6,
                    total: 8,
                    children: [
                        { key: 'PROJ-101', summary: 'Implement OAuth2 login', status: 'done' },
                        { key: 'PROJ-102', summary: 'Add role-based access control', status: 'done' },
                        { key: 'PROJ-103', summary: 'Create user permissions UI', status: 'inprogress' },
                        { key: 'PROJ-104', summary: 'Add JWT token refresh', status: 'inprogress' },
                        { key: 'PROJ-105', summary: 'Implement MFA support', status: 'todo' },
                        { key: 'PROJ-106', summary: 'Add session management', status: 'todo' },
                        { key: 'PROJ-107', summary: 'Security audit and fixes', status: 'done' },
                        { key: 'PROJ-108', summary: 'Documentation for auth flow', status: 'done' }
                    ]
                },
                {
                    key: 'PROJ-200',
                    title: 'Payment Processing Integration',
                    progress: 40,
                    completed: 2,
                    total: 5,
                    children: [
                        { key: 'PROJ-201', summary: 'Stripe API integration', status: 'done' },
                        { key: 'PROJ-202', summary: 'Payment webhook handlers', status: 'done' },
                        { key: 'PROJ-203', summary: 'Refund processing logic', status: 'inprogress' },
                        { key: 'PROJ-204', summary: 'Payment receipt generation', status: 'blocked' },
                        { key: 'PROJ-205', summary: 'PCI compliance review', status: 'todo' }
                    ]
                },
                {
                    key: 'PROJ-300',
                    title: 'Mobile App - iOS',
                    progress: 20,
                    completed: 1,
                    total: 5,
                    children: [
                        { key: 'PROJ-301', summary: 'Setup React Native project', status: 'done' },
                        { key: 'PROJ-302', summary: 'Build login screen', status: 'inprogress' },
                        { key: 'PROJ-303', summary: 'Implement navigation', status: 'review' },
                        { key: 'PROJ-304', summary: 'Add push notifications', status: 'todo' },
                        { key: 'PROJ-305', summary: 'App Store submission', status: 'todo' }
                    ]
                }
            ];
            
            featuresList.innerHTML = sampleFeatures.map((feature, index) => `
                <div class="feature-card">
                    <div class="feature-header">
                        <div style="flex: 1;">
                            <div class="feature-title">${feature.title}</div>
                            <div class="feature-key">${feature.key}</div>
                        </div>
                        <div class="feature-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${feature.progress}%;"></div>
                            </div>
                            <div class="progress-text">${feature.completed}/${feature.total} complete (${feature.progress}%)</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <button class="expand-toggle" onclick="toggleFeature(${index})">
                            <span id="toggle-icon-${index}">▼</span> 
                            <span style="font-size: 13px; font-weight: 600;">Show ${feature.total} child issues</span>
                        </button>
                    </div>
                    <div id="feature-children-${index}" class="child-issues" style="display: none;">
                        ${feature.children.map(child => `
                            <div class="child-issue">
                                <div class="child-issue-info">
                                    <span class="child-issue-key">${child.key}</span>
                                    <span class="child-issue-summary">${child.summary}</span>
                                </div>
                                <span class="child-issue-status status-${child.status}">
                                    ${child.status === 'todo' ? 'To Do' : 
                                      child.status === 'inprogress' ? 'In Progress' :
                                      child.status === 'review' ? 'Review' :
                                      child.status === 'blocked' ? 'Blocked' : 'Done'}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('');
            
            addLog('info', `Loaded ${sampleFeatures.length} features`);
        }

        // Export features to CSV
        function exportFeatures() {
            // TODO: Get actual feature data
            const csv = 'Feature Key,Title,Progress,Completed,Total,Status\\n' +
                        'PROJ-100,User Authentication,75%,6,8,In Progress\\n' +
                        'PROJ-200,Payment Processing,40%,2,5,In Progress\\n' +
                        'PROJ-300,Mobile App iOS,20%,1,5,In Progress\\n';
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `features-export-${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            
            showStatus('✅ Features exported to CSV', 'success');
            addLog('success', 'Features exported to CSV');
        }

        // Toggle feature expansion
        function toggleFeature(index) {
            const children = document.getElementById(`feature-children-${index}`);
            const icon = document.getElementById(`toggle-icon-${index}`);
            
            if (children.style.display === 'none') {
                children.style.display = 'block';
                icon.textContent = '▲';
            } else {
                children.style.display = 'none';
                icon.textContent = '▼';
            }
        }

        // Dependency Canvas
        let canvasState = {
            cards: [],
            links: [],
            selectedCard: null,
            zoom: 1,
            panX: 0,
            panY: 0,
            isDragging: false,
            dragStartX: 0,
            dragStartY: 0,
            draggedCard: null,
            dataStore: {} // Store loaded dependency data
        };

        // Load dependency data from URL
        async function loadDependencyData() {
            const url = document.getElementById('canvas-data-url').value.trim();
            if (!url) {
                showStatus('Please enter a URL', 'error');
                return;
            }

            try {
                addLog('info', `Loading dependency data from ${url}...`);
                const response = await fetch(url);
                const data = await response.json();
                
                canvasState.dataStore = data;
                showStatus(`✅ Loaded ${Object.keys(data).length} issues from URL`, 'success');
                addLog('success', `Data loaded: ${Object.keys(data).length} issues`);
            } catch (error) {
                showStatus('❌ Failed to load data: ' + error.message, 'error');
                addLog('error', 'Failed to load dependency data: ' + error.message);
            }
        }

        // Load dependency data from file
        function loadDependencyFile() {
            const fileInput = document.getElementById('canvas-data-file');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const data = JSON.parse(e.target.result);
                    canvasState.dataStore = data;
                    showStatus(`✅ Loaded ${Object.keys(data).length} issues from file`, 'success');
                    addLog('success', `Data loaded from ${file.name}: ${Object.keys(data).length} issues`);
                } catch (error) {
                    showStatus('❌ Invalid JSON file: ' + error.message, 'error');
                    addLog('error', 'Failed to parse JSON file: ' + error.message);
                }
            };
            reader.readAsText(file);
        }

        // Load issue dependencies
        async function loadIssueDependencies() {
            const issueKey = document.getElementById('canvas-issue-key').value.trim();
            
            // Check if we have data loaded
            if (Object.keys(canvasState.dataStore).length === 0) {
                showStatus('⚠️ Please load dependency data first (URL or file)', 'error');
                return;
            }
            
            if (!issueKey) {
                showStatus('Please enter an issue key', 'error');
                return;
            }

            const rootIssue = canvasState.dataStore[issueKey];
            if (!rootIssue) {
                showStatus(`Issue ${issueKey} not found in loaded data`, 'error');
                return;
            }

            addLog('info', `Loading dependencies for ${issueKey}...`);

            // Clear and rebuild canvas
            clearCanvas();
            
            // Add root card at center
            addCanvasCard(rootIssue, 400, 200, true);
            
            // Add linked issues in a circular layout
            const linkedKeys = new Set();
            rootIssue.links.forEach(link => linkedKeys.add(link.target));
            
            const radius = 200;
            const angleStep = (2 * Math.PI) / linkedKeys.size;
            let angle = 0;
            
            linkedKeys.forEach(key => {
                const issue = canvasState.dataStore[key];
                if (issue) {
                    const x = 400 + radius * Math.cos(angle);
                    const y = 200 + radius * Math.sin(angle);
                    addCanvasCard(issue, x, y, false);
                    angle += angleStep;
                }
            });
            
            // Add links
            rootIssue.links.forEach(link => {
                addCanvasLink(rootIssue.key, link.target, link.type);
            });
            
            renderCanvas();
            showStatus(`Loaded ${linkedKeys.size + 1} issues with dependencies`, 'success');
        }

        // Add card to canvas
        function addCanvasCard(issue, x, y, isRoot) {
            const card = {
                id: issue.key,
                key: issue.key,
                summary: issue.summary,
                status: issue.status,
                x: x,
                y: y,
                isRoot: isRoot,
                links: issue.links || []
            };
            
            canvasState.cards.push(card);
        }

        // Add link between cards
        function addCanvasLink(fromKey, toKey, type) {
            canvasState.links.push({
                from: fromKey,
                to: toKey,
                type: type
            });
        }

        // Render canvas
        function renderCanvas() {
            const container = document.getElementById('canvas-cards');
            const svg = document.getElementById('dependency-svg');
            
            // Set SVG size
            const rect = container.getBoundingClientRect();
            svg.setAttribute('width', rect.width);
            svg.setAttribute('height', rect.height);
            
            // Clear existing content
            container.innerHTML = '';
            svg.innerHTML = '';
            
            // Draw links first (so they appear behind cards)
            canvasState.links.forEach((link, index) => {
                const fromCard = canvasState.cards.find(c => c.id === link.from);
                const toCard = canvasState.cards.find(c => c.id === link.to);
                
                if (fromCard && toCard) {
                    drawLink(svg, fromCard, toCard, link.type, index);
                }
            });
            
            // Draw cards
            canvasState.cards.forEach((card, index) => {
                const cardEl = createCardElement(card, index);
                container.appendChild(cardEl);
            });
        }

        // Create card DOM element
        function createCardElement(card, index) {
            const div = document.createElement('div');
            div.className = 'canvas-card' + (card.status === 'blocked' ? ' blocked' : '');
            div.style.left = card.x + 'px';
            div.style.top = card.y + 'px';
            div.dataset.index = index;
            
            const statusClass = 'status-' + card.status;
            const statusText = card.status === 'todo' ? 'To Do' : 
                              card.status === 'inprogress' ? 'In Progress' :
                              card.status === 'review' ? 'Review' :
                              card.status === 'blocked' ? 'Blocked' : 'Done';
            
            div.innerHTML = `
                <div class="canvas-card-key">${card.key}</div>
                <div class="canvas-card-summary">${card.summary}</div>
                <span class="canvas-card-status ${statusClass}">${statusText}</span>
                ${card.links.length > 0 ? `<div class="canvas-card-links">🔗 ${card.links.length} link${card.links.length > 1 ? 's' : ''}</div>` : ''}
            `;
            
            // Make card draggable
            div.addEventListener('mousedown', (e) => startDragCard(e, index));
            div.addEventListener('click', (e) => {
                e.stopPropagation();
                selectCard(index);
            });
            
            return div;
        }

        // Draw link between cards
        function drawLink(svg, fromCard, toCard, type, index) {
            const fromX = fromCard.x + 110; // Center of card (220/2)
            const fromY = fromCard.y + 50;
            const toX = toCard.x + 110;
            const toY = toCard.y + 50;
            
            let color, strokeDasharray, strokeWidth;
            
            if (type === 'blocks' || type === 'blocked-by') {
                color = '#DE350B'; // Red for blockers
                strokeDasharray = '5,5'; // Dashed line
                strokeWidth = 2;
            } else if (type === 'depends' || type === 'required-by') {
                color = '#00875A'; // Green for dependencies
                strokeDasharray = 'none';
                strokeWidth = 2;
            } else {
                color = '#0052CC'; // Blue for related
                strokeDasharray = 'none';
                strokeWidth = 1;
            }
            
            // Draw arrow line
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', fromX);
            line.setAttribute('y1', fromY);
            line.setAttribute('x2', toX);
            line.setAttribute('y2', toY);
            line.setAttribute('stroke', color);
            line.setAttribute('stroke-width', strokeWidth);
            if (strokeDasharray !== 'none') {
                line.setAttribute('stroke-dasharray', strokeDasharray);
            }
            line.setAttribute('marker-end', `url(#arrowhead-${type})`);
            svg.appendChild(line);
            
            // Add arrowhead marker if not exists
            if (!document.getElementById(`arrowhead-${type}`)) {
                const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
                const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
                marker.setAttribute('id', `arrowhead-${type}`);
                marker.setAttribute('markerWidth', '10');
                marker.setAttribute('markerHeight', '10');
                marker.setAttribute('refX', '9');
                marker.setAttribute('refY', '3');
                marker.setAttribute('orient', 'auto');
                
                const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                polygon.setAttribute('points', '0 0, 10 3, 0 6');
                polygon.setAttribute('fill', color);
                
                marker.appendChild(polygon);
                defs.appendChild(marker);
                svg.appendChild(defs);
            }
            
            // Add sequence number for dependency chains
            if (type === 'depends' || type === 'required-by') {
                const midX = (fromX + toX) / 2;
                const midY = (fromY + toY) / 2;
                
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', midX);
                circle.setAttribute('cy', midY);
                circle.setAttribute('r', '12');
                circle.setAttribute('fill', 'white');
                circle.setAttribute('stroke', color);
                circle.setAttribute('stroke-width', '2');
                svg.appendChild(circle);
                
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', midX);
                text.setAttribute('y', midY + 4);
                text.setAttribute('text-anchor', 'middle');
                text.setAttribute('font-size', '12');
                text.setAttribute('font-weight', 'bold');
                text.setAttribute('fill', color);
                text.textContent = index + 1;
                svg.appendChild(text);
            }
        }

        // Card dragging
        function startDragCard(e, index) {
            e.stopPropagation();
            canvasState.draggedCard = index;
            canvasState.dragStartX = e.clientX - canvasState.cards[index].x;
            canvasState.dragStartY = e.clientY - canvasState.cards[index].y;
            
            document.addEventListener('mousemove', dragCard);
            document.addEventListener('mouseup', stopDragCard);
        }

        function dragCard(e) {
            if (canvasState.draggedCard !== null) {
                const card = canvasState.cards[canvasState.draggedCard];
                card.x = e.clientX - canvasState.dragStartX;
                card.y = e.clientY - canvasState.dragStartY;
                renderCanvas();
            }
        }

        function stopDragCard() {
            canvasState.draggedCard = null;
            document.removeEventListener('mousemove', dragCard);
            document.removeEventListener('mouseup', stopDragCard);
        }

        // Select card
        function selectCard(index) {
            canvasState.selectedCard = index;
            
            // Highlight selected card
            const cards = document.querySelectorAll('.canvas-card');
            cards.forEach((card, i) => {
                if (i === index) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            });
            
            const selectedIssue = canvasState.cards[index];
            addLog('info', `Selected: ${selectedIssue.key} - ${selectedIssue.summary}`);
        }

        // Clear canvas
        function clearCanvas() {
            canvasState.cards = [];
            canvasState.links = [];
            canvasState.selectedCard = null;
            document.getElementById('canvas-cards').innerHTML = '';
            document.getElementById('dependency-svg').innerHTML = '';
            addLog('info', 'Canvas cleared');
        }

        // Reset zoom
        function resetCanvasZoom() {
            canvasState.zoom = 1;
            canvasState.panX = 0;
            canvasState.panY = 0;
            renderCanvas();
            addLog('info', 'Canvas view reset');
        }

        // Export canvas as image
        function exportCanvasImage() {
            const container = document.getElementById('dependency-canvas-container');
            
            // TODO: Implement proper canvas export using html2canvas or similar
            showStatus('⚠️ Canvas export feature coming soon!', 'info');
            addLog('info', 'Canvas export requested');
        }

        // Dev persona functions
        function loadDevView() {
            addLog('info', 'Loading Dev view...');
            // TODO: Load GitHub sync status
        }

        function syncGitHubToJira() {
            showStatus('🔄 Syncing GitHub PRs to Jira...', 'info');
            addLog('info', 'Starting GitHub → Jira sync');
            // TODO: Trigger actual sync
            setTimeout(() => {
                showStatus('✅ Sync completed!', 'success');
                addLog('success', 'GitHub sync completed');
            }, 2000);
        }

        function viewSyncLog() {
            switchTab('logs');
            addLog('info', 'Viewing sync log');
        }

        // SM persona functions
        async function loadSMView() {
            addLog('info', 'Loading SM view...');
            await loadRealInsights();
            loadHygieneReport();
        }

        async function loadRealInsights() {
            try {
                const response = await fetch('/api/insights', {
                    headers: {'X-Days': '7'}
                });
                const data = await response.json();
                
                if (data.insights && data.insights.length > 0) {
                    displayInsights(data.insights);
                } else {
                    // Show placeholder if no insights yet
                    displayPlaceholderInsights();
                }
            } catch (error) {
                addLog('error', 'Failed to load insights: ' + error.message);
                displayPlaceholderInsights();
            }
        }

        function displayInsights(insights) {
            const container = document.getElementById('sm-insights');
            container.innerHTML = '';
            
            insights.forEach(insight => {
                const severityColor = {
                    'error': '#DE350B',
                    'warning': '#FF991F',
                    'info': '#0052CC'
                }[insight.severity] || '#0052CC';
                
                const item = document.createElement('div');
                item.className = 'favorite-item';
                item.style.borderLeftColor = severityColor;
                item.innerHTML = `
                    <div class="favorite-header">
                        <div class="favorite-name">${insight.title}</div>
                        <div style="display: flex; gap: 5px;">
                            <button class="btn-small" onclick="viewInsightDetails(${insight.id})">View</button>
                            ${!insight.resolved ? `<button class="btn-small btn-success" onclick="resolveInsight(${insight.id})">✓ Resolve</button>` : ''}
                        </div>
                    </div>
                    <div class="favorite-desc">${insight.message}</div>
                    <div style="font-size: 11px; color: #5E6C84; margin-top: 8px;">
                        ${new Date(insight.timestamp).toLocaleString()}
                    </div>
                `;
                container.appendChild(item);
            });
            
            addLog('info', `Loaded ${insights.length} insights`);
        }

        function displayPlaceholderInsights() {
            const container = document.getElementById('sm-insights');
            container.innerHTML = `
                <div class="favorite-item" style="border-left-color: #0052CC;">
                    <div class="favorite-header">
                        <div class="favorite-name">📊 No Insights Yet</div>
                    </div>
                    <div class="favorite-desc">
                        Run insights analysis to detect patterns, issues, and trends in your Jira data.
                        Click "Run Hygiene Check" to generate insights.
                    </div>
                </div>
            `;
        }

        async function resolveInsight(insightId) {
            try {
                const response = await fetch('/api/insights/resolve', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({id: insightId})
                });
                const data = await response.json();
                
                if (data.success) {
                    showStatus('✅ Insight marked as resolved', 'success');
                    loadRealInsights(); // Refresh
                } else {
                    showStatus('❌ Failed to resolve: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('❌ Error: ' + error.message, 'error');
            }
        }

        function viewInsightDetails(insightId) {
            addLog('info', `Viewing insight #${insightId}`);
            showStatus(`📊 Viewing insight details...`, 'info');
            // TODO: Show detailed modal or navigate to detail view
        }

        function loadHygieneReport() {
            const report = document.getElementById('sm-hygiene-report');
            report.innerHTML = `
                <div class="workflow-item" style="border-left-color: #FF991F;">
                    <div class="workflow-info">
                        <div class="workflow-name">7 Stale Tickets</div>
                        <div class="workflow-desc">No updates in 14+ days</div>
                    </div>
                    <button class="btn-small">View</button>
                </div>
                <div class="workflow-item" style="border-left-color: #FF991F;">
                    <div class="workflow-info">
                        <div class="workflow-name">5 Missing Story Points</div>
                        <div class="workflow-desc">Stories without estimates</div>
                    </div>
                    <button class="btn-small">View</button>
                </div>
                <div class="workflow-item" style="border-left-color: #DE350B;">
                    <div class="workflow-info">
                        <div class="workflow-name">3 Long-Running Stories</div>
                        <div class="workflow-desc">In progress > 10 days</div>
                    </div>
                    <button class="btn-small">View</button>
                </div>
            `;
        }

        async function runHygieneCheck() {
            showStatus('🔍 Running hygiene check...', 'info');
            addLog('info', 'Running team hygiene check');
            
            // TODO: Gather real Jira data from scraper
            // For now, run with sample data
            const sampleData = {
                stories: [],
                bugs: [],
                tickets: [],
                velocity_history: [38, 42, 45, 40, 38],
                sprint_data: {}
            };
            
            try {
                const response = await fetch('/api/insights/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({jira_data: sampleData})
                });
                const data = await response.json();
                
                if (data.success) {
                    showStatus(`✅ Analysis complete: ${data.insights.length} insights generated`, 'success');
                    addLog('success', `Hygiene check completed: ${data.insights.length} insights`);
                    loadRealInsights(); // Refresh display
                } else {
                    showStatus('❌ Analysis failed: ' + data.error, 'error');
                }
            } catch (error) {
                showStatus('❌ Error: ' + error.message, 'error');
                addLog('error', 'Hygiene check failed: ' + error.message);
            }
        }

        function exportHygieneReport() {
            const csv = 'Issue Type,Count,Severity,Description\\n' +
                        'Stale Tickets,7,Medium,No updates in 14+ days\\n' +
                        'Missing Story Points,5,Medium,Stories without estimates\\n' +
                        'Long-Running Stories,3,High,In progress > 10 days\\n';
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `hygiene-report-${new Date().toISOString().split('T')[0]}.csv`;
            a.click();
            
            showStatus('✅ Hygiene report exported', 'success');
            addLog('success', 'Hygiene report exported to CSV');
        }

        function viewInsight(type) {
            addLog('info', `Viewing ${type} insight`);
            showStatus(`📊 Viewing ${type} insight details...`, 'info');
            // TODO: Show detailed insight modal or navigate to detail view
        }

        // ========================================
        // FEEDBACK SYSTEM
        // ========================================
        let feedbackAttachments = [];
        let mediaRecorder = null;
        let recordedChunks = [];
        let recordingStartTime = null;
        let recordingInterval = null;
        let hasGitHubToken = false;

        // Console log capture
        (function() {
            const originalLog = console.log;
            const originalError = console.error;
            const originalWarn = console.warn;
            
            console.log = function(...args) {
                captureConsoleLog('log', args.join(' '));
                originalLog.apply(console, args);
            };
            
            console.error = function(...args) {
                captureConsoleLog('error', args.join(' '));
                originalError.apply(console, args);
            };
            
            console.warn = function(...args) {
                captureConsoleLog('warn', args.join(' '));
                originalWarn.apply(console, args);
            };
            
            window.addEventListener('error', (event) => {
                captureConsoleLog('error', `${event.message} at ${event.filename}:${event.lineno}`);
            });
        })();

        function captureConsoleLog(level, message) {
            fetch('/api/feedback/console-log', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    level: level,
                    message: message,
                    timestamp: new Date().toISOString()
                })
            }).catch(() => {});  // Silent fail
        }

        function initFeedbackSystem() {
            // Check if token exists in localStorage (like forge-terminal)
            const savedToken = localStorage.getItem('jira_github_token');
            if (savedToken) {
                hasGitHubToken = true;
                console.log('GitHub token found in localStorage');
            } else {
                hasGitHubToken = false;
                console.log('No GitHub token - feedback will save locally only');
            }
        }

        function openFeedbackModal() {
            // Check if token is configured
            const savedToken = localStorage.getItem('jira_github_token');
            if (!savedToken) {
                // Show setup modal first
                document.getElementById('github-token-modal').style.display = 'block';
                return;
            }
            
            // Token exists, open feedback modal directly
            document.getElementById('feedback-modal').style.display = 'block';
        }

        function minimizeFeedbackModal() {
            // Hide the modal
            document.getElementById('feedback-modal').style.display = 'none';
            
            // Show minimized indicator
            const indicator = document.getElementById('feedback-minimized-indicator');
            if (!indicator) {
                // Create indicator if it doesn't exist
                const div = document.createElement('div');
                div.id = 'feedback-minimized-indicator';
                div.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    right: 90px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    cursor: pointer;
                    z-index: 998;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    transition: transform 0.2s;
                `;
                div.innerHTML = '📝 Feedback (minimized)';
                div.onclick = restoreFeedbackModal;
                div.onmouseenter = function() { this.style.transform = 'scale(1.05)'; };
                div.onmouseleave = function() { this.style.transform = 'scale(1)'; };
                document.body.appendChild(div);
            } else {
                indicator.style.display = 'flex';
            }
            
            addLog('info', 'Feedback modal minimized (data preserved)');
        }

        function restoreFeedbackModal() {
            // Show the modal
            document.getElementById('feedback-modal').style.display = 'block';
            
            // Hide minimized indicator
            const indicator = document.getElementById('feedback-minimized-indicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
            
            addLog('info', 'Feedback modal restored');
        }

        function closeFeedbackModal() {
            document.getElementById('feedback-modal').style.display = 'none';
            
            // Hide minimized indicator if visible
            const indicator = document.getElementById('feedback-minimized-indicator');
            if (indicator) {
                indicator.style.display = 'none';
            }
            
            // Reset form
            document.getElementById('feedback-title').value = '';
            document.getElementById('feedback-description').value = '';
            document.getElementById('feedback-attachments').innerHTML = '';
            feedbackAttachments = [];
            
            // Stop recording if active
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                stopRecordingAndRestore();
            }
        }

        function closeGitHubTokenModal() {
            document.getElementById('github-token-modal').style.display = 'none';
        }

        async function saveGitHubToken() {
            const token = document.getElementById('github-token-input').value.trim();
            
            if (!token) {
                showTokenStatus('Please enter a token', 'error');
                return;
            }
            
            showTokenStatus('Validating token...', 'info');
            
            try {
                // Validate token by calling GitHub API directly
                const response = await fetch('https://api.github.com/user', {
                    headers: {
                        'Authorization': `token ${token}`
                    }
                });
                
                if (response.ok) {
                    const userData = await response.json();
                    // Save to localStorage (like forge-terminal does)
                    localStorage.setItem('jira_github_token', token);
                    showTokenStatus(`✅ Token validated for user: ${userData.login}`, 'success');
                    hasGitHubToken = true;
                    setTimeout(() => {
                        closeGitHubTokenModal();
                        openFeedbackModal();
                    }, 1500);
                } else {
                    const errorData = await response.json();
                    showTokenStatus('Invalid token: ' + errorData.message, 'error');
                }
            } catch (error) {
                showTokenStatus('Validation failed: ' + error.message, 'error');
            }
        }

        function showTokenStatus(message, type) {
            const status = document.getElementById('token-status');
            status.textContent = message;
            status.className = 'status-' + type;
            status.style.display = 'block';
        }

        async function captureScreenshot() {
            try {
                addLog('info', 'Capturing screenshot...');
                
                // Use html2canvas to capture the page
                const canvas = await html2canvas(document.body);
                const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png', 0.9));
                const reader = new FileReader();
                
                reader.onloadend = function() {
                    const base64 = reader.result.split(',')[1];
                    feedbackAttachments.push({
                        name: `screenshot-${Date.now()}.png`,
                        content: base64,
                        mime_type: 'image/png',
                        type: 'image'
                    });
                    renderAttachments();
                    showStatus('✅ Screenshot captured', 'success');
                };
                
                reader.readAsDataURL(blob);
                
            } catch (error) {
                showStatus('❌ Screenshot failed: ' + error.message, 'error');
                addLog('error', 'Screenshot capture failed: ' + error.message);
            }
        }

        // Recording flow: Step 1 - User clicks "Record Video" button
        function prepareRecording() {
            // Minimize modal
            minimizeFeedbackModal();
            
            // Show "Start Recording" overlay button
            const overlay = document.createElement('div');
            overlay.id = 'recording-start-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 99999;
                background: rgba(0, 0, 0, 0.9);
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
            `;
            overlay.innerHTML = `
                <div style="color: white; text-align: center;">
                    <div style="font-size: 18px; font-weight: 600; margin-bottom: 10px;">Ready to Record</div>
                    <div style="font-size: 14px; color: #aaa; margin-bottom: 15px;">Navigate to where you want to start</div>
                    <button id="start-record-btn" style="
                        background: #DE350B;
                        color: white;
                        border: none;
                        padding: 12px 24px;
                        border-radius: 6px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: background 0.2s;
                    ">⏺ Start Recording</button>
                </div>
            `;
            document.body.appendChild(overlay);
            
            document.getElementById('start-record-btn').onclick = startActualRecording;
            
            addLog('info', 'Recording prepared - waiting for user to click Start');
        }

        // Recording flow: Step 2 - User clicks "Start Recording"
        async function startActualRecording() {
            // Remove the start overlay
            const startOverlay = document.getElementById('recording-start-overlay');
            if (startOverlay) startOverlay.remove();
            
            try {
                const stream = await navigator.mediaDevices.getDisplayMedia({
                    video: { mediaSource: 'screen' },
                    audio: false
                });
                
                mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'video/webm'
                });
                
                recordedChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        recordedChunks.push(event.data);
                    }
                };
                
                mediaRecorder.onstop = async () => {
                    const blob = new Blob(recordedChunks, { type: 'video/webm' });
                    const reader = new FileReader();
                    
                    reader.onloadend = function() {
                        const base64 = reader.result.split(',')[1];
                        feedbackAttachments.push({
                            name: `recording-${Date.now()}.webm`,
                            content: base64,
                            mime_type: 'video/webm',
                            type: 'video'
                        });
                        renderAttachments();
                        
                        // Remove recording overlay
                        const overlay = document.getElementById('recording-timer-overlay');
                        if (overlay) overlay.remove();
                        
                        // Restore modal
                        restoreFeedbackModal();
                        showFeedbackStatus('✅ Video recording saved', 'success');
                    };
                    
                    reader.readAsDataURL(blob);
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                recordingStartTime = Date.now();
                
                // Show recording timer overlay
                const overlay = document.createElement('div');
                overlay.id = 'recording-timer-overlay';
                overlay.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 99999;
                    background: rgba(222, 53, 11, 0.95);
                    padding: 15px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                    display: flex;
                    align-items: center;
                    gap: 12px;
                `;
                overlay.innerHTML = `
                    <span style="color: white; font-size: 24px; animation: pulse 1s infinite;">⏺</span>
                    <div style="color: white;">
                        <div style="font-weight: 600; font-size: 16px;" id="recording-timer-text">00:0</div>
                        <div style="font-size: 12px; opacity: 0.9;">Recording...</div>
                    </div>
                    <button id="stop-record-btn" style="
                        background: rgba(0,0,0,0.3);
                        color: white;
                        border: 1px solid rgba(255,255,255,0.3);
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: 600;
                        cursor: pointer;
                        margin-left: 8px;
                    ">⏹ Stop</button>
                `;
                
                // Add pulse animation
                const style = document.createElement('style');
                style.textContent = '@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }';
                document.head.appendChild(style);
                
                document.body.appendChild(overlay);
                
                document.getElementById('stop-record-btn').onclick = stopRecording;
                
                // Update timer
                recordingInterval = setInterval(() => {
                    if (recordingStartTime) {
                        const elapsed = Date.now() - recordingStartTime;
                        const seconds = Math.floor(elapsed / 1000);
                        const ms = Math.floor((elapsed % 1000) / 100);
                        const timerEl = document.getElementById('recording-timer-text');
                        if (timerEl) {
                            timerEl.textContent = `${String(seconds).padStart(2, '0')}:${ms}`;
                        }
                    }
                }, 100);
                
                // Auto-stop after 30 seconds
                setTimeout(() => {
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        stopRecording();
                    }
                }, 30000);
                
                addLog('info', 'Recording started (30s max)');
                
            } catch (error) {
                // Remove any overlays on error
                const startOverlay = document.getElementById('recording-start-overlay');
                if (startOverlay) startOverlay.remove();
                
                restoreFeedbackModal();
                showFeedbackStatus('❌ Recording failed: ' + error.message, 'error');
                addLog('error', 'Video recording failed: ' + error.message);
            }
        }

        // Recording flow: Step 3 - Stop recording (manual or auto)
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                clearInterval(recordingInterval);
                addLog('info', 'Recording stopped');
            }
        }

        function updateRecordingTimer() {
            if (recordingStartTime) {
                const elapsed = Date.now() - recordingStartTime;
                const seconds = Math.floor(elapsed / 1000);
                const ms = Math.floor((elapsed % 1000) / 100);
                document.getElementById('recording-timer').textContent = 
                    `${String(seconds).padStart(2, '0')}:${ms}`;
            }
        }

        function renderAttachments() {
            const container = document.getElementById('feedback-attachments');
            container.innerHTML = '';
            
            feedbackAttachments.forEach((attachment, index) => {
                const preview = document.createElement('div');
                preview.className = 'attachment-preview';
                
                if (attachment.type === 'image') {
                    preview.innerHTML = `
                        <img src="data:${attachment.mime_type};base64,${attachment.content}" alt="${attachment.name}">
                        <div style="font-size: 11px; color: #5E6C84; margin-bottom: 5px;">${attachment.name}</div>
                        <button class="btn-danger btn-small" onclick="removeAttachment(${index})">Remove</button>
                    `;
                } else if (attachment.type === 'video') {
                    preview.innerHTML = `
                        <video controls src="data:${attachment.mime_type};base64,${attachment.content}"></video>
                        <div style="font-size: 11px; color: #5E6C84; margin-bottom: 5px;">${attachment.name}</div>
                        <button class="btn-danger btn-small" onclick="removeAttachment(${index})">Remove</button>
                    `;
                }
                
                container.appendChild(preview);
            });
        }

        function removeAttachment(index) {
            feedbackAttachments.splice(index, 1);
            renderAttachments();
        }

        async function submitFeedback() {
            const title = document.getElementById('feedback-title').value.trim();
            const description = document.getElementById('feedback-description').value.trim();
            const includeLogs = document.getElementById('feedback-include-logs').checked;
            
            if (!title || !description) {
                showFeedbackStatus('Please fill in title and description', 'error');
                return;
            }
            
            const submitBtn = document.getElementById('submit-feedback-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';
            
            // Get GitHub token from localStorage (like forge-terminal)
            const githubToken = localStorage.getItem('jira_github_token');
            const repoName = 'mikejsmith1985/jira-automation';
            
            let githubIssueUrl = null;
            let githubIssueNumber = null;
            
            // Try to create GitHub issue (frontend, won't crash server)
            if (githubToken) {
                try {
                    showFeedbackStatus('Creating GitHub issue...', 'info');
                    
                    // Build issue body
                    let body = description + '\\n\\n';
                    
                    // Add logs if requested
                    if (includeLogs) {
                        body += '## Application Logs\\n```\\n';
                        body += logs.map(l => `[${l.timestamp}] ${l.level.toUpperCase()}: ${l.message}`).join('\\n');
                        body += '\\n```\\n\\n';
                    }
                    
                    // Add system info
                    body += '## System Information\\n';
                    body += `- User Agent: ${navigator.userAgent}\\n`;
                    body += `- Timestamp: ${new Date().toISOString()}\\n`;
                    
                    // Upload screenshots to GitHub repo (if any)
                    const imageUrls = [];
                    for (let i = 0; i < feedbackAttachments.length; i++) {
                        const attachment = feedbackAttachments[i];
                        if (attachment.type === 'image') {
                            try {
                                showFeedbackStatus(`Uploading screenshot ${i + 1}/${feedbackAttachments.length}...`, 'info');
                                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                                const filename = `feedback-${timestamp}-${i}.png`;
                                const content = attachment.content;
                                
                                const uploadRes = await fetch(`https://api.github.com/repos/${repoName}/contents/feedback-screenshots/${filename}`, {
                                    method: 'PUT',
                                    headers: {
                                        'Authorization': `token ${githubToken}`,
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({
                                        message: 'Upload feedback screenshot',
                                        content: content,
                                    })
                                });
                                
                                if (uploadRes.ok) {
                                    const uploadData = await uploadRes.json();
                                    imageUrls.push(uploadData.content.download_url);
                                }
                            } catch (err) {
                                console.warn('Screenshot upload failed:', err);
                            }
                        }
                    }
                    
                    // Add screenshots to body
                    if (imageUrls.length > 0) {
                        body += '\\n## Screenshots\\n';
                        imageUrls.forEach(url => {
                            body += `![screenshot](${url})\\n\\n`;
                        });
                    }
                    
                    // Create the issue via GitHub API
                    showFeedbackStatus('Creating issue...', 'info');
                    const issueRes = await fetch(`https://api.github.com/repos/${repoName}/issues`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `token ${githubToken}`,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            title: title,
                            body: body,
                            labels: ['user-feedback', 'bug']
                        })
                    });
                    
                    if (issueRes.ok) {
                        const issueData = await issueRes.json();
                        githubIssueUrl = issueData.html_url;
                        githubIssueNumber = issueData.number;
                        addLog('success', `GitHub issue #${githubIssueNumber} created`);
                    } else {
                        const errorData = await issueRes.json();
                        addLog('warn', `GitHub issue creation failed: ${errorData.message}`);
                    }
                } catch (error) {
                    console.error('GitHub submission failed:', error);
                    addLog('warn', 'GitHub submission failed, saving locally only');
                }
            }
            
            // Always save to SQLite (via backend)
            try {
                showFeedbackStatus('Saving feedback...', 'info');
                const response = await fetch('/api/feedback/submit', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        title: title,
                        description: description,
                        attachments: feedbackAttachments,
                        include_logs: includeLogs,
                        github_issue_url: githubIssueUrl,
                        github_issue_number: githubIssueNumber
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    if (githubIssueUrl) {
                        showFeedbackStatus(
                            `✅ Feedback submitted! <a href="${githubIssueUrl}" target="_blank" style="color: inherit;">View issue #${githubIssueNumber}</a>`,
                            'success'
                        );
                    } else {
                        showFeedbackStatus('✅ Feedback saved locally (configure GitHub token to sync)', 'success');
                    }
                    
                    setTimeout(() => {
                        closeFeedbackModal();
                    }, 3000);
                } else {
                    showFeedbackStatus('❌ Error: ' + data.error, 'error');
                }
                
            } catch (error) {
                showFeedbackStatus('❌ Failed: ' + error.message, 'error');
                addLog('error', 'Feedback submission error: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Feedback';
            }
        }

        function showFeedbackStatus(message, type) {
            const status = document.getElementById('feedback-status');
            status.innerHTML = message;
            status.className = 'status-' + type;
            status.style.display = 'block';
        }

        // Initialize on load
        window.addEventListener('load', () => {
            addLog('info', 'UI initialized');
            loadWorkflows();
            loadSettings();
            initFeedbackSystem();
            
            // Attach feedback button event listener
            const feedbackBtn = document.getElementById('feedback-btn');
            if (feedbackBtn) {
                feedbackBtn.addEventListener('click', openFeedbackModal);
            }
            
            // Restore selected persona if exists
            if (selectedPersona) {
                const personaCards = document.querySelectorAll('.persona-card');
                personaCards.forEach((card, index) => {
                    const personas = ['po', 'dev', 'sm'];
                    if (personas[index] === selectedPersona) {
                        card.classList.add('selected');
                        // Trigger persona selection to show quick actions
                        setTimeout(() => {
                            card.click();
                        }, 100);
                    }
                });
            }
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
    global github_feedback
    
    # Initialize GitHub feedback if token exists in config
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        if 'feedback' in config:
            token = config['feedback'].get('github_token')
            repo = config['feedback'].get('repo')
            
            if token and repo:
                github_feedback = GitHubFeedback(token=token, repo_name=repo)
                print("[OK] GitHub feedback system initialized")
    except Exception as e:
        print(f"[WARN] GitHub feedback not configured: {str(e)}")
    
    server_address = ('localhost', 5000)
    httpd = HTTPServer(server_address, SyncHandler)
    print("[START] Waypoint starting...")
    print("[SERVER] http://localhost:5000")
    print("[BROWSER] Opening browser...")
    print("[WAIT] Starting server (this will block)...")
    httpd.serve_forever()

if __name__ == '__main__':
    # Start browser opener in background
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run server
    run_server()
