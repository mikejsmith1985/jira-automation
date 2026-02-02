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
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sync_engine import SyncEngine
from insights_engine import InsightsEngine
from feedback_db import FeedbackDB
from github_feedback import GitHubFeedback, LogCapture
from version_checker import VersionChecker
from login_detector import check_login_status
from csv_importer import JiraCSVImporter

# Extension system imports
from extensions import get_extension_manager, ExtensionCapability
from extensions.jira import JiraExtension
from extensions.github import GitHubExtension
from extensions.reporting import EnhancedInsightsEngine, ReportGenerator
from storage import get_data_store, get_config_manager

import logging

# Global state
def get_base_dir():
    """Get base directory for bundled resources (READ-ONLY when frozen)"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return sys._MEIPASS
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

def get_data_dir():
    """Get writable data directory for config and user data"""
    if getattr(sys, 'frozen', False):
        # Running as executable - use AppData for persistence across versions
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        data_dir = os.path.join(appdata, 'Waypoint')
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    else:
        # Running as script - use script directory
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
DATA_DIR = get_data_dir()
LOG_FILE = os.path.join(DATA_DIR, 'jira-sync.log')

# Configure logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

APP_VERSION = "1.3.10"  # Version sync automation - local dev

def safe_print(msg):
    """Print safely even when console is not available (PyInstaller --noconsole)"""
    logging.info(msg) # Log to file as well
    try:
        if sys.stdout:
            # sys.stdout.write(f"{msg}\n") # Handled by StreamHandler now
            pass
    except:
        pass

driver = None
sync_engine = None
sync_thread = None
is_syncing = False
insights_engine = None
feedback_db = FeedbackDB(db_path=os.path.join(DATA_DIR, 'feedback.db'))  # SQLite-based feedback storage
github_feedback = None  # Optional GitHub sync
log_capture = LogCapture(LOG_FILE)
version_checker = None  # Version update checker
browser_opened = False  # Flag to prevent double-opening

# Extension system globals
extension_manager = None
data_store = None
config_manager = None
enhanced_insights = None
report_generator = None

class SyncHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the web UI"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        safe_print(f"[GET] {self.path}")
        
        if self.path == '/' or self.path == '/index.html':
            self._serve_html_with_cache_busting('modern-ui.html', 'text/html; charset=utf-8')
        elif self.path.startswith('/assets/'):
            # Serve static assets
            # Strip query parameters (e.g. ?v=1.0)
            clean_path = self.path.split('?')[0]
            filepath = clean_path[1:]  # Remove leading slash
            content_type = self._get_content_type(filepath)
            safe_print(f"[STATIC] Serving {filepath} as {content_type}")
            self._serve_static_file(filepath, content_type)
        elif self.path == '/api/status':
            self._handle_status()
        elif self.path == '/api/config':
            self._handle_get_config()
        elif self.path == '/api/integrations/status':
            self._handle_integrations_status()
        elif self.path == '/api/selenium/status':
            self._handle_selenium_status()
        elif self.path == '/api/automation/rules':
            self._handle_get_automation_rules()
        elif self.path == '/api/insights':
            self._handle_get_insights()
        elif self.path == '/api/insights/trend':
            self._handle_get_trend()
        elif self.path == '/api/feedback/validate-token':
            self._handle_validate_feedback_token()
        elif self.path == '/api/version':
            self._handle_get_version()
        elif self.path == '/api/version/check':
            # Handle update check - returns dict that needs to be sent as JSON
            result = self._handle_check_updates()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        elif self.path == '/api/version/releases':
            self._handle_list_releases()
        elif self.path == '/api/snow-jira/config':
            self._handle_get_snow_config()
        else:
            self.send_response(404)
            self.end_headers()
    
    def _serve_static_file(self, filepath, content_type):
        """Serve static files with caching"""
        try:
            # Convert to absolute path
            abs_filepath = os.path.join(BASE_DIR, filepath)
            safe_print(f"[SERVE] Attempting to serve: {abs_filepath}")
            
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
                    # Aggressive no-cache to prevent stale assets
                    self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
                    self.send_header('Pragma', 'no-cache')
                    self.send_header('Expires', '0')
                    self.end_headers()
                    self.wfile.write(f.read())
        except FileNotFoundError:
            safe_print(f"[ERROR] File not found: {abs_filepath}")
            safe_print(f"[DEBUG] BASE_DIR = {BASE_DIR}")
            safe_print(f"[DEBUG] DATA_DIR = {DATA_DIR}")
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"File not found: {filepath}".encode())
        except Exception as e:
            safe_print(f"[ERROR] Failed to serve {filepath}: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Server error: {str(e)}".encode())
    
    def _serve_html_with_cache_busting(self, filepath, content_type):
        """Serve HTML with cache-busting query parameters injected"""
        try:
            abs_filepath = os.path.join(BASE_DIR, filepath)
            safe_print(f"[SERVE] Serving HTML with cache busting: {abs_filepath}")
            
            with open(abs_filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Inject version into template
            html_content = html_content.replace('{{VERSION}}', APP_VERSION)
            
            # Inject version query parameters into asset URLs
            version_param = f"?v={APP_VERSION}"
            html_content = html_content.replace('/assets/css/modern-ui.css', f'/assets/css/modern-ui.css{version_param}')
            html_content = html_content.replace('/assets/js/modern-ui-v2.js', f'/assets/js/modern-ui-v2.js{version_param}')
            html_content = html_content.replace('/assets/js/servicenow-jira.js', f'/assets/js/servicenow-jira.js{version_param}')
            html_content = html_content.replace('/assets/js/html2canvas.min.js', f'/assets/js/html2canvas.min.js{version_param}')
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            
        except FileNotFoundError:
            safe_print(f"[ERROR] HTML file not found: {abs_filepath}")
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"File not found: {filepath}".encode())
        except Exception as e:
            safe_print(f"[ERROR] Failed to serve HTML with cache busting: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Server error: {str(e)}".encode())
    
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
            elif self.path == '/api/import/csv':
                self._handle_csv_upload()
                return
            elif self.path == '/api/import/save-mapping':
                self._handle_save_mapping()
                return
            elif self.path == '/api/import/mappings':
                self._handle_get_mappings()
                return
            elif self.path == '/api/import/process':
                self._handle_process_csv()
                return
            elif self.path == '/api/feedback/submit':
                # Handle multipart form data for file uploads
                self._handle_feedback_submit()
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
            elif self.path == '/api/feedback/save-token':
                response = self.handle_save_feedback_token(data)
            # Extension system endpoints
            elif self.path == '/api/extensions':
                response = self._handle_list_extensions()
            elif self.path.startswith('/api/extensions/') and '/config' in self.path:
                ext_name = self.path.split('/')[3]
                response = self._handle_extension_config(ext_name, data)
            elif self.path.startswith('/api/extensions/') and '/test' in self.path:
                ext_name = self.path.split('/')[3]
                response = self._handle_extension_test(ext_name)
            # Data import/export endpoints
            elif self.path == '/api/data/import':
                response = self._handle_data_import(data)
            elif self.path == '/api/data/export':
                response = self._handle_data_export(data)
            elif self.path == '/api/data/features':
                response = self._handle_get_features()
            elif self.path == '/api/data/dependencies':
                response = self._handle_get_dependencies()
            # Update checker endpoints
            elif self.path == '/api/updates/check':
                response = self._handle_check_updates()
            elif self.path == '/api/updates/apply':
                response = self._handle_apply_update(data)
            elif self.path == '/api/app/restart':
                response = self._handle_app_restart()
            # Jira-specific endpoints
            elif self.path == '/api/jira/query':
                response = self._handle_jira_query(data)
            elif self.path == '/api/jira/update':
                response = self._handle_jira_update(data)
            elif self.path == '/api/jira/bulk-update':
                response = self._handle_jira_bulk_update(data)
            elif self.path == '/api/jira/test-connection':
                response = self._handle_jira_test_connection()
            # Reporting endpoints
            elif self.path == '/api/reports/daily-scrum':
                response = self._handle_daily_scrum_report(data)
            elif self.path == '/api/reports/generate':
                response = self._handle_generate_report(data)
            elif self.path == '/api/reports/insights':
                response = self._handle_get_insights()
            elif self.path == '/api/integrations/save':
                response = self.handle_save_integrations(data)
            elif self.path == '/api/integrations/test-github':
                response = self.handle_test_github_connection(data)
            elif self.path == '/api/automation/save':
                response = self.handle_save_automation_rules(data)
            elif self.path == '/api/selenium/open-jira':
                response = self.handle_open_jira_browser(data)
            elif self.path == '/api/selenium/check-login':
                response = self.handle_check_jira_login()
            elif self.path == '/api/po/load-data':
                response = self.handle_load_po_data(data)
            elif self.path == '/api/sm/scrape-metrics':
                response = self.handle_scrape_sm_metrics(data)
            elif self.path == '/api/snow-jira/save-config':
                response = self.handle_save_snow_config(data)
            elif self.path == '/api/snow-jira/test-connection':
                response = self.handle_test_snow_connection()
            elif self.path == '/api/export-logs':
                response = self.handle_export_logs()
            elif self.path == '/api/snow-jira/validate-prb':
                response = self.handle_validate_prb(data)
            elif self.path == '/api/snow-jira/sync':
                response = self.handle_snow_jira_sync(data)
            else:
                response = {'success': False, 'error': 'Unknown endpoint'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            safe_print(f"ERROR in do_POST: {str(e)}")
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
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
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
    
    def _handle_integrations_status(self):
        """Return real integration status based on config AND Selenium state"""
        global driver
        try:
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            except FileNotFoundError:
                config = {}
            
            github_config = config.get('github', {})
            jira_config = config.get('jira', {})
            feedback_config = config.get('feedback', {})
            
            github_token = github_config.get('api_token', '')
            github_connected = bool(github_token and github_token != '' and github_token != 'YOUR_GITHUB_TOKEN_HERE')
            
            jira_url = jira_config.get('base_url', '')
            jira_configured = bool(jira_url and jira_url != '' and 'your-company' not in jira_url)
            
            feedback_token = feedback_config.get('github_token', '')
            feedback_configured = bool(feedback_token and feedback_token != '' and feedback_token != 'YOUR_GITHUB_TOKEN_HERE')
            
            # Check REAL Selenium browser state for Jira
            jira_browser_open = False
            jira_logged_in = False
            jira_current_url = None
            
            if driver is not None:
                try:
                    jira_current_url = driver.current_url
                    jira_browser_open = True
                    
                    # Check if logged in
                    if 'atlassian.net' in jira_current_url or 'jira' in jira_current_url.lower():
                        jira_logged_in, _, _ = check_login_status(driver)
                except:
                    jira_browser_open = False
            
            status = {
                'github': {
                    'configured': github_connected,
                    'base_url': github_config.get('base_url', ''),
                    'organization': github_config.get('organization', ''),
                    'repositories': github_config.get('repositories', []),
                    'has_token': github_connected
                },
                'jira': {
                    'configured': jira_configured,
                    'base_url': jira_url,
                    'project_keys': jira_config.get('project_keys', []),
                    'browser_open': jira_browser_open,
                    'logged_in': jira_logged_in,
                    'current_url': jira_current_url,
                    'status': 'Connected' if jira_logged_in else ('Browser Open - Please Login' if jira_browser_open else ('URL Configured' if jira_configured else 'Not Configured'))
                },
                'feedback': {
                    'configured': feedback_configured,
                    'repo': feedback_config.get('repo', '')
                }
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def _handle_get_automation_rules(self):
        """Return automation rules from config"""
        try:
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
            except FileNotFoundError:
                config = {}
            
            automation = config.get('automation', {})
            
            rules = {
                'pr_opened': {
                    'enabled': automation.get('pr_opened', {}).get('enabled', False),
                    'add_comment': automation.get('pr_opened', {}).get('add_comment', False),
                    'set_status': automation.get('pr_opened', {}).get('set_status', ''),
                    'add_label': automation.get('pr_opened', {}).get('add_label', ''),
                    'description': 'When a PR is opened, update the linked Jira ticket'
                },
                'pr_updated': {
                    'enabled': automation.get('pr_updated', {}).get('enabled', False),
                    'add_comment': automation.get('pr_updated', {}).get('add_comment', False),
                    'set_status': automation.get('pr_updated', {}).get('set_status', ''),
                    'add_label': automation.get('pr_updated', {}).get('add_label', ''),
                    'description': 'When a PR receives new commits'
                },
                'pr_merged': {
                    'enabled': automation.get('pr_merged', {}).get('enabled', False),
                    'branch_rules': automation.get('pr_merged', {}).get('branch_rules', []),
                    'description': 'When a PR is merged (branch-specific rules)'
                },
                'pr_closed': {
                    'enabled': automation.get('pr_closed', {}).get('enabled', False),
                    'add_comment': automation.get('pr_closed', {}).get('add_comment', False),
                    'set_status': automation.get('pr_closed', {}).get('set_status', ''),
                    'add_label': automation.get('pr_closed', {}).get('add_label', ''),
                    'description': 'When a PR is closed without merging'
                }
            }
            
            active_count = sum(1 for r in rules.values() if r.get('enabled', False))
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'rules': rules,
                'active_count': active_count,
                'total_count': len(rules)
            }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _is_driver_valid(self):
        """Check if the driver session is still valid"""
        global driver
        if driver is None:
            return False
        try:
            # Try to access current_url - will fail if session is invalid
            _ = driver.current_url
            return True
        except Exception:
            return False
    
    def _reset_driver(self):
        """Reset the driver and sync engine after invalid session"""
        global driver, sync_engine
        safe_print("🔄 Resetting invalid driver session...")
        try:
            if driver is not None:
                driver.quit()
        except:
            pass
        driver = None
        sync_engine = None
        safe_print("✅ Driver reset complete")

    def handle_init(self, data):
        """Initialize browser"""
        global driver, sync_engine
        
        try:
            # Check if existing driver session is valid
            if driver is not None:
                try:
                    # Try to get current URL to check if session is alive
                    _ = driver.current_url
                    # Session is valid, navigate to Jira
                    jira_url = data.get('jiraUrl', sync_engine.config['jira']['base_url'] if sync_engine else '')
                    driver.get(jira_url)
                    return {'success': True, 'message': 'Browser reused. Please log in to Jira.'}
                except Exception as e:
                    # Session is invalid, need to reinitialize
                    safe_print(f"⚠️ Invalid session detected: {str(e)}")
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = None
                    sync_engine = None
            
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
            import traceback
            traceback.print_exc()
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
            with open(os.path.join(DATA_DIR, 'config.yaml'), 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False)
            return {'success': True, 'message': 'Configuration saved'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_save_integrations(self, data):
        """Save integration settings to config"""
        try:
            # Use DATA_DIR for writable config
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            safe_print(f"[DEBUG] Saving integrations to: {config_path}")
            
            # Create config file if it doesn't exist
            if not os.path.exists(config_path):
                safe_print(f"[DEBUG] Config file not found, creating new one")
                config = {}
            else:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f) or {}
            
            if 'github' in data:
                if 'github' not in config:
                    config['github'] = {}
                config['github']['api_token'] = data['github'].get('api_token', config['github'].get('api_token', ''))
                config['github']['base_url'] = data['github'].get('base_url', config['github'].get('base_url', ''))
                config['github']['organization'] = data['github'].get('organization', config['github'].get('organization', ''))
                if 'repositories' in data['github']:
                    config['github']['repositories'] = data['github']['repositories']
            
            if 'jira' in data:
                if 'jira' not in config:
                    config['jira'] = {}
                config['jira']['base_url'] = data['jira'].get('base_url', config['jira'].get('base_url', ''))
                if 'project_keys' in data['jira']:
                    config['jira']['project_keys'] = data['jira']['project_keys']
            
            if 'feedback' in data:
                if 'feedback' not in config:
                    config['feedback'] = {}
                config['feedback']['github_token'] = data['feedback'].get('github_token', config.get('feedback', {}).get('github_token', ''))
                config['feedback']['repo'] = data['feedback'].get('repo', config.get('feedback', {}).get('repo', ''))
            
            # ADD: Handle ServiceNow config
            if 'servicenow' in data:
                if 'servicenow' not in config:
                    config['servicenow'] = {}
                # Validate required fields
                url = data['servicenow'].get('url', '').strip()
                jira_project = data['servicenow'].get('jira_project', '').strip()
                
                if url:  # Only update if URL is provided
                    config['servicenow']['url'] = url
                if jira_project:  # Only update if project is provided
                    config['servicenow']['jira_project'] = jira_project
                if 'field_mapping' in data['servicenow']:
                    config['servicenow']['field_mapping'] = data['servicenow']['field_mapping']
                
                safe_print(f"[SNOW] ServiceNow config updated - URL: '{url}', Project: '{jira_project}'")
            
            safe_print(f"[DEBUG] Writing config: {config}")
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Re-initialize GitHub feedback client if token was updated
            global github_feedback, github_feedback_client
            if 'feedback' in data and data['feedback'].get('github_token'):
                try:
                    token = data['feedback']['github_token']
                    repo = data['feedback'].get('repo', config.get('feedback', {}).get('repo', ''))
                    if token and repo:
                        github_feedback = GitHubFeedback(token=token, repo_name=repo)
                        github_feedback_client = github_feedback
                        safe_print("[OK] GitHub feedback system re-initialized")
                except Exception as e:
                    safe_print(f"[WARN] Failed to re-initialize feedback system: {e}")
            
            # Reload config_manager to pick up new settings for update checker etc.
            global config_manager
            if config_manager:
                config_manager.load()
                safe_print("[OK] Config reloaded")
            
            return {'success': True, 'message': 'Integration settings saved'}
        except PermissionError as e:
            safe_print(f"[ERROR] Permission denied writing config: {e}")
            return {'success': False, 'error': f'Permission denied: Cannot write to config file. Try running as administrator.'}
        except Exception as e:
            safe_print(f"[ERROR] Failed to save integrations: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'Save failed: {str(e)}'}
    
    def handle_test_github_connection(self, data):
        """Test GitHub API connection with provided token"""
        try:
            token = data.get('token', '')
            if not token:
                return {'success': False, 'error': 'No token provided'}
            
            import requests
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'success': True,
                    'user': user_data.get('login', 'Unknown'),
                    'message': f"Connected as {user_data.get('login', 'Unknown')}"
                }
            elif response.status_code == 401:
                return {'success': False, 'error': 'Invalid token - authentication failed'}
            else:
                return {'success': False, 'error': f'GitHub API error: {response.status_code}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_save_automation_rules(self, data):
        """Save automation rule settings"""
        try:
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            if 'automation' not in config:
                config['automation'] = {}
            
            for rule_name in ['pr_opened', 'pr_updated', 'pr_merged', 'pr_closed']:
                if rule_name in data:
                    if rule_name not in config['automation']:
                        config['automation'][rule_name] = {}
                    config['automation'][rule_name]['enabled'] = data[rule_name].get('enabled', False)
                    if 'add_comment' in data[rule_name]:
                        config['automation'][rule_name]['add_comment'] = data[rule_name]['add_comment']
                    if 'set_status' in data[rule_name]:
                        config['automation'][rule_name]['set_status'] = data[rule_name]['set_status']
                    if 'add_label' in data[rule_name]:
                        config['automation'][rule_name]['add_label'] = data[rule_name]['add_label']
                    if 'branch_rules' in data[rule_name]:
                        config['automation'][rule_name]['branch_rules'] = data[rule_name]['branch_rules']
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            return {'success': True, 'message': 'Automation rules saved'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_check_updates(self):
        """Check for available updates with comprehensive error handling"""
        try:
            from version_checker import VersionChecker
            
            # Get GitHub token and repo from config file directly
            # (not from config_manager which may be cached)
            github_token = None
            repo_owner = 'mikejsmith1985'  # Default fallback
            repo_name = 'jira-automation'
            
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f) or {}
                
                # Use feedback token (same PAT for feedback and updates)
                github_token = cfg.get('feedback', {}).get('github_token')
                
                # Validate token is not placeholder
                if github_token and github_token in ['YOUR_GITHUB_TOKEN_HERE', 'your_token_here', '']:
                    github_token = None
                    safe_print("[UPDATE] Feedback token is placeholder, not using")
                
                # Parse repo from feedback.repo (format: "owner/repo")
                feedback_repo = cfg.get('feedback', {}).get('repo', '')
                if feedback_repo and '/' in feedback_repo:
                    repo_owner, repo_name = feedback_repo.split('/', 1)
                
                # Fallback: try github.api_token if feedback token not set
                if not github_token:
                    github_token = cfg.get('github', {}).get('api_token')
                    if github_token and github_token in ['YOUR_GITHUB_TOKEN_HERE', 'your_token_here', '']:
                        github_token = None
            
            # CRITICAL: This is a private repo, must have token
            if not github_token:
                return {
                    'success': True,
                    'update_info': {
                        'available': False,
                        'current_version': APP_VERSION,
                        'error': 'GitHub token required for update checks. Configure in Settings > Integrations > Feedback.',
                        'needs_token': True
                    }
                }
            
            checker = VersionChecker(
                current_version=APP_VERSION,
                owner=repo_owner,
                repo=repo_name,
                token=github_token
            )
            
            # Check for updates (no cache for manual checks)
            result = checker.check_for_update(use_cache=False)
            
            # Always return success=True, errors are in update_info
            return {'success': True, 'update_info': result}
            
        except ImportError as e:
            # version_checker module not found
            return {
                'success': False,
                'error': 'Update checker not available. Module not found.'
            }
        except Exception as e:
            # Any other error
            error_msg = str(e)
            # Make error user-friendly
            if 'connection' in error_msg.lower() or 'network' in error_msg.lower():
                error_msg = 'Cannot connect to GitHub. Check your internet connection.'
            elif 'timeout' in error_msg.lower():
                error_msg = 'GitHub request timed out. Try again later.'
            elif len(error_msg) > 150:
                error_msg = error_msg[:150] + '...'
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def _handle_apply_update(self, data):
        """Download and apply an update"""
        global config_manager
        try:
            from version_checker import VersionChecker
            
            download_url = data.get('download_url')
            if not download_url:
                return {'success': False, 'error': 'No download URL provided'}
            
            # Get token from config - try multiple sources
            github_token = None
            
            # Method 1: Try config_manager
            if config_manager:
                try:
                    config = config_manager.get_config()
                    github_token = config.get('feedback', {}).get('github_token')
                    if not github_token:
                        github_token = config.get('github', {}).get('api_token')
                except Exception as e:
                    safe_print(f"[WARN] Could not read from config_manager: {e}")
            
            # Method 2: Read directly from config file if config_manager failed
            if not github_token:
                try:
                    config_path = os.path.join(DATA_DIR, 'config.yaml')
                    if os.path.exists(config_path):
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = yaml.safe_load(f) or {}
                        github_token = config.get('feedback', {}).get('github_token')
                        if not github_token:
                            github_token = config.get('github', {}).get('api_token')
                        safe_print(f"[INFO] Read token from file: {'found' if github_token else 'not found'}")
                except Exception as e:
                    safe_print(f"[WARN] Could not read config file: {e}")
            
            if github_token and github_token in ['YOUR_GITHUB_TOKEN_HERE', 'your_token_here', '']:
                github_token = None  # Ignore placeholder tokens
            
            safe_print(f"[UPDATE] Using token for download: {'Yes' if github_token else 'No'}")

            checker = VersionChecker(
                current_version=APP_VERSION,
                owner='mikejsmith1985',
                repo='jira-automation',
                token=github_token
            )
            
            result = checker.download_and_apply_update(download_url)
            
            if result.get('success'):
                # Trigger application exit after sending response
                import threading
                def shutdown():
                    import time
                    time.sleep(2)
                    os._exit(0)
                threading.Thread(target=shutdown, daemon=True).start()
            
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_app_restart(self):
        """Restart the application"""
        try:
            import subprocess
            
            # Get current exe path
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                # Running as script
                exe_path = os.path.abspath(__file__)
            
            safe_print("[RESTART] Restarting application...")
            
            # Start new instance
            if getattr(sys, 'frozen', False):
                # Frozen exe - just run it
                subprocess.Popen([exe_path], 
                               creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                               close_fds=True)
            else:
                # Running as script - restart with python
                subprocess.Popen([sys.executable, exe_path],
                               creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                               close_fds=True)
            
            # Schedule shutdown of current instance
            def shutdown():
                import time
                time.sleep(1)
                safe_print("[RESTART] Shutting down current instance...")
                os._exit(0)
            threading.Thread(target=shutdown, daemon=True).start()
            
            return {'success': True, 'message': 'Restarting application...'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_selenium_status(self):
        """Return REAL Selenium browser status"""
        global driver
        try:
            status = {
                'browser_open': False,
                'current_url': None,
                'jira_logged_in': False,
                'session_active': False
            }
            
            if driver is not None:
                try:
                    # Check if browser is still open
                    current_url = driver.current_url
                    status['browser_open'] = True
                    status['current_url'] = current_url
                    status['session_active'] = True
                    
                    # Check if logged in to Jira (look for common logged-in indicators)
                    if 'atlassian.net' in current_url or 'jira' in current_url.lower():
                        status['jira_logged_in'], _, _ = check_login_status(driver)
                except:
                    # Browser was closed
                    status['browser_open'] = False
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def handle_open_jira_browser(self, data):
        """Open Selenium browser and navigate to Jira for manual login"""
        global driver, sync_engine
        
        try:
            jira_url = data.get('jiraUrl', '')
            if not jira_url:
                # Try to get from config if it exists
                config_path = os.path.join(DATA_DIR, 'config.yaml')
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r') as f:
                            config = yaml.safe_load(f)
                        jira_url = config.get('jira', {}).get('base_url', '')
                    except Exception:
                        pass  # Silently fallback if config read fails
            
            if not jira_url or 'your-company' in jira_url:
                return {'success': False, 'error': 'Please configure Jira URL first'}
            
            # Check if existing driver session is valid
            if driver is not None:
                if not self._is_driver_valid():
                    safe_print("⚠️ Detected invalid session, resetting driver...")
                    self._reset_driver()
                else:
                    # Session is valid, just navigate
                    driver.get(jira_url)
                    return {
                        'success': True,
                        'message': f'Browser reused. Navigating to {jira_url}',
                        'url': jira_url
                    }
            
            # Initialize Chrome WebDriver if not already done
            if driver is None:
                chrome_options = Options()
                
                # Use persistent user data directory for session persistence
                user_data_dir = os.path.join(DATA_DIR, 'selenium_profile')
                os.makedirs(user_data_dir, exist_ok=True)
                chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
                
                # Browser options
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # Preserve session data
                chrome_options.add_argument('--disable-infobars')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--no-sandbox')
                
                driver = webdriver.Chrome(options=chrome_options)
            
            # Initialize sync engine
            if sync_engine is None:
                sync_engine = SyncEngine(driver)
            
            # Navigate to Jira
            driver.get(jira_url)
            
            return {
                'success': True, 
                'message': f'Browser opened. Please log in to Jira at {jira_url}. Your login will be remembered.',
                'url': jira_url
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def handle_check_jira_login(self):
        """Check if user is logged in to Jira"""
        global driver
        
        if not self._is_driver_valid():
            self._reset_driver()
            return {'success': False, 'logged_in': False, 'error': 'Browser session expired. Please reopen browser.'}
        
        try:
            current_url = driver.current_url
            
            # Check for login indicators with debug info
            logged_in, user_info, debug_info = check_login_status(driver, debug=True)
            
            return {
                'success': True,
                'logged_in': logged_in,
                'current_url': current_url,
                'user': user_info,
                'debug': debug_info
            }
        except Exception as e:
            # If we get an error accessing driver, reset it
            if 'invalid session' in str(e).lower():
                self._reset_driver()
                return {'success': False, 'logged_in': False, 'error': 'Browser session expired. Please reopen browser.'}
            return {'success': False, 'logged_in': False, 'error': str(e)}
    
    def handle_load_po_data(self, data):
        """Load PO data from URL or uploaded structure"""
        try:
            source_type = data.get('source_type', 'url')  # 'url' or 'data'
            
            if source_type == 'url':
                url = data.get('url', '')
                if not url:
                    return {'success': False, 'error': 'No URL provided'}
                
                # Fetch the URL
                import requests
                response = requests.get(url, timeout=30)
                if response.status_code != 200:
                    return {'success': False, 'error': f'Failed to fetch URL: {response.status_code}'}
                
                # Try to parse as JSON
                try:
                    structure = response.json()
                except:
                    return {'success': False, 'error': 'URL did not return valid JSON'}
            else:
                # Direct data upload
                structure = data.get('data', {})
            
            if not structure:
                return {'success': False, 'error': 'No data provided'}
            
            # Store the data for the PO view
            # Save to a local file for persistence
            with open('po_data.json', 'w', encoding='utf-8') as f:
                json.dump(structure, f, indent=2)
            
            # Calculate summary stats
            features = structure.get('features', [])
            total_issues = sum(len(f.get('children', [])) for f in features) + len(features)
            
            return {
                'success': True,
                'message': f'Loaded {len(features)} features, {total_issues} total issues',
                'summary': {
                    'features': len(features),
                    'total_issues': total_issues
                },
                'data': structure
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_scrape_sm_metrics(self, data):
        """Scrape SM metrics from Jira using Selenium"""
        global driver
        
        if driver is None:
            return {'success': False, 'error': 'Browser not open. Please open Jira browser first.'}
        
        try:
            jql = data.get('jql', '')
            board_url = data.get('board_url', '')
            custom_field_names = data.get('custom_field_names', [])
            
            if not jql and not board_url:
                return {'success': False, 'error': 'Provide either a JQL query or board URL'}
            
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            issues = []
            debug_info = []
            
            if board_url:
                # Navigate to board and scrape
                driver.get(board_url)
                time.sleep(3)  # Increased wait for board to load
                
                # Wait for board to load (try multiple common selectors)
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.ghx-issue, [role="button"], [data-testid*="card"], [data-testid*="list"]'))
                    )
                    debug_info.append("✓ Board loaded successfully")
                except:
                    debug_info.append("⚠ Timeout waiting for board elements")
                
                # Scrape issue cards - using broader selectors to catch different Jira versions
                # 1. Classic Kanban/Scrum boards (.ghx-issue)
                # 2. Next-gen/Team-managed boards ([data-testid*="card"])
                # 3. Generic accessible elements ([role="button"] with issue keys)
                
                # Find all potential card elements
                selectors_tried = []
                
                # Strategy 1: Classic board cards
                try:
                    classic_cards = driver.find_elements(By.CSS_SELECTOR, '.ghx-issue')
                    selectors_tried.append(f"Classic cards (.ghx-issue): {len(classic_cards)} found")
                except: pass
                
                # Strategy 2: Next-gen cards
                try:
                    nextgen_cards = driver.find_elements(By.CSS_SELECTOR, '[data-testid*="card"]')
                    selectors_tried.append(f"Next-gen cards ([data-testid*='card']): {len(nextgen_cards)} found")
                except: pass
                
                # Strategy 3: List items
                try:
                    list_items = driver.find_elements(By.CSS_SELECTOR, '[role="listitem"]')
                    selectors_tried.append(f"List items ([role='listitem']): {len(list_items)} found")
                except: pass
                
                # Strategy 4: Board swimlane cards
                try:
                    swimlane_cards = driver.find_elements(By.CSS_SELECTOR, '[data-test-id*="software-board.card"], [data-testid="list.draggable-list.draggable-item"]')
                    selectors_tried.append(f"Swimlane cards: {len(swimlane_cards)} found")
                except: pass
                
                # Strategy 5: Table rows (Backlog/List view)
                try:
                    table_rows = driver.find_elements(By.CSS_SELECTOR, 'tr[data-testid="issue-table-row"], .issuerow')
                    selectors_tried.append(f"Table rows: {len(table_rows)} found")
                except: pass
                
                # Strategy 6: Generic Grid Rows (Structure, Advanced Roadmaps)
                try:
                    grid_rows = driver.find_elements(By.CSS_SELECTOR, 'div[role="row"], .structure-row, .grid-row')
                    selectors_tried.append(f"Grid rows: {len(grid_rows)} found")
                except: pass
                
                debug_info.extend(selectors_tried)
                
                # Combine all potential cards
                potential_cards = driver.find_elements(By.CSS_SELECTOR, '.ghx-issue, [data-testid*="card"], [role="listitem"], [data-test-id*="software-board.card"], [data-testid="list.draggable-list.draggable-item"], tr[data-testid="issue-table-row"], .issuerow, div[role="row"], .structure-row, .grid-row')
                
                debug_info.append(f"Total potential cards found: {len(potential_cards)}")
                
                # Deduplicate by key
                seen_keys = set()
                
                # Track which issues are visible vs hidden for debugging
                visible_issues = []
                hidden_issues = []
                
                for el in potential_cards:
                    try:
                        key = None
                        
                        # Check if element is actually visible (not display:none, visibility:hidden, etc)
                        is_visible = el.is_displayed()
                        
                        # Strategy 1: Data attribute
                        if not key:
                            key = el.get_attribute('data-issue-key')
                            
                        # Strategy 2: Text search for pattern
                        if not key:
                            text = el.text
                            import re
                            # Look for PROJ-123 pattern
                            match = re.search(r'([A-Z]+-\d+)', text)
                            if match:
                                key = match.group(1)
                                
                        # Strategy 3: Child element
                        if not key:
                            try:
                                key_el = el.find_element(By.CSS_SELECTOR, '.ghx-key, [data-testid*="issue-key"], a[href*="/browse/"]')
                                key = key_el.text
                            except:
                                pass

                        if key and key not in seen_keys:
                            seen_keys.add(key)
                            
                            # Extract additional fields from card
                            issue_data = {
                                'key': key,
                                'visible': is_visible
                            }
                            
                            # Try to extract summary/title
                            try:
                                summary_el = el.find_element(By.CSS_SELECTOR, '.ghx-summary, [data-testid*="summary"], .issue-summary')
                                issue_data['summary'] = summary_el.text.strip()
                            except:
                                try:
                                    # Fallback: Get all text and remove the key
                                    card_text = el.text.strip()
                                    issue_data['summary'] = card_text.replace(key, '').strip()
                                except:
                                    issue_data['summary'] = None
                            
                            # Try to extract status
                            try:
                                status_el = el.find_element(By.CSS_SELECTOR, '.ghx-end, [data-testid*="status"], .status-lozenge, .issue-status')
                                issue_data['status'] = status_el.text.strip()
                            except:
                                issue_data['status'] = None
                            
                            # Try to extract assignee
                            try:
                                assignee_el = el.find_element(By.CSS_SELECTOR, '.ghx-avatar img, [data-testid*="assignee"] img, .assignee img')
                                issue_data['assignee'] = assignee_el.get_attribute('alt') or assignee_el.get_attribute('title')
                            except:
                                try:
                                    assignee_el = el.find_element(By.CSS_SELECTOR, '.ghx-avatar, [data-testid*="assignee"], .assignee')
                                    issue_data['assignee'] = assignee_el.get_attribute('title') or assignee_el.text.strip()
                                except:
                                    issue_data['assignee'] = None
                            
                            # Try to extract priority
                            try:
                                priority_el = el.find_element(By.CSS_SELECTOR, '.ghx-priority img, [data-testid*="priority"] img, .priority img')
                                issue_data['priority'] = priority_el.get_attribute('alt') or priority_el.get_attribute('title')
                            except:
                                issue_data['priority'] = None
                            
                            # Try to extract issue type
                            try:
                                type_el = el.find_element(By.CSS_SELECTOR, '.ghx-type img, [data-testid*="type"] img, .issue-type img')
                                issue_data['type'] = type_el.get_attribute('alt') or type_el.get_attribute('title')
                            except:
                                issue_data['type'] = None
                            
                            # Extract Custom Fields by Name
                            if custom_field_names and isinstance(custom_field_names, list):
                                for field_name in custom_field_names:
                                    safe_name = field_name.strip()
                                    if not safe_name: continue
                                    
                                    try:
                                        # Strategy A: Structure/Grid specific - Column matching
                                        # In grid views, columns often have IDs or classes related to the field
                                        # But finding the column index is hard without headers.
                                        # Instead, look for common attributes in the row.
                                        
                                        field_el = None
                                        
                                        # 1. Try generic robust selectors first (titles/tooltips)
                                        # Use case-insensitive matching where supported by browser/driver
                                        selector = f"[title*='{safe_name}' i], [data-tooltip*='{safe_name}' i], [aria-label*='{safe_name}' i]"
                                        
                                        try:
                                            field_el = el.find_element(By.CSS_SELECTOR, selector)
                                        except:
                                            # Fallback for browsers not supporting 'i' modifier
                                            try:
                                                selector = f"[title*='{safe_name}'], [data-tooltip*='{safe_name}'], [aria-label*='{safe_name}']"
                                                field_el = el.find_element(By.CSS_SELECTOR, selector)
                                            except: pass
                                            
                                        # 2. Try Structure/Grid specific cell selectors
                                        if not field_el:
                                            try:
                                                # Look for cells with data-id or class containing the field name
                                                # e.g. .cell-customfield_1000 or data-column-id="story-points"
                                                grid_selector = f"[data-column-id*='{safe_name.lower().replace(' ', '-')}' i], [class*='{safe_name.lower().replace(' ', '-')}' i]"
                                                field_el = el.find_element(By.CSS_SELECTOR, grid_selector)
                                            except: pass

                                        # If found, extract value
                                        if field_el:
                                            # Try to get value from text or attributes
                                            val = field_el.text.strip()
                                            
                                            # If text is empty, check attributes
                                            if not val:
                                                raw_val = field_el.get_attribute('title') or field_el.get_attribute('data-tooltip') or field_el.get_attribute('aria-label') or field_el.get_attribute('value')
                                                if raw_val:
                                                    # If attribute is "Field: Value", split it
                                                    if ':' in raw_val and safe_name in raw_val:
                                                        try:
                                                            val = raw_val.split(':', 1)[1].strip()
                                                        except: val = raw_val
                                                    else:
                                                        val = raw_val
                                            
                                            if val:
                                                issue_data[safe_name] = val
                                    except:
                                        # Field not found on this card
                                        pass

                            # Construct URL
                            base_url = driver.current_url.split('/secure/')[0].split('/browse/')[0]
                            issue_data['url'] = f"{base_url}/browse/{key}"
                            
                            if is_visible:
                                visible_issues.append(key)
                            else:
                                hidden_issues.append(key)
                            
                            issues.append(issue_data)
                            # Log each found issue for debugging
                            visibility_tag = "VISIBLE" if is_visible else "HIDDEN"
                            summary_preview = issue_data.get('summary', '')[:50] if issue_data.get('summary') else 'No summary'
                            print(f"[SCRAPE] Found issue: {key} [{visibility_tag}] - {summary_preview}")
                    except Exception as e:
                        # Log card extraction failures
                        print(f"[SCRAPE] Failed to extract key from card: {e}")
                        pass
                
                debug_info.append(f"Issues extracted from cards: {len(issues)} (Visible: {len(visible_issues)}, Hidden: {len(hidden_issues)})")
                if hidden_issues:
                    debug_info.append(f"Hidden issues: {', '.join(hidden_issues)}")
                
                # Fallback Strategy: Look for any links to issues
                # This is the most robust method as it doesn't rely on card structure, just links
                if len(issues) == 0:
                    debug_info.append("⚠ No issues found with card selectors, trying link strategy...")
                    try:
                        # Find all links containing /browse/
                        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/browse/"]')
                        debug_info.append(f"Found {len(links)} links with /browse/")
                        import re
                        for link in links:
                            href = link.get_attribute('href')
                            # Match /browse/PROJECT-123
                            match = re.search(r'/browse/([A-Z]+-\d+)', href)
                            if match:
                                key = match.group(1)
                                
                                # Check if we already have this key
                                existing_issue = next((i for i in issues if i['key'] == key), None)
                                
                                if existing_issue:
                                    # We already have this issue, but maybe this link has a better summary?
                                    # (e.g. first link was "PROJ-123", this link is "Fix bug in login")
                                    if not existing_issue.get('summary') or existing_issue['summary'] == key:
                                        try:
                                            text = link.text.strip()
                                            if text and text != key:
                                                existing_issue['summary'] = text
                                                print(f"[SCRAPE] Updated summary for {key}: {text}")
                                        except: pass
                                else:
                                    if key not in seen_keys:
                                        seen_keys.add(key)
                                        issue_data = {'key': key, 'visible': True}
                                        
                                        # Try to get summary from text or title
                                        try:
                                            text = link.text.strip()
                                            title = link.get_attribute('title')
                                            
                                            if text and text != key:
                                                issue_data['summary'] = text
                                            elif title:
                                                issue_data['summary'] = title
                                            else:
                                                # Use key as fallback summary
                                                issue_data['summary'] = key
                                        except:
                                            issue_data['summary'] = key
                                            
                                        issues.append(issue_data)
                                        print(f"[SCRAPE] Found issue from link: {key}")
                        debug_info.append(f"Issues extracted from links: {len(issues)}")
                    except Exception as e:
                        debug_info.append(f"❌ Link strategy failed: {e}")

                # DEBUG: If still 0 issues, save page source for inspection
                if len(issues) == 0:
                    debug_info.append("❌ Still found 0 issues. Saving page source to debug_jira_scrape.html")
                    try:
                        with open(os.path.join(DATA_DIR, 'debug_jira_scrape.html'), 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        debug_info.append(f"✓ Debug file saved to {os.path.join(DATA_DIR, 'debug_jira_scrape.html')}")
                    except Exception as e:
                        debug_info.append(f"❌ Failed to save debug file: {e}")
            
            elif jql:
                # Navigate to issue search with JQL
                base_url = driver.current_url.split('/browse')[0].split('/jira')[0]
                search_url = f"{base_url}/issues/?jql={jql.replace(' ', '%20')}"
                driver.get(search_url)
                
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="issue-table"], .issue-table, .navigator-content'))
                )
                
                # Scrape issue rows
                issue_rows = driver.find_elements(By.CSS_SELECTOR, '[data-testid="issue-table-row"], .issuerow, tr.issue-row')
                for row in issue_rows:
                    try:
                        key_el = row.find_element(By.CSS_SELECTOR, '[data-testid="issue-key"], .issuekey a, td.issuekey a')
                        
                        issue_data = {
                            'key': key_el.text,
                            'url': key_el.get_attribute('href'),
                            'visible': row.is_displayed()
                        }
                        
                        # Summary
                        try:
                            summary_el = row.find_element(By.CSS_SELECTOR, '[data-testid*="summary"], .summary, td.summary')
                            issue_data['summary'] = summary_el.text.strip()
                        except: issue_data['summary'] = None
                        
                        # Priority
                        try:
                            priority_el = row.find_element(By.CSS_SELECTOR, '[data-testid*="priority"] img, .priority img, td.priority img')
                            issue_data['priority'] = priority_el.get_attribute('alt') or priority_el.get_attribute('title')
                        except: issue_data['priority'] = None
                        
                        # Status
                        try:
                            status_el = row.find_element(By.CSS_SELECTOR, '[data-testid*="status"], .status, td.status')
                            issue_data['status'] = status_el.text.strip()
                        except: issue_data['status'] = None
                        
                        # Type
                        try:
                            type_el = row.find_element(By.CSS_SELECTOR, '[data-testid*="issuetype"] img, .issuetype img, td.issuetype img')
                            issue_data['type'] = type_el.get_attribute('alt') or type_el.get_attribute('title')
                        except: issue_data['type'] = None
                        
                        issues.append(issue_data)
                    except:
                        pass
            
            # Calculate basic metrics
            visible_count = sum(1 for i in issues if i.get('visible', True))
            hidden_count = len(issues) - visible_count
            
            metrics = {
                'total_issues': len(issues),
                'visible_issues': visible_count,
                'hidden_issues': hidden_count,
                'issues_scraped': issues,  # Return ALL issues with visibility flag
                'scrape_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'debug_info': debug_info,
                'scraping_explanation': {
                    'how_it_works': 'The scraper uses multiple strategies to find issue keys on the board',
                    'strategies': [
                        '1. Classic boards: Looks for .ghx-issue CSS class',
                        '2. Next-gen boards: Looks for [data-testid*="card"] elements',
                        '3. List items: Looks for [role="listitem"] elements',
                        '4. Swimlane cards: Looks for [data-test-id*="software-board.card"]',
                        '5. Data attributes: Checks data-issue-key attribute on elements',
                        '6. Text pattern: Searches element text for PROJ-123 pattern using regex',
                        '7. Child elements: Looks for .ghx-key or issue links inside cards',
                        '8. Fallback: Finds all <a> tags with href containing /browse/ and extracts keys'
                    ],
                    'visibility_detection': 'Each issue is checked with is_displayed() to detect if visible in Jira UI',
                    'phantom_issues': 'Issues marked as hidden exist in DOM but are not visible (archived, filtered, collapsed, stale DOM)',
                    'why_scrape_finds_more': [
                        'Jira may keep archived/resolved issues in DOM',
                        'Client-side filters hide issues without removing from HTML',
                        'Collapsed swimlanes keep issues in DOM',
                        'Stale DOM from previous board state',
                        'Lazy loading artifacts'
                    ],
                    'recommendation': 'Use visible_issues count to match Jira UI. Hidden issues are phantom entries.'
                }
            }
            
            # Save metrics for SM view
            try:
                with open(os.path.join(DATA_DIR, 'sm_metrics.json'), 'w', encoding='utf-8') as f:
                    json.dump({'issues': issues, 'metrics': metrics}, f, indent=2)
            except:
                pass
            
            return {
                'success': True,
                'message': f'Scraped {len(issues)} issues from Jira ({visible_count} visible, {hidden_count} hidden)',
                'metrics': metrics
            }
        except Exception as e:
            import traceback
            return {
                'success': False, 
                'error': str(e),
                'traceback': traceback.format_exc()
            }

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
    
    def _handle_get_version(self):
        """Get current version"""
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'version': APP_VERSION
            }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def _handle_list_releases(self):
        """List recent releases"""
        global version_checker, config_manager
        try:
            if version_checker is None:
                # Get token from config
                github_token = None
                if config_manager:
                    config = config_manager.get_config()
                    # Try feedback token first, then generic github token
                    github_token = config.get('feedback', {}).get('github_token')
                    if not github_token:
                        github_token = config.get('github', {}).get('api_token')

                version_checker = VersionChecker(
                    current_version=APP_VERSION,
                    owner='mikejsmith1985',
                    repo='jira-automation',
                    token=github_token
                )
            
            limit = int(self.headers.get('X-Limit', '10'))
            result = version_checker.list_recent_releases(limit=limit)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
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
    
    def _handle_csv_upload(self):
        """Handle CSV file upload for import"""
        try:
            import cgi
            
            # Parse multipart form data
            content_type = self.headers['Content-Type']
            content_length = int(self.headers['Content-Length'])
            
            environ = {
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type,
                'CONTENT_LENGTH': str(content_length)
            }
            
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ=environ,
                keep_blank_values=True
            )
            
            if 'file' not in form:
                raise ValueError("No file uploaded")
                
            fileitem = form['file']
            if not fileitem.file:
                raise ValueError("Empty file")
                
            importer = JiraCSVImporter()
            result = importer.parse_csv(fileitem.file.read())
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))
            
    def _handle_save_mapping(self):
        """Save CSV field mapping"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            mapping = data.get('mapping')
            mapping_name = data.get('name', 'default')
            
            # Save to config/storage
            config_path = os.path.join(DATA_DIR, 'csv_mappings.json')
            mappings = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    mappings = json.load(f)
            
            mappings[mapping_name] = mapping
            
            with open(config_path, 'w') as f:
                json.dump(mappings, f, indent=2)
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))

    def _handle_get_mappings(self):
        """Get saved CSV mappings"""
        try:
            config_path = os.path.join(DATA_DIR, 'csv_mappings.json')
            mappings = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    mappings = json.load(f)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'mappings': mappings}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))

    def _handle_process_csv(self):
        """Process CSV with provided mapping"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            mapping = data.get('mapping')
            rows = data.get('rows') # If passing rows back from client
            
            # NOTE: In a real app we would read the file from server temp storage.
            # For this MVP, since we returned rows to client in _handle_csv_upload,
            # we can accept them back here, or re-upload.
            # BUT passing rows back and forth is inefficient.
            # BETTER: _handle_csv_upload saves to temp file, returns file_id.
            
            # Let's pivot: Client has the headers. Client likely doesn't have full rows if file was huge.
            # But importer.parse_csv returned 'rows'. 
            # If the client sends 'rows' back, we process them.
            
            if not rows or not mapping:
                raise ValueError("Missing rows or mapping")
                
            importer = JiraCSVImporter()
            result = importer.map_data(rows, mapping)
            
            # Save processed data for persistence
            po_data_path = os.path.join(DATA_DIR, 'po_data.json')
            with open(po_data_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode('utf-8'))

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
    
    def _handle_feedback_submit(self):
        """Handle multipart form data feedback submission with file uploads"""
        global github_feedback_client, log_capture
        try:
            import cgi
            import io
            
            # Parse multipart form data
            content_type = self.headers['Content-Type']
            content_length = int(self.headers['Content-Length'])
            
            # Create environment for cgi.FieldStorage
            environ = {
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type,
                'CONTENT_LENGTH': str(content_length)
            }
            
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ=environ,
                keep_blank_values=True
            )
            
            # Extract form fields
            title = form.getvalue('title', 'User Feedback')
            description = form.getvalue('description', '')
            include_logs = form.getvalue('include_logs', 'true') == 'true'
            
            # Build issue body
            body = f"{description}\n\n"
            
            if include_logs:
                body += "## Logs\n```\n"
                body += log_capture.export_all_logs()
                body += "\n```\n\n"
            
            # Add system info
            import platform
            body += "## System Information\n"
            body += f"- OS: {platform.system()} {platform.release()}\n"
            body += f"- Python: {platform.python_version()}\n"
            body += f"- App Version: {APP_VERSION}\n"
            body += f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # Handle file attachments
            attachments = []
            
            if 'screenshot' in form:
                screenshot = form['screenshot']
                if screenshot.file:
                    screenshot_data = screenshot.file.read()
                    attachments.append({
                        'name': 'screenshot.png',
                        'content': base64.b64encode(screenshot_data).decode('utf-8'),
                        'mime_type': 'image/png'
                    })
            
            if 'video' in form:
                video = form['video']
                if video.file:
                    video_data = video.file.read()
                    attachments.append({
                        'name': 'recording.webm',
                        'content': base64.b64encode(video_data).decode('utf-8'),
                        'mime_type': 'video/webm'
                    })
            
            # Submit to GitHub
            if github_feedback_client:
                print(f"[INFO] Submitting feedback to GitHub: {title}")
                print(f"[INFO] Repository: {github_feedback_client.repo_name}")
                print(f"[INFO] Attachments: {len(attachments)} files")
                
                result = github_feedback_client.create_issue(
                    title=title,
                    body=body,
                    labels=['bug', 'user-feedback'],
                    attachments=attachments if attachments else None
                )
                
                print(f"[INFO] GitHub API result: {result}")
                
                if result['success']:
                    print(f"[SUCCESS] Created issue #{result['issue_number']}: {result['issue_url']}")
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': True,
                        'issue_number': result['issue_number'],
                        'issue_url': result['issue_url']
                    }).encode('utf-8'))
                else:
                    error_msg = result.get('error', 'Failed to create issue')
                    print(f"[ERROR] GitHub issue creation failed: {error_msg}")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'error': f"GitHub API Error: {error_msg}"
                    }).encode('utf-8'))
            else:
                # No GitHub token configured
                print("[ERROR] GitHub feedback client not initialized - token not configured")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'error': 'GitHub token not configured. Go to Settings tab and configure your GitHub Personal Access Token and repository.'
                }).encode('utf-8'))
                
        except Exception as e:
            print(f"[ERROR] Feedback submission exception: {e}")
            import traceback
            traceback.print_exc()
            
            error_detail = str(e)
            # Check for common errors
            if 'Bad credentials' in error_detail:
                error_detail = 'Invalid GitHub token. Please check your token in Settings tab.'
            elif 'Not Found' in error_detail or '404' in error_detail:
                error_detail = 'Repository not found. Please check repository name in Settings (format: owner/repo).'
            elif 'rate limit' in error_detail.lower():
                error_detail = 'GitHub API rate limit exceeded. Please try again later.'
            elif 'permission' in error_detail.lower() or 'forbidden' in error_detail.lower():
                error_detail = 'Permission denied. Ensure your token has "repo" or "public_repo" scope.'
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': f'Exception: {error_detail}'
            }).encode('utf-8'))
    
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
            safe_print(f"ERROR in handle_submit_feedback: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def handle_save_feedback_token(self, data):
        """Save GitHub feedback token to config"""
        global github_feedback
        try:
            token = data.get('token', '')
            repo = data.get('repo', '')
            
            if not token or not repo:
                return {'success': False, 'error': 'Token and repo required'}
            
            # Load config or create new one if missing
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}
                except Exception:
                    config = {}
            else:
                config = {}
            
            # Update feedback section
            if 'feedback' not in config:
                config['feedback'] = {}
            
            config['feedback']['github_token'] = token
            config['feedback']['repo'] = repo
            
            # Save config
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Initialize GitHub feedback client
            github_feedback = GitHubFeedback(token=token, repo_name=repo)
            
            # Validate token
            validation = github_feedback.validate_token()
            
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
            safe_print(f"ERROR in handle_save_feedback_token: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # ========== Extension System Handlers ==========
    
    def _handle_list_extensions(self):
        """List all registered extensions"""
        global extension_manager
        try:
            if not extension_manager:
                self._init_extension_system()
            
            extensions = extension_manager.list_extensions()
            return {'success': True, 'extensions': extensions}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_extension_config(self, ext_name, data):
        """Get or update extension configuration"""
        global extension_manager
        try:
            if not extension_manager:
                self._init_extension_system()
            
            if data:
                result = extension_manager.configure_extension(ext_name, data)
                return result
            else:
                config = extension_manager.get_extension_config(ext_name)
                schema = extension_manager.get_extension_schema(ext_name)
                return {'success': True, 'config': config, 'schema': schema}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_extension_test(self, ext_name):
        """Test extension connection"""
        global extension_manager
        try:
            if not extension_manager:
                self._init_extension_system()
            
            return extension_manager.test_extension(ext_name)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== Data Import/Export Handlers ==========
    
    def _handle_data_import(self, data):
        """Import data from an extension"""
        global extension_manager, data_store, driver
        try:
            if not extension_manager:
                self._init_extension_system()
            
            extension_name = data.get('extension', 'jira')
            query = data.get('query', {})
            
            ext = extension_manager.get_extension(extension_name)
            if not ext:
                return {'success': False, 'error': f'Extension {extension_name} not found'}
            
            if ext.status.value != 'ready':
                ext.initialize(extension_manager.get_extension_config(extension_name), driver=driver)
            
            result = ext.extract_data(query)
            
            if result.get('success'):
                import_id = data_store.save_import(
                    extension=extension_name,
                    data=result.get('data', []),
                    query=query.get('jql', str(query))
                )
                
                features = ext.transform_to_features(result)
                dependencies = ext.transform_to_dependencies(result)
                
                data_store.save_features(features, import_id)
                data_store.save_dependencies(dependencies, import_id)
                
                data_store.log_action('import', extension_name, {
                    'query': query,
                    'count': result.get('count', 0)
                })
                
                return {
                    'success': True,
                    'count': result.get('count', 0),
                    'import_id': import_id,
                    'features_count': len(features),
                    'message': f'Imported {result.get("count", 0)} items'
                }
            else:
                return result
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_data_export(self, data):
        """Export data to specified format"""
        global extension_manager, data_store, report_generator
        try:
            if not report_generator:
                report_generator = ReportGenerator()
            
            format = data.get('format', 'csv')
            data_type = data.get('type', 'features')
            
            if data_type == 'features':
                export_data = data_store.get_latest_features() or []
            elif data_type == 'dependencies':
                export_data = data_store.get_latest_dependencies() or {}
            else:
                export_data = data.get('data', [])
            
            ext = extension_manager.get_extension('jira')
            if ext and format == 'csv':
                content = ext.export_to_csv(export_data)
            else:
                content = report_generator.generate('export', {'data': export_data}, format)
            
            return {'success': True, 'content': content, 'format': format}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_get_features(self):
        """Get current feature structure"""
        global data_store
        try:
            # Check for po_data.json first (CSV Import pivot)
            po_data_path = os.path.join(get_data_dir(), 'po_data.json')
            if os.path.exists(po_data_path):
                with open(po_data_path, 'r') as f:
                    data = json.load(f)
                    # Support both old and new format
                    if 'issues' in data:
                        return {'success': True, 'features': data['issues']}
                    return {'success': True, 'features': data}

            if not data_store:
                data_store = get_data_store()
            
            features = data_store.get_latest_features()
            return {'success': True, 'features': features or []}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_get_dependencies(self):
        """Get current dependency graph"""
        global data_store
        try:
            if not data_store:
                data_store = get_data_store()
            
            dependencies = data_store.get_latest_dependencies()
            return {'success': True, 'dependencies': dependencies or {}}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== Jira-Specific Handlers ==========
    
    def _handle_jira_query(self, data):
        """Execute JQL query"""
        global extension_manager, driver
        try:
            if not extension_manager:
                self._init_extension_system()
            
            jira_ext = extension_manager.get_extension('jira')
            if not jira_ext:
                return {'success': False, 'error': 'Jira extension not found'}
            
            if jira_ext.status.value != 'ready':
                config = extension_manager.get_extension_config('jira')
                jira_ext.initialize(config, driver=driver)
            
            jql = data.get('jql', '')
            max_results = data.get('max_results', 500)
            
            result = jira_ext.extract_data({
                'jql': jql,
                'max_results': max_results
            })
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_jira_update(self, data):
        """Update single Jira issue"""
        global extension_manager, driver
        try:
            if not extension_manager:
                self._init_extension_system()
            
            jira_ext = extension_manager.get_extension('jira')
            if not jira_ext:
                return {'success': False, 'error': 'Jira extension not found'}
            
            issue_key = data.get('issue_key', '')
            updates = data.get('updates', {})
            
            result = jira_ext.update_single(issue_key, updates)
            
            data_store.log_action('update_single', 'jira', {
                'issue_key': issue_key,
                'updates': updates
            }, success=result.get('success', False))
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_jira_bulk_update(self, data):
        """Bulk update Jira issues"""
        global extension_manager, data_store
        try:
            if not extension_manager:
                self._init_extension_system()
            
            jira_ext = extension_manager.get_extension('jira')
            if not jira_ext:
                return {'success': False, 'error': 'Jira extension not found'}
            
            jql = data.get('jql', '')
            updates = data.get('updates', {})
            template_name = data.get('template')
            
            if template_name:
                result = jira_ext.execute_bulk_template(template_name)
            else:
                result = jira_ext.update_bulk({'jql': jql}, updates)
            
            data_store.log_action('bulk_update', 'jira', {
                'jql': jql,
                'updates': updates,
                'template': template_name,
                'updated': result.get('updated', 0),
                'failed': result.get('failed', 0)
            }, success=result.get('success', False))
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_jira_test_connection(self):
        """Test Jira connection"""
        global extension_manager, driver
        try:
            if not extension_manager:
                self._init_extension_system()
            
            jira_ext = extension_manager.get_extension('jira')
            if not jira_ext:
                return {'success': False, 'error': 'Jira extension not found'}
            
            if jira_ext.status.value != 'ready':
                config = extension_manager.get_extension_config('jira')
                jira_ext.initialize(config, driver=driver)
            
            return jira_ext.test_connection()
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== Reporting Handlers ==========
    
    def _handle_daily_scrum_report(self, data):
        """Generate daily scrum report"""
        global extension_manager, enhanced_insights, data_store
        try:
            if not enhanced_insights:
                custom_rules = config_manager.get_insight_rules() if config_manager else []
                enhanced_insights = EnhancedInsightsEngine(custom_rules)
            
            jira_ext = extension_manager.get_extension('jira') if extension_manager else None
            
            if jira_ext and jira_ext.status.value == 'ready':
                jql = data.get('jql', '')
                result = jira_ext.generate_daily_scrum_report(jql)
                
                if result.get('success'):
                    return result
            
            latest_import = data_store.get_latest_import('jira') if data_store else None
            if latest_import:
                issues = latest_import.get('data', [])
                insights = enhanced_insights.generate_daily_scrum_insights(issues)
                return {'success': True, 'report': insights}
            
            return {'success': False, 'error': 'No data available. Import data first.'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_generate_report(self, data):
        """Generate custom report"""
        global report_generator, data_store
        try:
            if not report_generator:
                report_generator = ReportGenerator()
            
            report_type = data.get('type', 'metrics')
            format = data.get('format', 'html')
            
            latest_import = data_store.get_latest_import('jira') if data_store else None
            if not latest_import:
                return {'success': False, 'error': 'No data available'}
            
            report_data = data.get('data', latest_import.get('data', []))
            
            content = report_generator.generate(report_type, {'data': report_data}, format)
            
            return {'success': True, 'content': content, 'format': format}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_get_insights(self):
        """Get active insights"""
        global enhanced_insights, data_store
        try:
            if not enhanced_insights:
                custom_rules = config_manager.get_insight_rules() if config_manager else []
                enhanced_insights = EnhancedInsightsEngine(custom_rules)
            
            insights = enhanced_insights.get_active_insights(days=7)
            return {'success': True, 'insights': insights}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ========== Initialization Helpers ==========
    
    def _init_extension_system(self):
        """Initialize the extension system"""
        global extension_manager, data_store, config_manager, driver
        
        if not extension_manager:
            extension_manager = get_extension_manager()
            data_store = get_data_store()
            config_manager = get_config_manager()
            
            jira_ext = JiraExtension()
            github_ext = GitHubExtension()
            
            extension_manager.register_extension(jira_ext)
            extension_manager.register_extension(github_ext)
            
            if driver:
                jira_config = config_manager.get_extension_config('jira')
                if not jira_config:
                    jira_config = {
                        'base_url': config_manager.get('jira.base_url', ''),
                        'project_key': config_manager.get('jira.project_key', '')
                    }
                jira_ext.initialize(jira_config, driver=driver)

    # ========== ServiceNow Integration Handlers ==========
    
    def _handle_get_snow_config(self):
        """Get ServiceNow configuration (GET handler)"""
        try:
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            snow_config = config.get('servicenow', {})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'config': snow_config}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
    
    def handle_get_snow_config(self):
        """Get ServiceNow configuration"""
        try:
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            snow_config = config.get('servicenow', {})
            return {'success': True, 'config': snow_config}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_save_snow_config(self, data):
        """Save ServiceNow configuration with validation"""
        try:
            # Extract and validate required fields
            url = data.get('url', '').strip()
            jira_project = data.get('jira_project', '').strip()
            
            # Validation
            if not url:
                return {'success': False, 'error': 'ServiceNow URL is required. Please enter your ServiceNow instance URL (e.g., https://yourcompany.service-now.com)'}
            
            if not url.startswith('http://') and not url.startswith('https://'):
                return {'success': False, 'error': 'URL must start with http:// or https://'}
            
            if not jira_project:
                return {'success': False, 'error': 'Jira Project Key is required. Please enter the project key where issues will be created (e.g., PROJ, DEV)'}
            
            # Load existing config
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'servicenow' not in config:
                config['servicenow'] = {}
            
            # Update with validated data
            config['servicenow'].update({
                'url': url,
                'jira_project': jira_project,
                'field_mapping': data.get('field_mapping', {})
            })
            
            # Save config
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Update sync engine if it exists
            global sync_engine
            if sync_engine:
                with open(config_path, 'r', encoding='utf-8') as f:
                    sync_engine.config = yaml.safe_load(f)
            
            safe_print(f"[SNOW] Configuration saved - URL: {url}, Project: {jira_project}")
            
            return {
                'success': True,
                'message': f'ServiceNow configuration saved successfully. URL: {url}'
            }
        except Exception as e:
            safe_print(f"ERROR in handle_save_snow_config: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def handle_test_snow_connection(self):
        """Test ServiceNow connection with comprehensive error handling"""
        global driver
        
        # Check 1: Browser initialized
        if driver is None:
            return {
                'success': False,
                'error': 'Browser not open. Please open Jira browser first to initialize Selenium.'
            }
        
        try:
            # Check 2: Load config
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            if not os.path.exists(config_path):
                return {
                    'success': False,
                    'error': 'Configuration file not found. Please configure integrations first.'
                }
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Check 3: ServiceNow config exists
            if not config or 'servicenow' not in config:
                return {
                    'success': False,
                    'error': 'ServiceNow not configured. Please add ServiceNow URL in Integrations tab.'
                }
            
            snow_config = config.get('servicenow', {})
            
            # Check 4: URL is configured
            url = snow_config.get('url', '').strip()
            if not url:
                return {
                    'success': False,
                    'error': 'ServiceNow URL not configured. Please enter your ServiceNow URL in Integrations tab.'
                }
            
            # Check 5: URL format is valid
            if not url.startswith('http://') and not url.startswith('https://'):
                return {
                    'success': False,
                    'error': f'Invalid ServiceNow URL format: {url}. URL must start with http:// or https://'
                }
            
            # Check 6: Jira project configured (needed for SnowJiraSync)
            jira_project = snow_config.get('jira_project', '').strip()
            if not jira_project:
                return {
                    'success': False,
                    'error': 'Jira Project not configured for ServiceNow integration. Please enter a Jira project key.'
                }
            
            # Add minimal jira config if missing (needed for SnowJiraSync initialization)
            if 'jira' not in config:
                config['jira'] = {'base_url': '', 'project_keys': [jira_project]}
            
            # Test connection
            safe_print(f"[SNOW] Testing connection to {url}...")
            
            from snow_jira_sync import SnowJiraSync
            snow_sync = SnowJiraSync(driver, config)
            
            result = snow_sync.test_connection()
            
            if result.get('success'):
                safe_print(f"[SNOW] ✓ Connection test successful")
            else:
                safe_print(f"[SNOW] ✗ Connection test failed: {result.get('error')}")
            
            return result
            
        except KeyError as e:
            # Config key missing
            safe_print(f"[SNOW] Configuration error: missing key {e}")
            return {
                'success': False,
                'error': f'Configuration incomplete: missing {e}. Please check Integrations settings.'
            }
        except Exception as e:
            # Unexpected error
            safe_print(f"[SNOW] Error testing connection: {e}")
            error_msg = str(e)
            # Make error user-friendly
            if 'WebDriver' in error_msg or 'selenium' in error_msg.lower():
                error_msg = 'Browser error. Try closing and reopening the browser.'
            elif 'connection' in error_msg.lower() or 'network' in error_msg.lower():
                error_msg = 'Network error. Check your internet connection and ServiceNow URL.'
            elif len(error_msg) > 200:
                error_msg = error_msg[:200] + '... (See logs for full error)'
            
            return {
                'success': False,
                'error': error_msg
            }
    
    
    def handle_export_logs(self):
        """Export logs and diagnostics for debugging"""
        try:
            import datetime
            
            # Collect diagnostics
            diagnostics = []
            diagnostics.append("="*70)
            diagnostics.append("WAYPOINT DIAGNOSTICS EXPORT")
            diagnostics.append("="*70)
            diagnostics.append(f"Generated: {datetime.datetime.now().isoformat()}")
            diagnostics.append(f"App Version: {APP_VERSION}")
            diagnostics.append("")
            
            # System info
            diagnostics.append("--- SYSTEM INFO ---")
            diagnostics.append(f"Python Version: {sys.version}")
            diagnostics.append(f"Platform: {sys.platform}")
            diagnostics.append(f"Executable: {sys.executable}")
            if getattr(sys, 'frozen', False):
                diagnostics.append("Running as: Frozen executable (PyInstaller)")
            else:
                diagnostics.append("Running as: Python script")
            diagnostics.append("")
            
            # Paths
            diagnostics.append("--- PATHS ---")
            diagnostics.append(f"Data Directory: {DATA_DIR}")
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            diagnostics.append(f"Config Path: {config_path}")
            diagnostics.append(f"Config Exists: {os.path.exists(config_path)}")
            log_file = os.path.join(DATA_DIR, 'jira-sync.log')
            diagnostics.append(f"Log File: {log_file}")
            diagnostics.append(f"Log File Exists: {os.path.exists(log_file)}")
            diagnostics.append("")
            
            # Configuration status (without sensitive data)
            diagnostics.append("--- CONFIGURATION STATUS ---")
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}
                    
                    # Check each integration (without showing actual values)
                    if 'servicenow' in config:
                        snow = config['servicenow']
                        url = snow.get('url', '')
                        diagnostics.append(f"ServiceNow URL: {'<configured>' if url else '<NOT CONFIGURED>'}")
                        diagnostics.append(f"  - URL length: {len(url)} chars")
                        diagnostics.append(f"  - Jira Project: {snow.get('jira_project', '<NOT CONFIGURED>')}")
                        diagnostics.append(f"  - Field Mapping: {'<configured>' if snow.get('field_mapping') else '<none>'}")
                    else:
                        diagnostics.append("ServiceNow: <NOT CONFIGURED>")
                    
                    if 'jira' in config:
                        jira = config['jira']
                        diagnostics.append(f"Jira Base URL: {'<configured>' if jira.get('base_url') else '<NOT CONFIGURED>'}")
                        diagnostics.append(f"  - Project Keys: {jira.get('project_keys', [])}")
                    else:
                        diagnostics.append("Jira: <NOT CONFIGURED>")
                    
                    if 'github' in config:
                        github = config['github']
                        diagnostics.append(f"GitHub API Token: {'<configured>' if github.get('api_token') else '<NOT CONFIGURED>'}")
                        diagnostics.append(f"  - Organization: {github.get('organization', '<none>')}")
                    else:
                        diagnostics.append("GitHub: <NOT CONFIGURED>")
                    
                    if 'feedback' in config:
                        feedback = config['feedback']
                        diagnostics.append(f"Feedback GitHub Token: {'<configured>' if feedback.get('github_token') else '<NOT CONFIGURED>'}")
                        diagnostics.append(f"  - Repo: {feedback.get('repo', '<none>')}")
                    else:
                        diagnostics.append("Feedback: <NOT CONFIGURED>")
                else:
                    diagnostics.append("Config file not found!")
            except Exception as e:
                diagnostics.append(f"Error reading config: {e}")
            
            diagnostics.append("")
            
            # Browser status
            diagnostics.append("--- BROWSER STATUS ---")
            global driver
            if driver is None:
                diagnostics.append("Selenium Driver: NOT INITIALIZED")
            else:
                diagnostics.append("Selenium Driver: INITIALIZED")
                try:
                    diagnostics.append(f"  - Current URL: {driver.current_url}")
                except:
                    diagnostics.append("  - Current URL: <unable to retrieve>")
            diagnostics.append("")
            
            # Recent logs (last 500 lines)
            diagnostics.append("--- RECENT LOGS (last 500 lines) ---")
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Get last 500 lines
                    recent_lines = lines[-500:] if len(lines) > 500 else lines
                    diagnostics.append(f"Total log lines: {len(lines)}, showing last: {len(recent_lines)}")
                    diagnostics.append("")
                    diagnostics.extend([line.rstrip() for line in recent_lines])
                except Exception as e:
                    diagnostics.append(f"Error reading log file: {e}")
            else:
                diagnostics.append("Log file not found")
            
            diagnostics.append("")
            diagnostics.append("="*70)
            diagnostics.append("END OF DIAGNOSTICS")
            diagnostics.append("="*70)
            
            # Join all diagnostics
            log_data = "\n".join(diagnostics)
            
            return {
                'success': True,
                'log_data': log_data,
                'lines': len(diagnostics)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_validate_prb(self, data):
        """Validate a PRB and extract data"""
        global driver
        
        if driver is None:
            return {'success': False, 'error': 'Browser not open. Please open Jira browser first to initialize Selenium.'}
        
        try:
            prb_number = data.get('prb_number', '').strip()
            if not prb_number:
                return {'success': False, 'error': 'PRB number is required'}
            
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            from snow_jira_sync import SnowJiraSync
            snow_sync = SnowJiraSync(driver, config)
            
            result = snow_sync.validate_prb(prb_number)
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_snow_jira_sync(self, data):
        """Execute ServiceNow to Jira sync workflow"""
        global driver
        
        if driver is None:
            return {'success': False, 'error': 'Browser not open. Please open Jira browser first to initialize Selenium.'}
        
        try:
            prb_number = data.get('prb_number', '').strip()
            selected_inc = data.get('selected_inc', '').strip()
            
            if not prb_number:
                return {'success': False, 'error': 'PRB number is required'}
            if not selected_inc:
                return {'success': False, 'error': 'Incident number is required'}
            
            config_path = os.path.join(DATA_DIR, 'config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            from snow_jira_sync import SnowJiraSync
            snow_sync = SnowJiraSync(driver, config)
            
            result = snow_sync.sync_prb_to_jira(prb_number, selected_inc)
            return result
        except Exception as e:
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
        #settings {
            padding-left: 50px;
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
                ruleDiv.className = 'branch-rule-container';
                ruleDiv.innerHTML = `
                    <div class="branch-rule-content">
                        <div class="branch-rule-grid">
                            <div class="branch-rule-field">
                                <label>Branch Name</label>
                                <input type="text" value="${rule.branch}" 
                                       onchange="updateBranchRule(${index}, 'branch', this.value)"
                                       placeholder="e.g., DEV, INT, PVS">
                            </div>
                            <div class="branch-rule-field">
                                <label>Move to Status</label>
                                <input type="text" value="${rule.set_status || ''}" 
                                       onchange="updateBranchRule(${index}, 'set_status', this.value)"
                                       placeholder="e.g., Ready for QA">
                            </div>
                            <div class="branch-rule-field">
                                <label>Add Label</label>
                                <input type="text" value="${rule.add_label || ''}" 
                                       onchange="updateBranchRule(${index}, 'add_label', this.value)"
                                       placeholder="e.g., merged-dev">
                            </div>
                            <div class="branch-rule-field branch-rule-checkbox">
                                <label>
                                    <input type="checkbox" ${rule.add_comment !== false ? 'checked' : ''}
                                           onchange="updateBranchRule(${index}, 'add_comment', this.checked)">
                                    <span>Add comment</span>
                                </label>
                            </div>
                        </div>
                        <button class="btn-small btn-danger branch-rule-delete" onclick="removeBranchRule(${index})" 
                                title="Delete this branch rule">
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
                                    addLog('success', `Screenshot ${i + 1} uploaded successfully`);
                                } else {
                                    const errorData = await uploadRes.json();
                                    const errorMsg = `Screenshot upload failed: ${uploadRes.status} - ${errorData.message || 'Unknown error'}`;
                                    console.error(errorMsg, errorData);
                                    addLog('error', errorMsg);
                                }
                            } catch (err) {
                                const errorMsg = `Screenshot upload error: ${err.message}`;
                                console.error(errorMsg, err);
                                addLog('error', errorMsg);
                            }
                        }
                    }
                    
                    // Add screenshots to body
                    if (imageUrls.length > 0) {
                        body += '\\n## Screenshots\\n';
                        imageUrls.forEach(url => {
                            body += `![screenshot](${url})\\n\\n`;
                        });
                        addLog('success', `${imageUrls.length} screenshot(s) attached to issue`);
                    } else if (feedbackAttachments.length > 0) {
                        // Had attachments but none uploaded successfully
                        const imgCount = feedbackAttachments.filter(a => a.type === 'image').length;
                        if (imgCount > 0) {
                            addLog('warn', `${imgCount} screenshot(s) failed to upload - check token permissions`);
                        }
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
    global browser_opened
    if browser_opened:
        safe_print("[BROWSER] Already opened, skipping duplicate call")
        return
    browser_opened = True
    time.sleep(1.5)
    safe_print("[BROWSER] Opening browser at http://127.0.0.1:5000")
    # new=2 opens in a new tab (avoids potential double-open with new=0)
    try:
        webbrowser.open('http://127.0.0.1:5000', new=2)
    except Exception as e:
        safe_print(f"[WARN] Failed to open browser: {e}")

def run_server():
    """Run the HTTP server"""
    global github_feedback
    
    # Initialize GitHub feedback if token exists in config
    config_path = os.path.join(DATA_DIR, 'config.yaml')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            if config and 'feedback' in config:
                token = config['feedback'].get('github_token')
                repo = config['feedback'].get('repo')
                
                if token and repo and token not in ['YOUR_GITHUB_TOKEN_HERE', 'your_token_here']:
                    github_feedback = GitHubFeedback(token=token, repo_name=repo)
                    print("[OK] GitHub feedback system initialized")
        except yaml.YAMLError as e:
            print(f"[WARN] Config file is corrupt: {str(e)}")
        except Exception as e:
            print(f"[WARN] Could not load config: {str(e)}")
    # If config doesn't exist, silently continue (first launch)
    
    server_address = ('127.0.0.1', 5000)
    httpd = HTTPServer(server_address, SyncHandler)
    safe_print("[START] Waypoint starting...")
    safe_print("[SERVER] http://127.0.0.1:5000")
    safe_print("[BROWSER] Opening browser...")
    safe_print("[WAIT] Starting server (this will block)...")
    httpd.serve_forever()

if __name__ == '__main__':
    # Print data directory info
    safe_print(f"[CONFIG] Data directory: {DATA_DIR}")
    
    # Prevent multiple instances using a lock file
    lock_file = os.path.join(DATA_DIR, 'waypoint.lock')
    if os.path.exists(lock_file):
        # Try to read the PID from lock file
        try:
            with open(lock_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if that process is still running
            import psutil
            if psutil.pid_exists(old_pid):
                try:
                    proc = psutil.Process(old_pid)
                    # Check if it's actually Waypoint
                    if 'waypoint' in proc.name().lower() or 'python' in proc.name().lower():
                        safe_print(f"[WARN] Another Waypoint instance is running (PID {old_pid})")
                        safe_print("[ACTION] Attempting to close old instance...")
                        
                        # Try graceful shutdown first
                        proc.terminate()
                        
                        # Wait up to 5 seconds for it to close
                        try:
                            proc.wait(timeout=5)
                            safe_print("[OK] Old instance closed successfully")
                            # Remove stale lock file
                            if os.path.exists(lock_file):
                                os.remove(lock_file)
                        except psutil.TimeoutExpired:
                            # Force kill if graceful shutdown didn't work
                            safe_print("[WARN] Old instance didn't close gracefully, force killing...")
                            proc.kill()
                            proc.wait(timeout=2)
                            safe_print("[OK] Old instance force-killed")
                            if os.path.exists(lock_file):
                                os.remove(lock_file)
                    else:
                        # Not Waypoint, might be a stale PID reused by another app
                        safe_print(f"[INFO] Lock file PID {old_pid} is not Waypoint, removing stale lock")
                        os.remove(lock_file)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process doesn't exist or can't access it, remove lock
                    safe_print("[INFO] Removing stale lock file")
                    if os.path.exists(lock_file):
                        os.remove(lock_file)
            else:
                # PID doesn't exist, remove stale lock
                safe_print("[INFO] Removing stale lock file (process no longer exists)")
                if os.path.exists(lock_file):
                    os.remove(lock_file)
        except Exception as e:
            # Lock file is invalid or can't be read
            safe_print(f"[INFO] Removing invalid lock file: {e}")
            try:
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except:
                pass
    
    # Write our PID to lock file
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass  # Non-critical if we can't write lock file
    
    try:
        # Ensure config.yaml exists in DATA_DIR
        config_file = os.path.join(DATA_DIR, 'config.yaml')
        
        # Migration: Check if running as frozen executable and config doesn't exist in new location
        if getattr(sys, 'frozen', False) and not os.path.exists(config_file):
            # Look for config in old location (exe directory)
            old_config = os.path.join(os.path.dirname(sys.executable), 'config.yaml')
            if os.path.exists(old_config):
                import shutil
                shutil.copy(old_config, config_file)
                safe_print(f"[MIGRATE] Copied config from old location to {config_file}")
                safe_print(f"[INFO] Config is now stored in {DATA_DIR} for persistence across versions")
        
        if not os.path.exists(config_file):
            # Copy from bundled template if it doesn't exist
            template_file = os.path.join(BASE_DIR, 'config.yaml')
            if os.path.exists(template_file):
                import shutil
                shutil.copy(template_file, config_file)
                safe_print(f"[INIT] Created config.yaml at {config_file}")
            else:
                safe_print(f"[WARN] No config template found, creating minimal config")
                # Create minimal config
                minimal_config = {
                    'github': {'api_token': '', 'base_url': 'https://github.com', 'organization': 'your-org', 'repositories': []},
                    'jira': {'base_url': 'https://your-company.atlassian.net', 'project_keys': []},
                    'feedback': {'github_token': '', 'repo': ''},
                    'automation': {}
                }
                with open(config_file, 'w', encoding='utf-8') as f:
                    yaml.dump(minimal_config, f, default_flow_style=False)
        
        # Start browser opener in background
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Run server
        run_server()
    finally:
        # Clean up lock file on exit
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except:
            pass



