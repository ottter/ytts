import subprocess
import sys
import os
import pkg_resources

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

def download_audio(youtube_url, output_path):
    output_template = output_path + "%(title)s.%(ext)s"
    command = [
        "youtube-dl",
        "--extract-audio",
        "--audio-format", "wav",
        "-o", output_template,
        youtube_url
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.splitlines()
        downloaded_file = ""
        for line in lines:
            if "[ffmpeg] Destination:" in line:
                downloaded_file = line.split(": ")[1]
                break

        if downloaded_file:
            mono_file = downloaded_file.replace(".wav", "_mono.wav")
            ffmpeg_command = ["ffmpeg", "-i", downloaded_file, "-ac", "1", mono_file]
            subprocess.run(ffmpeg_command)
            print(f"Converted to mono: {mono_file}")
        else:
            print("Error: Could not determine downloaded file name.")
    else:
        print("Error: youtube-dl command failed.")

if __name__ == "__main__":
    if "--audio" not in sys.argv:
        print("Usage: ytts.py [--skip-reqs] --audio <YouTube-URL> [--path <Download-Path>]")
        sys.exit(1)

    if "--skip-reqs" not in sys.argv:
        install_requirements()

    audio_index = sys.argv.index("--audio")
    if audio_index + 1 < len(sys.argv):
        youtube_url = sys.argv[audio_index + 1]
        output_path = ""
        if "--path" in sys.argv:
            path_index = sys.argv.index("--path")
            if path_index + 1 < len(sys.argv):
                output_path = sys.argv[path_index + 1]
                if not output_path.endswith(os.sep):
                    output_path += os.sep
        download_audio(youtube_url, output_path)
    else:
        print("Error: No YouTube URL provided after --audio")
        sys.exit(1)


# Convert the audio to mono
# ffmpeg -i input.wav -ac 1 output_mono.wav

# Automatic speech recognition
# deepspeech --model deepspeech-0.9.3-models.pbmm --scorer deepspeech-0.9.3-models.scorer --audio output_mono.wav > transcription.txt

# Align audio and text
# mfa align /path/to/audio /path/to/transcriptions /path/to/dictionary /path/to/output


