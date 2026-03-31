let currentApp = "Unknown";
const API_BASE_URL = "http://localhost:8000/api/v1";

Office.onReady((info) => {
    if (info.host === Office.HostType.Word) {
        currentApp = "word";
    } else if (info.host === Office.HostType.Excel) {
        currentApp = "excel";
    } else if (info.host === Office.HostType.PowerPoint) {
        currentApp = "powerpoint";
    }

    document.getElementById("context-info").innerText = `Đang làm việc trên ${currentApp}`;
    document.getElementById("send-btn").onclick = sendToAI;
    document.getElementById("action-btn").onclick = executeAutomation;

    const token = localStorage.getItem("access_token");
    if (!token) {
        appendMessage("Vui lòng đăng nhập qua Web App trước khi sử dụng AI tích hợp.", 'system');
    }
});

async function sendToAI() {
    const input = document.getElementById("prompt-input").value;
    const token = localStorage.getItem("access_token");
    
    if (!input) return;
    if (!token) {
        appendMessage("Chưa đăng nhập! Vui lòng đăng nhập qua web.", 'error');
        return;
    }
    
    appendMessage(input, 'user');
    document.getElementById("prompt-input").value = "";

    try {
        const response = await fetch(`${API_BASE_URL}/chat/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ message: input, app_context: currentApp })
        });
        
        if (response.status === 401 || response.status === 403) {
            appendMessage("Phiên đăng nhập hết hạn.", 'error');
            return;
        }

        const data = await response.json();
        appendMessage(data.message, 'ai');
    } catch (e) {
        appendMessage("Lỗi kết nối tới server AI.", 'error');
    }
}

async function executeAutomation() {
    const requestText = document.getElementById("prompt-input").value;
    const token = localStorage.getItem("access_token");
    
    if (!requestText) {
        alert("Vui lòng nhập yêu cầu tự động hoá.");
        return;
    }
    if (!token) {
        alert("Chưa đăng nhập!");
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/office/generate-macro`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ action_type: 'generate', content: requestText, app: currentApp })
        });
        
        if (response.status === 401 || response.status === 403) {
            alert("Phiên đăng nhập hết hạn.");
            return;
        }
        
        const data = await response.json();
        alert("Hệ thống đề xuất:\n" + data.explanation + "\n\nMã lệnh: " + data.macro_script);
    } catch (e) {
        console.error(e);
        alert("Lỗi kết nối AI.");
    }
}

function appendMessage(text, role) {
    const chatHist = document.getElementById("chat-history");
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.innerText = text;
    chatHist.appendChild(div);
    chatHist.scrollTop = chatHist.scrollHeight;
}
