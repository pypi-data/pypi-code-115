#!/usr/bin/env python
import json
from .BaseApi import BaseApi

class WalletApi(BaseApi):

    def __init__(self, walletKey, secretKey, cryptoSymbol):
        self.name = "WalletApi"
        self.headers = {
            "X-Wallet-Key": walletKey,
            "X-Secret-Key": secretKey
        }
        self.suffix = f"wallet/{cryptoSymbol}"
        super().__init__(suffix=self.suffix, headers=self.headers)

    def getBlockchainInfo(self):
        return self.executeRequest('GET', 'blockchain-info')

    def getTransactionInfo(self, txid):
        return self.executeRequest('GET', 'transaction-info', {'txid': txid})

    def getDepositAddresses(self):
        return self.executeRequest('GET', 'deposit-addresses')

    def validateAddresses(self, addresses):
        return self.executeRequest('POST', 'validate-addresses',{
            'addresses' : json.dumps(addresses)
        })
    
    def estimateFee(self, destinations, feePerByte = None, extraField = None):
        return self.executeRequest('POST', 'estimate-fee',{
            'destination' : json.dumps(destinations),
            'fee_per_byte' : feePerByte,
            'extra_field' : extraField
        })
    
    def sendTransaction(self, destinations, feePerByte = None, extraField = None):
        return self.executeRequest('POST', 'send-transaction',{
            'destination' : json.dumps(destinations),
            'fee_per_byte' : feePerByte,
            'extra_field' : extraField
        })      

        