__all__ = ('__version__', )

__version__ = '0.3.0'

import enum


class EMPTY:
    def __contains__(self, k):
        return False


EMPTY = EMPTY()


class ContentType(enum.Enum):
    PLAIN = 'plain'
    HTML = 'html'
    ALTERNATIVE = 'alternative'


