import pytest

from smtpc import message
from smtpc.errors import InvalidTemplateFieldNameError, InvalidJsonTemplateError
from smtpc.message import SimpleTemplate


@pytest.mark.parametrize('name', [
    'a',
    'asdf',
    'asdfZXCV',
    'asdfZXCV123',
    'ZXCV123',
    'ZXCV123_aa',
])
def test_field_name_validator_valid_names(name):
    print(type(name), name)
    assert message.Builder._template_validate_field_name(name) is None


@pytest.mark.parametrize('name', [
    '',
    ' ',
    'a a',
    'aa@aa',
    'aa.aa',
])
def test_field_name_validator_incorrect_names(name):
    with pytest.raises(InvalidTemplateFieldNameError):
        message.Builder._template_validate_field_name(name)


@pytest.mark.parametrize('name', [
    None,
    123,
    True,
    False
])
def test_field_name_validator_incorrect_names(name):
    with pytest.raises(TypeError):
        message.Builder._template_validate_field_name(name)


@pytest.mark.parametrize('field, expected', [
    ['name=value', ('name', 'value')],
    ['name=value other = value', ('name', 'value other = value')],
    ['name=', ('name', '')],
    ['name={asd}', ('name', '{asd}')],
])
def test_parsing_fields_simple(field, expected):
    assert message.Builder._template_parse_field(field) == expected


@pytest.mark.parametrize('field, expected', [
    ['name=[]', ('name', [])],
    ['name=123', ('name', 123)],
    ['name={}', ('name', {})],
    ['name=["a", "b", "c"]', ('name', ['a', 'b', 'c'])],
    ['name={"a": 1, "b": 2, "c": 3}', ('name', {"a": 1, "b": 2, "c": 3})],
    ['name={"a": 1, "b": 2, "c": [1, 2, 3]}', ('name', {"a": 1, "b": 2, "c": [1, 2, 3]})],
    ['name=null', ('name', None)],
])
def test_parsing_fields_json_valid(field, expected):
    assert message.Builder._template_parse_field(field, True) == expected


@pytest.mark.parametrize('field', [
    'name=value other = value',
    'name={asd}',
    'name=[asd]',
    'name=',
    'name={0}',
])
def test_parsing_fields_json_incorrect(field):
    with pytest.raises(InvalidJsonTemplateError):
        message.Builder._template_parse_field(field, True)


@pytest.mark.parametrize('tpl, fields, expected', [
    ['', {'a': 1}, ''],
    ['asd', {'a': 1}, 'asd'],
    ['asd {{ value }} asd', {'a': 1}, 'asd {{ value }} asd'],
    ['asd {{ value }} asd', {'value': 'INSIDE'}, 'asd INSIDE asd'],
    ['asd {{value }} asd', {'value': 'INSIDE'}, 'asd INSIDE asd'],
    ['asd {{value}} asd', {'value': 'INSIDE'}, 'asd INSIDE asd'],
    ['asd {{value}} asd', {'value': 'INSIDE'}, 'asd INSIDE asd'],
    ['asd {{value}} asd {% if something %}{% endif %}', {'value': 'INSIDE'}, 'asd INSIDE asd {% if something %}{% endif %}'],
])
def test_simple_template_valid(tpl, fields, expected):
    t = SimpleTemplate(tpl)
    v = t.render(**fields)
    assert v == expected
