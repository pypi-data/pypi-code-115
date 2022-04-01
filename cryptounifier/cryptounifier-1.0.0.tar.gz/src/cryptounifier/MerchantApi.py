#!/usr/bin/env python
import json
from .BaseApi import BaseApi

class MerchantApi(BaseApi):

    def __init__(self, merchantKey, secretKey):
        self.name = "MerchantApi"
        self.headers = {
            "X-Merchant-Key": merchantKey,
            "X-Secret-Key": secretKey
        }
        self.suffix = "merchant"
        super().__init__(suffix=self.suffix, headers=self.headers)

    def invoiceInfo(self, invoiceHash):
        return self.executeRequest("GET",
                                   "invoice-info",
                                   {"invoice_hash": invoiceHash})

    def processInvoices(self, invoiceHashes):
        return self.executeRequest("POST",
                                   "process-invoices",
                                   {"invoice_hashes": invoiceHashes})

    def forwardInvoices(self, invoiceHashes):
        return self.executeRequest("POST", "forwards-invoices", {"invoice_hashes": invoiceHashes})

    def generateInvoiceAddress(self, invoiceHash, cryptocurrency):
        return self.executeRequest("POST", "generate-invoice-address", {
            "invoice_hash": invoiceHash,
            "cryptocurrency": cryptocurrency
        })

    def createInvoice(self, cryptocurrencies, currency=None, targetValue=None, title=None, description=None ):
       return self.executeRequest("POST", "create-invoice", {
            "cryptocurrencies" :  json.dumps(cryptocurrencies),
            "currency"         : currency,
            "target_value"     : targetValue,
            "title"            : title,
            "description"      : description
        })

    def estimateInvoicePrice(self, cryptocurrencies, currency=None, targetValue=None):
        return self.executeRequest("POST", "estimate-invoice-price", {
            "cryptocurrencies" :  json.dumps(cryptocurrencies),
            "currency"         : currency,
            "target_value"     : targetValue
        })

    def recoverInvoicePrivateKey(self, invoiceHash, cryptocurrency):
        return self.executeRequest("POST","recover-invoice-private-key",{
            "invoice_hash" : invoiceHash,
            "cryptocurrency" : cryptocurrency
        }) 