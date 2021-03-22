import toml

from smtpc import config
from . import *


def test_config_files_created(smtpctmppath, capsys):
    callsmtpc(capsys=capsys)

    config_file = smtpctmppath / config.CONFIG_FILE.name
    assert config_file.exists(), f'Config file {config_file} not created'

    with config_file.open('r') as fh:
        data = toml.load(fh)
        assert data == {'smtpc': {}}, f'Config file {config_file} has invalid content'

    profiles_file = smtpctmppath / config.PREDEFINED_PROFILES_FILE.name
    assert profiles_file.exists(), f'Profiles file {profiles_file} not created'

    with profiles_file.open('r') as fh:
        data = toml.load(fh)
        assert data == {'profiles': {}}, f'Profiles file {profiles_file} has invalid content'

    messages_file = smtpctmppath / config.PREDEFINED_MESSAGES_FILE.name
    assert messages_file.exists(), f'Messages file {messages_file} not created'

    with messages_file.open('r') as fh:
        data = toml.load(fh)
        assert data == {'messages': {}}, f'Messages file {messages_file} has invalid content'
