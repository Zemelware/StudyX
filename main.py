import os

from flask import Flask, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

message_history = []

# TODO: create a field for the API key


def get_ai_response(message):
    return "Hi"


@app.route("/", methods=["GET", "POST"])
@app.route("/interactive-quiz", methods=["GET", "POST"])
@app.route("/interactive-quiz/", methods=["GET", "POST"])
def chat():
    global message_history

    # TODO: make sure that the user has to wait for the AI to respond before they can send another message
    if request.method == "POST":
        # First retrieve the message from the form
        message = request.form["message"]
        if message.strip() == "":
            # Don't send a blank message
            return redirect(url_for("chat"))

        # Add the message to the message history
        message_history.append({"message": message, "sender": "user"})

        # Get the AI response
        ai_response = get_ai_response(message)
        # Add the AI response to the message history
        message_history.append({"message": ai_response, "sender": "ai"})

        session["message_history"] = message_history

        # Redirect to the chat page to prevent form resubmission if the user refreshes the page
        return redirect(url_for("chat"))
    else:
        if "message_history" in session:
            # If the user has already been chatting with the AI, then we want to retrieve the message history from the session
            message_history = session["message_history"]
            # Render the chat page with the message history
            return render_template("chat.html", messages=message_history)
        else:
            return render_template("chat.html", messages=[])


if __name__ == "__main__":
    app.run(debug=True)
