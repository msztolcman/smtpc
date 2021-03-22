from smtpc import config
from smtpc.enums import ExitCodes, ContentType

from . import *


def test_delete_message_missing_name(smtpctmppath, capsys):
    r = callsmtpc(['messages', 'delete'], capsys)

    assert r.code == ExitCodes.OTHER.value
    assert 'the following arguments are required: name' in r.err


def test_delete_message_unknown_name(smtpctmppath, capsys):
    r = callsmtpc(['messages', 'delete', 'qqq'], capsys)

    assert r.code == ExitCodes.OTHER.value
    assert 'argument name: invalid choice: \'qqq\'' in r.err


def test_delete_message_valid(smtpctmppath, capsys):
    r = callsmtpc(['messages', 'add', 'simple1', '--from', 'from1@smtpc.net', '--to', 'receiver1@smtpc.net'], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(smtpctmppath / config.PREDEFINED_MESSAGES_FILE.name)
    messages = data['messages']
    assert 'simple1' in messages
    assert messages['simple1'] == {'address_from': 'from1@smtpc.net', 'address_to': ['receiver1@smtpc.net'],
        'body_type': ContentType.PLAIN.value}

    r = callsmtpc(['messages', 'add', 'simple2', '--from', 'from2@smtpc.net', '--to', 'receiver2@smtpc.net'], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(smtpctmppath / config.PREDEFINED_MESSAGES_FILE.name)
    messages = data['messages']
    assert 'simple1' in messages
    assert messages['simple1'] == {'address_from': 'from1@smtpc.net', 'address_to': ['receiver1@smtpc.net'],
        'body_type': ContentType.PLAIN.value}
    assert 'simple2' in messages
    assert messages['simple2'] == {'address_from': 'from2@smtpc.net', 'address_to': ['receiver2@smtpc.net'],
        'body_type': ContentType.PLAIN.value}

    r = callsmtpc(['messages', 'delete', 'simple1'], capsys)
    assert r.code == ExitCodes.OK.value
    data = load_toml_file(smtpctmppath / config.PREDEFINED_MESSAGES_FILE.name)
    messages = data['messages']
    assert 'simple2' in messages
    assert messages['simple2'] == {'address_from': 'from2@smtpc.net', 'address_to': ['receiver2@smtpc.net'],
        'body_type': ContentType.PLAIN.value}
