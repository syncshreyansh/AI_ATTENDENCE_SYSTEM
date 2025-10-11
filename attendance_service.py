# Attendance management service
from datetime import datetime, date, time, timedelta
from models import db, Student, Attendance, Alert
from whatsapp_service import WhatsAppService

class AttendanceService:
    def __init__(self):
        self.whatsapp = WhatsAppService()

    def mark_attendance(self, student_id, confidence, blink_verified=False):
        # Mark student attendance
        today = date.today()
        current_time = datetime.now().time()
        
        # Check if already marked today
        existing = Attendance.query.filter_by(
            student_id=student_id,
            date=today
        ).first()
        
        if not existing:
            points = self.calculate_points(current_time, blink_verified)
            attendance = Attendance(
                student_id=student_id,
                date=today,
                time_in=current_time,
                status='present',
                confidence=confidence,
                blink_verified=blink_verified,
                points_earned=points
            )
            # Update student points
            student = Student.query.get(student_id)
            if student:
                student.points += points
                db.session.add(attendance)
                db.session.commit()
                return {
                    'success': True,
                    'points': points,
                    'student_name': student.name
                }
        
        return {'success': False, 'message': 'Already marked today'}

    def calculate_points(self, time_in, blink_verified=False):
        # Calculate points based on arrival time and verification
        base_points = 10
        
        # Early arrival bonus
        if time_in < time(8, 30):
            base_points += 5
        elif time_in > time(9, 0):
            base_points -= 3
            
        # Liveness verification bonus
        if blink_verified:
            base_points += 2
            
        return max(base_points, 1)

    def get_attendance_stats(self, date_filter=None):
        # Get attendance statistics
        if not date_filter:
            date_filter = date.today()
            
        total_students = Student.query.filter_by(status='active').count()
        present_today = Attendance.query.filter_by(
            date=date_filter,
            status='present'
        ).count()
        
        return {
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': total_students - present_today,
            'attendance_rate': (present_today / total_students * 100) if total_students > 0 else 0
        }

    def check_absence_patterns(self):
        # Check for consecutive absences
        cutoff_date = date.today() - timedelta(days=3)
        
        # Subquery to find IDs of students who were present in the last 3 days
        present_student_ids = db.session.query(Attendance.student_id).filter(Attendance.date >= cutoff_date).distinct()
        
        # Find students who are active but not in the list of present students
        absent_students = Student.query.filter(
            Student.status == 'active',
            ~Student.id.in_(present_student_ids)
        ).all()
        
        for student in absent_students:
            if student.parent_phone:
                alert = Alert(
                    student_id=student.id,
                    alert_type='consecutive_absence',
                    message=f'{student.name} has been absent for 3+ days'
                )
                db.session.add(alert)
                
                # Send WhatsApp alert
                self.whatsapp.send_absence_alert(
                    student.parent_phone,
                    student.name,
                    3
                )
        db.session.commit()