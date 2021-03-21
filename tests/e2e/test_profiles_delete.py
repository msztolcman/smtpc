import os

from smtpc import config
from smtpc.enums import ExitCodes

from . import *


def test_delete_profile_missing_name(tmp_path, capsys):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmp_path)

    r = callsmtpc(['profiles', 'delete'], capsys)

    assert r.code == ExitCodes.OTHER.value
    assert 'the following arguments are required: name' in r.err


def test_delete_profile_unknown_name(tmp_path, capsys):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmp_path)

    r = callsmtpc(['profiles', 'delete', 'qqq'], capsys)

    assert r.code == ExitCodes.OTHER.value
    assert 'argument name: invalid choice: \'qqq\'' in r.err


def test_delete_profile_valid(tmp_path, capsys):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmp_path)

    r = callsmtpc(['profiles', 'add', 'simple1', '--host', 'localhost'], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(tmp_path / config.PREDEFINED_PROFILES_FILE.name)
    profiles = data['profiles']
    assert 'simple1' in profiles
    assert profiles['simple1'] == {'host': 'localhost'}

    r = callsmtpc(['profiles', 'add', 'simple2', '--host', 'localhost'], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(tmp_path / config.PREDEFINED_PROFILES_FILE.name)
    profiles = data['profiles']
    assert 'simple1' in profiles
    assert profiles['simple1'] == {'host': 'localhost'}
    assert 'simple2' in profiles
    assert profiles['simple2'] == {'host': 'localhost'}

    r = callsmtpc(['profiles', 'delete', 'simple1'], capsys)
    assert r.code == ExitCodes.OK.value
    data = load_toml_file(tmp_path / config.PREDEFINED_PROFILES_FILE.name)
    profiles = data['profiles']
    assert 'simple2' in profiles
    assert profiles['simple2'] == {'host': 'localhost'}
