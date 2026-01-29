# Example: How to customize your fixVersion creation

# This file shows you how to edit create_fix_versions.py to create
# your own custom release schedule

# ============================================================
# OPTION 1: Simple date list with custom format
# ============================================================

# Your release dates (YYYY-MM-DD format)
my_dates = [
    '2026-02-05',
    '2026-02-12',
    '2026-02-19',
    '2026-02-26'
]

# Your version name format - choose one:
# - 'Release {date}' → 'Release 2026-02-05'
# - 'Sprint {month_short} {day}' → 'Sprint Feb 05'
# - 'v{year}.{month}.{day}' → 'v2026.02.05'
# - '{month_name} {day} Release' → 'February 05 Release'

format_option = 'Sprint {month_short} {day}'

# Then in create_fix_versions.py, use:
# results = creator.create_versions_from_dates(
#     dates=my_dates,
#     name_format=format_option,
#     project_key='YOUR_PROJECT_KEY'
# )

# ============================================================
# OPTION 2: Generate dates automatically (bi-weekly sprints)
# ============================================================

from datetime import datetime, timedelta

def generate_sprint_dates(start_date, num_sprints, sprint_length_days=14):
    """
    Generate sprint end dates automatically
    
    Args:
        start_date: First sprint end date (YYYY-MM-DD string)
        num_sprints: How many sprints to generate
        sprint_length_days: Days between sprints (default: 14 for bi-weekly)
    
    Returns:
        List of date strings
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    dates = []
    
    for i in range(num_sprints):
        sprint_end = start + timedelta(days=i * sprint_length_days)
        dates.append(sprint_end.strftime('%Y-%m-%d'))
    
    return dates

# Example: Generate 6 bi-weekly sprints starting Feb 5, 2026
auto_dates = generate_sprint_dates('2026-02-05', num_sprints=6, sprint_length_days=14)
# Result: ['2026-02-05', '2026-02-19', '2026-03-05', '2026-03-19', '2026-04-02', '2026-04-16']

# ============================================================
# OPTION 3: Monthly releases on specific day
# ============================================================

def generate_monthly_releases(start_month, num_months, day_of_month=1):
    """
    Generate monthly release dates (e.g., 1st of every month)
    
    Args:
        start_month: Starting month (YYYY-MM format)
        num_months: How many months
        day_of_month: Day of month for release (default: 1)
    """
    from dateutil.relativedelta import relativedelta
    
    year, month = map(int, start_month.split('-'))
    start = datetime(year, month, day_of_month)
    dates = []
    
    for i in range(num_months):
        release_date = start + relativedelta(months=i)
        dates.append(release_date.strftime('%Y-%m-%d'))
    
    return dates

# Example: Monthly releases on the 1st, starting March 2026
monthly_dates = generate_monthly_releases('2026-03', num_months=6, day_of_month=1)
# Result: ['2026-03-01', '2026-04-01', '2026-05-01', '2026-06-01', '2026-07-01', '2026-08-01']

# ============================================================
# OPTION 4: Custom format examples
# ============================================================

# You can use these placeholders in name_format:
# {date} - Full date (2026-02-05)
# {year} - Year (2026)
# {month} - Month number (02)
# {day} - Day number (05)
# {month_name} - Full month name (February)
# {month_short} - Short month name (Feb)

format_examples = {
    'Simple date': 'Release {date}',
    'Semantic version': 'v{year}.{month}.{day}',
    'Sprint style': 'Sprint {month_short} {day}',
    'Readable': '{month_name} {day}, {year} Release',
    'Short version': '{year}.{month}',
    'Quarter style': 'Q1-{year} Week {day}',
}

# ============================================================
# USAGE INSTRUCTIONS
# ============================================================

"""
TO USE THIS:

1. Edit create_fix_versions.py
2. Find the section that looks like:

   sprint_dates = [
       '2026-02-05',
       '2026-02-12',
       ...
   ]

3. Replace with your dates and format:

   my_custom_dates = [
       '2026-03-01',
       '2026-03-15',
       '2026-03-29'
   ]
   
   results = creator.create_versions_from_dates(
       dates=my_custom_dates,
       name_format='v{year}.{month}.{day}',
       project_key='YOUR_PROJECT',
       description_template='Release on {date}'
   )

4. Run: python create_fix_versions.py
"""
