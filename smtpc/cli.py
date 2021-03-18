import argparse
import logging
import smtplib
import sys
from typing import Optional

import structlog
import toml.decoder

from . import __version__
from . import message
from .config import ensure_config_files, PREDEFINED_PROFILES_FILE, PREDEFINED_MESSAGES_FILE, Config
from .enums import ExitCodes
from .errors import SMTPcError
from .predefined_messages import PredefinedMessages, PredefinedMessage
from .predefined_profiles import PredefinedProfiles, PredefinedProfile
from .utils import exitc, determine_ssl_tls_by_port

logger = structlog.get_logger()
CONFIG: Optional[Config] = None
PREDEFINED_PROFILES: Optional[PredefinedProfiles] = None
PREDEFINED_MESSAGES: Optional[PredefinedMessages] = None


def parse_argv(argv):
    content_type_choices = [message.ContentType.PLAIN.value, message.ContentType.HTML.value]

    parser = argparse.ArgumentParser('SMTPc')
    parser.add_argument('--debug', '-D', dest='debug_level', action='count', default=0,
        help='Enable debug messages. Can be used multiple times to increase debug level.')
    version = f'%(prog)s {__version__} (https://github.com/msztolcman/smtpc (c) 2021 Marcin Sztolcman)'
    parser.add_argument('-v', '--version', action='version', version=version,
        help='Display the version and exit.')

    sub = parser.add_subparsers(dest='command')

    # SEND command
    p_send = sub.add_parser('send', help="Send message.")
    p_send.add_argument('--dry-run', action='store_true',
        help='Stop processing just before creating SMTP connection with remote server')
    p_send.add_argument('--profile', '-P', choices=PREDEFINED_PROFILES.keys(),
        help='Get set of connection details (--host, --port, --login, --password etc) from config file.')
    p_send.add_argument('--message', '-M', choices=PREDEFINED_MESSAGES.keys(),
        help='Get set of message details (--subject, --from, --to, --cc etc) from config file.')

    # SEND command - profile configuration stuff
    p_send.add_argument('--login', '-l',
        help='Login for SMTP authentication. Required if --password was given.')
    p_send.add_argument('--password', '-p',
        help='Password for SMTP authentication. Required if --login was given.')
    p_send.add_argument('--host', '-s',
        help='SMTP server. Can be also together with port, ie: 127.0.0.1:465.')
    p_send.add_argument('--port', '-o', type=int,
        help='Port for SMTP connection. Default: 25.')
    p_send.add_argument('--tls', action='store_true', default=None,
        help='Force upgrade connection to TLS. Default if --port is 587.')
    p_send.add_argument('--no-tls', action='store_true', default=None,
        help='Force disable TLS upgrade.')
    p_send.add_argument('--ssl', action='store_true', default=None,
        help='Force use SSL connection. Default if --port is 465.')
    p_send.add_argument('--no-ssl', action='store_true', default=None,
        help='Force disable SSL connection.')
    p_send.add_argument('--connection-timeout', type=int, help='')
    p_send.add_argument('--session-timeout', type=int, help='')
    p_send.add_argument('--identify-as',
        help='Domain used for SMTP identification in EHLO/HELO command.')
    p_send.add_argument('--source-address',
        help='Source IP address to use when connecting.')

    # SEND command - message related stuff
    p_send.add_argument('--subject', '-j',
        help='Subject for email.')
    p_send.add_argument('--body', '-b',
        help='Body of email. Has less priority then --body-text and --body-html.')
    p_send.add_argument('--body-type', choices=content_type_choices,
        help='Typehint for email Content-Type.')
    p_send.add_argument('--body-plain',
        help='Text part of the message for text/plain version.')
    p_send.add_argument('--body-html',
        help='Text part of the message for text/html version.')
    p_send.add_argument('--raw-body', action='store_true',
        help='Do not try to generate email body with headers, use content from --body as whole message body.')
    p_send.add_argument('--template-field', '-I', dest='template_fields', action='append',
        help='If given, should be in format: "FieldName=FieldValue". Then all occurrences of "{FieldName}" '
             'in subject or body will be replaced with "value"')
    p_send.add_argument('--template-field-json', '-J', dest='template_fields_json', action='append',
        help='If given, should be in format: "FieldName=JSON". Then all occurrences of "{FieldName}" '
             'in subject or body will be replaced with "json value"')
    p_send.add_argument('--envelope-from', '-F',
        help='Sender address for SMTP session. If missing, then address from --from is used.')
    p_send.add_argument('--from', '-f', dest='address_from',
        help='Sender addres. Will be used for SMTP session if --envelope-from is missing.')
    p_send.add_argument('--envelope-to', '-T', action='append',
        help='Email recpients for SMTP session. Can be used multiple times.'
             'If used, then --to, -cc and --bcc are not used for SMTP session.')
    p_send.add_argument('--to', '-t', dest='address_to', action='append',
        help='Email recipients for To header. Used in SMTP session if --envelope-to is missing.')
    p_send.add_argument('--cc', '-c', dest='address_cc', action='append',
        help='Email recipients for Cc header. Used in SMTP session if --envelope-to is missing.')
    p_send.add_argument('--bcc', '-C', dest='address_bcc', action='append',
        help='Used in SMTP session if --envelope-to is missing. Will not be included in generated message.')
    p_send.add_argument('--reply-to', dest='reply_to', action='append',
        help='How to fill Reply-To header.')
    p_send.add_argument('--header', '-H', dest='headers', action='append',
        help='Additional headers in format: HeaderName=HeaderValue. Can be used multiple times.')

    # PROFILES command
    p_profiles = sub.add_parser('profiles', help="Manage connection profiles.")
    p_profiles_sub = p_profiles.add_subparsers(dest='subcommand')

    p_profiles_edit = p_profiles_sub.add_parser('edit', help='Open profiles configuration in default editor.')
    p_profiles_list = p_profiles_sub.add_parser('list', help='List known connection profiles. Use -D or -DD to see more informations.')
    p_profiles_delete = p_profiles_sub.add_parser('delete', help='Remove connection profile.')
    p_profiles_delete.add_argument('name', nargs=1, choices=PREDEFINED_PROFILES.keys(),
        help='Name of connection profile to remove.')
    p_profiles_add = p_profiles_sub.add_parser('add', help='Add new connection profile.')
    p_profiles_add.add_argument('name', nargs=1, help='Unique name of connection profile.')
    p_profiles_add.add_argument('--login', '-l',
        help='Login for SMTP authentication. Required if --password was given.')
    p_profiles_add.add_argument('--password', '-p',
        help='Password for SMTP authentication. Required if --login was given.')
    p_profiles_add.add_argument('--host', '-s',
        help='SMTP server. Can be also together with port, ie: 127.0.0.1:465.')
    p_profiles_add.add_argument('--port', '-o', type=int,
        help='Port for SMTP connection. Default: 25.')
    p_profiles_add.add_argument('--tls', action='store_true', default=None,
        help='Force upgrade connection to TLS. Default if --port is 587.')
    p_profiles_add.add_argument('--no-tls', action='store_true', default=None,
        help='Force disable TLS upgrade.')
    p_profiles_add.add_argument('--ssl', action='store_true', default=None,
        help='Force use SSL connection. Default if --port is 465.')
    p_profiles_add.add_argument('--no-ssl', action='store_true', default=None,
        help='Force disable SSL connection.')
    p_profiles_add.add_argument('--connection-timeout', type=int,
        help='')
    p_profiles_add.add_argument('--session-timeout', type=int,
        help='')
    p_profiles_add.add_argument('--identify-as',
        help='Domain used for SMTP identification in EHLO/HELO command.')
    p_profiles_add.add_argument('--source-address',
        help='Source IP address to use when connecting.')

    # MESSAGES command
    p_messages = sub.add_parser('messages', help='Manage saved messages.')
    p_messages_sub = p_messages.add_subparsers(dest='subcommand')

    p_messages_edit = p_messages_sub.add_parser('edit', help='Open messages configuration in default editor.')
    p_messages_list = p_messages_sub.add_parser('list', help='List known messages. Use -D or -DD to see more informations.')
    p_messages_delete = p_messages_sub.add_parser('delete', help='Remove message.')
    p_messages_delete.add_argument('name', nargs=1, choices=PREDEFINED_MESSAGES.keys(),
        help='Name of message to remove.')
    p_messages_add = p_messages_sub.add_parser('add', help='Add new message.')
    p_messages_add.add_argument('name', nargs=1, help='Unique name of message.')
    p_messages_add.add_argument('--subject', '-j',
        help='Subject for email.')
    p_messages_add.add_argument('--body', '-b',
        help='Body of email. Has less priority then --body-text and --body-html.')
    p_messages_add.add_argument('--body-type', choices=content_type_choices,
        help='Typehint for email Content-Type.')
    p_messages_add.add_argument('--body-plain',
        help='Text part of the message for text/plain version.')
    p_messages_add.add_argument('--body-html',
        help='Text part of the message for text/html version.')
    p_messages_add.add_argument('--raw-body', action='store_true',
        help='Do not try to generate email body with headers, use content from --body as whole message body.')
    p_messages_add.add_argument('--envelope-from', '-F',
        help='Sender address for SMTP session. If missing, then address from --from is used.')
    p_messages_add.add_argument('--from', '-f', dest='address_from',
        help='Sender addres. Will be used for SMTP session if --envelope-from is missing.')
    p_messages_add.add_argument('--envelope-to', '-T', action='append',
        help='Email recpients for SMTP session. Can be used multiple times.'
             'If used, then --to, -cc and --bcc are not used for SMTP session.')
    p_messages_add.add_argument('--to', '-t', dest='address_to', action='append',
        help='Email recipients for To header. Used in SMTP session if --envelope-to is missing.')
    p_messages_add.add_argument('--cc', '-c', dest='address_cc', action='append',
        help='Email recipients for Cc header. Used in SMTP session if --envelope-to is missing.')
    p_messages_add.add_argument('--bcc', '-C', dest='address_bcc', action='append',
        help='Used in SMTP session if --envelope-to is missing. Will not be included in generated message.')
    p_messages_add.add_argument('--reply-to', dest='reply_to', action='append',
        help='How to fill Reply-To header.')
    p_messages_add.add_argument('--header', '-H', dest='headers', action='append',
        help='Additional headers in format: HeaderName=HeaderValue. Can be used multiple times.')

    args = parser.parse_args(argv)

    def setup_connection_args(args):
        if args.tls and args.ssl:
            parser.error("Cannot use --ssl and --tls together")

        if args.host and args.host.startswith(('smtp://', 'smtps://')):
            args.host = args.host.replace('smtp://', '').replace('smtps://', '')

        if args.host and ':' in args.host:
            host, port = args.host.split(':', 1)
            args.host = host
            if not args.port:
                try:
                    args.port = int(port)
                except ValueError:
                    parser.error(f"SMTP port: invalid int value: {port}")

        if (args.login and not args.password) or (not args.login and args.password):
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

        if args.headers:
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
            exitc(ExitCodes.OK)

    elif args.command == 'messages':
        if args.subcommand == 'add':
            setup_message_args(args)
        elif not args.subcommand:
            p_messages.print_help()
            exitc(ExitCodes.OK)

    else:
        parser.print_help()
        exitc(ExitCodes.OK)

    if hasattr(args, 'reply_to') and args.reply_to and len(args.reply_to) > 1:
        parser.error("Currently only one --reply-to can be used")

    if hasattr(args, 'template_fields') and args.template_fields:
        for tpl_field in args.template_fields:
            if '=' not in tpl_field:
                parser.error(f"Invalid template field syntax: {tpl_field}. Required syntax: FieldName=FieldValue")

    if hasattr(args, 'template_fields_json') and args.template_fields_json:
        for tpl_field in args.template_fields_json:
            if '=' not in tpl_field:
                parser.error(f"Invalid template field syntax: {tpl_field}. Required syntax: FieldName=json")

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


class AbstractCommand:
    def __init__(self, args: argparse.Namespace):
        self.args = args

    def handle(self):
        pass

    def log_exception(self, msg, **kwargs):
        log_method = logger.exception if self.args.debug_level > 0 else logger.error
        log_method(msg, **kwargs)


class ProfilesCommand(AbstractCommand):
    def list(self):
        if not PREDEFINED_PROFILES:
            print('No known profiles')
        else:
            print('Known profiles:')
            for name, profile in PREDEFINED_PROFILES.items():
                if self.args.debug_level > 0:
                    data = profile.to_dict()
                    if self.args.debug_level == 1:
                        data['password'] = '***'
                    print(f"- {name} ({data})")
                else:
                    print(f"- {name}")

    def edit(self):
        import os
        import subprocess

        editor = os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vim'
        logger.debug(f'editor: {editor}')
        cmd = [editor, str(PREDEFINED_PROFILES_FILE), ]
        subprocess.run(cmd)

    def delete(self):
        PREDEFINED_PROFILES.delete(self.args.name[0])

    def add(self):
        self.args.ssl, self.args.tls = determine_ssl_tls_by_port(self.args.port,
            self.args.ssl, self.args.tls, self.args.no_ssl, self.args.no_tls)
        PREDEFINED_PROFILES.add(PredefinedProfile(
            name=self.args.name[0],
            login=self.args.login,
            password=self.args.password,
            host=self.args.host,
            port=self.args.port,
            ssl=self.args.ssl,
            tls=self.args.tls,
            connection_timeout=self.args.connection_timeout,
            identify_as=self.args.identify_as,
            source_address=self.args.source_address,
        ))
        logger.info('Profile saved', profile=self.args.name[0])

    def handle(self):
        if self.args.subcommand == 'list':
            self.list()
        elif self.args.subcommand == 'edit':
            self.edit()
        elif self.args.subcommand == 'delete':
            self.delete()
        else:
            self.add()


class MessagesCommand(AbstractCommand):
    def list(self):
        if not PREDEFINED_MESSAGES:
            print('No known messages')
        else:
            print('Known messages:')
            for name, message in PREDEFINED_MESSAGES.items():
                if self.args.debug_level > 0:
                    print(f"- {name} (subject: \"{message.subject or ''}\", "
                          f"from: \"{message.address_from or message.envelope_from}\", "
                          f"to: \"{', '.join(message.address_to or message.envelope_to)}\")")
                else:
                    print(f"- {name}")

    def edit(self):
        import os
        import subprocess

        editor = os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vim'
        logger.debug(f'editor: {editor}')
        cmd = [editor, str(PREDEFINED_MESSAGES_FILE), ]
        subprocess.run(cmd)

    def add(self):
        PREDEFINED_MESSAGES.add(PredefinedMessage(
            name=self.args.name[0],
            envelope_from=self.args.envelope_from,
            address_from=self.args.address_from,
            envelope_to=self.args.envelope_to,
            address_to=self.args.address_to,
            address_cc=self.args.address_cc,
            address_bcc=self.args.address_bcc,
            reply_to=self.args.reply_to,
            subject=self.args.subject,
            body_plain=self.args.body_plain,
            body_html=self.args.body_html,
            body_raw=self.args.body if self.args.raw_body else None,
            body_type=self.args.body_type,
            headers=self.args.headers,
        ))
        # TODO: shouldn't be logger call
        logger.info('Message saved', message=self.args.name[0])

    def delete(self):
        PREDEFINED_MESSAGES.delete(self.args.name[0])

    def handle(self):
        if self.args.subcommand == 'list':
            self.list()
        elif self.args.subcommand == 'edit':
            self.edit()
        elif self.args.subcommand == 'delete':
            self.delete()
        else:
            self.add()


class SendCommand(AbstractCommand):
    def handle(self):
        try:
            self._handle()
        except SMTPcError as exc:
            self.log_exception('exception found', message=str(exc))
            exitc(ExitCodes.OTHER)

    def _handle(self):
        predefined_message = None if not self.args.message else PREDEFINED_MESSAGES[self.args.message]
        if not predefined_message and self.args.raw_body:
            message_body = self.args.body
        else:
            message_builder = message.Builder(
                message=predefined_message,
                subject=self.args.subject,
                envelope_from=self.args.envelope_from,
                address_from=self.args.address_from,
                envelope_to=self.args.envelope_to,
                address_to=self.args.address_to,
                address_cc=self.args.address_cc,
                reply_to=self.args.reply_to,
                body_type=self.args.body_type,
                body_html=self.args.body_html,
                body_plain=self.args.body_plain,
                template_fields=self.args.template_fields,
                template_fields_json=self.args.template_fields_json,
                headers=self.args.headers,
            )
            message_body = message_builder.execute()

        if self.args.profile:
            profile = PREDEFINED_PROFILES[self.args.profile]
        else:
            profile = None

        try:
            send_message = message.Sender(
                predefined_profile=profile,
                predefined_message=predefined_message,
                connection_timeout=self.args.connection_timeout,
                source_address=self.args.source_address,
                debug_level=self.args.debug_level,
                host=self.args.host,
                port=self.args.port,
                identify_as=self.args.identify_as,
                tls=self.args.tls,
                ssl=self.args.ssl,
                login=self.args.login,
                password=self.args.password,
                envelope_from=self.args.envelope_from,
                address_from=self.args.address_from,
                envelope_to=self.args.envelope_to,
                address_to=self.args.address_to,
                address_cc=self.args.address_cc,
                address_bcc=self.args.address_bcc,
                reply_to=self.args.reply_to,
                message_body=message_body,
                no_ssl=self.args.no_ssl,
                no_tls=self.args.no_tls,
                dry_run=self.args.dry_run,
            )
            send_message.execute()
        except (smtplib.SMTPSenderRefused, smtplib.SMTPAuthenticationError) as exc:
            logger.error(exc.smtp_error.decode(), smtp_code=exc.smtp_code)


def main():
    ensure_config_files()

    global PREDEFINED_PROFILES, PREDEFINED_MESSAGES
    try:
        PREDEFINED_PROFILES = PredefinedProfiles.read()
    except toml.decoder.TomlDecodeError as exc:
        PREDEFINED_PROFILES = PredefinedProfiles()
        # TODO: shouldn't be logger call?
        logger.error(f"profiles configuration error: {exc}")

    try:
        PREDEFINED_MESSAGES = PredefinedMessages.read()
    except toml.decoder.TomlDecodeError as exc:
        PREDEFINED_MESSAGES = PredefinedMessages()
        # TODO: shouldn't be logger call?
        logger.error(f"messages configuration error: {exc}")

    args = parse_argv(sys.argv[1:])
    configure_logger(args.debug_level > 0)

    if args.command == 'profiles':
        handler = ProfilesCommand(args)
    elif args.command == 'send':
        handler = SendCommand(args)
    elif args.command == 'messages':
        handler = MessagesCommand(args)

    handler.handle()

    exitc(ExitCodes.OK)
