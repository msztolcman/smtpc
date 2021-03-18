import os
import pathlib
import sys
import tempfile

import fileperms
import structlog
import toml

logger = structlog.get_logger()
ENV_SMTPC_CONFIG_DIR = 'SMTPC_CONFIG_DIR'
ENV_XDG_CONFIG_HOME = 'XDG_CONFIG_HOME'
XDG_CONFIG_HOME = pathlib.Path('.config')
CONFIG_DIRNAME = 'smtpc'


def get_config_dir() -> pathlib.Path:
    env_config_dir = os.environ.get(ENV_SMTPC_CONFIG_DIR)
    if env_config_dir:
        return pathlib.Path(env_config_dir)

    home_dir = pathlib.Path.home()

    xdg_config_home_dir = os.environ.get(
        ENV_XDG_CONFIG_HOME,
        home_dir / XDG_CONFIG_HOME
    )
    return pathlib.Path(xdg_config_home_dir) / CONFIG_DIRNAME


CONFIG_DIR = get_config_dir()
PREDEFINED_PROFILES_FILE = CONFIG_DIR / 'profiles.toml'
CONFIG_FILE = CONFIG_DIR / 'config.toml'
PREDEFINED_MESSAGES_FILE = CONFIG_DIR / 'messages.toml'


def ensure_config_files():
    dir_perms = fileperms.Permissions()
    dir_perms.owner_read = True
    dir_perms.owner_write = True
    dir_perms.owner_exec = True

    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(mode=int(dir_perms), parents=True, exist_ok=True)

    if not PREDEFINED_PROFILES_FILE.is_file():
        save_toml_file(PREDEFINED_PROFILES_FILE, {'profiles': {}})

    if not CONFIG_FILE.is_file():
        save_toml_file(CONFIG_FILE, {'smtpc': {}})

    if not PREDEFINED_MESSAGES_FILE.is_file():
        save_toml_file(PREDEFINED_MESSAGES_FILE, {'messages': {}})


def save_toml_file(file: pathlib.Path, data: dict):
    file_perms = fileperms.Permissions()
    file_perms.owner_read = True
    file_perms.owner_write = True

    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=file.parent, delete=False, prefix='tmp.', suffix='.toml') as fh:
            tmp_file = pathlib.Path(fh.name)
            toml.dump(data, fh)
    except Exception as exc:
        logger.error('cannot save config file', file=str(file), message=str(exc))
        return

    tmp_file.chmod(file_perms)

    bak_file = file.parent / (file.name + '.bak')
    try:
        file.rename(bak_file)
    except Exception as exc:
        logger.error('cannot create backup file', file=str(bak_file), message=str(exc))
        return

    try:
        tmp_file.rename(file)
    except Exception as exc:
        logger.error('cannot create new config file', bak_file=str(bak_file), new_config=str(tmp_file), message=str(exc))
        print(f"Below content should be saved in {file}:", file=sys.stderr)
        print(toml.dumps(data), file=sys.stderr)
        return


class Config:
    pass
