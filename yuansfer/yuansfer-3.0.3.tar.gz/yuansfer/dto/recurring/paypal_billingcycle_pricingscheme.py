# -*- coding: utf-8 -*-
from yuansfer.dto.recurring.paypal_billingcycle_amount import PayPalBillingCycleAmount
from yuansfer.dto.recurring.paypal_billingcycle_frequency import PayPalBillingCycleFrequency
class PayPalBillingCyclePricingScheme(dict):
    def __init__(
            self,
            version: int = None,
            fixed_price: PayPalBillingCycleAmount = None,
            pricing_model = None,
            tiers: PayPalBillingCycleFrequency = None,
            update_time = None, create_time = None):
        self.version = version
        self.fixed_price = fixed_price
        self.pricing_model = pricing_model
        self.tiers = tiers
        self.update_time = update_time
        self.create_time = create_time
        self.__dict__ = self