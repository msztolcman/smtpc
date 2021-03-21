import os
from unittest import mock

import pytest
import toml

from smtpc import config
from smtpc import encryption
from smtpc.enums import ExitCodes

from . import *


def test_config_files_created(tmpdir, capsys):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmpdir)
    callsmtpc(capsys=capsys)

    config_file = tmpdir.join(config.CONFIG_FILE.name)
    assert config_file.exists(), f'Config file {config_file} not created'

    with config_file.open('r') as fh:
        data = toml.load(fh)
        assert data == {'smtpc': {}}, f'Config file {config_file} has invalid content'

    profiles_file = tmpdir.join(config.PREDEFINED_PROFILES_FILE.name)
    assert profiles_file.exists(), f'Profiles file {profiles_file} not created'

    with profiles_file.open('r') as fh:
        data = toml.load(fh)
        assert data == {'profiles': {}}, f'Profiles file {profiles_file} has invalid content'

    messages_file = tmpdir.join(config.PREDEFINED_MESSAGES_FILE.name)
    assert messages_file.exists(), f'Messages file {messages_file} not created'

    with messages_file.open('r') as fh:
        data = toml.load(fh)
        assert data == {'messages': {}}, f'Messages file {messages_file} has invalid content'


def test_add_profile_missing_login_password(tmpdir, capsys):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmpdir)

    r = callsmtpc(['profiles', 'add', 'simple', '--login'], capsys)
    assert r.code == ExitCodes.OTHER.value
    assert 'argument --login/-l: expected one argument' in r.err

    r = callsmtpc(['profiles', 'add', 'simple', '--login', 'asd'], capsys)
    assert r.code == ExitCodes.OTHER.value
    assert 'Required both or none: --login, --password' in r.err

    r = callsmtpc(['profiles', 'add', 'simple', '--password', 'asd'], capsys)
    assert r.code == ExitCodes.OTHER.value
    assert 'Required both or none: --login, --password' in r.err


@pytest.mark.parametrize('params,expected', [
    [
        ['--login', 'asd', '--password', 'qwe'],
        {'login': 'asd', 'password': 'qwe'}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1'}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1:123'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 123}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1', '--port', '347'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 347}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1', '--port', '587'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 587, 'tls': True}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1:587'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 587, 'tls': True}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1', '--port', '465'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 465, 'ssl': True}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1:465'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 465, 'ssl': True}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1:465', '--tls'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 465, 'tls': True}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1:587', '--ssl'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 587, 'ssl': True}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1:587', '--no-tls'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 587}
    ],
    [
        ['--login', 'asd', '--password', 'qwe', '--host', '127.0.0.1:465', '--no-ssl'],
        {'login': 'asd', 'password': 'qwe', 'host': '127.0.0.1', 'port': 465}
    ],
    [
        ['--host', 'localhost', '--connection-timeout', '10', '--source-address', '1.1.1.1', '--identify-as', 'smtpc.net'],
        {'host': 'localhost', 'connection_timeout': 10, 'source_address': '1.1.1.1', 'identify_as': 'smtpc.net'}
    ],
])
def test_add_profile(tmpdir, capsys, params, expected):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmpdir)
    r = callsmtpc(['profiles', 'add', 'simple1', *params], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(tmpdir.join(config.PREDEFINED_PROFILES_FILE.name))
    profiles = data['profiles']
    assert 'simple1' in profiles
    assert profiles['simple1'] == expected


def test_add_profile_interactive_password(tmpdir, capsys):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmpdir)

    with mock.patch('getpass.getpass', lambda: 'pass'):
        r = callsmtpc(['profiles', 'add', 'simple1', '--login', 'asd', '--password'], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(tmpdir.join(config.PREDEFINED_PROFILES_FILE.name))
    profiles = data['profiles']
    assert 'simple1' in profiles
    assert profiles['simple1'] == {'login': 'asd', 'password': 'pass'}


def test_add_profile_encrypt_password(tmpdir, capsys):
    os.environ[config.ENV_SMTPC_CONFIG_DIR] = str(tmpdir)
    os.environ[config.ENV_SMTPC_SALT] = 'testsalt'

    with mock.patch('getpass.getpass', lambda p: 'key'):
        r = callsmtpc(['profiles', 'add', 'simple1', '--login', 'asd', '--password', 'pass', '--encrypt-password'], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(tmpdir.join(config.PREDEFINED_PROFILES_FILE.name))
    profiles = data['profiles']
    assert 'simple1' in profiles
    assert 'login' in profiles['simple1']
    assert profiles['simple1']['login'] == 'asd'
    assert 'password' in profiles['simple1']
    assert profiles['simple1']['password'].startswith('enc:')
    assert encryption.decrypt(profiles['simple1']['password'], os.environ[config.ENV_SMTPC_SALT], 'key')


