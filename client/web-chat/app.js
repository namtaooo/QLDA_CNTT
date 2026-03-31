const API_BASE_URL = "http://localhost:8000/api/v1";

document.addEventListener("DOMContentLoaded", async () => {
    // 1. Auth Check
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "login.html";
        return;
    }

    // 2. Fetch User Profile
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                localStorage.removeItem("access_token");
                window.location.href = "login.html";
                return;
            }
            throw new Error("Failed to load profile");
        }
        const user = await response.json();
        document.getElementById("user-name").textContent = user.full_name || user.email;
        document.getElementById("user-role").textContent = user.role || "Nhân viên";
        document.getElementById("user-avatar").textContent = (user.full_name || "U")[0].toUpperCase();
    } catch (error) {
        console.error("Profile load err:", error);
    }

    // 3. Setup UI events
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const suggestionChips = document.querySelectorAll(".suggestion-chip");
    const logoutBtn = document.getElementById("logout-btn");
    
    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = '44px';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Handle Enter key
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener("click", sendMessage);

    // Handle suggestion chips
    suggestionChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const text = chip.innerText.replace('💡 ', '');
            chatInput.value = text;
            sendMessage();
        });
    });

    // Logout
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "login.html";
    });
});

async function sendMessage() {
    const inputEl = document.getElementById("chat-input");
    const message = inputEl.value.trim();
    const token = localStorage.getItem("access_token");
    
    if (!message) return;

    // Reset input
    inputEl.value = "";
    inputEl.style.height = '44px';

    // Append user message
    appendMessage(message, "user");

    try {
        const response = await fetch(`${API_BASE_URL}/chat/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ message: message, app_context: 'web' })
        });

        if (response.status === 401 || response.status === 403) {
            alert("Phiên đăng nhập hết hạn, vui lòng đăng nhập lại.");
            localStorage.removeItem("access_token");
            window.location.href = "login.html";
            return;
        }

        if (!response.ok) throw new Error("Network response was not ok");
        
        const data = await response.json();
        
        // Render Markdown if marked library available, else simple break lines
        let htmlContent = data.message.replace(/\\n/g, '<br>');
        if (typeof marked !== 'undefined') {
            htmlContent = marked.parse(data.message);
        }
        
        appendMessage(htmlContent, "ai", true);
        
    } catch (error) {
        console.error("Error connecting to server:", error);
        appendMessage("Xin lỗi, tôi đang gặp sự cố kết nối tới máy chủ.", "system");
    }
}

function appendMessage(text, role, isHTML = false) {
    const container = document.getElementById("messages-container");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;
    
    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = "bubble";
    
    if (isHTML) {
        bubbleDiv.innerHTML = text;
    } else {
        bubbleDiv.innerHTML = `<p>${text.replace(/\\n/g, '<br>')}</p>`;
    }
    
    msgDiv.appendChild(bubbleDiv);
    container.appendChild(msgDiv);
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}
