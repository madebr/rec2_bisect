import argparse
import ctypes
import pathlib
import platform
import sys

REC2_BISECT_ROOT = pathlib.Path(__file__).parent


def win32_error_messagebox(message: str, title: str):
    ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)


def run_gui():
    import rec2_bisect.gui
    rec2_bisect.gui.run_gui()


def main():
    sys.path.append(str(REC2_BISECT_ROOT.parent))
    from rec2_bisect.packages.pyside6 import PYSIDE6_ROOT
    sys.path.append(str(PYSIDE6_ROOT))
    from rec2_bisect import dep_manager
    if platform.system() != "Windows":
        print("rec2_bisect is only supported on Windows")
        return 1
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--action", choices=("gui", "download"))
    args = parser.parse_args()

    should_download_dependencies = args.action == "download"

    deps_available = dep_manager.check_install_dependencies()
    if all(deps_available.values()):
        if should_download_dependencies:
            print("Dependencies are available already. Not downloading them again.")
            print("Remove the 'deps' folder manually.")
            return 1
    else:
        if should_download_dependencies:
            dep_manager.download_extract_dependencies()
            return 0
        else:
            missing_deps = list(name for name, avail in deps_available.items() if not avail)
            win32_error_messagebox(
                message=f"Some dependencies are missing:\n{', '.join(missing_deps)}" +
                        "\n\nRun download.bat to download dependencies.",
                title="Dependencies were missing",
            )
            return 1
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
