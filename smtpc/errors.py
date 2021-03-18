class SMTPcError(Exception):
    pass


class MissingBodyError(SMTPcError):
    pass


class TemplateError(SMTPcError):
    pass


class InvalidTemplateFieldNameError(TemplateError):
    pass


class InvalidJsonTemplateError(TemplateError):
    pass
