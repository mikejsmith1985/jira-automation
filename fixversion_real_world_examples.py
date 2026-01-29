#!/usr/bin/env python
"""
Real-world examples of using the fixVersion creator

Copy and modify these examples to match your team's needs.
"""

from datetime import datetime, timedelta
from jira_version_creator import JiraVersionCreator
import yaml

# ============================================================
# Example 1: Two-Week Sprint Cadence
# ============================================================

def create_sprint_versions_bi_weekly():
    """
    Create 6 bi-weekly sprint versions
    Example: "Sprint Feb 05", "Sprint Feb 19", "Sprint Mar 05"...
    """
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Generate dates: Every other Thursday starting Feb 5, 2026
    start_date = datetime(2026, 2, 5)
    sprint_dates = []
    
    for i in range(6):
        sprint_end = start_date + timedelta(days=i * 14)
        sprint_dates.append(sprint_end.strftime('%Y-%m-%d'))
    
    print(f"Creating {len(sprint_dates)} bi-weekly sprint versions:")
    for date in sprint_dates:
        print(f"  - {date}")
    print()
    
    # Setup (assumes you have a driver setup elsewhere)
    # creator = JiraVersionCreator(driver, config)
    # results = creator.create_versions_from_dates(
    #     dates=sprint_dates,
    #     name_format='Sprint {month_short} {day}',
    #     project_key='KAN',
    #     description_template='Sprint ending on {date}'
    # )
    # return results

# ============================================================
# Example 2: Monthly Release Schedule
# ============================================================

def create_monthly_releases():
    """
    Create monthly release versions on the 1st of each month
    Example: "v2026.03", "v2026.04", "v2026.05"...
    """
    # Generate first day of each month for 6 months
    start = datetime(2026, 3, 1)
    release_dates = []
    
    for i in range(6):
        # Calculate months forward
        month = ((start.month - 1 + i) % 12) + 1
        year = start.year + ((start.month - 1 + i) // 12)
        release_date = datetime(year, month, 1)
        release_dates.append(release_date.strftime('%Y-%m-%d'))
    
    print(f"Creating {len(release_dates)} monthly releases:")
    for date in release_dates:
        print(f"  - {date}")
    print()
    
    # Usage:
    # creator = JiraVersionCreator(driver, config)
    # results = creator.create_versions_from_dates(
    #     dates=release_dates,
    #     name_format='v{year}.{month}',
    #     project_key='PROJ',
    #     description_template='Release for {month_name} {year}'
    # )

# ============================================================
# Example 3: Quarterly Release Cadence
# ============================================================

def create_quarterly_releases():
    """
    Create quarterly releases (Q1, Q2, Q3, Q4)
    Example: "Q1 2026", "Q2 2026", "Q3 2026", "Q4 2026"
    """
    quarters = [
        ('2026-03-31', 'Q1 2026'),
        ('2026-06-30', 'Q2 2026'),
        ('2026-09-30', 'Q3 2026'),
        ('2026-12-31', 'Q4 2026'),
    ]
    
    print("Creating quarterly release versions:")
    for date, name in quarters:
        print(f"  - {name} (ending {date})")
    print()
    
    # For quarterly releases, you might want to create them manually
    # since the names don't follow a date-based pattern:
    # 
    # for release_date, version_name in quarters:
    #     creator.create_version(
    #         project_key='PROJ',
    #         version_name=version_name,
    #         release_date=release_date,
    #         description=f'Quarterly release ending {release_date}'
    #     )

# ============================================================
# Example 4: Hotfix Versions (Current Week)
# ============================================================

def create_hotfix_versions_this_week():
    """
    Create hotfix versions for each day this week
    Example: "Hotfix 2026-02-03", "Hotfix 2026-02-04"...
    """
    today = datetime.now()
    # Find Monday of this week
    monday = today - timedelta(days=today.weekday())
    
    hotfix_dates = []
    for i in range(5):  # Monday through Friday
        day = monday + timedelta(days=i)
        hotfix_dates.append(day.strftime('%Y-%m-%d'))
    
    print(f"Creating {len(hotfix_dates)} hotfix versions for this week:")
    for date in hotfix_dates:
        print(f"  - Hotfix {date}")
    print()
    
    # Usage:
    # creator = JiraVersionCreator(driver, config)
    # results = creator.create_versions_from_dates(
    #     dates=hotfix_dates,
    #     name_format='Hotfix {date}',
    #     project_key='SUPPORT',
    #     description_template='Hotfix version for {date}'
    # )

# ============================================================
# Example 5: End-of-Month Releases
# ============================================================

def create_end_of_month_releases():
    """
    Create releases on the last day of each month
    Example: "Release Feb 2026", "Release Mar 2026"...
    """
    from calendar import monthrange
    
    release_dates = []
    start_year = 2026
    start_month = 3
    
    for i in range(6):
        # Calculate month
        month = ((start_month - 1 + i) % 12) + 1
        year = start_year + ((start_month - 1 + i) // 12)
        
        # Get last day of month
        _, last_day = monthrange(year, month)
        release_date = datetime(year, month, last_day)
        release_dates.append(release_date.strftime('%Y-%m-%d'))
    
    print(f"Creating {len(release_dates)} end-of-month releases:")
    for date in release_dates:
        print(f"  - {date}")
    print()
    
    # Usage:
    # creator = JiraVersionCreator(driver, config)
    # results = creator.create_versions_from_dates(
    #     dates=release_dates,
    #     name_format='Release {month_short} {year}',
    #     project_key='PROD',
    #     description_template='End of month release for {month_name} {year}'
    # )

# ============================================================
# Example 6: Custom Sprint Names with Sprint Numbers
# ============================================================

def create_numbered_sprints():
    """
    Create sprints with sequential numbers
    Example: "Sprint 23", "Sprint 24", "Sprint 25"...
    
    Note: This requires custom creation since sprint numbers
    don't come from dates directly
    """
    sprint_info = [
        ('2026-02-05', 'Sprint 23'),
        ('2026-02-19', 'Sprint 24'),
        ('2026-03-05', 'Sprint 25'),
        ('2026-03-19', 'Sprint 26'),
        ('2026-04-02', 'Sprint 27'),
        ('2026-04-16', 'Sprint 28'),
    ]
    
    print(f"Creating {len(sprint_info)} numbered sprint versions:")
    for date, name in sprint_info:
        print(f"  - {name} (ending {date})")
    print()
    
    # For custom names that don't follow date patterns,
    # create each version individually:
    #
    # for release_date, version_name in sprint_info:
    #     creator.create_version(
    #         project_key='SCRUM',
    #         version_name=version_name,
    #         release_date=release_date,
    #         description=f'Sprint ending {release_date}'
    #     )

# ============================================================
# Example 7: Generate Full Year of Bi-Weekly Sprints
# ============================================================

def create_full_year_sprints():
    """
    Generate a full year of bi-weekly sprints
    (26 sprints for 52 weeks)
    """
    start_date = datetime(2026, 1, 8)  # First sprint ends Jan 8
    sprint_dates = []
    
    for i in range(26):
        sprint_end = start_date + timedelta(days=i * 14)
        sprint_dates.append(sprint_end.strftime('%Y-%m-%d'))
    
    print(f"Creating {len(sprint_dates)} sprints for entire year 2026:")
    print(f"  First: {sprint_dates[0]}")
    print(f"  Last: {sprint_dates[-1]}")
    print()
    
    # This creates a LOT of versions, so be careful!
    # You might want to break this into quarters:
    #
    # Q1_dates = sprint_dates[0:7]   # First 7 sprints
    # Q2_dates = sprint_dates[7:13]  # Next 6 sprints
    # Q3_dates = sprint_dates[13:20] # Next 7 sprints
    # Q4_dates = sprint_dates[20:26] # Last 6 sprints
    #
    # Then create each quarter separately

# ============================================================
# Main - Uncomment the example you want to test
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Real-World fixVersion Creation Examples")
    print("=" * 60)
    print()
    
    # Uncomment one of these to see the dates:
    
    create_sprint_versions_bi_weekly()
    # create_monthly_releases()
    # create_quarterly_releases()
    # create_hotfix_versions_this_week()
    # create_end_of_month_releases()
    # create_numbered_sprints()
    # create_full_year_sprints()
    
    print()
    print("=" * 60)
    print("To actually CREATE these versions in Jira:")
    print("1. Uncomment the creator.create_versions_from_dates() calls")
    print("2. Setup driver with: driver = setup_driver()")
    print("3. Or copy these dates into create_fix_versions.py")
    print("=" * 60)
