message_field = document.querySelector("textarea[name='message']");
message_field.addEventListener("input", autoResize, false);

function autoResize() {
  this.style.height = "auto";
  this.style.height = this.scrollHeight + "px";
}
