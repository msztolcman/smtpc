__all__ = ['guess_content_type', 'exit']

import sys
from typing import Optional

from .enums import ContentType, ExitCodes


def exit(err_code: ExitCodes):
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
