class SMTPcError(Exception):
    pass


class MissingBodyError(SMTPcError):
    pass


class InvalidTemplateFieldName(SMTPcError):
    pass
