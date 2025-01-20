#!/bin/bash




python -m pip download \
  --python-version 39 \
  --only-binary=:all: \
  --platform win_amd64 \
  pip


python -m pip download \
  --python-version 39 \
  --only-binary=:all: \
  --platform win_amd64 \
  PySide6


MSVC versions: 14.29 14.30 14.31 14.32 14.33 14.34 14.35 14.36 14.37 14.38 14.39 14.40 14.41 14.42
Windows SDK versions: 18362 19041 20348 22000 22621 26100
