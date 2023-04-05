messageField = document.querySelector("textarea[name='message']");
messageField.addEventListener("input", () => {
  // Automatically resize the message box
  messageField.style.height = messageField.scrollHeight + "px";
});
