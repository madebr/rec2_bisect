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


class Git:
    def __init__(self, path: Path):
        self.path = path

    def clone_repo(self, url: str):
        subprocess.check_call(["git", "clone", url, str(self.path)], cwd=self.path)

    @property
    def working_tree_clean(self) -> bool:
        try:
            subprocess.check_call(["git", "status", "--porcelain"], stdout=subprocess.DEVNULL, cwd=self.path)
            return True
        except subprocess.CalledProcessError:
            return False

    @property
    def active_branch(self) -> str:
        return subprocess.check_output(["git", "branch", "--show-current"], cwd=self.path, text=True).strip()

    def clean(self, force: bool = True) -> None:
        subprocess.check_call(["git", "clean"] + ["-f"] if force else [], cwd=self.path)

    def git_log(self, branch: str) -> list[GitCommitSummary]:
        output = subprocess.check_output(["git", "log", branch, "--pretty=\"%H,%aI,%s\""], cwd=self.path, text=True)
        commits = []
        for line in output.splitlines(keepends=False):
            commit_hash, commit_date, commit_subject = line.split(",", 2)
            commits.append(
                GitCommitSummary(hash=commit_hash, date=datetime.datetime.fromisoformat(commit_date), subject=commit_subject))
        return commits

    def show_commit(self, commit: str) -> GitCommitDetails:
        reader = io.StringIO(subprocess.check_output(["git", "show", commit], cwd=self.path, text=True))
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
