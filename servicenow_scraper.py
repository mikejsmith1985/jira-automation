"""
ServiceNow scraper module - Playwright version
Handles data extraction from ServiceNow PRB tickets via browser automation
Now using Playwright for better modern web app support and native Shadow DOM handling
"""
import time
import logging
import os

class ServiceNowScraper:
    """Scrapes data from ServiceNow Problem (PRB) tickets using Playwright"""
    
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
        
        # Log configuration for debugging
        self.logger.info(f"[SNOW] ServiceNowScraper initialized (Playwright)")
        # Normalize base_url - remove trailing slash to prevent double slashes
        self.base_url = self.base_url.rstrip('/') if self.base_url else ''
        self.logger.info(f"[SNOW] Base URL: '{self.base_url}'")
        if not self.base_url:
            self.logger.error("[SNOW] ERROR: ServiceNow URL is empty or not configured!")
            self.logger.error("[SNOW] Please configure ServiceNow URL in Integrations tab")
        
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
        Navigate to a specific PRB ticket
        
        Args:
            prb_number: The PRB number (e.g., 'PRB0123456')
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            if not self.base_url:
                raise ValueError("ServiceNow URL not configured")
            
            prb_url = f"{self.base_url}/problem.do?sysparm_query=number={prb_number}"
            self.logger.info(f"[SNOW] Navigating to PRB: {prb_url}")
            
            # Playwright's goto with networkidle waits for page to fully load
            # This will wait through SAML redirects
            self.page.goto(prb_url, wait_until='networkidle', timeout=30000)
            
            # After SAML redirect, we might be on the homepage, not the PRB page
            # Check the final URL
            final_url = self.page.url
            self.logger.info(f"[SNOW] Page loaded, final URL: {final_url}")
            
            # If we got redirected away from the PRB page (SAML redirect to home)
            if 'problem.do' not in final_url and prb_number not in final_url:
                self.logger.warning(f"[SNOW] SAML redirect detected - landed on {final_url} instead of PRB page")
                self.logger.info(f"[SNOW] Attempting to navigate to PRB again...")
                
                # Try navigating again - should work now that SAML auth is complete
                self.page.goto(prb_url, wait_until='networkidle', timeout=30000)
                final_url = self.page.url
                self.logger.info(f"[SNOW] Second attempt - final URL: {final_url}")
            
            self.logger.info(f"[SNOW] Page loaded, checking for PRB...")
            
            # Quick check: Is PRB in page content?
            page_content = self.page.content()
            if prb_number not in page_content:
                self.logger.error(f"[SNOW] PRB {prb_number} not found in page source")
                self.logger.error(f"[SNOW] Current URL: {self.page.url}")
                self.logger.error(f"[SNOW] This usually means:")
                self.logger.error(f"[SNOW]   1. PRB doesn't exist or is misspelled")
                self.logger.error(f"[SNOW]   2. SAML/SSO redirected to login or home page")
                self.logger.error(f"[SNOW]   3. You don't have permission to view this PRB")
                return False
            
            self.logger.info(f"[SNOW] PRB {prb_number} confirmed in page source")
            
            # Check if we're in an iframe context (ServiceNow often uses gsft_main)
            # Playwright handles iframes more elegantly than Selenium
            try:
                # Try to find the main iframe
                frame = self.page.frame_locator('#gsft_main')
                # Test if frame exists by trying to find body in it
                frame.locator('body').wait_for(state='attached', timeout=5000)
                self.logger.info("[SNOW] Found gsft_main iframe, using frame context")
                self.frame = frame
            except Exception:
                self.logger.info("[SNOW] No gsft_main iframe, using main page context")
                # Use main page as "frame"
                self.frame = self.page
            
            # Try to find form fields with Playwright's smart waiting
            # Playwright automatically pierces Shadow DOM and handles dynamic content!
            form_found = False
            
            # Try multiple selectors (Playwright will wait automatically)
            selectors_to_try = [
                "[id='problem.short_description']",
                "[id='short_description']",
                "[id='problem.description']",
                "[id='description']",
                "[id='problem.number']",
                "[id='number']",
            ]
            
            for selector in selectors_to_try:
                try:
                    self.logger.info(f"[SNOW] Trying selector: {selector}")
                    # Playwright waits automatically, timeout 3s per selector
                    locator = self.frame.locator(selector).first
                    locator.wait_for(state='attached', timeout=3000)
                    self.logger.info(f"[SNOW] ✓ Found element: {selector}")
                    form_found = True
                    break
                except Exception as e:
                    self.logger.debug(f"[SNOW] Selector {selector} not found: {e}")
                    continue
            
            if not form_found:
                # Enhanced debugging: Use JavaScript to find ALL elements with IDs
                self.logger.warning("[SNOW] Form fields not found with standard selectors")
                self.logger.info("[SNOW] Running JavaScript debug to find all IDs on page...")
                
                try:
                    # Execute JavaScript to find all element IDs
                    all_ids = self.page.evaluate("""
                        () => {
                            const elements = document.querySelectorAll('[id]');
                            return Array.from(elements).slice(0, 50).map(el => ({
                                id: el.id,
                                tag: el.tagName,
                                type: el.type || 'N/A',
                                visible: el.offsetParent !== null
                            }));
                        }
                    """)
                    self.logger.warning(f"[SNOW] Found {len(all_ids)} elements with IDs:")
                    for elem in all_ids[:20]:  # Log first 20
                        self.logger.info(f"[SNOW]   - {elem['id']} ({elem['tag']}, visible={elem['visible']})")
                except Exception as e:
                    self.logger.error(f"[SNOW] Could not execute debug JavaScript: {e}")
                
                # Check for Shadow DOM
                try:
                    shadow_roots = self.page.evaluate("""
                        () => {
                            const findShadowRoots = (root = document.body) => {
                                const shadows = [];
                                root.querySelectorAll('*').forEach(el => {
                                    if (el.shadowRoot) {
                                        shadows.push(el.tagName);
                                    }
                                });
                                return shadows;
                            };
                            return findShadowRoots();
                        }
                    """)
                    if shadow_roots:
                        self.logger.warning(f"[SNOW] Found Shadow DOM roots: {shadow_roots}")
                        self.logger.info("[SNOW] Playwright should pierce these automatically")
                    else:
                        self.logger.info("[SNOW] No Shadow DOM detected")
                except Exception as e:
                    self.logger.error(f"[SNOW] Could not check for Shadow DOM: {e}")
                
                # Try ServiceNow's GlideForm API (JavaScript-based field access)
                try:
                    self.logger.info("[SNOW] Attempting ServiceNow GlideForm API...")
                    glide_form_data = self.page.evaluate("""
                        () => {
                            if (typeof g_form !== 'undefined') {
                                return {
                                    hasGlideForm: true,
                                    number: g_form.getValue('number'),
                                    short_description: g_form.getValue('short_description'),
                                    description: g_form.getValue('description')
                                };
                            }
                            return {hasGlideForm: false};
                        }
                    """)
                    
                    if glide_form_data.get('hasGlideForm'):
                        self.logger.info(f"[SNOW] ✓ GlideForm API available!")
                        self.logger.info(f"[SNOW] Number: {glide_form_data.get('number')}")
                        self.logger.info(f"[SNOW] Short desc: {glide_form_data.get('short_description', '')[:50]}...")
                        # We can use GlideForm as fallback!
                        self.use_glide_form = True
                        form_found = True
                    else:
                        self.logger.warning("[SNOW] GlideForm API not available")
                        self.use_glide_form = False
                except Exception as e:
                    self.logger.error(f"[SNOW] Error checking GlideForm API: {e}")
                    self.use_glide_form = False
                
                # Save debug HTML
                if not form_found:
                    try:
                        # Try to import DATA_DIR, if fails use current directory
                        try:
                            from app import DATA_DIR
                        except:
                            DATA_DIR = os.getcwd()
                        debug_file = os.path.join(DATA_DIR, "snow_debug.html")
                        html_content = self.page.content()
                        with open(debug_file, "w", encoding="utf-8") as f:
                            f.write(html_content)
                        self.logger.info(f"[SNOW] Saved page HTML to: {debug_file}")
                    except Exception as e:
                        self.logger.warning(f"[SNOW] Could not save debug HTML: {e}")
                    
                    self.logger.error(f"[SNOW] Could not find form fields for {prb_number}")
                    return False
            
            self.logger.info(f"[SNOW] ✓ Successfully navigated to PRB {prb_number}")
            return self.login_check()
            
        except Exception as e:
            self.logger.error(f"[SNOW] Error navigating to PRB {prb_number}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def extract_prb_data(self):
        """
        Extract all relevant fields from the current PRB ticket
        
        Returns:
            dict: PRB data with keys matching ServiceNow field names
        """
        prb_data = {}
        
        try:
            prb_data['prb_number'] = self._get_field_value('problem.number')
            prb_data['short_description'] = self._get_field_value('problem.short_description')
            prb_data['description'] = self._get_field_value('problem.description')
            prb_data['configuration_item'] = self._get_field_value('sys_display.problem.cmdb_ci')
            prb_data['impact'] = self._get_field_value('problem.impact')
            prb_data['urgency'] = self._get_field_value('problem.urgency')
            prb_data['priority'] = self._get_field_value('problem.priority')
            prb_data['problem_category'] = self._get_field_value('problem.u_problem_category')
            prb_data['detection'] = self._get_field_value('problem.u_dectection')
            
            self.logger.info(f"[SNOW] Extracted PRB data: {prb_data.get('prb_number', 'Unknown')}")
            return prb_data
            
        except Exception as e:
            self.logger.error(f"[SNOW] Error extracting PRB data: {e}")
            return None
    
    def _get_field_value(self, field_id):
        """
        Get value from a ServiceNow form field using Playwright
        
        Playwright advantages over Selenium:
        - Automatically pierces Shadow DOM
        - Smart auto-waiting
        - Better handling of modern web apps
        
        Args:
            field_id: Field ID (e.g., 'problem.short_description')
            
        Returns:
            str: Field value or empty string if not found
        """
        # If GlideForm API is available, use it as primary method
        if hasattr(self, 'use_glide_form') and self.use_glide_form:
            try:
                # Extract field name from ID (remove 'problem.' prefix if present)
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
                    self.logger.debug(f"[SNOW] Got value for {field_id} via GlideForm")
                    return value
            except Exception as e:
                self.logger.debug(f"[SNOW] GlideForm failed for {field_id}: {e}")
        
        # Try multiple variations of the field ID
        field_variations = [
            field_id,  # Original (e.g., "problem.short_description")
        ]
        
        # If field has "problem." prefix, also try without it
        if field_id.startswith('problem.'):
            short_id = field_id.replace('problem.', '', 1)
            field_variations.append(short_id)  # e.g., "short_description"
        
        # If field has dots, also try with underscores
        if '.' in field_id:
            underscore_id = field_id.replace('.', '_')
            field_variations.append(underscore_id)
        
        self.logger.debug(f"[SNOW] Looking for field: {field_id} (variations: {field_variations})")
        
        for variation in field_variations:
            try:
                # Use Playwright's locator (auto-waits, pierces Shadow DOM)
                locator = self.frame.locator(f"[id='{variation}']").first
                
                # Check if element exists (with short timeout)
                try:
                    locator.wait_for(state='attached', timeout=2000)
                except:
                    continue  # Element doesn't exist, try next variation
                
                # Get the element's tag name to determine how to extract value
                tag_name = locator.evaluate('el => el.tagName.toLowerCase()')
                
                if tag_name == 'select':
                    # For select elements, get selected option text
                    value = locator.evaluate('el => el.options[el.selectedIndex]?.text || ""')
                    return value
                elif tag_name == 'textarea':
                    # For textarea, use input_value()
                    return locator.input_value()
                else:
                    # For input fields, use input_value()
                    return locator.input_value()
                    
            except Exception as e:
                self.logger.debug(f"[SNOW] Error reading field {variation}: {e}")
                continue
        
        # None of the variations worked
        self.logger.warning(f"[SNOW] Field not found: {field_id} (tried: {', '.join(field_variations)})")
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
            
            # Wait for incident table to load
            time.sleep(2)
            
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
            
            time.sleep(2)
            
            self.logger.info(f"[SNOW] Updated PRB {prb_number} with Jira key {jira_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"[SNOW] Error updating PRB {prb_number}: {e}")
            return False
