# 🔍 Codebase Audit: Data Import/Export Architecture

## The Critical Gap You Identified

You're absolutely right. I was explaining how Selenium works for the **Dev persona** (PR sync), but that doesn't address the **PO persona's data needs**.

---

## Current State Analysis

### ✅ What EXISTS

#### 1. **Frontend UI for Data Import** (modern-ui.html)
- ✅ "Automation" tab with "Data Imports" section
- ✅ Jira Data Scraper UI (lines 231-287)
  - JQL query input
  - Field selection checkboxes
  - Auto-refresh interval
  - "Import Now" and "Test Connection" buttons
- ✅ Dependency Canvas Data section (lines 289-349)
  - Radio buttons for "From Jira" or "Upload JSON"
  - Project key input
  - JSON file upload option
  - "Load Data" button

#### 2. **GitHub Scraper** (github_scraper.py)
- ✅ Uses Selenium to extract PR data from GitHub
- ✅ Returns structured PR information
- ✅ Finds Jira ticket keys in PR titles

#### 3. **Jira Automator** (jira_automator.py)
- ✅ Uses Selenium to UPDATE Jira tickets
- ✅ Finds elements, clicks buttons, types in fields
- ✅ Changes statuses, adds labels, adds comments

---

### ❌ What's MISSING

#### 1. **No Jira Data Extractor/Scraper**
- ❌ No `jira_scraper.py` or `jira_extractor.py`
- ❌ Can't read features/epics from Jira
- ❌ No way to get feature structure from Jira
- ❌ No JQL query execution via Selenium

#### 2. **No Backend API Handlers**
- ❌ No `/api/jira/import` endpoint
- ❌ No `/api/jira/test-connection` endpoint
- ❌ No `/api/dependency/load` endpoint
- ❌ No handler to save imported data to config

#### 3. **No Data Storage/Processing**
- ❌ No way to parse Jira API response
- ❌ No CSV export/import functionality
- ❌ No JSON structure validation
- ❌ No transformation of Jira data → Waypoint format

#### 4. **No Frontend JavaScript Handlers**
- ❌ "Import Now" button has no click handler
- ❌ "Test Connection" button has no handler
- ❌ "Load Data" button has no handler
- ❌ File upload validation missing
- ❌ Status messages not implemented

---

## User Journey Gaps

### PO Persona: What SHOULD Happen

```
PO: Clicks "Automation" tab
   ├─→ UI shows Jira Data Scraper form
   ├─→ User enters JQL: "project = MYPROJ AND type = Epic"
   ├─→ User clicks "Test Connection"
   │   ❌ MISSING: Backend handler to test Jira connection
   │
   ├─→ User clicks "Import Now"
   │   ❌ MISSING: Backend handler to:
   │       • Execute JQL query via Selenium
   │       • Extract features/epics from Jira
   │       • Parse response
   │       • Transform to feature structure
   │       • Save to config or temp storage
   │
   ├─→ User clicks "PO" tab
   │   ✅ UI shows features
   │   ❌ MISSING: Features list is empty (no data source)
   │
   └─→ User sees dependency canvas
       ❌ MISSING: No data extraction from Jira
```

---

## What Needs to Be Built

### Phase 1: Jira Data Extraction (Priority 1)

**New file: `jira_scraper.py`**
```python
class JiraScraper:
    """Extract features, epics, and dependencies from Jira"""
    
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
    
    def execute_jql(self, jql_query):
        """Execute JQL query via Jira web UI and return results"""
        # Navigate to Jira search
        # Enter JQL
        # Parse results
        # Return structured data
    
    def get_epics(self, project_key):
        """Get all epics from project"""
        # JQL: "project = KEY AND type = Epic"
    
    def get_stories(self, epic_key):
        """Get all stories under an epic"""
        # JQL: "parent = EPIC_KEY"
    
    def get_dependencies(self, issue_key):
        """Get dependencies/blockers for issue"""
        # Parse issue links
        # Extract relationships
    
    def get_metrics(self, issue_key):
        """Get metrics (story points, cycle time, etc)"""
        # Parse custom fields
        # Return structured metrics
```

### Phase 2: Backend API Handlers (Priority 1)

**New in `app.py`:**
```python
def _handle_jira_import(self, data):
    """Import features from Jira"""
    # Get JQL query from request
    # Create JiraScraper
    # Execute query
    # Return results
    
def _handle_jira_test_connection(self, data):
    """Test Jira connection"""
    # Try to navigate to Jira
    # Check if authenticated
    # Return status

def _handle_dependency_load(self, data):
    """Load dependency data"""
    # Check if from Jira or JSON
    # Extract data
    # Save to config
```

### Phase 3: Data Transformation (Priority 2)

**New file: `data_transformer.py`**
```python
class DataTransformer:
    """Transform Jira data to Waypoint format"""
    
    def jira_to_features(self, jira_response):
        """Convert Jira epics to feature structure"""
        # Transform: Epic → Feature
        # Group: Stories → Child issues
        # Calculate: Progress, status
        # Return: [{name, key, status, children: [...]}]
    
    def jira_to_dependencies(self, jira_issues):
        """Convert Jira links to dependency structure"""
        # Parse issue links
        # Build dependency graph
        # Identify blockers
        # Return: [{key, blockers: [...]}, ...]
    
    def csv_to_features(self, csv_data):
        """Import from CSV export"""
        # Parse CSV
        # Transform to feature structure
    
    def validate_feature_json(self, json_data):
        """Validate feature JSON structure"""
        # Check required fields
        # Return validation errors
```

### Phase 4: Config Storage (Priority 2)

**Update config.yaml structure:**
```yaml
jira:
  base_url: https://company.atlassian.net
  project_key: MYPROJ
  
data_sources:
  features:
    source: jira  # or 'csv', 'json', 'manual'
    jql_query: "project = MYPROJ AND type = Epic"
    last_import: 2025-12-26T01:15:50Z
    auto_refresh: 60  # minutes
    
  dependencies:
    source: jira  # or 'json'
    project_keys: MYPROJ, SHARED
    issue_limit: 500
    last_import: 2025-12-26T01:15:50Z
    
imported_data:
  features: [...]  # Stored feature structure
  dependencies: [...]  # Stored dependency graph
```

---

## Current Data Flow (What's Broken)

```
PO Wants Features
  ↓
Clicks "Import Now"
  ↓
Frontend sends POST to... NOWHERE ❌
  ↓
No backend handler
  ↓
Jira data NEVER extracted
  ↓
PO sees empty feature list ❌
```

---

## What Should Happen

```
PO Wants Features
  ↓
Clicks "Import Now"
  ↓
Frontend sends POST /api/jira/import ✅
  ↓
Backend: JiraScraper.execute_jql("project = MYPROJ AND type = Epic") ✅
  ↓
Selenium navigates to Jira ✅
  ↓
Selenium searches with JQL ✅
  ↓
Selenium parses HTML results ✅
  ↓
DataTransformer converts to feature structure ✅
  ↓
Saves to config.yaml ✅
  ↓
Frontend updates PO tab ✅
  ↓
PO sees: Features ✅ + Dependency Canvas ✅ + Metrics ✅
```

---

## File-by-File Status

### ✅ Files That Exist and Work
- `app.py` - Main backend, but missing handlers
- `modern-ui.html` - UI is there, but no JS handlers
- `github_scraper.py` - Works for GitHub
- `jira_automator.py` - Works for updating Jira
- `sync_engine.py` - Orchestrates sync
- `config.yaml` - Configuration

### ❌ Files That Are Missing
- `jira_scraper.py` - **CRITICAL** - Extract data from Jira
- `data_transformer.py` - Transform to Waypoint format
- `data_validator.py` - Validate imported data
- `csv_parser.py` - Handle CSV imports
- Frontend JavaScript handlers for import buttons

### ❌ Features That Are Missing
- API endpoint: `/api/jira/import`
- API endpoint: `/api/jira/test-connection`
- API endpoint: `/api/dependency/load`
- API endpoint: `/api/features/save`
- JavaScript event handlers for import buttons
- Data validation and error handling
- CSV/JSON file parsing
- Transformation pipeline

---

## The Real User Journey (What You Need)

### For PO Persona

**Step 1: Configure Jira Data Source**
```
User navigates to: Automation → Data Imports → Jira Data Scraper
User enters: JQL = "project = MYPROJ AND type = Epic"
User clicks: "Test Connection"
  → Backend should test Jira auth and connectivity
  
User clicks: "Import Now"
  → Backend should:
    1. Execute JQL via Selenium
    2. Parse results
    3. Extract feature structure
    4. Save to config
    5. Return success status
```

**Step 2: View Features**
```
User navigates to: PO tab
  → Features & Epics section should be POPULATED
  → Shows hierarchical list of imported features
  → Shows progress/status
  → Shows child stories
  
User navigates to: Dependency Canvas
  → Should show dependency graph
  → Should show blockers
  → Interactive visualization
```

**Step 3: Optional - Export to CSV**
```
User clicks: "Export Features"
  → Downloads CSV with current features
User clicks: "Export Dependencies"
  → Downloads CSV with dependency structure
```

---

## What's ACTUALLY in Place vs Missing

| Feature | UI | Backend | Data Flow | Status |
|---------|----|---------|-----------| ------|
| **Jira Data Import** | ✅ Yes | ❌ No | ❌ Broken | **CRITICAL** |
| **Dependency Loading** | ✅ Yes | ❌ No | ❌ Broken | **CRITICAL** |
| **Feature Display** | ✅ Yes | ❌ No data | ❌ Broken | **CRITICAL** |
| **CSV Import** | ❌ No | ❌ No | ❌ Broken | **HIGH** |
| **CSV Export** | ❌ No | ❌ No | ❌ Broken | **HIGH** |
| **Metrics Collection** | ✅ UI exists | ❌ No | ❌ Broken | **MEDIUM** |
| **GitHub Sync** | ✅ Yes | ✅ Yes | ✅ Works | ✅ DONE |
| **Jira Updates** | ✅ Yes | ✅ Yes | ✅ Works | ✅ DONE |

---

## Summary

**The core issue:** The UI exists for PO data import, but there's **zero backend implementation** to extract data from Jira and make it available to the frontend.

**What's needed:**
1. ✅ **Jira Scraper** - Extract features/epics/dependencies
2. ✅ **Backend Handlers** - `/api/jira/import`, `/api/dependency/load`
3. ✅ **Data Transformer** - Convert Jira → Waypoint format
4. ✅ **Config Storage** - Save imported data persistently
5. ✅ **Frontend Handlers** - Wire up import buttons
6. ✅ **CSV Support** - Parse/export CSV files

**Without this:** The PO persona cannot actually use Waypoint to view their features because there's no way to get feature data into the system!

This is exactly what you were pointing out. The UI promises functionality that the backend doesn't support yet.
