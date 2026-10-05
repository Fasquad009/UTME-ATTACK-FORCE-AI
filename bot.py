import os
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-6-luna")

SYSTEM_PROMPT = r'''
You are UTME ATTACK FORCE AI, a friendly JAMB/UTME study assistant.

Make every answer easy for a normal student to understand on a phone.

FORMAT RULES:
- Never use ### headings.
- Never show LaTeX or computer commands such as \\frac, \\sqrt, $$, \\text, or programming syntax.
- Never use raw asterisks. Use **bold** only for important words; the website renders this as real bold text.
- Number multiple questions 1., 2., 3. and keep each question with its options.
- Put the final choice on its own line as **Answer: C. [option]**.
- Use short paragraphs and blank lines.
- For a single question, give the answer first and then the explanation.

MATHS RULES:
- Write mathematics like a teacher, not like computer code.
- NEVER write \\frac{3}{4}. Write 3/4 for a simple fraction.
- NEVER write \\sqrt{25}. Write √25 = 5.
- Use normal symbols students understand: ×, ÷, +, −, =, √, ≤, ≥, ², ³.
- Show calculations one clear step per line.
- Explain what each step means in plain English.
- Do not use unexplained mathematical markup.
- If a fraction is important, explain it in ordinary words too.

PHOTO RULES:
- Carefully read the uploaded question and options.
- Solve what is actually visible in the photo.
- If the image is too blurry or part of the question is missing, say what is unclear instead of guessing.

VOICE RULES:
- Treat speech-to-text as a normal question and correct obvious transcription mistakes when the intended question is clear.
'''

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UTME ATTACK FORCE AI</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0b1220;color:#f8fafc;font-family:Arial,Helvetica,sans-serif}
header{padding:17px 14px;text-align:center;background:#111827;border-bottom:1px solid #263244}
header h1{margin:0;font-size:21px} header p{margin:6px 0 0;color:#aab4c3;font-size:13px}
#chat{height:calc(100vh - 158px);overflow-y:auto;padding:16px 11px 115px}
.msg{max-width:94%;margin:10px 0;padding:14px 15px;border-radius:18px;line-height:1.58;font-size:15px;word-wrap:break-word}
.user{margin-left:auto;background:#128c4a;color:white;border-bottom-right-radius:5px}
.ai{margin-right:auto;background:#1d2633;color:#f3f6fa;border-bottom-left-radius:5px}
.ai p{margin:0 0 12px}.ai p:last-child{margin-bottom:0}.ai strong{font-weight:800;color:#fff}
.qblock{margin:14px 0 0}.qnum{font-weight:800}.typing{opacity:.65;font-style:italic}
.photo-preview{max-width:220px;border-radius:12px;display:block;margin-top:8px}
.composer{position:fixed;bottom:0;left:0;right:0;background:#101722;border-top:1px solid #293548;padding:9px;display:flex;gap:7px;align-items:center}
#input{min-width:0;flex:1;border:0;border-radius:22px;padding:12px 14px;background:#252f3d;color:#fff;outline:none;font-size:15px}
button{height:44px;border:0;border-radius:22px;padding:0 14px;background:#16a34a;color:#fff;font-weight:700}
.iconbtn{width:44px;padding:0;background:#334155;font-size:19px} button:disabled{opacity:.55} #photoInput{display:none}
.fraction{display:inline-flex;flex-direction:column;vertical-align:middle;text-align:center;line-height:1.05;margin:0 3px}
.fraction .top{border-bottom:1px solid #fff;padding:0 4px}.fraction .bottom{padding:1px 4px 0}
</style>
</head>
<body>
<header><h1>UTME ATTACK FORCE AI</h1><p>Type, speak, or take a photo of your question</p></header>
<div id="chat"></div>
<div class="composer">
<input id="photoInput" type="file" accept="image/*" capture="environment">
<button class="iconbtn" id="camera" title="Take a photo">📷</button>
<button class="iconbtn" id="mic" title="Voice input">🎤</button>
<input id="input" placeholder="Ask your UTME question..." autocomplete="off">
<button id="send">Send</button>
</div>
<script>
const chat=document.getElementById('chat'),input=document.getElementById('input'),send=document.getElementById('send'),mic=document.getElementById('mic'),camera=document.getElementById('camera'),photoInput=document.getElementById('photoInput');
let selectedImageDataUrl=null;
function escapeHTML(s){return s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));}
function formatAI(raw){
 let s=escapeHTML((raw||'').replace(/\r/g,''));
 s=s.replace(/\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}/g,'<span class="fraction"><span class="top">$1</span><span class="bottom">$2</span></span>');
 s=s.replace(/\\sqrt\s*\{([^{}]+)\}/g,'√$1').replace(/\\times/g,'×').replace(/\\div/g,'÷').replace(/\\leq/g,'≤').replace(/\\geq/g,'≥').replace(/\\pm/g,'±').replace(/\\cdot/g,'·').replace(/\^\{2\}/g,'²').replace(/\^\{3\}/g,'³');
 s=s.replace(/\$\$/g,'').replace(/\$/g,'').replace(/\\text\s*\{([^{}]+)\}/g,'$1').replace(/\\left|\\right/g,'');
 s=s.replace(/^\s*#{1,6}\s*/gm,'').replace(/\*\*(.+?)\*\*/gs,'<strong>$1</strong>');
 const lines=s.split('\n');let out='',inQ=false;
 for(const line of lines){const t=line.trim();if(!t){if(inQ){out+='</div>';inQ=false;}continue;}
  const m=t.match(/^(\d+)\.\s+(.*)$/); if(m){if(inQ)out+='</div>';out+='<div class="qblock"><span class="qnum">'+m[1]+'.</span> '+m[2];inQ=true;continue;}
  if(inQ)out+='<br>'+line;else out+='<p>'+line+'</p>';
 }
 if(inQ)out+='</div>'; return out;
}
function addMessage(text,who,typing=false){const d=document.createElement('div');d.className='msg '+who+(typing?' typing':'');d.innerHTML=who==='ai'?formatAI(text):escapeHTML(text);chat.appendChild(d);chat.scrollTop=chat.scrollHeight;return d;}
function addPhotoPreview(url){const d=document.createElement('div');d.className='msg user';d.innerHTML="📷 Photo question<img class='photo-preview' src='"+url+"' alt='Question photo'>";chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}
function compressImage(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>{const img=new Image();img.onload=()=>{let w=img.width,h=img.height,max=1600;if(w>max||h>max){const k=Math.min(max/w,max/h);w=Math.round(w*k);h=Math.round(h*k);}const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').drawImage(img,0,0,w,h);resolve(c.toDataURL('image/jpeg',.78));};img.onerror=()=>reject(new Error('Could not read that image.'));img.src=r.result;};r.onerror=()=>reject(new Error('Could not read the photo.'));r.readAsDataURL(file);});}
camera.onclick=()=>photoInput.click();
photoInput.onchange=async()=>{const f=photoInput.files[0];if(!f)return;try{selectedImageDataUrl=await compressImage(f);addPhotoPreview(selectedImageDataUrl);input.placeholder='Add instructions or tap Send...';input.focus();}catch(e){alert(e.message);}photoInput.value='';};
async function ask(){const text=input.value.trim();if(!text&&!selectedImageDataUrl)return;const image=selectedImageDataUrl;if(text)addMessage(text,'user');input.value='';input.placeholder='Ask your UTME question...';const typing=addMessage('Thinking...','ai',true);send.disabled=mic.disabled=camera.disabled=true;try{const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text||'Solve the question in this photo.',image:image})});const data=await r.json();typing.remove();if(!r.ok)throw new Error(data.error||'Request failed.');addMessage(data.answer,'ai');selectedImageDataUrl=null;}catch(e){typing.remove();addMessage('Sorry, I could not solve that right now. '+e.message,'ai');}finally{send.disabled=mic.disabled=camera.disabled=false;input.focus();}}
send.onclick=ask;input.addEventListener('keydown',e=>{if(e.key==='Enter')ask();});
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SpeechRecognition){const rec=new SpeechRecognition();rec.lang='en-NG';rec.interimResults=false;rec.continuous=false;mic.onclick=()=>{try{rec.start();mic.textContent='🔴';}catch(e){}};rec.onresult=e=>{input.value=e.results[0][0].transcript;mic.textContent='🎤';};rec.onerror=()=>mic.textContent='🎤';rec.onend=()=>mic.textContent='🎤';}else{mic.onclick=()=>alert('Voice input is not supported by this browser. Try Chrome on Android.');}
</script>
</body></html>'''

def call_openai(message, image_data_url=None):
    if not OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY is missing in Render environment variables.')
    if image_data_url:
        user_input=[{'role':'user','content':[{'type':'input_text','text':message or 'Solve the question in this photo.'},{'type':'input_image','image_url':image_data_url,'detail':'high'}]}]
    else:
        user_input=message
    payload={'model':OPENAI_MODEL,'instructions':SYSTEM_PROMPT,'input':user_input}
    req=Request('https://api.openai.com/v1/responses',data=json.dumps(payload).encode('utf-8'),headers={'Content-Type':'application/json','Authorization':'Bearer '+OPENAI_API_KEY},method='POST')
    try:
        with urlopen(req,timeout=120) as response:data=json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        body=e.read().decode('utf-8',errors='replace');raise RuntimeError('OpenAI API error: '+body[:700])
    answer=data.get('output_text')
    if not answer:
        pieces=[]
        for item in data.get('output',[]):
            for content in item.get('content',[]):
                if content.get('type')=='output_text':pieces.append(content.get('text',''))
        answer='\n'.join(pieces).strip()
    if not answer:raise RuntimeError('The AI returned an empty answer.')
    return answer

class Handler(BaseHTTPRequestHandler):
    def send_json(self,obj,status=200):
        body=json.dumps(obj).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Access-Control-Allow-Origin','*');self.end_headers();self.wfile.write(body)
    def do_GET(self):
        if self.path=='/' or self.path.startswith('/?'):
            body=HTML.encode('utf-8');self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        else:self.send_error(404)
    def do_POST(self):
        if self.path!='/ask':self.send_error(404);return
        try:
            length=int(self.headers.get('Content-Length','0'));data=json.loads(self.rfile.read(length).decode('utf-8'));message=str(data.get('message','')).strip();image=data.get('image')
            if not message and not image:self.send_json({'error':'Please enter a question or send a photo.'},400);return
            if image and len(image)>8_000_000:self.send_json({'error':'That photo is too large. Please take a clearer, smaller photo.'},400);return
            self.send_json({'answer':call_openai(message,image)})
        except Exception as e:self.send_json({'error':str(e)},500)
    def log_message(self,format,*args):print(format % args)

port=int(os.environ.get('PORT','10000'));server=ThreadingHTTPServer(('0.0.0.0',port),Handler);print(f'UTME ATTACK FORCE AI running on port {port}');server.serve_forever()
