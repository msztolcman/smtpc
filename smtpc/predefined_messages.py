import enum
from typing import Optional, List

import toml

from .config import PREDEFINED_MESSAGES_FILE, save_toml_file
from .enums import ContentType
from .utils import guess_content_type


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
        result = {}
        for key in self.__slots__:
            if key == 'name':
                continue
            value = getattr(self, key)
            if isinstance(value, enum.Enum):
                value = value.value
            result[key] = value
        return result

    def __str__(self):
        d = self.to_dict()
        return '<PredefinedMessage ' + ', '.join([f'{k}={v}' for k, v in d.items()]) + '>'

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
                body_type=ContentType(guess_content_type(message.get('body_type'), message.get('body_plain'), message.get('body_html'))),
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
