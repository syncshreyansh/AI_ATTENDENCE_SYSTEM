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
        # You will need to download this file and place it in your project folder
        self.predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
        self.known_encodings = []
        self.known_names = []
        self.known_ids = []
        self.load_known_faces()

    def load_known_faces(self):
        # Load all enrolled students
        # Note: This requires an active Flask application context to work
        try:
            students = Student.query.filter_by(status='active').all()
            self.known_encodings = []
            self.known_names = []
            self.known_ids = []
            for student in students:
                if student.face_encoding:
                    self.known_encodings.append(student.face_encoding)
                    self.known_names.append(student.name)
                    self.known_ids.append(student.id)
        except Exception as e:
            print(f"Error loading known faces: {e}")
            print("This may be due to running outside of a Flask app context.")


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
        return results

    def enroll_student(self, frame, student_id):
        # Enroll new student face
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        if len(face_locations) == 1:
            face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
            student = Student.query.get(student_id)
            if student:
                student.face_encoding = face_encoding
                # Note: This will not commit the change to the database.
                # The calling function should handle db.session.commit()
                return True
        return False