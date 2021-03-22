from smtpc import config
from smtpc.enums import ExitCodes

from . import *


def test_list_messages_empty(smtpctmppath, capsys):
    r = callsmtpc(['messages', 'list'], capsys)

    assert r.code == ExitCodes.OK.value
    assert 'No known messages\n' == r.out, 'Messages list not empty?'


def test_list_messages_valid(smtpctmppath, capsys):
    r = callsmtpc(['messages', 'add', 'simple1',
        '--body-plain', 'some test',
        '--from', 'test@smtpc.net',
        '--to', 'receiver@smtpc.net',
    ], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(smtpctmppath / config.PREDEFINED_MESSAGES_FILE.name)
    messages = data['messages']
    assert 'simple1' in messages, 'Expected message simple1 not found'
    assert messages['simple1'] == {
        'body_type': 'plain', 'body_plain': 'some test',
        'address_from': 'test@smtpc.net', 'address_to': ['receiver@smtpc.net'],
        # 'subject': '',
    }, 'Expected message simple1 is invalid'

    r = callsmtpc(['messages', 'list'], capsys)
    assert 'Known messages:\n- simple1\n' == r.out

    r = callsmtpc(['-D', 'messages', 'list'], capsys)
    assert "Known messages:\n- simple1 (subject: \"\", from: \"test@smtpc.net\", to: \"receiver@smtpc.net\")\n" == r.out

    r = callsmtpc(['-DD', 'messages', 'list'], capsys)
    assert "Known messages:\n- simple1 (subject: \"\", from: \"test@smtpc.net\", to: \"receiver@smtpc.net\")\n" == r.out
