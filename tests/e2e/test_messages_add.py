import pytest

from smtpc import config
from smtpc.enums import ExitCodes, ContentType

from . import *


@pytest.mark.parametrize('params, expected',
    [
        [
            ['--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net'],
            {'address_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net'], 'body_type': ContentType.PLAIN.value}
        ],
        [
            ['--envelope-from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net'],
            {'envelope_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net'], 'body_type': ContentType.PLAIN.value}
        ],
        [
            ['--from', 'smtpc@smtpc.net', '--envelope-to', 'receiver@smtpc.net'],
            {'address_from': 'smtpc@smtpc.net', 'envelope_to': ['receiver@smtpc.net'], 'body_type': ContentType.PLAIN.value}
        ],
        [
            ['--envelope-from', 'smtpc@smtpc.net', '--envelope-to', 'receiver@smtpc.net'],
            {'envelope_from': 'smtpc@smtpc.net', 'envelope_to': ['receiver@smtpc.net'], 'body_type': ContentType.PLAIN.value}
        ],
        [
            ['--from', 'smtpc@smtpc.net', '--cc', 'receiver@smtpc.net'],
            {'address_from': 'smtpc@smtpc.net', 'address_cc': ['receiver@smtpc.net'], 'body_type': ContentType.PLAIN.value}
        ],
        [
            ['--from', 'smtpc@smtpc.net', '--bcc', 'receiver@smtpc.net'],
            {'address_from': 'smtpc@smtpc.net', 'address_bcc': ['receiver@smtpc.net'], 'body_type': ContentType.PLAIN.value}
        ],
        [
            ['--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net', '--to', 'receiver2@smtpc.net'],
            {'address_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net', 'receiver2@smtpc.net'], 'body_type': ContentType.PLAIN.value}
        ],
        [
            ['--from', 'smtpc@smtpc.net', '--envelope-to', 'receiver@smtpc.net', '--envelope-to', 'receiver2@smtpc.net'],
            {'address_from': 'smtpc@smtpc.net', 'envelope_to': ['receiver@smtpc.net', 'receiver2@smtpc.net'], 'body_type': ContentType.PLAIN.value}
        ],
        [
            ['--envelope-from', 'smtpc@smtpc.net', '--envelope-to', 'receiver@smtpc.net', '--to', 'receiver2@smtpc.net'],
            {'envelope_from': 'smtpc@smtpc.net', 'envelope_to': ['receiver@smtpc.net'], 'address_to': ['receiver2@smtpc.net'],
                'body_type': ContentType.PLAIN.value}
        ],
        [
            [
                '--envelope-from', 'env-smtpc@smtpc.net', '--envelope-to', 'env-receiver@smtpc.net',
                '--to', 'receiver1@smtpc.net', '--to', 'receiver2@smtpc.net',
                '--cc', 'cc1@smtpc.net', '--cc', 'cc2@smtpc.net',
                '--bcc', 'bcc1@smtpc.net', '--bcc', 'bcc2@smtpc.net',
                '--subject', 'some subject',
                '--reply-to', 'reply-to@smtpc.net',
                '--header', 'SomeHeader1=some header 1', '--header', 'SomeHeader2=some header 2',
                '--body-plain', 'some plain body', '--body-html', 'some html body',
            ],
            {
                'envelope_from': 'env-smtpc@smtpc.net', 'envelope_to': ['env-receiver@smtpc.net'],
                'address_to': ['receiver1@smtpc.net', 'receiver2@smtpc.net'],
                'address_cc': ['cc1@smtpc.net', 'cc2@smtpc.net'],
                'address_bcc': ['bcc1@smtpc.net', 'bcc2@smtpc.net'],
                'subject': 'some subject',
                'reply_to': ['reply-to@smtpc.net'],
                'headers': ['SomeHeader1=some header 1', 'SomeHeader2=some header 2'],
                'body_type': ContentType.ALTERNATIVE.value, 'body_plain': 'some plain body', 'body_html': 'some html body',
            },
        ],
    ],
    ids=[
        'from and to',
        'envelope-from and to',
        'from and envelope-to',
        'envelope-from and envelope-to',
        'from and cc',
        'from and bcc',
        'multiple to',
        'multiple envelope-to',
        'mixing --envelope-from/to with --from/to',
        'all params given',
    ],
)
def test_add_message_valid(smtpctmppath, capsys, params, expected):
    r = callsmtpc(['messages', 'add', 'simple1', *params], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(smtpctmppath / config.PREDEFINED_MESSAGES_FILE.name)
    messages = data['messages']
    assert 'simple1' in messages
    assert messages['simple1'] == expected


@pytest.mark.parametrize('params, expected_in_err',
    [
        [
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body-type', 'invalid',
            ],
            '--body-type: invalid choice: \'invalid\''
        ],
        [
            [],
            'Any sender (--envelope-from or --from) required',
        ],
        [
            ['--from', 'a'],
            'Any receiver (--envelope-to,--to, --cc, --bcc) required',
        ],
        [
            ['--to', 'a'],
            'Any sender (--envelope-from or --from) required',
        ],
    ],
    ids=[
        'invalid --body-type',
        'missing to/cc/bcc/envelope-to and from/envelope-from',
        'missing to/envelope-to',
        'missing from/envelope-from',
    ]
)
def test_add_message_error(smtpctmppath, capsys, params, expected_in_err):
    r = callsmtpc(['messages', 'add', 'simple1', *params], capsys)

    assert r.code == ExitCodes.OTHER.value
    assert expected_in_err in r.err


@pytest.mark.parametrize('params, expected',
    [
        [
            ['--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net'],
            {'address_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net'], 'body_type': ContentType.PLAIN.value}
        ],
        [
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body-plain', 'some plain body',
            ],
            {
                'address_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net'],
                'body_type': ContentType.PLAIN.value, 'body_plain': 'some plain body',
            }
        ],
        [
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body-html', 'some html body',
            ],
            {
                'address_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net'],
                'body_type': ContentType.HTML.value, 'body_html': 'some html body',
            }
        ],
        [
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body-plain', 'some plain body', '--body-html', 'some html body',
            ],
            {
                'address_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net'],
                'body_type': ContentType.ALTERNATIVE.value,
                'body_plain': 'some plain body', 'body_html': 'some html body',
            }
        ],
        [
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body-plain', 'some plain body', '--body-type', ContentType.HTML.value,
            ],
            {
                'address_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net'],
                'body_type': ContentType.HTML.value,
                'body_plain': 'some plain body',
            }
        ],
        [
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body-html', 'some html body', '--body-type', ContentType.PLAIN.value,
            ],
            {
                'address_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net'],
                'body_type': ContentType.PLAIN.value,
                'body_html': 'some html body',
            }
        ],
        pytest.param(
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body', 'some body',
            ],
            {
                'address_from': 'smtpc@smtpc.net', 'address_to': ['receiver@smtpc.net'],
                'body_type': ContentType.PLAIN.value,
                'body_plain': 'some body',
            },
            marks=pytest.mark.skip(reason='not finished yet')
        ),
    ],
    ids=[
        'no body, just body type',
        'just plain body',
        'just html body',
        'alternative',
        'plain body with body type set to html',
        'html body with body type set to plain',
        'just --body',
    ]
)
def test_add_message_body_valid(smtpctmppath, capsys, params, expected):
    r = callsmtpc(['messages', 'add', 'simple1', *params], capsys)

    assert r.code == ExitCodes.OK.value
    data = load_toml_file(smtpctmppath / config.PREDEFINED_MESSAGES_FILE.name)
    messages = data['messages']
    assert 'simple1' in messages
    assert messages['simple1'] == expected


@pytest.mark.parametrize('params, expected_in_err',
    [
        [
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body-plain', 'some plain body', '--raw-body'
            ],
            'Use --raw-body only with --body param'
        ],
        [
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body-html', 'some html body', '--raw-body'
            ],
            'Use --raw-body only with --body param'
        ],
        [
            [
                '--from', 'smtpc@smtpc.net', '--to', 'receiver@smtpc.net',
                '--body-type', ContentType.PLAIN.value, '--raw-body'
            ],
            'Use --raw-body only with --body param'
        ],
    ],
    ids=[
        'body plain with --raw-body param',
        'body html with --raw-body param',
        'body type with --raw-body param',
    ]
)
def test_add_message_raw_body_error(smtpctmppath, capsys, params, expected_in_err):
    r = callsmtpc(['messages', 'add', 'simple1', *params], capsys)

    assert r.code == ExitCodes.OTHER.value
    assert expected_in_err in r.err
