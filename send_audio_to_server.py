import requests

with open("recording.wav", "rb") as f:
    r = requests.post("http://localhost:5001/upload-audio",
                      files={"recording.wav": f})
