from unittest import mock

import pytest


@pytest.fixture(scope='function', autouse=True)
def patch_smtpc_cli_select_select():
    with mock.patch('smtpc.cli.select.select', autospec=True) as mocked_select_select:
        mocked_select_select.return_value = (False, )
        yield
