from pathlib import Path

class Commit:
    def __init__(self, repo, msg, cid, branch, path, init=True):
        self.repo = repo
        self.msg = msg
        self.cid = cid
        self.branch = branch
        self.path = Path(path)
        self.path_zap_commit = path / ".zap-commit"
        self.path_zap_commit_cid = self.path_zap_commit / "cid"
        self.path_zap_commit_msg = self.path_zap_commit / "msg"
        self.init() if init else ...
    def init(self):
        mkdir(zap_commit_path)
        with commit.path_zap_commit_cid.open("w") as file:
            file.write(str(cid))
        with commit.path_zap_commit_msg.open("w") as file:
            file.write(msg)
    @classmethod
    def from_existing(cls, repo, cid, branch):
        path = repo.get_branch_path(branch) / cid
        with (path / ".zap-commit" / "msg").open() as file:
            msg = file.read()
        return cls(
            repo,
            msg,
            cid,
            branch,
            path,
            init=False
        )