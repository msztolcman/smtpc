from smtpc.enums import ContentType
from smtpc.message import Builder


def test_builder_simple():
    builder = Builder(
        subject='some subject',
        envelope_from=None,
        address_from='smtpc@example.com',
        envelope_to=None,
        address_to=['smtpc@example.net'],
        address_cc=['smtpc@example.org'],
        reply_to=['smtpc@example.gov'],
        body_type=ContentType.PLAIN,
        body_html=None,
        body_plain='some body',
        headers=[],
        message=None,
    )

    assert builder.subject == 'some subject'
    assert builder.envelope_from is None
    assert builder.address_from == 'smtpc@example.com'
    assert builder.envelope_to == []
    assert builder.address_to == ['smtpc@example.net']
    assert builder.address_cc == ['smtpc@example.org']
    assert builder.reply_to == ['smtpc@example.gov']
    assert builder.body_type == ContentType.PLAIN
    assert builder.body_html is None
    assert builder.body_plain == 'some body'
    assert builder.headers == []
