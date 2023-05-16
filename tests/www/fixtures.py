from random import randint
from uuid import uuid4

import pytest


@pytest.fixture()
def code():
    return str(randint(1, 100))


@pytest.fixture()
def state():
    return str(uuid4())
