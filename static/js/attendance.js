// static/js/attendance.js

function trackAttendance() {
    fetch("/start-scan")
      .then(r => r.text())
      .then(msg => alert(msg))
      .catch(err => {
        console.error(err);
        alert("⚠️ Failed to launch attendance scanner.");
      });
  }
  