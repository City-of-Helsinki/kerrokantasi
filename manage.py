#!/usr/bin/env python
import json

import os
import sys


def read_npm_scripts():
    with open(os.path.join(os.path.dirname(__file__), "package.json")) as infp:
        data = json.load(infp)
        return data["scripts"]


def run_npm_script():
    """
    Run a command if it exists in the `scripts` section of `package.json`.

    :return: Returns True if a script was run.
    :rtype: bool
    """
    scripts = read_npm_scripts()
    if len(sys.argv) > 1 and sys.argv[1] in scripts:
        os.environ["PATH"] = "%s%s%s" % (
            os.path.join(os.path.dirname(__file__), "node_modules", ".bin"),
            os.pathsep,
            os.environ["PATH"]
        )
        command = scripts[sys.argv[1]]
        args = list(sys.argv[2:])
        if args and args[0] == "--":
            args.pop(0)
        command = (command + " " + " ".join(args)).strip()
        print(">", command)
        os.system(command)
        return True
    return False


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kerrokantasi.settings")
    if run_npm_script():
        sys.exit(0)
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
