import os
import pathlib
from typing import Optional, Dict

import fileperms
import toml

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
PROFILES_FILE = CONFIG_DIR / 'profiles.toml'
CONFIG_FILE = CONFIG_DIR / 'config.toml'


def ensure_config_files():
    dir_perms = fileperms.Permissions()
    dir_perms.owner_read = True
    dir_perms.owner_write = True
    dir_perms.owner_exec = True

    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(mode=int(dir_perms), parents=True, exist_ok=True)

    if not PROFILES_FILE.is_file():
        save_toml_file(PROFILES_FILE, {'profiles': {}})

    if not CONFIG_FILE.is_file():
        save_toml_file(CONFIG_FILE, {'smtpc': {}})


def save_toml_file(file: pathlib.Path, data: dict):
    file_perms = fileperms.Permissions()
    file_perms.owner_read = True
    file_perms.owner_write = True

    file.touch(mode=int(file_perms))
    with file.open('w') as fh:
        toml.dump(data, fh)


class Profile:
    __slots__ = (
        'name', 'login', 'password',
        'host', 'port', 'ssl', 'tls',
        'connection_timeout', 'identify_as', 'source_address',
    )

    def __init__(self,
        name: str, *,
        login: Optional[str] = None,
        password: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        ssl: Optional[bool] = None,
        tls: Optional[bool] = None,
        connection_timeout: Optional[int] = None,
        identify_as: Optional[str] = None,
        source_address: Optional[str] = None,
    ):
        self.name = name
        self.login = login
        self.password = password
        self.host = host
        self.port = port
        self.ssl = ssl
        self.tls = tls
        self.connection_timeout = connection_timeout
        self.identify_as = identify_as
        self.source_address = source_address

    def to_dict(self):
        r = {
            k: getattr(self, k)
            for k in self.__slots__
            if k != 'name'
        }
        return r

    def __str__(self):
        d = []
        for k in self.__slots__:
            if k == 'password':
                d.append(f"{k}=***")
            else:
                d.append(f"{k}={getattr(self, k)}")
        return '<Profile ' + ', '.join(d) + '>'
    __repr__ = __str__


class Profiles(dict):
    @classmethod
    def read(cls) -> 'Profiles':
        with PROFILES_FILE.open('r') as fh:
            data = toml.load(fh)

        p = cls()
        if 'profiles' not in data:
            return p

        for name, profile in data['profiles'].items():
            p[name] = Profile(
                name=name,
                login=profile.get('login'),
                password=profile.get('password'),
                host=profile.get('host'),
                port=profile.get('port'),
                ssl=profile.get('ssl'),
                tls=profile.get('tls'),
                connection_timeout=profile.get('connection_timeout'),
                identify_as=profile.get('identify_as'),
                source_address=profile.get('source_address'),
            )

        return p

    def add(self, profile: Profile):
        self[profile.name] = profile
        save_toml_file(PROFILES_FILE, {
            'profiles': {
                name: profile.to_dict()
                for name, profile in self.items()
            }
        })


class Config:
    pass
