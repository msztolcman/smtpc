__all__ = ['determine_ssl_tls_by_port', 'exitc', 'get_editor']

import os
import sys
from typing import Optional, NoReturn, Tuple

from .enums import ExitCodes


def exitc(err_code: ExitCodes) -> NoReturn:
    sys.exit(err_code.value)


def get_editor() -> str:
    return os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vim'


def determine_ssl_tls_by_port(
    port: Optional[int],
    ssl: Optional[bool], tls: Optional[bool],
    no_ssl: Optional[bool] = None, no_tls: Optional[bool] = None,
) -> Tuple[bool, bool]:
    if not ssl and not tls:
        if port == 465 and not no_ssl:
            ssl = True
        elif port == 587 and not no_tls:
            tls = True

    return ssl, tls
