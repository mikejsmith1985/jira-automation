"""
Report Generator
Multi-format report generation for SM persona
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from io import StringIO


class ReportGenerator:
    """
    Generate reports in multiple formats (HTML, CSV, JSON).
    Supports daily scrum, sprint, and custom reports.
    """
    
    def __init__(self):
        self.templates = {
            'daily_scrum': self._daily_scrum_template,
            'sprint_summary': self._sprint_summary_template,
            'team_health': self._team_health_template,
            'metrics': self._metrics_template
        }
    
    def generate(self, report_type: str, data: Dict, format: str = 'html') -> str:
        """
        Generate report in specified format.
        
        Args:
            report_type: Type of report (daily_scrum, sprint_summary, etc.)
            data: Report data
            format: Output format (html, csv, json, markdown)
            
        Returns:
            Report content as string
        """
        if format == 'html':
            return self._generate_html(report_type, data)
        elif format == 'csv':
            return self._generate_csv(report_type, data)
        elif format == 'json':
            return self._generate_json(data)
        elif format == 'markdown':
            return self._generate_markdown(report_type, data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_html(self, report_type: str, data: Dict) -> str:
        """Generate HTML report"""
        template_func = self.templates.get(report_type, self._generic_template)
        content = template_func(data)
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Waypoint Report - {report_type.replace('_', ' ').title()}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .report-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .report-header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .report-header .meta {{ opacity: 0.9; font-size: 14px; }}
        .section {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            font-size: 20px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card .value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .stat-card .label {{ color: #666; font-size: 14px; }}
        .issue-list {{ list-style: none; }}
        .issue-list li {{
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .issue-list li:last-child {{ border-bottom: none; }}
        .issue-key {{
            font-weight: bold;
            color: #667eea;
            margin-right: 10px;
        }}
        .badge {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }}
        .badge-critical {{ background: #fee2e2; color: #dc2626; }}
        .badge-high {{ background: #fef3c7; color: #d97706; }}
        .badge-medium {{ background: #dbeafe; color: #2563eb; }}
        .badge-low {{ background: #dcfce7; color: #16a34a; }}
        .health-score {{
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            padding: 20px;
        }}
        .health-good {{ color: #16a34a; }}
        .health-warning {{ color: #d97706; }}
        .health-critical {{ color: #dc2626; }}
        .discussion-points {{
            background: #fffbeb;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin-top: 15px;
        }}
        .discussion-points li {{ margin-bottom: 8px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .footer {{
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    {content}
    <div class="footer">
        Generated by Waypoint on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>'''
    
    def _daily_scrum_template(self, data: Dict) -> str:
        """Generate daily scrum report content"""
        summary = data.get('summary', {})
        blockers = data.get('blockers', {})
        in_progress = data.get('in_progress', {})
        completed = data.get('completed_yesterday', {})
        discussion = data.get('discussion_points', [])
        
        health_score = summary.get('health_score', 100)
        health_class = 'good' if health_score >= 80 else ('warning' if health_score >= 50 else 'critical')
        
        blockers_html = ''
        for issue in blockers.get('issues', []):
            blockers_html += f'''
                <li>
                    <div>
                        <span class="issue-key">{issue.get('key', '')}</span>
                        {issue.get('summary', '')}
                    </div>
                    <span class="badge badge-critical">{issue.get('assignee', 'Unassigned')}</span>
                </li>'''
        
        discussion_html = ''.join(f'<li>{point}</li>' for point in discussion)
        
        return f'''
<div class="report-header">
    <h1>🌅 Daily Scrum Report</h1>
    <div class="meta">Generated: {datetime.now().strftime('%A, %B %d, %Y at %H:%M')}</div>
</div>

<div class="section">
    <h2>📊 Team Health</h2>
    <div class="health-score health-{health_class}">{health_score}%</div>
    <div class="stat-grid">
        <div class="stat-card">
            <div class="value">{summary.get('total_active', 0)}</div>
            <div class="label">Active Issues</div>
        </div>
        <div class="stat-card">
            <div class="value">{blockers.get('count', 0)}</div>
            <div class="label">Blocked</div>
        </div>
        <div class="stat-card">
            <div class="value">{in_progress.get('count', 0)}</div>
            <div class="label">In Progress</div>
        </div>
        <div class="stat-card">
            <div class="value">{completed.get('count', 0)}</div>
            <div class="label">Completed Yesterday</div>
        </div>
    </div>
</div>

<div class="section">
    <h2>🚫 Blockers ({blockers.get('count', 0)})</h2>
    <ul class="issue-list">
        {blockers_html if blockers_html else '<li>No blockers! 🎉</li>'}
    </ul>
</div>

<div class="section">
    <h2>💬 Discussion Points</h2>
    <ul class="discussion-points">
        {discussion_html if discussion_html else '<li>No critical items to discuss</li>'}
    </ul>
</div>
'''
    
    def _sprint_summary_template(self, data: Dict) -> str:
        """Generate sprint summary content"""
        metrics = data.get('scrum', {})
        by_status = data.get('by_status', {})
        
        status_rows = ''.join(
            f'<tr><td>{status}</td><td>{count}</td></tr>'
            for status, count in by_status.items()
        )
        
        return f'''
<div class="report-header">
    <h1>🏃 Sprint Summary</h1>
    <div class="meta">Sprint Report</div>
</div>

<div class="section">
    <h2>📈 Sprint Metrics</h2>
    <div class="stat-grid">
        <div class="stat-card">
            <div class="value">{metrics.get('velocity', 0)}</div>
            <div class="label">Velocity (Points)</div>
        </div>
        <div class="stat-card">
            <div class="value">{metrics.get('stories_done', 0)}/{metrics.get('stories_total', 0)}</div>
            <div class="label">Stories Completed</div>
        </div>
        <div class="stat-card">
            <div class="value">{metrics.get('completion_rate', 0):.1f}%</div>
            <div class="label">Completion Rate</div>
        </div>
        <div class="stat-card">
            <div class="value">{metrics.get('remaining_points', 0)}</div>
            <div class="label">Remaining Points</div>
        </div>
    </div>
</div>

<div class="section">
    <h2>📊 By Status</h2>
    <table>
        <thead>
            <tr><th>Status</th><th>Count</th></tr>
        </thead>
        <tbody>
            {status_rows}
        </tbody>
    </table>
</div>
'''
    
    def _team_health_template(self, data: Dict) -> str:
        """Generate team health report content"""
        insights = data.get('insights', [])
        
        insights_html = ''
        for insight in insights:
            severity_class = insight.get('severity', 'medium')
            insights_html += f'''
                <tr>
                    <td><span class="badge badge-{severity_class}">{severity_class.upper()}</span></td>
                    <td>{insight.get('message', '')}</td>
                    <td>{insight.get('count', 0)}</td>
                </tr>'''
        
        return f'''
<div class="report-header">
    <h1>💚 Team Health Report</h1>
    <div class="meta">Health Analysis</div>
</div>

<div class="section">
    <h2>🔍 Insights</h2>
    <table>
        <thead>
            <tr><th>Severity</th><th>Issue</th><th>Affected</th></tr>
        </thead>
        <tbody>
            {insights_html if insights_html else '<tr><td colspan="3">No issues found! Team is healthy! 🎉</td></tr>'}
        </tbody>
    </table>
</div>
'''
    
    def _metrics_template(self, data: Dict) -> str:
        """Generate metrics report content"""
        return self._generic_template(data)
    
    def _generic_template(self, data: Dict) -> str:
        """Generic template for unknown report types"""
        import json
        return f'''
<div class="report-header">
    <h1>📄 Report</h1>
</div>
<div class="section">
    <pre>{json.dumps(data, indent=2)}</pre>
</div>
'''
    
    def _generate_csv(self, report_type: str, data: Dict) -> str:
        """Generate CSV report"""
        import csv
        
        output = StringIO()
        
        if 'data' in data and isinstance(data['data'], list):
            issues = data['data']
            if issues:
                writer = csv.DictWriter(output, fieldnames=issues[0].keys())
                writer.writeheader()
                writer.writerows(issues)
        else:
            writer = csv.writer(output)
            for key, value in data.items():
                if isinstance(value, (str, int, float)):
                    writer.writerow([key, value])
        
        return output.getvalue()
    
    def _generate_json(self, data: Dict) -> str:
        """Generate JSON report"""
        import json
        return json.dumps(data, indent=2, default=str)
    
    def _generate_markdown(self, report_type: str, data: Dict) -> str:
        """Generate Markdown report"""
        title = report_type.replace('_', ' ').title()
        
        md = f"# {title}\n\n"
        md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        
        def dict_to_md(d: Dict, level: int = 0) -> str:
            result = ""
            indent = "  " * level
            
            for key, value in d.items():
                if isinstance(value, dict):
                    result += f"{indent}## {key}\n\n"
                    result += dict_to_md(value, level + 1)
                elif isinstance(value, list):
                    result += f"{indent}### {key}\n\n"
                    for item in value:
                        if isinstance(item, dict):
                            result += f"{indent}- "
                            result += ", ".join(f"**{k}**: {v}" for k, v in item.items())
                            result += "\n"
                        else:
                            result += f"{indent}- {item}\n"
                    result += "\n"
                else:
                    result += f"{indent}**{key}**: {value}\n\n"
            
            return result
        
        md += dict_to_md(data)
        
        return md
    
    def save_report(self, content: str, filename: str, directory: str = 'reports') -> str:
        """Save report to file"""
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
