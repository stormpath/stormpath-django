#!/usr/bin/env python
import os
import sys

def set_env():
    try:
        with open('.env') as f:
            lines = f.readlines()
            for line in lines:
                k, v = line.split('=')
                os.environ[k] = v.strip()
    except IOError:
        pass

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__),"..")))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testproject.settings")
    set_env()
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
