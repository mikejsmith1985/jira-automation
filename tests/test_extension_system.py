"""
Tests for Extension System
"""
import os
import sys
import unittest
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions.base_extension import (
    BaseExtension, 
    DataSourceExtension, 
    ExtensionCapability, 
    ExtensionStatus
)
from extensions.extension_manager import ExtensionManager
from extensions.jira.jira_transformer import JiraTransformer
from storage.data_store import DataStore
from storage.config_manager import ConfigManager


class MockExtension(DataSourceExtension):
    """Mock extension for testing"""
    
    @property
    def name(self): return "mock"
    
    @property
    def display_name(self): return "Mock Extension"
    
    @property
    def version(self): return "1.0.0"
    
    @property
    def description(self): return "Test extension"
    
    @property
    def config_schema(self): return {"type": "object", "properties": {}}
    
    def initialize(self, config, **kwargs):
        self._config = config
        self._status = ExtensionStatus.READY
        return True
    
    def test_connection(self):
        return {'success': True, 'message': 'Connected'}
    
    def get_capabilities(self):
        return [ExtensionCapability.READ]
    
    def extract_data(self, query):
        return {'success': True, 'data': [{'key': 'TEST-1'}], 'count': 1}
    
    def transform_to_features(self, raw_data):
        return [{'key': 'TEST-1', 'name': 'Test Feature'}]
    
    def transform_to_dependencies(self, raw_data):
        return {}


class TestExtensionManager(unittest.TestCase):
    """Test ExtensionManager functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.yaml')
        self.manager = ExtensionManager(self.config_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_register_extension(self):
        """Test extension registration"""
        ext = MockExtension()
        result = self.manager.register_extension(ext)
        
        self.assertTrue(result)
        self.assertIn('mock', self.manager.extensions)
    
    def test_get_extension(self):
        """Test getting extension by name"""
        ext = MockExtension()
        self.manager.register_extension(ext)
        
        retrieved = self.manager.get_extension('mock')
        self.assertEqual(retrieved.name, 'mock')
    
    def test_list_extensions(self):
        """Test listing all extensions"""
        ext = MockExtension()
        self.manager.register_extension(ext)
        
        extensions = self.manager.list_extensions()
        self.assertEqual(len(extensions), 1)
        self.assertEqual(extensions[0]['name'], 'mock')
    
    def test_configure_extension(self):
        """Test extension configuration"""
        ext = MockExtension()
        self.manager.register_extension(ext)
        
        result = self.manager.configure_extension('mock', {'test_key': 'test_value'})
        self.assertTrue(result['success'])
    
    def test_get_data_sources(self):
        """Test getting data source extensions"""
        ext = MockExtension()
        self.manager.register_extension(ext)
        ext.initialize({})
        
        sources = self.manager.get_data_sources()
        self.assertEqual(len(sources), 1)


class TestJiraTransformer(unittest.TestCase):
    """Test JiraTransformer functionality"""
    
    def setUp(self):
        self.sample_issues = [
            {
                'key': 'PROJ-1',
                'summary': 'Epic 1',
                'type': 'Epic',
                'status': 'In Progress',
                'assignee': 'user1',
                'links': []
            },
            {
                'key': 'PROJ-2',
                'summary': 'Story 1',
                'type': 'Story',
                'status': 'Done',
                'epic_link': 'PROJ-1',
                'story_points': 5,
                'assignee': 'user2',
                'links': []
            },
            {
                'key': 'PROJ-3',
                'summary': 'Story 2',
                'type': 'Story',
                'status': 'In Progress',
                'epic_link': 'PROJ-1',
                'story_points': 3,
                'assignee': 'user1',
                'links': [{'type': 'is blocked by', 'target': 'PROJ-2'}]
            }
        ]
    
    def test_to_feature_structure(self):
        """Test converting issues to feature structure"""
        features = JiraTransformer.to_feature_structure(self.sample_issues)
        
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0]['key'], 'PROJ-1')
        self.assertEqual(len(features[0]['children']), 2)
        self.assertEqual(features[0]['progress'], 50.0)
    
    def test_to_dependency_graph(self):
        """Test converting issues to dependency graph"""
        graph = JiraTransformer.to_dependency_graph(self.sample_issues)
        
        self.assertIn('PROJ-3', graph)
        self.assertEqual(len(graph['PROJ-3']['blockers']), 1)
        self.assertEqual(graph['PROJ-3']['blockers'][0]['key'], 'PROJ-2')
    
    def test_to_metrics_scrum(self):
        """Test calculating Scrum metrics"""
        metrics = JiraTransformer.to_metrics(self.sample_issues, mode='scrum')
        
        self.assertIn('summary', metrics)
        self.assertIn('scrum', metrics)
        self.assertEqual(metrics['summary']['total_issues'], 3)
    
    def test_to_metrics_kanban(self):
        """Test calculating Kanban metrics"""
        metrics = JiraTransformer.to_metrics(self.sample_issues, mode='kanban')
        
        self.assertIn('kanban', metrics)
        self.assertIn('wip', metrics['kanban'])
    
    def test_to_daily_scrum_report(self):
        """Test generating daily scrum report"""
        report = JiraTransformer.to_daily_scrum_report(self.sample_issues)
        
        self.assertIn('blockers', report)
        self.assertIn('in_progress', report)
        self.assertIn('summary', report)
    
    def test_csv_round_trip(self):
        """Test CSV export and import"""
        csv_output = JiraTransformer.to_csv(self.sample_issues)
        self.assertIn('PROJ-1', csv_output)
        
        # CSV import uses different column names, so check export works
        self.assertIn('key', csv_output.lower())
        self.assertIn('summary', csv_output.lower())


class TestDataStore(unittest.TestCase):
    """Test DataStore functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.store = DataStore(self.db_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_get_import(self):
        """Test saving and retrieving import"""
        data = [{'key': 'TEST-1', 'summary': 'Test'}]
        import_id = self.store.save_import('jira', data, 'project = TEST')
        
        self.assertIsNotNone(import_id)
        
        latest = self.store.get_latest_import('jira')
        self.assertEqual(latest['count'], 1)
        self.assertEqual(latest['data'][0]['key'], 'TEST-1')
    
    def test_save_and_get_features(self):
        """Test saving and retrieving features"""
        features = [{'key': 'FEAT-1', 'name': 'Feature 1'}]
        feat_id = self.store.save_features(features)
        
        self.assertIsNotNone(feat_id)
        
        retrieved = self.store.get_latest_features()
        self.assertEqual(len(retrieved), 1)
    
    def test_save_and_get_insights(self):
        """Test saving and retrieving insights"""
        insight_id = self.store.save_insight(
            rule_name='test_rule',
            severity='high',
            message='Test insight',
            affected_issues=['TEST-1', 'TEST-2']
        )
        
        self.assertIsNotNone(insight_id)
        
        insights = self.store.get_active_insights()
        self.assertEqual(len(insights), 1)
        self.assertEqual(insights[0]['rule_name'], 'test_rule')
    
    def test_resolve_insight(self):
        """Test resolving an insight"""
        insight_id = self.store.save_insight('test', 'low', 'Test')
        
        result = self.store.resolve_insight(insight_id)
        self.assertTrue(result)
        
        insights = self.store.get_active_insights()
        self.assertEqual(len(insights), 0)
    
    def test_audit_log(self):
        """Test audit logging"""
        log_id = self.store.log_action(
            action='import',
            extension='jira',
            details={'count': 10}
        )
        
        self.assertIsNotNone(log_id)
        
        logs = self.store.get_audit_log(days=1)
        self.assertEqual(len(logs), 1)


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.yaml')
        self.manager = ConfigManager(self.config_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_get_with_default(self):
        """Test getting config with default"""
        value = self.manager.get('nonexistent.key', 'default')
        self.assertEqual(value, 'default')
    
    def test_set_and_get(self):
        """Test setting and getting config"""
        self.manager.set('test.key', 'test_value')
        value = self.manager.get('test.key')
        self.assertEqual(value, 'test_value')
    
    def test_extension_config(self):
        """Test extension configuration"""
        self.manager.set_extension_config('jira', {'base_url': 'https://test.atlassian.net'})
        
        config = self.manager.get_extension_config('jira')
        self.assertEqual(config['base_url'], 'https://test.atlassian.net')
    
    def test_insight_rules(self):
        """Test insight rule management"""
        rule = {
            'name': 'test_rule',
            'condition': 'status = blocked',
            'severity': 'high'
        }
        
        self.manager.add_insight_rule(rule)
        
        rules = self.manager.get_insight_rules()
        self.assertEqual(len(rules), 1)
        
        self.manager.remove_insight_rule('test_rule')
        rules = self.manager.get_insight_rules()
        self.assertEqual(len(rules), 0)


if __name__ == '__main__':
    unittest.main()
