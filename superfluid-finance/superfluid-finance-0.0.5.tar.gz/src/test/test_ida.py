import pytest
from superfluid_finance.IDAV1 import IDA
from superfluid_finance import account_provider as a
import web3
from superfluid_finance.provider import infura_connect

@pytest.fixture(scope="session")
def account1():
    return a.load_account("0")

@pytest.fixture(scope="session")
def account2():
    return a.load_account("1")

@pytest.fixture(scope="session")
def _ida():
    return IDA("kovan", "infura")

@pytest.fixture(scope="session")
def w3():
    return infura_connect("kovan")

@pytest.fixture(scope="session")
def index():
    return 1

@pytest.fixture(scope="module")
def token():
    w3 = infura_connect("kovan")
    return w3.toChecksumAddress("0x43F54B13A0b17F67E61C9f0e41C3348B3a2BDa09")


def test_create_index(token, _ida, index, account1):
    _ida.create_index(token, index, "", account1)

    checker = _ida.get_index(token, account1, index)
    assert(
        checker[0] == True
    )

def test_update_index(token, _ida, index, account1):
    _ida.update_index(token, index, 100000000000000000000, "", account1)

    checker = _ida.get_index(token, account1, index)

    assert(
        checker[1] == 100000000000000000000
    )



