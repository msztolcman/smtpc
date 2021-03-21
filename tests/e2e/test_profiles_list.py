import os

from smtpc import config
from smtpc.enums import ExitCodes

from . import *


def test_list_empty(tmp_path, capsys):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmp_path)

    r = callsmtpc(['profiles', 'list'], capsys)

    assert r.code == ExitCodes.OK.value
    assert 'No known profiles\n' == r.out


def test_list_profiles(tmp_path, capsys):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmp_path)

    r = callsmtpc(['profiles', 'add', 'simple1', '--host', 'localhost', '--login', 'asd', '--password', 'qwe'], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(tmp_path / config.PREDEFINED_PROFILES_FILE.name)
    profiles = data['profiles']
    assert 'simple1' in profiles
    assert profiles['simple1'] == {'host': 'localhost', 'login': 'asd', 'password': 'qwe'}

    r = callsmtpc(['profiles', 'list'], capsys)
    assert 'Known profiles:\n- simple1\n' == r.out

    r = callsmtpc(['-D', 'profiles', 'list'], capsys)
    assert "Known profiles:\n- simple1 ({'login': 'asd', 'password': '***', 'host': 'localhost', 'port': None, 'ssl': None, 'tls': None, 'connection_timeout': None, 'identify_as': None, 'source_address': None})\n" == r.out

    r = callsmtpc(['-DD', 'profiles', 'list'], capsys)
    assert "Known profiles:\n- simple1 ({'login': 'asd', 'password': 'qwe', 'host': 'localhost', 'port': None, 'ssl': None, 'tls': None, 'connection_timeout': None, 'identify_as': None, 'source_address': None})\n" == r.out
