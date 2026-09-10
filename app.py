import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from google import genai
from google.genai import types
from chatbot_config import SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.1-flash-lite"

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not configured in the .env file.")

client = genai.Client(api_key=API_KEY)


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"error": "Please enter a question."}), 400

    contents = []

    for item in history[-12:]:
        role = item.get("role")
        text = (item.get("text") or "").strip()
        if role in {"user", "model"} and text:
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=text)]
                )
            )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)]
        )
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            answer = (
                "I can help with HealthMate-AI study topics. "
                "Please ask a health or healthcare-related study question."
            )

        return jsonify({"answer": answer})

    except Exception:
        return jsonify({
            "error": "I couldn't process that question right now. "
                     "Please try again."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
