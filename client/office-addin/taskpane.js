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
});

async function sendToAI() {
    const input = document.getElementById("prompt-input").value;
    if (!input) return;
    
    appendMessage(input, 'user');
    document.getElementById("prompt-input").value = "";

    try {
        const response = await fetch(`${API_BASE_URL}/chat/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Authorization: 'Bearer {token}' - will be added when auth UI is ready
            },
            body: JSON.stringify({ message: input, app_context: currentApp })
        });
        
        const data = await response.json();
        appendMessage(data.message, 'ai');
    } catch (e) {
        appendMessage("Lỗi kết nối tới server AI.", 'error');
    }
}

async function executeAutomation() {
    // Generate macro via API and run it
    const requestText = document.getElementById("prompt-input").value;
    if (!requestText) {
        alert("Vui lòng nhập yêu cầu tự động hoá.");
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/office/generate-macro`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action_type: 'generate', content: requestText, app: currentApp })
        });
        const data = await response.json();
        alert("Hệ thống đề xuất:\n" + data.explanation + "\n\nMã lệnh: " + data.macro_script);
        // Note: For actual Office.js execution, you'll need eval() or specific Word.run/Excel.run logic here
    } catch (e) {
        console.error(e);
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
