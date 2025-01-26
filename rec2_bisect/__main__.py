import argparse
import ctypes
import pathlib
import platform
import sys

from .rec2 import REC2

REC2_BISECT_ROOT = pathlib.Path(__file__).parent


def win32_error_messagebox(message: str, title: str):
    ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)


def main():
    sys.path.append(str(REC2_BISECT_ROOT.parent))
    from rec2_bisect import dep_manager
    if platform.system() != "Windows":
        print("rec2_bisect is only supported on Windows")
        return 1
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--action", choices=("download", "build", "run"))
    args = parser.parse_args()

    deps_available = dep_manager.check_install_dependencies()
    if args.action != "download" and not all(deps_available.values()):
        missing_deps = list(name for name, avail in deps_available.items() if not avail)
        win32_error_messagebox(
            message=f"Some dependencies are missing:\n{', '.join(missing_deps)}" +
                    "\n\nRun download.bat to download dependencies.",
            title="Dependencies were missing",
        )
        return 1

    if args.action == "download":
        if all(deps_available.values()):
            print("Dependencies are available already. Not downloading them again.")
            print("Remove the 'deps' folder manually before running this command again.")
            return 1

        dep_manager.download_extract_dependencies()
        return 0

    rec2 = REC2.create()
    if args.action == "run":
        rec2.run()
        return 0
    elif args.action == "build":
        rec2.build()
        return 0
    else:
        parser.error("Unknown action!")


if __name__ == "__main__":
    raise SystemExit(main())
