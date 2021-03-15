from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List

from . import ContentType
from .config import EMPTY
from .defaults import DEFAULTS_VALUES_MESSAGE
from .predefined_messages import PredefinedMessage


def build_message(*,
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
) -> MIMEBase:
    if message:
        if subject is EMPTY:
            subject = message.subject
        if envelope_from is EMPTY:
            envelope_from = message.envelope_from
        if address_from is EMPTY:
            address_from = message.address_from
        if envelope_to is EMPTY:
            envelope_to = message.envelope_to
        if address_to is EMPTY:
            address_to = message.address_to
        if address_cc is EMPTY:
            address_cc = message.address_cc
        if body_type is EMPTY:
            body_type = message.body_type
        if body_html is EMPTY:
            body_html = message.body_html
        if body_plain is EMPTY:
            body_plain = message.body_plain
        if headers is EMPTY:
            headers = message.headers

    if subject is EMPTY:
        subject = DEFAULTS_VALUES_MESSAGE['subject']
    if envelope_from is EMPTY:
        envelope_from = DEFAULTS_VALUES_MESSAGE['envelope_from']
    if address_from is EMPTY:
        address_from = DEFAULTS_VALUES_MESSAGE['address_from']
    if envelope_to is EMPTY:
        envelope_to = DEFAULTS_VALUES_MESSAGE['envelope_to']
    if address_to is EMPTY:
        address_to = DEFAULTS_VALUES_MESSAGE['address_to']
    if address_cc is EMPTY:
        address_cc = DEFAULTS_VALUES_MESSAGE['address_cc']
    if body_type is EMPTY:
        body_type = DEFAULTS_VALUES_MESSAGE['body_type']
    if body_html is EMPTY:
        body_html = DEFAULTS_VALUES_MESSAGE['body_html']
    if body_plain is EMPTY:
        body_plain = DEFAULTS_VALUES_MESSAGE['body_plain']
    if headers is EMPTY:
        headers = DEFAULTS_VALUES_MESSAGE['headers']

    if body_type == ContentType.ALTERNATIVE:
        message = MIMEMultipart('alternative')
        if body_plain:
            message.attach(MIMEText(body_plain, 'plain'))
        if body_html:
            message.attach(MIMEText(body_html, 'html'))
    elif body_type == ContentType.PLAIN:
        message = MIMEText(body_plain, 'plain')
    elif body_type == ContentType.HTML:
        message = MIMEText(body_html, 'html')

    for header in headers:
        header_name, header_value = header.split('=', 1)
        message[header_name.strip()] = header_value.strip()

    if subject:
        message['Subject'] = subject
    message['From'] = address_from or envelope_from
    if address_to or address_cc:
        if address_to:
            message['To'] = ', '.join(address_to)
        if address_cc:
            message['Cc'] = ', '.join(address_cc)
    else:
        message['To'] = ', '.join(envelope_to)

    return message
