import os
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI

app = Flask(__name__)

# ============================================================
# OPENAI SETTINGS
# ============================================================

API_KEY = os.environ.get("OPENAI_API_KEY")

MODEL = os.environ.get(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)

client = OpenAI(api_key=API_KEY) if API_KEY else None


# ============================================================
# MAIN AI INSTRUCTIONS
# ============================================================

SYSTEM_PROMPT = """
You are UTME ATTACK FORCE AI.

You are an educational AI assistant designed for Nigerian
students preparing for UTME/JAMB and school examinations.

MAIN PURPOSE:
- UTME preparation
- JAMB preparation
- School examinations
- Academic learning
- Revision
- Topic explanations
- Practice questions
- Step-by-step solutions
- Study assistance

SUPPORTED SUBJECTS:
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
and other legitimate school subjects.

============================================================
EDUCATION FOCUS
============================================================

Stay focused on education, examinations, school subjects,
learning and academic assistance.

If a request is clearly unrelated to education, politely
redirect the student to an educational topic.

============================================================
READ MODE
============================================================

READ MODE is for learning a topic.

Teach the selected topic like an excellent secondary-school
teacher.

Use this structure when appropriate:

1. Topic introduction
2. Simple definition
3. Main ideas
4. Important terms
5. Detailed explanation
6. Important formulas
7. Worked examples
8. UTME examination points
9. Common mistakes
10. Quick revision summary

Use simple language.

Do not make the notes unnecessarily complicated.

For Mathematics and Physics, write mathematics clearly.

Example:

Speed = Distance ÷ Time

Do NOT use ugly computer notation such as:

frac{distance}{time}

Explain what every symbol means.

============================================================
PRACTICE MODE
============================================================

PRACTICE MODE creates NEW AI-GENERATED UTME-STYLE practice
questions.

IMPORTANT:

Every question created in Practice Mode is AI-GENERATED.

NEVER call it:
- a genuine JAMB question
- an original JAMB question
- an authentic past question
- an official JAMB question
- a question from a particular JAMB year

If multiple-choice questions are requested:

A. option
B. option
C. option
D. option

Then give:

Correct Answer:
Explanation:

Make the questions appropriate for serious UTME preparation.

============================================================
PHOTO / CAMERA
============================================================

When the student sends a photograph:

1. Read the image carefully.
2. Identify the question.
3. Solve it.
4. Show the working clearly.
5. Explain the reasoning.
6. Give the final answer.
7. If it is multiple choice, identify the correct option.

Do not invent text that cannot be read.

If the photograph is genuinely unclear, tell the student
which part cannot be read.

============================================================
ACCURACY
============================================================

Accuracy is more important than pretending to know something.

Never invent claims about JAMB history or official questions.

============================================================
TEACHING STYLE
============================================================

Be clear, friendly and student-friendly.

Use headings, lists and spacing.

Make the student understand WHY the answer is correct,
not just the final answer.
"""


# ============================================================
# AI TEXT REQUEST
# ============================================================

def ask_ai(prompt):

    if not client:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured on Render."
        )

    response = client.responses.create(
        model=MODEL,
        instructions=SYSTEM_PROMPT,
        input=prompt
    )

    return response.output_text


# ============================================================
# READ MODE
# ============================================================

def read_topic(subject, topic):

    prompt = f"""
The student selected READ MODE.

SUBJECT:
{subject}

TOPIC:
{topic}

Teach this topic as high-quality study notes.

Use clear sections.

Include:

# {topic}

## Introduction

Give a simple introduction.

## What is {topic}?

Give a simple definition.

## Main ideas

Explain the important concepts one by one.

## Important terms

Explain important words the student must understand.

## Formulas

If the topic contains formulas:

Write formulas clearly.

Explain what each symbol means.

## Worked examples

Give useful examples and explain them step by step.

## UTME focus

List the important points a UTME student should remember.

## Common mistakes

Explain mistakes students commonly make.

## Quick revision

End with a short revision summary.

IMPORTANT:

These are teaching notes.

Do not claim that anything in the lesson is a genuine
JAMB past question.
"""

    return ask_ai(prompt)


# ============================================================
# PRACTICE MODE
# ============================================================

def practice_topic(subject, topic, number):

    prompt = f"""
The student selected PRACTICE MODE.

SUBJECT:
{subject}

TOPIC:
{topic}

NUMBER OF QUESTIONS:
{number}

Create {number} NEW AI-GENERATED UTME-style practice
questions.

IMPORTANT:

These are AI-GENERATED PRACTICE QUESTIONS.

Do not call them genuine JAMB questions.

Do not attach a JAMB year to them.

For every multiple-choice question use:

Question 1.

[Question]

A. ...
B. ...
C. ...
D. ...

Correct Answer:
...

Explanation:
...

Make the questions challenging enough for serious UTME
preparation.

Use the selected subject and topic.

For Mathematics and Physics, show calculations clearly.
"""

    return ask_ai(prompt)


# ============================================================
# IMAGE QUESTION SOLVER
# ============================================================

def solve_image(image_data, subject, mode):

    if not client:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured on Render."
        )

    if mode == "read":

        mode_instruction = """
The student is using READ MODE.

Use the photograph as learning material.

Explain the educational material shown in the image
clearly and teach the student what it means.
"""

    else:

        mode_instruction = """
The student is using PRACTICE MODE.

Solve the question shown in the photograph.

Do not claim that the photographed question is a genuine
JAMB past question.
"""

    prompt = f"""
{mode_instruction}

SUBJECT:
{subject}

Read the photograph carefully.

If there is a question:

1. State what the question is asking.
2. Show the solution step by step.
3. Explain the reasoning.
4. Give the final answer clearly.
5. If multiple choice, identify the correct option.

If the image contains notes or educational material,
explain those notes clearly.

If part of the image cannot be read, do not guess.
Tell the student what part is unclear.
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
                        "image_url": image_data,
                        "detail": "original"
                    }
                ]
            }
        ]
    )

    return response.output_text


# ============================================================
# WEBSITE
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
}

.controls {
    background: white;
    padding: 12px;
    border-bottom: 1px solid #ddd;
}

.mode-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 10px;
}

.mode-button {
    border: none;
    padding: 13px;
    border-radius: 10px;
    font-weight: bold;
    font-size: 15px;
}

.read-mode {
    background: #7c3aed;
    color: white;
}

.practice-mode {
    background: #059669;
    color: white;
}

.active {
    outline: 3px solid #f59e0b;
}

select,
input {
    width: 100%;
    padding: 12px;
    border: 1px solid #ccc;
    border-radius: 9px;
    font-size: 15px;
    margin-top: 8px;
}

.number-row {
    display: grid;
    grid-template-columns: 1fr;
}

#chat {
    max-width: 900px;
    margin: auto;
    padding: 15px;
    padding-bottom: 180px;
}

.message {
    padding: 14px 15px;
    margin: 10px 0;
    border-radius: 13px;
    line-height: 1.6;
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

.status {
    text-align: center;
    font-size: 13px;
    color: #555;
    margin-bottom: 7px;
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
    font-size: 18px;
}

.send {
    background: #2563eb;
}

input[type="file"] {
    display: none;
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
id="readButton"
class="mode-button read-mode active"
onclick="setMode('read')">

📖 READ MODE

</button>


<button
id="practiceButton"
class="mode-button practice-mode"
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
placeholder="Enter topic e.g. Motion, Algebra, Cell Division"
>


<div class="number-row">

<input
id="number"
type="number"
min="1"
max="20"
value="5"
placeholder="Number of practice questions"
>

</div>

</div>


<div id="chat">

<div class="message ai">

Welcome to UTME Attack Force AI.

📖 READ MODE
Choose a subject and topic to study clear notes,
explanations, formulas and examples.

🤖 PRACTICE MODE
Choose a subject and topic to receive NEW
AI-GENERATED UTME-style practice questions.

📷 You can photograph a question.

🎤 You can use your microphone.

</div>

</div>


<div class="composer">

<div
class="status"
id="status">

📖 READ MODE — Learn the topic

</div>


<div class="composer-row">

<input
id="message"
placeholder="Enter a topic or question..."
onkeydown="if(event.key === 'Enter') sendMessage()"
>


<button
class="action"
onclick="startVoice()"
title="Voice input">

🎤

</button>


<label
class="action"
title="Take or upload a photo">

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

let mode = "read";


function setMode(newMode) {

    mode = newMode;

    const readButton =
        document.getElementById("readButton");

    const practiceButton =
        document.getElementById("practiceButton");

    const status =
        document.getElementById("status");

    readButton.classList.remove("active");

    practiceButton.classList.remove("active");


    if (mode === "read") {

        readButton.classList.add("active");

        status.textContent =
            "📖 READ MODE — Learn the topic";

        document.getElementById("message")
            .placeholder =
            "Enter a topic to learn...";

    } else {

        practiceButton.classList.add("active");

        status.textContent =
            "🤖 PRACTICE MODE — AI-generated questions";

        document.getElementById("message")
            .placeholder =
            "Enter a topic to practice...";

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

    window.scrollTo(
        0,
        document.body.scrollHeight
    );

    return message;
}


async function sendMessage() {

    const input =
        document.getElementById("message");

    const message =
        input.value.trim();

    const subject =
        document.getElementById("subject").value;

    const topicInput =
        document.getElementById("topic").value.trim();

    const number =
        document.getElementById("number").value;


    if (!subject) {

        alert("Please choose a subject first.");

        return;
    }


    if (!message && !topicInput) {

        alert("Please enter a topic or question.");

        return;
    }


    const topic =
        topicInput || message;


    addMessage(
        message || topic,
        "user"
    );


    input.value = "";


    const loading =
        addMessage(
            mode === "read"
            ? "📖 Preparing your lesson..."
            : "🤖 Preparing your practice questions...",
            "ai"
        );


    try {

        const response =
            await fetch("/chat", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    message: message || topic,
                    mode: mode,
                    subject: subject,
                    topic: topic,
                    number: number

                })

            });


        const data =
            await response.json();


        loading.remove();


        addMessage(
            data.reply ||
            "Sorry, I could not process that request.",
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


    if (!subject) {

        alert("Please choose a subject first.");

        fileInput.value = "";

        return;
    }


    addMessage(
        "📷 Photo uploaded.",
        "user"
    );


    const loading =
        addMessage(
            "🔎 Reading the image...",
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

                            subject:
                                subject,

                            mode:
                                mode

                        })

                    });


                const data =
                    await response.json();


                loading.remove();


                addMessage(
                    data.reply ||
                    "I could not process the image.",
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
                mode === "read"
                ? "📖 READ MODE"
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
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template_string(HTML)


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    message = data.get("message", "").strip()

    mode = data.get("mode", "read")

    subject = data.get("subject", "").strip()

    topic = data.get("topic", "").strip()

    number = data.get("number", 5)


    if not subject:

        return jsonify({
            "reply":
                "Please choose a subject first."
        })


    if not topic:

        topic = message


    if not topic:

        return jsonify({
            "reply":
                "Please enter a topic or question."
        })


    try:

        if mode == "read":

            answer = read_topic(
                subject,
                topic
            )

        else:

            try:
                question_number = int(number)
            except (TypeError, ValueError):
                question_number = 5

            question_number = max(
                1,
                min(question_number, 20)
            )

            answer = practice_topic(
                subject,
                topic,
                question_number
            )


        return jsonify({
            "reply": answer
        })


    except Exception as error:

        print(
            "AI ERROR:",
            repr(error)
        )

        return jsonify({
            "reply":
                "The AI could not process the request right now. "
                "Please try again."
        }), 500


# ============================================================
# IMAGE ENDPOINT
# ============================================================

@app.route("/image", methods=["POST"])
def image_question():

    data = request.get_json(silent=True) or {}

    image = data.get("image")

    subject = data.get("subject", "").strip()

    mode = data.get("mode", "practice")


    if not image:

        return jsonify({
            "reply":
                "No image was received."
        }), 400


    if not subject:

        return jsonify({
            "reply":
                "Please choose a subject first."
        }), 400


    try:

        answer = solve_image(
            image_data=image,
            subject=subject,
            mode=mode
        )


        return jsonify({
            "reply": answer
        })


    except Exception as error:

        print(
            "IMAGE ERROR:",
            repr(error)
        )

        return jsonify({
            "reply":
                "I could not process that image. "
                "Please make sure the photograph is clear and try again."
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
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
)
