from pathlib import Path
import urllib.request
import shutil
import subprocess

from rec2_bisect.paths import REC2_DEPS_ROOT, REC2_DOWNLOAD_ROOT

THIS_PATH = Path(__file__).resolve().parent

GIT_URL = "https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.2/PortableGit-2.47.1.2-64-bit.7z.exe"
GIT_ROOT = REC2_DEPS_ROOT / "git"
GIT_PATH = GIT_ROOT / "bin"
GIT_EXE_PATH = GIT_PATH / "git.exe"
GIT_ENV = {
    "PATH": str(GIT_PATH),
}

def download_extract_git() -> None:
    download_path = REC2_DOWNLOAD_ROOT / "git"
    installer_exe_path = download_path / "portable-git-installer.exe"
    shutil.rmtree(download_path, ignore_errors=True)
    download_path.mkdir(parents=True)

    shutil.rmtree(GIT_ROOT, ignore_errors=True)
    GIT_ROOT.mkdir(parents=True)

    print("[ ] Downloading git ...")
    with urllib.request.urlopen(GIT_URL) as stream:
        exe_data = stream.read()
    with installer_exe_path.open("wb") as f:
        f.write(exe_data)
    print("[x] Downloading git finished")

    print("[ ] Extracting git ...")
    subprocess.check_call([str(installer_exe_path), "-y", "-o", str(GIT_ROOT)])
    print("[x] Extracting git finished")


def has_git() -> bool:
    if not GIT_EXE_PATH.exists():
        return False
    try:
        subprocess.check_output([str(GIT_EXE_PATH), "--version"], text=True)
        return True
    except subprocess.CalledProcessError:
        return False
