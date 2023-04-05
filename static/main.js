messageField = document.querySelector("textarea[name='message']");
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
    if (!event.repeat) {
      event.target.form.submit();
    }

    event.preventDefault(); // Prevents the addition of a new line in the text field
  }
}
