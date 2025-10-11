🔮 Smart Attendance System with Face Recognition
A futuristic, real-time attendance system powered by Python, OpenCV, and Flask, featuring a sleek, glassmorphism UI with dark/light modes.

This project revolutionizes traditional attendance tracking by using computer vision to automate the process. It's a full-stack application that combines a powerful Python backend for face recognition with a highly aesthetic and responsive web dashboard for monitoring.

✨ Core Features
👨‍💻 Real-Time Face Recognition: Uses the dlib and face_recognition libraries to identify enrolled students from a live webcam feed.

😉 Liveness Detection: Implements blink detection (calculating Eye Aspect Ratio) to ensure the subject is a live person, not a static photo.

🔮 Aesthetic Frontend: A beautiful glassmorphism interface built with pure HTML, CSS, and JavaScript. Features include:

Animated "liquid glass" cards with purple glow effects.

A sleek, animated dark/light mode toggle.

A fully responsive grid-based layout for perfect alignment.

📊 Live Dashboard: The frontend updates in real-time using WebSockets (Flask-SocketIO) to display attendance events as they happen.

⚡ Performance Optimized: The backend is optimized to reduce CPU load by implementing frame skipping and configurable camera resolution, ensuring smooth operation.

🔐 Secure & Modular: The backend is organized into services for attendance, face recognition, and API routes, making it easy to maintain and extend.

⚙️ What Does What: System Architecture
This project is a full-stack application with distinct components working together. Here’s how they fit:

Frontend (The "Face" - What You See)
templates/dashboard.html: The core structure of the web application. It defines all the elements like cards, buttons, and the video feed placeholder.

static/css/dashboard.css: This file contains all the aesthetic styling. It's responsible for the glassmorphism, purple glow, animations, dark/light modes, and the perfectly aligned grid layout.

static/js/dashboard.js: The interactive brain of the frontend. It connects to the backend via WebSockets, handles user actions (like clicking "Start System" or enrolling a student), manages the live camera feed in the browser, and dynamically updates the UI when new data arrives.

Backend (The "Brain" - The Server Logic)
main.py: The entry point of the application. It starts the Flask web server, initializes the database, and runs the main camera processing loop in a separate thread for performance.

routes.py: Defines all the API endpoints. When your browser fetches data (like stats or the leaderboard), it's communicating with the functions defined in this file.

config.py: A centralized place to manage all settings, such as camera resolution, port number, and face recognition tolerances.

Computer Vision Engine (The "Eyes")
face_recognition_service.py: This is the heart of the AI. It contains all the complex computer vision logic for detecting faces, calculating the eye aspect ratio for blink detection, and comparing faces against the database of enrolled students.

shape_predictor_68_face_landmarks.dat: A crucial pre-trained model file from dlib that the CV engine uses to locate 68 specific points on a face.

Database (The "Memory")
models.py: Defines the structure (schema) for the database tables (Student, Attendance, etc.) using Flask-SQLAlchemy.

attendance.db: The physical SQLite database file where all student information, face encodings, and attendance records are stored.

🚀 Getting Started
Follow these instructions to get the project running on your local machine.

Prerequisites
You will need the following installed on your system:

Python 3.9+: Make sure Python is installed and added to your system's PATH.

Microsoft C++ Build Tools: Required to compile the dlib library.

Download the Visual Studio Build Tools.

During installation, select the "Desktop development with C++" workload.

CMake: Required for the dlib build process.

Download the official installer from cmake.org.

During installation, make sure to select the option "Add CMake to the system PATH for all users".

Installation
Clone the repository:

git clone [https://github.com/YOUR_USERNAME/smart-attendance-system.git](https://github.com/YOUR_USERNAME/smart-attendance-system.git)
cd smart-attendance-system

Create and activate a Python virtual environment:

# Create the environment
python -m venv venv

# Activate it (on Windows)
venv\Scripts\activate

Install the required Python packages:

pip install -r requirements.txt

This step might take several minutes as it needs to compile dlib.

Download the Face Predictor Model:

Download the model file from this link.

Extract it using a tool like 7-Zip or WinRAR.

Place the resulting shape_predictor_68_face_landmarks.dat file in the main project folder.

Running the Application
Start the Flask server:

python main.py

Open the dashboard:

Open your web browser and navigate to http://localhost:5000.

📝 How to Use
Enroll a Student:

Click the "Enroll Student" button.

Fill in the details.

Click "Capture Photo" and allow camera access when prompted.

Click the final "Enroll Student" button.

Start the System:

Click the "Start System" button. The status indicator will turn green and "Online".

The backend will now start processing your camera feed.

Mark Attendance:

Position your face in front of the camera and blink a couple of times.

The dashboard will update in real-time when you are recognized.
