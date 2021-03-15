from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Any

from . import ContentType
from .config import EMPTY
from .defaults import DEFAULTS_VALUES_MESSAGE
from .predefined_messages import PredefinedMessage


class BuildMessage:
    __slots__ = (
        'subject',
        'envelope_from', 'address_from',
        'envelope_to', 'address_to', 'address_cc',
        'body_type', 'body_html', 'body_plain',
        'headers',
        'predefined_message',
    )

    def __init__(self, *,
        subject: Optional[str],
        envelope_from: Optional[str],
        address_from: Optional[str],
        envelope_to: Optional[List[str]],
        address_to: Optional[List[str]],
        address_cc: Optional[List[str]],
        body_type: ContentType,
        body_html: Optional[str] = None,
        body_plain: Optional[str] = None,
        headers: Optional[List[str]] = None,
        message: Optional[PredefinedMessage] = None
    ):
        self.predefined_message = message

        message_fields = {
            'subject': subject,
            'envelope_from': envelope_from,
            'address_from': address_from,
            'envelope_to': envelope_to,
            'address_to': address_to,
            'address_cc': address_cc,
            'body_type': body_type,
            'body_html': body_html,
            'body_plain': body_plain,
            'headers': headers,
        }
        for name in message_fields:
            self._set_property(name, message_fields[name], message, DEFAULTS_VALUES_MESSAGE)

    def execute(self) -> MIMEBase:
        if self.body_type == ContentType.ALTERNATIVE:
            message = MIMEMultipart('alternative')
            if self.body_plain:
                message.attach(MIMEText(self.body_plain, 'plain'))
            if self.body_html:
                message.attach(MIMEText(self.body_html, 'html'))
        elif self.body_type == ContentType.PLAIN:
            message = MIMEText(self.body_plain, 'plain')
        elif self.body_type == ContentType.HTML:
            message = MIMEText(self.body_html, 'html')

        for header in self.headers:
            header_name, header_value = header.split('=', 1)
            message[header_name.strip()] = header_value.strip()

        if self.subject:
            message['Subject'] = self.subject
        message['From'] = self.address_from or self.envelope_from
        if self.address_to or self.address_cc:
            if self.address_to:
                message['To'] = ', '.join(self.address_to)
            if self.address_cc:
                message['Cc'] = ', '.join(self.address_cc)
        else:
            message['To'] = ', '.join(self.envelope_to)

        return message

    def _set_property(self, name: str, initial: Any, low_prio: PredefinedMessage, defaults: dict):
        value = initial
        if low_prio and initial is EMPTY:
            value = getattr(low_prio, name)
        if value is EMPTY:
            value = defaults[name]
        setattr(self, name, value)
