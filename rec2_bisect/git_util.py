import dataclasses
import datetime
import io
from pathlib import Path
import subprocess


@dataclasses.dataclass(frozen=True)
class GitCommitSummary:
    hash: str
    date: datetime.datetime
    subject: str


@dataclasses.dataclass(frozen=True)
class GitCommitDetails:
    hash: str
    date: str
    author: str
    message: str
    contents: str


def git_clone_repo(path: Path, url: str):
    subprocess.check_call(["git", "clone", url, str(path)], cwd=path)


def git_hash(path: Path):
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()


def git_is_clean(path: Path) -> bool:
    try:
        subprocess.check_call(["git", "status", "--porcelain"], stdout=subprocess.DEVNULL, cwd=path)
        return True
    except subprocess.CalledProcessError:
        return False


def git_active_branch(path: Path) -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=path, text=True).strip()


def git_clean(path: Path, force: bool = True) -> None:
    subprocess.check_call(["git", "clean"] + ["-f"] if force else [], cwd=path)


def git_log(path: Path, branch: str) -> list[GitCommitSummary]:
    output = subprocess.check_output(["git", "log", branch, "--pretty=\"%H,%aI,%s\""], cwd=path, text=True)
    commits = []
    for line in output.splitlines(keepends=False):
        commit_hash, commit_date, commit_subject = line.split(",", 2)
        commits.append(
            GitCommitSummary(
                hash=commit_hash,
                date=datetime.datetime.fromisoformat(commit_date),
                subject=commit_subject)
        )
    return commits


def git_show_commit(path: Path, commit: str) -> GitCommitDetails:
    reader = io.StringIO(subprocess.check_output(["git", "show", commit], cwd=path, text=True))
    commit_hash = "<unknown>"
    commit_author = "<unknown>"
    commit_date = "<unknown>"
    commit_message = ""
    commit_contents = ""
    while True:
        line = reader.readline()
        if line.startswith("commit"):
            commit_hash = line.removeprefix("commit").strip()
        elif line.startswith("Author:"):
            commit_author = line.removeprefix("Author:").strip()
        elif line.startswith("Date: "):
            commit_date = line.removeprefix("Date:").strip()
        elif line.startswith(" "):
            commit_message += line
        else:
            commit_contents += line
            break
    commit_contents += reader.read()
    return GitCommitDetails(
        hash=commit_hash,
        author=commit_author,
        date=commit_date,
        message=commit_message,
        contents=commit_contents,
    )
