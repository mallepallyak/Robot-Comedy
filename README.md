# Milo Conversation Experiment

Compare two ways of generating conversational comedy with the Milo robot:

- **Baseline:** a single prompt generates Milo’s response.
- **Personalized:** a scriptwriter identifies user context and a humor strategy before a comedian generates the response.

Both conditions use local Llama 3.1 through Ollama, OpenAI Whisper for transcription, and a Java socket bridge to make Milo speak.

## 1. Get the project

Clone the repository using its actual URL:

```sh
git clone <repository-url>
cd <repository-folder>
```

Run the commands below from this project folder.

The main files are:

```text
AIForMilo-baseline.py          Baseline condition
AIForMilo-personalized.py      Personalized condition
src/main/java/
  MiloSocketBridge.java       Sends generated speech to Milo
requirements.txt              Python dependencies
.env.example                  API key configuration template
```

## 2. Set up Python

Use Python 3 with virtual environment support.

### macOS / Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` in a text editor and replace the placeholder with your own OpenAI API key with access to audio transcription:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
```

Both Python scripts load this file automatically. An existing `OPENAI_API_KEY` environment variable takes precedence.

`.env` is ignored by Git. Commit only `.env.example`.

Allow microphone access for your terminal or Python application when prompted.

## 3. Install and start Ollama

Install Ollama for your operating system from the [official download page](https://ollama.com/download), then start the application.

Download the model:

```sh
ollama pull llama3.1
```

Check that it is available:

```sh
ollama list
```

Test a response:

```sh
ollama run llama3.1 "Say hello in one sentence."
```

See the [Ollama CLI documentation](https://docs.ollama.com/cli) and [Llama 3.1 model page](https://ollama.com/library/llama3.1).

The Python scripts expect Ollama at:

```text
http://localhost:11434/v1
```

If Ollama is not running in the background, start its server in a separate terminal:

```sh
ollama serve
```

Leave it running. If the address is already in use, check whether Ollama is already running.

Keep the same downloaded model for both experimental conditions.

## 4. Configure the Milo connection

Power on Milo and ensure network connection.

Open:

```text
src/main/java/MiloSocketBridge.java
```

Update these settings near the top:

```java
public static final int BRIDGE_PORT = 10000;
public static final String MILO_IP = "YOUR_MILO_IP";
public static final int MILO_PORT = 4001;

public static final String LOCAL_IP = "YOUR_COMPUTER_INTERFACE_IP";
```

- `MILO_IP` is the robot’s reachable network address.
- `LOCAL_IP` is an address assigned to your computer’s network interface used to reach Milo.
- `MILO_PORT` is the robot command port.
- `BRIDGE_PORT` is the port on which Java receives text from Python.

The existing addresses are specific to the original setup and must be checked before use.

For the instructions here, run Python, Ollama, and Java on the same computer. Keep the Python settings as:

```python
BRIDGE_HOST = "localhost"
BRIDGE_PORT = 10000
```

## 5. Start the Java bridge

Install a Java Development Kit (JDK) if needed. Java 21 was used to check compilation.

In a separate terminal, open the project folder and check Java:

```sh
java -version
javac -version
```

Compile and run the bridge:

```sh
cd src/main/java
javac MiloSocketBridge.java
java MiloSocketBridge
```

Use the `.java` extension when compiling and omit it when running. Recompile after changing the IP addresses or other code. The bridge uses only Java’s built-in libraries, so no external Java dependencies are needed.

Wait for:

```text
Milo Bridge running on port 10000
Waiting for Python connection...
```

Leave this terminal running.

**This message confirms the bridge is listening.** It connects to Milo when Python sends a response, so the robot connection is checked during the next step.

## 6. Test the complete system

In another terminal, open the project folder and activate the Python environment.

Start either condition for a practice run:

```sh
python AIForMilo-baseline.py
```

At the prompt:

1. Type `r` and press Enter.
2. Speak a short sentence.
3. Press Enter again to stop recording.
4. Wait for transcription and response generation.
5. Confirm that Milo speaks the response.

Check both terminals:

- Python should print the transcript and generated response.
- Java should report that it connected to Milo and sent the speech.

Type `quit` to end the practice run. **Restart the Python script before collecting experiment data**, so practice conversation history is cleared.

## 7. Run an experiment session


### Before the participant starts

1. Confirm Ollama and the Java bridge are running.
2. Check microphone placement and Milo’s speech volume.
3. Record the participant ID, assigned condition, session order, and planned duration or number of turns.
4. Keep the model, equipment, instructions, and stopping rule consistent across conditions.
5. Start a fresh Python process for the assigned condition.

### Select the condition

**Baseline:**

```sh
python AIForMilo-baseline.py
```

**Personalized:**

```sh
python AIForMilo-personalized.py
```

Run one condition at a time.

### Conduct each conversation turn

1. Type `r` and press Enter.
2. Let the participant speak.
3. Press Enter to stop recording.
4. Wait while the system transcribes, generates a response, and sends it to Milo.
5. Allow Milo to finish speaking before starting the next recording.
6. Repeat until the session’s stopping rule is reached.

Use `r` in both scripts, even if the personalized script’s startup message says `record`.

### Finish the condition

1. Type `quit`.
2. Collect the ratings or questionnaire specified by the study.
3. Save your session notes and any required terminal output.
4. Record transcription errors, connection failures, or interruptions.

The application does **not** automatically save a full transcript, timings, ratings, or participant records. Arrange data collection before the session. `user_recording.wav` is overwritten on every turn.

### Start another condition or participant

Start the appropriate Python script again. Conversation history and personalized user context reset when the Python process restarts.

Ollama and the Java bridge can remain running between sessions.

Follow the study’s assigned order and restart Python between conditions.

### Shut down

- Python: type `quit`.
- Java bridge: press `Ctrl+C` in its terminal.
- Manually started Ollama server: press `Ctrl+C` in its terminal.

## 8. Troubleshooting

| Problem | What to check |
|---|---|
| Missing API key error | Check `.env` beside the scripts and replace its placeholder. |
| Transcription authentication or quota error | Check the OpenAI key and account API access. |
| Cannot connect to Ollama | Start Ollama and verify it is available on port `11434`. |
| Model not found | Run `ollama pull llama3.1`. |
| Python reports connection refused on port `10000` | Start the Java bridge and check that both programs use the same port. |
| Java reports `Cannot assign requested address` | Set `LOCAL_IP` to an address actually assigned to your computer. |
| Java reports Milo is unreachable | Check robot power, robot IP, network/VPN connection, and port `4001`. |
| Python prints a response but Milo is silent | Check the Java terminal for robot connection or sending errors. |
| Microphone error or empty recording | Check microphone permissions and the default input device; allow time to record before pressing Enter. |
| PortAudio error | Check the operating-system audio dependencies required by `sounddevice`. |
| `java` or `javac` cannot be found | Check that a JDK is installed and its commands are available on your terminal’s PATH. |
| Java cannot find `MiloSocketBridge` | Run the commands from `src/main/java` and compile successfully before running `java MiloSocketBridge`. |

## 9. Experiment notes

Both conditions retain conversation history during a running session. The personalized condition also accumulates extracted user context.

Responses vary between runs. For reproducibility, record the repository revision, model ID from `ollama list`, software versions, session length, and condition order. Avoid updating the model or changing prompts during data collection.

Internet access is needed to download dependencies and models, and during the experiment for Whisper transcription. Participant audio is sent to OpenAI for transcription; generated conversation uses the local Ollama model. Account for this data flow in the study’s participant information and data-handling procedure.
