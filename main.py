import os
import re
from datetime import timedelta

import openai
import tiktoken
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for
from openai.error import RateLimitError

from flask_session import Session

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
client_api_key = os.getenv("CLIENT_API_KEY")

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = os.urandom(24)
app.config.from_object(__name__)

Session(app)

chat_history = []


def transcribe_audio(file):
    transcript = openai.Audio.transcribe(
        "whisper-1", file, prompt="The transcript is a school lecture.", response_format="text")
    return transcript


def transcript_to_notes(transcript, model):
    transcript_sections = split_transcript_into_sections(transcript, model)

    notes = ""
    if len(transcript_sections) == 1:
        # Since the two models behave differently, they need to be pro-prompted differently
        if model == "gpt-3.5-turbo":
            messages = [
                {"role": "system", "content": "You are a professional note taker that takes excellent notes."},
                {"role": "user", "content": "I am going to give you a transcript from a lecture to create notes for. Create the notes in Markdown format. \
Make sure all the important information is contained in the notes. \
Keep in mind that the transcript may have picked up students talking. Just focus on the actual speaker. Type 'Y' if you're ready."},
                {"role": "assistant", "content": "Y"},
                {"role": "user", "content": transcript}
            ]
        elif model == "gpt-4":
            messages = [
                {"role": "system", "content": "You are a professional note taker that takes excellent notes based on a transcript from a school lecture. \
You always take notes in Markdown format. \
Make sure all the important information is contained in the notes. \
Keep in mind that the transcript may have picked up students talking. Just focus on the actual speaker."},
                {"role": "user", "content": "I am going to give you a transcript to create notes for. Type 'Y' if you're ready."},
                {"role": "assistant", "content": "Y"},
                {"role": "user", "content": transcript}
            ]

        notes = gpt_api_call(messages, model)
    else:
        # If the transcript is split into multiple sections, the model must be prompted differently
        for i, transcript_section in enumerate(transcript_sections):

            # TODO: make more readable
            if model == "gpt-3.5-turbo" and i == 0:
                messages = [
                    {"role": "system", "content": "You are a professional note taker that takes excellent notes."},
                    {"role": "user", "content": f"I am going to give you a transcript from a lecture to create notes for. \
The transcript is split into multiple parts. Right now I am giving you part #1. Create the notes in Markdown format. \
Make sure all the important information is contained in the notes. \
Keep in mind that the transcript may have picked up students talking. Just focus on the actual speaker. \
Type 'Y' if you're ready to create the notes."},
                    {"role": "assistant", "content": "Y"},
                    {"role": "user", "content": transcript_section}
                ]
            elif model == "gpt-3.5-turbo":
                # TODO: prompt better. Currently, the model re-writes the whole notes.

                notes_after_last_heading = ""
                # Split by newline characters to get individual lines
                lines = notes.split("\n")

                # Loop through the lines in reverse order
                for index, line in enumerate(reversed(lines)):
                    # Check if the line starts with up to 6 hashes followed by a space
                    if re.match(r"^#{1,6} ", line):
                        # If the line starts with a heading prefix, update last_heading_index
                        # Set notes_after_last_heading to every line after and including the last heading
                        notes_after_last_heading = "\n".join(
                            lines[-(index + 1):])
                        break

                print("Notes after last heading:\n" +
                      notes_after_last_heading + "\n")

                messages = [
                    {"role": "system", "content": "You are a professional note taker that takes excellent notes."},
                    {"role": "user", "content": f"I am going to give you a transcript from a lecture to create notes for. \
The transcript is split into multiple parts. Right now I am giving you part #{i + 1}. Create the notes in Markdown format. \
Make sure all the important information is contained in the notes. \
Keep in mind that the transcript may have picked up students talking. Just focus on the actual speaker. \
First I will give you the last section of notes from the previous part of the transcript then I will give you part #{i + 1} of the transcript. \
IMPORTANT: Only write the notes for the given part do NOT write the entirety of the notes  \
Type 'Y' if you're ready for the previous notes."},
                    {"role": "assistant", "content": "Y"},
                    {"role": "user", "content": f"Here's the previous section of notes. Type 'R' once you've read them.\n\n{notes_after_last_heading}"},
                    {"role": "assistant", "content": "R"},
                    {"role": "user", "content": f"Here is part #{i + 1} of the transcript. Only reply with the notes for this part of the transcript. \
Make sure to seamlessly integrate the notes you create with my previous notes and also create the necessary headings. \
Important: do NOT re-write my previous notes and do NOT re-write the title of the notes with something like 'Cont'd' or anything else, ONLY write the new notes.\n\n\
Now here is part #{i + 1} of the transcript:\n\n{transcript_section}"}
                ]
            # TODO: stop the model from re-writing the title of the notes
            elif model == "gpt-4" and i == 0:
                messages = [
                    {"role": "system", "content": "You are a professional note taker that takes excellent notes based on a transcript from a school lecture. \
You always take notes in Markdown format. \
Make sure all the important information is contained in the notes. \
Keep in mind that the transcript may have picked up students talking. Just focus on the actual speaker."},
                    {"role": "user", "content": f"I am going to give you a transcript from a lecture to create notes for. \
The transcript is split into multiple parts. Right now I am giving you part #1. \
Make sure all the important information is contained in the notes. \
Keep in mind that the transcript may have picked up students talking. Just focus on the actual speaker. \
Type 'Y' if you're ready to create the notes."},
                    {"role": "assistant", "content": "Y"},
                    {"role": "user", "content": transcript_section}
                ]
            elif model == "gpt-4":
                pass

            # Add a newline character before the response (to ensure the markdown appears as a heading) if it's not the first response
            response_prefix = "" if i == 0 else "\n\n"

            print("Messages:", messages, "\n")

            notes += response_prefix + gpt_api_call(messages, model)

    return notes


def split_transcript_into_sections(transcript, model):
    """Splits the transcript into sections to get around the model token limit."""

    # Token limits: 4,096 tokens for gpt-3.5-turbo and 8,192 tokens for gpt-4
    if model == "gpt-3.5-turbo":
        # This is the max number of tokens that are allowed per section.
        # This number shouldn't be too close to the model token limit so there is room left for the model's response.
        section_token_limit = 3000
    elif model == "gpt-4":
        section_token_limit = 6000

    # Get the number of tokens in the transcript so it can be split properly into sections
    enc = tiktoken.get_encoding("cl100k_base")
    encoded_transcript = enc.encode(transcript)
    transcript_token_count = len(encoded_transcript)

    # After every section_token_limit number of tokens, split the transcript to create a new section
    transcript_sections = []
    text_after_last_period = ""
    for i in range(0, transcript_token_count, section_token_limit):
        if i + section_token_limit < transcript_token_count:
            # Take the sentence fragment after the last sentence from the previous section and add it to the beginning of the next section
            section = text_after_last_period + \
                enc.decode(encoded_transcript[i:i + section_token_limit])

            # Don't split in the middle of a sentence.
            # Cut off the section at the last period before the section_token_limit,
            # then save the sentence fragment after the last period in a variable to add to the beginning of the next section
            section_ended_at_sentence = section.rsplit(".", 1)[0] + "."
            text_after_last_period = section.rsplit(".", 1)[1]

            # Add the section to the list
            transcript_sections.append(section_ended_at_sentence)
        else:
            # If the last section is less than section_token_limit tokens, just add the rest of the transcript as the last section
            section_until_end = text_after_last_period + \
                enc.decode(encoded_transcript[i:])

            transcript_sections.append(section_until_end)

    return transcript_sections


def ai_chat_response(message_history, notes, model):
    # Make an API call to OpenAI to get the AI response

    if model == "gpt-3.5-turbo":
        messages = [
            {"role": "system", "content": "You are a helpful and friendly tutor assistant that helps students learn material."},
            {"role": "user", "content": "I'm going to give you notes to quiz me on. You must ask me questions one at a time to make sure I understand the material. \
After I answer a question, let me know if got it right or wrong and explain the answer if I'm wrong, then ask the next question. \
Feel free to ask me to expand on my answer if you feel it was missing information or only partly correct. You can give me hints if I'm struggling. Only give me the answer if I ask for it. \
Continuously quiz me until you've covered all the material, at which point you will let me know that I've been quizzed on everything. Type 'Y' if you're ready for the notes."},
            {"role": "assistant", "content": "Y"},
            {"role": "user", "content": "Here are the notes. Only reply with the first question.\n" + notes},
            *message_history
        ]
    elif model == "gpt-4":
        # TODO: Edit the system message here
        messages = [
            {"role": "system", "content": "You are a helpful and friendly tutor assistant. I will give you notes from a school lecture. \
You must quiz me on the notes to make sure I understand the material. \
After I answer a question, you must give me feedback on whether I got it right or wrong. \
If it's correct, write 'Correct!' and if it's wrong, write 'Wrong!' and explain why it's wrong. \
You can give hints if I'm struggling and you can also give me the answer only if I ask for it, but try to help me figure it out first. \
You will continuously quiz me until you've covered all the material, at which point you will let me know that I've been quizzed on everything."},
            {"role": "user", "content": "I am going to give you notes to quiz me on. Type 'Y' if you're ready."},
            {"role": "assistant", "content": "Y"},
            {"role": "user", "content": "Here are the notes. Don't reply with anything except the question.\n" + notes},
            *message_history
        ]

    ai_response = gpt_api_call(messages, model)

    return ai_response


def gpt_api_call(messages, model):
    try:
        response_json = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.4
        )
    except RateLimitError:
        print(
            "The server is experiencing a high volume of requests. Please try again later.")

    response_content = response_json["choices"][0]["message"]["content"]
    finish_reason = response_json["choices"][0]["finish_reason"]
    print("Response content:\n", response_content, "\n")

    check_finish_reason(finish_reason)

    return response_content


def check_finish_reason(finish_reason):
    # TODO: create a visual message if the finish reason is any of these (maybe in the side menu)

    if finish_reason == "length":
        # This means that the model reached its token limit
        print("The model reached its token limit.")
    elif finish_reason == "content_filter":
        # This means that OpenAI blocked the message with their content filter
        print("The message contained content that was against OpenAI's policy.")


@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    api_key = request.headers["api-key"]

    # Use an API key so everyone isn't able to send audio files to the server
    if api_key != client_api_key:
        print("Invalid API key")
        return "Invalid API key", 401

    audio_file = request.files["recording"]
    global audio_file_path
    audio_file_path = "./static/recording.wav"
    audio_file.save(audio_file_path)

    # TODO: currently doesn't refresh the page. Figure out how to have the audio show up right away and not have to manually refresh the page (maybe use HTMX or AJAX)
    return "Audio uploaded successfully"


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
                audio_file = ""
                if audio_file_path != "":
                    with open(audio_file_path, "rb") as f:
                        audio_file = f

                # TODO: delete the audio file after it's been transcribed (or maybe keep all the audio files in a folder)

                if audio_file == "":
                    # Show an error if there's no audio loaded when the user clicks "Create transcript"
                    session["no_audio_modal"] = True
                elif transcript.strip() != "" and not "overwrite-transcript" in request.form:
                    # Show a warning if the user tries to overwrite an existing transcript
                    # (this will not be run if the user confirms that they want to overwrite the transcript)
                    session["overwrite_transcript_modal"] = True
                elif test_mode_enabled:
                    transcript = "This is a test transcript."
                else:
                    transcript = transcribe_audio(audio_file)

            session["transcript"] = transcript

        return redirect(url_for("transcript"))
    else:
        # Load the transcript from the session (default to empty string if it doesn't exist)
        transcript = session.get("transcript", "")

        # Default values for the modal
        show_modal = False
        modal_title = ""
        modal_body = ""
        modal_button1_text = "Okay"
        modal_button1_style = "primary"
        modal_show_danger_button = False

        # Check if any modal should be displayed then remove it from the session
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
            modal_button1_style = "secondary"
            modal_show_danger_button = True

        if any([no_audio_modal, overwrite_transcript_modal]):
            show_modal = True

        return render_template("transcript.html", transcript=transcript, test_mode_enabled=test_mode_enabled, display_modal=show_modal,
                               modal_title=modal_title, modal_body=modal_body, modal_button1_text=modal_button1_text, modal_button1_style=modal_button1_style, modal_show_danger_button=modal_show_danger_button)


@app.route("/notes", methods=["GET", "POST"])
@app.route("/notes/", methods=["GET", "POST"])
def notes():
    # TODO: when waiting for the model to respond, display a loading animation or write "Thinking..." or something

    # This is for the model selection dropdown
    selected_model = session.get("model-notes", "GPT-3.5")

    if request.method == "POST":

        if "model-notes" in request.form:
            selected_model = request.form["model-notes"]
            session["model-notes"] = selected_model
        else:
            notes = request.form.get("notes", "")

            # Check if the user clicked the "Create notes" button or confirmed that they want to overwrite the notes
            if "create-notes" in request.form or "overwrite-notes" in request.form:
                transcript = session.get("transcript", "")

                if transcript.strip() == "":
                    # Display an error if the transcript is empty
                    session["no_transcript_modal"] = True
                elif notes.strip() != "" and not "overwrite-notes" in request.form:
                    # Show a warning if the user tries to overwrite existing notes
                    session["overwrite_notes_modal"] = True
                else:
                    if selected_model == "GPT-3.5":
                        notes = transcript_to_notes(
                            transcript, "gpt-3.5-turbo")
                    elif selected_model == "GPT-4":
                        notes = transcript_to_notes(transcript, "gpt-4")
                    elif selected_model == "Test mode":
                        notes = "# These are test notes."

            session["notes"] = notes

        return redirect(url_for("notes"))
    else:
        # Load the notes from the session (default to empty string if they don't exist)
        notes = session.get("notes", "")

        # Default values for the modal
        show_modal = False
        modal_title = ""
        modal_body = ""
        modal_button1_text = "Okay"
        modal_button1_style = "primary"
        modal_show_danger_button = False

        # Check if any modal should be displayed then remove it from the session
        no_transcript_modal = session.pop("no_transcript_modal", False)
        overwrite_notes_modal = session.pop("overwrite_notes_modal", False)

        if no_transcript_modal:
            modal_title = "No transcript"
            modal_body = "There must be a transcript to create notes from. On the \"Transcript\" page please transcribe audio or paste in a transcript."
        elif overwrite_notes_modal:
            modal_title = "Overwrite notes?"
            modal_body = "Are you sure you want to overwrite the existing notes and create new ones?"
            modal_button1_text = "Cancel"
            modal_button1_style = "secondary"
            modal_show_danger_button = True

        if any([no_transcript_modal, overwrite_notes_modal]):
            show_modal = True

        return render_template("notes.html", notes=notes, selected_model=selected_model, display_modal=show_modal,
                               modal_title=modal_title, modal_body=modal_body, modal_button1_text=modal_button1_text, modal_button1_style=modal_button1_style, modal_show_danger_button=modal_show_danger_button)


@app.route("/save_notes", methods=["POST"])
def save_notes():
    # Save the notes to the session (this will run when the user manually edits the notes)
    notes = request.form.get("notes", "")
    session["notes"] = notes
    return "Success"


@app.route("/interactive-quiz", methods=["GET", "POST"])
@app.route("/interactive-quiz/", methods=["GET", "POST"])
def quiz():
    # TODO: when waiting for a response from the model, write "Thinking..." in the chat box
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
                                           modal_button1_text="Cancel", modal_button1_style="secondary", modal_button2_text="Restart",
                                           modal_button2_style="danger", modal_button2_name="restart-quiz", messages=chat_history)
                else:
                    # Reset the chat history
                    chat_history.clear()
                    session["quiz_started"] = True

            if "message" in request.form or "sample-response" in request.form:
                if "message" in request.form:
                    message = request.form.get("message", "")
                    if message.strip() == "":
                        # Don't send a blank message
                        return render_template("chat_body.html", messages=chat_history)
                elif "sample-response" in request.form:
                    message = request.form.get("sample-response", "")

                # Add the message to the chat history
                chat_history.append({"role": "user", "content": message})

            # Get the AI response if the quiz is started
            if session.get("quiz_started", False):
                notes = session.get("notes", "")
                if selected_model == "GPT-3.5":
                    ai_response = ai_chat_response(
                        chat_history, notes, "gpt-3.5-turbo")
                elif selected_model == "GPT-4":
                    ai_response = ai_chat_response(
                        chat_history, notes, "gpt-4")
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
    app.run(debug=True, host="0.0.0.0", port=5001)
