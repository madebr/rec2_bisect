from rec2_bisect.packages.cmake import has_cmake, download_extract_cmake
from rec2_bisect.packages.git import has_git, download_extract_git
from rec2_bisect.packages.msvc import has_msvc, download_extract_msvc
from rec2_bisect.packages.ninja import has_ninja, download_extract_ninja


def check_install_dependencies() -> dict[str, bool]:
    result = {
        "cmake": has_cmake(),
        "git": has_git(),
        "msvc": has_msvc(arch="x86"),
        "ninja": has_ninja(),
    }
    for name, r in result.items():
        print(f"{name:<20}{'yes' if r else 'no'}")
    return result


def download_extract_dependencies() -> None:
    download_extract_cmake()
    download_extract_git()
    download_extract_ninja()
    download_extract_msvc(arch="x86")
