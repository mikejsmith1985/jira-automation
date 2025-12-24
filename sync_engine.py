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
        
        # Track processed PRs to avoid duplicates
        self.processed_prs = set()
        
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
                    # Skip if already processed recently
                    pr_id = f"{pr['repo']}-{pr['number']}"
                    if pr_id in self.processed_prs:
                        continue
                    
                    updated_count = self._process_pr(pr)
                    total_updated += updated_count
                    
                    # Mark as processed
                    self.processed_prs.add(pr_id)
                    
                    # Delay between updates
                    delay = self.config['performance']['delay_between_updates_seconds']
                    time.sleep(delay)
                    
                except Exception as e:
                    self.logger.error(f"Error processing PR {pr.get('url', 'unknown')}: {e}")
                    continue
        
        self.logger.info(f"✅ Sync cycle complete. Updated {total_updated} tickets.")
        
        # Clear processed set periodically (keep last 1000)
        if len(self.processed_prs) > 1000:
            self.processed_prs.clear()
    
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
        
        updates = {}
        
        # Determine which rule set to use
        if status == 'open':
            rules = automation['pr_opened']
        elif status == 'merged':
            rules = automation['pr_merged']
        elif status == 'closed':
            rules = automation['pr_closed']
        else:
            rules = automation.get('pr_updated', {})
        
        # Build comment from template
        if rules.get('add_comment'):
            template = rules['comment_template']
            comment = template.format(
                pr_url=pr['url'],
                branch_name=pr.get('branch', 'unknown'),
                author=pr.get('author', 'unknown'),
                commit_message=pr.get('last_commit_message', ''),
                merger=pr.get('merged_by', '')
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
