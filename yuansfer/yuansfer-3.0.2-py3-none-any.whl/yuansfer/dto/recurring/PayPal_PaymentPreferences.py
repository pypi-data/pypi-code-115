# -*- coding: utf-8 -*-
from yuansfer.dto.recurring.paypal_paymentpreferences_setupfee import PayPalPaymentPreferencesSetUpFee

class PayPalPaymentPreferences(dict):
    def __init__(self, auto_bill_outstanding: bool = None, setup_fee: PayPalPaymentPreferencesSetUpFee = None,
    setup_fee_failure_action = None, payment_failure_threshold: int = None):
        self.auto_bill_outstanding = str(auto_bill_outstanding).lower() if auto_bill_outstanding is not None else auto_bill_outstanding
        self.setup_fee = setup_fee
        self.setup_fee_failure_action = setup_fee_failure_action
        self.Payment_failure_threshold = payment_failure_threshold
        self.__dict__ = self