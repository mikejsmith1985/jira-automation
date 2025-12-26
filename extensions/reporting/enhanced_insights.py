"""
Enhanced Insights Engine
Flexible, configurable insights and analysis for SM persona
"""
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from storage.data_store import get_data_store


class InsightRule:
    """
    Configurable insight rule that can be evaluated against issues.
    """
    
    def __init__(self, name: str, condition: str, severity: str, 
                 message_template: str, category: str = 'general'):
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message_template = message_template
        self.category = category
    
    def evaluate(self, issues: List[Dict]) -> Optional[Dict]:
        """
        Evaluate rule against issues.
        
        Returns:
            Insight dict if rule matches, None otherwise
        """
        matches = self._find_matches(issues)
        
        if matches:
            return {
                'rule': self.name,
                'severity': self.severity,
                'category': self.category,
                'message': self.message_template.format(
                    count=len(matches),
                    issues=', '.join(m['key'] for m in matches[:5])
                ),
                'affected_issues': [m['key'] for m in matches],
                'count': len(matches)
            }
        return None
    
    def _find_matches(self, issues: List[Dict]) -> List[Dict]:
        """Find issues matching the condition"""
        matches = []
        
        for issue in issues:
            if self._evaluate_condition(issue):
                matches.append(issue)
        
        return matches
    
    def _evaluate_condition(self, issue: Dict) -> bool:
        """Evaluate condition against single issue"""
        try:
            condition = self.condition.lower()
            
            if 'status' in condition:
                status = issue.get('status', '').lower()
                if 'blocked' in condition and status == 'blocked':
                    return True
                if 'done' in condition and status in ['done', 'closed', 'resolved']:
                    return True
                if 'in progress' in condition and status in ['in progress', 'in review']:
                    return True
            
            if 'assignee' in condition:
                assignee = issue.get('assignee', '')
                if 'unassigned' in condition and not assignee:
                    return True
            
            if 'labels' in condition:
                labels = issue.get('labels', [])
                if 'missing' in condition and not labels:
                    return True
            
            if 'story_points' in condition or 'points' in condition:
                points = issue.get('story_points', 0) or 0
                if 'missing' in condition and points == 0:
                    return True
                if '>' in condition:
                    match = re.search(r'>\s*(\d+)', condition)
                    if match and points > int(match.group(1)):
                        return True
            
            if 'type' in condition:
                issue_type = issue.get('type', '').lower()
                if 'bug' in condition and issue_type == 'bug':
                    return True
                if 'story' in condition and issue_type == 'story':
                    return True
            
            return False
            
        except Exception:
            return False


class EnhancedInsightsEngine:
    """
    Enhanced insights engine with configurable rules and flexible reporting.
    """
    
    DEFAULT_RULES = [
        {
            'name': 'blocked_issues',
            'condition': 'status = blocked',
            'severity': 'high',
            'message_template': '{count} issues are blocked',
            'category': 'blockers'
        },
        {
            'name': 'unassigned_in_progress',
            'condition': 'status in progress AND assignee unassigned',
            'severity': 'medium',
            'message_template': '{count} in-progress issues have no assignee',
            'category': 'hygiene'
        },
        {
            'name': 'missing_story_points',
            'condition': 'story_points missing AND type = story',
            'severity': 'low',
            'message_template': '{count} stories are missing story point estimates',
            'category': 'hygiene'
        },
        {
            'name': 'high_wip',
            'condition': 'status in progress',
            'severity': 'warning',
            'message_template': '{count} issues currently in progress (check WIP limits)',
            'category': 'flow'
        }
    ]
    
    def __init__(self, custom_rules: List[Dict] = None):
        self.data_store = get_data_store()
        self.rules: List[InsightRule] = []
        
        self._load_default_rules()
        
        if custom_rules:
            for rule_config in custom_rules:
                self.add_rule(rule_config)
    
    def _load_default_rules(self):
        """Load default insight rules"""
        for rule_config in self.DEFAULT_RULES:
            self.add_rule(rule_config)
    
    def add_rule(self, rule_config: Dict) -> bool:
        """Add a new insight rule"""
        try:
            rule = InsightRule(
                name=rule_config['name'],
                condition=rule_config['condition'],
                severity=rule_config.get('severity', 'medium'),
                message_template=rule_config.get('message_template', '{count} issues match rule'),
                category=rule_config.get('category', 'general')
            )
            self.rules.append(rule)
            return True
        except Exception as e:
            print(f"Error adding rule: {e}")
            return False
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name"""
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != rule_name]
        return len(self.rules) < original_count
    
    def analyze(self, issues: List[Dict], categories: List[str] = None) -> List[Dict]:
        """
        Run all insight rules against issues.
        
        Args:
            issues: List of Jira issues
            categories: Optional filter by categories
            
        Returns:
            List of insight dictionaries
        """
        insights = []
        
        for rule in self.rules:
            if categories and rule.category not in categories:
                continue
            
            insight = rule.evaluate(issues)
            if insight:
                insights.append(insight)
                
                self.data_store.save_insight(
                    rule_name=insight['rule'],
                    severity=insight['severity'],
                    message=insight['message'],
                    affected_issues=insight['affected_issues']
                )
        
        insights.sort(key=lambda x: {
            'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'warning': 4
        }.get(x['severity'], 5))
        
        return insights
    
    def get_active_insights(self, days: int = 7) -> List[Dict]:
        """Get unresolved insights from database"""
        return self.data_store.get_active_insights(days)
    
    def resolve_insight(self, insight_id: int) -> bool:
        """Mark an insight as resolved"""
        return self.data_store.resolve_insight(insight_id)
    
    def generate_daily_scrum_insights(self, issues: List[Dict]) -> Dict:
        """
        Generate insights specifically for daily scrum.
        
        Returns:
            Structured insights for standup discussion
        """
        insights = self.analyze(issues)
        
        blockers = [i for i in insights if i['category'] == 'blockers']
        hygiene = [i for i in insights if i['category'] == 'hygiene']
        flow = [i for i in insights if i['category'] == 'flow']
        
        blocked_issues = [
            issue for issue in issues 
            if issue.get('status', '').lower() == 'blocked'
        ]
        
        return {
            'summary': {
                'total_insights': len(insights),
                'critical_count': sum(1 for i in insights if i['severity'] in ['critical', 'high']),
                'health_score': self._calculate_health_score(issues, insights)
            },
            'blockers': {
                'insights': blockers,
                'issues': [
                    {
                        'key': b['key'],
                        'summary': b.get('summary', ''),
                        'assignee': b.get('assignee', 'Unassigned')
                    }
                    for b in blocked_issues
                ]
            },
            'hygiene': hygiene,
            'flow': flow,
            'discussion_points': self._generate_discussion_points(insights, issues)
        }
    
    def _calculate_health_score(self, issues: List[Dict], insights: List[Dict]) -> int:
        """Calculate team health score (0-100)"""
        if not issues:
            return 100
        
        score = 100
        
        for insight in insights:
            severity_penalty = {
                'critical': 20,
                'high': 15,
                'medium': 10,
                'low': 5,
                'warning': 3
            }.get(insight['severity'], 5)
            
            score -= severity_penalty
        
        blocked_pct = sum(1 for i in issues if i.get('status', '').lower() == 'blocked') / len(issues) * 100
        score -= int(blocked_pct * 2)
        
        return max(0, min(100, score))
    
    def _generate_discussion_points(self, insights: List[Dict], issues: List[Dict]) -> List[str]:
        """Generate discussion points for daily scrum"""
        points = []
        
        critical = [i for i in insights if i['severity'] in ['critical', 'high']]
        if critical:
            points.append(f"⚠️ {len(critical)} high-priority issues need attention")
        
        blocked = [i for i in issues if i.get('status', '').lower() == 'blocked']
        if blocked:
            points.append(f"🚫 {len(blocked)} blocked issues to discuss")
        
        in_progress = [i for i in issues if i.get('status', '').lower() in ['in progress', 'in review']]
        if len(in_progress) > 10:
            points.append(f"📊 High WIP: {len(in_progress)} items in progress")
        
        if not points:
            points.append("✅ No critical issues - team health looks good!")
        
        return points
    
    def get_trend_data(self, metric_type: str, days: int = 30) -> List[Dict]:
        """Get historical trend data for a metric"""
        return self.data_store.get_metric_history(metric_type, days)
    
    def save_metric_snapshot(self, metric_type: str, data: Dict, mode: str = 'scrum'):
        """Save current metric snapshot for trending"""
        self.data_store.save_metrics(metric_type, data, mode)
    
    def get_rules(self) -> List[Dict]:
        """Get all configured rules"""
        return [
            {
                'name': r.name,
                'condition': r.condition,
                'severity': r.severity,
                'message_template': r.message_template,
                'category': r.category
            }
            for r in self.rules
        ]
