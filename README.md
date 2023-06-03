# I hear U

IhearU is a voice-controlled command and transcription tool that uses the OpenAI Whisper ASR model to transcribe and execute voice commands. The application listens to the user's speech in real-time and transcribes it, while also allowing the user to execute commands through voice input.

## Features

- Real-time transcription of speech
- Voice commands for opening and closing applications
- Adjustable parameters for energy threshold, record timeout, and phrase timeout## Requirements

- Python 3.8 or higher
- `speech_recognition` library
- `torch` library
- `whisper` library
- `pyttsx3` library

## Installation Usage

You can install the program using the following command:

```bash
git clone https://github.com/salastro/IhearU.git
pip install -e .
ihearu
```

### Optional Command-line Arguments

You can customize the behavior of the application using the following command-line arguments:

- `--model`: Model to use (choices: "tiny", "base", "small", "medium", "large", default: "base")
- `--non_english`: Don't use the English model (store_true)
- `--energy_threshold`: Energy level for mic to detect (default: 1000)
- `--record_timeout`: How real-time the recording is in seconds (default: 2)
- `--phrase_timeout`: How much empty space between recordings before it is considered a new line in the transcription (default: 3)

Example usage with arguments:

```bash
ihearu --model large --energy_threshold 1500 --record_timeout 2.5 --phrase_timeout 4
```

## Voice Commands

The following voice commands are supported:

- "open terminal"
- "open monitor"
- "open browser"
- "open file manager"
- "open editor"
- "open telegram"
- "close window"

To execute a command, say "command" followed by the desired command. For example, to open a browser, say "command open browser".

Commands are to be configured by editing the source code and reinstalling.

Default:

```python
commands = [
    ["open terminal", "st", "Terminal opened."],
    ["open monitor", "st -e btop", "Monitor opened."],
    ["open browser", "firefox", "Browser opened."],
    ["open file manager", "st -e nnn", "File manager opened."],
    ["open editor", "st -e nvim", "Editor opened."],
    ["open telegram", "telegram-desktop", "Telegram opened."],
    ["close window", "xdotool getactivewindow windowkill", "Window closed."],
]
```
