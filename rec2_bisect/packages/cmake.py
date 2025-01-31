import io
import os.path
from pathlib import Path
import urllib.request
import shutil
import subprocess
import zipfile

from rec2_bisect.paths import REC2_DEPS_ROOT, REC2_DOWNLOAD_ROOT

THIS_PATH = Path(__file__).resolve().parent

CMAKE_URL = "https://github.com/Kitware/CMake/releases/download/v3.31.4/cmake-3.31.4-windows-x86_64.zip"
CMAKE_ROOT = REC2_DEPS_ROOT / "cmake"
CMAKE_PATH = CMAKE_ROOT / "bin"
CMAKE_EXE_PATH = CMAKE_PATH / "cmake.exe"
CMAKE_ENV = {
    "PATH": str(CMAKE_PATH),
}


def download_extract_cmake() -> None:
    download_path = REC2_DOWNLOAD_ROOT / "cmake"
    shutil.rmtree(download_path, ignore_errors=True)
    download_path.mkdir(parents=True)

    shutil.rmtree(CMAKE_ROOT, ignore_errors=True)
    CMAKE_ROOT.mkdir(parents=True)

    print("[ ] Downloading CMake ...")
    with urllib.request.urlopen(CMAKE_URL) as stream:
        zip_data = stream.read()
    _, filename = CMAKE_URL.rsplit("/", 1)
    cmake_basename, _ = os.path.splitext(filename)
    print("[x] Downloading CMake finished")
    print("[ ] Extracting CMake ...")
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        lprefix = f"{cmake_basename}/"
        for arcname in zf.namelist():
            target_filename = arcname.removeprefix(lprefix)
            target_path = CMAKE_ROOT / target_filename
            if arcname.endswith("/"):
                target_path.mkdir(exist_ok=True)
                continue
            data = zf.read(arcname)
            with open(target_path, "wb") as f:
                f.write(data)
    print("[x] Extracting CMake finished")


def has_cmake() -> bool:
    if not CMAKE_EXE_PATH.exists():
        return False
    try:
        subprocess.check_output([str(CMAKE_EXE_PATH), "--version"], text=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
