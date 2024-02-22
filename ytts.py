"""Youtube to TTS"""
import warnings
import shutil
import sys
import os
from montreal_forced_aligner.command_line.align import run_align_corpus
from montreal_forced_aligner.config import TEMP_DIR
from setup import install_requirements
from data_prep import data_prep


warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead", module="whisper")


def align_audio(audio_path, dictionary_path, output_path):
    """"""
    # Align the audio and transcriptions
    run_align_corpus(
        corpus_directory=audio_path,
        dictionary_path=dictionary_path,
        acoustic_model_path='english',  # Use the pre-trained English model
        output_directory=output_path,
        temp_directory=TEMP_DIR,  # Temporary directory for intermediate files
        verbose=True,  # Print detailed output
        clean=True,  # Clean up intermediate files after alignment
    )


def get_argument_value(argument, default=None):
    """Retrieve the value of a command-line argument."""
    try:
        index = sys.argv.index(argument)
        return sys.argv[index + 1]
    except (ValueError, IndexError):
        return default

def main():
    """"""
    command = sys.argv[1]
    commands = {
        "transcribe": command_transcribe,
        "clear": command_clear,
        "delete": command_clear,
        "update": command_update,
        "tts": command_tts,
        "help": command_help
    }

    if command in commands:
        commands[command]()
    elif command not in commands:
        print(f"Unknown command: {command}")
        sys.exit(1)
    else:
        print("Usage: ytts.py transcribe <YouTube-URL> --person <Person-Name> [--path <Download-Subfolder-Path>]")
        sys.exit(1)

def command_transcribe():
    """"""
    youtube_url = sys.argv[2]
    person_name = get_argument_value("--person", "default")
    mono_folder = get_argument_value("--path", f"./{person_name}-mono/") + os.sep

    data_prep(mono_folder, person_name, youtube_url)

    # if not os.path.exists(alignments_output):
    #     os.makedirs(alignments_output)
    # align_audio(audio_path=transcript_output,
    #             transcriptions_path="",
    #             dictionary_path="",
    #             output_path=alignments_output)



def command_clear():
    """"""
    if len(sys.argv) < 3:
        print("Usage: ytts.py clear --person <person_name> | --name <person_name> | --audio")
        sys.exit(1)

    option = sys.argv[2]

    if option in ('--person', '--name') and len(sys.argv) >= 4:
        person_name = sys.argv[3]
        mono_folder = f"./{person_name}-mono/"
        output_folder = f"./{person_name}-transcripts/"
        if os.path.exists(mono_folder):
            print(f"Deleting {mono_folder}...")
            shutil.rmtree(mono_folder)
        if os.path.exists(output_folder):
            print(f"Deleting {output_folder}...")
            shutil.rmtree(output_folder)
    elif option == '--audio':
        print("Clearing audio files...")
    else:
        print(f"ytts.py: invalid option -- '{option[2:]}'")
        print("Usage: ytts.py clear --person <person_name> | --name <person_name> | --audio")
        sys.exit(1)

def command_update():
    """"""
    install_requirements()

def command_tts():
    """"""
    print("not yet...")
    sys.exit(0)

def command_help():
    """"""
    commands = {
        "clear": {
            "usage": "ytts.py clear --person <person_name> | --name <person_name> | --audio",
            "description": "Deletes all the specified person's content, or specific transcriptions."
        },
        "transcribe": {
            "usage": "ytts.py transcribe <audio_file> [--person <person_name>]",
            "description": "Transcribes the given audio file. Optionally, specify the person's name for personalized transcription."
        },
        "update": {
            "usage": "ytts.py update",
            "description": "Update"
        },
        "tts": {
            "usage": "ytts.py tts",
            "description": "Converts the given text to speech."
        }
    }

    print("ytts.py command usage:\n")
    for command, info in commands.items():
        print(f"{command.capitalize()}:")
        print(f"   - Usage: {info['usage']}")
        print(f"   - Description: {info['description']}\n")

    # print("For more information on a specific command, use 'ytts.py <command> --help'.")


if __name__ == "__main__":
    main()

# Align audio and text
# mfa align /path/to/audio /path/to/transcriptions /path/to/dictionary /path/to/output

# https://dev.to/azure/ai-using-whisper-to-convert-audio-to-text-from-my-podcast-episode-in-spanish-c96
