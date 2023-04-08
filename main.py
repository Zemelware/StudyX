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
    # transcript = openai.Audio.transcribe(
    #     "whisper-1", file, prompt="The transcript is a school lecture.", response_format="text")
    transcript = "This is a test transcript."
    return transcript


def transcript_to_notes(transcript, model):
    # TODO: add support for notes with headings and stuff (maybe using markdown)

    # response = openai.ChatCompletion.create(
    #     model=model,
    #     messages=[
    #         {"role": "system", "content": "You are a note taker that takes notes based on a transcript from a school lecture.\
    #                                        Make the notes concise but make sure you also get down all the important information.\
    #                                        Also, keep in mind that the transcript may contain text from different people speaking.\
    #                                        Don't type anything else but the notes."},
    #         {"role": "user", "content": "I am going to give you a transcript to create notes for. Type 'Y' if you're ready."},
    #         {"role": "assistant", "content": "Y"},
    #         {"role": "user", "content": transcript}
    #     ]
    # )
    # notes = response["choices"][0]["message"]["content"]
    # TODO: also check the finish reason to make sure its valid

    notes = "These are test notes.\n- This\n- Is\n- A\n- Test"

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


@app.route("/", methods=["GET", "POST"])
@app.route("/transcript", methods=["GET", "POST"])
@app.route("/transcript/", methods=["GET", "POST"])
def transcript():
    if request.method == "POST":
        # TODO: see how to use the action attribute of form (and if it's necessary to use)
        if "create-transcript" in request.form:
            # TODO: figure out how to retrieve audio
            audio = ""
            transcript = transcribe_audio(audio)

            session["transcript"] = transcript

            return redirect(url_for("transcript"))
        elif "create-notes" in request.form:
            transcript = request.form["transcript"]
            # TODO: create dropdown for user to select the model
            notes = transcript_to_notes(transcript, "gpt-3.5-turbo")

            session["notes"] = notes

            return redirect(url_for("notes"))
    else:
        if "transcript" in session:
            transcript = session["transcript"]
        else:
            transcript = ""

        return render_template("transcript.html", transcript=transcript)


@app.route("/notes", methods=["GET", "POST"])
@app.route("/notes/", methods=["GET", "POST"])
def notes():
    if request.method == "POST":
        pass
    else:
        if "notes" in session:
            notes = session["notes"]
        else:
            notes = ""

        return render_template("notes.html", notes=notes)


@app.route("/interactive-quiz", methods=["GET", "POST"])
@app.route("/interactive-quiz/", methods=["GET", "POST"])
def quiz():
    global chat_history

    if "model" in session:
        model = session["model"]
    else:
        model = "gpt-3.5"

    if request.method == "POST":
        if "message" in request.form:
            message = request.form["message"]
            if message.strip() == "":
                # Don't send a blank message
                return redirect(url_for("quiz"))

            # Add the message to the chat history
            chat_history.append({"role": "user", "content": message})

            # Get the AI response
            if model == "gpt-3.5":
                ai_response = ai_chat_response(chat_history, "gpt-3.5-turbo")
            elif model == "gpt-4":
                ai_response = ai_chat_response(chat_history, "gpt-4")
            elif model == "test mode":
                ai_response = "This is a test message."

            # Add the AI response to the chat history
            chat_history.append({"role": "assistant", "content": ai_response})

            session["chat_history"] = chat_history

        if "model" in request.form:
            model = request.form["model"]

            session["model"] = model

        # Redirect to the chat page
        return redirect(url_for("quiz"))
    else:
        if "chat_history" in session:
            # If the user has already been chatting with the AI, then we want to retrieve the chat history from the session
            chat_history = session["chat_history"]
        else:
            # Otherwise, start with an empty chat history
            chat_history = []

        # Render the quiz page with the chat history
        return render_template("quiz.html", messages=chat_history, selected_model=model)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
