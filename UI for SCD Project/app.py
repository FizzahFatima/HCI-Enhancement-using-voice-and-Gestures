from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import speech_recognition as sr

import threading
import os

from gesture_detector import GestureDetector

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# --- Routes ---
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/voice")
def voice():
    return render_template("voice.html")

@app.route("/gesture")
def gesture():
    return render_template("gesture.html")

@app.route("/Text_Speech")
def Text_Speech():
    return render_template("Text_Speech.html")

@app.route("/settings")
def settings():
    return render_template("settings.html")

# Voice listen API
@app.route("/listen", methods=["POST"])
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        audio_data = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        text = "Could not understand audio"
    except sr.RequestError:
        text = "Google API unavailable"

    return jsonify({"status": "success", "text": text})

 # gesture dector
gesture_detector = None
gesture_thread = None

@socketio.on("start_gesture")
def start_gesture():
    global gesture_detector, gesture_thread

    print("Gesture start signal received")

    if gesture_detector is None:
        gesture_detector = GestureDetector(socketio)

    if gesture_thread is None or not gesture_thread.is_alive():
        gesture_thread = threading.Thread(target=gesture_detector.start, daemon=True)
        gesture_thread.start()

    emit("gesture_status", {"status": "started"})


@socketio.on("stop_gesture")
def stop_gesture():
    global gesture_detector

    print("Gesture stop signal received")

    if gesture_detector:
        gesture_detector.stop()
        gesture_detector = None

    emit("gesture_status", {"status": "stopped"})


@socketio.on("connect")
def handle_connect():
    print("Client connected")


@socketio.on("disconnect")
def handle_disconnect():
    global gesture_detector

    print("Client disconnected")

    if gesture_detector:
        gesture_detector.stop()
        gesture_detector = None


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
