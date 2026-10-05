import os
import json
import re
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna")

SYSTEM_PROMPT = """
You are UTME ATTACK FORCE AI, a clean and helpful JAMB/UTME study assistant.

IMPORTANT RESPONSE RULES:
1. Write in a clear, natural and well-organized way.
2. Never put ### or other heading symbols in the visible answer.
3. You may use **bold** for important answers. The website will render the bold correctly.
4. Never use asterisks for anything except **bold**.
5. For multiple questions, ALWAYS number them 1., 2., 3., etc.
6. Keep each question and its options together.
7. Put the final answer clearly on its own line as **Answer: X. [correct option]**.
8. Give a short, useful explanation after each answer when appropriate.
9. Separate different questions with a blank line.
10. Do not add unnecessary introductions such as "Sure, I can help..." when the user asks a direct question.
11. For a normal single question, give the answer first, then a concise explanation.
12. Make the response suitable for a student preparing for UTME.
"""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UTME ATTACK FORCE AI</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#f1f5f9;font-family:Arial,sans-serif}
header{padding:18px 16px;text-align:center;background:#151b23;border-bottom:1px solid #293241}
header h1{margin:0;font-size:22px}
header p{margin:6px 0 0;color:#9ca3af;font-size:13px}
#chat{height:calc(100vh - 145px);overflow-y:auto;padding:18px 12px 100px}
.msg{max-width:92%;margin:10px 0;padding:14px 16px;border-radius:18px;line-height:1.55;white-space:normal;word-wrap:break-word}
.user{margin-left:auto;background:#159447;color:white;border-bottom-right-radius:5px}
.ai{margin-right:auto;background:#20262e;color:#f5f5f5;border-bottom-left-radius:5px}
.ai p{margin:0 0 12px}
.ai p:last-child{margin-bottom:0}
.ai strong{font-weight:800}
.ai .q{margin-top:12px}
.composer{position:fixed;bottom:0;left:0;right:0;background:#11161d;border-top:1px solid #293241;padding:10px;display:flex;gap:8px}
#input{flex:1;border:0;border-radius:22px;padding:13px 15px;background:#252b33;color:white;outline:none;font-size:15px}
button{border:0;border-radius:22px;padding:0 16px;background:#18a34a;color:white;font-weight:bold}
#mic{background:#374151;font-size:18px}
button:disabled{opacity:.55}
.typing{opacity:.65;font-style:italic}
</style>
</head>
<body>
<header>
<h1>UTME ATTACK FORCE AI</h1>
<p>Ask your UTME questions</p>
</header>

<div id="chat"></div>

<div class="composer">
<input id="input" placeholder="Ask your UTME question..." autocomplete="off">
<button id="mic" title="Voice input">🎤</button>
<button id="send">Send</button>
</div>

<script>
const chat = document.getElementById("chat");
const input = document.getElementById("input");
const send = document.getElementById("send");
const mic = document.getElementById("mic");

function addMessage(text, who, isTyping=false){
  const div=document.createElement("div");
  div.className="msg "+who+(isTyping?" typing":"");
  div.innerHTML = who==="ai" ? formatAI(text) : escapeHTML(text);
  chat.appendChild(div);
  chat.scrollTop=chat.scrollHeight;
  return div;
}

function escapeHTML(s){
  return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[c]));
}

function formatAI(raw){
  let s=escapeHTML(raw.replace(/\r/g,""));

  // Render Markdown bold, but do NOT show the ** characters.
  s=s.replace(/\*\*(.+?)\*\*/gs,"<strong>$1</strong>");

  // Remove heading markers if the model ever sends them.
  s=s.replace(/^\s*#{1,6}\s*/gm,"");

  // Turn numbered question starts into separated blocks.
  s=s.replace(/(^|\n)(\d+)\.\s+/g,'$1<div class="q"><strong>$2.</strong> ');

  // Close question blocks before the next numbered item.
  s=s.replace(/<\/div>\s*(?=<div class="q">)/g,"</div>");

  // Paragraphs from blank lines.
  const parts=s.split(/\n\s*\n/);
  s=parts.map(p=>{
    if(p.trim().startsWith('<div class="q">')){
      return p + (p.endsWith("</div>") ? "" : "</div>");
    }
    return "<p>"+p.replace(/\n/g,"<br>")+"</p>";
  }).join("");

  return s;
}

async function ask(){
  const text=input.value.trim();
  if(!text) return;

  input.value="";
  addMessage(text,"user");
  const typing=addMessage("Thinking...","ai",true);
  send.disabled=true;

  try{
    const r=await fetch("/ask",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message:text})
    });
    const data=await r.json();
    typing.remove();
    if(!r.ok) throw new Error(data.error || "Request failed");
    addMessage(data.answer,"ai");
  }catch(e){
    typing.remove();
    addMessage("Sorry, I could not get an answer right now. "+e.message,"ai");
  }finally{
    send.disabled=false;
    input.focus();
  }
}

send.onclick=ask;
input.addEventListener("keydown",e=>{if(e.key==="Enter")ask();});

// Voice input: uses the phone/browser speech-recognition feature.
// This avoids sending an audio file to the server.
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if(SpeechRecognition){
  const rec=new SpeechRecognition();
  rec.lang="en-NG";
  rec.interimResults=false;
  rec.continuous=false;

  mic.onclick=()=>{
    try{
      rec.start();
      mic.textContent="🔴";
    }catch(e){}
  };

  rec.onresult=e=>{
    input.value=e.results[0][0].transcript;
    mic.textContent="🎤";
  };
  rec.onerror=()=>mic.textContent="🎤";
  rec.onend=()=>mic.textContent="🎤";
}else{
  mic.onclick=()=>{
    alert("Voice input is not supported by this browser. Try Chrome on Android.");
  };
}
</script>
</body>
</html>
"""

def call_openai(message):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing in Render environment variables.")

    payload = {
        "model": OPENAI_MODEL,
        "instructions": SYSTEM_PROMPT,
        "input": message,
    }

    req = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + OPENAI_API_KEY,
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError("OpenAI API error: " + body[:500])

    answer = data.get("output_text")
    if not answer:
        # Fallback for unusual response shapes.
        pieces = []
        for item in data.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    pieces.append(content.get("text", ""))
        answer = "\n".join(pieces).strip()

    if not answer:
        raise RuntimeError("The AI returned an empty answer.")

    return answer

class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, status=200):
        body=json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            body=HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/ask":
            self.send_error(404)
            return

        try:
            length=int(self.headers.get("Content-Length","0"))
            data=json.loads(self.rfile.read(length).decode("utf-8"))
            message=str(data.get("message","")).strip()

            if not message:
                self.send_json({"error":"Please enter a question."},400)
                return

            answer=call_openai(message)
            self.send_json({"answer":answer})
        except Exception as e:
            self.send_json({"error":str(e)},500)

    def log_message(self, format, *args):
        print(format % args)

port=int(os.environ.get("PORT","10000"))
server=ThreadingHTTPServer(("0.0.0.0",port),Handler)
print(f"UTME AI running on port {port}")
server.serve_forever()
