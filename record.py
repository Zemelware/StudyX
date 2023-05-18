import os
import wave
from time import sleep
from pydub import AudioSegment

import pyaudio
import RPi.GPIO as GPIO

recording = False
led_on = False

LED_PIN = 19
BUTTON_PIN = 16

# Setup the pins
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Initialize some variables for pyaudio
chunk = 4096
sample_format = pyaudio.paInt16
channels = 1
fs = 44100
filename = "static/recording.wav"

p = pyaudio.PyAudio()

while True:

    frames = []  # Initialize array to store frames

    while not recording:
        # Check if the button was pressed
        if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            stream = p.open(format=sample_format,
                            channels=channels,
                            rate=fs,
                            frames_per_buffer=chunk,
                            input=True)
            recording = True
            sleep(0.5)


# Recording loop
    while recording:
        data = stream.read(chunk, exception_on_overflow=False)
        frames.append(data)

        # Check if the LED is off. If so, turn it on.
        if not led_on:
            led_on = True
            GPIO.output(LED_PIN, GPIO.HIGH)

        # Check if the button is pressed again. If so, turn the LED off and break out of the loop.
        if GPIO.input(BUTTON_PIN) == GPIO.HIGH:
            # Turn the LED off
            GPIO.output(LED_PIN, GPIO.LOW)
            led_on = False

            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            # Terminate the PortAudio interface
            # p.terminate()
            
            # Save the recorded data as a WAV file
            wf = wave.open(filename, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b''.join(frames))
            wf.close()

            filename_mp3 = filename.split(".")[0] + "mp3"
            # Boost the audio to make it louder
            song = AudioSegment.from_wav(filename)
            song = song + 35  # Number of DB to increase by
            song.export(filename_mp3, format="mp3")

            os.remove(filename)

            recording = False

