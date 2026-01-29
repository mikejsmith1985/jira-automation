# Jira fixVersion Batch Creator

Automatically create multiple fixVersions in Jira using Selenium browser automation.

## ✨ Features

- 🎯 Create multiple fixVersions from a list of release dates
- 🎨 Flexible version name formatting (semantic versions, sprint names, etc.)
- 📅 Automatic date-based naming with multiple placeholder options
- 🔐 Uses existing Jira login session (no API tokens needed)
- ✅ Validates login before proceeding
- 📊 Detailed results summary (created, skipped, failed)

## 🚀 Quick Start

### 1. Prerequisites

- Chrome browser installed
- Python with selenium installed (`pip install selenium`)
- Valid Jira account with permission to create versions

### 2. Run the Script

```bash
python create_fix_versions.py
```

### 3. Login (if needed)

If not already logged in, the script will:
1. Open a Chrome browser window
2. Navigate to your Jira instance
3. Wait for you to login manually
4. Detect when login is complete
5. Proceed with version creation

### 4. Customize Your Dates

Edit `create_fix_versions.py` and modify the date list:

```python
sprint_dates = [
    '2026-02-05',
    '2026-02-12',
    '2026-02-19',
    '2026-02-26'
]
```

## 🎨 Version Name Formats

### Available Placeholders

| Placeholder | Example Output | Description |
|------------|----------------|-------------|
| `{date}` | 2026-02-05 | Full date |
| `{year}` | 2026 | Year |
| `{month}` | 02 | Month (zero-padded) |
| `{day}` | 05 | Day (zero-padded) |
| `{month_name}` | February | Full month name |
| `{month_short}` | Feb | Abbreviated month |

### Format Examples

```python
# Sprint style
name_format='Sprint {month_short} {day}'
# Result: Sprint Feb 05

# Semantic version
name_format='v{year}.{month}.{day}'
# Result: v2026.02.05

# Readable format
name_format='Release {month_name} {day}, {year}'
# Result: Release February 05, 2026

# Simple
name_format='Release {date}'
# Result: Release 2026-02-05
```

## 📝 Usage Examples

### Example 1: Weekly Sprints

```python
from jira_version_creator import JiraVersionCreator

creator = JiraVersionCreator(driver, config)

sprint_dates = [
    '2026-02-05',
    '2026-02-12',
    '2026-02-19'
]

results = creator.create_versions_from_dates(
    dates=sprint_dates,
    name_format='Sprint {month_short} {day}',
    project_key='KAN',
    description_template='Sprint ending on {date}'
)

print(f"Created: {len(results['created'])}")
print(f"Skipped: {len(results['skipped'])}")
print(f"Failed: {len(results['failed'])}")
```

### Example 2: Monthly Releases

```python
release_dates = [
    '2026-03-01',
    '2026-04-01',
    '2026-05-01'
]

results = creator.create_versions_from_dates(
    dates=release_dates,
    name_format='v{year}.{month}',
    project_key='PROJ',
    description_template='Monthly release for {month_name} {year}'
)
```

### Example 3: Generate Dates Automatically

```python
from datetime import datetime, timedelta

# Generate 6 bi-weekly sprint dates
start_date = datetime(2026, 2, 5)
sprint_dates = []

for i in range(6):
    sprint_end = start_date + timedelta(days=i * 14)
    sprint_dates.append(sprint_end.strftime('%Y-%m-%d'))

# Create versions
results = creator.create_versions_from_dates(
    dates=sprint_dates,
    name_format='Sprint {month_short} {day}',
    project_key='SCRUM'
)
```

## ⚙️ Configuration

The script uses settings from `config.yaml`:

```yaml
jira:
  base_url: https://your-company.atlassian.net/
  project_keys:
    - KAN
    - PROJ
```

## 🔍 How It Works

1. **Login Detection**: Checks if you're logged into Jira using `login_detector.py`
2. **Session Reuse**: Uses persistent Chrome profile to maintain login state
3. **Navigation**: Navigates to project versions page (`/plugins/servlet/project-config/PROJECT/versions`)
4. **Form Automation**: 
   - Clicks "Create Version" button
   - Fills in version name, description, release date
   - Submits form
5. **Results**: Reports success/failure for each version

## 🛡️ Error Handling

- **Already exists**: Skipped (won't create duplicates)
- **Login expired**: Prompts you to login again
- **Invalid date format**: Skips with error message
- **Form not found**: Tries multiple selectors (supports different Jira versions)

## 🎯 Use Cases

### Sprint Planning
Create fixVersions for the next quarter of sprints:
```python
# Q1 2026 bi-weekly sprints
dates = ['2026-01-15', '2026-01-29', '2026-02-12', '2026-02-26', '2026-03-12', '2026-03-26']
format = 'Sprint {month_short} {day}'
```

### Release Planning
Plan monthly releases for the year:
```python
# Monthly releases on the 1st
dates = ['2026-01-01', '2026-02-01', '2026-03-01', ... '2026-12-01']
format = 'Release {month_name} {year}'
```

### Versioning
Semantic version releases:
```python
dates = ['2026-03-15', '2026-06-15', '2026-09-15', '2026-12-15']
format = 'v{year}.{month}.{day}'
```

## 📚 API Reference

### `JiraVersionCreator`

#### `create_versions_from_dates(dates, name_format, project_key=None, description_template="", archive_old=False)`

Create multiple fixVersions at once.

**Parameters:**
- `dates` (list): List of date strings in YYYY-MM-DD format
- `name_format` (str): Format string with placeholders (see table above)
- `project_key` (str, optional): Jira project key. Uses first from config if None
- `description_template` (str, optional): Description with {date} placeholder
- `archive_old` (bool): Auto-archive versions with past release dates

**Returns:**
```python
{
    'created': ['Sprint Feb 05', 'Sprint Feb 12'],
    'skipped': ['Sprint Feb 19'],  # Already existed
    'failed': [{'date': '2026-13-45', 'error': 'Invalid date format'}]
}
```

#### `create_version(project_key, version_name, release_date=None, description="", archived=False)`

Create a single fixVersion.

**Parameters:**
- `project_key` (str): Jira project key
- `version_name` (str): Name of the version
- `release_date` (str, optional): Release date in YYYY-MM-DD
- `description` (str, optional): Version description
- `archived` (bool): Whether to archive this version

**Returns:** `True` if successful, `False` otherwise

## 🐛 Troubleshooting

### "Could not find 'Create Version' button"
- Make sure you have permission to create versions in the project
- Try navigating to the versions page manually first to verify access

### "Not logged in to Jira"
- Close the browser completely and run the script again
- Delete `selenium_profile` folder to clear browser cache

### Versions not showing up
- Refresh the versions page in Jira
- Check the project key is correct in config.yaml

### Date format errors
- Ensure dates are in YYYY-MM-DD format
- Month and day should be zero-padded (02 not 2)

## 📄 License

Part of the GitHub-Jira Sync Tool project.
