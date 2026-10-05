import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UTME ATTACK FORCE AI</title>
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0d1117;
            color: white;
        }

        .header {
            background: #161b22;
            padding: 18px;
            text-align: center;
            font-size: 22px;
            font-weight: bold;
        }

        .subtitle {
            text-align: center;
            color: #8b949e;
            padding: 8px;
        }

        #chat {
            height: calc(100vh - 150px);
            overflow-y: auto;
            padding: 15px;
        }

        .message {
            margin: 10px 0;
            padding: 12px 15px;
            border-radius: 15px;
            max-width: 85%;
            line-height: 1.5;
        }

        .bot {
            background: #21262d;
            margin-right: auto;
        }

        .user {
            background: #238636;
            margin-left: auto;
        }

        .input-area {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            display: flex;
            padding: 10px;
            background: #161b22;
        }

        input {
            flex: 1;
            padding: 13px;
            border: none;
            border-radius: 10px;
            outline: none;
            font-size: 16px;
        }

        button {
            margin-left: 8px;
            padding: 13px 18px;
            border: none;
            border-radius: 10px;
            background: #238636;
            color: white;
            font-weight: bold;
        }
    </style>
</head>

<body>

<div class="header">🤖 UTME ATTACK FORCE AI</div>
<div class="subtitle">Your JAMB/UTME AI Assistant</div>

<div id="chat">
    <div class="message bot">
        👋 Hello! I am UTME ATTACK FORCE AI.<br>
        Ask me a UTME question and I will help you.
    </div>
</div>

<div class="input-area">
    <input id="message" placeholder="Ask your UTME question..." />
    <button onclick="sendMessage()">Send</button>
</div>

<script>
async function sendMessage() {
    const input = document.getElementById("message");
    const chat = document.getElementById("chat");

    const message = input.value.trim();

    if (!message) return;

    chat.innerHTML += `
        <div class="message user">${message}</div>
    `;

    input.value = "";

    chat.innerHTML += `
        <div class="message bot" id="typing">Thinking...</div>
    `;

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        document.getElementById("typing").remove();

        chat.innerHTML += `
            <div class="message bot">${data.reply}</div>
        `;

        chat.scrollTop = chat.scrollHeight;

    } catch (error) {
        document.getElementById("typing").innerText =
            "Sorry, something went wrong.";
    }
}

document.getElementById("message").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});
</script>

</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        if self.path == "/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            data = json.loads(body)
            message = data.get("message", "")

            reply = (
                "I received your question: " + message +
                "<br><br>🧠 AI response system is being connected."
            )

            response = json.dumps({
                "reply": reply
            })

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.encode())

    def log_message(self, format, *args):
        pass


port = int(os.environ.get("PORT", 10000))

server = HTTPServer(("0.0.0.0", port), Handler)

print("UTME ATTACK FORCE AI is running...")
server.serve_forever()
