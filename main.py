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


def ai_chat_response(message_history, notes, model):
    # Make an API call to OpenAI to get the AI response
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful tutor assistant. You will be given notes from a school lecture.\
                                           You must quiz the user on the notes to make sure they understand the material.\
                                           After the user answers a question, you must give them feedback on whether they got it right or wrong.\
                                           If it's correct, write 'Correct!' and if it's wrong, write 'Wrong!' and explain why it's wrong.\
                                           You can give hints if the user is struggling and you can also give them the answer only if they ask for it.\
                                           You will continuously quiz the user until you've covered all the material"},
            {"role": "user", "content": "I am going to give you a notes to quiz me on. Type 'Y' if you're ready."},
            {"role": "assistant", "content": "Y"},
            {"role": "user", "content": notes},
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


def check_finish_reason(finish_reason):
    # TODO: add more stuff here

    if finish_reason == "length":
        # This means that the model reached its token limit
        pass
    elif finish_reason == "content_filter":
        # This means that OpenAI blocked the message with their content filter
        pass


@app.route("/")
def index():
    return redirect(url_for("transcript"))


@app.route("/transcript", methods=["GET", "POST"])
@app.route("/transcript/", methods=["GET", "POST"])
def transcript():
    test_mode_enabled = session.get("test-mode", False)

    if request.method == "POST":
        if "test-mode" in request.form:
            # Get the value of the switch to check if "test mode" is enabled
            session["test-mode"] = request.form["test-mode"] == "on"
        else:
            transcript = request.form.get("transcript", "")

            if "create-transcript" in request.form or "overwrite-transcript" in request.form:
                # TODO: figure out how to retrieve audio
                audio = "."
                if audio == "":
                    # Show an error if there's no audio loaded when the user clicks "Create transcript"
                    session["no_audio_modal"] = True
                elif transcript.strip() != "" and not "overwrite-transcript" in request.form:
                    # Show a warning if the user tries to overwrite an existing transcript
                    # (this will not be run if the user confirms that they want to overwrite the transcript)
                    session["overwrite_transcript_modal"] = True
                elif test_mode_enabled:
                    transcript = "This is a test transcript."
                else:
                    transcript = transcribe_audio(audio)

            session["transcript"] = transcript

        return redirect(url_for("transcript"))
    else:
        # Load the transcript from the session (default to empty string if it doesn't exist)
        transcript = session.get("transcript", "")

        show_modal = False
        modal_title = ""
        modal_body = ""
        modal_button1_text = "Okay"
        modal_show_danger_button = False

        # Check if the modal should be displayed then remove it from the session
        no_audio_modal = session.pop("no_audio_modal", False)
        overwrite_transcript_modal = session.pop(
            "overwrite_transcript_modal", False)

        if no_audio_modal:
            modal_title = "No audio"
            modal_body = "There is no audio loaded to transcribe. Please record audio and try again."
        elif overwrite_transcript_modal:
            modal_title = "Overwrite transcript?"
            modal_body = "Are you sure you want to overwrite the existing transcript and create a new one?"
            modal_button1_text = "Cancel"
            modal_show_danger_button = True

        if any([no_audio_modal, overwrite_transcript_modal]):
            show_modal = True

        return render_template("transcript.html", transcript=transcript, test_mode_enabled=test_mode_enabled, display_modal=show_modal,
                               modal_title=modal_title, modal_body=modal_body, modal_button1_text=modal_button1_text, modal_show_danger_button=modal_show_danger_button)


@app.route("/notes", methods=["GET", "POST"])
@app.route("/notes/", methods=["GET", "POST"])
def notes():
    # TODO: create warning modal if the user clicks "Create notes" and there are already notes

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
                    session["no_transcript_modal"] = True
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
        no_transcript_modal = session.pop(
            "no_transcript_modal", False)

        return render_template("notes.html", notes=notes, selected_model=selected_model, display_modal=no_transcript_modal)


@app.route("/interactive-quiz", methods=["GET", "POST"])
@app.route("/interactive-quiz/", methods=["GET", "POST"])
def quiz():
    global chat_history

    selected_model = session.get("model-quiz", "GPT-3.5")

    if request.method == "POST":
        if "model-quiz" in request.form:
            # Set the selected model (from the dropdown)
            selected_model = request.form["model-quiz"]
            session["model-quiz"] = selected_model
            return redirect(url_for("quiz"))
        else:
            if "start-quiz" in request.form or "restart-quiz" in request.form:
                notes = session.get("notes", "")
                if notes.strip() == "":
                    # Display an error if the notes are empty
                    return render_template("chat_body.html", modal_title="No notes",
                                           modal_body="There must be notes on the previous screen to create the quiz from. Please create notes from a transcript or paste in your notes.",
                                           modal_button1_text="Okay", modal_button1_style="primary", messages=chat_history)

                # Display a warning if the user tries to restart the quiz. If they confirmed they want to restart, then the quiz will be restarted
                if session.get("quiz_started", False) and not "restart-quiz" in request.form:
                    return render_template("chat_body.html", modal_title="Restart quiz?",
                                           modal_body="Are you sure you want to restart the quiz? All of your previous messages will be deleted.",
                                           modal_button1_text="Cancel", modal_button2_text="Yes, I'm sure", modal_button1_style="primary",
                                           modal_button2_style="danger", modal_button2_name="restart-quiz", messages=chat_history)
                else:
                    # Reset the chat history
                    chat_history.clear()
                    session["quiz_started"] = True

            if "message" in request.form:
                message = request.form.get("message", "")
                if message.strip() == "":
                    # Don't send a blank message
                    return render_template("chat_body.html", messages=chat_history)

                # Add the message to the chat history
                chat_history.append({"role": "user", "content": message})

            # Get the AI response if the quiz is started
            if session.get("quiz_started", False):
                if selected_model == "GPT-3.5":
                    ai_response = ai_chat_response(
                        chat_history, "gpt-3.5-turbo")
                elif selected_model == "GPT-4":
                    ai_response = ai_chat_response(chat_history, "gpt-4")
                elif selected_model == "Test mode":
                    ai_response = "This is a test message."

                # Add the AI response to the chat history
                chat_history.append(
                    {"role": "assistant", "content": ai_response})

                session["chat_history"] = chat_history
            else:
                # Display an error if the user tries to send a message without starting the quiz
                return render_template("chat_body.html", modal_title="Start the quiz",
                                       modal_body="You must start the quiz before sending a message. Please click the \"Start quiz\" button.",
                                       modal_button1_text="Okay", modal_button1_style="primary")

            return render_template("chat_body.html", messages=chat_history)

    else:
        # Load the chat history from the session (default to empty list if it doesn't exist)
        chat_history = session.get("chat_history", [])

        return render_template("quiz.html", messages=chat_history, selected_model=selected_model)


if __name__ == "__main__":
    app.run(debug=True, port=5002)
