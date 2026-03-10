const API_BASE_URL = "http://localhost:8000/api/v1";

document.addEventListener("DOMContentLoaded", () => {
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const suggestionChips = document.querySelectorAll(".suggestion-chip");
    
    // Auto-resize textarea
    chatInput.addEventListener('input', function() {
        this.style.height = '44px';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Handle Enter key (Shift+Enter for new line)
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
});

async function sendMessage() {
    const inputEl = document.getElementById("chat-input");
    const message = inputEl.value.trim();
    
    if (!message) return;

    // Reset input
    inputEl.value = "";
    inputEl.style.height = '44px';

    // Append user message
    appendMessage(message, "user");

    try {
        // Show loading state (optional: you can add a typing indicator)
        
        const response = await fetch(`${API_BASE_URL}/chat/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Authorization will be needed here later
            },
            body: JSON.stringify({ message: message, app_context: 'web' })
        });

        if (!response.ok) throw new Error("Network response was not ok");
        
        const data = await response.json();
        appendMessage(data.message, "ai");
        
    } catch (error) {
        console.error("Error connecting to server:", error);
        appendMessage("Xin lỗi, tôi đang gặp sự cố kết nối tới máy chủ.", "system");
    }
}

function appendMessage(text, role) {
    const container = document.getElementById("messages-container");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;
    
    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = "bubble";
    
    // Simple formatting (convert newlines to br - in production use a markdown parser)
    bubbleDiv.innerHTML = `<p>${text.replace(/\\n/g, '<br>')}</p>`;
    
    msgDiv.appendChild(bubbleDiv);
    container.appendChild(msgDiv);
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}
