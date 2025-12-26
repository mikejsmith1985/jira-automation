"""
Jira Data Transformer
Transforms Jira data to Waypoint structures
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class JiraTransformer:
    """
    Transform Jira data to Waypoint-compatible structures.
    Handles feature hierarchy, dependency graphs, and metrics.
    """
    
    @staticmethod
    def to_feature_structure(issues: List[Dict]) -> List[Dict]:
        """
        Transform flat Jira issues to hierarchical feature structure.
        
        Args:
            issues: List of Jira issue dictionaries
            
        Returns:
            Hierarchical feature structure for PO view
        """
        features = []
        epics = [i for i in issues if i.get('type', '').lower() == 'epic']
        stories = [i for i in issues if i.get('type', '').lower() in ['story', 'task', 'bug', 'subtask']]
        
        for epic in epics:
            epic_key = epic['key']
            
            children = [
                s for s in stories 
                if s.get('epic_link') == epic_key or s.get('parent') == epic_key
            ]
            
            done_count = sum(1 for c in children if c.get('status', '').lower() in ['done', 'closed', 'resolved'])
            total_points = sum(c.get('story_points', 0) or 0 for c in children)
            done_points = sum(
                c.get('story_points', 0) or 0 
                for c in children 
                if c.get('status', '').lower() in ['done', 'closed', 'resolved']
            )
            
            progress = (done_count / len(children) * 100) if children else 0
            
            feature = {
                'key': epic_key,
                'name': epic.get('summary', ''),
                'description': epic.get('description', ''),
                'status': epic.get('status', ''),
                'priority': epic.get('priority', ''),
                'assignee': epic.get('assignee', ''),
                'progress': round(progress, 1),
                'total_children': len(children),
                'done_children': done_count,
                'total_points': total_points,
                'done_points': done_points,
                'labels': epic.get('labels', []),
                'children': [
                    {
                        'key': child['key'],
                        'name': child.get('summary', ''),
                        'status': child.get('status', ''),
                        'type': child.get('type', ''),
                        'assignee': child.get('assignee', ''),
                        'priority': child.get('priority', ''),
                        'story_points': child.get('story_points', 0),
                        'labels': child.get('labels', [])
                    }
                    for child in children
                ]
            }
            
            features.append(feature)
        
        orphan_stories = [
            s for s in stories
            if not s.get('epic_link') and not s.get('parent')
        ]
        
        if orphan_stories:
            features.append({
                'key': '__NO_EPIC__',
                'name': 'Stories Without Epic',
                'status': 'N/A',
                'priority': 'N/A',
                'progress': 0,
                'total_children': len(orphan_stories),
                'done_children': sum(1 for s in orphan_stories if s.get('status', '').lower() in ['done', 'closed']),
                'children': [
                    {
                        'key': s['key'],
                        'name': s.get('summary', ''),
                        'status': s.get('status', ''),
                        'type': s.get('type', ''),
                        'assignee': s.get('assignee', ''),
                        'story_points': s.get('story_points', 0)
                    }
                    for s in orphan_stories
                ]
            })
        
        return features
    
    @staticmethod
    def to_dependency_graph(issues: List[Dict]) -> Dict:
        """
        Build dependency graph from issue links.
        
        Args:
            issues: List of Jira issues with links
            
        Returns:
            Dependency graph dictionary
        """
        graph = {}
        
        for issue in issues:
            key = issue['key']
            
            graph[key] = {
                'key': key,
                'title': issue.get('summary', ''),
                'status': issue.get('status', ''),
                'type': issue.get('type', ''),
                'assignee': issue.get('assignee', ''),
                'blockers': [],
                'blocks': [],
                'related': []
            }
            
            for link in issue.get('links', []):
                link_type = link.get('type', '').lower()
                target = link.get('target', '')
                
                if 'blocked by' in link_type or 'depends on' in link_type:
                    graph[key]['blockers'].append({
                        'key': target,
                        'type': link.get('type', '')
                    })
                elif 'blocks' in link_type or 'is dependency' in link_type:
                    graph[key]['blocks'].append({
                        'key': target,
                        'type': link.get('type', '')
                    })
                else:
                    graph[key]['related'].append({
                        'key': target,
                        'type': link.get('type', '')
                    })
        
        return graph
    
    @staticmethod
    def to_metrics(issues: List[Dict], mode: str = 'scrum', sprint_name: str = None) -> Dict:
        """
        Calculate metrics for SM reporting.
        
        Args:
            issues: List of Jira issues
            mode: 'scrum' or 'kanban'
            sprint_name: Optional sprint name filter
            
        Returns:
            Metrics dictionary
        """
        metrics = {
            'summary': {
                'total_issues': len(issues),
                'done': 0,
                'in_progress': 0,
                'todo': 0,
                'blocked': 0
            },
            'by_status': defaultdict(int),
            'by_type': defaultdict(int),
            'by_assignee': defaultdict(int),
            'by_priority': defaultdict(int)
        }
        
        for issue in issues:
            status = issue.get('status', 'Unknown').lower()
            
            metrics['by_status'][issue.get('status', 'Unknown')] += 1
            metrics['by_type'][issue.get('type', 'Unknown')] += 1
            metrics['by_assignee'][issue.get('assignee', 'Unassigned')] += 1
            metrics['by_priority'][issue.get('priority', 'None')] += 1
            
            if status in ['done', 'closed', 'resolved']:
                metrics['summary']['done'] += 1
            elif status in ['in progress', 'in review', 'in development']:
                metrics['summary']['in_progress'] += 1
            elif status in ['blocked']:
                metrics['summary']['blocked'] += 1
            else:
                metrics['summary']['todo'] += 1
        
        metrics['by_status'] = dict(metrics['by_status'])
        metrics['by_type'] = dict(metrics['by_type'])
        metrics['by_assignee'] = dict(metrics['by_assignee'])
        metrics['by_priority'] = dict(metrics['by_priority'])
        
        if mode == 'scrum':
            metrics['scrum'] = JiraTransformer._calculate_scrum_metrics(issues, sprint_name)
        else:
            metrics['kanban'] = JiraTransformer._calculate_kanban_metrics(issues)
        
        return metrics
    
    @staticmethod
    def _calculate_scrum_metrics(issues: List[Dict], sprint_name: str = None) -> Dict:
        """Calculate Scrum-specific metrics"""
        sprint_issues = issues
        if sprint_name:
            sprint_issues = [i for i in issues if sprint_name in str(i.get('sprints', []))]
        
        total_points = sum(i.get('story_points', 0) or 0 for i in sprint_issues)
        done_issues = [i for i in sprint_issues if i.get('status', '').lower() in ['done', 'closed', 'resolved']]
        done_points = sum(i.get('story_points', 0) or 0 for i in done_issues)
        
        return {
            'velocity': done_points,
            'total_committed': total_points,
            'completion_rate': (done_points / total_points * 100) if total_points else 0,
            'stories_done': len(done_issues),
            'stories_total': len(sprint_issues),
            'remaining_points': total_points - done_points
        }
    
    @staticmethod
    def _calculate_kanban_metrics(issues: List[Dict]) -> Dict:
        """Calculate Kanban-specific metrics"""
        in_progress = [i for i in issues if i.get('status', '').lower() in ['in progress', 'in review', 'in development']]
        
        return {
            'wip': len(in_progress),
            'wip_by_assignee': JiraTransformer._count_by_field(in_progress, 'assignee'),
            'throughput_estimate': 'N/A'
        }
    
    @staticmethod
    def _count_by_field(issues: List[Dict], field: str) -> Dict:
        """Count issues by a specific field"""
        counts = defaultdict(int)
        for issue in issues:
            value = issue.get(field, 'Unknown')
            counts[value] += 1
        return dict(counts)
    
    @staticmethod
    def to_daily_scrum_report(issues: List[Dict], insights: List[Dict] = None) -> Dict:
        """
        Generate daily scrum-focused report.
        
        Args:
            issues: Current sprint/active issues
            insights: Optional insights from insights engine
            
        Returns:
            Report structure for daily scrum
        """
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        blockers = [
            i for i in issues 
            if i.get('status', '').lower() == 'blocked' or
            any(link.get('type', '').lower().startswith('blocked') for link in i.get('links', []))
        ]
        
        recently_completed = [
            i for i in issues
            if i.get('status', '').lower() in ['done', 'closed', 'resolved']
        ]
        
        in_progress = [
            i for i in issues
            if i.get('status', '').lower() in ['in progress', 'in review', 'in development']
        ]
        
        at_risk = []
        if insights:
            at_risk = [
                insight for insight in insights
                if insight.get('severity') in ['high', 'critical']
            ]
        
        return {
            'generated_at': now.isoformat(),
            'blockers': {
                'count': len(blockers),
                'issues': [
                    {
                        'key': b['key'],
                        'summary': b.get('summary', ''),
                        'assignee': b.get('assignee', ''),
                        'blocked_reason': JiraTransformer._get_blocker_reason(b)
                    }
                    for b in blockers
                ]
            },
            'completed_yesterday': {
                'count': len(recently_completed),
                'issues': [
                    {
                        'key': c['key'],
                        'summary': c.get('summary', ''),
                        'assignee': c.get('assignee', ''),
                        'type': c.get('type', '')
                    }
                    for c in recently_completed[:10]
                ]
            },
            'in_progress': {
                'count': len(in_progress),
                'by_assignee': JiraTransformer._group_by_assignee(in_progress)
            },
            'at_risk': {
                'count': len(at_risk),
                'insights': at_risk[:5]
            },
            'summary': {
                'total_active': len([i for i in issues if i.get('status', '').lower() not in ['done', 'closed']]),
                'blocked_percentage': (len(blockers) / len(issues) * 100) if issues else 0,
                'health': 'good' if len(blockers) == 0 else ('warning' if len(blockers) < 3 else 'critical')
            }
        }
    
    @staticmethod
    def _get_blocker_reason(issue: Dict) -> str:
        """Extract blocker reason from issue links"""
        for link in issue.get('links', []):
            if 'blocked' in link.get('type', '').lower():
                return f"Blocked by {link.get('target', 'unknown')}"
        return 'Status set to Blocked'
    
    @staticmethod
    def _group_by_assignee(issues: List[Dict]) -> Dict:
        """Group issues by assignee"""
        grouped = defaultdict(list)
        for issue in issues:
            assignee = issue.get('assignee', 'Unassigned')
            grouped[assignee].append({
                'key': issue['key'],
                'summary': issue.get('summary', '')
            })
        return dict(grouped)
    
    @staticmethod
    def from_csv(csv_data: str, mapping: Dict = None) -> List[Dict]:
        """
        Parse CSV data to issue structure.
        
        Args:
            csv_data: CSV string content
            mapping: Optional column name mapping
            
        Returns:
            List of issue dictionaries
        """
        import csv
        from io import StringIO
        
        issues = []
        mapping = mapping or {
            'Issue key': 'key',
            'Summary': 'summary',
            'Issue Type': 'type',
            'Status': 'status',
            'Priority': 'priority',
            'Assignee': 'assignee',
            'Epic Link': 'epic_link',
            'Story Points': 'story_points',
            'Labels': 'labels'
        }
        
        reader = csv.DictReader(StringIO(csv_data))
        
        for row in reader:
            issue = {}
            for csv_col, field_name in mapping.items():
                if csv_col in row:
                    value = row[csv_col]
                    if field_name == 'story_points':
                        try:
                            value = float(value) if value else 0
                        except:
                            value = 0
                    elif field_name == 'labels':
                        value = [l.strip() for l in value.split(',') if l.strip()] if value else []
                    issue[field_name] = value
            
            if issue.get('key'):
                issues.append(issue)
        
        return issues
    
    @staticmethod
    def to_csv(issues: List[Dict], columns: List[str] = None) -> str:
        """
        Export issues to CSV format.
        
        Args:
            issues: List of issue dictionaries
            columns: Optional list of columns to include
            
        Returns:
            CSV string
        """
        import csv
        from io import StringIO
        
        if not issues:
            return ''
        
        columns = columns or ['key', 'summary', 'type', 'status', 'priority', 'assignee', 'story_points']
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        
        for issue in issues:
            row = {k: issue.get(k, '') for k in columns}
            if 'labels' in columns and isinstance(row.get('labels'), list):
                row['labels'] = ', '.join(row['labels'])
            writer.writerow(row)
        
        return output.getvalue()
