#!/usr/bin/env python
import json
from .BaseApi import BaseApi

class WalletTokenApi(BaseApi):

    def __init__(self, walletKey, secretKey, cryptoSymbol, tokenSymbol):
        self.name = "WalletTokenApi"
        self.headers = {
            "X-Wallet-Key": walletKey,
            "X-Secret-Key": secretKey
        }
        self.suffix = f"wallet/{cryptoSymbol}/token/{tokenSymbol}"
        super().__init__(suffix=self.suffix, headers=self.headers)

    def getBalance(self):
        return self.executeRequest('GET', 'balance')
    
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

        