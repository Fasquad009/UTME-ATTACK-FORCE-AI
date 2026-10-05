import os
import base64
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI

app = Flask(__name__)

# ============================================================
# OPENAI
# ============================================================

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")


# ============================================================
# UTME ATTACK FORCE - EDUCATIONAL RULES
# ============================================================

SYSTEM_PROMPT = """
You are UTME ATTACK FORCE AI.

You are an educational AI assistant for Nigerian students.

YOUR PURPOSE:
- UTME/JAMB preparation
- School examinations
- Academic learning
- Educational questions
- Revision
- Explanations
- Step-by-step problem solving
- Study assistance

SUPPORTED SUBJECTS INCLUDE:
English Language
Mathematics
Physics
Chemistry
Biology
Economics
Government
Literature
Geography
Civic Education
Agricultural Science
Computer/ICT
and other legitimate academic subjects.

EDUCATION-ONLY RULE:
You are NOT a general-purpose entertainment chatbot.

If a request is unrelated to education, school, learning, examinations,
UTME/JAMB, or an academic subject, politely refuse and redirect the student
to an educational topic.

TRUE MODE RULE:
TRUE MODE means GENUINE VERIFIED PAST UTME QUESTIONS.

NEVER invent a question in TRUE MODE.
NEVER change an AI-generated question and call it a genuine JAMB question.
NEVER claim a question is from a particular JAMB year unless the application
has supplied verified source information for that question.

If a genuine question is not available in the verified database, say clearly:

"I don't currently have a verified genuine question for that request."

PRACTICE MODE RULE:
PRACTICE MODE creates NEW AI-GENERATED practice questions.

Every generated practice question must be treated as:
"AI-GENERATED PRACTICE QUESTION"

Never call an AI-generated question an authentic JAMB past question.

SOLUTIONS:
- Explain answers clearly.
- Use simple student-friendly language.
- Show working for Mathematics and Physics.
- Do not use confusing computer-style notation when normal mathematical
  formatting can be used.
- Clearly separate formulas, substitutions and final answers.
- If an image contains a question, carefully read the image before solving it.
- If the image is unclear, say which part cannot be read instead of guessing.

PAST QUESTIONS:
If a question comes from the verified database supplied by the application,
preserve its year, subject and source information.

IMPORTANT:
Accuracy is more important than pretending to know something.
"""


# ============================================================
# VERIFIED TRUE-MODE DATABASE
# ============================================================
#
# IMPORTANT:
# Do NOT put invented questions here.
#
# This list is intentionally empty until verified genuine questions
# are added. Later, we can load hundreds or thousands of verified
# questions from a JSON/database file without changing the main app.
#

PAST_QUESTIONS = []


# ============================================================
# SUBJECTS
# ============================================================

SUBJECTS = [
    "English Language",
    "Mathematics",
    "Physics",
    "Chemistry",
    "Biology",
    "Economics",
    "Government",
    "Literature",
    "Geography",
    "Civic Education",
    "Agricultural Science",
    "Computer/ICT"
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def education_check(message):
    """
    Basic first-line filter.

    The AI itself performs the final educational-scope decision,
    but this helps redirect obvious non-educational requests.
    """

    text = message.lower().strip()

    educational_words = [
        "utme", "jamb", "exam", "examination", "school",
        "student", "study", "lesson", "question", "solve",
        "mathematics", "math", "physics", "chemistry",
        "biology", "english", "government", "economics",
        "literature", "geography", "agriculture", "computer",
        "calculate", "equation", "formula", "revision",
        "homework", "assignment", "topic", "subject",
        "education", "academic", "science"
    ]

    if any(word in text for word in educational_words):
        return True

    # Keep the AI available for normal educational questions even
    # when the student doesn't use obvious keywords.
    return True


def get_true_questions(subject=None, year=None, topic=None, limit=10):
    """
    Retrieve ONLY questions that actually exist in the verified
    question database.
    """

    results = []

    for question in PAST_QUESTIONS:

        if subject:
            if question.get("subject", "").lower() != subject.lower():
                continue

        if year:
            if str(question.get("year", "")) != str(year):
                continue

        if topic:
            if topic.lower() not in question.get("topic", "").lower():
                continue

        results.append(question)

        if len(results) >= limit:
            break

    return results


def format_true_questions(questions):
    """
    Converts verified database questions into a safe prompt.
    """

    output = []

    for q in questions:

        item = f"""
YEAR: {q.get("year", "Unknown")}
SUBJECT: {q.get("subject", "Unknown")}
TOPIC: {q.get("topic", "Unknown")}
SOURCE: {q.get("source", "Verified database")}

QUESTION:
{q.get("question", "")}

OPTIONS:
A. {q.get("A", "")}
B. {q.get("B", "")}
C. {q.get("C", "")}
D. {q.get("D", "")}

CORRECT ANSWER:
{q.get("answer", "")}

EXPLANATION:
{q.get("explanation", "")}
"""

        output.append(item)

    return "\n\n----------------------------\n\n".join(output)


# ============================================================
# AI TEXT RESPONSE
# ============================================================

def ask_ai(user_message, mode="practice", subject="", topic=""):
    """

    Sends the student's request to the OpenAI Responses API.
    """

    if mode == "true":

        questions = get_true_questions(
            subject=subject,
            topic=topic,
            limit=10
        )

        if not questions:

            return (
                "TRUE MODE\n\n"
                "I don't currently have a verified genuine UTME "
                "question for that request.\n\n"
                "I will not invent a question and label it as a "
                "real JAMB/UTME past question.\n\n"
                "You can switch to PRACTICE MODE for an "
                "AI-generated UTME-style question."
            )

        database_text = format_true_questions(questions)

        prompt = f"""
The student selected TRUE MODE.

Use ONLY the verified questions below.

Do not create additional questions.
Do not modify them into different questions.
Do not claim anything outside the supplied database is genuine.

Student request:
{user_message}

Subject:
{subject}

Topic:
{topic}

VERIFIED QUESTIONS:
{database_text}

Present the verified questions clearly.
Give the answer and explanation when appropriate.
Keep the source/year information.
"""

    else:

        prompt = f"""
The student selected PRACTICE MODE.

Create an educational UTME-style practice response.

Subject:
{subject}

Topic:
{topic}

Student request:
{user_message}

IMPORTANT:
Any question you create is AI-GENERATED.
Do not describe it as a genuine JAMB past question.

Make the question challenging but appropriate for UTME preparation.
Give four options where a multiple-choice question is requested.
Provide the correct answer and a clear explanation.
"""

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=prompt
    )

    return response.output_text


# ============================================================
# IMAGE QUESTION SOLVING
# ============================================================

def solve_image(image_data, message="", mode="practice", subject=""):
    """
    Solves a question from a camera/photo upload.

    The image is sent to the model as an image input.
    """

    if not image_data:
        return "No image was received."

    if mode == "true":
        extra_rule = """
The student selected TRUE MODE.

Do not claim that the photographed question is a genuine JAMB
question unless the application has independently verified it.

You may solve the question shown in the image, but do not invent
a year/source.
"""
    else:
        extra_rule = """
The student selected PRACTICE MODE.
Solve the educational question shown in the image.
"""

    prompt = f"""
{extra_rule}

Subject:
{subject}

Student's message:
{message}

Read the question carefully from the photograph.

Then:
1. State what the question is asking.
2. Solve it step by step.
3. Give the final answer clearly.
4. If it is multiple choice, identify the correct option.
5. Do not guess if the image is too blurry to read.
"""

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": image_data
                    }
                ]
            }
        ]
    )

    return response.output_text


# ============================================================
# WEB PAGE
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>UTME Attack Force AI</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f3f4f6;
    color: #111827;
}

.header {
    background: #111827;
    color: white;
    text-align: center;
    padding: 18px 12px;
}

.header h1 {
    margin: 0;
    font-size: 24px;
}

.header p {
    margin: 7px 0 0;
    font-size: 14px;
    opacity: 0.9;
}

.controls {
    background: white;
    padding: 12px;
    display: grid;
    gap: 9px;
    border-bottom: 1px solid #ddd;
}

select,
input {
    width: 100%;
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 9px;
    font-size: 15px;
}

.mode-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}

.mode-button {
    padding: 12px;
    border: none;
    border-radius: 9px;
    font-weight: bold;
    cursor: pointer;
}

.true-mode {
    background: #1d4ed8;
    color: white;
}

.practice-mode {
    background: #059669;
    color: white;
}

.active {
    outline: 3px solid #f59e0b;
}

#chat {
    padding: 15px;
    padding-bottom: 180px;
    max-width: 900px;
    margin: auto;
}

.message {
    padding: 13px 15px;
    margin: 10px 0;
    border-radius: 13px;
    line-height: 1.55;
    white-space: pre-wrap;
}

.ai {
    background: white;
    border: 1px solid #ddd;
}

.user {
    background: #dbeafe;
    margin-left: 12%;
}

.composer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-top: 1px solid #ddd;
    padding: 10px;
}

.composer-row {
    display: grid;
    grid-template-columns: 1fr auto auto auto;
    gap: 7px;
}

.action {
    border: none;
    border-radius: 9px;
    padding: 12px;
    background: #111827;
    color: white;
    font-weight: bold;
}

.send {
    background: #2563eb;
}

input[type=file] {
    display: none;
}

.status {
    text-align: center;
    font-size: 12px;
    color: #666;
    padding: 5px;
}

</style>

</head>

<body>

<div class="header">

<h1>UTME ATTACK FORCE AI</h1>

<p>UTME • JAMB • EXAMINATION • EDUCATION</p>

</div>


<div class="controls">

<div class="mode-buttons">

<button
id="trueButton"
class="mode-button true-mode"
onclick="setMode('true')">

🎯 TRUE MODE
</button>

<button
id="practiceButton"
class="mode-button practice-mode active"
onclick="setMode('practice')">

🤖 PRACTICE MODE
</button>

</div>


<select id="subject">

<option value="">Choose Subject</option>

<option>English Language</option>
<option>Mathematics</option>
<option>Physics</option>
<option>Chemistry</option>
<option>Biology</option>
<option>Economics</option>
<option>Government</option>
<option>Literature</option>
<option>Geography</option>
<option>Civic Education</option>
<option>Agricultural Science</option>
<option>Computer/ICT</option>

</select>


<input
id="topic"
placeholder="Optional topic e.g. Mechanics, Algebra, Organic Chemistry"
>

</div>


<div id="chat">

<div class="message ai">

Welcome to UTME Attack Force AI.

Choose TRUE MODE for verified genuine past questions,
or PRACTICE MODE for AI-generated UTME-style questions.

I focus on education and examination preparation.

</div>

</div>


<div class="composer">

<div class="status" id="status">
PRACTICE MODE
</div>

<div class="composer-row">

<input
id="message"
placeholder="Ask an educational question..."
onkeydown="if(event.key === 'Enter') sendMessage()"
>

<button
class="action"
onclick="startVoice()"
title="Voice input">

🎤

</button>


<label class="action" title="Take or upload a question photo">

📷

<input
id="photo"
type="file"
accept="image/*"
capture="environment"
onchange="sendPhoto()"
>

</label>


<button
class="action send"
onclick="sendMessage()">

➤

</button>

</div>

</div>


<script>

let mode = "practice";


function setMode(newMode) {

    mode = newMode;

    const trueButton =
        document.getElementById("trueButton");

    const practiceButton =
        document.getElementById("practiceButton");

    const status =
        document.getElementById("status");

    trueButton.classList.remove("active");
    practiceButton.classList.remove("active");

    if (mode === "true") {

        trueButton.classList.add("active");

        status.textContent =
            "🎯 TRUE MODE — verified questions only";

    } else {

        practiceButton.classList.add("active");

        status.textContent =
            "🤖 PRACTICE MODE — AI-generated questions";

    }
}


function addMessage(text, type) {

    const chat =
        document.getElementById("chat");

    const message =
        document.createElement("div");

    message.className =
        "message " + type;

    message.textContent = text;

    chat.appendChild(message);

    chat.scrollTop = chat.scrollHeight;

    return message;
}


async function sendMessage() {

    const input =
        document.getElementById("message");

    const message =
        input.value.trim();

    if (!message) return;

    const subject =
        document.getElementById("subject").value;

    const topic =
        document.getElementById("topic").value;

    addMessage(message, "user");

    input.value = "";

    const loading =
        addMessage("Thinking...", "ai");

    try {

        const response =
            await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    message: message,
                    mode: mode,
                    subject: subject,
                    topic: topic

                })

            });


        const data =
            await response.json();

        loading.remove();

        addMessage(
            data.reply ||
            "Sorry, I could not answer that.",
            "ai"
        );

    } catch (error) {

        loading.textContent =
            "Connection error. Please try again.";

    }

}


async function sendPhoto() {

    const fileInput =
        document.getElementById("photo");

    const file =
        fileInput.files[0];

    if (!file) return;

    const subject =
        document.getElementById("subject").value;

    const topic =
        document.getElementById("topic").value;

    addMessage(
        "📷 Question photo uploaded.",
        "user"
    );

    const loading =
        addMessage(
            "Reading and solving the question...",
            "ai"
        );


    const reader =
        new FileReader();


    reader.onload =
        async function() {

            try {

                const response =
                    await fetch("/image", {

                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            image:
                                reader.result,

                            mode:
                                mode,

                            subject:
                                subject,

                            topic:
                                topic

                        })

                    });


                const data =
                    await response.json();

                loading.remove();

                addMessage(
                    data.reply ||
                    "I could not read that image.",
                    "ai"
                );

            } catch (error) {

                loading.textContent =
                    "There was a problem processing the photo.";

            }

        };


    reader.readAsDataURL(file);

}


function startVoice() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!SpeechRecognition) {

        alert(
            "Voice input is not supported by this browser. " +
            "Try Chrome on Android."
        );

        return;
    }


    const recognition =
        new SpeechRecognition();

    recognition.lang = "en-NG";

    recognition.interimResults = false;

    recognition.maxAlternatives = 1;


    recognition.onstart =
        function() {

            document.getElementById("status")
                .textContent =
                "🎤 Listening...";

        };


    recognition.onresult =
        function(event) {

            const text =
                event.results[0][0].transcript;

            document.getElementById("message")
                .value = text;

            document.getElementById("status")
                .textContent =
                mode === "true"
                ? "🎯 TRUE MODE"
                : "🤖 PRACTICE MODE";

        };


    recognition.onerror =
        function() {

            document.getElementById("status")
                .textContent =
                "Voice input failed. Try again.";

        };


    recognition.start();

}

</script>

</body>

</html>
"""


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template_string(HTML)


# ============================================================
# TEXT CHAT
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()

    mode = data.get("mode", "practice")

    subject = data.get("subject", "")

    topic = data.get("topic", "")


    if not message:

        return jsonify({
            "reply":
                "Please enter an educational question."
        })


    try:

        answer = ask_ai(
            message,
            mode=mode,
            subject=subject,
            topic=topic
        )

        return jsonify({
            "reply": answer
        })


    except Exception as error:

        print("OPENAI ERROR:", error)

        return jsonify({
            "reply":
                "Sorry, the AI could not process your question right now."
        }), 500


# ============================================================
# IMAGE / CAMERA QUESTIONS
# ============================================================

@app.route("/image", methods=["POST"])
def image_question():

    data = request.get_json(silent=True) or {}

    image = data.get("image")

    mode = data.get("mode", "practice")

    subject = data.get("subject", "")


    if not image:

        return jsonify({
            "reply": "No question image was received."
        }), 400


    try:

        answer = solve_image(
            image_data=image,
            message="Solve the question in this image.",
            mode=mode,
            subject=subject
        )

        return jsonify({
            "reply": answer
        })


    except Exception as error:

        print("IMAGE ERROR:", error)

        return jsonify({
            "reply":
                "Sorry, I could not process that question image."
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "app": "UTME Attack Force AI"
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
)
