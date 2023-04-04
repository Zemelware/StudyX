import os

import openai
from flask import Flask, redirect, render_template, request, session, url_for
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = API_KEY

app = Flask(__name__)
app.secret_key = os.urandom(24)

chat_history = []


def get_ai_response(message):
    # Make an API call to OpenAI to get the AI response
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            *chat_history,
            {"role": "user", "content": message}
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

# TODO: add message support for multiple lines


@app.route("/", methods=["GET", "POST"])
@app.route("/interactive-quiz", methods=["GET", "POST"])
@app.route("/interactive-quiz/", methods=["GET", "POST"])
def chat():
    global chat_history

    # TODO: make sure that the user has to wait for the AI to respond before they can send another message
    if request.method == "POST":
        # First retrieve the message from the form
        message = request.form["message"]
        if message.strip() == "":
            # Don't send a blank message
            return redirect(url_for("chat"))

        # Add the message to the chat history
        chat_history.append({"role": "user", "content": message})

        # Get the AI response
        ai_response = get_ai_response(message)
        # Add the AI response to the chat history
        chat_history.append({"role": "assistant", "content": ai_response})

        print(chat_history)

        session["chat_history"] = chat_history

        # Redirect to the chat page to prevent form resubmission if the user refreshes the page
        return redirect(url_for("chat"))
    else:
        if "chat_history" in session:
            # If the user has already been chatting with the AI, then we want to retrieve the chat history from the session
            chat_history = session["chat_history"]
        else:
            # Otherwise, start with an empty chat history
            chat_history = []

        # Render the chat page with the chat history
        return render_template("chat.html", messages=chat_history)


if __name__ == "__main__":
    app.run(debug=True)
