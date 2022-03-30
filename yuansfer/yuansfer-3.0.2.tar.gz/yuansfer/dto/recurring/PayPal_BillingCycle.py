# -*- coding: utf-8 -*-
from yuansfer.dto.recurring.paypal_billingcycle_pricingscheme import PayPalBillingCyclePricingScheme
from yuansfer.dto.recurring.paypal_billingcycle_frequency import PayPalBillingCycleFrequency

class PayPalBillingCycle(dict):
    def __init__(self, pricing_scheme: PayPalBillingCyclePricingScheme = None, frequency: PayPalBillingCycleFrequency = None, tenure_type = None,sequence: int = None,total_cycles: int = None):
        self.pricing_scheme = pricing_scheme
        self.frequency = frequency
        self.tenure_type = tenure_type
        self.sequence = sequence
        self.total_cycles = total_cycles
        self.__dict__ = self