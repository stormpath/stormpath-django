import os


def set_env(fpath):
    try:
        with open(fpath) as f:
            lines = f.readlines()
            for line in lines:
                if not line.isspace() and not line.startswith("#"):
                    k, v = line.split('=')
                    os.environ[k] = v.strip()
    except IOError:
        pass


