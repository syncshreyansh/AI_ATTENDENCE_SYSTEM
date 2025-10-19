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
import os 

api = Blueprint('api', __name__)
attendance_service = AttendanceService()
face_service = FaceRecognitionService()

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

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
        
        # Check if student_id already exists 
        existing_student = Student.query.filter_by(student_id=data['student_id']).first()
        if existing_student:
            print(f"### DEBUG ### Student creation failed: ID {data['student_id']} already exists.")
            return jsonify({'message': f"Student ID {data['student_id']} already exists."}), 400
            
        student = Student(
            name=data['name'],
            student_id=data['student_id'],
            class_name=data['class'],
            section=data['section'],
            parent_phone=data.get('parent_phone')
        )
        db.session.add(student)
        db.session.commit()
        print(f"### DEBUG ### Student created successfully: {data['student_id']}")
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
    print("\n### DEBUG ### /api/enroll endpoint was hit.")
    
    # Enroll student face encoding
    data = request.json
    student_id_str = data['student_id'] # This is the string ID like "101"
    frame_data = data['frame']  # Base64 encoded frame
    
    print(f"### DEBUG ### Attempting to enroll for student_id: {student_id_str}")
    
    # Decode frame and process
    frame_bytes = base64.b64decode(frame_data)
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Try to enroll the face encoding
    # UPDATED: Now expects a (success, message) tuple
    success, message = face_service.enroll_student(frame, student_id_str)
    
    print(f"### DEBUG ### face_service.enroll_student() returned: success={success}, message={message}")
    
    if success:
        try:
            print("### DEBUG ### Face encoding successful. Trying to save image...")
            # Find student again to save image path
            student = Student.query.filter_by(student_id=student_id_str).first()
            if student:
                # Create the file path
                enroll_dir = os.path.join('static', 'enrollments')
                print(f"### DEBUG ### Target directory: {enroll_dir}")
                ensure_dir(enroll_dir)
                
                image_filename = f"student_{student_id_str}.jpg"
                image_path = os.path.join(enroll_dir, image_filename)
                
                # Save the image to the file
                cv2.imwrite(image_path, frame)
                print(f"### DEBUG ### Image saved to: {image_path}")
                
                # Store the path in the database
                student.image_path = image_path
            
            # Commit both face_encoding and image_path
            db.session.commit()
            print("### DEBUG ### Database commit successful.")
            face_service.load_known_faces()  # Reload faces
            return jsonify({'success': True, 'message': 'Face enrolled and image saved successfully'})
            
        except Exception as e:
            db.session.rollback()
            print(f"\n\n### DEBUG ### ERROR_SAVING_IMAGE_OR_DB_COMMIT: {str(e)}\n\n")
            return jsonify({'success': False, 'message': f'Face enrolled, but failed to save image: {str(e)}'})
    else:
        print(f"### DEBUG ### Face enrollment failed: {message}")
        return jsonify({'success': False, 'message': message})

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