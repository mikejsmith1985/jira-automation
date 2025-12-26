# 🏗️ Implementation Plan: Complete Backend Data Flow

## Executive Summary

Building a **plugin-based architecture** for data exchange with:
- **Core UI/Interface** - How users interact with data
- **Extension System** - Pluggable adapters for Jira, GitHub, future integrations
- **Flexible Configuration** - UI-driven settings backed by scalable YAML/SQLite storage

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WAYPOINT CORE                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │   UI Layer      │  │  API Layer      │  │  Config Manager     │ │
│  │  (modern-ui)    │  │  (app.py)       │  │  (config.yaml +     │ │
│  │                 │  │                 │  │   SQLite)           │ │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘ │
│           │                    │                       │            │
│           └────────────────────┼───────────────────────┘            │
│                                │                                    │
│  ┌─────────────────────────────┴─────────────────────────────────┐ │
│  │                    EXTENSION MANAGER                          │ │
│  │  - Loads/unloads extensions                                   │ │
│  │  - Manages extension lifecycle                                │ │
│  │  - Routes requests to appropriate extension                   │ │
│  └─────────────────────────────┬─────────────────────────────────┘ │
└────────────────────────────────┼────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ JIRA EXTENSION    │  │ GITHUB EXTENSION  │  │ FUTURE EXTENSIONS │
│ (jira_extension/) │  │ (github_extension)│  │ (csv, api, etc)   │
│                   │  │                   │  │                   │
│ - JiraScraper     │  │ - GitHubScraper   │  │ - Plugin interface│
│ - JiraUpdater     │  │ - GitHubAPI       │  │ - Config schema   │
│ - JiraTransformer │  │ - PRTransformer   │  │ - UI components   │
│ - Config schema   │  │ - Config schema   │  │                   │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

---

## Phase 1: Core Extension System

### 1.1 Base Extension Interface

**File: `extensions/base_extension.py`**

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BaseExtension(ABC):
    """Base class for all Waypoint extensions"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique extension identifier"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for UI"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version"""
        pass
    
    @property
    @abstractmethod
    def config_schema(self) -> Dict:
        """JSON schema for extension configuration"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict) -> bool:
        """Initialize extension with config"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict:
        """Test if extension can connect to its data source"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities: ['read', 'write', 'bulk_update', etc]"""
        pass


class DataSourceExtension(BaseExtension):
    """Extension that can read data from external source"""
    
    @abstractmethod
    def extract_data(self, query: Dict) -> Dict:
        """Extract data based on query parameters"""
        pass
    
    @abstractmethod
    def transform_to_features(self, raw_data: Any) -> List[Dict]:
        """Transform raw data to Waypoint feature structure"""
        pass
    
    @abstractmethod
    def transform_to_dependencies(self, raw_data: Any) -> Dict:
        """Transform raw data to dependency graph"""
        pass


class DataSinkExtension(BaseExtension):
    """Extension that can write data to external source"""
    
    @abstractmethod
    def update_single(self, identifier: str, updates: Dict) -> bool:
        """Update a single item"""
        pass
    
    @abstractmethod
    def update_bulk(self, query: Dict, updates: Dict) -> Dict:
        """Bulk update items matching query"""
        pass
```

### 1.2 Extension Manager

**File: `extensions/extension_manager.py`**

```python
class ExtensionManager:
    """Manages loading, configuration, and lifecycle of extensions"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.extensions = {}
        self.config_path = config_path
        self.load_config()
    
    def register_extension(self, extension: BaseExtension):
        """Register an extension"""
        self.extensions[extension.name] = extension
    
    def get_extension(self, name: str) -> Optional[BaseExtension]:
        """Get extension by name"""
        return self.extensions.get(name)
    
    def list_extensions(self) -> List[Dict]:
        """List all registered extensions with status"""
        pass
    
    def configure_extension(self, name: str, config: Dict) -> bool:
        """Update extension configuration"""
        pass
    
    def get_data_sources(self) -> List[DataSourceExtension]:
        """Get all extensions that can read data"""
        pass
    
    def get_data_sinks(self) -> List[DataSinkExtension]:
        """Get all extensions that can write data"""
        pass
```

---

## Phase 2: Jira Extension

### 2.1 Jira Scraper (Data Extraction)

**File: `extensions/jira/jira_scraper.py`**

```python
class JiraScraper:
    """Extract data from Jira via Selenium"""
    
    def __init__(self, driver, config: Dict):
        self.driver = driver
        self.config = config
        self.base_url = config.get('base_url')
    
    def execute_jql(self, jql: str, max_results: int = 500) -> List[Dict]:
        """Execute JQL query and return results"""
        # Navigate to Jira search
        # Enter JQL
        # Parse results table
        # Handle pagination
        pass
    
    def get_issue_details(self, issue_key: str) -> Dict:
        """Get full details for a single issue"""
        # Navigate to issue
        # Extract all fields
        # Extract links/dependencies
        pass
    
    def get_issue_links(self, issue_key: str) -> List[Dict]:
        """Extract issue links (blockers, dependencies)"""
        pass
    
    def get_epic_children(self, epic_key: str) -> List[Dict]:
        """Get all issues under an epic"""
        jql = f'"Epic Link" = {epic_key}'
        return self.execute_jql(jql)
    
    def get_sprint_issues(self, sprint_name: str) -> List[Dict]:
        """Get all issues in a sprint"""
        jql = f'sprint = "{sprint_name}"'
        return self.execute_jql(jql)
```

### 2.2 Jira Updater (Data Writing)

**File: `extensions/jira/jira_updater.py`**

```python
class JiraUpdater:
    """Update Jira tickets via Selenium"""
    
    def __init__(self, driver, config: Dict):
        self.driver = driver
        self.config = config
    
    def update_issue(self, issue_key: str, updates: Dict) -> bool:
        """Update a single issue with specified changes"""
        # Navigate to issue
        # Apply each update type
        pass
    
    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add comment to issue"""
        pass
    
    def update_field(self, issue_key: str, field_id: str, value: Any) -> bool:
        """Update a specific field"""
        pass
    
    def add_label(self, issue_key: str, label: str) -> bool:
        """Add label to issue"""
        pass
    
    def transition_status(self, issue_key: str, status: str) -> bool:
        """Transition issue to new status"""
        pass
    
    def bulk_update(self, jql: str, updates: Dict) -> Dict:
        """
        Apply updates to all issues matching JQL
        Returns: {success: int, failed: int, errors: [...]}
        """
        issues = self.scraper.execute_jql(jql)
        results = {'success': 0, 'failed': 0, 'errors': []}
        
        for issue in issues:
            try:
                self.update_issue(issue['key'], updates)
                results['success'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({'key': issue['key'], 'error': str(e)})
        
        return results
```

### 2.3 Jira Data Transformer

**File: `extensions/jira/jira_transformer.py`**

```python
class JiraTransformer:
    """Transform Jira data to Waypoint structures"""
    
    @staticmethod
    def to_feature_structure(issues: List[Dict]) -> List[Dict]:
        """
        Transform Jira issues to feature hierarchy
        Input: Flat list of Jira issues
        Output: Hierarchical feature structure for PO view
        """
        features = []
        epics = [i for i in issues if i.get('type') == 'Epic']
        
        for epic in epics:
            feature = {
                'key': epic['key'],
                'name': epic['summary'],
                'status': epic['status'],
                'priority': epic.get('priority'),
                'assignee': epic.get('assignee'),
                'progress': 0,
                'children': []
            }
            
            # Find child issues
            children = [i for i in issues if i.get('epic_link') == epic['key']]
            done_count = sum(1 for c in children if c['status'] == 'Done')
            
            feature['children'] = children
            feature['progress'] = (done_count / len(children) * 100) if children else 0
            
            features.append(feature)
        
        return features
    
    @staticmethod
    def to_dependency_graph(issues: List[Dict]) -> Dict:
        """
        Build dependency graph from issue links
        Output: {issue_key: {blockers: [...], blocks: [...]}}
        """
        graph = {}
        
        for issue in issues:
            key = issue['key']
            graph[key] = {
                'title': issue['summary'],
                'status': issue['status'],
                'blockers': [],
                'blocks': []
            }
            
            for link in issue.get('links', []):
                if link['type'] in ['is blocked by', 'depends on']:
                    graph[key]['blockers'].append(link['target'])
                elif link['type'] in ['blocks', 'is dependency of']:
                    graph[key]['blocks'].append(link['target'])
        
        return graph
    
    @staticmethod
    def to_metrics(issues: List[Dict], mode: str = 'scrum') -> Dict:
        """
        Calculate metrics for SM reporting
        Mode: 'scrum' or 'kanban'
        """
        metrics = {
            'total_issues': len(issues),
            'by_status': {},
            'by_type': {},
            'by_assignee': {}
        }
        
        if mode == 'scrum':
            metrics['velocity'] = calculate_velocity(issues)
            metrics['sprint_burndown'] = calculate_burndown(issues)
            metrics['commitment_accuracy'] = calculate_commitment(issues)
        else:  # kanban
            metrics['cycle_time'] = calculate_cycle_time(issues)
            metrics['throughput'] = calculate_throughput(issues)
            metrics['wip'] = calculate_wip(issues)
        
        return metrics
```

### 2.4 Jira Extension (Main Entry Point)

**File: `extensions/jira/jira_extension.py`**

```python
from extensions.base_extension import DataSourceExtension, DataSinkExtension

class JiraExtension(DataSourceExtension, DataSinkExtension):
    """Main Jira extension - provides read and write capabilities"""
    
    name = "jira"
    display_name = "Jira (Selenium)"
    version = "1.0.0"
    
    config_schema = {
        "type": "object",
        "properties": {
            "base_url": {"type": "string", "title": "Jira Base URL"},
            "project_key": {"type": "string", "title": "Default Project"},
            "session_persist_hours": {"type": "integer", "default": 8},
            "default_jql": {"type": "string", "title": "Default JQL Query"},
            "field_mappings": {
                "type": "object",
                "title": "Custom Field Mappings",
                "additionalProperties": {"type": "string"}
            },
            "bulk_update_templates": {
                "type": "array",
                "title": "Bulk Update Templates",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "jql": {"type": "string"},
                        "updates": {"type": "object"}
                    }
                }
            }
        },
        "required": ["base_url"]
    }
    
    def __init__(self, driver=None):
        self.driver = driver
        self.scraper = None
        self.updater = None
        self.transformer = JiraTransformer()
        self.config = {}
    
    def initialize(self, config: Dict) -> bool:
        self.config = config
        if self.driver:
            self.scraper = JiraScraper(self.driver, config)
            self.updater = JiraUpdater(self.driver, config)
        return True
    
    def test_connection(self) -> Dict:
        try:
            self.driver.get(self.config['base_url'])
            # Check if logged in
            is_authenticated = 'login' not in self.driver.current_url.lower()
            return {
                'success': True,
                'authenticated': is_authenticated,
                'message': 'Connected to Jira'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_capabilities(self) -> List[str]:
        return ['read', 'write', 'bulk_update', 'metrics']
    
    def extract_data(self, query: Dict) -> Dict:
        jql = query.get('jql', f'project = {self.config["project_key"]}')
        max_results = query.get('max_results', 500)
        
        issues = self.scraper.execute_jql(jql, max_results)
        
        return {
            'raw_issues': issues,
            'count': len(issues),
            'query': jql
        }
    
    def transform_to_features(self, raw_data: Any) -> List[Dict]:
        return self.transformer.to_feature_structure(raw_data['raw_issues'])
    
    def transform_to_dependencies(self, raw_data: Any) -> Dict:
        return self.transformer.to_dependency_graph(raw_data['raw_issues'])
    
    def update_single(self, identifier: str, updates: Dict) -> bool:
        return self.updater.update_issue(identifier, updates)
    
    def update_bulk(self, query: Dict, updates: Dict) -> Dict:
        jql = query.get('jql')
        return self.updater.bulk_update(jql, updates)
```

---

## Phase 3: SM Reporting System

### 3.1 Insights Engine Enhancement

**File: `extensions/reporting/insights_engine.py`**

```python
class EnhancedInsightsEngine:
    """Flexible insights and reporting for SM persona"""
    
    def __init__(self, db_path: str = 'insights.db'):
        self.db = sqlite3.connect(db_path)
        self.rules = self.load_rules()
    
    def load_rules(self) -> List[Dict]:
        """Load configurable insight rules from config"""
        pass
    
    def add_rule(self, rule: Dict) -> bool:
        """Add custom insight rule"""
        # Rule format:
        # {
        #   name: "Stale Tickets",
        #   condition: "updated < -7d AND status != Done",
        #   severity: "warning",
        #   message_template: "{count} tickets not updated in 7 days"
        # }
        pass
    
    def analyze(self, issues: List[Dict], mode: str = 'scrum') -> List[Dict]:
        """Run all insight rules against issues"""
        insights = []
        
        for rule in self.rules:
            matches = self.evaluate_rule(rule, issues)
            if matches:
                insights.append({
                    'rule': rule['name'],
                    'severity': rule['severity'],
                    'message': rule['message_template'].format(count=len(matches)),
                    'affected_issues': matches
                })
        
        return insights
    
    def generate_daily_scrum_report(self, issues: List[Dict]) -> Dict:
        """Generate report optimized for daily standup"""
        return {
            'blockers': self.get_blockers(issues),
            'completed_yesterday': self.get_recently_completed(issues, days=1),
            'in_progress': self.get_in_progress(issues),
            'at_risk': self.get_at_risk(issues),
            'insights': self.analyze(issues)
        }
    
    def export_report(self, report: Dict, format: str = 'html') -> str:
        """Export report in specified format"""
        if format == 'html':
            return self.render_html_report(report)
        elif format == 'pdf':
            return self.render_pdf_report(report)
        elif format == 'csv':
            return self.render_csv_report(report)
```

### 3.2 Daily Scrum Mode

**New UI component for focused standup view**

Features:
- Blockers prominently displayed
- Yesterday's completions
- Today's focus items
- At-risk items (based on insights)
- Quick actions (update status, add blocker note)
- Timer for timeboxing

---

## Phase 4: API Handlers

### 4.1 New Endpoints

**Updates to `app.py`**

```python
# Extension Management
'/api/extensions'                    # GET: List all extensions
'/api/extensions/{name}/config'      # GET/POST: Extension config
'/api/extensions/{name}/test'        # POST: Test connection
'/api/extensions/{name}/status'      # GET: Extension status

# Data Import (via extensions)
'/api/data/import'                   # POST: Import from any extension
'/api/data/export'                   # POST: Export to format

# Jira-specific (routed through extension)
'/api/jira/query'                    # POST: Execute JQL
'/api/jira/issue/{key}'              # GET: Issue details, PUT: Update
'/api/jira/bulk-update'              # POST: Bulk update

# Reporting
'/api/reports/generate'              # POST: Generate report
'/api/reports/daily-scrum'           # GET: Daily scrum view
'/api/reports/export'                # POST: Export report

# Configuration
'/api/config/schema'                 # GET: Full config schema
'/api/config'                        # GET/PUT: Configuration
```

---

## Phase 5: Data Storage

### 5.1 Hybrid Storage Strategy

**Best Practice: SQLite for structured data + YAML for configuration**

```
config.yaml           - User-editable settings, extension configs
data/
  waypoint.db         - SQLite database
    ├── imported_data    - Cached Jira data
    ├── insights         - Historical insights
    ├── metrics          - Metric snapshots over time
    └── audit_log        - All actions for debugging
```

**File: `storage/data_store.py`**

```python
class DataStore:
    """Unified data storage interface"""
    
    def __init__(self, db_path: str = 'data/waypoint.db'):
        self.db = sqlite3.connect(db_path)
        self.init_schema()
    
    def save_import(self, extension: str, data: Dict) -> int:
        """Save imported data with timestamp"""
        pass
    
    def get_latest_import(self, extension: str) -> Dict:
        """Get most recent import from extension"""
        pass
    
    def get_import_history(self, extension: str, days: int = 30) -> List[Dict]:
        """Get import history for trend analysis"""
        pass
    
    def save_insight(self, insight: Dict) -> int:
        """Save insight with timestamp"""
        pass
    
    def save_metric_snapshot(self, metrics: Dict) -> int:
        """Save point-in-time metric snapshot for trending"""
        pass
```

---

## Phase 6: Frontend Integration

### 6.1 Extension Configuration UI

New UI section in Settings/Automation tab:
- List installed extensions
- Configure each extension
- Test connections
- Enable/disable extensions

### 6.2 Bulk Update UI

New UI for SM/Dev:
- JQL query builder
- Preview affected issues
- Select update actions
- Execute with progress
- View results

### 6.3 Daily Scrum Mode

New tab or modal:
- Focused standup view
- Blockers at top
- Quick actions
- Timer
- Export to clipboard

---

## File Structure (Final)

```
jira-automation/
├── app.py                           # Main app (updated with new handlers)
├── config.yaml                      # User configuration
├── extensions/
│   ├── __init__.py
│   ├── base_extension.py            # Abstract base classes
│   ├── extension_manager.py         # Extension lifecycle management
│   ├── jira/
│   │   ├── __init__.py
│   │   ├── jira_extension.py        # Main Jira extension
│   │   ├── jira_scraper.py          # Data extraction
│   │   ├── jira_updater.py          # Data writing
│   │   └── jira_transformer.py      # Data transformation
│   ├── github/
│   │   ├── __init__.py
│   │   ├── github_extension.py      # Main GitHub extension
│   │   ├── github_scraper.py        # (existing, moved)
│   │   └── github_api.py            # (future: when API access granted)
│   └── reporting/
│       ├── __init__.py
│       ├── insights_engine.py       # Enhanced insights
│       ├── report_generator.py      # Multi-format reports
│       └── daily_scrum.py           # Scrum-focused view
├── storage/
│   ├── __init__.py
│   ├── data_store.py                # SQLite operations
│   └── config_manager.py            # YAML config management
├── data/
│   └── waypoint.db                  # SQLite database
├── modern-ui.html                   # (updated with new components)
└── tests/
    ├── test_jira_extension.py
    ├── test_data_store.py
    └── test_insights_engine.py
```

---

## Implementation Order

### Week 1: Core Foundation
1. ✅ Create extension base classes
2. ✅ Create extension manager
3. ✅ Set up data store (SQLite)
4. ✅ Create Jira extension structure

### Week 2: Jira Integration
5. ✅ Implement JiraScraper (data extraction)
6. ✅ Implement JiraUpdater (data writing)
7. ✅ Implement JiraTransformer
8. ✅ Wire API handlers

### Week 3: SM Reporting
9. ✅ Enhance InsightsEngine
10. ✅ Build daily scrum mode
11. ✅ Add report export (HTML/PDF/CSV)
12. ✅ Add configurable insight rules

### Week 4: Frontend & Polish
13. ✅ Wire all frontend buttons
14. ✅ Extension configuration UI
15. ✅ Bulk update UI
16. ✅ Comprehensive testing
17. ✅ Documentation

---

## Success Criteria

### PO Persona ✅
- Can click "Import Now" and see features
- Dependency canvas populates with real data
- Can export features to CSV

### Dev Persona ✅
- Existing GitHub sync still works
- Can configure automation rules
- Can see sync status

### SM Persona ✅
- Daily scrum mode available
- Configurable insights
- Export reports in multiple formats
- Historical trending

### Technical ✅
- Plugin architecture allows easy extension
- All config via UI
- Scalable SQLite storage
- Tests pass
- No breaking changes

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Jira HTML changes break scraper | Use stable selectors, add retry logic, version checks |
| Session timeout during bulk ops | Add session refresh, checkpoint/resume |
| Large dataset performance | Pagination, lazy loading, background processing |
| Extension conflicts | Namespace isolation, dependency checking |

---

## Questions Resolved ✅

1. **Session persistence**: 8-hour default, refreshes daily ✅
2. **Storage**: SQLite + YAML hybrid ✅
3. **Bulk updates**: Templates + custom (Option C) ✅
4. **SM Reporting**: Dashboard + Export (Option C) ✅
5. **GitHub**: Plugin architecture for future ✅
6. **Configurability**: UI-driven, scalable backend ✅
