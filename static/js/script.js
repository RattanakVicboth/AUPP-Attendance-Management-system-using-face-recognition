const photoInput = document.getElementById("photo");
const submitBtn = document.querySelector("button[type='submit']");
const photoError = document.getElementById("photo-error");

if (photoInput) {
    photoInput.addEventListener("change", function () {
        if (photoInput.files.length === 0) {
            photoError.textContent = "Please upload your photo.";
            photoError.style.display = "block";
            submitBtn.disabled = true;
            return;
        }

        const formData = new FormData();
        formData.append("photo", photoInput.files[0]);

        fetch("/api/check_face", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.face_detected) {
                photoError.textContent = "";
                photoError.style.display = "none";
                submitBtn.disabled = false;
            } else {
                photoError.textContent = "No face detected! Please upload a clear face photo.";
                photoError.style.display = "block";
                submitBtn.disabled = true;
                photoInput.value = ""; 
            }
        })
        .catch(error => {
            console.error("Face check error:", error);
            photoError.textContent = "Network error. Please try again.";
            photoError.style.display = "block";
            submitBtn.disabled = true;
        });
    });
}

    
    const form = document.getElementById("registration-form"); 
    if (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();  // ✋ prevent page from navigating

            console.log("Validation started...");

            // Clear previous error messages
            document.querySelectorAll(".error-message").forEach(msg => {
                msg.textContent = "";
                msg.style.display = "none";
            });

            if (validateForm()) {
                console.log("Form validation passed.");

                const formData = new FormData(form);

                fetch(form.action, {
                    method: "POST",
                    body: formData,
                })
                .then(response => {
                    if (!response.ok) {
                        // If backend validation fails
                        return response.json().then(errorData => {
                            console.error("Validation errors:", errorData.details);

                            if (errorData.details) {
                                // Show specific field errors
                                if (errorData.details.name) {
                                    const nameError = document.getElementById("name-error");
                                    nameError.textContent = errorData.details.name;
                                    nameError.style.display = "block";
                                }
                                if (errorData.details.email) {
                                    const emailError = document.getElementById("email-error");
                                    emailError.textContent = errorData.details.email;
                                    emailError.style.display = "block";
                                }
                                if (errorData.details.student_id) {
                                    const idError = document.getElementById("id-error");
                                    idError.textContent = errorData.details.student_id;
                                    idError.style.display = "block";
                                }
                                if (errorData.details.phone) {
                                    const phoneError = document.getElementById("phone-error");
                                    phoneError.textContent = errorData.details.phone;
                                    phoneError.style.display = "block";
                                }
                                if (errorData.details.photo) {
                                    const photoError = document.getElementById("photo-error");
                                    photoError.textContent = errorData.details.photo;
                                    photoError.style.display = "block";
                                }
                            }

                            throw new Error("Validation failed");
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("Registration successful!");
                    alert("✅ Registration successful!");
                    form.reset();
                })
                .catch(error => {
                    console.error("Error during registration:", error);
                });
            } else {
                console.log("Form validation failed (client-side)");
            }
        });
    }


    // Navigation active state (keeping your existing code)
    const links = document.querySelectorAll("nav a");
    links.forEach(link => {
        link.addEventListener("click", function (event) {
            links.forEach(l => l.classList.remove("active"));
            event.target.classList.add("active");
        });
    });


// Separate validation function that returns true/false
function validateForm() {
    let isValid = true;

    console.log("Running validations...");

    // Clear previous error messages
    document.querySelectorAll(".error-message").forEach(msg => {
        msg.textContent = "";
        msg.style.display = "none";
    });

    // Validate Name (Only alphabetic characters allowed)
    const name = document.getElementById("name").value;
    const namePattern = /^[a-zA-Z\s]+$/;  // Only allows alphabets and spaces
    const nameError = document.getElementById("name-error");

    if (!name.trim() || !namePattern.test(name)) {
        nameError.textContent = "Please enter a valid name containing only letters and spaces.";
        nameError.style.display = "block";
        isValid = false;
    }

    // Validate Email (AUPP email format)
    const email = document.getElementById("email").value;
    const emailPattern = /^[a-zA-Z0-9._%+-]+@aupp\.edu\.kh$/;  // AUPP email format
    const emailError = document.getElementById("email-error");

    if (!email || !emailPattern.test(email)) {
        emailError.textContent = "Please enter a valid AUPP email address.";
        emailError.style.display = "block";
        isValid = false;
    }

    // Validate Student ID – only digits, max 8 characters
    const idInput = document.getElementById("student_id");
    const idError = document.getElementById("id-error");
    const idPattern = /^[0-9]{1,8}$/;

    if (!idPattern.test(idInput.value)) {
        idError.textContent = "Please enter a valid student ID (up to 8 digits).";
        idError.style.display = "block";
        isValid = false;
    }

    // Validate Phone number (Cambodia format) - Only numbers allowed, prefix +855 fixed
    const phone = document.getElementById("phone").value;
    const phonePattern = /^[0-9]{8,9}$/; // Validates Cambodia phone numbers (8-9 digits)
    const phoneError = document.getElementById("phone-error");

    if (!phone || !phonePattern.test(phone)) {
        phoneError.textContent = "Please enter a valid Cambodian phone number (8-9 digits).";
        phoneError.style.display = "block";
        isValid = false;
    }

    // Validate Photo
    const photo = document.getElementById("photo");
    const photoError = document.getElementById("photo-error");

    if (!photo.files || photo.files.length === 0) {
        photoError.textContent = "Please submit your photo for facial recognition.";
        photoError.style.display = "block";
        isValid = false;
    }
    return isValid;
}

    // Admin login modal functionality
    function openAdminLogin() {
        const modal = document.getElementById('adminLoginModal');
        modal.style.display = 'flex'; // show modal
    }

    function closeAdminLogin() {
        const modal = document.getElementById('adminLoginModal');
        modal.style.display = 'none'; // hide modal
    
        // Clear inputs
        document.getElementById('adminUsername').value = '';
        document.getElementById('adminPassword').value = '';
        
        // Hide error message
        document.getElementById('loginError').style.display = 'none';
    }

// Admin Login verification
function checkAdminLogin() {
    const username = document.getElementById('adminUsername').value.trim();
    const password = document.getElementById('adminPassword').value.trim();

    fetch('/verify_admin', {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            console.log("✅ Admin login successful!");
            closeAdminLogin(); // Close the login modal

            // 🟢 Start the scanner by calling /start-scan
            fetch('/start-scan')
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Failed to start scanner");
                    }
                    console.log("✅ Scanner started successfully!");
                    // Optionally you can reload or navigate after starting the scanner
                    window.location.href = "/membership";
                })
                .catch(error => {
                    console.error("⚠️ Failed to start scanner:", error);
                    const loginError = document.getElementById("loginError");
                    loginError.textContent = "Scanner could not be started.";
                    loginError.style.display = "block";
                });
        } else {
            console.error("❌ Admin login failed!");
            const loginError = document.getElementById("loginError");
            loginError.textContent = "Invalid username or password.";
            loginError.style.display = "block";
        }
    })
    .catch(error => {
        console.error("⚠️ Network or server error during login:", error);
        const loginError = document.getElementById("loginError");
        loginError.textContent = "Network error. Please try again.";
        loginError.style.display = "block";
    });
}