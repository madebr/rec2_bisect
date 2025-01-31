import dataclasses
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import typing


from rec2_bisect.paths import REC2_DEPS_ROOT
from rec2_bisect.util import join_os_environ

MSVC_ROOT = REC2_DEPS_ROOT / "msvc/msvc"
THIS_PATH = Path(__file__).resolve().parent
PORTABLE_MSVC_PY = THIS_PATH / "vendored/portable-msvc.py"


@dataclasses.dataclass(frozen=True)
class MSVCToolchain:
    path: tuple[Path, ...]
    include_path: tuple[Path, ...]
    lib_path: tuple[Path, ...]
    cl_exe: Path
    lib_exe: Path
    link_exe: Path
    dumpbin_exe: Path

    @property
    def env(self) -> dict[str, str]:
        return {
            "PATH": os.path.pathsep.join(str(p) for p in self.path),
            "INCLUDE": os.path.pathsep.join(str(p) for p in self.include_path),
            "LIB": os.path.pathsep.join(str(p) for p in self.lib_path),
        }

    @classmethod
    def create(cls, arch: str) -> typing.Optional["MSVCToolchain"]:
        msvc_setup_bat = MSVC_ROOT / f"setup_{arch}.bat"
        if not msvc_setup_bat.exists():
            return None
        try:
            output_env = subprocess.check_output([
                "cmd", "/c", f"setup_{arch}.bat && set"], cwd=MSVC_ROOT, text=True, stdin=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            return None
        msvc_env_paths = {}
        for line in output_env.strip().splitlines(keepends=False):
            k, v = line.split("=", 1)
            if k.upper() in ("PATH", "INCLUDE", "LIB",):
                paths = v.split(os.path.pathsep)
                new_paths = tuple(tuple(p for p in paths if Path(p).is_relative_to(MSVC_ROOT)))
                msvc_env_paths[k.upper()] = new_paths
        msvc_paths = msvc_env_paths["PATH"]
        msvc_lib_paths = msvc_env_paths["LIB"]
        msvc_include_paths = msvc_env_paths["INCLUDE"]
        msvc_path = os.path.pathsep.join(str(p) for p in msvc_paths)
        cl_exe = shutil.which("cl.exe", path=msvc_path)
        lib_exe = shutil.which("lib.exe", path=msvc_path)
        link_exe = shutil.which("link.exe", path=msvc_path)
        dumpbin_exe = shutil.which("dumpbin.exe", path=msvc_path)

        if not cl_exe or not lib_exe or not link_exe or not dumpbin_exe:
            return None
        return cls(
            path=msvc_paths,
            include_path=msvc_include_paths,
            lib_path=msvc_lib_paths,
            cl_exe=Path(cl_exe),
            lib_exe=Path(lib_exe),
            link_exe=Path(link_exe),
            dumpbin_exe=Path(dumpbin_exe),
        )


def download_extract_msvc(arch: str) -> None:
    shutil.rmtree(MSVC_ROOT, ignore_errors=True)
    MSVC_ROOT.mkdir(parents=True)

    print("[ ] Creating portable MSVC...")
    subprocess.check_call([
        sys.executable, str(PORTABLE_MSVC_PY),
        "--target", arch,
        "--accept-license"
    ], cwd=MSVC_ROOT.parent)
    print("[x] Creating portable MSVC finished")


def has_msvc(arch: str) -> bool:
    msvc_toolchain = MSVCToolchain.create(arch=arch)
    if not msvc_toolchain:
        return False
    temp_path = Path(tempfile.gettempdir())
    selftest_obj = temp_path / "selftest.obj"
    selftest_exe = temp_path / "selftest.exe"
    selftest_pdb = temp_path / "selftest.pdb"
    selftest_obj.unlink(missing_ok=True)
    selftest_exe.unlink(missing_ok=True)
    selftest_pdb.unlink(missing_ok=True)
    msvc_env = join_os_environ(msvc_toolchain.env)
    compile_args = [
        msvc_toolchain.cl_exe, "/nologo",
        "/c", str(THIS_PATH / "msvc_selftest.c"),
        "/MT", f"/Fo{selftest_obj}"
    ]
    try:
        subprocess.check_call(compile_args, text=True, cwd=temp_path, env=msvc_env)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Test compilation failed")
        return False
    if not selftest_obj.exists():
        return False
    link_args = [
        msvc_toolchain.link_exe, "/nologo",
        str(selftest_obj), f"/OUT:{selftest_exe}",
        "/OPT:REF", "/INCREMENTAL:NO", "/DEBUG",
        f"/PDB:{selftest_pdb}", "user32.lib"
    ]
    try:
        subprocess.check_call(link_args, text=True, cwd=temp_path, env=msvc_env)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Test linking failed")
        return False
    if not selftest_exe.exists() or not selftest_pdb.exists():
        return False
    dumpbin_args = [msvc_toolchain.dumpbin_exe, "/IMPORTS", str(selftest_exe)]
    try:
        subprocess.run(dumpbin_args, capture_output=True, text=True, cwd=temp_path, env=msvc_env)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Test dumpbin failed")
        return False
    return True
