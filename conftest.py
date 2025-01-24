import pytest
from django.core import mail


@pytest.fixture(scope="function", autouse=True)
def _dj_autoclear_mailbox():
    """
    Override the `_dj_autoclear_mailbox` test fixture in `pytest_django`
    to clear the outbox only if it exists.
    """
    if hasattr(mail, 'outbox'):
        del mail.outbox[:]
