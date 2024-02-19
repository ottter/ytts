from setup import install_requirements

import sys
import os
import time
import shutil
import whisper
import warnings
from tqdm import tqdm
from pytube import YouTube
from pytube.exceptions import PytubeError
from pydub import AudioSegment
from pydub.silence import split_on_silence


warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead", module="whisper")


def download_audio(source_path, youtube_url):
    """Download the audio from video and convert to mono"""
    try:
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.get_audio_only()
        if not audio_stream:
            raise Exception("No audio stream found")

        # Check if the corresponding .wav file already exists
        wav_filename = "mono_" + os.path.splitext(audio_stream.default_filename)[0] + ".wav"
        if os.path.exists(os.path.join(source_path, wav_filename)):
            print(f"Skipping download, '{wav_filename}' already exists.")
            return wav_filename

        print(f"Downloading '{audio_stream.default_filename}' from {youtube_url}...")
        audio_stream.download(output_path=source_path)
        print(f"Downloaded '{audio_stream.default_filename}' to '{source_path}'")
        return audio_stream.default_filename
    except PytubeError as e:
        print(f"Error: Failed to download audio from '{youtube_url}'. {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def convert_to_mono(source_path, filename):
    file_path = os.path.join(source_path, filename)
    audio = AudioSegment.from_file(file_path)
    mono_audio = audio.set_channels(1)
    mono_filename = 'mono_' + filename.replace('.mp4', '.wav')
    mono_file_path = os.path.join(source_path, mono_filename)
    mono_audio.export(mono_file_path, format="wav")

    print(f"Converted '{filename}' to mono, creating '{mono_filename}")
    os.remove(file_path)
    print(f"Deleted '{filename}'")
    return mono_filename

def transcribe_audio(audio_path, output_folder, model_name="base", silence_thresh=-40, min_silence_len=700, keep_silence=500):
    start_time = time.time()

    # Load the Whisper model
    model = whisper.load_model(model_name)

    # Load the audio file using pydub
    audio = AudioSegment.from_file(audio_path)

    # Split the audio into chunks based on silence
    audio_chunks = split_on_silence(
        audio,
        silence_thresh=silence_thresh,      # Adjust this value based on your audio file
        min_silence_len=min_silence_len,    # The minimum length of silence in ms
        keep_silence=keep_silence           # The amount of silence to leave at the beginning and end of each chunk in ms
    )

    transcription = ""
    count = len(audio_chunks)

    x = 50  # The threshold for the total number of chunks
    y = 2  # The number of chunks to process at the beginning and end if there are more than x chunks

    for i, chunk in enumerate(tqdm(audio_chunks, desc="Transcribing", unit="chunk")):
        if len(audio_chunks) <= x or (i < y or i >= len(audio_chunks) - y):
            base_filename = os.path.splitext(os.path.basename(audio_path))[0]
            out_wav = os.path.join(output_folder, f"{i+1:03d}_{base_filename}.wav")
            out_txt = os.path.join(output_folder, f"{i+1:03d}_{base_filename}.txt")

            print(f"\r\nExporting >> {out_wav} - {i+1}/{count}")
            chunk.export(out_wav, format="wav")

            try:
                result = model.transcribe(out_wav)
                transcript_chunk = result["text"]
                print(transcript_chunk)

                # Append transcript in memory if you have sufficient memory
                transcription += " " + transcript_chunk

                with open(out_txt, 'w') as f:
                    f.write(transcript_chunk)
            except UnicodeEncodeError:
                print(f"Skipping transcription of {out_wav} due to UnicodeEncodeError")
                os.remove(out_wav)  # Delete the chunk and continue
                continue
    
    print(f"Transcript:\n{transcription}\n")

    # print the elapsed time
    print(f"Elapsed time: {int(time.time() - start_time)} seconds")

    return transcription

def transcribe_folder(mono_folder, output_folder, model_name="base"):
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate through each file in the folder
    for file in os.listdir(mono_folder):
        if file.endswith(".wav"):
            # Construct the paths for the audio file and its corresponding transcription file
            audio_path = os.path.join(mono_folder, file)
            transcription_file = os.path.splitext(file)[0] + ".txt"
            output_path = os.path.join(output_folder, transcription_file)

            # Check if the transcription file already exists
            if not os.path.exists(output_path):
                print(f"Transcribing {audio_path}...")
                # Transcribe the audio file
                transcribe_audio(audio_path, output_folder, model_name=model_name)
            else:
                print(f"Skipping {audio_path}, transcription already exists.")


def get_argument_value(argument, default=None):
    """Retrieve the value of a command-line argument."""
    try:
        index = sys.argv.index(argument)
        return sys.argv[index + 1]
    except (ValueError, IndexError):
        return default

def main():
    if len(sys.argv) < 3:
        print("Usage: ytts.py transcribe <YouTube-URL> --person <Person-Name> [--path <Download-Subfolder-Path>]")
        sys.exit(1)

    command = sys.argv[1]
    commands = {
        "transcribe": transcribe_command,
        "clear": clear_command,
        "delete": clear_command,
        "update": update_command,
        "tts": tts_command
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

def transcribe_command():
    youtube_url = sys.argv[2]
    person_name = get_argument_value("--person", "default")
    mono_folder = get_argument_value("--path", f"./{person_name}-mono/") + os.sep
    output_folder = f"./{person_name}-transcripts/"

    audio_filename = download_audio(mono_folder, youtube_url)
    convert_to_mono(mono_folder, audio_filename)
    transcribe_folder(mono_folder, output_folder, model_name="base")

def clear_command():
    person_name = sys.argv[2]
    if not person_name:
        print("Error: No person name provided after 'clear' command")
        sys.exit(1)

    mono_folder = f"./{person_name}-mono/"
    output_folder = f"./{person_name}-transcripts/"
    if os.path.exists(mono_folder):
        print(f"Deleting {mono_folder}...")
        shutil.rmtree(mono_folder)
        print(f"Deleting {output_folder}...")
        shutil.rmtree(output_folder)
    else:
        print(f"Folder {mono_folder} does not exist.")

def update_command():
    install_requirements()

def tts_command():
    print("not yet...")
    sys.exit(0)

if __name__ == "__main__":
    main()

# Align audio and text
# mfa align /path/to/audio /path/to/transcriptions /path/to/dictionary /path/to/output

# https://dev.to/azure/ai-using-whisper-to-convert-audio-to-text-from-my-podcast-episode-in-spanish-c96
