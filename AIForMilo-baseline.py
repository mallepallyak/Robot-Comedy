# BASELINE MILO SCRIPT (NO DUAL PROMPTING)

import socket
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
import threading
import re

# ------------------ CONFIG ------------------

# Load the local .env beside these scripts; existing environment variables take precedence.
load_dotenv(Path(__file__).resolve().parent / ".env")
openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
if not openai_api_key or openai_api_key == "your_openai_api_key_here":
    raise RuntimeError("Set OPENAI_API_KEY in .env (copy .env.example first).")

BRIDGE_HOST = 'localhost'
BRIDGE_PORT = 10000

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="EMPTY"
)

whisper_client = OpenAI(api_key=openai_api_key)

RATE = 16000
CHANNELS = 1
FILENAME = "user_recording.wav"

baseline_conversation = []

# ------------------ BASELINE PROMPT ------------------

BASELINE_PROMPT = """
You are MILO, a stand-up comedian robot.

### Behavior Rules
- Keep responses short (2–4 sentences)
- Always reference something the user said
- Avoid repeating previous jokes
- No generic humor
- Do NOT include stage directions like *chuckles*, *winks*, etc.
- Use natural spoken tone instead.

### Style
- self-deprecating
- light teasing (safe)
- surprise/twist

### Interaction
- Say something funny
- Optionally ask ONE short question

### Output
Respond with ONLY the spoken line.
"""

# ------------------ BASELINE LLM ------------------

def send_to_Baseline(user_input):

    if len(baseline_conversation) == 0:
        baseline_conversation.append({
            "role": "system",
            "content": BASELINE_PROMPT
        })
    baseline_conversation.append({
        "role": "user",
        "content": user_input
    })

    # keep short memory (prevents repetition)
    # if len(baseline_conversation) > 6:
    #     baseline_conversation[:] = [baseline_conversation[0]] + baseline_conversation[-5:]

    response = client.chat.completions.create(
        model="llama3.1",
        messages=baseline_conversation,
        temperature=0.8,
        max_tokens=80
    )

    assistant_message = response.choices[0].message.content

    # remove stage directions
    assistant_message = re.sub(r"\*.*?\*", "", assistant_message)
    assistant_message = re.sub(r"\s+", " ", assistant_message).strip()

    baseline_conversation.append({
        "role": "assistant",
        "content": assistant_message
    })

    print("🤖 Milo (Baseline):", assistant_message)
    return assistant_message

# ------------------ AUDIO ------------------

def record_until_enter():
    print("🎤 Recording... press Enter to stop")

    frames = []
    stop_flag = {"stop": False}

    def stop():
        input()
        stop_flag["stop"] = True

    threading.Thread(target=stop, daemon=True).start()

    stream = sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16')
    stream.start()

    while not stop_flag["stop"]:
        data, _ = stream.read(1024)
        frames.append(data.copy())

    stream.stop()
    stream.close()

    audio = np.concatenate(frames, axis=0)
    wavfile.write(FILENAME, RATE, audio)
    print("Saved:", FILENAME)

def transcribe_audio():
    print("Transcribing...")
    with open(FILENAME, "rb") as f:
        transcript = whisper_client.audio.transcriptions.create(
            model="whisper-1",
            language="en",
            file=f
        )
        print("🧑:", transcript.text)
        return transcript.text


def send_to_milo(message):
    try:
        with socket.create_connection((BRIDGE_HOST, BRIDGE_PORT)) as sock:
            print("Connected to Java bridge.")
            payload = message + "\n"
            sock.sendall((payload).encode('utf-8'))
            # time.sleep(0.2)
            sock.shutdown(socket.SHUT_WR)
    except Exception as e:
        print("Socket error:", e)

# ------------------ MAIN ------------------

def main():
    print("Baseline Mode: Press 'r' to speak, 'quit' to exit.\n")

    while True:
        cmd = input(">>> ").strip().lower()

        if cmd == "r":
            record_until_enter()
            text = transcribe_audio()

            response = send_to_Baseline(text)

            # uncomment if connected to Milo
            send_to_milo(response)

        elif cmd == "quit":
            print("Exiting.")
            break

        else:
            print("Unknown command. Use 'r' or 'quit'.")

if __name__ == "__main__":
    main()