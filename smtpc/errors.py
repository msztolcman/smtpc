class SMTPcError(Exception):
    pass


class MissingBodyError(SMTPcError):
    pass
