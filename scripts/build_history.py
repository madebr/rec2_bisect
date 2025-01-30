#!/usr/bin/env python

import argparse
from pathlib import Path
import subprocess
import sys
from typing import IO


def main():
    parser = argparse.ArgumentParser(allow_abbrev=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--build", required=True, type=Path)
    parser.add_argument("--commits", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--what", choices=("msvc", "mingw", "checks"), required=True)
    args = parser.parse_args()

    with args.commits.open() as f:
        f: IO
        lines = f.readlines()
        lines.reverse()

    if args.what == "mingw":
        subprocess.check_call([
            "cmake", "-S", str(args.source), "-B", str(args.build), "-GNinja",
            "-DREC2_WERROR=ON",
            f"-DCMAKE_TOOLCHAIN_FILE={args.source}/cmake/toolchains/mingw32.cmake",
        ])
    elif args.what == "msvc":
        subprocess.check_call([
            "cmake", "-S", str(args.source), "-B", str(args.build), "-GNinja",
            "-DREC2_WERROR=ON",
            "-DCMAKE_C_COMPILER=cl",
            "-DCMAKE_CXX_COMPILER=cl",
        ])

    with args.log.open("a") as fl:
        fl: IO
        for line in lines:
            line = line.strip()
            commit, descr = line.split(" ", 1)
            subprocess.check_call(["git", "checkout", commit], cwd=args.source)
            try:
                if args.what in ("mingw", "msvc"):
                    subprocess.check_call(["cmake", "--build", args.build])
                    result = "OK"
                else:
                    path_collect_symbols_py = args.source / "scripts/collect-symbols.py"
                    if path_collect_symbols_py.is_file():
                        subprocess.check_call([
                            sys.executable, str(path_collect_symbols_py), "--summary", "-Werror",
                        ])
                        result = "OK"
                    else:
                        result = "SKIP"
                msg = f"{result:<4} {commit} {descr}\n"

            except subprocess.SubprocessError:
                msg = f"FAIL {commit} {descr}\n"
            fl.write(msg)
            fl.flush()


if __name__ == "__main__":
    raise SystemExit(main())
