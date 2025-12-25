"""
Simple SQLite-based feedback storage
No external dependencies, no API calls, no crashes
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path


class FeedbackDB:
    """Simple feedback storage in SQLite"""
    
    def __init__(self, db_path='feedback.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Create feedback table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                timestamp TEXT NOT NULL,
                logs TEXT,
                attachments TEXT,
                status TEXT DEFAULT 'open',
                github_issue_url TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_feedback(self, title, description, logs=None, attachments=None):
        """
        Store feedback in database
        
        Args:
            title: Feedback title
            description: Feedback description
            logs: JSON string of log data
            attachments: JSON string of attachments (base64 encoded)
            
        Returns:
            int: Feedback ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO feedback (title, description, timestamp, logs, attachments)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, timestamp, logs, attachments))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def get_all_feedback(self, status=None):
        """
        Get all feedback entries
        
        Args:
            status: Filter by status ('open', 'closed', 'synced')
            
        Returns:
            list: List of feedback dicts
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM feedback WHERE status = ? ORDER BY timestamp DESC', (status,))
        else:
            cursor.execute('SELECT * FROM feedback ORDER BY timestamp DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_feedback(self, feedback_id):
        """Get single feedback entry by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM feedback WHERE id = ?', (feedback_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_status(self, feedback_id, status, github_issue_url=None):
        """Update feedback status (open, closed, synced)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if github_issue_url:
            cursor.execute('''
                UPDATE feedback 
                SET status = ?, github_issue_url = ?
                WHERE id = ?
            ''', (status, github_issue_url, feedback_id))
        else:
            cursor.execute('''
                UPDATE feedback 
                SET status = ?
                WHERE id = ?
            ''', (status, feedback_id))
        
        conn.commit()
        conn.close()
    
    def export_to_json(self, output_file='feedback_export.json'):
        """Export all feedback to JSON file"""
        feedback_list = self.get_all_feedback()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(feedback_list, f, indent=2)
        
        return output_file
    
    def export_to_csv(self, output_file='feedback_export.csv'):
        """Export all feedback to CSV file"""
        import csv
        
        feedback_list = self.get_all_feedback()
        
        if not feedback_list:
            return None
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'title', 'description', 'timestamp', 'status'])
            writer.writeheader()
            
            for item in feedback_list:
                writer.writerow({
                    'id': item['id'],
                    'title': item['title'],
                    'description': item['description'],
                    'timestamp': item['timestamp'],
                    'status': item['status']
                })
        
        return output_file
