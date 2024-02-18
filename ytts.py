import requests
import wave
import sys
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
import numpy as np
from deepspeech import Model
from tqdm import tqdm
from pytube import YouTube
from pytube.exceptions import PytubeError
from pydub import AudioSegment
from setup import install_requirements


def download_model():
    """Download the model used to create the transcription"""
    model_directory = "./models"
    if not os.path.exists(model_directory):
        os.makedirs(model_directory)
    
    default_model = "https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm"

    if "--model" in sys.argv:
        model_index = sys.argv.index("--model")
        if model_index + 1 < len(sys.argv):
            model_url = sys.argv[model_index + 1]
    else:
        model_url = default_model
    
    model_filename = os.path.basename(model_url)
    model_path = os.path.join(model_directory, model_filename)

    scorer_url = model_url.replace('.pbmm', '.scorer')
    scorer_filename = model_filename.replace('.pbmm', '.scorer')
    scorer_path = os.path.join(model_directory, scorer_filename)

    files_to_download = [
        {"url": model_url, "path": model_path},
        {"url": scorer_url, "path": scorer_path}
    ]

    for file in files_to_download:
        if os.path.exists(file["path"]):
            print(f"File already exists at {file['path']}. Skipping download.")
        else:
            print(f"Downloading from {file['url']}...")
            response = requests.get(file["url"], stream=True)
            with open(file["path"], 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"Downloaded to {file['path']}")
    return model_filename

def download_audio(source_path, youtube_url):
    """Download the audio from video and convert to mono"""
    try:
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.get_audio_only()
        if not audio_stream:
            raise Exception("No audio stream found")

        filename = audio_stream.default_filename
        print(f"Downloading '{filename}'...")
        audio_stream.download(output_path=source_path)
        print(f"Downloaded '{filename}' to '{source_path}'")
        return filename
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

def transcribe_audio(model_filename, scorer_filename, audio_path, output_path):
    model_path = os.path.join('./models', model_filename)
    scorer_path = os.path.join('./models', scorer_filename)

    model = Model(model_path)
    model.enableExternalScorer(scorer_path)

    with wave.open(audio_path, 'rb') as wf:
        frames = wf.getnframes()
        buffer = wf.readframes(frames)
        audio = np.frombuffer(buffer, dtype=np.int16)

    # Split the audio into chunks and transcribe each chunk
    chunk_size = 8192  # You can adjust the chunk size
    chunks = [audio[i:i + chunk_size] for i in range(0, len(audio), chunk_size)]
    transcription = ""

    for chunk in tqdm(chunks, desc="Transcribing", unit="chunk"):
        transcription += model.stt(chunk)

    with open(output_path, 'w') as f:
        f.write(transcription)

    return transcription

def transcribe_folder(model_filename, folder_path, output_folder):
    scorer_filename = model_filename.replace('.pbmm', '.scorer')

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(folder_path):
        if filename.endswith('.wav'):
            audio_path = os.path.join(folder_path, filename)
            output_path = os.path.join(output_folder, filename.replace('.wav', '.txt'))
            print(f"Transcribing {audio_path}...")
            transcribe_audio(model_filename, scorer_filename, audio_path, output_path)
            print(f"Transcription saved to {output_path}")


def get_argument_value(argument, default=None):
    """Retrieve the value of a command-line argument."""
    try:
        index = sys.argv.index(argument)
        return sys.argv[index + 1]
    except (ValueError, IndexError):
        return default

def main():
    if "--audio" not in sys.argv:
        print("Usage: ytts.py [--skip-reqs] --audio <YouTube-URL> --person <> [--path <Download-Subfolder-Path>]")
        sys.exit(1)

    if "--skip-reqs" not in sys.argv:
        install_requirements()

    youtube_url = get_argument_value("--audio")
    person_name = get_argument_value("--person", "default")
    source_path = get_argument_value("--path", f"./{person_name}-mono/") + os.sep
    output_folder = f"./{person_name}-transcripts/"

    if not youtube_url:
        print("Error: No YouTube URL provided after --audio")
        sys.exit(1)

    print(f"Creating {source_path}")
    model_filename = download_model()
    audio_filename = download_audio(source_path, youtube_url)
    convert_to_mono(source_path, audio_filename)
    transcribe_folder(model_filename, source_path, output_folder)

if __name__ == "__main__":
    main()

# Align audio and text
# mfa align /path/to/audio /path/to/transcriptions /path/to/dictionary /path/to/output

# https://dev.to/azure/ai-using-whisper-to-convert-audio-to-text-from-my-podcast-episode-in-spanish-c96
