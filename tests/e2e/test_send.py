import email
from unittest import mock

import pytest

import smtpc
from smtpc import config
from smtpc.enums import ContentType, ExitCodes
from . import *


def test_send_simple_valid(smtpctmppath, capsys):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net'], capsys)

        mocked_smtp_class.assert_called()
        mocked_smtp.ehlo.assert_called()
        mocked_smtp.sendmail.assert_called()

        smtp_sendmail_args = mocked_smtp.sendmail.call_args.args
        assert smtp_sendmail_args[0] == 'send@smtpc.net'
        assert smtp_sendmail_args[1] == ['receive@smtpc.net']

        received_message = email.message_from_string(smtp_sendmail_args[2])
        assert sorted(received_message.keys()) == ['Content-Transfer-Encoding', 'Content-Type', 'From', 'MIME-Version', 'To', 'User-Agent']

        assert f"SMTPc/{smtpc.__version__}" in received_message['User-Agent']
        assert 'send@smtpc.net' == received_message['From']
        assert 'receive@smtpc.net' == received_message['To']
        assert received_message.get_content_type() == 'text/plain'


@pytest.mark.parametrize('params, expected',
    [
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'plain\nmessage'],
            {
                'sender': 'send@smtpc.net',
                'to': 'receive@smtpc.net',
                'receivers': ['receive@smtpc.net'],
                'body': 'plain\nmessage',
                'content_type': 'text/plain',
            },
        ],
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'plain\nmessage', '--body-type', ContentType.PLAIN.value],
            {
                'sender': 'send@smtpc.net',
                'to': 'receive@smtpc.net',
                'receivers': ['receive@smtpc.net'],
                'body': 'plain\nmessage',
                'content_type': 'text/plain',
            },
        ],
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'html\nmessage', '--body-type', ContentType.HTML.value],
            {
                'sender': 'send@smtpc.net',
                'to': 'receive@smtpc.net',
                'receivers': ['receive@smtpc.net'],
                'body': 'html\nmessage',
                'content_type': 'text/html',
            },
        ],
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body-html', 'html\nmessage', '--body-type', ContentType.HTML.value],
            {
                'sender': 'send@smtpc.net',
                'to': 'receive@smtpc.net',
                'receivers': ['receive@smtpc.net'],
                'body': 'html\nmessage',
                'content_type': 'text/html',
            },
        ],
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body-html', 'html\nmessage'],
            {
                'sender': 'send@smtpc.net',
                'to': 'receive@smtpc.net',
                'receivers': ['receive@smtpc.net'],
                'body': 'html\nmessage',
                'content_type': 'text/html',
            },
        ],
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'html\nmessage', '--body-html', 'ignored', '--body-type', ContentType.HTML.value],
            {
                'sender': 'send@smtpc.net',
                'to': 'receive@smtpc.net',
                'receivers': ['receive@smtpc.net'],
                'body': 'html\nmessage',
                'content_type': 'text/html',
            },
        ],
    ],
    ids=[
        'just --body',
        '--body with --body-type=plain',
        '--body with --body-type=html',
        '--body-html with --body-type=html',
        '--body-html without',
        '--body and --body-html with --body-type=html',
    ],
)
def test_send_simple_text_valid(smtpctmppath, capsys, params, expected):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']

        r = callsmtpc(params, capsys)
        assert r.code == ExitCodes.OK.value

        mocked_smtp_class.assert_called()
        mocked_smtp.ehlo.assert_called()
        mocked_smtp.sendmail.assert_called()

        smtp_sendmail_args = mocked_smtp.sendmail.call_args.args
        assert smtp_sendmail_args[0] == expected['sender']
        assert smtp_sendmail_args[1] == expected['receivers']

        received_message = email.message_from_string(smtp_sendmail_args[2])
        assert sorted(received_message.keys()) == ['Content-Transfer-Encoding', 'Content-Type', 'From', 'MIME-Version', 'To', 'User-Agent']

        assert f"SMTPc/{smtpc.__version__}" in received_message['User-Agent']
        assert received_message['From'] == expected['sender']
        assert received_message['To'] == expected['to']
        assert received_message.get_content_type() == expected['content_type']

        message_body = received_message.as_string().split("\n\n", 1)
        assert len(message_body) == 2, 'No message body found'
        assert message_body[1] == expected['body']


@pytest.mark.parametrize('params, expected_body',
    [
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'some\nmessage', '--body-type', ContentType.ALTERNATIVE.value],
            '''\
--{SMTPC_BOUNDARY}
Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

some
message
--{SMTPC_BOUNDARY}--
'''
        ],
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body-html', 'html\nmessage', '--body-type', ContentType.ALTERNATIVE.value],
            '''\
--{SMTPC_BOUNDARY}
Content-Type: text/html; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

html
message
--{SMTPC_BOUNDARY}--
'''
        ],
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'some\nbody', '--body-html', 'html\nmessage', '--body-type', ContentType.ALTERNATIVE.value],
            '''\
--{SMTPC_BOUNDARY}
Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

some
body
--{SMTPC_BOUNDARY}
Content-Type: text/html; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

html
message
--{SMTPC_BOUNDARY}--
'''
        ],
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'some\nbody', '--body-html', 'html\nmessage'],
            '''\
--{SMTPC_BOUNDARY}
Content-Type: text/plain; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

some
body
--{SMTPC_BOUNDARY}
Content-Type: text/html; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

html
message
--{SMTPC_BOUNDARY}--
'''
        ],
    ],
    ids=[
        'just --body',
        'just --body-html',
        'both --body and --body-html, with --body-type=alternative',
        'both --body and --body-html, without --body-type',
    ]
)
def test_send_alternative_valid(smtpctmppath, capsys, params, expected_body):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(params, capsys)
        assert r.code == ExitCodes.OK.value

        mocked_smtp_class.assert_called()
        mocked_smtp.ehlo.assert_called()
        mocked_smtp.sendmail.assert_called()

        smtp_sendmail_args = mocked_smtp.sendmail.call_args.args
        assert smtp_sendmail_args[0] == 'send@smtpc.net'
        assert smtp_sendmail_args[1] == ['receive@smtpc.net']

        received_message = email.message_from_string(smtp_sendmail_args[2])
        assert sorted(received_message.keys()) == ['Content-Type', 'From', 'MIME-Version', 'To', 'User-Agent']

        assert f"SMTPc/{smtpc.__version__}" in received_message['User-Agent']
        assert 'send@smtpc.net' == received_message['From']
        assert 'receive@smtpc.net' == received_message['To']
        assert received_message.get_content_type() == 'multipart/alternative'

        message_body = received_message.as_string().split("\n\n", 1)
        assert len(message_body) == 2, 'No message body found'

        expected_body = expected_body.replace('{SMTPC_BOUNDARY}', received_message.get_boundary())
        assert message_body[1] == expected_body


@pytest.mark.parametrize('params, expected_body',
    [
        [
            ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'some\nmessage', '--raw-body'],
            '''
some
message'''
        ],
    ],
    ids=[
        '--body with --raw-body',
    ]
)
def test_send_raw_valid(smtpctmppath, capsys, params, expected_body):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(params, capsys)
        assert r.code == ExitCodes.OK.value

        mocked_smtp_class.assert_called()
        mocked_smtp.ehlo.assert_called()
        mocked_smtp.sendmail.assert_called()

        smtp_sendmail_args = mocked_smtp.sendmail.call_args.args
        assert smtp_sendmail_args[0] == 'send@smtpc.net'
        assert smtp_sendmail_args[1] == ['receive@smtpc.net']

        received_message = email.message_from_string(smtp_sendmail_args[2])
        assert sorted(received_message.keys()) == []
        assert received_message.get_content_type() == 'text/plain'
        assert received_message.as_string() == expected_body


@pytest.mark.parametrize('params, expected',
    [
        [
            ['--host', 'smtpc.net'],
            {
                'connection': ('smtpc.net', 25),
                'smtp':  {'source_address': None, 'timeout': 30},
                'login': (),
            }
        ],
        pytest.param(
            ['--host', 'smtpc.net', '--tls'],
            {
                'connection': ('smtpc.net', 587),
                'smtp':  {'source_address': None, 'timeout': 30},
                'login': (),
            },
            marks=pytest.mark.skip(reason='not implemented yet'),
        ),
        [
            ['--host', 'smtpc.net', '--port', '123'],
            {
                'connection': ('smtpc.net', 123),
                'smtp':  {'source_address': None, 'timeout': 30},
                'login': (),
            }
        ],
        [
            ['--host', 'smtpc.net:456'],
            {
                'connection': ('smtpc.net', 456),
                'smtp':  {'source_address': None, 'timeout': 30},
                'login': (),
            }
        ],
        [
            ['--host', 'smtpc.net:456', '--tls'],
            {
                'connection': ('smtpc.net', 456),
                'smtp':  {'source_address': None, 'timeout': 30},
                'login': (),
            }
        ],
        [
            ['--host', 'smtpc.net', '--login', 'some-login@smtpc.net', '--password', 'some-password'],
            {
                'connection': ('smtpc.net', 25),
                'smtp':  {'source_address': None, 'timeout': 30},
                'login': ('some-login@smtpc.net', 'some-password'),
            }
        ],
        [
            ['--host', 'smtpc.net', '--source-address', '1.1.1.1', '--connection-timeout', '100'],
            {
                'connection': ('smtpc.net', 25),
                'smtp':  {'source_address': '1.1.1.1', 'timeout': 100},
                'login': (),
            }
        ]
    ],
    ids=[
        '--host only, without port',
        '--host only, without port, but with --tls',
        '--host and --port',
        '--host with port after colon',
        '--host with --tls',
        '--login and --password',
        '--source-address, --connection-timeout'
    ]
)
def test_connection_args_valid(smtpctmppath, capsys, params, expected):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(['send', '--from', 'sender@smtpc.net', '--to', 'receiver@smtpc.net',
            *params], capsys)
        assert r.code == ExitCodes.OK.value

        mocked_smtp_class.assert_called()
        assert mocked_smtp_class.call_args.kwargs == expected['smtp']

        mocked_smtp.ehlo.assert_called()
        mocked_smtp.connect.assert_called()
        mocked_smtp.sendmail.assert_called()

        smtp_connect_args = mocked_smtp.connect.call_args.args
        assert smtp_connect_args == expected['connection']

        if '--tls' in params:
            mocked_smtp.starttls.assert_called()

        if '--login' in params:
            mocked_smtp.login.assert_called()
            smtp_login_args = mocked_smtp.login.call_args.args
            assert expected['login'] == smtp_login_args


@pytest.mark.parametrize('smtpc_params, profile_params, expected',
    [
        [
            ['--host', 'smtpc.net', '--port', '123', '--login', 'some-login', '--password', 'some-password',
                '--source-address', '1.1.1.1', '--connection-timeout', '50'],
            ['--host', 'example.net', '--port', '456', '--login', 'another-login', '--password', 'another-password',
                '--source-address', '2.2.2.2', '--connection-timeout', '100'],
            {
                'connection': ('smtpc.net', 123),
                'smtp':  {'source_address': '1.1.1.1', 'timeout': 50},
                'login': ('some-login', 'some-password'),
            }
        ],
        [
            [],
            ['--host', 'example.net', '--port', '456', '--login', 'another-login', '--password', 'another-password',
                '--source-address', '2.2.2.2', '--connection-timeout', '100'],
            {
                'connection': ('example.net', 456),
                'smtp':  {'source_address': '2.2.2.2', 'timeout': 100},
                'login': ('another-login', 'another-password'),
            }
        ],
        [
            ['--host', 'smtpc.net', '--login', 'some-login', '--password', 'some-password'],
            ['--host', 'example.net', '--port', '456', '--login', 'another-login', '--password', 'another-password',
                '--source-address', '2.2.2.2', '--connection-timeout', '100'],
            {
                'connection': ('smtpc.net', 456),
                'smtp':  {'source_address': '2.2.2.2', 'timeout': 100},
                'login': ('some-login', 'some-password'),
            }
        ],
        pytest.param(
            ['--host', 'smtpc.net', '--login', 'some-login'],
            ['--host', 'example.net', '--port', '456', '--login', 'another-login', '--password', 'another-password',
                '--source-address', '2.2.2.2', '--connection-timeout', '100'],
            {
                'connection': ('smtpc.net', 456),
                'smtp':  {'source_address': '2.2.2.2', 'timeout': 100},
                'login': ('some-login', 'another-password'),
            },
            marks=pytest.mark.skip(reason='not implemented yet'),
        ),
    ],
    ids=[
        'smtpc params should have higher priority then profile',
        'connection params from profile',
        'mixed',
        'login and password from different places',
    ]
)
def test_send_with_profile_valid(smtpctmppath, capsys, smtpc_params, profile_params, expected):
    r = callsmtpc(['profiles', 'add', 'simple1', *profile_params], capsys)
    assert r.code == ExitCodes.OK.value, r

    data = load_toml_file(smtpctmppath / config.PREDEFINED_PROFILES_FILE.name)
    profiles = data['profiles']
    assert 'simple1' in profiles

    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']

        r = callsmtpc(['send', '--from', 'sender@smtpc.net', '--to', 'receiver@smtpc.net', '--profile', 'simple1',
            *smtpc_params], capsys)
        assert r.code == ExitCodes.OK.value, r

        mocked_smtp_class.assert_called()
        assert mocked_smtp_class.call_args.kwargs == expected['smtp']

        mocked_smtp.ehlo.assert_called()
        mocked_smtp.connect.assert_called()
        mocked_smtp.sendmail.assert_called()

        smtp_connect_args = mocked_smtp.connect.call_args.args
        assert smtp_connect_args == expected['connection']

        if '--tls' in smtpc_params:
            mocked_smtp.starttls.assert_called()

        if '--login' in smtpc_params:
            mocked_smtp.login.assert_called()
            smtp_login_args = mocked_smtp.login.call_args.args
            assert expected['login'] == smtp_login_args


@pytest.mark.parametrize('smtpc_params, message_params, expected',
    [
        [
            [
                '--subject', 'some-subject', '--from', 'sender@smtpc.net', '--to', 'receiver1@smtpc.net', '--to', 'receiver2@smtpc.net',
                '--cc', 'cc1@smtpc.net', '--cc', 'cc2@smtpc.net', '--bcc', 'bcc1@smtpc.net', '--bcc', 'bcc2@smtpc.net',
                '--body', 'some\nbody',
            ],
            [
                '--subject', 'another-subject', '--from', 'another-sender@smtpc.net',
                '--to', 'another-receiver1@smtpc.net', '--to', 'another-receiver2@smtpc.net',
                '--cc', 'another-cc1@smtpc.net', '--cc', 'another-cc2@smtpc.net',
                '--bcc', 'another-bcc1@smtpc.net', '--bcc', 'another-bcc2@smtpc.net',
                '--body', 'another\nbody'
            ],
            {
                'sender': 'sender@smtpc.net',
                'envelope_from': 'sender@smtpc.net',
                'to': 'receiver1@smtpc.net, receiver2@smtpc.net',
                'cc': 'cc1@smtpc.net, cc2@smtpc.net',
                'envelope_to': [
                    'receiver1@smtpc.net', 'receiver2@smtpc.net',
                    'cc1@smtpc.net', 'cc2@smtpc.net',
                    'bcc1@smtpc.net', 'bcc2@smtpc.net',
                ],
                'subject': 'some-subject', 'body': 'some\nbody',
            }
        ],
        [
            [],
            [
                '--subject', 'another-subject', '--from', 'another-sender@smtpc.net',
                '--to', 'another-receiver1@smtpc.net', '--to', 'another-receiver2@smtpc.net',
                '--cc', 'another-cc1@smtpc.net', '--cc', 'another-cc2@smtpc.net',
                '--bcc', 'another-bcc1@smtpc.net', '--bcc', 'another-bcc2@smtpc.net',
                '--body', 'another\nbody'
            ],
            {
                'sender': 'another-sender@smtpc.net',
                'envelope_from': 'another-sender@smtpc.net',
                'to': 'another-receiver1@smtpc.net, another-receiver2@smtpc.net',
                'cc': 'another-cc1@smtpc.net, another-cc2@smtpc.net',
                'envelope_to': [
                    'another-receiver1@smtpc.net', 'another-receiver2@smtpc.net',
                    'another-cc1@smtpc.net', 'another-cc2@smtpc.net',
                    'another-bcc1@smtpc.net', 'another-bcc2@smtpc.net',
                ],
                'subject': 'another-subject', 'body': 'another\nbody'
            }
        ],
        [
            [
                '--subject', 'some-subject', '--from', 'sender@smtpc.net',
                '--cc', 'cc1@smtpc.net', '--cc', 'cc2@smtpc.net',
            ],
            [
                '--subject', 'another-subject', '--from', 'another-sender@smtpc.net',
                '--to', 'another-receiver1@smtpc.net', '--to', 'another-receiver2@smtpc.net',
                '--cc', 'another-cc1@smtpc.net', '--cc', 'another-cc2@smtpc.net',
                '--bcc', 'another-bcc1@smtpc.net', '--bcc', 'another-bcc2@smtpc.net',
                '--body', 'another\nbody'
            ],
            {
                'sender': 'sender@smtpc.net',
                'envelope_from': 'sender@smtpc.net',
                'to': 'another-receiver1@smtpc.net, another-receiver2@smtpc.net',
                'cc': 'cc1@smtpc.net, cc2@smtpc.net',
                'envelope_to': [
                    'another-receiver1@smtpc.net', 'another-receiver2@smtpc.net',
                    'cc1@smtpc.net', 'cc2@smtpc.net',
                    'another-bcc1@smtpc.net', 'another-bcc2@smtpc.net',
                ],
                'subject': 'some-subject', 'body': 'another\nbody'
            }
        ],
        [
            [
                '--from', 'sender@smtpc.net', '--envelope-from', 'envelope-sender@smtpc.net',
                '--to', 'receiver@smtpc.net', '--envelope-to', 'envelope-receiver@smtpc.net',
            ],
            [
                '--from', 'another-sender@smtpc.net', '--envelope-from', 'another-envelope-sender@smtpc.net',
                '--to', 'another-receiver@smtpc.net', '--envelope-to', 'another-envelope-receiver@smtpc.net',
            ],
            {
                'sender': 'sender@smtpc.net',
                'envelope_from': 'envelope-sender@smtpc.net',
                'to': 'receiver@smtpc.net',
                'cc': None,
                'envelope_to': ['envelope-receiver@smtpc.net'],
                'body': '',
            }
        ],
        [
            [
                '--from', 'sender@smtpc.net', '--to', 'receiver@smtpc.net',
            ],
            [
                '--envelope-from', 'another-envelope-sender@smtpc.net',
                '--envelope-to', 'another-envelope-receiver@smtpc.net',
            ],
            {
                'sender': 'sender@smtpc.net',
                'envelope_from': 'another-envelope-sender@smtpc.net',
                'to': 'receiver@smtpc.net',
                'cc': None,
                'envelope_to': ['another-envelope-receiver@smtpc.net'],
                'body': '',
            }
        ],
    ],
    ids=[
        'smtpc params should have higher priority then message',
        'message params from message',
        'mixed',
        'envelope from smtpc',
        'envelope from message',
    ]
)
def test_send_with_message_valid(smtpctmppath, capsys, smtpc_params, message_params, expected):
    r = callsmtpc(['messages', 'add', 'simple1', *message_params], capsys)
    assert r.code == ExitCodes.OK.value, r

    data = load_toml_file(smtpctmppath / config.PREDEFINED_MESSAGES_FILE.name)
    messages = data['messages']
    assert 'simple1' in messages

    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']

        r = callsmtpc(['send', '--message', 'simple1',
            *smtpc_params], capsys)
        assert r.code == ExitCodes.OK.value, r

        mocked_smtp.sendmail.assert_called()
        smtp_sendmail_args = mocked_smtp.sendmail.call_args.args
        assert smtp_sendmail_args[0] == expected['envelope_from']
        assert smtp_sendmail_args[1] == expected['envelope_to']

        received_message = email.message_from_string(smtp_sendmail_args[2])
        expected_headers = ['Content-Transfer-Encoding', 'Content-Type', 'From', 'MIME-Version',
            'To', 'User-Agent']
        if '--cc' in smtpc_params or '--cc' in message_params:
            expected_headers.append('Cc')
        if '--subject' in smtpc_params or '--subject' in message_params:
            expected_headers.append('Subject')
        assert sorted(received_message.keys()) == sorted(expected_headers)

        assert f"SMTPc/{smtpc.__version__}" in received_message['User-Agent']
        assert received_message['From'] == expected['sender']
        assert received_message['To'] == expected['to']
        assert received_message['Cc'] == expected['cc']
        assert received_message.get_content_type() == 'text/plain'
        if '--subject' in smtpc_params or '--subject' in message_params:
            assert received_message['Subject'] == expected['subject']

        message_body = received_message.as_string().split("\n\n", 1)
        assert len(message_body) == 2, 'No message body found'
        assert message_body[1] == expected['body']


def test_send_interactive_password(smtpctmppath, capsys):
    with \
        mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class,\
        mock.patch('getpass.getpass', lambda: 'pass')\
    :
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(['send', '--from', 'sender@smtpc.net', '--to', 'receiver@smtpc.net', '--login', 'asd', '--password'], capsys)
        assert r.code == ExitCodes.OK.value, r

        mocked_smtp_class.assert_called()

        mocked_smtp.login.assert_called()
        smtp_login_args = mocked_smtp.login.call_args.args
        assert smtp_login_args == ('asd', 'pass')
