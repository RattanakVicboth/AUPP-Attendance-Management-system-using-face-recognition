// static/js/upload.js
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("photo");
    input.addEventListener("change", async () => {
      const file = input.files[0];
      if (!file) return;
  
      const form = new FormData();
      form.append("photo", file);
      form.append("name", document.getElementById("name").value.trim());
      form.append("student_id", document.getElementById("student_id").value.trim());
      form.append("email", document.getElementById("email").value.trim());
      form.append("phone", document.getElementById("phone").value.trim());
      
      try {
        const resp = await fetch("/api/register", {
          method: "POST",
          body: form
        });
        const data = await resp.json();
        if (data.success) {
          alert(`✅ Photo saved as ${data.filename}`);
        } else {
          alert(`❌ Upload failed: ${data.error}`);
        }
      } catch (err) {
        console.error(err);
        alert("⚠️ Could not upload photo.");
      }
    });
  });
  