"""
CSV Importer Module
Handles parsing of Jira CSV exports and mapping to internal data structure.
"""
import csv
import io
import logging

class JiraCSVImporter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_csv(self, file_content_bytes):
        """
        Parses raw CSV bytes and returns headers and rows.
        """
        try:
            # Decode bytes to string
            content = file_content_bytes.decode('utf-8')
            
            # Use StringIO to create a file-like object
            f = io.StringIO(content)
            
            # Read CSV
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)
            
            return {
                'success': True,
                'headers': headers,
                'rows': rows,
                'count': len(rows)
            }
        except Exception as e:
            self.logger.error(f"Error parsing CSV: {e}")
            return {'success': False, 'error': str(e)}

    def map_data(self, rows, mapping):
        """
        Maps raw CSV rows to internal schema based on provided mapping.
        
        Args:
            rows: List of dicts (from CSV)
            mapping: Dict of {internal_field: csv_header}
                     e.g. {'key': 'Issue key', 'summary': 'Summary'}
        """
        mapped_issues = []
        
        for row in rows:
            issue = {}
            for internal_field, csv_header in mapping.items():
                if csv_header and csv_header in row:
                    issue[internal_field] = row[csv_header]
            
            # Ensure minimal required fields
            if 'key' in issue:
                mapped_issues.append(issue)
                
        return mapped_issues
