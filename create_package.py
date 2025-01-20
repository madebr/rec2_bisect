#!/usr/bin/env python
import glob
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parent


PACKAGER_ROOT = Path(tempfile.gettempdir()) / "rec2-bisector-package-creation-root"
shutil.rmtree(PACKAGER_ROOT, ignore_errors=True)
PACKAGER_ROOT.mkdir(parents=True)

DOWNLOAD_DIR_PATH = PACKAGER_ROOT / "downloads"
DOWNLOAD_DIR_PATH.mkdir()

PACKAGE_ROOT = PACKAGER_ROOT / "package"
PACKAGE_ROOT.mkdir()

PYTHON_URL = "https://www.python.org/ftp/python/3.13.1/python-3.13.1-embed-amd64.zip"
PYTHON_EMBED_PATH = DOWNLOAD_DIR_PATH / "python3-embed.zip"

DIST_ROOT = PACKAGER_ROOT / "dist"
DIST_ROOT.mkdir()

ZIP_PACKAGE_PATH = DIST_ROOT / "rec2-bisect.zip"

print("[ ] Downloading python3 ...")
subprocess.check_call(["wget", PYTHON_URL, "-O", str(PYTHON_EMBED_PATH)])
print("[x] Downloading python3 finished")

with zipfile.ZipFile(PYTHON_EMBED_PATH) as zf:
    zf.extractall(PACKAGE_ROOT)

print("[ ] Downloading pip ...")
subprocess.check_call([
    "python", "-m", "pip", "download",
    "--python-version", "39",
    "--only-binary=:all:",
    "--platform", "win_amd64",
    "pip"
], cwd=DOWNLOAD_DIR_PATH)
print("[x] Downloading pip finished")

downloaded_whl_archives = glob.glob(str(DOWNLOAD_DIR_PATH / "*.whl"))

for whl in downloaded_whl_archives:
    with zipfile.ZipFile(whl) as zf:
        zf.extractall(PACKAGE_ROOT)

with zipfile.ZipFile(ZIP_PACKAGE_PATH, "w") as zf:
    for root, _, filenames in os.walk(PACKAGE_ROOT):
        rel_path = Path(root).relative_to(PACKAGE_ROOT)
        for filename in filenames:
            zf.write(str(Path(root) / filename), arcname=str(rel_path / filename))
    for root, _, filenames in os.walk(PROJECT_ROOT / "rec2_bisect"):
        rel_path = Path(root).relative_to(PROJECT_ROOT)
        for filename in filenames:
            zf.write(str(Path(root) / filename), arcname=str(rel_path / filename))
        zf.write(PROJECT_ROOT / "start.bat", arcname="start.bat")
        zf.write(PROJECT_ROOT / "download.bat", arcname="download.bat")

print(f"[X] Created {ZIP_PACKAGE_PATH}")
