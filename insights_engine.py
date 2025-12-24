"""
Rule-Based Insights Engine
Analyzes Jira data to detect patterns, issues, and trends without AI/LLM.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path


class InsightsDatabase:
    """Manages persistent storage of insights and metrics history"""
    
    def __init__(self, db_path='data/insights.db'):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        """Initialize database schema"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                type TEXT,
                severity TEXT,
                title TEXT,
                message TEXT,
                data TEXT,
                resolved BOOLEAN DEFAULT 0,
                resolved_at DATETIME
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                metric_type TEXT,
                value REAL,
                metadata TEXT
            )
        ''')
        
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_insights_timestamp 
            ON insights(timestamp)
        ''')
        
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_insights_type 
            ON insights(type)
        ''')
        
        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_type 
            ON metrics_history(metric_type, timestamp)
        ''')
        
        self.conn.commit()
    
    def add_insight(self, insight_type, severity, title, message, data=None):
        """Store a new insight"""
        self.conn.execute('''
            INSERT INTO insights (timestamp, type, severity, title, message, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now(), insight_type, severity, title, message, 
              json.dumps(data) if data else None))
        self.conn.commit()
    
    def get_recent_insights(self, days=7, unresolved_only=True):
        """Retrieve recent insights"""
        query = '''
            SELECT id, timestamp, type, severity, title, message, data, resolved
            FROM insights 
            WHERE timestamp > datetime('now', '-{} days')
        '''.format(days)
        
        if unresolved_only:
            query += ' AND resolved = 0'
        
        query += ' ORDER BY timestamp DESC'
        
        results = self.conn.execute(query).fetchall()
        return [
            {
                'id': r[0],
                'timestamp': r[1],
                'type': r[2],
                'severity': r[3],
                'title': r[4],
                'message': r[5],
                'data': json.loads(r[6]) if r[6] else None,
                'resolved': bool(r[7])
            }
            for r in results
        ]
    
    def resolve_insight(self, insight_id):
        """Mark an insight as resolved"""
        self.conn.execute('''
            UPDATE insights 
            SET resolved = 1, resolved_at = ?
            WHERE id = ?
        ''', (datetime.now(), insight_id))
        self.conn.commit()
    
    def track_metric(self, metric_type, value, metadata=None):
        """Store a metric snapshot"""
        self.conn.execute('''
            INSERT INTO metrics_history (timestamp, metric_type, value, metadata)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now(), metric_type, value, 
              json.dumps(metadata) if metadata else None))
        self.conn.commit()
    
    def get_metric_trend(self, metric_type, days=30):
        """Get historical trend for a metric"""
        results = self.conn.execute('''
            SELECT timestamp, value, metadata 
            FROM metrics_history
            WHERE metric_type = ? AND timestamp > datetime('now', '-{} days')
            ORDER BY timestamp ASC
        '''.format(days), (metric_type,)).fetchall()
        
        return [
            {
                'timestamp': r[0],
                'value': r[1],
                'metadata': json.loads(r[2]) if r[2] else None
            }
            for r in results
        ]
    
    def close(self):
        """Close database connection"""
        self.conn.close()


class InsightsEngine:
    """Generates insights from Jira data using rule-based analysis"""
    
    def __init__(self, db_path='data/insights.db'):
        self.db = InsightsDatabase(db_path)
        self.thresholds = {
            'scope_creep_percent': 30,
            'defect_escape_rate': 0.2,
            'velocity_change_percent': 15,
            'stale_days': 14,
            'long_running_days': 10,
            'sprint_completion_min': 70
        }
    
    def analyze_all(self, jira_data):
        """Run all insight checks on provided Jira data"""
        insights = []
        
        insights.extend(self.detect_scope_creep(jira_data.get('stories', [])))
        insights.extend(self.detect_defect_leakage(
            jira_data.get('bugs', []), 
            jira_data.get('stories', [])
        ))
        insights.extend(self.analyze_velocity_trend(
            jira_data.get('velocity_history', [])
        ))
        insights.extend(self.check_team_hygiene(jira_data.get('tickets', [])))
        insights.extend(self.analyze_sprint_completion(
            jira_data.get('sprint_data', {})
        ))
        
        # Store insights in database
        for insight in insights:
            self.db.add_insight(
                insight['type'],
                insight['severity'],
                insight['title'],
                insight['message'],
                insight.get('data')
            )
        
        # Track daily metrics
        self._track_daily_metrics(jira_data)
        
        return insights
    
    def detect_scope_creep(self, stories):
        """Detect stories with significant story point growth"""
        insights = []
        scope_creep_stories = []
        
        for story in stories:
            initial_points = story.get('initial_story_points')
            current_points = story.get('story_points')
            
            if current_points and initial_points and initial_points > 0:
                growth = ((current_points - initial_points) / initial_points) * 100
                
                if growth > self.thresholds['scope_creep_percent']:
                    scope_creep_stories.append({
                        'key': story['key'],
                        'initial': initial_points,
                        'current': current_points,
                        'growth': growth
                    })
        
        if scope_creep_stories:
            total_growth = sum(s['growth'] for s in scope_creep_stories) / len(scope_creep_stories)
            severity = 'error' if len(scope_creep_stories) >= 3 else 'warning'
            
            insights.append({
                'type': 'scope_creep',
                'severity': severity,
                'title': f'⚠️ Scope Creep in {len(scope_creep_stories)} Stories',
                'message': f'Average growth: {total_growth:.0f}%. Review sprint planning and requirements clarity.',
                'data': {
                    'affected_stories': scope_creep_stories,
                    'count': len(scope_creep_stories),
                    'avg_growth': total_growth
                }
            })
        
        return insights
    
    def detect_defect_leakage(self, bugs, stories):
        """Calculate and alert on defect escape rate"""
        insights = []
        
        if not bugs:
            return insights
        
        production_bugs = [b for b in bugs if b.get('environment') == 'production']
        total_bugs = len(bugs)
        escape_rate = len(production_bugs) / total_bugs if total_bugs > 0 else 0
        
        if escape_rate > self.thresholds['defect_escape_rate']:
            insights.append({
                'type': 'defect_leakage',
                'severity': 'error',
                'title': f'🐛 High Defect Leakage ({escape_rate:.0%})',
                'message': f'{len(production_bugs)} of {total_bugs} bugs found in production. Review QA process and test coverage.',
                'data': {
                    'production_bugs': len(production_bugs),
                    'total_bugs': total_bugs,
                    'escape_rate': escape_rate
                }
            })
        
        return insights
    
    def analyze_velocity_trend(self, velocity_history):
        """Detect significant velocity changes"""
        insights = []
        
        if len(velocity_history) < 3:
            return insights
        
        recent_3 = velocity_history[-3:]
        previous_3 = velocity_history[-6:-3] if len(velocity_history) >= 6 else None
        
        recent_avg = sum(recent_3) / len(recent_3)
        
        if previous_3:
            previous_avg = sum(previous_3) / len(previous_3)
            change = ((recent_avg - previous_avg) / previous_avg) * 100
            
            if abs(change) > self.thresholds['velocity_change_percent']:
                trend = '↗️' if change > 0 else '↘️'
                severity = 'info' if change > 0 else 'warning'
                
                insights.append({
                    'type': 'velocity_trend',
                    'severity': severity,
                    'title': f'{trend} Velocity Trend: {change:+.0f}%',
                    'message': f'Average velocity changed from {previous_avg:.0f} to {recent_avg:.0f} points.',
                    'data': {
                        'recent_avg': recent_avg,
                        'previous_avg': previous_avg,
                        'change_percent': change
                    }
                })
        
        return insights
    
    def check_team_hygiene(self, tickets):
        """Run multiple hygiene checks"""
        insights = []
        
        # Stale tickets
        stale = [t for t in tickets if self._days_since_update(t) > self.thresholds['stale_days']]
        if stale:
            insights.append({
                'type': 'stale_tickets',
                'severity': 'warning',
                'title': f'📋 {len(stale)} Stale Tickets',
                'message': f'{len(stale)} tickets with no updates in {self.thresholds["stale_days"]}+ days.',
                'data': {
                    'count': len(stale),
                    'ticket_keys': [t['key'] for t in stale[:10]]
                }
            })
        
        # Missing story points
        no_points = [t for t in tickets if not t.get('story_points') and t.get('type') == 'Story']
        if no_points:
            insights.append({
                'type': 'missing_estimates',
                'severity': 'warning',
                'title': f'📊 {len(no_points)} Stories Without Estimates',
                'message': f'{len(no_points)} stories are missing story points.',
                'data': {
                    'count': len(no_points),
                    'ticket_keys': [t['key'] for t in no_points[:10]]
                }
            })
        
        # Long-running stories
        long_running = [t for t in tickets 
                       if t.get('status') == 'In Progress' 
                       and self._days_in_status(t) > self.thresholds['long_running_days']]
        if long_running:
            insights.append({
                'type': 'long_running',
                'severity': 'error',
                'title': f'⏰ {len(long_running)} Long-Running Stories',
                'message': f'{len(long_running)} stories in progress > {self.thresholds["long_running_days"]} days. Check for blockers.',
                'data': {
                    'count': len(long_running),
                    'ticket_keys': [t['key'] for t in long_running]
                }
            })
        
        # Blocked items
        blocked = [t for t in tickets if 'blocked' in [l.lower() for l in t.get('labels', [])]]
        if blocked:
            avg_blocked_days = sum(self._days_since_blocked(t) for t in blocked) / len(blocked)
            insights.append({
                'type': 'blocked_items',
                'severity': 'error',
                'title': f'🚫 {len(blocked)} Blocked Items',
                'message': f'{len(blocked)} blocked items (avg {avg_blocked_days:.0f} days). Address blockers urgently.',
                'data': {
                    'count': len(blocked),
                    'avg_days': avg_blocked_days,
                    'ticket_keys': [t['key'] for t in blocked]
                }
            })
        
        return insights
    
    def analyze_sprint_completion(self, sprint_data):
        """Analyze sprint completion patterns"""
        insights = []
        
        if not sprint_data:
            return insights
        
        committed = sprint_data.get('committed_points', 0)
        completed = sprint_data.get('completed_points', 0)
        
        if committed == 0:
            return insights
        
        completion_rate = (completed / committed) * 100
        
        if completion_rate < self.thresholds['sprint_completion_min']:
            insights.append({
                'type': 'missed_targets',
                'severity': 'error',
                'title': f'⚠️ Low Sprint Completion ({completion_rate:.0f}%)',
                'message': f'Completed {completed} of {committed} committed points. Review sprint planning.',
                'data': {
                    'committed': committed,
                    'completed': completed,
                    'completion_rate': completion_rate,
                    'sprint': sprint_data.get('sprint_name')
                }
            })
        
        return insights
    
    def _track_daily_metrics(self, jira_data):
        """Store daily metric snapshots for trend analysis"""
        if 'velocity_history' in jira_data and jira_data['velocity_history']:
            current_velocity = jira_data['velocity_history'][-1]
            self.db.track_metric('velocity', current_velocity)
        
        if 'tickets' in jira_data:
            tickets = jira_data['tickets']
            wip_count = len([t for t in tickets if t.get('status') == 'In Progress'])
            blocked_count = len([t for t in tickets 
                               if 'blocked' in [l.lower() for l in t.get('labels', [])]])
            
            self.db.track_metric('wip_count', wip_count)
            self.db.track_metric('blocked_count', blocked_count)
    
    def _days_since_update(self, ticket):
        """Calculate days since last update"""
        updated = ticket.get('updated')
        if not updated:
            return 0
        
        try:
            updated_date = datetime.fromisoformat(updated.replace('Z', '+00:00'))
            return (datetime.now() - updated_date).days
        except:
            return 0
    
    def _days_in_status(self, ticket):
        """Calculate days in current status"""
        status_changed = ticket.get('status_changed')
        if not status_changed:
            return 0
        
        try:
            changed_date = datetime.fromisoformat(status_changed.replace('Z', '+00:00'))
            return (datetime.now() - changed_date).days
        except:
            return 0
    
    def _days_since_blocked(self, ticket):
        """Calculate days since ticket was blocked"""
        blocked_date = ticket.get('blocked_date')
        if not blocked_date:
            return 0
        
        try:
            blocked_dt = datetime.fromisoformat(blocked_date.replace('Z', '+00:00'))
            return (datetime.now() - blocked_dt).days
        except:
            return 0
    
    def get_insights(self, days=7, unresolved_only=True):
        """Retrieve stored insights"""
        return self.db.get_recent_insights(days, unresolved_only)
    
    def get_metric_trend(self, metric_type, days=30):
        """Get historical metric trend"""
        return self.db.get_metric_trend(metric_type, days)
    
    def resolve_insight(self, insight_id):
        """Mark insight as resolved"""
        self.db.resolve_insight(insight_id)
    
    def close(self):
        """Clean up resources"""
        self.db.close()
