import subprocess
import requests
import wave
import sys
import os
import pkg_resources
import numpy as np
from deepspeech import Model
from pytube import YouTube
from pydub import AudioSegment


def check_requirements_installed(requirements_path):
    """Check whether requirements.txt package is already installed"""
    with open(requirements_path, 'r') as f:
        requirements = [line.strip() for line in f if line.strip()]

    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    
    missing_packages = []
    for requirement in requirements:
        package_name = requirement.split('==')[0].split('>')[0].split('<')[0]
        if package_name not in installed_packages:
            missing_packages.append(requirement)

    return missing_packages

def check_ffmpeg_installed():
    """Check if ffmpeg and ffprobe are installed and in PATH -- https://ffmpeg.org/"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["ffprobe", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print("ffmpeg and ffprobe are installed and available in PATH.")
        return True
    except:
        print("ffmpeg or ffprobe is not installed or not available in PATH.")
        sys.exit(1)

def install_requirements():
    """Install the contents of requirements.txt"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        missing_packages = check_requirements_installed(requirements_path)
        if missing_packages:
            print(f"Installing missing packages: {', '.join(missing_packages)}")
            subprocess.check_call([os.sys.executable, '-m', 'pip', 'install', *missing_packages])
        else:
            print("All packages from requirements.txt are already installed.")
    else:
        print("Error: requirements.txt file not found in the same directory as the script.")

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
        model_filename = os.path.basename(default_model)
    
    files_to_download = [
        {"url": model_url, 
         "path": os.path.join(model_directory, os.path.basename(model_url))},
        {"url": model_url.replace('.pbmm', '.scorer'), 
         "path": os.path.join(model_directory, os.path.basename(model_url.replace('.pbmm', '.scorer')))}
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

def download_audio(youtube_url, source_path):
    """Download the audio from video and convert to mono"""
    yt = YouTube(youtube_url)
    audio_stream = yt.streams.get_audio_only()
    filename = audio_stream.default_filename
    print(f"Downloaded '{filename}'")
    file_path = os.path.join(source_path, filename)
    audio_stream.download(output_path=source_path)

    # Convert to mono
    audio = AudioSegment.from_file(file_path)
    mono_audio = audio.set_channels(1)
    mono_filename = 'mono_' + filename.replace('.mp4', '.wav')
    mono_file_path = os.path.join(source_path, mono_filename)
    mono_audio.export(mono_file_path, format="wav")

    print(f"Converted '{filename}' to mono, creating '{mono_filename}")
    os.remove(file_path)
    print(f"Deleted '{filename}'")
    return mono_filename  # Return the path to the mono file

def transcribe_audio(model_filename, scorer_filename, audio_path, output_path):
    model_path = os.path.join('./models', model_filename)
    scorer_path = os.path.join('./models', scorer_filename)

    model = Model(model_path)
    model.enableExternalScorer(scorer_path)

    with wave.open(audio_path, 'rb') as wf:
        frames = wf.getnframes()
        buffer = wf.readframes(frames)
        audio = np.frombuffer(buffer, dtype=np.int16)

    transcription = model.stt(audio)

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


if __name__ == "__main__":
    if "--audio" not in sys.argv:
        print("Usage: ytts.py [--skip-reqs] --audio <YouTube-URL> [--path <Download-Path>]")
        sys.exit(1)

    if "--skip-reqs" not in sys.argv:
        install_requirements()

    check_ffmpeg_installed()

    person_index = sys.argv.index("--person")
    audio_index = sys.argv.index("--audio")

    if audio_index + 1 < len(sys.argv):
        youtube_url = sys.argv[audio_index + 1]
        person_name = sys.argv[person_index + 1]
        source_path = f"./{person_name}-mono/"
        output_folder = f"./{person_name}-transcripts/"
        if "--path" in sys.argv:
            path_index = sys.argv.index("--path")
            if path_index + 1 < len(sys.argv):
                source_path = sys.argv[path_index + 1]
                if not source_path.endswith(os.sep):
                    print(f"Creating ./{source_path}")
                    source_path += os.sep
        model_filename = download_model()
        download_audio(youtube_url, source_path)
        transcribe_folder(model_filename, source_path, output_folder)
    else:
        print("Error: No YouTube URL provided after --audio")
        sys.exit(1)

# Align audio and text
# mfa align /path/to/audio /path/to/transcriptions /path/to/dictionary /path/to/output

