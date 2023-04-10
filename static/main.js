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
