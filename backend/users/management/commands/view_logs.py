from django.core.management.base import BaseCommand
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'View recent log entries from all log files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lines',
            type=int,
            default=10,
            help='Number of recent lines to show from each log file (default: 10)'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Show logs from specific file only (django, auth, api, error)'
        )

    def handle(self, *args, **options):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        logs_dir = BASE_DIR / 'logs'
        lines_to_show = options['lines']
        specific_file = options.get('file')
        
        log_files = {
            'django': 'Django General Logs',
            'auth': 'Authentication Logs', 
            'api': 'API Request/Response Logs',
            'error': 'Error Logs'
        }
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("LMS LOG VIEWER - Recent Log Entries"))
        self.stdout.write("=" * 80)
        
        files_to_show = {specific_file: log_files[specific_file]} if specific_file else log_files
        
        for log_key, description in files_to_show.items():
            log_file = f"{log_key}.log"
            log_path = logs_dir / log_file
            
            self.stdout.write(f"\n📋 {description} ({log_file})")
            self.stdout.write("-" * 60)
            
            if log_path.exists():
                try:
                    with open(log_path, 'r') as f:
                        file_lines = f.readlines()
                        recent_lines = file_lines[-lines_to_show:] if len(file_lines) > lines_to_show else file_lines
                        
                        for line in recent_lines:
                            self.stdout.write(line.strip())
                            
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error reading {log_file}: {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"File not found: {log_file}"))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(f"Log files location: {logs_dir}")
        self.stdout.write("=" * 80)
