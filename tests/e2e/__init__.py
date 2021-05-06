__all__ = ['CallResult', 'callsmtpc', 'load_toml_file', 'smtpctmppath', 'prepare_smtp_mock', ]

from collections import namedtuple
from unittest import mock

import pytest
import toml

from smtpc import config, cli

CallResult = namedtuple('CallResult', 'code, out, err')


class LocalExit(Exception):
    def __init__(self, code):
        self.code = code


def local_exitc(code):
    raise LocalExit(code)


def callsmtpc(args=None, capsys=None) -> CallResult:
    if not args:
        args = []

    config._generate_paths()
    with \
        mock.patch('sys.exit', local_exitc),\
        pytest.raises(LocalExit) as exc\
    :
        cli.main(args)

    captured = capsys.readouterr()
    stdout, stderr = captured.out, captured.err
    return CallResult(exc.value.code, stdout, stderr)


def load_toml_file(name):
    with name.open('r') as fh:
        data = toml.load(fh)
    return data


@pytest.fixture
def smtpctmppath(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_SMTPC_CONFIG_DIR, str(tmp_path))
    return tmp_path


def prepare_smtp_mock(mocked_smtp):
    mocked_smtp.connect.return_value = ['250', b'OK, mocked']
    mocked_smtp.ehlo_resp = mocked_smtp.helo_resp = None
    mocked_smtp.ehlo.return_value = [250]
