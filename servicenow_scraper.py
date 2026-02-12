"""
ServiceNow scraper module - Playwright version
Handles data extraction from ServiceNow PRB tickets via browser automation
Now using Playwright for better modern web app support and native Shadow DOM handling
"""
import time
import logging
import os
from datetime import datetime

class ServiceNowScraper:
    """Scrapes data from ServiceNow Problem (PRB) tickets using Playwright"""
    
    # Constants
    # Timeouts are ONLY for actual failures - Playwright waits intelligently
    SAML_TIMEOUT_MS = 60000  # 60 seconds max wait for SAML redirect (failure timeout)
    ELEMENT_TIMEOUT_MS = 10000  # 10 seconds max wait for elements (failure timeout)
    FAST_TIMEOUT_MS = 3000  # 3 seconds for optional checks (reduced from aggressive 500ms)
    
    def __init__(self, page, config):
        """
        Initialize ServiceNow scraper
        
        Args:
            page: Playwright Page object (not Selenium driver)
            config: Configuration dict with servicenow settings
        """
        self.page = page
        self.config = config
        self.base_url = config.get('servicenow', {}).get('url', '').strip()
        self.logger = logging.getLogger(__name__)
        self.start_time = None  # For timing logs
        
        # Setup diagnostics directory
        try:
            from app import DATA_DIR
            self.data_dir = DATA_DIR
        except:
            self.data_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Waypoint')
        
        self.diagnostics_dir = os.path.join(self.data_dir, 'diagnostics')
        os.makedirs(self.diagnostics_dir, exist_ok=True)
        
        # Log configuration for debugging
        self.logger.info(f"[SNOW] ServiceNowScraper initialized (Playwright)")
        # Normalize base_url - remove trailing slash to prevent double slashes
        self.base_url = self.base_url.rstrip('/') if self.base_url else ''
        self.logger.info(f"[SNOW] Base URL: '{self.base_url}'")
        self.logger.info(f"[SNOW] Diagnostics dir: '{self.diagnostics_dir}'")
        if not self.base_url:
            self.logger.error("[SNOW] ERROR: ServiceNow URL is empty or not configured!")
            self.logger.error("[SNOW] Please configure ServiceNow URL in Integrations tab")
    
    def _elapsed(self):
        """Get elapsed time since operation started"""
        if self.start_time is None:
            return "00:00.0"
        elapsed = time.time() - self.start_time
        mins = int(elapsed // 60)
        secs = elapsed % 60
        return f"{mins:02d}:{secs:05.2f}"
    
    def _log(self, message, level='info'):
        """Log with timestamp"""
        full_msg = f"[SNOW] [{self._elapsed()}] {message}"
        if level == 'error':
            self.logger.error(full_msg)
        elif level == 'warning':
            self.logger.warning(full_msg)
        else:
            self.logger.info(full_msg)
    
    def _capture_diagnostic_screenshot(self, prb_number, reason):
        """Capture screenshot for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prb_fail_{prb_number}_{timestamp}.png"
            filepath = os.path.join(self.diagnostics_dir, filename)
            self.page.screenshot(path=filepath)
            self._log(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            self._log(f"Failed to capture screenshot: {e}", 'error')
            return None
    
    def _capture_page_state(self, prb_number):
        """Capture comprehensive page state for debugging"""
        self._log("=== DIAGNOSTIC SNAPSHOT ===")
        
        screenshot_path = None
        
        try:
            # Current URL
            current_url = self.page.url
            self._log(f"URL: {current_url}")
            
            # Page title
            title = self.page.title()
            self._log(f"Title: {title}")
            
            # Screenshot
            screenshot_path = self._capture_diagnostic_screenshot(prb_number, "failure")
            
            # Page content preview
            content = self.page.content()
            preview = content[:500].replace('\n', ' ').replace('\r', '')
            self._log(f"Content preview: {preview}...")
            
            # Check for PRB number in content
            prb_in_content = prb_number in content if prb_number else False
            self._log(f"PRB in content: {'YES' if prb_in_content else 'NO'}")
            
            # Check for gsft_main iframe
            try:
                iframe_count = self.page.locator('#gsft_main').count()
                self._log(f"gsft_main iframe: {'FOUND' if iframe_count > 0 else 'NOT FOUND'}")
            except:
                self._log("gsft_main iframe: CHECK FAILED")
            
            # Count input elements
            try:
                input_count = self.page.locator('input').count()
                self._log(f"Input elements: {input_count}")
            except:
                pass
            
            # Check for common SAML/SSO indicators
            url_lower = current_url.lower()
            if 'okta' in url_lower:
                self._log("⚠️ DETECTED: Okta SSO page")
            if 'saml' in url_lower:
                self._log("⚠️ DETECTED: SAML auth page")
            if 'login' in url_lower:
                self._log("⚠️ DETECTED: Login page")
            
            # Save full HTML for debugging
            html_path = os.path.join(self.diagnostics_dir, f"prb_fail_{prb_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self._log(f"HTML saved: {html_path}")
            
        except Exception as e:
            self._log(f"Error capturing page state: {e}", 'error')
        
        self._log("=== END DIAGNOSTIC ===")
        return screenshot_path
    
    def login_check(self):
        """Check if logged into ServiceNow"""
        try:
            current_url = self.page.url
            
            # Check for various login/auth pages
            login_indicators = [
                'login',
                'sso',
                'saml',
                'oauth',
                'auth',
                'signin',
                'logon'
            ]
            
            url_lower = current_url.lower()
            
            # Check if on any auth-related page
            for indicator in login_indicators:
                if indicator in url_lower:
                    self.logger.warning(f"ServiceNow authentication page detected ('{indicator}' in URL)")
                    self.logger.warning(f"Current URL: {current_url}")
                    return False
            
            # Also check for common SSO providers in URL
            sso_providers = ['okta.com', 'login.microsoftonline.com', 'adfs', 'pingidentity', 'onelogin']
            for provider in sso_providers:
                if provider in url_lower:
                    self.logger.warning(f"SSO provider detected: {provider}")
                    self.logger.warning(f"Current URL: {current_url}")
                    return False
            
            return True  # Assume logged in if not on auth page
        except Exception as e:
            self.logger.error(f"Error checking ServiceNow login: {e}")
            return True  # Don't fail on error, assume logged in
    
    def navigate_to_prb(self, prb_number):
        """
        Navigate to a specific PRB ticket with comprehensive diagnostics
        
        Args:
            prb_number: The PRB number (e.g., 'PRB0123456')
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        self.start_time = time.time()
        screenshot_path = None
        
        try:
            if not self.base_url:
                raise ValueError("ServiceNow URL not configured. Please set it in Settings > Integrations.")
            
            prb_url = f"{self.base_url}/problem.do?sysparm_query=number={prb_number}"
            self._log(f"Starting navigation to {prb_number}")
            self._log(f"Target URL: {prb_url}")
            self._log(f"Timeout: {self.SAML_TIMEOUT_MS}ms (for SAML/Okta)")
            
            # === STEP 1: Initial navigation ===
            # Playwright waits intelligently - no wasted time!
            # 'domcontentloaded' = faster than 'networkidle', sufficient for ServiceNow
            self._log("Step 1: Initial page.goto...")
            try:
                self.page.goto(prb_url, wait_until='domcontentloaded', timeout=self.SAML_TIMEOUT_MS)
            except Exception as e:
                self._log(f"Initial navigation error: {e}", 'error')
                # Don't fail yet - might be timeout during SAML, but page might be usable
                
            current_url = self.page.url
            self._log(f"Step 1 complete. Current URL: {current_url}")
            
            # === STEP 2: Handle SAML redirect ===
            if 'problem.do' not in current_url and prb_number not in current_url:
                self._log("SAML redirect detected - not on PRB page yet")
                
                # Check if we're on an auth page
                url_lower = current_url.lower()
                if any(x in url_lower for x in ['okta', 'saml', 'login', 'sso', 'auth']):
                    self._log(f"⚠️ Auth page detected: {current_url}")
                    self._log("Waiting for authentication to complete...")
                    
                    # Wait for navigation away from auth page (up to 60s)
                    try:
                        self.page.wait_for_url(
                            lambda url: 'okta' not in url.lower() and 'saml' not in url.lower() and 'login' not in url.lower(),
                            timeout=self.SAML_TIMEOUT_MS
                        )
                        self._log(f"Auth complete. New URL: {self.page.url}")
                    except Exception as e:
                        self._log(f"Timeout waiting for auth: {e}", 'error')
                        screenshot_path = self._capture_page_state(prb_number)
                        return False
                
                # Navigate to PRB again now that auth should be complete
                self._log("Step 2: Re-navigating to PRB after SAML...")
                try:
                    self.page.goto(prb_url, wait_until='domcontentloaded', timeout=self.SAML_TIMEOUT_MS)
                except Exception as e:
                    self._log(f"Second navigation error: {e}", 'error')
                    # Continue - page might still be usable
                    
                current_url = self.page.url
                self._log(f"Step 2 complete. Current URL: {current_url}")
            
            # === STEP 3: Wait for PRB form elements ===
            self._log("Step 3: Waiting for PRB form elements...")
            
            # Wait for specific form elements instead of just networkidle
            form_selectors = [
                "[id='problem.number']",
                "[id='problem.short_description']",
                "[id='sys_readonly.problem.number']",  # Read-only variant
                "input[id*='problem']",  # Any input with 'problem' in ID
            ]
            
            form_found = False
            for selector in form_selectors:
                try:
                    self._log(f"Checking for element: {selector}")
                    locator = self.page.locator(selector).first
                    # Playwright waits efficiently - returns immediately when element appears
                    locator.wait_for(state='attached', timeout=self.ELEMENT_TIMEOUT_MS)
                    self._log(f"✓ Found form element: {selector}")
                    form_found = True
                    break
                except Exception as e:
                    self._log(f"Not found: {selector} ({str(e)[:50]}...)")
                    continue
            
            if not form_found:
                # Try iframe - ServiceNow commonly uses #gsft_main iframe
                self._log("Form not found in main page, checking iframe...")
                try:
                    frame = self.page.frame_locator('#gsft_main')
                    for selector in form_selectors:
                        try:
                            locator = frame.locator(selector).first
                            locator.wait_for(state='attached', timeout=self.ELEMENT_TIMEOUT_MS)
                            self._log(f"✓ Found form element in iframe: {selector}")
                            form_found = True
                            self.frame = frame
                            break
                        except Exception as e:
                            self._log(f"Iframe selector {selector} failed: {str(e)[:50]}")
                            continue
                except Exception as e:
                    self._log(f"Iframe check failed: {e}", 'warning')
            
            if not form_found:
                # Last resort: check if PRB number is anywhere in page content
                self._log("Form elements not found, checking page content...")
                content = self.page.content()
                if prb_number in content:
                    self._log(f"✓ PRB {prb_number} found in page content (form may still be loading)")
                    form_found = True
                    self.frame = self.page
                else:
                    self._log(f"✗ PRB {prb_number} NOT found in page content", 'error')
                    screenshot_path = self._capture_page_state(prb_number)
                    return False
            
            # === STEP 4: Final verification ===
            self._log("Step 4: Final verification...")
            
            # Set frame context
            if not hasattr(self, 'frame') or self.frame is None:
                try:
                    frame = self.page.frame_locator('#gsft_main')
                    frame.locator('body').wait_for(state='attached', timeout=3000)
                    self.frame = frame
                    self._log("Using gsft_main iframe context")
                except:
                    self.frame = self.page
                    self._log("Using main page context")
            
            # Check for GlideForm API
            try:
                glide_check = self.page.evaluate("""
                    () => typeof g_form !== 'undefined' ? g_form.getValue('number') : null
                """)
                if glide_check:
                    self._log(f"✓ GlideForm API available. PRB number: {glide_check}")
                    self.use_glide_form = True
                else:
                    self.use_glide_form = False
            except:
                self.use_glide_form = False
            
            elapsed_total = time.time() - self.start_time
            self._log(f"✓ Successfully navigated to PRB {prb_number} (total: {elapsed_total:.2f}s)")
            return True
            
        except Exception as e:
            self._log(f"Error navigating to PRB: {e}", 'error')
            import traceback
            self.logger.error(traceback.format_exc())
            screenshot_path = self._capture_page_state(prb_number)
            return False
    
    def extract_prb_data(self):
        """
        Extract data from visible text content - works regardless of field state/status
        
        Returns:
            dict: PRB data with short_description, description, and related_incidents
        """
        prb_data = {}
        
        try:
            import re
            
            # Get all visible text from page body (works for read-only and editable fields)
            self._log("Extracting visible text from page...")
            page_text = self.page.inner_text('body')
            
            # Save raw text for debugging
            try:
                debug_path = os.path.join(self.diagnostics_dir, f"prb_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.write(page_text)
                self._log(f"Saved page text to: {debug_path}")
            except:
                pass
            
            # 1. Extract PRB number (should be in page somewhere)
            prb_match = re.search(r'(PRB\d{7,})', page_text)
            prb_data['prb_number'] = prb_match.group(1) if prb_match else ''
            self._log(f"PRB Number: {prb_data['prb_number']}")
            
            # 2. Extract short description (look for label + value pattern)
            # Common patterns: "Short description\n<value>" or "Short description: <value>"
            short_patterns = [
                r'Short description[:\s]+(.+?)(?:\n|$)',
                r'Problem statement[:\s]+(.+?)(?:\n|$)',
                r'short_description[:\s]+(.+?)(?:\n|$)',
            ]
            prb_data['short_description'] = ''
            for pattern in short_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    prb_data['short_description'] = match.group(1).strip()
                    break
            self._log(f"Short Description: {prb_data['short_description'][:100]}...")
            
            # 3. Extract long description (multi-line field)
            # Look for "Description" label followed by content until next field/section
            desc_patterns = [
                r'Description[:\s]+(.+?)(?:\n\n|\nProblem statement|\nConfiguration item|\nRelated|$)',
                r'problem\.description[:\s]+(.+?)(?:\n\n|\nProblem statement|\nConfiguration item|$)',
            ]
            prb_data['description'] = ''
            for pattern in desc_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                if match:
                    prb_data['description'] = match.group(1).strip()
                    break
            self._log(f"Description: {prb_data['description'][:100]}...")
            
            # 4. Extract all related INC numbers from anywhere in the page
            inc_matches = re.findall(r'INC\d{7,}', page_text)
            prb_data['related_incidents'] = list(set(inc_matches))  # Dedupe
            self._log(f"Related Incidents: {prb_data['related_incidents']}")
            
            if not prb_data['prb_number']:
                self._log("WARNING: Could not extract PRB number from page text", 'warning')
            
            self._log(f"✓ Successfully extracted PRB data")
            return prb_data
            
        except Exception as e:
            self._log(f"Error extracting PRB data: {e}", 'error')
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _get_field_value(self, field_id):
        """
        Get value from a ServiceNow form field using Playwright
        
        Optimized for performance: reduced timeouts, fewer fallbacks
        
        Args:
            field_id: Field ID (e.g., 'problem.short_description')
            
        Returns:
            str: Field value or empty string if not found
        """
        # If GlideForm API is available, use it as primary method (FASTEST)
        if hasattr(self, 'use_glide_form') and self.use_glide_form:
            try:
                field_name = field_id.replace('problem.', '').replace('sys_display.problem.', '')
                
                value = self.page.evaluate(f"""
                    () => {{
                        if (typeof g_form !== 'undefined') {{
                            return g_form.getValue('{field_name}');
                        }}
                        return null;
                    }}
                """)
                
                if value:
                    return value
            except Exception as e:
                self.logger.debug(f"[SNOW] GlideForm failed for {field_id}: {e}")
        
        # APPROACH 1: Container-based extraction (works in read-only view)
        # Playwright waits efficiently - returns immediately when element is ready
        container_id = f"element.{field_id}"
        try:
            container = self.frame.locator(f"[id='{container_id}']").first
            container.wait_for(state='attached', timeout=self.FAST_TIMEOUT_MS)
            
            # Try read-only value spans first (for closed/resolved tickets)
            readonly_selectors = [
                '.readonly-value',
                '[id*="readonly"]',
                'span[id*="sys_readonly"]'
            ]
            
            for selector in readonly_selectors:
                try:
                    readonly_el = container.locator(selector).first
                    # Playwright's smart wait - no time wasted!
                    readonly_el.wait_for(state='attached', timeout=1000)
                    value = readonly_el.text_content().strip()
                    if value:
                        return value
                except:
                    continue
            
            # If no read-only value, try input within container (edit mode)
            try:
                input_el = container.locator('input, textarea, select').first
                input_el.wait_for(state='attached', timeout=1000)
                
                tag_name = input_el.evaluate('el => el.tagName.toLowerCase()')
                if tag_name == 'select':
                    value = input_el.evaluate('el => el.options[el.selectedIndex]?.text || ""')
                else:
                    value = input_el.input_value()
                
                if value:
                    return value
            except:
                pass
                
        except Exception as e:
            self.logger.debug(f"[SNOW] Container approach failed for {field_id}: {e}")
        
        # APPROACH 2: Direct field lookup (legacy, reduced timeout 2000ms → 500ms)
        field_variations = [field_id]
        
        if field_id.startswith('problem.'):
            short_id = field_id.replace('problem.', '', 1)
            field_variations.append(short_id)
        
        if '.' in field_id:
            underscore_id = field_id.replace('.', '_')
            field_variations.append(underscore_id)
        
        for variation in field_variations:
            try:
                locator = self.frame.locator(f"[id='{variation}']").first
                locator.wait_for(state='attached', timeout=2000)
                
                tag_name = locator.evaluate('el => el.tagName.toLowerCase()')
                
                if tag_name == 'select':
                    value = locator.evaluate('el => el.options[el.selectedIndex]?.text || ""')
                    return value
                elif tag_name == 'textarea':
                    return locator.input_value()
                elif tag_name == 'input':
                    return locator.input_value()
                    
            except Exception as e:
                self.logger.debug(f"[SNOW] Direct lookup failed for {variation}: {e}")
                continue
        
        self.logger.warning(f"[SNOW] Field not found: {field_id}")
        return ''
    
    def extract_incident_numbers(self):
        """
        Navigate to Incidents tab and extract related INC numbers
        
        Returns:
            list: List of dicts with INC data
        """
        incidents = []
        
        try:
            # Click Incidents tab (Playwright auto-waits for clickable)
            self.frame.locator("text='Incidents'").first.click(timeout=10000)
            
            # Wait for incident table to load using element check instead of sleep
            self.frame.locator(".list_table").first.wait_for(state='visible', timeout=5000)
            
            # Find all incident rows
            rows = self.frame.locator(".list_table tr").all()
            
            for row in rows[1:]:  # Skip header
                try:
                    cells = row.locator("td").all()
                    if len(cells) >= 2:
                        inc_number = cells[0].locator("a").text_content().strip()
                        
                        inc_summary = ''
                        if len(cells) >= 3:
                            inc_summary = cells[2].text_content().strip()
                        
                        if inc_number.startswith('INC'):
                            incidents.append({
                                'number': inc_number,
                                'summary': inc_summary
                            })
                            self.logger.info(f"[SNOW] Found incident: {inc_number}")
                            
                except Exception as e:
                    self.logger.warning(f"[SNOW] Error parsing incident row: {e}")
                    continue
            
            if not incidents:
                self.logger.warning("[SNOW] No incidents found in Incidents tab")
            
            return incidents
            
        except Exception as e:
            self.logger.error(f"[SNOW] Error extracting incident numbers: {e}")
            return []
    
    def update_prb_problem_statement(self, prb_number, jira_key):
        """
        Update the PRB Problem Statement with Jira key
        
        Args:
            prb_number: PRB number to update
            jira_key: Jira key to append (e.g., 'PROJ-123')
            
        Returns:
            bool: True if update successful
        """
        try:
            if not self.navigate_to_prb(prb_number):
                return False
            
            # Find problem statement field
            field_locator = self.frame.locator("[id='problem.short_description']").first
            current_value = field_locator.input_value()
            
            if jira_key in current_value:
                self.logger.info(f"[SNOW] Jira key {jira_key} already in Problem Statement")
                return True
            
            new_value = f"{current_value} - {jira_key}"
            
            # Clear and fill (Playwright makes this easier)
            field_locator.fill(new_value)
            
            # Click save button
            self.frame.locator("[id='sysverb_update']").click()
            
            # Wait for save to complete using load state instead of sleep
            self.page.wait_for_load_state('networkidle', timeout=5000)
            
            self.logger.info(f"[SNOW] Updated PRB {prb_number} with Jira key {jira_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"[SNOW] Error updating PRB {prb_number}: {e}")
            return False
