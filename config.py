# System configuration settings
import os
from datetime import timedelta

class Config:
    # Database
    DATABASE_PATH = 'attendance_system.db'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_PORT = 5000
    DEBUG = False
    
    # Camera
    CAMERA_INDEX = 0
    FRAME_WIDTH = 1280
    FRAME_HEIGHT = 720
    
    # Face Recognition
    FACE_TOLERANCE = 0.6
    RECOGNITION_CONFIDENCE = 0.4
    
    # Blink Detection
    EAR_THRESHOLD = 0.25
    BLINK_CONSECUTIVE_FRAMES = 3
    REQUIRED_BLINKS = 2
    
    # WhatsApp API
    WHATSAPP_TOKEN = os.environ.get('WHATSAPP_TOKEN')
    WHATSAPP_PHONE_ID = os.environ.get('WHATSAPP_PHONE_ID')
    WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.environ.get('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
    
    # Alert Settings
    ABSENCE_THRESHOLD = 3
    LATE_THRESHOLD_MINUTES = 10
    TAMPER_SENSITIVITY = 0.8