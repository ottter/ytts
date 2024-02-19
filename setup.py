import os
import sys
import subprocess
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