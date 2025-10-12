import os
from pathlib import Path

def view_logs():
    """
    Utility function to view recent log entries
    """
    BASE_DIR = Path(__file__).resolve().parent.parent
    logs_dir = BASE_DIR / 'logs'
    
    log_files = {
        'django.log': 'Django General Logs',
        'auth.log': 'Authentication Logs', 
        'api.log': 'API Request/Response Logs',
        'error.log': 'Error Logs'
    }
    
    print("=" * 80)
    print("LMS LOG VIEWER - Recent Log Entries")
    print("=" * 80)
    
    for log_file, description in log_files.items():
        log_path = logs_dir / log_file
        
        if log_path.exists():
            print(f"\n📋 {description} ({log_file})")
            print("-" * 60)
            
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    # Show last 10 lines
                    recent_lines = lines[-10:] if len(lines) > 10 else lines
                    
                    for line in recent_lines:
                        print(line.strip())
                        
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
        else:
            print(f"\n📋 {description} ({log_file}) - File not found")
    
    print("\n" + "=" * 80)
    print("Log files location:", logs_dir)
    print("=" * 80)

if __name__ == "__main__":
    view_logs()
