import enum
import os
import pathlib
from typing import Optional, Dict, List

import fileperms
import toml

from . import ContentType

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

    file.touch(mode=int(file_perms))
    with file.open('w') as fh:
        toml.dump(data, fh)


class PredefinedProfile:
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
            k: getattr(self, k) if not isinstance(getattr(self, k), enum.Enum) else getattr(self, k).value
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
        return '<PredefinedProfile ' + ', '.join(d) + '>'
    __repr__ = __str__


class PredefinedProfiles(dict):
    @classmethod
    def read(cls) -> 'PredefinedProfiles':
        with PREDEFINED_PROFILES_FILE.open('r') as fh:
            data = toml.load(fh)

        p = cls()
        if 'profiles' not in data:
            return p

        for name, profile in data['profiles'].items():
            p[name] = PredefinedProfile(
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

    def add(self, profile: PredefinedProfile):
        self[profile.name] = profile
        save_toml_file(PREDEFINED_PROFILES_FILE, {
            'profiles': {
                name: profile.to_dict()
                for name, profile in self.items()
            }
        })


class PredefinedMessage:
    __slots__ = (
        'name', 'envelope_from', 'address_from', 'envelope_to', 'address_to', 'address_cc', 'address_bcc',
        'subject', 'body_plain', 'body_html', 'body_raw', 'body_type', 'headers',
    )

    def __init__(self,
        name: str, *,
        envelope_from: Optional[str] = None,
        address_from: Optional[str] = None,
        envelope_to: Optional[List[str]] = None,
        address_to: Optional[List[str]] = None,
        address_cc: Optional[List[str]] = None,
        address_bcc: Optional[List[str]] = None,
        subject: Optional[str] = None,
        body_plain: Optional[str] = None,
        body_html: Optional[str] = None,
        body_raw: Optional[str] = None,
        body_type: Optional[str] = None,
        headers: Optional[List[str]] = None,
    ):
        self.name = name
        self.envelope_from = envelope_from
        self.address_from = address_from
        self.envelope_to = envelope_to
        self.address_to = address_to
        self.address_cc = address_cc
        self.address_bcc = address_bcc
        self.subject = subject
        self.body_plain = body_plain
        self.body_html = body_html
        self.body_raw = body_raw
        self.body_type = body_type
        self.headers = headers

    def to_dict(self):
        r = {
            k: getattr(self, k) if not isinstance(getattr(self, k), enum.Enum) else getattr(self, k).value
            for k in self.__slots__
            if k != 'name'
        }
        return r

    def __str__(self):
        d = []
        for k in self.__slots__:
            d.append(f"{k}={getattr(self, k)}")
        return '<PredefinedMessage ' + ', '.join(d) + '>'

    __repr__ = __str__


class PredefinedMessages(dict):
    @classmethod
    def read(cls) -> 'PredefinedMessages':
        with PREDEFINED_MESSAGES_FILE.open('r') as fh:
            data = toml.load(fh)

        m = cls()
        if 'messages' not in data:
            return m

        for name, message in data['messages'].items():
            m[name] = PredefinedMessage(
                name=name,
                envelope_from=message.get('envelope_from'),
                address_from=message.get('address_from'),
                envelope_to=message.get('envelope_to'),
                address_to=message.get('address_to'),
                address_cc=message.get('address_cc'),
                address_bcc=message.get('address_bcc'),
                subject=message.get('subject'),
                body_plain=message.get('body_plain'),
                body_html=message.get('body_html'),
                body_raw=message.get('body_raw'),
                body_type=ContentType(message.get('body_type')),
                headers=message.get('headers'),
            )

        return m

    def add(self, message: PredefinedMessage):
        self[message.name] = message
        save_toml_file(PREDEFINED_MESSAGES_FILE, {
            'messages': {
                name: message.to_dict()
                for name, message in self.items()
            }
        })


class Config:
    pass
