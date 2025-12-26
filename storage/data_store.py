"""
Data Store
SQLite-based storage for imported data, insights, and metrics
"""
import os
import json
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager


class DataStore:
    """
    SQLite-based data storage for Waypoint.
    Stores imported data, insights, metrics, and audit logs.
    """
    
    def __init__(self, db_path: str = 'data/waypoint.db'):
        self.db_path = db_path
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self._init_schema()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_schema(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS imports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extension TEXT NOT NULL,
                    query TEXT,
                    data TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    import_id INTEGER,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (import_id) REFERENCES imports(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    import_id INTEGER,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (import_id) REFERENCES imports(id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    affected_issues TEXT,
                    resolved INTEGER DEFAULT 0,
                    resolved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    mode TEXT DEFAULT 'scrum',
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    extension TEXT,
                    details TEXT,
                    success INTEGER DEFAULT 1,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_imports_extension ON imports(extension)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_imports_created ON imports(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_insights_resolved ON insights(resolved)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_type ON metrics(metric_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action)')
    
    def save_import(self, extension: str, data: List[Dict], query: str = None) -> int:
        """
        Save imported data.
        
        Returns:
            Import ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO imports (extension, query, data, count) VALUES (?, ?, ?, ?)',
                (extension, query, json.dumps(data), len(data))
            )
            return cursor.lastrowid
    
    def get_latest_import(self, extension: str) -> Optional[Dict]:
        """Get most recent import from an extension"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM imports WHERE extension = ? ORDER BY created_at DESC LIMIT 1',
                (extension,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'extension': row['extension'],
                    'query': row['query'],
                    'data': json.loads(row['data']),
                    'count': row['count'],
                    'created_at': row['created_at']
                }
            return None
    
    def get_import_history(self, extension: str, days: int = 30, limit: int = 100) -> List[Dict]:
        """Get import history for an extension"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute(
                '''SELECT id, extension, query, count, created_at 
                   FROM imports 
                   WHERE extension = ? AND created_at >= ?
                   ORDER BY created_at DESC
                   LIMIT ?''',
                (extension, cutoff, limit)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def save_features(self, features: List[Dict], import_id: int = None) -> int:
        """Save feature structure"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO features (import_id, data) VALUES (?, ?)',
                (import_id, json.dumps(features))
            )
            return cursor.lastrowid
    
    def get_latest_features(self) -> Optional[List[Dict]]:
        """Get most recent feature structure"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT data FROM features ORDER BY created_at DESC LIMIT 1'
            )
            row = cursor.fetchone()
            
            if row:
                return json.loads(row['data'])
            return None
    
    def save_dependencies(self, dependencies: Dict, import_id: int = None) -> int:
        """Save dependency graph"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO dependencies (import_id, data) VALUES (?, ?)',
                (import_id, json.dumps(dependencies))
            )
            return cursor.lastrowid
    
    def get_latest_dependencies(self) -> Optional[Dict]:
        """Get most recent dependency graph"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT data FROM dependencies ORDER BY created_at DESC LIMIT 1'
            )
            row = cursor.fetchone()
            
            if row:
                return json.loads(row['data'])
            return None
    
    def save_insight(self, rule_name: str, severity: str, message: str, 
                     affected_issues: List[str] = None) -> int:
        """Save an insight"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO insights (rule_name, severity, message, affected_issues) 
                   VALUES (?, ?, ?, ?)''',
                (rule_name, severity, message, json.dumps(affected_issues or []))
            )
            return cursor.lastrowid
    
    def get_active_insights(self, days: int = 7) -> List[Dict]:
        """Get unresolved insights"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute(
                '''SELECT * FROM insights 
                   WHERE resolved = 0 AND created_at >= ?
                   ORDER BY 
                       CASE severity 
                           WHEN 'critical' THEN 1 
                           WHEN 'high' THEN 2 
                           WHEN 'medium' THEN 3 
                           ELSE 4 
                       END,
                       created_at DESC''',
                (cutoff,)
            )
            
            return [
                {
                    'id': row['id'],
                    'rule_name': row['rule_name'],
                    'severity': row['severity'],
                    'message': row['message'],
                    'affected_issues': json.loads(row['affected_issues']),
                    'created_at': row['created_at']
                }
                for row in cursor.fetchall()
            ]
    
    def resolve_insight(self, insight_id: int) -> bool:
        """Mark insight as resolved"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE insights SET resolved = 1, resolved_at = ? WHERE id = ?',
                (datetime.now().isoformat(), insight_id)
            )
            return cursor.rowcount > 0
    
    def save_metrics(self, metric_type: str, data: Dict, mode: str = 'scrum') -> int:
        """Save metric snapshot"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO metrics (metric_type, mode, data) VALUES (?, ?, ?)',
                (metric_type, mode, json.dumps(data))
            )
            return cursor.lastrowid
    
    def get_metric_history(self, metric_type: str, days: int = 30) -> List[Dict]:
        """Get metric history for trending"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute(
                '''SELECT * FROM metrics 
                   WHERE metric_type = ? AND created_at >= ?
                   ORDER BY created_at ASC''',
                (metric_type, cutoff)
            )
            
            return [
                {
                    'id': row['id'],
                    'metric_type': row['metric_type'],
                    'mode': row['mode'],
                    'data': json.loads(row['data']),
                    'created_at': row['created_at']
                }
                for row in cursor.fetchall()
            ]
    
    def log_action(self, action: str, extension: str = None, 
                   details: Dict = None, success: bool = True, error: str = None) -> int:
        """Log an action to audit log"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO audit_log (action, extension, details, success, error) 
                   VALUES (?, ?, ?, ?, ?)''',
                (action, extension, json.dumps(details) if details else None, 
                 1 if success else 0, error)
            )
            return cursor.lastrowid
    
    def get_audit_log(self, days: int = 7, action: str = None, limit: int = 100) -> List[Dict]:
        """Get audit log entries"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            if action:
                cursor.execute(
                    '''SELECT * FROM audit_log 
                       WHERE action = ? AND created_at >= ?
                       ORDER BY created_at DESC
                       LIMIT ?''',
                    (action, cutoff, limit)
                )
            else:
                cursor.execute(
                    '''SELECT * FROM audit_log 
                       WHERE created_at >= ?
                       ORDER BY created_at DESC
                       LIMIT ?''',
                    (cutoff, limit)
                )
            
            return [
                {
                    'id': row['id'],
                    'action': row['action'],
                    'extension': row['extension'],
                    'details': json.loads(row['details']) if row['details'] else None,
                    'success': bool(row['success']),
                    'error': row['error'],
                    'created_at': row['created_at']
                }
                for row in cursor.fetchall()
            ]
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up data older than specified days"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('DELETE FROM imports WHERE created_at < ?', (cutoff,))
            cursor.execute('DELETE FROM features WHERE created_at < ?', (cutoff,))
            cursor.execute('DELETE FROM dependencies WHERE created_at < ?', (cutoff,))
            cursor.execute('DELETE FROM metrics WHERE created_at < ?', (cutoff,))
            cursor.execute('DELETE FROM audit_log WHERE created_at < ?', (cutoff,))
            cursor.execute('DELETE FROM insights WHERE resolved = 1 AND resolved_at < ?', (cutoff,))


_store_instance: Optional[DataStore] = None


def get_data_store(db_path: str = 'data/waypoint.db') -> DataStore:
    """Get or create the global data store instance"""
    global _store_instance
    if _store_instance is None:
        _store_instance = DataStore(db_path)
    return _store_instance
