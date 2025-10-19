document.addEventListener("DOMContentLoaded", () => {
  // === THEME TOGGLE LOGIC ===
  const themeToggle = document.getElementById("themeToggle");
  function applyTheme(theme) {
    if (theme === "dark") {
      document.body.classList.add("dark-mode");
      themeToggle.classList.add("dark");
    } else {
      document.body.classList.remove("dark-mode");
      themeToggle.classList.remove("dark");
    }
  }
  themeToggle.addEventListener("click", () => {
    const isDark = document.body.classList.toggle("dark-mode");
    themeToggle.classList.toggle("dark", isDark);
    localStorage.setItem("theme", isDark ? "dark" : "light");
  });
  const savedTheme = localStorage.getItem("theme");
  const prefersDark =
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(savedTheme || (prefersDark ? "dark" : "light"));

  // Initialize the main dashboard functionality
  window.dashboard = new AttendanceDashboard();
});

// === MAIN DASHBOARD CLASS ===
class AttendanceDashboard {
  constructor() {
    this.socket = io();
    this.isSystemRunning = false;
    this.videoStream = null; // To hold the *enrollment* camera stream
    this.liveStream = null; // To hold the *live feed* camera stream

    // --- CACHE DOM ELEMENTS ---
    // Enrollment Modal
    this.captureBtn = document.getElementById("capturePhoto");
    this.recaptureBtn = document.getElementById("recapturePhoto");
    this.videoPreview = document.getElementById("videoPreview");
    this.photoCanvas = document.getElementById("photoCanvas");
    this.enrollSubmitBtn = document.getElementById("enrollSubmitBtn");
    this.enrollModal = document.getElementById("enrollModal");
    this.enrollForm = document.getElementById("enrollForm");

    // Header Controls
    this.startBtn = document.getElementById("startSystem");
    this.stopBtn = document.getElementById("stopSystem");
    this.statusDot = document.getElementById("statusDot");
    this.statusText = document.getElementById("statusText");

    // Live Feed
    this.liveFeedVideo = document.getElementById("liveFeedVideo");
    this.feedPlaceholder = document.getElementById("feedPlaceholder");

    // Recognition Popup
    this.recognitionOverlay = document.getElementById("recognitionOverlay");
    this.recognitionOverlayText = document.getElementById(
      "recognitionOverlayText"
    );
    this.overlayTimeout = null;

    // Stats
    this.presentCountEl = document.getElementById("presentCount");
    this.absentCountEl = document.getElementById("absentCount");
    this.attendanceRateEl = document.getElementById("attendanceRate");
    this.totalStudentsEl = document.getElementById("totalStudents");

    // Recent Events
    this.recentEventsList = document.getElementById("recentEvents");

    this.initializeEventListeners();
    this.loadInitialData();
  }

  initializeEventListeners() {
    this.startBtn.addEventListener("click", () => this.startSystem());
    this.stopBtn.addEventListener("click", () => this.stopSystem());

    document
      .getElementById("enrollBtn")
      .addEventListener("click", () => this.openModal());
    document
      .getElementById("closeModal")
      .addEventListener("click", () => this.closeModal());
    document
      .getElementById("cancelEnroll")
      .addEventListener("click", () => this.closeModal());

    this.enrollForm.addEventListener("submit", (e) => this.handleEnrollSubmit(e));
    this.captureBtn.addEventListener("click", () => this.capturePhoto());
    this.recaptureBtn.addEventListener("click", () => this.recapturePhoto());

    // --- SocketIO Listeners ---
    this.socket.on("recognition_status", (data) => {
      if (data.status === "clear") {
        this.showOverlay(null); // Hide overlay
      } else if (data.status === "unknown") {
        this.showOverlay(data.message, "error"); // Show "Student not listed"
      } else if (data.status === "recognizing") {
        this.showOverlay(data.message, "recognizing"); // Show "Recognizing..."
      }
    });

    this.socket.on("attendance_update", (data) =>
      this.handleAttendanceUpdate(data)
    );
    this.socket.on("system_started", () => this.updateSystemStatus(true));
    this.socket.on("system_stopped", () => this.updateSystemStatus(false));
  }

  // === Video Stream Methods ===

  async startVideoStream() {
    // For enrollment modal
    if (this.videoStream) return;
    try {
      this.videoStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });
      this.videoPreview.srcObject = this.videoStream;
      this.videoPreview.style.display = "block";
      this.photoCanvas.style.display = "none";
    } catch (error) {
      this.showNotification(
        "Camera access denied. Please allow camera permissions in your browser.",
        "error"
      );
      this.closeModal();
    }
  }

  stopVideoStream() {
    // For enrollment modal
    if (this.videoStream) {
      this.videoStream.getTracks().forEach((track) => track.stop());
      this.videoStream = null;
    }
  }

  async startLiveFeed() {
    // For main dashboard feed
    if (this.liveStream) return;
    try {
      this.liveStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });
      this.liveFeedVideo.srcObject = this.liveStream;
      this.liveFeedVideo.style.display = "block";
      this.feedPlaceholder.style.display = "none";
    } catch (error) {
      this.showNotification(
        "Camera access denied. Please allow camera permissions.",
        "error"
      );
      this.updateSystemStatus(false); // Failed to start, so update status back
    }
  }

  stopLiveFeed() {
    // For main dashboard feed
    if (this.liveStream) {
      this.liveStream.getTracks().forEach((track) => track.stop());
      this.liveStream = null;
    }
    this.liveFeedVideo.srcObject = null;
    this.liveFeedVideo.style.display = "none";
    this.feedPlaceholder.style.display = "flex"; // Show placeholder
  }

  // === Enrollment Modal Methods ===

  openModal() {
    if (this.isSystemRunning) {
      this.showNotification(
        "Please stop the system before enrolling a new student.",
        "warning"
      );
      return;
    }
    this.enrollModal.style.display = "block";
    this.startVideoStream(); // Start *enrollment* preview
    this.resetCaptureUI();
  }

  closeModal() {
    this.stopVideoStream(); // Stop *enrollment* preview
    this.enrollModal.style.display = "none";
    this.enrollForm.reset();
    this.resetCaptureUI();
  }

  capturePhoto() {
    if (!this.videoStream) {
      this.showNotification("Camera is not active.", "warning");
      return;
    }
    const context = this.photoCanvas.getContext("2d");

    this.photoCanvas.width = this.videoPreview.videoWidth;
    this.photoCanvas.height = this.videoPreview.videoHeight;

    // Flip the context to get a non-mirrored final image
    context.translate(this.photoCanvas.width, 0);
    context.scale(-1, 1);
    context.drawImage(
      this.videoPreview,
      0,
      0,
      this.photoCanvas.width,
      this.photoCanvas.height
    );

    this.stopVideoStream();

    this.videoPreview.style.display = "none";
    this.photoCanvas.style.display = "block";

    this.captureBtn.classList.add("hidden");
    this.recaptureBtn.classList.remove("hidden");
    this.enrollSubmitBtn.disabled = false; // Enable submit
  }

  recapturePhoto() {
    this.videoPreview.style.display = "block";
    this.photoCanvas.style.display = "none";

    this.captureBtn.classList.remove("hidden");
    this.recaptureBtn.classList.add("hidden");
    this.enrollSubmitBtn.disabled = true; // Disable submit

    this.startVideoStream(); // Restart camera
  }

  resetCaptureUI() {
    this.videoPreview.style.display = "block";
    this.photoCanvas.style.display = "none";

    this.captureBtn.classList.remove("hidden");
    this.recaptureBtn.classList.add("hidden");

    this.enrollSubmitBtn.disabled = true; // Always disable submit on reset
  }

  // === Data Loading & API Methods ===

  async loadInitialData() {
    this.loadStats();
    // this.loadLeaderboard(); // You can uncomment this if you implement it
    this.loadRecentAttendance();
  }

  async loadStats() {
    try {
      const response = await fetch("/api/stats");
      const data = await response.json();

      this.presentCountEl.textContent = data.present_today;
      this.absentCountEl.textContent = data.absent_today;
      this.attendanceRateEl.textContent = `${Math.round(
        data.attendance_rate
      )}%`;
      this.totalStudentsEl.textContent = data.total_students;
    } catch (error) {
      console.error("Error loading stats:", error);
    }
  }

  async loadLeaderboard() {
    // Stub for leaderboard
    console.log("Loading leaderboard...");
  }

  async loadRecentAttendance() {
    try {
      const response = await fetch("/api/attendance"); // Fetches today's attendance
      const data = await response.json();

      this.recentEventsList.innerHTML = ""; // Clear the list

      if (data.length === 0) {
        this.recentEventsList.innerHTML =
          '<p style="text-align: center; color: var(--text-secondary)">No events yet</p>';
        return;
      }

      data.forEach((event) => {
        this.addRecentEvent(event);
      });
    } catch (error) {
      console.error("Error loading recent attendance:", error);
    }
  }

  // === System & Socket Methods ===

  startSystem() {
    this.socket.emit("start_system");
    this.startBtn.disabled = true; // Prevent double clicks
  }

  stopSystem() {
    this.socket.emit("stop_system");
    this.stopBtn.disabled = true; // Prevent double clicks
  }

  updateSystemStatus(isRunning) {
    this.isSystemRunning = isRunning;
    if (isRunning) {
      this.startBtn.disabled = true;
      this.stopBtn.disabled = false;
      this.statusDot.classList.remove("offline");
      this.statusDot.classList.add("online");
      this.statusText.textContent = "Online";
      this.startLiveFeed(); // Start frontend camera
    } else {
      this.startBtn.disabled = false;
      this.stopBtn.disabled = true;
      this.statusDot.classList.remove("online");
      this.statusDot.classList.add("offline");
      this.statusText.textContent = "Offline";
      this.stopLiveFeed(); // Stop frontend camera
      this.showOverlay(null); // Clear any popups
    }
  }

  handleAttendanceUpdate(data) {
    // data = { student_name: 'John Doe', points: 10, timestamp: ... }

    // Show the live popup
    this.showOverlay(`${data.student_name} Marked!`, "success");

    // Show the corner notification
    this.showNotification(
      `${data.student_name} marked present! (+${data.points} points)`,
      "success"
    );

    // Add to recent events list
    this.addRecentEvent({
      student_name: data.student_name,
      time_in: data.timestamp, // Pass the timestamp
    });

    // Refresh the stats cards
    this.loadStats();
  }

  async handleEnrollSubmit(event) {
    event.preventDefault();

    const isPhotoTaken = this.photoCanvas.style.display === "block";
    if (!isPhotoTaken) {
      this.showNotification(
        "Please capture a photo before enrolling.",
        "warning"
      );
      return;
    }

    // 1. Get Data from Form
    const studentData = {
      name: document.getElementById("studentName").value,
      student_id: document.getElementById("studentId").value,
      class: document.getElementById("studentClass").value,
      section: document.getElementById("studentSection").value,
      parent_phone: document.getElementById("parentPhone").value,
    };

    try {
      // 2. Create the Student First
      const createStudentResponse = await fetch("/api/students", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(studentData),
      });

      const createResult = await createStudentResponse.json();

      if (!createStudentResponse.ok) {
        this.showNotification(
          createResult.message || "Failed to create student.",
          "error"
        );
        return;
      }

      // 3. If Student Created, Enroll Face
      const studentIdForEnroll = studentData.student_id;
      const canvas = document.getElementById("photoCanvas");
      const frameData = canvas.toDataURL("image/jpeg").split(",")[1];

      const enrollFaceResponse = await fetch("/api/enroll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: studentIdForEnroll,
          frame: frameData,
        }),
      });

      const enrollResult = await enrollFaceResponse.json();

      if (enrollResult.success) {
        this.showNotification(
          "Student created and face enrolled successfully!",
          "success"
        );
        this.closeModal();
        this.loadInitialData(); // Auto-update stats
      } else {
        // Student was created, but face enrollment failed.
        this.showNotification(
          `Student created, but: ${
            enrollResult.message || "Face enrollment failed."
          }`,
          "warning"
        );
        this.closeModal();
        this.loadInitialData(); // Still update (total students changed)
      }
    } catch (error) {
      console.error("Enrollment error:", error);
      this.showNotification("An error occurred during enrollment.", "error");
    }
  }

  // === Helper & UI Methods ===

  showOverlay(message, type) {
    // Clear any existing timer
    clearTimeout(this.overlayTimeout);

    if (!message) {
      // Hide the overlay
      this.recognitionOverlay.classList.remove("show");
      return;
    }

    // Set message and type
    this.recognitionOverlayText.textContent = message;
    this.recognitionOverlay.className = "recognition-overlay"; // Reset classes
    this.recognitionOverlay.classList.add(type); // 'success', 'error', or 'recognizing'
    this.recognitionOverlay.classList.add("show");

    // Auto-hide after 2 seconds
    this.overlayTimeout = setTimeout(() => {
      this.recognitionOverlay.classList.remove("show");
    }, 2000);
  }

  addRecentEvent(data) {
    // data = { student_name: 'John Doe', time_in: 1678886400 }
    // Check if placeholder is there
    const placeholder = this.recentEventsList.querySelector("p");
    if (placeholder) {
      this.recentEventsList.innerHTML = ""; // Clear "No events yet"
    }

    const item = document.createElement("div");
    item.className = "list-item";

    let time = data.time_in;
    
    if (typeof time === 'number') {
        time = this.formatTime(time); // Format timestamp
    } else if (time && time.includes("T")) {
        time = this.formatTime(new Date(time).getTime() / 1000); // Format ISO string
    }

    item.innerHTML = `
      <div class="item-info">
        <strong>${data.student_name}</strong>
        <small>Marked present</small>
      </div>
      <div class="item-badge">
        <small>${time || "Just now"}</small>
      </div>
    `;

    this.recentEventsList.prepend(item); // Add to top of list
  }

  formatTime(timestamp) {
    // timestamp is in seconds
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  }

  showNotification(message, type = "success") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Add to body
    document.body.appendChild(notification);

    // Add CSS for notification
    const style = document.createElement("style");
    style.innerHTML = `
      .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 12px;
        color: #fff;
        font-weight: 600;
        z-index: 2000;
        animation: slideIn 0.3s ease-out, fadeOut 0.3s ease-in 2.7s;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
      }
      .notification.success {
        background: linear-gradient(135deg, #10b981, #059669);
      }
      .notification.error {
        background: linear-gradient(135deg, #ef4444, #dc2626);
      }
      .notification.warning {
        background: linear-gradient(135deg, #f59e0b, #d97706);
      }
      @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
      @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; transform: translateX(100%); }
      }
    `;
    document.head.appendChild(style);

    // Remove after 3 seconds
    setTimeout(() => {
      notification.remove();
      style.remove();
    }, 3000);
  }
}