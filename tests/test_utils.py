import pytest

from smtpc.enums import ContentType
from smtpc.utils import guess_content_type, determine_ssl_tls_by_port


@pytest.mark.parametrize('body_type,body_plain,body_html,expected', [
    ['unknown', None, None, ContentType.PLAIN],
    ['plain', None, None, ContentType.PLAIN],
    ['html', None, None, ContentType.HTML],
    ['html', 'a', None, ContentType.HTML],
    ['html', None, 'a', ContentType.HTML],
    ['plain', None, None, ContentType.PLAIN],
    ['plain', 'a', None, ContentType.PLAIN],
    ['plain', None, 'a', ContentType.PLAIN],
    [None, 'a', None, ContentType.PLAIN],
    [None, None, 'a', ContentType.HTML],
    [None, 'a', 'a', ContentType.ALTERNATIVE],
])
def test_guess_content_type(body_type, body_plain, body_html, expected):
    assert guess_content_type(body_type, body_plain, body_html) == expected


@pytest.mark.parametrize('port, ssl, tls, no_ssl, no_tls, expected', [
    [123, None, None, None, None, (None, None)],
    [ 25, None, None, None, None, (None, None)],
    [465, None, None, None, None, (True, None)],
    [587, None, None, None, None, (None, True)],

    [123, True, None, None, None, (True, None)],
    [123, None, True, None, None, (None, True)],
    [123, True, None, True, None, (True, None)],
    [123, None, True, None, True, (None, True)],


    [465, None, None, None, None, (True, None)],
    [465, True, None, None, None, (True, None)],
    [465, None, True, None, None, (None, True)],
    [465, None, None, True, None, (None, None)],
    [465, None, None, None, True, (True, None)],

    [587, None, None, None, None, (None, True)],
    [587, True, None, None, None, (True, None)],
    [587, None, True, None, None, (None, True)],
    [587, None, None, True, None, (None, True)],
    [587, None, None, None, True, (None, None)],
])
def test_determine_ssl_tls_by_port(port, ssl, tls, no_ssl, no_tls, expected):
    assert determine_ssl_tls_by_port(port, ssl, tls, no_ssl, no_tls) == expected
