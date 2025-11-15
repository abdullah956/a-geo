"""
Management command to check if the auto-end scheduler is running
"""
import logging
from django.core.management.base import BaseCommand
from attendance.auto_end_scheduler import _scheduler_thread, _scheduler_running

logger = logging.getLogger('attendance')


class Command(BaseCommand):
    help = 'Check if the auto-end scheduler is running'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Auto-End Scheduler Status Check')
        self.stdout.write('='*60 + '\n')
        
        # Check scheduler status
        if _scheduler_running:
            self.stdout.write(self.style.SUCCESS('✓ Scheduler flag: RUNNING'))
        else:
            self.stdout.write(self.style.ERROR('✗ Scheduler flag: NOT RUNNING'))
        
        if _scheduler_thread is not None:
            if _scheduler_thread.is_alive():
                self.stdout.write(self.style.SUCCESS(f'✓ Scheduler thread: ALIVE (name: {_scheduler_thread.name})'))
            else:
                self.stdout.write(self.style.ERROR('✗ Scheduler thread: DEAD'))
        else:
            self.stdout.write(self.style.ERROR('✗ Scheduler thread: NOT CREATED'))
        
        # Try to manually run the check function
        self.stdout.write('\n' + '-'*60)
        self.stdout.write('Testing auto-end function...')
        self.stdout.write('-'*60)
        
        try:
            from attendance.auto_end_scheduler import auto_end_expired_sessions
            ended_count = auto_end_expired_sessions()
            self.stdout.write(self.style.SUCCESS(f'✓ Function executed successfully. Ended {ended_count} session(s)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Function failed: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())
        
        self.stdout.write('\n' + '='*60 + '\n')

