import os

import openai
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = os.urandom(24)

chat_history = []

# TODO: format backtick as inline code and triple backtick as code block


def transcribe_audio(file):
    transcript = openai.Audio.transcribe(
        "whisper-1", file, prompt="The transcript is a school lecture.", response_format="text")
    return transcript


def transcript_to_notes(transcript, model):
    # TODO: add support for notes with headings and stuff (maybe using markdown)

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a note taker that takes notes based on a transcript from a school lecture.\
                                           Make the notes concise but make sure you also get down all the important information.\
                                           Also, keep in mind that the transcript may contain text from different people speaking.\
                                           Don't type anything else but the notes."},
            {"role": "user", "content": "I am going to give you a transcript to create notes for. Type 'Y' if you're ready."},
            {"role": "assistant", "content": "Y"},
            {"role": "user", "content": transcript}
        ]
    )
    notes = response["choices"][0]["message"]["content"]
    # TODO: also check the finish reason to make sure its valid

    return notes


def ai_chat_response(message_history, model):
    # Make an API call to OpenAI to get the AI response
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            *message_history
        ]
    )
    response_text = response["choices"][0]["message"]["content"]
    finish_reason = response["choices"][0]["finish_reason"]

    if finish_reason == "length":
        # This means that the model reached its token limit
        pass
    elif finish_reason == "content_filter":
        # This means that OpenAI blocked the message with their content filter
        pass

    return response_text


@app.route("/")
def index():
    return redirect(url_for("transcript"))


@app.route("/transcript", methods=["GET", "POST"])
@app.route("/transcript/", methods=["GET", "POST"])
def transcript():
    test_mode_enabled = session.get("test-mode", "off")

    if request.method == "POST":
        if "test-mode" in request.form:
            session["test-mode"] = request.form["test-mode"] == "on"
        else:
            transcript = request.form.get("transcript", "")

            if "create-transcript" in request.form:
                # TODO: figure out how to retrieve audio
                audio = ""
                if audio == "":
                    session["display_error_modal"] = True
                else:
                    if test_mode_enabled:
                        transcript = "This is a test transcript."
                    else:
                        transcript = transcribe_audio(audio)

            session["transcript"] = transcript

        return redirect(url_for("transcript"))
    else:
        # Load the transcript from the session (default to empty string if it doesn't exist)
        transcript = session.get("transcript", "")
        # Check if the modal should be displayed then remove it from the session
        display_error_modal = session.pop("display_error_modal", False)

        return render_template("transcript.html", transcript=transcript, test_mode_enabled=test_mode_enabled, display_modal=display_error_modal)


@app.route("/notes", methods=["GET", "POST"])
@app.route("/notes/", methods=["GET", "POST"])
def notes():
    # This is for the model selection dropdown
    selected_model = session.get("model-notes", "GPT-3.5")

    if request.method == "POST":

        if "model-notes" in request.form:
            selected_model = request.form["model-notes"]
            session["model-notes"] = selected_model
        else:
            # Check if the user clicked the "Create notes" button
            notes = request.form["notes"]

            if "create-notes" in request.form:
                transcript = session.get("transcript", "")

                if transcript.strip() == "":
                    # Display an error if the transcript is empty
                    session["display_error_modal"] = True
                else:
                    if selected_model == "GPT-3.5":
                        notes = transcript_to_notes(
                            transcript, "gpt-3.5-turbo")
                    elif selected_model == "GPT-4":
                        notes = transcript_to_notes(transcript, "gpt-4")
                    elif selected_model == "Test mode":
                        notes = "These are test notes."

            session["notes"] = notes

        return redirect(url_for("notes"))
    else:
        # Load the notes from the session (default to empty string if they don't exist)
        notes = session.get("notes", "")
        # Check if the modal should be displayed then remove it from the session
        display_error_modal = session.pop("display_error_modal", False)

        return render_template("notes.html", notes=notes, selected_model=selected_model, display_modal=display_error_modal)


@app.route("/interactive-quiz", methods=["GET", "POST"])
@app.route("/interactive-quiz/", methods=["GET", "POST"])
def quiz():
    global chat_history

    if "model-quiz" in session:
        selected_model = session["model-quiz"]
    else:
        selected_model = "GPT-3.5"

    if request.method == "POST":
        if "message" in request.form:
            message = request.form["message"]
            if message.strip() == "":
                # Don't send a blank message
                return redirect(url_for("quiz"))

            # Add the message to the chat history
            chat_history.append({"role": "user", "content": message})

            # Get the AI response
            if selected_model == "GPT-3.5":
                ai_response = ai_chat_response(chat_history, "gpt-3.5-turbo")
            elif selected_model == "GPT-4":
                ai_response = ai_chat_response(chat_history, "gpt-4")
            elif selected_model == "Test mode":
                ai_response = "This is a test message."

            # Add the AI response to the chat history
            chat_history.append({"role": "assistant", "content": ai_response})

            session["chat_history"] = chat_history

        if "model-quiz" in request.form:
            selected_model = request.form["model-quiz"]

            session["model-quiz"] = selected_model

        # Redirect to the chat page
        return redirect(url_for("quiz"))
    else:
        # Load the chat history from the session (default to empty list if it doesn't exist)
        chat_history = session.get("chat_history", [])

        # Render the quiz page with the chat history
        return render_template("quiz.html", messages=chat_history, selected_model=selected_model)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
