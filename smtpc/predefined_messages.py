import copy
import enum
from typing import Optional, List, NoReturn

import toml

from . import config
from .enums import ContentType


class PredefinedMessage:
    __slots__ = (
        'name', 'envelope_from', 'address_from', 'envelope_to', 'address_to', 'address_cc', 'address_bcc', 'reply_to',
        'subject', 'body', 'body_html', 'raw_body', 'body_type', 'headers',
    )

    def __init__(self,
        name: str, *,
        envelope_from: Optional[str] = None,
        address_from: Optional[str] = None,
        envelope_to: Optional[List[str]] = None,
        address_to: Optional[List[str]] = None,
        address_cc: Optional[List[str]] = None,
        address_bcc: Optional[List[str]] = None,
        reply_to: Optional[List[str]] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        body_html: Optional[str] = None,
        raw_body: Optional[bool] = None,
        body_type: Optional[ContentType] = None,
        headers: Optional[List[str]] = None,
    ) -> NoReturn:
        self.name = name
        self.envelope_from = envelope_from
        self.address_from = address_from
        self.envelope_to = envelope_to
        self.address_to = address_to
        self.address_cc = address_cc
        self.address_bcc = address_bcc
        self.reply_to = reply_to
        self.subject = subject
        self.body = body
        self.body_html = body_html
        self.raw_body = raw_body
        self.body_type = body_type
        self.headers = headers

    def to_dict(self) -> dict:
        keys = list(copy.copy(self.__slots__))
        keys.remove('name')
        result = {}
        for key in keys:
            value = getattr(self, key)
            if isinstance(value, enum.Enum):
                value = value.value
            result[key] = value
        return result

    def __str__(self) -> str:
        d = self.to_dict()
        items = [
            f'{k}={v}' if k not in ('body', 'body_html') else f'{k}=[{len(v)} characters]'
            for k, v in d.items()
        ]
        return '<PredefinedMessage ' + ', '.join(items) + '>'

    __repr__ = __str__


class PredefinedMessages(dict):
    @classmethod
    def read(cls) -> 'PredefinedMessages':
        with config.PREDEFINED_MESSAGES_FILE.open('r') as fh:
            data = toml.load(fh)

        m = cls()
        if 'messages' not in data:
            return m

        rewrite_messages = False
        for name, message in data['messages'].items():
            body = message.get('body')
            raw_body = None

            if message.get('body_raw'):
                body = message['body_raw']
                raw_body = True
                rewrite_messages = True
            elif message.get('body_plain'):
                body = message['body_plain']
                rewrite_messages = True

            m[name] = PredefinedMessage(
                name=name,
                envelope_from=message.get('envelope_from'),
                address_from=message.get('address_from'),
                envelope_to=message.get('envelope_to'),
                address_to=message.get('address_to'),
                address_cc=message.get('address_cc'),
                address_bcc=message.get('address_bcc'),
                reply_to=message.get('reply_to'),
                subject=message.get('subject'),
                body=body,
                body_html=message.get('body_html'),
                raw_body=raw_body,
                body_type=ContentType(message['body_type']) if 'body_type' in message else None,
                headers=message.get('headers'),
            )

        if rewrite_messages:
            m._save()

        return m

    def add(self, new_message: PredefinedMessage) -> NoReturn:
        self[new_message.name] = new_message
        self._save()

    def delete(self, message_name: str) -> NoReturn:
        del self[message_name]
        self._save()

    def _save(self) -> NoReturn:
        config.save_toml_file(config.PREDEFINED_MESSAGES_FILE, {
            'messages': {
                name: message.to_dict()
                for name, message in self.items()
            },
        })
