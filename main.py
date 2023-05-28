import argparse
import io
import os
from datetime import datetime, timedelta
from queue import Queue
from subprocess import Popen
from tempfile import NamedTemporaryFile
from time import sleep

import speech_recognition as sr
import torch
import whisper
import pyttsx3


def parse_arguments() -> argparse.Namespace:
    """TODO: Docstring for parse_arguments.
    :returns: TODO

    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="base", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=1000,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=2,
                        help="How real time the recording is in seconds.",
                        type=float)
    parser.add_argument("--phrase_timeout", default=3,
                        help="How much empty space between recordings before we"
                             "consider it a new line in the transcription.",
                        type=float)
    return parser.parse_args()


def load_model(model: str, non_english: str) -> whisper.Whisper:
    """
    Load/download whisper model.
    :model: The name of the model to load.
    :non_english: Whether to load the english model or not.
    :returns: The loaded Whisper model.
    """
    if model != "large" and not non_english:
        model = model + ".en"
    return whisper.load_model(model)


def notify(message: str) -> None:
    """TODO: Docstring for notify.

    :message: TODO
    :returns: None

    """
    speak(message)
    # Popen(["espeak", message])
    # Popen(["notify-send", "listenMe", message])


def speak(message: str) -> None:
    """TODO: Docstring for speak.

    :message: TODO
    :returns: TODO

    """
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()

    # Convert the text to speech
    engine.say(message)

    # Wait for the speech to finish and clean up resources
    engine.runAndWait()
    engine.stop()


def command(text: str) -> None:
    """TODO: Docstring for command.

    :text: TODO
    :command: TODO
    :returns: TODO

    """
    commands = [
        ["open terminal", "st", "Terminal opened."],
        ["open monitor", "st -e btop", "Monitor opened."],
        ["open browser", "firefox", "Browser opened."],
        ["open file manager", "st -e nnn", "File manager opened."],
        ["open editor", "st -e nvim", "Editor opened."],
        ["open telegram", "telegram-desktop", "Telegram opened."],
        ["close window", "xdotool getactivewindow windowkill", "Window closed."],
    ]
    command_executed = False
    for cmd in commands:
        if cmd[0] in text:
            command_executed = True
            try:
                Popen(cmd[1].split(), stdout=open(os.devnull, 'wb'),
                      stderr=open(os.devnull, 'wb'))
                notify(cmd[2])
            except FileNotFoundError:
                notify(f"Command {cmd[0]} not working.")
            break
    if not command_executed:
        notify("Not found.")


def main():
    args = parse_arguments()
    # The last time a recording was retreived from the queue.
    phrase_time = None
    # Current raw audio bytes.
    last_sample = bytes()
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice
    # feauture where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    # Definitely do this, dynamic energy compensation lowers the energy
    # threshold dramtically to a point where the SpeechRecognizer never stops
    # recording.
    recorder.dynamic_energy_threshold = False

    source = sr.Microphone(sample_rate=16000)

    audio_model = load_model(args.model, args.non_english)

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    temp_file = NamedTemporaryFile().name
    transcription = ['']

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData) -> None:
        """
        Threaded callback function to recieve audio data when recordings
        finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(
        source, record_callback, phrase_time_limit=record_timeout)

    # Cue the user that we're ready to go.
    print("Model loaded.\n")

    while True:
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings, consider the
                # phrase complete. Clear the current working audio buffer to
                # start over with the new data.
                if phrase_time and now - phrase_time > timedelta(seconds=phrase_timeout):
                    last_sample = bytes()
                    phrase_complete = True
                # This is the last time we received new audio data from the
                # queue.
                phrase_time = now

                # Concatenate our current audio data with the latest audio
                # data.
                while not data_queue.empty():
                    data = data_queue.get()
                    last_sample += data

                # Use AudioData to convert the raw data to wav data.
                audio_data = sr.AudioData(
                    last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                # Write wav data to the temporary file as bytes.
                with open(temp_file, 'w+b') as f:
                    f.write(wav_data.read())

                # Read the transcription.
                result = audio_model.transcribe(
                    temp_file, fp16=torch.cuda.is_available())
                text = result['text'].strip()

                # Check if the transcription is a command.
                if "command" in text.lower():
                    command(text.lower())
                    phrase_complete = True

                # If we detected a pause between recordings, add a new item to
                # our transcripion. Otherwise edit the existing one.
                if phrase_complete:
                    transcription.append(text)
                else:
                    transcription[-1] = text

                # Clear the console to reprint the updated transcription.
                os.system('cls' if os.name == 'nt' else 'clear')
                for line in transcription:
                    print(line)
                # Flush stdout.
                print('', end='', flush=True)

                # Infinite loops are bad for processors, must sleep.
                sleep(0.25)
        except KeyboardInterrupt:
            break

    # Clear the console and print the final transcription.
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\n\nTranscription:")
    for line in transcription:
        print(line)


if __name__ == "__main__":
    main()
