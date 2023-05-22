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
  var sampleResponses = document.getElementById("sample-responses");
  var chatBody = document.getElementById("chat-body");
  document.body.addEventListener("htmx:afterRequest", function (event) {
    // This function is called after every HTMX request
    var elementId = event.target.id;

    // This runs after a typed message is sent
    if (elementId === messageForm.id) {
      messageField.value = ""; // Clear the message field
      messageField.style.height = "auto"; // Reset the height of the message field
    }

    // This runs after a sample response is sent or a typed message is sent
    if (elementId === sampleResponses.id || elementId === messageForm.id) {
      messageField.focus(); // Focus on the message field

      // Scroll to the bottom of the chat window
      chatBody.scrollTo({
        top: chatBody.scrollHeight,
        behavior: "smooth",
      });
    }
  });
}

if (
  window.location.pathname === "/notes" ||
  window.location.pathname === "/notes/"
) {
  notesTextarea = document.getElementById("notes-textarea");
  var simplemdeNotes = new SimpleMDE({
    forceSync: true, // Sync the values of EasyMDE and the textarea
    element: notesTextarea,
    toolbar: [
      "bold",
      "italic",
      "heading",
      "|",
      "quote",
      "unordered-list",
      "ordered-list",
      "|",
      "link",
      "image",
      "table",
      "|",
      "preview",
      "side-by-side",
      "fullscreen",
      "|",
      "guide",
    ],
  });

  simplemdeNotes.togglePreview(); // Enable preview mode

  simplemdeNotes.codemirror.on("change", function () {
    // This function is called when the notes are changed

    // Send a post request to save the notes
    $.post("/save_notes", { notes: simplemdeNotes.value() });
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
