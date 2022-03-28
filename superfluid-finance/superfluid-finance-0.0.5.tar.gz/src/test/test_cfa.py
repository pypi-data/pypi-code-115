
import pytest
import superfluid_finance.CFAV1 as cfa
from superfluid_finance import account_provider as a
import web3
from superfluid_finance.provider import infura_connect
from brownie import convert

@pytest.fixture(scope="session")
def account1():
    return a.load_account("0")

@pytest.fixture(scope="session")
def account2():
    return a.load_account("1")

@pytest.fixture(scope="session")
def _cfa():
    return cfa.CFA("kovan", "infura")

@pytest.fixture(scope="module")
def w3():
    return infura_connect("kovan")

@pytest.fixture(scope="module")
def token():
    w3 = infura_connect("kovan")
    return w3.toChecksumAddress("0x43F54B13A0b17F67E61C9f0e41C3348B3a2BDa09")


def test_net_flow(w3, _cfa):
    #_cfa.get_DepositRequiredForFlowRate(w3.toChecksumAddress("0x43F54B13A0b17F67E61C9f0e41C3348B3a2BDa09"), 256888555)
    net =_cfa.get_net_flow(
        w3.toChecksumAddress("0x43F54B13A0b17F67E61C9f0e41C3348B3a2BDa09"),
        w3.toChecksumAddress("0xaC18157FFFdc96C9724eB1CF42eb05F8f70e645B")
    )

#This function tests the current flow between two addresses
#if the flow rate is not zero, it deletes the flow to prepare for the next test function
#hence, it tests the get_flow & delete flow
def test_get_flow(w3, _cfa, token, account1):
    
    flow_info = _cfa.get_flow(
        token,
        account1.address,
        w3.toChecksumAddress("0xC6dfd274bB7ed085d7465CF848C1F0D4065d6dF6")
    )

    if flow_info[1] != 0:
        _cfa.delete_flow(
            token,
            account1.address,
            w3.toChecksumAddress("0xC6dfd274bB7ed085d7465CF848C1F0D4065d6dF6"),
            "",
            account1
        )
    flow_info = _cfa.get_flow(
        token,
        account1.address,
        w3.toChecksumAddress("0xC6dfd274bB7ed085d7465CF848C1F0D4065d6dF6")
    )
    assert(
        flow_info[1] == 0
    )


#This function tests the creation of a flow flom account1 to the address
def test_create_flow(_cfa, token, account1):
    _cfa.create_flow(
        token,
        "0xC6dfd274bB7ed085d7465CF848C1F0D4065d6dF6",
        120000000000000,
        "",
        account1
    )
    flow_info = _cfa.get_flow(
        token,
        account1.address,
        "0xC6dfd274bB7ed085d7465CF848C1F0D4065d6dF6"
    )
    assert(
        flow_info[1] == 120000000000000
    )

def test_update_flow(_cfa, token, account1):
    _cfa.update_flow(
        token,
        "0xC6dfd274bB7ed085d7465CF848C1F0D4065d6dF6",
        180000000000000,
        "",
        account1
    )
    flow_info = _cfa.get_flow(
        token,
        account1,
        "0xC6dfd274bB7ed085d7465CF848C1F0D4065d6dF6"
    )
    assert(
        flow_info[1] == 180000000000000
    )

