#!/usr/bin/env python
import subprocess
import shlex


def run(cmd):
    """ run command
    """
    cmd = shlex.split(cmd)
    res = subprocess.run(cmd, check=True, capture_output=True)
    return res.stdout.decode()


def rename():
    """ remove prefix and suffix from container names e.g. rasa_app_1 => app
    """
    names = run("sudo docker ps --format {{.Names}}")
    for name in names.split():
        if name.count("_") < 2:
            continue
        newname = name[name.find("_") + 1 : name.rfind("_")]
        if name == newname:
            continue
        cmd = shlex.split(f"sudo docker rename {name} {newname}")
        subprocess.run(cmd)


if __name__ == "__main__":
    rename()
