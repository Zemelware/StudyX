if (
  window.location.pathname === "/interactive-quiz" ||
  window.location.pathname === "/interactive-quiz/"
) {
  var messageField = document.querySelector("textarea[name='message']");

  messageField.addEventListener("input", () => {
    // Automatically resize the message box
    messageField.style.height = "auto";
    messageField.style.height = messageField.scrollHeight + "px";
  });

  messageField.addEventListener("keydown", submitOnEnter);
  function submitOnEnter(event) {
    // This function submits the form when the user presses enter and creates a new line when shift+enter is pressed

    // even.which === 13 checks if the enter key was pressed
    if (event.which === 13 && !event.shiftKey) {
      // event.repeat checks if the key is being held down
      if (!event.repeat) {
        var sendButton = document.getElementById("send-button");
        sendButton.click();
      }

      event.preventDefault(); // Prevents a new line from being created if the enter key is held down
    }
  }

  var messageForm = document.getElementById("message-form");
  var chatBody = document.getElementById("chat-body");
  document.body.addEventListener("htmx:afterRequest", function (event) {
    // This function is called after every HTMX request
    var elementId = event.target.id;

    // After a message is sent, clear the message field and focus on it
    if (elementId === messageForm.id) {
      messageField.value = "";
      messageField.focus();
      // Scroll to the bottom of the chat window
      chatBody.scrollTo({
        top: chatBody.scrollHeight,
        behavior: "smooth",
      });
    }
  });
}

function updateTestModeSwitch() {
  // This function updates the test mode switch on the transcript page to reflect if the switch is on or off
  var checkbox = document.getElementById("test-mode-switch");
  var hiddenField = document.getElementById("test-mode-hidden");

  if (checkbox.checked) {
    hiddenField.value = "on";
  } else {
    hiddenField.value = "off";
  }
}
