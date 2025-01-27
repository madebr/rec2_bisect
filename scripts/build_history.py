#!/usr/bin/env python

import argparse
from pathlib import Path
import subprocess
from typing import IO


def main():
    parser = argparse.ArgumentParser(allow_abbrev=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--build", required=True, type=Path)
    parser.add_argument("--commits", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()

    with args.commits.open() as f:
        f: IO
        lines = f.readlines()
        lines.reverse()

    with args.log.open("a") as fl:
        fl: IO
        for line in lines:
            line = line.strip()
            commit, descr = line.split(" ", 1)
            subprocess.check_call(["git", "checkout", commit], cwd=args.source)
            try:
                subprocess.check_call(["cmake", "--build", args.build])
                msg = f"OK   {commit} {descr}\n"

            except subprocess.SubprocessError:
                msg = f"FAIL {commit} {descr}\n"
            fl.write(msg)
            fl.flush()


if __name__ == "__main__":
    raise SystemExit(main())
