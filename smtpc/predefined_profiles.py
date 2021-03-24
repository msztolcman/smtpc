import enum
from typing import Optional, NoReturn

import toml

from . import config


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
    ) -> NoReturn:
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

    def to_dict(self) -> dict:
        result = {}
        for key in self.__slots__:
            if key == 'name':
                continue
            value = getattr(self, key)
            if isinstance(value, enum.Enum):
                value = value.value
            result[key] = value
        return result

    def __str__(self) -> str:
        d = self.to_dict()
        d['password'] = '***'
        return '<PredefinedProfile ' + ', '.join([f'{k}={v}' for k, v in d.items()]) + '>'
    __repr__ = __str__


class PredefinedProfiles(dict):
    @classmethod
    def read(cls) -> 'PredefinedProfiles':
        with config.PREDEFINED_PROFILES_FILE.open('r') as fh:
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

    def add(self, new_profile: PredefinedProfile) -> NoReturn:
        self[new_profile.name] = new_profile
        config.save_toml_file(config.PREDEFINED_PROFILES_FILE, {
            'profiles': {
                name: profile.to_dict()
                for name, profile in self.items()
            },
        })

    def delete(self, profile_name: str) -> NoReturn:
        del self[profile_name]

        config.save_toml_file(config.PREDEFINED_PROFILES_FILE, {
            'profiles': {
                name: profile.to_dict()
                for name, profile in self.items()
            },
        })
