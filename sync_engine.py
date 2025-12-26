"""
GitHub-Jira Sync Engine
Orchestrates the sync between GitHub PRs and Jira tickets
"""
import yaml
import time
import logging
from datetime import datetime
import schedule
from github_scraper import GitHubScraper
from jira_automator import JiraAutomator

class SyncEngine:
    """Main sync orchestration engine"""
    
    def __init__(self, driver, config_path='config.yaml'):
        self.driver = driver
        
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.github = GitHubScraper(driver, self.config)
        self.jira = JiraAutomator(driver, self.config)
        
        # Setup logging
        self._setup_logging()
        
        # Track PR states to detect changes (not just "seen before")
        # Format: {'repo-123': 'open', 'repo-124': 'merged'}
        self.pr_states = {}
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config['logging']
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config['file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def sync_once(self):
        """Run a single sync cycle"""
        self.logger.info("🔄 Starting sync cycle...")
        
        total_updated = 0
        
        # Process each configured repository
        for repo in self.config['github']['repositories']:
            self.logger.info(f"📦 Processing repository: {repo}")
            
            # Get recent PRs
            lookback = self.config['schedule']['lookback_hours']
            prs = self.github.get_recent_prs(repo, hours_back=lookback)
            
            self.logger.info(f"Found {len(prs)} PRs to process")
            
            # Process each PR
            for pr in prs:
                try:
                    # Check if PR state has changed
                    pr_id = f"{pr['repo']}-{pr['number']}"
                    current_status = pr['status']
                    previous_status = self.pr_states.get(pr_id)
                    
                    # Only process if:
                    # 1. Never seen before (previous_status is None)
                    # 2. Status changed (open -> merged, open -> closed, etc.)
                    if previous_status is None:
                        self.logger.info(f"  🆕 New PR detected: {pr_id} ({current_status})")
                        should_process = True
                    elif previous_status != current_status:
                        self.logger.info(f"  🔄 PR state changed: {pr_id} ({previous_status} → {current_status})")
                        should_process = True
                    else:
                        self.logger.debug(f"  ⏭️ Skipping {pr_id} (no state change)")
                        should_process = False
                    
                    if should_process:
                        updated_count = self._process_pr(pr)
                        total_updated += updated_count
                        
                        # Update state tracking
                        self.pr_states[pr_id] = current_status
                    
                    # Delay between checks
                    delay = self.config['performance']['delay_between_updates_seconds']
                    time.sleep(delay)
                    
                except Exception as e:
                    self.logger.error(f"Error processing PR {pr.get('url', 'unknown')}: {e}")
                    continue
        
        self.logger.info(f"✅ Sync cycle complete. Updated {total_updated} tickets.")
        
        # Clear old state tracking periodically (keep last 1000)
        if len(self.pr_states) > 1000:
            self.logger.info("🧹 Clearing old PR state tracking (keeping last 1000)")
            # Keep only the most recent 1000 entries
            recent_items = list(self.pr_states.items())[-1000:]
            self.pr_states = dict(recent_items)
    
    def _process_pr(self, pr):
        """Process a single PR and update linked Jira tickets"""
        self.logger.info(f"🔗 Processing PR: {pr['title']}")
        
        updated_count = 0
        
        # Get detailed PR info if needed
        pr_details = self.github.get_pr_details(pr['url'])
        pr.update(pr_details)
        
        # Process each linked Jira ticket
        for ticket_key in pr['ticket_keys']:
            try:
                self.logger.info(f"  📝 Updating ticket: {ticket_key}")
                
                # Determine updates based on PR status
                updates = self._build_updates(pr)
                
                # Apply updates to Jira
                success = self.jira.update_ticket(ticket_key, updates)
                
                if success:
                    self.logger.info(f"  ✅ Successfully updated {ticket_key}")
                    updated_count += 1
                else:
                    self.logger.warning(f"  ⚠️ Failed to update {ticket_key}")
                    
            except Exception as e:
                self.logger.error(f"  ❌ Error updating {ticket_key}: {e}")
                continue
        
        return updated_count
    
    def _build_updates(self, pr):
        """Build update payload based on PR status and config"""
        automation = self.config['automation']
        status = pr['status']
        target_branch = pr.get('target_branch', '').upper()
        
        updates = {}
        
        # Determine which rule set to use
        if status == 'open':
            rules = automation['pr_opened']
        elif status == 'merged':
            # For merged PRs, check branch-specific rules
            rules = self._get_branch_rule(automation['pr_merged'], target_branch)
        elif status == 'closed':
            rules = automation['pr_closed']
        else:
            rules = automation.get('pr_updated', {})
        
        # Skip if disabled
        if not rules.get('enabled', True):
            return updates
        
        # Build comment from template
        if rules.get('add_comment'):
            template = rules['comment_template']
            comment = template.format(
                pr_url=pr['url'],
                branch_name=pr.get('branch', 'unknown'),
                author=pr.get('author', 'unknown'),
                commit_message=pr.get('last_commit_message', ''),
                merger=pr.get('merged_by', ''),
                target_branch=target_branch
            )
            updates['comment'] = comment
        
        # Set status
        if rules.get('set_status'):
            updates['status'] = rules['set_status']
        
        # Add label
        if rules.get('add_label'):
            updates['label'] = rules['add_label']
        
        # Update PR field
        if rules.get('update_pr_field'):
            updates['pr_field'] = pr['url']
        
        return updates
    
    def _get_branch_rule(self, merged_config, target_branch):
        """Get the appropriate branch rule for merged PRs"""
        branch_rules = merged_config.get('branch_rules', [])
        
        # Try to find exact branch match
        for rule in branch_rules:
            if rule['branch'].upper() == target_branch:
                return rule
        
        # Fall back to default rule
        for rule in branch_rules:
            if rule['branch'] == 'default':
                return rule
        
        # If no rules defined, return empty
        return {}
    
    def start_scheduled(self):
        """Start scheduled sync runs"""
        sched_config = self.config['schedule']
        
        if not sched_config['enabled']:
            self.logger.info("Scheduled sync is disabled")
            return
        
        # Schedule hourly sync during business hours
        for hour in range(sched_config['start_hour'], sched_config['end_hour'] + 1):
            schedule_time = f"{hour:02d}:00"
            schedule.every().day.at(schedule_time).do(self._sync_if_business_hours)
        
        self.logger.info(f"📅 Scheduled sync: Every hour from {sched_config['start_hour']}:00 to {sched_config['end_hour']}:00")
        self.logger.info("⏰ Scheduler started. Press Ctrl+C to stop.")
        
        # Run scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _sync_if_business_hours(self):
        """Run sync only if current time matches business hours config"""
        sched_config = self.config['schedule']
        now = datetime.now()
        
        # Check if weekday
        if sched_config['weekdays_only'] and now.weekday() >= 5:
            self.logger.info("⏭️ Skipping sync (weekend)")
            return
        
        # Check if business hours
        if now.hour < sched_config['start_hour'] or now.hour > sched_config['end_hour']:
            self.logger.info("⏭️ Skipping sync (outside business hours)")
            return
        
        # Run sync
        self.sync_once()
