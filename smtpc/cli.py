import argparse
import enum
import logging
import smtplib
import sys
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, List, Union

import structlog

from . import __version__
from .config import ensure_config_files, Profiles, Profile, PROFILES_FILE, Config

logger = structlog.get_logger()
PROFILES: Optional[Profiles] = None
CONFIG: Optional[Config] = None


class ContentType(enum.Enum):
    PLAIN = 'plain'
    HTML = 'html'
    ALTERNATIVE = 'alternative'


def parse_argv(argv):
    content_type_choices = [ContentType.PLAIN.value, ContentType.HTML.value]

    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', '-P', choices=PROFILES.keys(),
        help='Get set of connection details (--host, --port, --login, --password etc) from config file.')
    parser.add_argument('--save-profile', help='Save connection details')
    parser.add_argument('--list-profiles', action='store_true', help='List known profiles names and exit')
    parser.add_argument('--edit-profiles', action='store_true', help='Run $EDITOR with profiles files')
    parser.add_argument('--login', '-l', help='Login for SMTP authentication. Required if --password was given.')
    parser.add_argument('--password', '-p', help='Password for SMTP authentication. Required if --login was given.')
    parser.add_argument('--host', '-s', default='127.0.0.1',
        help='SMTP server. Can be also together with port, ie: 127.0.0.1:465.')
    parser.add_argument('--port', '-o', type=int, help='Port for SMTP connection. Default: 25.')
    parser.add_argument('--subject', '-j', help='Subject for email.')
    parser.add_argument('--body', '-b',
        help='Body of email. Has less priority then --body-text and --body-html.')
    parser.add_argument('--body-type', choices=content_type_choices, help='Typehint for email Content-Type. ')
    parser.add_argument('--body-plain', help='Text part of the message for text/plain version.')
    parser.add_argument('--body-html', help='Text part of the message for text/html version.')
    parser.add_argument('--raw-body', action='store_true',
        help='Do not try to generate email body with headers, use content from --body as whole message body.')
    parser.add_argument('--envelope-from', '-F',
        help='Sender address for SMTP session. If missing, then address from --from is used.')
    parser.add_argument('--from', '-f', dest='address_from',
        help='Sender addres. Will be used for SMTP session if --envelope-from is missing.')
    parser.add_argument('--envelope-to', '-T', action='append', default=[],
        help='Email recpients for SMTP session. Can be used multiple times. '
             'If used, then --to, -cc and --bcc are not used for SMTP session.')
    parser.add_argument('--to', '-t', dest='address_to', action='append', default=[],
        help='Email recipients for To header. Used in SMTP session if --envelope-to is missing.')
    parser.add_argument('--cc', '-c', dest='address_cc', action='append', default=[],
        help='Email recipients for Cc header. Used in SMTP session if --envelope-to is missing.')
    parser.add_argument('--bcc', '-C', dest='address_bcc', action='append', default=[],
        help='Used in SMTP session if --envelope-to is missing. Will not be included in generated message.')
    parser.add_argument('--tls', action='store_true', help='Force upgrade connection to TLS. Default if --port is 587.')
    parser.add_argument('--no-tls', action='store_true', help='Force disable TLS upgrade.')
    parser.add_argument('--ssl', action='store_true', help='Force use SSL connection. Default if --port is 465.')
    parser.add_argument('--no-ssl', action='store_true', help='Force disable SSL connection.')
    parser.add_argument('--header', '-H', dest='headers', action='append', default=[],
        help='Additional headers in format: HeaderName=HeaderValue. Can be used multiple times.')
    parser.add_argument('--connection-timeout', type=int, default=30, help='')
    parser.add_argument('--session-timeout', type=int, help='')
    parser.add_argument('--identify-as', help='Domain used for SMTP identification in EHLO/HELO command.')
    parser.add_argument('--source-address', help='Source IP address to use when connecting.')
    parser.add_argument('--debug', '-D', action='count', default=0,
        help='Enable debug messages. Can be used multiple times to increase debug level.')
    parser.add_argument('-v', '--version', action='store_true', help='Display the version and exit')
    args = parser.parse_args(argv)

    if args.version or args.list_profiles or args.edit_profiles:
        return args

    if args.tls and args.ssl:
        parser.error("Cannot use --ssl and --tls together")

    if ':' in args.host:
        host, port = args.host.split(':', 1)
        args.host = host
        if not args.port:
            args.port = int(port)

    if not args.port:
        args.port = 25

    if not args.ssl and not args.tls:
        if args.port == 465 and not args.no_ssl:
            args.ssl = True
        elif args.port == 587 and not args.no_tls:
            args.tls = True

    if (args.login and not args.password) or (not args.login and args.password):
        parser.error("Required both or none: --login, --password")

    if not args.envelope_from and not args.address_from:
        parser.error("Any from (--envelope-from or --address-from) required")

    if not args.envelope_to and not args.address_to and not args.address_cc and not args.address_bcc:
        parser.error("Any from (--envelope-to,--address-to, --address-cc, --address-bcc) required")

    if args.body_type == 'plain':
        args.body_type = ContentType.PLAIN
    elif args.body_type == 'html':
        args.body_type = ContentType.HTML
    else:
        # no body_type specified
        if args.body_plain and args.body_html:
            args.body_type = ContentType.ALTERNATIVE
        elif args.body_plain and not args.body_html:
            args.body_type = ContentType.PLAIN
        elif not args.body_plain and args.body_html:
            args.body_type = ContentType.HTML
        else:
            args.body_type = ContentType.PLAIN

    for header in args.headers:
        if '=' not in header:
            parser.error(f"Invalid header syntax: {header}. Required syntax: HeaderName=HeaderValue")

    return args


def configure_logger(debug_mode: bool = False):
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper("ISO"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG if debug_mode else logging.WARNING),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


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


def send_message(*,
    connection_timeout: int,
    source_address: Optional[str],
    debug_level: Optional[int],
    host: str,
    port: int,
    identify_as: Optional[str],
    tls: bool,
    ssl: bool,
    login: Optional[str],
    password: Optional[str],
    envelope_from: Optional[str],
    address_from: Optional[str],
    envelope_to: Optional[List[str]],
    address_to: Optional[List[str]],
    address_cc: Optional[List[str]],
    address_bcc: Optional[List[str]],
    message: Optional[Union[MIMEBase, str]],
    profile: Optional[Profile]
):
    if profile:
        logger.debug('using connection details from profile', profile=profile.name)
        login = profile.login
        password = profile.password
        host = profile.host
        port = profile.port
        ssl = profile.ssl
        tls = profile.tls
        connection_timeout = profile.connection_timeout
        identify_as = profile.identify_as
        source_address = profile.source_address

    if ssl:
        logger.debug('connecting using ssl', connection_timeout=connection_timeout,
            source_address=source_address)
        # don't pass host, don't want to connect yet!
        smtp = smtplib.SMTP_SSL(timeout=connection_timeout, source_address=source_address)
    else:
        logger.debug('connecting using plain connection', connection_timeout=connection_timeout,
            source_address=source_address)
        # don't pass host, don't want to connect yet!
        smtp = smtplib.SMTP(timeout=connection_timeout, source_address=source_address)

    if debug_level > 1:
        smtp.set_debuglevel(debug_level - 1)

    try:
        # HACK: connect doesn't set smtp._host, then ssl/tls will not work :/
        smtp._host = host
        smtp_code, smtp_message = smtp.connect(host, port, source_address=source_address)
        logger.debug('connected', host=host, port=port, source_address=source_address,
            smtp_code=smtp_code, smtp_message=smtp_message)
    except Exception as exc:
        logger.exception('connection error', host=host, port=port, exc=exc)
        raise exc

    smtp.ehlo(identify_as)

    if tls:
        logger.debug('upgrade connection to tls')
        smtp.starttls()

    if login and password:
        logger.debug('call login, will authorize when required', login=login)
        smtp.login(login, password)

    envelope_from = envelope_from or address_from
    envelope_to = envelope_to or (address_to + address_cc + address_bcc)

    try:
        smtp.sendmail(envelope_from, envelope_to, getattr(message, 'as_string', lambda: message)())
    except smtplib.SMTPSenderRefused as exc:
        logger.error(exc.smtp_error.decode(), smtp_code=exc.smtp_code)
        raise exc
    finally:
        smtp.quit()


def list_profiles(debug_level):
    print('Known profiles:')
    for name, profile in PROFILES.items():
        if debug_level > 0:
            data = profile.to_dict()
            if debug_level == 1:
                data['password'] = '***'
            print(f"- {name} ({data})")
        else:
            print(f"- {name}")


def edit_profiles():
    import os
    import subprocess
    cmd = [
        os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vim',
        str(PROFILES_FILE),
    ]
    subprocess.run(cmd)


def main():
    ensure_config_files()

    global PROFILES
    PROFILES = Profiles.read()

    args = parse_argv(sys.argv[1:])
    configure_logger(args.debug > 0)

    if args.version:
        print('SMTPc %s' % __version__)
        sys.exit(0)

    if args.list_profiles:
        list_profiles(args.debug)
        sys.exit(0)

    if args.edit_profiles:
        edit_profiles()
        sys.exit(0)

    if not args.profile and args.save_profile:
        PROFILES.add(Profile(
            name=args.save_profile,
            login=args.login,
            password=args.password,
            host=args.host,
            port=args.port,
            ssl=args.ssl,
            tls=args.tls,
            connection_timeout=args.connection_timeout,
            identify_as=args.identify_as,
            source_address=args.source_address,
        ))

    if args.raw_body:
        message = args.body
    else:
        message = build_message(
            subject=args.subject,
            envelope_from=args.envelope_from,
            address_from=args.address_from,
            envelope_to=args.envelope_to,
            address_to=args.address_to,
            address_cc=args.address_cc,
            body_type=args.body_type,
            body_html=args.body_html or args.body,
            body_plain=args.body_plain or args.body,
            headers=args.headers,
        )

    if args.profile:
        profile = PROFILES[args.profile]
    else:
        profile = None

    try:
        send_message(
            profile=profile,
            connection_timeout=args.connection_timeout,
            source_address=args.source_address,
            debug_level=args.debug,
            host=args.host,
            port=args.port,
            identify_as=args.identify_as,
            tls=args.tls,
            ssl=args.ssl,
            login=args.login,
            password=args.password,
            envelope_from=args.envelope_from,
            address_from=args.address_from,
            envelope_to=args.envelope_to,
            address_to=args.address_to,
            address_cc=args.address_cc,
            address_bcc=args.address_bcc,
            message=message,
        )
    except (smtplib.SMTPSenderRefused, smtplib.SMTPAuthenticationError) as exc:
        logger.error(exc.smtp_error.decode(), smtp_code=exc.smtp_code)

    sys.exit(0)
