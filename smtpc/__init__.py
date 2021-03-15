__all__ = ('__version__', )

__version__ = '0.3.0'

import enum


class ContentType(enum.Enum):
    PLAIN = 'plain'
    HTML = 'html'
    ALTERNATIVE = 'alternative'


