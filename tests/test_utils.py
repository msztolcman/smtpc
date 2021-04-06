import pytest

from smtpc.utils import determine_ssl_tls_by_port


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
