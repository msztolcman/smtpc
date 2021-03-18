__all__ = ['guess_content_type', 'determine_ssl_tls_by_port', 'exitc']

import sys
from typing import Optional

from .enums import ContentType, ExitCodes


def exitc(err_code: ExitCodes):
    sys.exit(err_code.value)


def guess_content_type(body_type: Optional[str], body_plain: Optional[str], body_html: Optional[str]) -> ContentType:
    if body_type in ('plain', 'html'):
        body_type = ContentType(body_type)
    elif body_plain and body_html:
        body_type = ContentType.ALTERNATIVE
    elif body_plain and not body_html:
        body_type = ContentType.PLAIN
    elif not body_plain and body_html:
        body_type = ContentType.HTML
    else:
        body_type = ContentType.PLAIN
    return body_type


def determine_ssl_tls_by_port(
    port: Optional[int],
    ssl: Optional[bool], tls: Optional[bool],
    no_ssl: Optional[bool] = None, no_tls: Optional[bool] = None
):
    if not ssl and not tls:
        if port == 465 and not no_ssl:
            ssl = True
        elif port == 587 and not no_tls:
            tls = True

    return ssl, tls
