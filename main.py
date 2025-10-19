# Main Flask application
from flask import Flask
from flask_socketio import SocketIO, emit
from models import db
from routes import api
from config import Config
import cv2
import threading
import time

def create_app():
    # Create and configure Flask app
    app = Flask(__name__)
    app.config.from_object(Config)
    # Initialize extensions
    db.init_app(app)
    # Register blueprints
    app.register_blueprint(api)
    return app

app = create_app()
socketio = SocketIO(app, cors_allowed_origins="*")

class CameraService:
    def __init__(self):
        self.camera = cv2.VideoCapture(Config.CAMERA_INDEX)
        # --- OPTIMIZATION: Apply resolution settings from config ---
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.FRAME_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.FRAME_HEIGHT)
        
        self.is_running = False
        self.blink_counter = 0
        self.frame_counter = 0  # Initialize frame counter for skipping frames

    def start_camera(self):
        # Start camera processing thread
        self.is_running = True
        thread = threading.Thread(target=self.process_frames)
        thread.daemon = True
        thread.start()

    def process_frames(self):
        # Main camera processing loop
        from face_recognition_service import FaceRecognitionService
        from attendance_service import AttendanceService
        
        with app.app_context():
            face_service = FaceRecognitionService()
            attendance_service = AttendanceService()

            while self.is_running:
                ret, frame = self.camera.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                self.frame_counter += 1

                if self.frame_counter % 3 == 0:
                    
                    # 1. Recognize faces
                    rec_result = face_service.recognize_faces(frame)
                    total_faces = rec_result['total_faces']
                    matches = rec_result['matches']
                    
                    # 2. Handle Blink Detection & Marking
                    if total_faces > 0 and len(matches) > 0:
                        if face_service.detect_blink(frame):
                            self.blink_counter += 1
                        
                        if self.blink_counter >= Config.REQUIRED_BLINKS:
                            for person in matches:
                                # App context is already active from the 'with' block
                                result = attendance_service.mark_attendance(
                                    person['student_id'],
                                    person['confidence'],
                                    True
                                )

                                if result['success']:
                                    # This event is our "SUCCESS" popup
                                    socketio.emit('attendance_update', {
                                        'student_name': result['student_name'],
                                        'points': result['points'],
                                        'timestamp': time.time()
                                    })
                            self.blink_counter = 0 # Reset blinks after successful recognition
                    
                    # 3. Send Status Updates to Frontend
                    elif total_faces > 0 and len(matches) == 0:
                        # Face detected, but not in database
                        socketio.emit('recognition_status', {
                            'status': 'unknown', 
                            'message': 'Student not listed'
                        })
                    
                    elif total_faces > 0 and len(matches) > 0:
                        # Face recognized, waiting for blinks
                        socketio.emit('recognition_status', {
                            'status': 'recognizing', 
                            'message': f"Recognized {matches[0]['name']}. Please blink..."
                        })

                    else: # total_faces == 0
                        # No face detected, clear any popups
                        socketio.emit('recognition_status', {'status': 'clear'})
                    

                
                time.sleep(0.05)

camera_service = CameraService()

@socketio.on('start_system')
def handle_start_system():
    # Start the attendance system
    camera_service.start_camera()
    emit('system_started', {'status': 'Camera system activated'})

@socketio.on('stop_system')
def handle_stop_system():
    # Stop the attendance system
    camera_service.is_running = False
    emit('system_stopped', {'status': 'Camera system deactivated'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # We are back to http://
    socketio.run(app, host='0.0.0.0', port=Config.FLASK_PORT, debug=Config.DEBUG)