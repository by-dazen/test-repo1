class CommandRegistry:
    def __init__(self):
        self.cmds = []
        self.init = False
    def register(self, init_optional = False):
        def register_1(fn):
            self.cmds.append((fn.__name__, fn, not init_optional))
            return fn
        return register_1
    def run(self, srcobj, name, args):
        for cmd in self.cmds:
            if cmd[0] == name:
                if cmd[2] and not self.init:
                    raise Exception(f"repo must be initialized to use '{name}'")
                fn = cmd[1]
                from inspect import signature
                sig = list(signature(fn).parameters.values())
                new_args = []
                for arg in sig:
                    new_args.append(srcobj.get_arg(f"--{arg}"))
                fn(*new_args)
                break
        else:
            raise Exception(f"unknown command: '{name}'")