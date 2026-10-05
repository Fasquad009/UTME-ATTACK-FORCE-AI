import os
import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ============================================================
# SETTINGS
# ============================================================

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

MODEL = os.environ.get(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)

OPENAI_URL = "https://api.openai.com/v1/responses"


# ============================================================
# SYSTEM INSTRUCTIONS
# ============================================================

SYSTEM_PROMPT = """
You are UTME ATTACK FORCE AI.

You are an educational AI assistant for Nigerian students
preparing for UTME, JAMB and school examinations.

Your purpose is:

- UTME preparation
- JAMB preparation
- School examinations
- Academic learning
- Revision
- Topic explanations
- Practice questions
- Step-by-step solutions
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

READ MODE teaches a selected subject and topic.

Use clear sections such as:

1. Introduction
2. Simple definition
3. Main ideas
4. Important terms
5. Detailed explanation
6. Important formulas
7. Worked examples
8. UTME focus
9. Common mistakes
10. Quick revision

Use simple student-friendly English.

For Mathematics and Physics, write calculations clearly.

For example:

Speed = Distance ÷ Time

Do NOT write ugly computer notation such as:

frac{distance}{time}

Explain symbols clearly.

============================================================
PRACTICE MODE
============================================================

PRACTICE MODE creates NEW AI-GENERATED UTME-STYLE
practice questions.

IMPORTANT:

Every question created by Practice Mode is AI-GENERATED.

NEVER call it:

- a genuine JAMB question
- an original JAMB question
- an authentic past question
- an official JAMB question
- a question from a particular JAMB year

If multiple-choice questions are requested, use:

A. option
B. option
C. option
D. option

Then:

Correct Answer:
Explanation:

Make questions useful and challenging for UTME preparation.

============================================================
PHOTO / CAMERA
============================================================

When a student sends a photograph:

1. Read the image carefully.
2. Identify the question or educational material.
3. Solve or explain it.
4. Show working clearly.
5. Explain the reasoning.
6. Give the final answer.
7. If multiple choice, identify the correct option.

Never invent text that cannot be read.

If part of the photograph is unclear, say exactly what
cannot be read.

============================================================
ACCURACY
============================================================

Accuracy is more important than pretending to know something.

Never invent claims about JAMB history.

Never present AI-generated questions as genuine JAMB
past questions.

============================================================
TEACHING STYLE
============================================================

Be clear, friendly and student-friendly.

Use headings, lists and spacing.

Make students understand WHY an answer is correct,
not just the final answer.
"""


# ============================================================
# OPENAI API CALL
# ============================================================

def call_openai(input_data):

    if not OPENAI_API_KEY:

        raise RuntimeError(
            "OPENAI_API_KEY is missing from Render Environment Variables."
        )

    payload = {
        "model": MODEL,
        "instructions": SYSTEM_PROMPT,
        "input": input_data
    }

    body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        OPENAI_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + OPENAI_API_KEY
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            req,
            timeout=120
        ) as response:

            raw = response.read().decode("utf-8")

            data = json.loads(raw)

            text = data.get("output_text")

            if text:
                return text

            # Fallback if output_text is not available.
            output = data.get("output", [])

            collected = []

            for item in output:

                for content in item.get("content", []):

                    if content.get("type") == "output_text":

                        collected.append(
                            content.get("text", "")
                        )

            result = "\n".join(collected).strip()

            if result:
                return result

            raise RuntimeError(
                "OpenAI returned a response but no text was found."
            )

    except urllib.error.HTTPError as error:

        status = error.code

        try:

            error_body = error.read().decode("utf-8")

            error_data = json.loads(error_body)

            api_error = error_data.get("error", {})

            error_type = api_error.get(
                "type",
                "unknown"
            )

            error_code = api_error.get(
                "code",
                "unknown"
            )

            error_message = api_error.get(
                "message",
                "No error message returned."
            )

            raise RuntimeError(
                f"OpenAI API error {status}: "
                f"{error_type} / {error_code} - "
                f"{error_message}"
            )

        except json.JSONDecodeError:

            raise RuntimeError(
                f"OpenAI API HTTP error {status}: "
                f"{error_body[:500]}"
            )

    except urllib.error.URLError as error:

        raise RuntimeError(
            "Could not connect to OpenAI API: "
            + str(error.reason)
        )

    except TimeoutError:

        raise RuntimeError(
            "The request to OpenAI timed out."
        )


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

Use this structure:

# {topic}

## Introduction

## What is {topic}?

## Main ideas

## Important terms

## Detailed explanation

## Formulas

If formulas apply, write them clearly and explain every
symbol.

## Worked examples

Give useful examples and explain them step by step.

## UTME focus

List the important points a UTME student should remember.

## Common mistakes

## Quick revision

These are teaching notes.

Do not claim that anything in this lesson is a genuine
JAMB past question.
"""

    return call_openai(prompt)


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

Do NOT call them genuine JAMB questions.

Do NOT call them original JAMB questions.

Do NOT attach a JAMB year to them.

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

For Mathematics and Physics, show calculations clearly.
"""

    return call_openai(prompt)


# ============================================================
# IMAGE QUESTION SOLVER
# ============================================================

def solve_image(image_data, subject, mode):

    if not OPENAI_API_KEY:

        raise RuntimeError(
            "OPENAI_API_KEY is missing from Render Environment Variables."
        )

    if mode == "read":

        instruction = """
The student is using READ MODE.

Use the photograph as learning material.

Explain the educational material shown in the image clearly
and teach the student what it means.
"""

    else:

        instruction = """
The student is using PRACTICE MODE.

Solve the question shown in the photograph.

Do not claim that the photographed question is a genuine
JAMB past question.
"""

    prompt = f"""
{instruction}

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

Tell the student which part is unclear.
"""

    image_input = [
        {
            "type": "input_text",
            "text": prompt
        },
        {
            "type": "input_image",
            "image_url": image_data,
            "detail": "high"
        }
    ]

    return call_openai([
        {
            "role": "user",
            "content": image_input
        }
    ])


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
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template_string(HTML)


# ============================================================
# CHAT
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json(silent=True) or {}

    message = str(
        data.get("message", "")
    ).strip()

    mode = data.get(
        "mode",
        "read"
    )

    subject = str(
        data.get("subject", "")
    ).strip()

    topic = str(
        data.get("topic", "")
    ).strip()

    number = data.get(
        "number",
        5
    )


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

            except (
                TypeError,
                ValueError
            ):

                question_number = 5


            question_number = max(
                1,
                min(
                    question_number,
                    20
                )
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

        error_text = str(error)

        print(
            "AI ERROR:",
            repr(error),
            flush=True
        )

        return jsonify({
            "reply":
                "AI ERROR\n\n" +
                error_text
        }), 500


# ============================================================
# IMAGE
# ============================================================

@app.route("/image", methods=["POST"])
def image_question():

    data = request.get_json(
        silent=True
    ) or {}

    image = data.get(
        "image"
    )

    subject = str(
        data.get(
            "subject",
            ""
        )
    ).strip()

    mode = data.get(
        "mode",
        "practice"
    )


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

        error_text = str(error)

        print(
            "IMAGE ERROR:",
            repr(error),
            flush=True
        )

        return jsonify({
            "reply":
                "IMAGE ERROR\n\n" +
                error_text
        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "ok",
        "app": "UTME Attack Force AI",
        "model": MODEL,
        "openai_key_configured":
            bool(OPENAI_API_KEY)
    })


# ============================================================
# START
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
