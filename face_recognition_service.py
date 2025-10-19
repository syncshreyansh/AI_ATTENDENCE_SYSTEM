# Face recognition and blink detection service
import cv2
import face_recognition
import dlib
import numpy as np
from scipy.spatial import distance as dist
import pickle
from models import Student

class FaceRecognitionService:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.loaded = False


    def _ensure_loaded(self):
      
        if not self.loaded:
            try:
                self.load_known_faces()
            except Exception as e:
                print(f"Error lazily loading faces: {e}")

    def load_known_faces(self):
        # Load all enrolled students
        # Note: This requires an active Flask application context to work
        print("### DEBUG ### Loading known faces from database...")
        try:
            students = Student.query.filter_by(status='active').all()
            self.known_encodings = []
            self.known_names = []
            self.known_ids = []
            for student in students:
                
                if student.face_encoding is not None:
                
                    self.known_encodings.append(student.face_encoding)
                    self.known_names.append(student.name)
                    self.known_ids.append(student.id)
            self.loaded = True # <-- SET FLAG
            print(f"### DEBUG ### Loaded {len(self.known_ids)} faces.")
        except Exception as e:
            print(f"Error loading known faces: {e}")



    def calculate_ear(self, eye):
        # Calculate Eye Aspect Ratio
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear

    def detect_blink(self, frame):
        # Detect blink for liveness verification
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray)
        for face in faces:
            landmarks = self.predictor(gray, face)
            landmarks = np.array([(p.x, p.y) for p in landmarks.parts()])
            left_eye = landmarks[42:48]
            right_eye = landmarks[36:42]
            left_ear = self.calculate_ear(left_eye)
            right_ear = self.calculate_ear(right_eye)
            ear = (left_ear + right_ear) / 2.0
            if ear < 0.25:
                return True
        return False

    def recognize_faces(self, frame):
        self._ensure_loaded()
        # Recognize faces in frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        results = []
        
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_encodings, face_encoding)
            face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
            
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index] and face_distances[best_match_index] < 0.6:
                    results.append({
                        'student_id': self.known_ids[best_match_index],
                        'name': self.known_names[best_match_index],
                        'confidence': 1 - face_distances[best_match_index]
                    })
        
        # Return both the matches and the total number of faces detected
        return {'matches': results, 'total_faces': len(face_locations)}

    def enroll_student(self, frame, student_id):
        self._ensure_loaded()
        # Enroll new student face
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        face_locations = face_recognition.face_locations(rgb_frame, model='hog')
        
        if len(face_locations) == 0:
            print("### DEBUG ### 'hog' model found 0 faces, trying 'cnn' model...")
            face_locations = face_recognition.face_locations(rgb_frame, model='cnn')

        # Check the results
        if len(face_locations) == 0:
            return (False, "No face found in the image. Please try again with better lighting or a clearer photo.")
        
        if len(face_locations) > 1:
            return (False, "Multiple faces found. Please ensure only one person is in the photo.")

        face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
        
        student = Student.query.filter_by(student_id=student_id).first()
        
        if student:
            student.face_encoding = face_encoding
            return (True, "Face encoding successful.")
        
        return (False, "Student ID not found in database (this should not happen).")