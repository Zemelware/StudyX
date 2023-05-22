const recordButton = document.getElementById("record-button");
const audioPlayer = document.getElementById("audio-player");

recordButton.addEventListener("click", toggleRecording);

let chunks = [];
let mediaRecorder = null;
let audioBlob = null;

function toggleRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert(
      "Your browser does not support recording! Please use a different browser."
    );
    return;
  }

  recordButton.innerHTML =
    mediaRecorder && mediaRecorder.state === "recording" ? "Record" : "Stop";
  if (!mediaRecorder) {
    // Start recording
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.start();
        mediaRecorder.ondataavailable = mediaRecorderOnDataAvailable;
        mediaRecorder.onstop = mediaRecorderStop;
      })
      .catch((err) => {
        alert("Error: " + err);
      });
  } else {
    // Stop recording
    mediaRecorder.stop();
  }
}

function mediaRecorderOnDataAvailable(e) {
  chunks.push(e.data);
}

function mediaRecorderStop() {
  // Create a blob from the chunks
  audioBlob = new Blob(chunks, { type: "audio/mp3" });
  const audioUrl = window.URL.createObjectURL(audioBlob);
  audioPlayer.src = audioUrl;
  mediaRecorder = null;
  chunks = [];
}
