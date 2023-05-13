import wave

import pyaudio
import RPi.GPIO as GPIO

from send_audio_to_server import send_audio_to_server

LED_PIN = 19
BUTTON_PIN = 16

recording = False
led_on = False

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

chunk = 4096
sample_format = pyaudio.paInt16
channels = 1
fs = 44100
filename = "recording.wav"

p = pyaudio.PyAudio()


stream = p.open(format=sample_format,
                channels=channels,
                rate=fs,
                frames_per_buffer=chunk,
                input=True)

frames = []  # Initialize array to store frames

button_down = False
while not recording:
    if not button_down:
        button_down = True
        recording = GPIO.input(BUTTON_PIN) == GPIO.HIGH
        print("button on: " + str(recording))


# Recording loop
while recording:
    # Check if the LED is off. If so, turn it on.
    if not led_on:
        led_on = True
        GPIO.output(LED_PIN, GPIO.HIGH)
        print("LED on")

    # Check if the button is pressed again. If so, turn the LED off and break out of the loop.
    if GPIO.input(BUTTON_PIN) == GPIO.HIGH and not button_down:
        # Turn the LED off
        recording = False
        GPIO.output(LED_PIN, GPIO.LOW)

        led_on = False
        break

    data = stream.read(chunk)
    frames.append(data)

    button_down = False

# Stop and close the stream
stream.stop_stream()
stream.close()
# Terminate the PortAudio interface
p.terminate()


# Save the recorded data as a WAV file
wf = wave.open(filename, 'wb')
wf.setnchannels(channels)
wf.setsampwidth(p.get_sample_size(sample_format))
wf.setframerate(fs)
wf.writeframes(b''.join(frames))
wf.close()

send_audio_to_server(filename)
