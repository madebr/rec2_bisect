import shutil
import subprocess
import sys
import zipfile

from rec2_bisect.paths import REC2_DEPS_ROOT, REC2_DOWNLOAD_ROOT

PYSIDE6_ROOT = REC2_DEPS_ROOT / "pyside6"


def download_extract_pyside6() -> None:
    download_path = REC2_DOWNLOAD_ROOT / "pyside6"
    shutil.rmtree(download_path, ignore_errors=True)
    download_path.mkdir(parents=True)

    shutil.rmtree(PYSIDE6_ROOT, ignore_errors=True)
    PYSIDE6_ROOT.mkdir(parents=True)

    print("[ ] Downloading PySide6 ...")
    subprocess.check_call([
        sys.executable,
        "-m", "pip",
        "download",
        "--python-version", "39",
        "--only-binary=:all:",
        "PySide6",
    ], text=True, cwd=download_path)
    print("[x] Downloading PySide6 finished")
    for pkg in download_path.iterdir():
        with zipfile.ZipFile(pkg) as zf:
            print(f"[ ] Extracting {pkg.name} ...")
            zf.extractall(PYSIDE6_ROOT)
            print(f"[x] Extracting {pkg.name} finished")


def has_pyside6() -> bool:
    try:
        import PySide6
        return True
    except ImportError:
        return False


def check_install_pyside6() -> None:
    pyside6_available = has_pyside6()
    if pyside6_available:
        print("PySide6 is available")
    else:
        print("PySide6 is NOT available")
        download_extract_pyside6()
