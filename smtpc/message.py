__all__ = ['Builder', 'Sender']

import copy
import email
import json
import os
import re
import smtplib
import socket
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Any, Union, NoReturn, Tuple

import structlog

from . import __version__
from . import config
from .defaults import DEFAULTS_VALUES_MESSAGE, DEFAULTS_VALUES_PROFILE
from .enums import ContentType, ExitCodes
from .errors import InvalidTemplateFieldNameError, InvalidJsonTemplateError
from .predefined_messages import PredefinedMessage
from .predefined_profiles import PredefinedProfile
from .utils import exitc, determine_ssl_tls_by_port

try:
    from . import encryption
except ImportError:
    encryption = None

logger = structlog.get_logger()


class SimpleTemplate:
    def __init__(self, tpl: str) -> NoReturn:
        self.tpl = tpl

    def render(self, **fields) -> str:
        if not fields:
            return self.tpl

        data = self.tpl
        for name, value in fields.items():
            data = re.sub(r'\{\{\s*' + name + r'\s*\}\}', str(value), data)

        return data


try:
    from jinja2 import Template
except ImportError:
    Template = SimpleTemplate


class Builder:
    __slots__ = (
        'subject',
        'envelope_from', 'address_from',
        'envelope_to', 'address_to', 'address_cc', 'reply_to',
        'body_type', 'body_html', 'body', 'raw_body', 'template_fields', 'template_fields_json',
        'headers',
    )

    def __init__(self, *,
        subject: Optional[str],
        envelope_from: Optional[str],
        address_from: Optional[str],
        envelope_to: Optional[List[str]],
        address_to: Optional[List[str]],
        address_cc: Optional[List[str]],
        reply_to: Optional[List[str]],
        body_type: Optional[ContentType],
        body_html: Optional[str] = None,
        body: Optional[str] = None,
        raw_body: Optional[bool] = None,
        template_fields: Optional[List[str]] = None,
        template_fields_json: Optional[List[str]] = None,
        headers: Optional[List[str]] = None,
        predefined_message: Optional[PredefinedMessage] = None,
    ) -> NoReturn:
        self.template_fields = template_fields or []
        self.template_fields_json = template_fields_json or []

        message_fields = {
            'subject': subject,
            'envelope_from': envelope_from,
            'address_from': address_from,
            'envelope_to': envelope_to,
            'address_to': address_to,
            'address_cc': address_cc,
            'reply_to': reply_to,
            'body_type': body_type,
            'body_html': body_html,
            'body': body,
            'raw_body': raw_body,
            'headers': headers,
        }
        for name in message_fields:
            self._set_property(name, message_fields[name], predefined_message, DEFAULTS_VALUES_MESSAGE)

    def execute(self) -> MIMEBase:
        if self.raw_body:
            message = email.message_from_string(self.body)
        else:
            if self.body_type:
                if self.body_type == ContentType.HTML:
                    body = self.body if self.body is not None else self.body_html
                    message = MIMEText(self.template(body), 'html')
                elif self.body_type == ContentType.PLAIN:
                    message = MIMEText(self.template(self.body), 'plain')
                else:
                    message = MIMEMultipart('alternative')
                    if self.body:
                        message.attach(MIMEText(self.template(self.body), 'plain'))
                    if self.body_html:
                        message.attach(MIMEText(self.template(self.body_html), 'html'))
            else:
                message = MIMEText(self.template(self.body or ''), 'plain')

        for header in self.headers:
            header_name, header_value = header.split('=', 1)
            message[header_name.strip()] = header_value.strip()

        if self.subject:
            message['Subject'] = self.template(self.subject)
        if self.reply_to:
            message['Reply-To'] = self.reply_to[0]
        message['From'] = self.address_from or self.envelope_from
        if self.address_to or self.address_cc:
            if self.address_to:
                message['To'] = ', '.join(self.address_to)
            if self.address_cc:
                message['Cc'] = ', '.join(self.address_cc)
        else:
            message['To'] = ', '.join(self.envelope_to)

        del message['User-Agent']
        message['User-Agent'] = f'SMTPc/{__version__} (https://smtpc.net (c) 2021 Marcin Sztolcman)'

        return message

    def _set_property(self, name: str, initial: Any, low_prio: Optional[PredefinedMessage], defaults: dict) -> NoReturn:
        value = initial
        if low_prio and initial is None:
            value = getattr(low_prio, name)
        if value is None:
            value = defaults[name]
        setattr(self, name, value)

    def template(self, data: str) -> str:
        if not self.template_fields and not self.template_fields_json:
            return data

        fields = {}
        for field in self.template_fields:
            field, value = self._template_parse_field(field)
            fields[field] = value

        for field in self.template_fields_json:
            field, value = self._template_parse_field(field, True)
            fields[field] = value

        tpl = Template(data)
        data = tpl.render(**fields)
        return data

    @classmethod
    def _template_parse_field(cls, field: str, is_json: bool = False) -> Tuple[str, str]:
        field, value = field.split('=', 1)
        cls._template_validate_field_name(field)
        if not is_json:
            return field, value

        try:
            value = json.loads(value)
        except json.decoder.JSONDecodeError as exc:
            raise InvalidJsonTemplateError(f"Invalid json for field \"{field}\": {exc}")
        return field, value

    @classmethod
    def _template_validate_field_name(cls, name: str) -> NoReturn:
        m = re.match(r'^[a-zA-Z0-9_]+$', name)
        if not m:
            raise InvalidTemplateFieldNameError('Template field name can contain only ASCII letters,'
                ' digits and underscores.')


class Sender:
    __slots__ = (
        'connection_timeout', 'source_address',
        'host', 'port', 'identify_as', 'ssl', 'tls',
        'login', 'password',
        'envelope_from', 'address_from',
        'envelope_to', 'address_to', 'address_cc', 'address_bcc', 'reply_to',
        'message_body', 'predefined_profile', 'predefined_message',
        'debug_level', 'dry_run',
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
        password_key: Optional[str],
        envelope_from: Optional[str],
        address_from: Optional[str],
        envelope_to: Optional[List[str]],
        address_to: Optional[List[str]],
        address_cc: Optional[List[str]],
        address_bcc: Optional[List[str]],
        reply_to: Optional[List[str]],
        message_body: Optional[Union[MIMEBase, str]],
        predefined_profile: Optional[PredefinedProfile],
        predefined_message: Optional[PredefinedMessage],
        dry_run: Optional[bool],
    ) -> NoReturn:
        self.debug_level = debug_level
        self.message_body = message_body
        self.dry_run = dry_run

        if predefined_profile:
            logger.debug('using connection details from predefined profile', profile=predefined_profile.name)

        profile_fields = {
            'login': login,
            'password': password,
            'host': host,
            'port': port,
            'connection_timeout': connection_timeout,
            'identify_as': identify_as,
            'source_address': source_address,
        }
        for name in profile_fields:
            self._set_property(name, profile_fields[name], predefined_profile, DEFAULTS_VALUES_PROFILE)

        self.password = self.prepare_password(self.password, password_key)

        if any(item is not None for item in [port, ssl, tls, no_ssl, no_tls]) or not predefined_profile:
            self.ssl, self.tls = determine_ssl_tls_by_port(port, ssl, tls, no_ssl, no_tls)
        elif predefined_profile:
            self.ssl, self.tls = determine_ssl_tls_by_port(predefined_profile.port, predefined_profile.ssl, predefined_profile.tls)

        message_fields = {
            'envelope_from': envelope_from,
            'address_from': address_from,
            'envelope_to': envelope_to,
            'address_to': address_to,
            'address_cc': address_cc,
            'address_bcc': address_bcc,
            'reply_to': reply_to,
        }
        for name in message_fields:
            self._set_property(name, message_fields[name], predefined_message, DEFAULTS_VALUES_MESSAGE)

        if self.debug_level > 1:
            logger.debug('profiles settings', **{k: getattr(self, k) if k != 'password' else '***' for k in profile_fields})
            logger.debug('message settings', **{k: getattr(self, k) for k in message_fields})

    def execute(self) -> List[str]:
        if self.ssl:
            logger.debug('connecting using ssl', host=self.host, port=self.port,
                connection_timeout=self.connection_timeout, source_address=self.source_address)
            # don't pass host, don't want to connect yet!
            if not self.dry_run:
                smtp = smtplib.SMTP_SSL(timeout=self.connection_timeout, source_address=self.source_address)
        else:
            logger.debug('connecting using plain connection', host=self.host, port=self.port,
                connection_timeout=self.connection_timeout, source_address=self.source_address)
            # don't pass host, don't want to connect yet!
            if not self.dry_run:
                smtp = smtplib.SMTP(timeout=self.connection_timeout, source_address=self.source_address)

        if self.dry_run:
            return

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
            exitc(ExitCodes.CONNECTION_ERROR)
        except Exception as exc:
            self.log_exception('connection error', host=self.host, port=self.port, message=str(exc), exception=exc.__class__.__name__)
            exitc(ExitCodes.CONNECTION_ERROR)

        smtp.ehlo(self.identify_as)

        if self.tls:
            logger.debug('upgrading connection to tls')
            smtp.starttls()

        if self.login and self.password:
            logger.debug('calling login, will authorize when required', login=self.login)
            smtp.login(self.login, self.password)

        envelope_from = self.envelope_from or self.address_from
        envelope_to = self.envelope_to or (self.address_to + self.address_cc + self.address_bcc)

        body = getattr(self.message_body, 'as_string', lambda: self.message_body)
        try:
            rejects = smtp.sendmail(envelope_from, envelope_to, body())
        except smtplib.SMTPSenderRefused as exc:
            self.log_exception(exc.smtp_error.decode(), smtp_code=exc.smtp_code)
            exitc(ExitCodes.OTHER)
        finally:
            smtp.quit()

        senders = list(copy.copy(envelope_to))
        if rejects:
            for address, info in rejects.items():
                logger.error(f"server doesn't accept message for {address}", smtp_code=info[0], smtp_message=info[1])
                senders.remove(address)

        return senders

    def prepare_password(self, password: Optional[str], key: str) -> str:
        if password is None:
            return password

        if password.startswith('enc:'):
            password = encryption.decrypt(password, os.environ.get(config.ENV_SMTPC_SALT, ''), key)
        elif password.startswith('raw:'):
            password = password[4:]
        return password

    def _set_property(self, name: str, initial: Any, low_prio: Optional[PredefinedMessage], defaults: dict) -> NoReturn:
        value = initial
        if low_prio and initial is None:
            value = getattr(low_prio, name)
        if value is None:
            value = defaults[name]
        setattr(self, name, value)

    def log_exception(self, msg: str, **kwargs) -> NoReturn:
        log_method = logger.exception if self.debug_level > 0 else logger.error
        log_method(msg, **kwargs)
