# AI backend for Milo
# Connecting and sending commands to Milo Java application

import socket
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import openai
import wave
import sounddevice as sd
import scipy.io.wavfile as wavfile
import json
import numpy as np
import threading
import re
import time

# Load the local .env beside these scripts; existing environment variables take precedence.
load_dotenv(Path(__file__).resolve().parent / ".env")
openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
if not openai_api_key or openai_api_key == "your_openai_api_key_here":
    raise RuntimeError("Set OPENAI_API_KEY in .env (copy .env.example first).")

BRIDGE_HOST = 'localhost'  # or the Java machine's IP
BRIDGE_PORT = 10000
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="EMPTY"
)
whisper_client = OpenAI(
    api_key=openai_api_key
)

global_user_context = ""

BASE_TEMPLATE = """
You are MILO, a stand-up comedian robot.

### User Context
{user_context}

### Humor Strategy
{humor_strategy}

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

scriptwriter_conversation = [
    {
        "role": "system",
        "content": """
            You are a prompt optimizer for a comedian AI.

            You DO NOT write jokes.

            ---

            ### TASK

            Given:
            - previous context
            - last comedian response
            - new user input

            Extract:

            1. USER_CONTEXT
            - key facts about the user

            2. HUMOR_STRATEGY
            - what kind of joke to make next

            ---

            ### STRICT RULES

            - Do NOT write dialogue
            - Do NOT write jokes
            - Do NOT include quotes
            - Do NOT rewrite full prompt

            ---

            ### OUTPUT FORMAT (EXACT)

            USER_CONTEXT: ...
            HUMOR_STRATEGY: ...
            """
    }
]
comedian_conversation = []


# FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
DURATION = 5
FILENAME = "user_recording.wav"

def record_audio():
    print("Recording for 5 seconds...")
    audio = sd.rec(int(DURATION * RATE), samplerate=RATE, channels=CHANNELS, dtype='int16')
    sd.wait()
    wavfile.write(FILENAME, RATE, audio)
    print("Done recording.\n")

def record_until_enter():
    print("🎤 Recording... press Enter to stop")

    frames = []
    stop_flag = {"stop": False}

    def stop_on_enter():
        input()  # waits for Enter key
        stop_flag["stop"] = True

    # start background thread to wait for Enter
    threading.Thread(target=stop_on_enter, daemon=True).start()

    stream = sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype='int16')
    stream.start()

    while not stop_flag["stop"]:
        data, _ = stream.read(1024)
        frames.append(data.copy())

    stream.stop()
    stream.close()

    audio = np.concatenate(frames, axis=0)
    wavfile.write(FILENAME, RATE, audio)
    print("✅ Saved:", FILENAME)

def transcribe_audio():
    print("Transcribing...")
    with open("user_recording.wav", "rb") as audio_file:
        transcript = whisper_client.audio.transcriptions.create(
            model="whisper-1",
            language="en",
            file=audio_file
        )
        print(transcript.text)
        return transcript.text

def get_last_assistant_message(conversation):
    for msg in reversed(conversation):
        if msg["role"] == "assistant":
            return msg["content"]
    return None

def get_last_system_prompt(conversation):
    for msg in reversed(conversation):
        if msg["role"] == "system":
            return msg["content"]
        return None

import re

def send_to_Scriptwriter(user_input):

    prev_response = get_last_assistant_message(comedian_conversation)

    messages = [
        scriptwriter_conversation[0],  # system only
        {
            "role": "user",
            "content": f"""
Last comedian response:
{prev_response}

User said:
{user_input}

Extract:

USER_CONTEXT: key facts
HUMOR_STRATEGY: what to joke about next

STRICT FORMAT:
USER_CONTEXT: ...
HUMOR_STRATEGY: ...
"""
        }
    ]

    response = client.chat.completions.create(
        model="llama3.1",
        messages=messages,
        temperature=0.5,
        max_tokens=80
    )

    output = response.choices[0].message.content.strip()
    print("Scriptwriter RAW:", output)

    # ---- ROBUST PARSE ----
    uc_match = re.search(r"USER_CONTEXT\s*:\s*(.*)", output, re.IGNORECASE)
    hs_match = re.search(r"HUMOR_STRATEGY\s*:\s*(.*)", output, re.IGNORECASE)

    user_context = uc_match.group(1).strip() if uc_match else ""
    humor_strategy = hs_match.group(1).strip() if hs_match else ""

    return user_context, humor_strategy

def send_to_Comedian(user_input, user_context, humor_strategy):

    final_prompt = BASE_TEMPLATE.format(
        user_context=user_context,
        humor_strategy=humor_strategy
    )

    if len(comedian_conversation) == 0:
        comedian_conversation.append({
            "role": "system",
            "content": final_prompt
        })
    else:
        comedian_conversation[0]["content"] = final_prompt

    comedian_conversation.append({
        "role": "user",
        "content": user_input
    })

    # # LIMIT HISTORY (fix repetition)
    # if len(comedian_conversation) > 5:
    #     comedian_conversation[:] = [comedian_conversation[0]] + comedian_conversation[-4:]

    response = client.chat.completions.create(
        model="llama3.1",
        messages=comedian_conversation,
        temperature=0.8,
        max_tokens=80
    )

    assistant_message = response.choices[0].message.content
    comedian_conversation.append({
        "role": "assistant",
        "content": assistant_message
    })

    print("comedian output is:", assistant_message)
    return assistant_message

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

def main():
    print("Type 'record' to speak. Type 'quit' to exit.\n")
    while True:
        cmd = input(">>> ").strip().lower()
        if cmd == "r":
            record_until_enter()
            text = transcribe_audio()
            
            global global_user_context
            print("Sending to scriptwriter")
            user_context_new, humor_strategy = send_to_Scriptwriter(text)

            # accumulate cleanly
            if user_context_new:
                if global_user_context:
                    global_user_context += ", " + user_context_new
                else:
                    global_user_context = user_context_new
            
            print("🔵 GLOBAL USER CONTEXT:", global_user_context)

            response = send_to_Comedian(text, global_user_context, humor_strategy)
            response = re.sub(r"\*.*?\*", "", response)
            response = re.sub(r"[\U00010000-\U0010ffff]", "", response)
            response = re.sub(r"\s+", " ", response).strip()
            send_to_milo(response)
        elif cmd == "quit":
            print("Exiting.")
            break
        else:
            print("Unknown command. Try 'record' or 'quit'.")

if __name__ == "__main__":
    main()