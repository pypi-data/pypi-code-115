import pytest
from superfluid_finance.supertoken_factory import SupertokenFatory 
from superfluid_finance import account_provider as a
from superfluid_finance import con_addresses

@pytest.fixture(scope="module")
def factory():
    return SupertokenFatory("kovan", "infura")

def test_view_function(factory):
    host = factory.get_host()
    host_local = con_addresses.addresses[factory.network]["host"]

    assert(host == host_local)

def test_wrap_token():
    pass