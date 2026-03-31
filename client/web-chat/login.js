const API_BASE_URL = "http://localhost:8000/api/v1";

document.addEventListener("DOMContentLoaded", () => {
    // Check if already logged in
    const token = localStorage.getItem("access_token");
    if (token) {
        window.location.href = "index.html";
        return;
    }

    const form = document.getElementById("login-form");
    const errorMsg = document.getElementById("error-message");
    const submitBtn = document.getElementById("submit-btn");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        errorMsg.style.display = "none";
        submitBtn.disabled = true;
        submitBtn.textContent = "Đang xử lý...";

        try {
            const formData = new URLSearchParams();
            formData.append('username', email); // OAuth2 requires 'username'
            formData.append('password', password);

            const response = await fetch(`${API_BASE_URL}/auth/login/access-token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: formData
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || "Đăng nhập thất bại");
            }

            const data = await response.json();
            
            // Save tokens
            localStorage.setItem("access_token", data.access_token);
            if (data.refresh_token) {
                localStorage.setItem("refresh_token", data.refresh_token);
            }

            // Redirect to chat
            window.location.href = "index.html";
            
        } catch (error) {
            errorMsg.textContent = error.message;
            errorMsg.style.display = "block";
            submitBtn.disabled = false;
            submitBtn.textContent = "Đăng nhập";
        }
    });
});
