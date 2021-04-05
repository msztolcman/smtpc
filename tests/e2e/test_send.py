import email
from unittest import mock

import pytest

import smtpc
from smtpc.enums import ContentType
from . import *


def test_send_simple_valid(smtpctmppath, capsys):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_class:
        smtp = mocked_class.return_value
        smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net'], capsys)

        mocked_class.assert_called()
        smtp.ehlo.assert_called()
        smtp.sendmail.assert_called()

        sendmail_args = smtp.sendmail.call_args.args
        assert sendmail_args[0] == 'send@smtpc.net'
        assert sendmail_args[1] == ['receive@smtpc.net']

        received_message = email.message_from_string(sendmail_args[2])
        assert sorted(received_message.keys()) == ['Content-Transfer-Encoding', 'Content-Type', 'From', 'MIME-Version', 'To', 'User-Agent']

        assert f"SMTPc/{smtpc.__version__}" in received_message['User-Agent']
        assert 'send@smtpc.net' == received_message['From']
        assert 'receive@smtpc.net' == received_message['To']
        assert received_message.get_content_type() == 'text/plain'


@pytest.mark.parametrize('params',
    [
        ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'plain\nmessage'],
        ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'plain\nmessage', '--body-type', ContentType.PLAIN.value],
    ],
    ids=[
        'just --body',
        '--body with --body-type=plain',
    ],
)
def test_send_text_plain_valid(smtpctmppath, capsys, params):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(params, capsys)

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

        message_body = received_message.as_string().split("\n\n", 1)
        assert len(message_body) == 2, 'No message body found'
        assert message_body[1] == 'plain\nmessage'


@pytest.mark.parametrize('params',
    [
        ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'html\nmessage', '--body-type', ContentType.HTML.value],
        ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body-html', 'html\nmessage', '--body-type', ContentType.HTML.value],
        ['send', '--from', 'send@smtpc.net', '--to', 'receive@smtpc.net', '--body', 'html\nmessage', '--body-html', 'ignored', '--body-type', ContentType.HTML.value],
    ],
    ids=[
        '--body with --body-type=html',
        '--body-html with --body-type=html',
        '--body and --body-html with --body-type=html',
    ],
)
def test_send_text_html_valid(smtpctmppath, capsys, params):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(params, capsys)

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
        assert received_message.get_content_type() == 'text/html'

        message_body = received_message.as_string().split("\n\n", 1)
        assert len(message_body) == 2, 'No message body found'
        assert message_body[1] == 'html\nmessage'


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
    ],
    ids=[
        'just --body',
        'just --body-html',
        'both --body and --body-html',
    ]
)
def test_send_alternative_valid(smtpctmppath, capsys, params, expected_body):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_smtp_class:
        mocked_smtp = mocked_smtp_class.return_value
        mocked_smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(params, capsys)

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
        # 'just --body-html',
        # 'both --body and --body-html',
    ]
)
def test_send_raw(smtpctmppath, capsys, params, expected_body):
    with mock.patch('smtplib.SMTP', autospec=True) as mocked_class:
        smtp = mocked_class.return_value
        smtp.connect.return_value = ['250', 'OK, mocked']
        r = callsmtpc(params, capsys)

        mocked_class.assert_called()
        smtp.ehlo.assert_called()
        smtp.sendmail.assert_called()

        smtp_sendmail_args = smtp.sendmail.call_args.args
        assert smtp_sendmail_args[0] == 'send@smtpc.net'
        assert smtp_sendmail_args[1] == ['receive@smtpc.net']

        received_message = email.message_from_string(smtp_sendmail_args[2])
        assert sorted(received_message.keys()) == []
        assert received_message.get_content_type() == 'text/plain'
        assert received_message.as_string() == expected_body
