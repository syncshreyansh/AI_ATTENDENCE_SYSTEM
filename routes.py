# Flask API routes
from flask import Blueprint, request, jsonify, render_template
from flask_socketio import emit
from datetime import datetime, date
from models import db, Student, Attendance, Alert
from attendance_service import AttendanceService
from face_recognition_service import FaceRecognitionService
import base64
import cv2
import numpy as np

api = Blueprint('api', __name__)
attendance_service = AttendanceService()
face_service = FaceRecognitionService()

@api.route('/')
def dashboard():
    # Serve main dashboard
    return render_template('dashboard.html')

@api.route('/api/students', methods=['GET', 'POST'])
def students():
    # Student CRUD operations
    if request.method == 'GET':
        students = Student.query.filter_by(status='active').all()
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'student_id': s.student_id,
            'class': s.class_name,
            'section': s.section,
            'points': s.points
        } for s in students])
    elif request.method == 'POST':
        data = request.json
        student = Student(
            name=data['name'],
            student_id=data['student_id'],
            class_name=data['class'],
            section=data['section'],
            parent_phone=data.get('parent_phone')
        )
        db.session.add(student)
        db.session.commit()
        return jsonify({'id': student.id, 'message': 'Student created'})

@api.route('/api/attendance', methods=['GET', 'POST'])
def attendance():
    # Attendance operations
    if request.method == 'GET':
        date_filter_str = request.args.get('date')
        date_filter = datetime.strptime(date_filter_str, '%Y-%m-%d').date() if date_filter_str else date.today()
        attendances = Attendance.query.filter_by(date=date_filter).all()
        return jsonify([{
            'id': a.id,
            'student_name': Student.query.get(a.student_id).name,
            'time_in': a.time_in.isoformat() if a.time_in else None,
            'status': a.status,
            'confidence': a.confidence,
            'points': a.points_earned
        } for a in attendances])
    elif request.method == 'POST':
        data = request.json
        result = attendance_service.mark_attendance(
            data['student_id'],
            data.get('confidence', 0.5),
            data.get('blink_verified', False)
        )
        return jsonify(result)

@api.route('/api/stats')
def stats():
    # Get attendance statistics
    stats_data = attendance_service.get_attendance_stats()
    return jsonify(stats_data)

@api.route('/api/leaderboard')
def leaderboard():
    # Get top students by points
    top_students = Student.query.filter_by(status='active').order_by(
        Student.points.desc()
    ).limit(10).all()
    return jsonify([{
        'rank': idx + 1,
        'name': s.name,
        'points': s.points,
        'class': f"{s.class_name}-{s.section}"
    } for idx, s in enumerate(top_students)])

@api.route('/api/alerts')
def alerts():
    # Get recent alerts
    recent_alerts = Alert.query.order_by(
        Alert.timestamp.desc()
    ).limit(20).all()
    return jsonify([{
        'id': a.id,
        'type': a.alert_type,
        'message': a.message,
        'timestamp': a.timestamp.isoformat(),
        'sent': a.sent
    } for a in recent_alerts])

@api.route('/api/enroll', methods=['POST'])
def enroll_face():
    # Enroll student face encoding
    data = request.json
    student_id = data['student_id']
    frame_data = data['frame']  # Base64 encoded frame
    
    # Decode frame and process
    frame_bytes = base64.b64decode(frame_data)
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    success = face_service.enroll_student(frame, student_id)
    if success:
        # Commit the face encoding to the database
        db.session.commit()
        face_service.load_known_faces()  # Reload faces
        return jsonify({'success': True, 'message': 'Face enrolled successfully'})
    else:
        return jsonify({'success': False, 'message': 'Face enrollment failed'})

@api.route('/api/recognize', methods=['POST'])
def recognize():
    # Process recognition request
    data = request.json
    frame_data = data['frame']
    blink_detected = data.get('blink_detected', False)
    
    # Decode and process frame
    frame_bytes = base64.b64decode(frame_data)
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    recognized = face_service.recognize_faces(frame)
    results = []
    for person in recognized:
        result = attendance_service.mark_attendance(
            person['student_id'],
            person['confidence'],
            blink_detected
        )
        results.append({
            'name': person['name'],
            'confidence': person['confidence'],
            'attendance_result': result
        })
    return jsonify({'recognized': results})