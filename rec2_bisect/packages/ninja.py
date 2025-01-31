import io
from pathlib import Path
import urllib.request
import shutil
import subprocess
import zipfile

from rec2_bisect.paths import REC2_DEPS_ROOT, REC2_DOWNLOAD_ROOT

THIS_PATH = Path(__file__).resolve().parent


NINJA_URL = "https://github.com/ninja-build/ninja/releases/download/v1.12.1/ninja-win.zip"
NINJA_ROOT = REC2_DEPS_ROOT / "ninja"
NINJA_PATH = NINJA_ROOT
NINJA_EXE_PATH = NINJA_ROOT / "ninja.exe"
NINJA_ENV = {
    "PATH": str(NINJA_PATH),
}


def download_extract_ninja() -> None:
    download_path = REC2_DOWNLOAD_ROOT / "ninja"
    shutil.rmtree(download_path, ignore_errors=True)
    download_path.mkdir(parents=True)

    shutil.rmtree(NINJA_ROOT, ignore_errors=True)
    NINJA_ROOT.mkdir(parents=True)

    print("[ ] Downloading ninja ...")
    with urllib.request.urlopen(NINJA_URL) as stream:
        zip_data = stream.read()
    print("[x] Downloading ninja finished")
    print("[ ] Extracting ninja ...")
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        zf.extract("ninja.exe", NINJA_ROOT)
    print("[x] Extracting ninja finished")


def has_ninja() -> bool:
    if not NINJA_EXE_PATH.exists():
        return False
    try:
        subprocess.check_output([str(NINJA_EXE_PATH), "--version"], text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
