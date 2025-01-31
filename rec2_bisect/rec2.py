import configparser
import hashlib
import os
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Optional

from .git_util import git_hash
from .util import join_os_environ
from .packages.git import GIT_ENV
from .packages.cmake import CMAKE_ENV
from .packages.msvc import MSVCToolchain
from .packages.ninja import NINJA_ENV

REC2_BISECT_ROOT = Path(__file__).resolve().parent

REC2_DLL_NAME = "rec2.dll"
REC2_PDB_NAME = "rec2.pdb"
REC2_INJECTOR_EXE_NAME = "rec2-injector.exe"


def is_rec2_source_path(p: Path) -> bool:
    cmake_path = p / "CMakeLists.txt"
    if not cmake_path.is_file():
        return False
    cmake_text = cmake_path.read_text()
    if "project(rec2" not in cmake_text:
        return False
    return True


def is_carma2_game_path(p: Path) -> bool:
    c2_hw_exe = p / "CARMA2_HW.EXE"
    if not c2_hw_exe.is_file():
        return False
    s = os.stat(c2_hw_exe)
    if s.st_size != 2680320:
        return False
    # if hashlib.sha256(c2_hw_exe.read_bytes()) != "9b896c2cbb170c01b3e9f904ce5e1808db29fe5b51184a5d55a6d19b1799b58d":
    #     return False
    return True


class REC2:
    def __init__(self,
                 source_path: Path,
                 build_path: Path,
                 cache_path: Path,
                 game_path: Path,
                 run_args: list[str],
                 windbg_path: Optional[Path]):
        self.source_path = source_path
        self.build_path = build_path
        self.cache_path = cache_path
        self.game_path = game_path
        self.run_args = run_args
        self.windbg_path = windbg_path
        self.msvc_toolchain = MSVCToolchain.create(arch="x86")

    @property
    def run_env(self) -> dict[str, str]:
        return join_os_environ(
            CMAKE_ENV,
            GIT_ENV,
            NINJA_ENV,
            self.msvc_toolchain.env,
        )

    def build(self):
        build_bin_path = self.build_path / "bin"
        build_dll_path = build_bin_path / REC2_DLL_NAME
        build_pdb_path = build_bin_path / REC2_PDB_NAME
        build_injector_path = build_bin_path / REC2_INJECTOR_EXE_NAME
        build_dll_path.unlink(missing_ok=True)
        build_pdb_path.unlink(missing_ok=True)
        build_injector_path.unlink(missing_ok=True)

        assert not build_dll_path.is_file()
        assert not build_injector_path.is_file()

        hash_start = git_hash(self.source_path)
        configure_cmd = [
            "cmake",
            "-S", str(self.source_path),
            "-B", str(self.build_path),
            "-DCMAKE_BUILD_TYPE=Debug",
            "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDebug",
            f"-DCMAKE_RUNTIME_OUTPUT_DIRECTORY={build_bin_path}",
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={build_bin_path}",
            "-DCMAKE_C_COMPILER=cl.exe",
            "-DCMAKE_CXX_COMPILER=cl.exe",
            "-GNinja",
        ]
        build_cmd = [
            "cmake",
            "--build", str(self.build_path),
            "--target", "rec2", "rec2-injector",
            # "--verbose",
        ]
        print("Configuring rec2:", configure_cmd)
        subprocess.check_call(configure_cmd, env=self.run_env)
        print("Building rec2:", build_cmd)
        subprocess.check_call(build_cmd, env=self.run_env)
        hash_end = git_hash(self.source_path)
        if hash_start != hash_end:
            raise ValueError("commit hash changed while building rec2")
        build_cache_path = self.cache_path / hash_end
        shutil.rmtree(build_cache_path, ignore_errors=True)
        build_cache_path.mkdir(parents=True)
        rec2_cache_dll_path = build_cache_path / REC2_DLL_NAME
        rec2_cache_pdb_path = build_cache_path / REC2_PDB_NAME
        rec2_cache_injector_path = build_cache_path / REC2_INJECTOR_EXE_NAME
        print(f"Copying {REC2_DLL_NAME}, {REC2_PDB_NAME} and {REC2_INJECTOR_EXE_NAME} to {rec2_cache_dll_path}")
        shutil.copyfile(src=build_dll_path, dst=rec2_cache_dll_path)
        if build_pdb_path.is_file():
            shutil.copyfile(src=build_pdb_path, dst=rec2_cache_pdb_path)
        shutil.copyfile(src=build_injector_path, dst=rec2_cache_injector_path)

    def create_run_cmd(self, args: list[str]) -> list[str]:
        hash_current = git_hash(self.source_path)
        build_cache_path = self.cache_path / hash_current
        rec2_cache_dll_path = build_cache_path / REC2_DLL_NAME
        rec2_cache_injector_path = build_cache_path / REC2_INJECTOR_EXE_NAME
        if not rec2_cache_dll_path.is_file() or not rec2_cache_injector_path.is_file():
            print(f"No {REC2_DLL_NAME} or {REC2_INJECTOR_EXE_NAME} for {hash_current}. Creating a new build...")
            self.build()
        assert rec2_cache_dll_path.is_file()
        assert rec2_cache_injector_path.is_file()
        return [
            str(rec2_cache_injector_path),
            str(self.game_path / "CARMA2_HW.EXE"),
            "--inject", str(rec2_cache_dll_path),
        ] + ["--"] + args + self.run_args

    def run(self, args: list[str]):
        run_cmd = self.create_run_cmd(args)
        print("Running rec2:", run_cmd)
        print("cwd:", self.game_path)
        subprocess.check_call(run_cmd, cwd=self.game_path, env=self.run_env)

    def debug(self, args: list[str]):
        hash_current = git_hash(self.source_path)
        build_cache_path = self.cache_path / hash_current
        if not self.windbg_path or not self.windbg_path.is_file():
            raise FileNotFoundError("Cannot find WinDbg (install WinDbg, or set windbg.path in config.ini)")
        run_cmd = [
            str(self.windbg_path),
            "-y", str(build_cache_path),
        ] + self.create_run_cmd(args)
        print("Running rec2:", run_cmd)
        print("cwd:", self.game_path)
        subprocess.check_call(run_cmd, cwd=self.game_path, env=self.run_env)

    @classmethod
    def create(cls) -> "REC2":
        config = configparser.ConfigParser()
        config_ini = REC2_BISECT_ROOT / "config.ini"
        with config_ini.open() as f:
            config.read_file(f)
        source_path = Path(config.get("rec2", "source", fallback="source").strip()).resolve()
        if not is_rec2_source_path(source_path):
            raise ValueError("Invalid source path. Modify config.ini to point to a rec2 source tree.")
        build_path = Path(config.get("rec2", "build", fallback="build").strip()).resolve()
        cache_path = Path(config.get("rec2", "cache", fallback="cache").strip()).resolve()
        game_path = Path(config.get("game", "path", fallback="game").strip()).resolve()
        if not is_carma2_game_path(game_path):
            raise ValueError("Invalid game path. Modify config.ini to point to Carmageddon 2 game path.")
        game_args = config.get("game", "arguments", fallback="").strip()
        if not game_args:
            run_args = []
        else:
            run_args = shlex.split(game_args)
        windbg_path = config.get("windbg", "path", fallback="").strip()
        if windbg_path:
            windbg_path = Path(windbg_path).resolve()
        else:
            windbg_path = Path(os.environ.get("LocalAppData", "C:/users/me") + "/Microsoft/WindowsApps/WinDbgX.exe").resolve()
        if not windbg_path.is_file:
            windbg_path = None

        return cls(
            source_path=source_path,
            build_path=build_path,
            cache_path=cache_path,
            game_path=game_path,
            run_args=run_args,
            windbg_path=windbg_path,
        )
