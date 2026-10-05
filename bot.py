import os
import json
import html
import urllib.request
import urllib.error
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
            background: #0b0f15;
            color: white;
        }

        header {
            background: #171c23;
            padding: 25px 15px;
            text-align: center;
        }

        h1 {
            margin: 0;
            font-size: 32px;
        }

        .subtitle {
            text-align: center;
            color: #9da4b0;
            font-size: 24px;
            margin: 15px 0 25px;
        }

        #chat {
            min-height: calc(100vh - 230px);
            padding: 10px 28px 120px;
        }

        .message {
            max-width: 82%;
            padding: 18px 28px;
            margin: 14px 0;
            border-radius: 25px;
            font-size: 20px;
            line-height: 1.5;
            word-wrap: break-word;
        }

        .bot {
            background: #22272e;
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
            gap: 14px;
            padding: 18px 20px;
            background: #171c23;
        }

        #message {
            flex: 1;
            min-width: 0;
            padding: 18px 24px;
            border: none;
            border-radius: 18px;
            font-size: 20px;
            outline: none;
        }

        button {
            border: none;
            border-radius: 18px;
            padding: 0 30px;
            background: #238636;
            color: white;
            font-size: 20px;
            font-weight: bold;
        }

        button:disabled {
            opacity: 0.6;
        }

        @media (max-width: 600px) {
            h1 {
                font-size: 29px;
            }

            .subtitle {
                font-size: 21px;
            }

            #chat {
                padding-left: 28px;
                padding-right: 28px;
            }

            .message {
                font-size: 19px;
                max-width: 90%;
            }

            .input-area {
                padding: 14px 20px;
            }

            #message {
                font-size: 18px;
                padding: 16px;
            }

            button {
                padding: 0 22px;
                font-size: 18px;
            }
        }
    </style>
</head>

<body>

<header>
    <h1>🧠 UTME ATTACK FORCE AI</h1>
</header>

<div class="subtitle">
    Your JAMB/UTME AI Assistant
</div>

<div id="chat">
    <div class="message bot">
        🧠 Hello! I am UTME ATTACK FORCE AI.<br><br>
        Ask me a UTME question and I will help you.
    </div>
</div>

<div class="input-area">
    <input
        id="message"
        type="text"
        placeholder="Ask your UTME question..."
        autocomplete="off"
    >

    <button id="send" onclick="sendMessage()">
        Send
    </button>
</div>

<script>
async function sendMessage() {
    const input = document.getElementById("message");
    const button = document.getElementById("send");
    const chat = document.getElementById("chat");

    const message = input.value.trim();

    if (!message) {
        return;
    }

    const userMessage = document.createElement("div");
    userMessage.className = "message user";
    userMessage.textContent = message;
    chat.appendChild(userMessage);

    input.value = "";
    button.disabled = true;
    button.textContent = "Thinking...";

    chat.scrollTop = chat.scrollHeight;
    window.scrollTo(0, document.body.scrollHeight);

    const loading = document.createElement("div");
    loading.className = "message bot";
    loading.textContent = "🧠 Thinking...";
    chat.appendChild(loading);

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

        loading.remove();

        const botMessage = document.createElement("div");
        botMessage.className = "message bot";

        if (data.reply) {
            botMessage.textContent = data.reply;
        } else {
            botMessage.textContent =
                "Sorry, I could not get an AI response.";
        }

        chat.appendChild(botMessage);

    } catch (error) {
        loading.remove();

        const errorMessage = document.createElement("div");
        errorMessage.className = "message bot";
        errorMessage.textContent =
            "Sorry, there was a connection problem. Please try again.";

        chat.appendChild(errorMessage);
    }

    button.disabled = false;
    button.textContent = "Send";

    window.scrollTo(0, document.body.scrollHeight);
}

document.getElementById("message").addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});
</script>

</body>
</html>
"""


def ask_openai(message):
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        return "The AI API key has not been connected yet."

    url = "https://api.openai.com/v1/responses"

    request_data = {
        "model": "gpt-6-luna",
        "instructions": (
            "You are UTME ATTACK FORCE AI, a helpful JAMB/UTME study assistant. "
            "Answer UTME questions clearly and accurately. "
            "For mathematics and science questions, show the important steps. "
            "For multiple-choice questions, identify the correct option and explain why. "
            "Keep answers understandable for Nigerian secondary-school students."
        ),
        "input": message
    }

    data = json.dumps(request_data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        if result.get("output_text"):
            return result["output_text"]

        for item in result.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")

        return "I received the request, but I could not generate an answer."

    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="ignore")

        print("OpenAI HTTP error:", error.code, error_body)

        if error.code == 401:
            return "The AI API key is invalid or not connected correctly."

        return "The AI service returned an error. Please try again."

    except Exception as error:
        print("OpenAI connection error:", error)
        return "I could not connect to the AI service. Please try again."


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):

        if self.path != "/chat":
            self.send_response(404)
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            data = json.loads(body)
            message = data.get("message", "").strip()

            if not message:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()

                self.wfile.write(
                    json.dumps({
                        "reply": "Please enter a question."
                    }).encode("utf-8")
                )
                return

            reply = ask_openai(message)

            response = json.dumps({
                "reply": reply
            })

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.end_headers()

            self.wfile.write(response.encode("utf-8"))

        except Exception as error:
            print("Server error:", error)

            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(
                json.dumps({
                    "reply": "Something went wrong on the server."
                }).encode("utf-8")
            )

    def log_message(self, format, *args):
        pass


port = int(os.environ.get("PORT", 10000))

server = HTTPServer(("0.0.0.0", port), Handler)

print("UTME ATTACK FORCE AI is running on port", port)

server.serve_forever()
