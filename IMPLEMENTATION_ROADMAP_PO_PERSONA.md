# 🛣️ Implementation Roadmap: Fixing the PO Persona Data Flow

## Status Summary

| Persona | Data Import | Data Display | Data Export | Status |
|---------|---|---|---|---|
| **PO** | ❌ Broken | ❌ Empty | ❌ Missing | 🚨 NOT FUNCTIONAL |
| **Dev** | ✅ Works | ✅ Shows Sync Status | ❌ N/A | ✅ FUNCTIONAL |
| **SM** | ⚠️ Partial | ✅ Shows Insights | ❌ Missing | ⚠️ PARTIAL |

---

## What's Blocking the PO Persona

### The User Clicks This
```
Automation Tab → Data Imports → Jira Data Scraper → "Import Now"
```

### What Currently Happens
```
Button click → No handler found → Nothing happens → User confused
```

### What Should Happen
```
Button click 
  → POST /api/jira/import
  → JiraScraper.execute_jql()
  → Selenium extracts data from Jira
  → DataTransformer converts to features
  → Saves to config
  → Frontend updates PO tab
  → User sees features + dependencies + metrics
```

---

## Implementation Roadmap

### ✅ DONE (Already in Place)
- Frontend UI for data import
- GitHub scraper with Selenium
- Jira automator with Selenium
- Sync engine orchestration

### ❌ TODO (Blocking PO Persona)

#### **Phase 1: Core Data Extraction (Week 1)**

**1.1 Create `jira_scraper.py`**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
import re

class JiraScraper:
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
    
    def execute_jql(self, jql_query):
        """Execute JQL and extract results"""
        # Navigate to Jira search
        # Enter JQL query
        # Parse HTML results
        # Return structured data
        
    def get_epics(self, project_key):
        """Get all epics from project"""
        jql = f'project = "{project_key}" AND type = Epic'
        return self.execute_jql(jql)
    
    def get_stories(self, epic_key):
        """Get stories under epic"""
        jql = f'parent = "{epic_key}"'
        return self.execute_jql(jql)
    
    def parse_issue_links(self, issue_html):
        """Extract dependencies and blockers"""
        # Find links section
        # Parse dependency relationships
        # Return blockers and blocks
```

**1.2 Add Backend Handlers (in `app.py`)**
```python
def _handle_jira_import(self, data):
    """POST /api/jira/import"""
    try:
        jql_query = data.get('jql_query', 'project = MYPROJ')
        include_fields = data.get('include_fields', {})
        
        scraper = JiraScraper(driver, self.config)
        results = scraper.execute_jql(jql_query)
        
        # Save results
        imported_data = {
            'features': results,
            'timestamp': datetime.now().isoformat(),
            'query': jql_query
        }
        
        # Update config
        self.config['imported_data'] = imported_data
        
        return {'success': True, 'count': len(results), 'data': results}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def _handle_jira_test_connection(self, data):
    """POST /api/jira/test-connection"""
    try:
        if driver is None:
            return {'success': False, 'error': 'Browser not initialized'}
        
        jira_url = data.get('jira_url', self.config['jira']['base_url'])
        driver.get(jira_url)
        time.sleep(1)
        
        # Check if we can see Jira (not logged out)
        current_url = driver.current_url
        is_logged_in = 'login' not in current_url.lower()
        
        return {
            'success': True,
            'connected': True,
            'authenticated': is_logged_in,
            'message': 'Connected to Jira'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

#### **Phase 2: Data Transformation (Week 1)**

**2.1 Create `data_transformer.py`**
```python
class DataTransformer:
    @staticmethod
    def jira_to_features(jira_issues):
        """Transform Jira epics/stories to feature structure"""
        features = []
        
        for epic in jira_issues:
            if epic.get('type') != 'Epic':
                continue
            
            feature = {
                'key': epic.get('key'),
                'name': epic.get('summary'),
                'status': epic.get('status'),
                'progress': calculate_progress(epic),
                'children': [
                    {
                        'key': story.get('key'),
                        'name': story.get('summary'),
                        'status': story.get('status'),
                        'assignee': story.get('assignee'),
                        'points': story.get('story_points', 0)
                    }
                    for story in epic.get('child_issues', [])
                ]
            }
            features.append(feature)
        
        return features
    
    @staticmethod
    def jira_to_dependencies(jira_issues):
        """Extract dependency graph from Jira"""
        dependencies = {}
        
        for issue in jira_issues:
            issue_key = issue.get('key')
            blockers = []
            
            for link in issue.get('issue_links', []):
                if link.get('type') in ['is blocked by', 'depends on']:
                    blockers.append({
                        'blocker': link.get('linked_key'),
                        'description': link.get('description', '')
                    })
            
            if blockers:
                dependencies[issue_key] = blockers
        
        return dependencies
    
    @staticmethod
    def csv_to_features(csv_data):
        """Import features from CSV file"""
        # Parse CSV
        # Validate structure
        # Convert to feature objects
        pass
```

**2.2 Update Config Structure**

```yaml
# config.yaml additions
jira:
  base_url: https://company.atlassian.net
  project_key: MYPROJ

data_imports:
  features:
    enabled: true
    source: jira  # or 'csv', 'json'
    jql_query: "project = MYPROJ AND type = Epic"
    auto_refresh_minutes: 60
    last_import: null
    last_error: null
  
  dependencies:
    enabled: true
    source: jira
    include_blockers: true
    last_import: null
    last_error: null

imported_data:
  features: []
  dependencies: {}
  metrics: {}
  last_update: null
```

#### **Phase 3: Frontend Integration (Week 1)**

**3.1 Add JavaScript Handlers (in `modern-ui.html`)**

```javascript
// Jira Import Handler
document.getElementById('jira-import-btn').addEventListener('click', async function() {
    const jqlQuery = document.getElementById('jira-jql-query').value;
    const statusDiv = document.getElementById('jira-import-status');
    
    try {
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = '<p>Importing...</p>';
        
        const response = await fetch('/api/jira/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jql_query: jqlQuery,
                include_fields: {
                    epics: true,
                    stories: true,
                    dependencies: true,
                    metrics: true
                }
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusDiv.innerHTML = `<p>✅ Imported ${result.count} items</p>`;
            // Reload PO tab
            loadPoTab();
        } else {
            statusDiv.innerHTML = `<p>❌ Error: ${result.error}</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<p>❌ Error: ${error.message}</p>`;
    }
});

// Test Connection Handler
document.getElementById('jira-test-btn').addEventListener('click', async function() {
    try {
        const response = await fetch('/api/jira/test-connection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.success && result.authenticated) {
            alert('✅ Connected to Jira');
        } else {
            alert('❌ Not authenticated to Jira. Please log in first.');
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
});

// Load Dependency Data
document.getElementById('dep-load-btn').addEventListener('click', async function() {
    const source = document.querySelector('input[name="dep-source"]:checked').value;
    
    let data = { source: source };
    
    if (source === 'jira') {
        data.project_keys = document.getElementById('dep-jira-keys').value;
        data.issue_limit = parseInt(document.getElementById('dep-jira-limit').value);
    } else {
        const file = document.getElementById('dep-json-file').files[0];
        if (!file) {
            alert('Please select a JSON file');
            return;
        }
        data.file = await file.text();
    }
    
    try {
        const response = await fetch('/api/dependency/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ Dependencies loaded');
            loadPoTab();  // Refresh PO tab
        } else {
            alert(`❌ Error: ${result.error}`);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
});
```

---

## Testing Checklist

### Manual Testing

- [ ] User navigates to Automation → Data Imports
- [ ] User enters JQL query: `project = MYPROJ AND type = Epic`
- [ ] User clicks "Test Connection"
  - [ ] Should show "Connected to Jira" or "Not authenticated"
- [ ] User clicks "Import Now"
  - [ ] Should show loading state
  - [ ] Should show success with count
  - [ ] Should not block UI
- [ ] User navigates to PO tab
  - [ ] Features should be populated
  - [ ] Dependencies should show
  - [ ] Metrics should display
- [ ] User clicks "Load Data" for dependencies
  - [ ] Should load from Jira or JSON
  - [ ] Dependency canvas should populate

### Unit Tests Needed

```python
# tests/test_jira_scraper.py
def test_execute_jql_returns_issues()
def test_get_epics_filters_correctly()
def test_parse_issue_links_extracts_blockers()

# tests/test_data_transformer.py
def test_jira_to_features_transforms_structure()
def test_jira_to_dependencies_extracts_relationships()
def test_csv_to_features_parses_csv()

# tests/test_api_handlers.py
def test_jira_import_handler_returns_data()
def test_jira_test_connection_returns_status()
```

---

## Success Criteria

### Phase Complete When:

1. ✅ `JiraScraper` class exists and can extract features from Jira
2. ✅ `/api/jira/import` endpoint returns feature list
3. ✅ `/api/jira/test-connection` endpoint tests auth
4. ✅ Features display in PO tab after import
5. ✅ Dependencies display in dependency canvas
6. ✅ User can export features to CSV
7. ✅ All error cases handled gracefully

### User Can Actually:

1. ✅ Click "Import Now" and see results
2. ✅ View imported features in PO tab
3. ✅ See dependency canvas populated
4. ✅ Understand what went wrong if it fails
5. ✅ Re-import when data changes in Jira

---

## Time Estimate

- **Phase 1**: 4-6 hours (Jira scraper + API handlers)
- **Phase 2**: 2-3 hours (Data transformer + config)
- **Phase 3**: 2-3 hours (Frontend wiring + testing)
- **Testing**: 2-3 hours (Unit tests + manual testing)

**Total**: ~12-15 hours of focused development

---

## Current Blockers

🚨 **These must be done BEFORE the PO persona can work:**

1. Jira scraper with Selenium
2. Backend API handlers
3. Data transformer
4. Frontend event handlers
5. Config storage structure

**Without these**, the import buttons are just placeholders.

---

## Success Metrics

Once complete:

- PO persona is fully functional
- Users can import features from Jira
- Features display with hierarchy and status
- Dependencies show in canvas
- User journey is complete
- Data persists across sessions
