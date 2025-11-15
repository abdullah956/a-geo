"""
Management command to test attendance rate calculation
"""
from django.core.management.base import BaseCommand
from courses.models import Enrollment
from attendance.models import AttendanceSession, Attendance


class Command(BaseCommand):
    help = 'Test attendance rate calculation for debugging'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Attendance Rate Calculation Test')
        self.stdout.write('='*60 + '\n')
        
        # Get all enrollments
        enrollments = Enrollment.objects.filter(is_active=True).select_related('student', 'course')[:10]
        
        for enrollment in enrollments:
            self.stdout.write(f"\nStudent: {enrollment.student.email}")
            self.stdout.write(f"Course: {enrollment.course.code} - {enrollment.course.title}")
            
            # Check all sessions
            all_sessions = AttendanceSession.objects.filter(course=enrollment.course)
            self.stdout.write(f"  Total sessions (all statuses): {all_sessions.count()}")
            
            for session in all_sessions:
                self.stdout.write(f"    - Session {session.id}: {session.title} - Status: '{session.status}'")
            
            # Check ended sessions
            ended_sessions = AttendanceSession.objects.filter(
                course=enrollment.course,
                status='ended'
            )
            self.stdout.write(f"  Ended sessions: {ended_sessions.count()}")
            
            # Check attendance records
            if ended_sessions.exists():
                attendances = Attendance.objects.filter(
                    session__in=ended_sessions,
                    student=enrollment.student
                )
                total_records = attendances.count()
                present_count = attendances.filter(is_present=True).count()
                
                self.stdout.write(f"  Attendance records: {total_records}")
                self.stdout.write(f"  Present: {present_count}, Absent: {total_records - present_count}")
                
                if ended_sessions.count() > 0:
                    rate = (present_count / ended_sessions.count() * 100)
                    self.stdout.write(f"  Attendance Rate: {rate:.2f}%")
                else:
                    self.stdout.write(f"  Attendance Rate: N/A (no ended sessions)")
            else:
                self.stdout.write(f"  No ended sessions - cannot calculate rate")
        
        self.stdout.write('\n' + '='*60 + '\n')

