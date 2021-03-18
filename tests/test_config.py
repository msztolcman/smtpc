import os
import pathlib

from smtpc.config import get_config_dir


def test_get_config_dir():
    orginal_env = os.environ.copy()

    try:
        os.environ.pop('SMTPC_CONFIG_DIR', None)
        os.environ.pop('XDG_CONFIG_HOME', None)
        assert get_config_dir() == pathlib.Path('~/.config/smtpc').expanduser()

        os.environ['SMTPC_CONFIG_DIR'] = '/tmp/asd/qwe'
        os.environ.pop('XDG_CONFIG_HOME', None)
        assert get_config_dir() == pathlib.Path('/tmp/asd/qwe')

        os.environ.pop('SMTPC_CONFIG_DIR', None)
        os.environ['XDG_CONFIG_HOME'] = '/tmp/asd/qwe'
        assert get_config_dir() == pathlib.Path('/tmp/asd/qwe/smtpc')
    finally:
        os.environ = orginal_env

