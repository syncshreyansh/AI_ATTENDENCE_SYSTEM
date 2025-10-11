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
    this.videoStream = null; // To hold the camera stream state
    this.initializeEventListeners();
    this.loadInitialData();
  }

  initializeEventListeners() {
    document
      .getElementById("startSystem")
      .addEventListener("click", () => this.startSystem());
    document
      .getElementById("stopSystem")
      .addEventListener("click", () => this.stopSystem());
    document
      .getElementById("enrollBtn")
      .addEventListener("click", () => this.openModal());
    document
      .getElementById("closeModal")
      .addEventListener("click", () => this.closeModal());
    document
      .getElementById("cancelEnroll")
      .addEventListener("click", () => this.closeModal());
    document
      .getElementById("enrollForm")
      .addEventListener("submit", (e) => this.handleEnrollSubmit(e));
    document
      .getElementById("capturePhoto")
      .addEventListener("click", () => this.capturePhoto());

    this.socket.on("attendance_update", (data) =>
      this.handleAttendanceUpdate(data)
    );
    this.socket.on("system_started", () => this.updateSystemStatus(true));
    this.socket.on("system_stopped", () => this.updateSystemStatus(false));
  }

  // --- NEW ROBUST VIDEO STREAM METHODS ---
  async startVideoStream() {
    if (this.videoStream) return;
    try {
      this.videoStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });
      const video = document.getElementById("videoPreview");
      video.srcObject = this.videoStream;
      video.style.display = "block";
      document.getElementById("photoCanvas").style.display = "none";
    } catch (error) {
      this.showNotification(
        "Camera access denied. Please allow camera permissions in your browser.",
        "error"
      );
      this.closeModal(); // Close modal if permission is denied
    }
  }

  stopVideoStream() {
    if (this.videoStream) {
      this.videoStream.getTracks().forEach((track) => track.stop());
      this.videoStream = null;
    }
  }

  // --- UPDATED MODAL & CAPTURE METHODS ---
  openModal() {
    document.getElementById("enrollModal").style.display = "block";
    this.startVideoStream(); // Start live preview only when modal opens
  }

  closeModal() {
    this.stopVideoStream(); // CRITICAL: Stop the camera when modal closes
    document.getElementById("enrollModal").style.display = "none";
    document.getElementById("enrollForm").reset();
    const captureBtn = document.getElementById("capturePhoto");
    captureBtn.innerHTML = '<i class="fas fa-camera"></i> Capture Photo';
    captureBtn.classList.remove("success"); // Reset button class
  }

  capturePhoto() {
    if (!this.videoStream) {
      this.showNotification("Camera is not active.", "warning");
      return;
    }
    const video = document.getElementById("videoPreview");
    const canvas = document.getElementById("photoCanvas");
    const context = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Flip the context to get a non-mirrored final image
    context.translate(canvas.width, 0);
    context.scale(-1, 1);
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    this.stopVideoStream();

    video.style.display = "none";
    canvas.style.display = "block";

    const captureBtn = document.getElementById("capturePhoto");
    captureBtn.innerHTML = '<i class="fas fa-check"></i> Photo Captured';
    captureBtn.classList.add("success");
  }

  // --- (The rest of your JS methods are fine) ---
  async loadInitialData() {
    /* ... */
  }
  async loadStats() {
    /* ... */
  }
  async loadLeaderboard() {
    /* ... */
  }
  async loadRecentAttendance() {
    /* ... */
  }
  startSystem() {
    /* ... */
  }
  stopSystem() {
    /* ... */
  }
  updateSystemStatus(isRunning) {
    /* ... */
  }
  handleAttendanceUpdate(data) {
    /* ... */
  }
  addRecentEvent(data) {
    /* ... */
  }
  async handleEnrollSubmit(event) {
    /* ... */
  }
  formatTime(timestamp) {
    /* ... */
  }
  showNotification(message, type = "success") {
    /* ... */
  }
}
