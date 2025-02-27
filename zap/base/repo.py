from pathlib import Path

class Repo:
    def __init__(self, srcobj, path, gh_url):
        self.srcobj = srcobj
        self.storage = Path(__file__).parent.parent / "storage"
        self.path = Path(path)
        self.path_zap = self.path / ".zap"
        self.path_zap_ghm = self.path_zap / "ghm"
        self.path_zap_branches = self.path_zap / "branches"
        self.path_zap_temp = self.path_zap / "temp"
        self.ghm = self.GHM(self, f"{gh_url.removesuffix('.git')}.git")
    @classmethod
    def generate(cls, srcobj, path):
        path = Path(path)
        if not (path / ".zap").exists():
            raise Exception(f"{path} is not a zap repository.")
        with (path / ".zap" / "ghm" / "url").open() as file:
            url = file.read().strip()
        return cls(srcobj, path, url)
    @staticmethod
    def init(path, url):
        from os import mkdir
        path = Path(path)
        if (path / ".zap").exists():
            return
        mkdir(path / ".zap")
        mkdir(path / ".zap" / "ghm")
        with (path / ".zap" / "ghm" / "url").open("w") as file:
            file.write(url)
        mkdir(path / ".zap" / "branches")
        mkdir(path / ".zap" / "temp")
    def get_branch_path(self, branch):
        return self.path_zap_branches / branch
    class GHM:
        def __init__(self, repo, url):
            self.repo = repo
            self.url = url
        def runcmd(self, l):
            from subprocess import run, CalledProcessError
            try:
                from sys import argv
                errors = "--verbose" not in argv
                run(l, check=errors, cwd=str(self.repo.path), capture_output=errors)
            except CalledProcessError as e:
                self.repo.srcobj.print(f"an unexpected internal error occurred while running {l[0]}\nplease forward this message to maintainers of zap here: "
                                       f"https://github.com/fossil-org/zap/issues/new", color="red", title="error")
        def init(self):
            self.runcmd(["git", "init"])
            self.runcmd(["git", "branch", "-f", "main"])
            self.runcmd(["git", "remote", "add", "origin", self.url])
            self.pull()
            self.add_all()
            self.commit("initial commit from zap")
            self.runcmd(["git", "push", "-u", "origin", "main", "-f"])
        def add_all(self):
            self.runcmd(["git", "add", "."])
        def pull(self):
            self.runcmd(["git", "pull"])
        def commit(self, msg):
            self.runcmd(["git", "commit", "-m", f"⚡ {msg}"])
        def push(self):
            self.runcmd(["git", "push", "--all", "--force"])
        def full_save(self, msg):
            self.pull()
            self.add_all()
            self.commit(msg)
            self.push()
    def get_commit(self, cid, branch):
        if not self.commit_exists(cid, branch):
            raise Exception(f"attempted to get commit with cid '{cid}' in branch '{branch}', but it does not exist.")
        from .commit import Commit
        return Commit.from_existing(self, cid, branch)
    def get_commit_path(self, cid, branch):
        return self.get_commit(cid, branch).path
    def get_commit_msg(self, cid, branch):
        return self.get_commit(cid, branch).msg
    def commit_exists(self, cid, branch):
        return self.get_commit_path(cid, branch).exists()
    @staticmethod
    def ignore(s):
        return lambda dir, files: [s] if s in files else []
    def commit(self, msg, branch):
        from os import makedirs, listdir, mkdir
        from shutil import copytree
        cid = len(listdir(self.get_branch_path(branch))) + 1
        path = Path(self.get_commit_path(cid, branch))
        from .commit import Commit
        commit = Commit(
            self,
            msg,
            cid,
            branch,
            path
        )
        makedirs(path, exist_ok=True)
        copytree(self.path, path, ignore=self.ignore(".zap"))
        self.ghm.full_save(msg)
    def rollback(self, cid, branch):
        from shutil import copytree, rmtree
        from .commit import Commit
        commit = Commit.from_existing(self, cid, branch)
        try:
            self.srcobj.print(f"""
are you sure you want to rollback to this commit?
cid: {cid}
msg: {commit.msg}

press <return> to continue
press <ctrl-c> or <ctrl-d> to cancel
            """.strip(), color="yellow", title="warning")
            self.srcobj.input(password=True)
        except (KeyboardInterrupt, EOFError):
            self.srcobj.print("rollback cancelled")
            return
        from uuid import uuid4
        temp_item_id = uuid4()
        path_temp = self.srcobj.path_temp / temp_item_id
        copytree(self.path_zap, path_temp)
        copytree(commit.path, self.path, ignore=self.ignore(".zap-commit"))
        copytree(path_temp, self.path / ".zap")
        rmtree(path_temp)
        self.ghm.full_save(f"redo {commit.msg.removeprefix('undo ')}" if commit.msg.startswith('undo ') else f"undo {commit.msg}")
    @classmethod
    def brain(cls, srcobj, args):
        cmd, *args = args
        from os import getcwd
        rg = srcobj.cmdreg.register
        try:
            repo = cls.generate(srcobj, getcwd())
        except Exception:
            ...
        @rg(init_optional=True)
        def init(url):
            cls.init(getcwd(), url)
            cls.generate(srcobj, getcwd()).ghm.init()
        @rg()
        def commit(msg, branch):
            repo.commit(msg, branch)
        @rg()
        def rollback(cid, branch):
            repo.rollback(cid, branch)
        from ..src.handle import SRC
        srcobj.cmdreg.run(SRC, cmd, args)