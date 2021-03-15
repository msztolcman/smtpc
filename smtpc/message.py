import smtplib
import socket
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Any, Union

import structlog

from .defaults import DEFAULTS_VALUES_MESSAGE, DEFAULTS_VALUES_PROFILE
from .enums import ContentType, ExitCodes
from .predefined_messages import PredefinedMessage
from .predefined_profiles import PredefinedProfile
from .utils import exit, guess_content_type

logger = structlog.get_logger()


class Builder:
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
        self.body_type = ContentType(guess_content_type(self.body_type, self.body_plain, self.body_html))

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

    def _set_property(self, name: str, initial: Any, low_prio: Optional[PredefinedMessage], defaults: dict):
        value = initial
        if low_prio and initial is None:
            value = getattr(low_prio, name)
        if value is None:
            value = defaults[name]
        setattr(self, name, value)


class Sender:
    __slots__ = (
        'connection_timeout', 'source_address',
        'host', 'port', 'identify_as', 'ssl', 'tls', 'no_ssl', 'no_tls',
        'login', 'password',
        'envelope_from', 'address_from',
        'envelope_to', 'address_to', 'address_cc', 'address_bcc',
        'message_body', 'predefined_profile', 'predefined_message',
        'debug_level',
    )

    def __init__(self, *,
        connection_timeout: int,
        source_address: Optional[str],
        debug_level: Optional[int],
        host: str,
        port: int,
        identify_as: Optional[str],
        tls: bool,
        no_tls: bool,
        ssl: bool,
        no_ssl: bool,
        login: Optional[str],
        password: Optional[str],
        envelope_from: Optional[str],
        address_from: Optional[str],
        envelope_to: Optional[List[str]],
        address_to: Optional[List[str]],
        address_cc: Optional[List[str]],
        address_bcc: Optional[List[str]],
        message_body: Optional[Union[MIMEBase, str]],
        predefined_profile: Optional[PredefinedProfile],
        predefined_message: Optional[PredefinedMessage],
    ):
        self.predefined_profile = predefined_profile
        self.predefined_message = predefined_message
        self.debug_level = debug_level
        self.message_body = message_body
        self.no_ssl = no_ssl
        self.no_tls = no_tls

        if not ssl and not tls:
            if port == 465 and not no_ssl:
                ssl = True
            elif port == 587 and not no_tls:
                tls = True

        if predefined_profile:
            logger.debug('using connection details from predefined profile', profile=predefined_profile.name)

        profile_fields = {
            'login': login,
            'password': password,
            'host': host,
            'port': port,
            'ssl': ssl,
            'tls': tls,
            'connection_timeout': connection_timeout,
            'identify_as': identify_as,
            'source_address': source_address,
        }
        for name in profile_fields:
            self._set_property(name, profile_fields[name], predefined_profile, DEFAULTS_VALUES_PROFILE)

        message_fields = {
            'envelope_from': envelope_from,
            'address_from': address_from,
            'envelope_to': envelope_to,
            'address_to': address_to,
            'address_cc': address_cc,
            'address_bcc': address_bcc,
        }
        for name in message_fields:
            self._set_property(name, message_fields[name], predefined_message, DEFAULTS_VALUES_MESSAGE)

        if self.debug_level > 1:
            logger.debug('profiles settings', **{k: getattr(self, k) for k in profile_fields})
            logger.debug('message settings', **{k: getattr(self, k) for k in message_fields})

    def execute(self):
        if self.ssl:
            logger.debug('connecting using ssl', host=self.host, port=self.port,
                connection_timeout=self.connection_timeout, source_address=self.source_address)
            # don't pass host, don't want to connect yet!
            smtp = smtplib.SMTP_SSL(timeout=self.connection_timeout, source_address=self.source_address)
        else:
            logger.debug('connecting using plain connection', host=self.host, port=self.port,
                connection_timeout=self.connection_timeout, source_address=self.source_address)
            # don't pass host, don't want to connect yet!
            smtp = smtplib.SMTP(timeout=self.connection_timeout, source_address=self.source_address)

        if self.debug_level > 1:
            smtp.set_debuglevel(self.debug_level - 1)

        try:
            # HACK: connect doesn't set smtp._host, then ssl/tls will not work :/
            smtp._host = self.host
            smtp_code, smtp_message = smtp.connect(self.host, self.port, source_address=self.source_address)
            logger.debug('connected', host=self.host, port=self.port, source_address=self.source_address,
                smtp_code=smtp_code, smtp_message=smtp_message)
        except socket.gaierror as exc:
            self.log_exception('connection error', host=self.host, port=self.port, errno=exc.errno, message=exc.strerror)
            exit(ExitCodes.CONNECTION_ERROR)
        except Exception as exc:
            self.log_exception('connection error', host=self.host, port=self.port, message=str(exc), exception=exc.__class__.__name__)
            exit(ExitCodes.CONNECTION_ERROR)

        smtp.ehlo(self.identify_as)

        if self.tls:
            logger.debug('upgrade connection to tls')
            smtp.starttls()

        if self.login and self.password:
            logger.debug('call login, will authorize when required', login=self.login)
            smtp.login(self.login, self.password)

        envelope_from = self.envelope_from or self.address_from
        envelope_to = self.envelope_to or (self.address_to + self.address_cc + self.address_bcc)

        try:
            smtp.sendmail(envelope_from, envelope_to, getattr(self.message_body, 'as_string', lambda: self.message_body)())
        except smtplib.SMTPSenderRefused as exc:
            log_method = logger.exception if self.debug_level > 0 else logger.error
            log_method(exc.smtp_error.decode(), smtp_code=exc.smtp_code)
            exit(ExitCodes.OTHER)
        finally:
            smtp.quit()

    def _set_property(self, name: str, initial: Any, low_prio: Optional[PredefinedMessage], defaults: dict):
        value = initial
        if low_prio and initial is None:
            value = getattr(low_prio, name)
        if value is None:
            value = defaults[name]
        setattr(self, name, value)

    def log_exception(self, msg, **kwargs):
        log_method = logger.exception if self.debug_level > 0 else logger.error
        log_method(msg, **kwargs)
