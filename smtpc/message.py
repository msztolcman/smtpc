import enum
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List


class ContentType(enum.Enum):
    PLAIN = 'plain'
    HTML = 'html'
    ALTERNATIVE = 'alternative'


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
) -> MIMEBase:
    if not headers:
        headers = []

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
