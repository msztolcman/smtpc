import argparse
import enum
import logging
import smtplib
import socket
import sys
from email.mime.base import MIMEBase
from typing import Optional, List, Union

import structlog
import toml.decoder

from . import __version__
from .config import ensure_config_files, PREDEFINED_PROFILES_FILE, PREDEFINED_MESSAGES_FILE, Config, EMPTY
from .defaults import DEFAULTS_VALUES_PROFILE, DEFAULTS_VALUES_MESSAGE
from .message import ContentType, build_message
from .predefined_messages import PredefinedMessages, PredefinedMessage
from .predefined_profiles import PredefinedProfiles, PredefinedProfile

logger = structlog.get_logger()
CONFIG: Optional[Config] = None
PREDEFINED_PROFILES: Optional[PredefinedProfiles] = None
PREDEFINED_MESSAGES: Optional[PredefinedMessages] = None

class ExitCodes(enum.Enum):
    OK = 0
    CONNECTION_ERROR = 1
    OTHER = 2


def exit(err_code: ExitCodes):
    sys.exit(err_code.value)


def parse_argv(argv):
    content_type_choices = [ContentType.PLAIN.value, ContentType.HTML.value]

    parser = argparse.ArgumentParser('SMTPc')
    parser.add_argument('--debug', '-D', action='count', default=0,
        help='Enable debug messages. Can be used multiple times to increase debug level.')
    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {__version__}',
        help='Display the version and exit.')

    sub = parser.add_subparsers(dest='command')

    # SEND command
    p_send = sub.add_parser('send', help="Send message.")
    p_send.add_argument('--profile', '-P', choices=PREDEFINED_PROFILES.keys(),
        help='Get set of connection details (--host, --port, --login, --password etc) from config file.')
    p_send.add_argument('--message', '-M', choices=PREDEFINED_MESSAGES.keys(),
        help='Get set of message details (--subject, --from, --to, --cc etc) from config file.')

    # SEND command - profile configuration stuff
    p_send.add_argument('--login', '-l', default=EMPTY,
        help='Login for SMTP authentication. Required if --password was given.')
    p_send.add_argument('--password', '-p', default=EMPTY,
        help='Password for SMTP authentication. Required if --login was given.')
    p_send.add_argument('--host', '-s', default=EMPTY,
        help='SMTP server. Can be also together with port, ie: 127.0.0.1:465.')
    p_send.add_argument('--port', '-o', type=int, default=EMPTY,
        help='Port for SMTP connection. Default: 25.')
    p_send.add_argument('--tls', action='store_true', default=EMPTY,
        help='Force upgrade connection to TLS. Default if --port is 587.')
    p_send.add_argument('--no-tls', action='store_true', help='Force disable TLS upgrade.')
    p_send.add_argument('--ssl', action='store_true', default=EMPTY,
        help='Force use SSL connection. Default if --port is 465.')
    p_send.add_argument('--no-ssl', action='store_true', help='Force disable SSL connection.')
    p_send.add_argument('--connection-timeout', type=int, default=30, help='')
    p_send.add_argument('--session-timeout', type=int, help='')
    p_send.add_argument('--identify-as', default=EMPTY,
        help='Domain used for SMTP identification in EHLO/HELO command.')
    p_send.add_argument('--source-address', default=EMPTY,
        help='Source IP address to use when connecting.')

    # SEND command - message related stuff
    p_send.add_argument('--subject', '-j', default=EMPTY,
        help='Subject for email.')
    p_send.add_argument('--body', '-b', default=EMPTY,
        help='Body of email. Has less priority then --body-text and --body-html.')
    p_send.add_argument('--body-type', choices=content_type_choices, default=EMPTY,
        help='Typehint for email Content-Type.')
    p_send.add_argument('--body-plain', default=EMPTY,
        help='Text part of the message for text/plain version.')
    p_send.add_argument('--body-html', default=EMPTY,
        help='Text part of the message for text/html version.')
    p_send.add_argument('--raw-body', default=EMPTY,
        action='store_true',
        help='Do not try to generate email body with headers, use content from --body as whole message body.')
    p_send.add_argument('--envelope-from', '-F', default=EMPTY,
        help='Sender address for SMTP session. If missing, then address from --from is used.')
    p_send.add_argument('--from', '-f', dest='address_from', default=EMPTY,
        help='Sender addres. Will be used for SMTP session if --envelope-from is missing.')
    p_send.add_argument('--envelope-to', '-T', action='append', default=EMPTY,
        help='Email recpients for SMTP session. Can be used multiple times.'
             'If used, then --to, -cc and --bcc are not used for SMTP session.')
    p_send.add_argument('--to', '-t', dest='address_to', action='append', default=EMPTY,
        help='Email recipients for To header. Used in SMTP session if --envelope-to is missing.')
    p_send.add_argument('--cc', '-c', dest='address_cc', action='append', default=EMPTY,
        help='Email recipients for Cc header. Used in SMTP session if --envelope-to is missing.')
    p_send.add_argument('--bcc', '-C', dest='address_bcc', action='append', default=EMPTY,
        help='Used in SMTP session if --envelope-to is missing. Will not be included in generated message.')
    p_send.add_argument('--header', '-H', dest='headers', action='append', default=EMPTY,
        help='Additional headers in format: HeaderName=HeaderValue. Can be used multiple times.')

    # PROFILES command
    p_profiles = sub.add_parser('profiles', help="Manage connection profiles.")
    p_profiles_sub = p_profiles.add_subparsers(dest='subcommand')

    p_profiles_edit = p_profiles_sub.add_parser('edit', help='Open profiles configuration in default editor.')
    p_profiles_list = p_profiles_sub.add_parser('list', help='List known connection profiles. Use -D or -DD to see more informations.')
    p_profiles_add = p_profiles_sub.add_parser('add', help='Add new connection profile.')
    p_profiles_add.add_argument('name', nargs=1, help='Unique name of connection profile.')
    p_profiles_add.add_argument('--login', '-l', default=DEFAULTS_VALUES_PROFILE['login'],
        help='Login for SMTP authentication. Required if --password was given.')
    p_profiles_add.add_argument('--password', '-p', default=DEFAULTS_VALUES_PROFILE['password'],
        help='Password for SMTP authentication. Required if --login was given.')
    p_profiles_add.add_argument('--host', '-s', default=DEFAULTS_VALUES_PROFILE['host'],
        help='SMTP server. Can be also together with port, ie: 127.0.0.1:465.')
    p_profiles_add.add_argument('--port', '-o', type=int, default=DEFAULTS_VALUES_PROFILE['port'],
        help='Port for SMTP connection. Default: 25.')
    p_profiles_add.add_argument('--tls', action='store_true', default=DEFAULTS_VALUES_PROFILE['tls'],
        help='Force upgrade connection to TLS. Default if --port is 587.')
    p_profiles_add.add_argument('--no-tls', action='store_true', help='Force disable TLS upgrade.')
    p_profiles_add.add_argument('--ssl', action='store_true', default=DEFAULTS_VALUES_PROFILE['ssl'],
        help='Force use SSL connection. Default if --port is 465.')
    p_profiles_add.add_argument('--no-ssl', action='store_true', help='Force disable SSL connection.')
    p_profiles_add.add_argument('--connection-timeout', type=int, default=DEFAULTS_VALUES_PROFILE['connection_timeout'],
        help='')
    p_profiles_add.add_argument('--session-timeout', type=int, default=DEFAULTS_VALUES_PROFILE['session_timeout'],
        help='')
    p_profiles_add.add_argument('--identify-as', default=DEFAULTS_VALUES_PROFILE['identify_as'],
        help='Domain used for SMTP identification in EHLO/HELO command.')
    p_profiles_add.add_argument('--source-address', default=DEFAULTS_VALUES_PROFILE['source_address'],
        help='Source IP address to use when connecting.')

    # MESSAGES command
    p_messages = sub.add_parser('messages', help='Manage saved messages.')
    p_messages_sub = p_messages.add_subparsers(dest='subcommand')

    p_messages_edit = p_messages_sub.add_parser('edit', help='Open messages configuration in default editor.')
    p_messages_list = p_messages_sub.add_parser('list', help='List known connection profiles.')
    p_messages_add = p_messages_sub.add_parser('add', help='Add new message.')
    p_messages_add.add_argument('name', nargs=1, help='Unique name of message.')
    p_messages_add.add_argument('--subject', '-j', help='Subject for email.')
    p_messages_add.add_argument('--body', '-b',
        help='Body of email. Has less priority then --body-text and --body-html.')
    p_messages_add.add_argument('--body-type', choices=content_type_choices, help='Typehint for email Content-Type.')
    p_messages_add.add_argument('--body-plain', help='Text part of the message for text/plain version.')
    p_messages_add.add_argument('--body-html', help='Text part of the message for text/html version.')
    p_messages_add.add_argument('--raw-body', action='store_true',
        help='Do not try to generate email body with headers, use content from --body as whole message body.')
    p_messages_add.add_argument('--envelope-from', '-F',
        help='Sender address for SMTP session. If missing, then address from --from is used.')
    p_messages_add.add_argument('--from', '-f', dest='address_from',
        help='Sender addres. Will be used for SMTP session if --envelope-from is missing.')
    p_messages_add.add_argument('--envelope-to', '-T', action='append', default=[],
        help='Email recpients for SMTP session. Can be used multiple times.'
             'If used, then --to, -cc and --bcc are not used for SMTP session.')
    p_messages_add.add_argument('--to', '-t', dest='address_to', action='append', default=[],
        help='Email recipients for To header. Used in SMTP session if --envelope-to is missing.')
    p_messages_add.add_argument('--cc', '-c', dest='address_cc', action='append', default=[],
        help='Email recipients for Cc header. Used in SMTP session if --envelope-to is missing.')
    p_messages_add.add_argument('--bcc', '-C', dest='address_bcc', action='append', default=[],
        help='Used in SMTP session if --envelope-to is missing. Will not be included in generated message.')
    p_messages_add.add_argument('--header', '-H', dest='headers', action='append', default=[],
        help='Additional headers in format: HeaderName=HeaderValue. Can be used multiple times.')

    args = parser.parse_args(argv)

    def setup_connection_args(args):
        if args.tls is not EMPTY and args.ssl is not EMPTY:
            parser.error("Cannot use --ssl and --tls together")

        if args.host is not EMPTY and args.host.startswith(('smtp://', 'smtps://')):
            args.host = args.host.replace('smtp://', '').replace('smtps://', '')

        if ':' in args.host:
            host, port = args.host.split(':', 1)
            args.host = host
            if not args.port:
                try:
                    args.port = int(port)
                except ValueError:
                    parser.error(f"SMTP port: invalid int value: {port}")

        if args.port is not EMPTY:
            args.port = 25

        if args.ssl is not EMPTY and args.tls is not EMPTY:
            if args.port == 465 and not args.no_ssl:
                args.ssl = True
            elif args.port == 587 and not args.no_tls:
                args.tls = True

        if (args.login is not EMPTY and args.password is EMPTY) or (args.login is not EMPTY and args.password is EMPTY):
            parser.error("Required both or none: --login, --password")

    def setup_message_args(args):
        if not getattr(args, 'message', False) and not args.envelope_from and not args.address_from:
            parser.error('Any from (--envelope-from or --from) required' + (
                ' if --message not specified' if not hasattr(args, 'message') else ''
            ))

        if not getattr(args, 'message', False) and not args.envelope_to and not args.address_to and not args.address_cc and not args.address_bcc:
            parser.error('Any from (--envelope-to,--to, --cc, --bcc) required' + (
                ' if --message not specified' if not hasattr(args, 'message') else ''
            ))

        if args.body_type in ('plain', 'html'):
            args.body_type = ContentType(args.body_type)
        elif args.body_plain and args.body_html:
            args.body_type = ContentType.ALTERNATIVE
        elif args.body_plain and not args.body_html:
            args.body_type = ContentType.PLAIN
        elif not args.body_plain and args.body_html:
            args.body_type = ContentType.HTML
        else:
            args.body_type = ContentType.PLAIN

        if args.headers is not EMPTY:
            for header in args.headers:
                if '=' not in header:
                    parser.error(f"Invalid header syntax: {header}. Required syntax: HeaderName=HeaderValue")

    if args.command == 'send':
        setup_connection_args(args)
        setup_message_args(args)

    elif args.command == 'profiles':
        if args.subcommand == 'add':
            setup_connection_args(args)
        elif not args.subcommand:
            p_profiles.print_help()
            sys.exit()

    elif args.command == 'messages':
        if args.subcommand == 'add':
            setup_message_args(args)
        elif not args.subcommand:
            p_messages.print_help()
            sys.exit()

    else:
        parser.print_help()
        sys.exit()

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
    message_body: Optional[Union[MIMEBase, str]],
    profile: Optional[PredefinedProfile],
    message: Optional[PredefinedMessage],
):
    if profile:
        logger.debug('using connection details from predefined profile', profile=profile.name)
        if login is EMPTY:
            login = profile.login
        if password is EMPTY:
            password = profile.password
        if host is EMPTY:
            host = profile.host
        if port is EMPTY:
            port = profile.port
        if ssl is EMPTY:
            ssl = profile.ssl
        if tls is EMPTY:
            tls = profile.tls
        if connection_timeout is EMPTY:
            connection_timeout = profile.connection_timeout
        if identify_as is EMPTY:
            identify_as = profile.identify_as
        if source_address is EMPTY:
            source_address = profile.source_address

    if login is EMPTY:
        login = DEFAULTS_VALUES_PROFILE['login']
    if password is EMPTY:
        password = DEFAULTS_VALUES_PROFILE['password']
    if host is EMPTY:
        host = DEFAULTS_VALUES_PROFILE['host']
    if port is EMPTY:
        port = DEFAULTS_VALUES_PROFILE['port']
    if ssl is EMPTY:
        ssl = DEFAULTS_VALUES_PROFILE['ssl']
    if tls is EMPTY:
        tls = DEFAULTS_VALUES_PROFILE['tls']
    if connection_timeout is EMPTY:
        connection_timeout = DEFAULTS_VALUES_PROFILE['connection_timeout']
    if identify_as is EMPTY:
        identify_as = DEFAULTS_VALUES_PROFILE['identify_as']
    if source_address is EMPTY:
        source_address = DEFAULTS_VALUES_PROFILE['source_address']

    if message:
        logger.debug('using message details from predefined message', message=message.name)
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
        if address_bcc is EMPTY:
            address_bcc = message.address_bcc

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
    if address_bcc is EMPTY:
        address_bcc = DEFAULTS_VALUES_MESSAGE['address_bcc']

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
    except socket.gaierror as exc:
        log_method = logger.exception if debug_level > 0 else logger.error
        log_method('connection error', host=host, port=port, errno=exc.errno, message=exc.strerror)
        exit(ExitCodes.CONNECTION_ERROR)
    except Exception as exc:
        log_method = logger.exception if debug_level > 0 else logger.error
        log_method('connection error', host=host, port=port, message=str(exc))
        exit(ExitCodes.CONNECTION_ERROR)

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
        smtp.sendmail(envelope_from, envelope_to, getattr(message_body, 'as_string', lambda: message_body)())
    except smtplib.SMTPSenderRefused as exc:
        log_method = logger.exception if debug_level > 0 else logger.error
        log_method(exc.smtp_error.decode(), smtp_code=exc.smtp_code)
        exit(ExitCodes.OTHER)
    finally:
        smtp.quit()


def list_profiles(debug_level):
    if not PREDEFINED_PROFILES:
        print('No known profiles')
    else:
        print('Known profiles:')
        for name, profile in PREDEFINED_PROFILES.items():
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

    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vim'
    logger.debug(f'editor: {editor}')
    cmd = [editor, str(PREDEFINED_PROFILES_FILE), ]
    subprocess.run(cmd)


def list_messages():
    if not PREDEFINED_MESSAGES:
        print('No known messages')
    else:
        print('Known messages:')
        for name, message in PREDEFINED_MESSAGES.items():
            print(f"- {name} (from: \"{message.address_from or message.envelope_from}\", subject: \"{message.subject or ''}\")")


def edit_messages():
    import os
    import subprocess

    editor = os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vim'
    logger.debug(f'editor: {editor}')
    cmd = [editor, str(PREDEFINED_MESSAGES_FILE), ]
    subprocess.run(cmd)


def handle_profiles(args):
    if args.subcommand == 'list':
        list_profiles(args.debug)
        exit(ExitCodes.OK)
    elif args.subcommand == 'edit':
        edit_profiles()
        exit(ExitCodes.OK)
    else:
        PREDEFINED_PROFILES.add(PredefinedProfile(
            name=args.name[0],
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
        logger.info('Profile saved', profile=args.name[0])


def handle_messages(args):
    if args.subcommand == 'list':
        list_messages()
        exit(ExitCodes.OK)
    elif args.subcommand == 'edit':
        edit_messages()
        exit(ExitCodes.OK)
    else:
        PREDEFINED_MESSAGES.add(PredefinedMessage(
            name=args.name[0],
            envelope_from=args.envelope_from,
            address_from=args.address_from,
            envelope_to=args.envelope_to,
            address_to=args.address_to,
            address_cc=args.address_cc,
            address_bcc=args.address_bcc,
            subject=args.subject,
            body_plain=args.body_plain,
            body_html=args.body_html,
            body_raw=args.body if args.raw_body else None,
            body_type=args.body_type,
            headers=args.headers,
        ))
        logger.info('Message saved', message=args.name[0])


def handle_send(args):
    message = None if not args.message else PREDEFINED_MESSAGES[args.message]
    if not message and args.raw_body:
        message_body = args.body
    else:
        message_body = build_message(
            message=message,
            subject=args.subject,
            envelope_from=args.envelope_from,
            address_from=args.address_from,
            envelope_to=args.envelope_to,
            address_to=args.address_to,
            address_cc=args.address_cc,
            body_type=args.body_type,
            body_html=args.body_html,
            body_plain=args.body_plain,
            headers=args.headers,
        )

    if args.profile:
        profile = PREDEFINED_PROFILES[args.profile]
    else:
        profile = None

    try:
        send_message(
            profile=profile,
            message=message,
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
            message_body=message_body,
        )
    except (smtplib.SMTPSenderRefused, smtplib.SMTPAuthenticationError) as exc:
        logger.error(exc.smtp_error.decode(), smtp_code=exc.smtp_code)


def main():
    ensure_config_files()

    global PREDEFINED_PROFILES, PREDEFINED_MESSAGES
    try:
        PREDEFINED_PROFILES = PredefinedProfiles.read()
    except toml.decoder.TomlDecodeError as exc:
        PREDEFINED_PROFILES = PredefinedProfiles()
        logger.error(f"profiles configuration error: {exc}")

    try:
        PREDEFINED_MESSAGES = PredefinedMessages.read()
    except toml.decoder.TomlDecodeError as exc:
        PREDEFINED_MESSAGES = PredefinedMessages()
        logger.error(f"messages configuration error: {exc}")

    args = parse_argv(sys.argv[1:])
    configure_logger(args.debug > 0)

    if args.command == 'profiles':
        handle_profiles(args)
    elif args.command == 'send':
        handle_send(args)
    elif args.command == 'messages':
        handle_messages(args)

    exit(ExitCodes.OK)
