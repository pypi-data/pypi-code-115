# -*- coding: utf-8 -*-
import json
from msilib.schema import Billboard
from random import randint
from xml.etree.ElementTree import tostring

from tests.api.test_api_base import ApiTestBase
from yuansfer.dto.recurring.paypal_billingcycle import PayPalBillingCycle
from yuansfer.dto.recurring.paypal_billingcycle_amount import PayPalBillingCycleAmount
from yuansfer.dto.recurring.paypal_billingcycle_frequency import PayPalBillingCycleFrequency
from yuansfer.dto.recurring.paypal_billingcycle_pricingscheme import PayPalBillingCyclePricingScheme
from yuansfer.dto.recurring.paypal_paymentpreferences import PayPalPaymentPreferences
from yuansfer.dto.recurring.paypal_paymentpreferences_setupfee import PayPalPaymentPreferencesSetUpFee
from yuansfer.dto.recurring.paypal_productschema import PayPalProductSchema
from yuansfer.dto.recurring.paypal_taxes import PayPalTaxes

class RecurringApiTests(ApiTestBase):
    # Class to initialize Yuansfer configuration
    @classmethod
    def setUpClass(cls):
        super(RecurringApiTests, cls).setUpClass()

    # Make Recurring Payment request.
    def test_paypal_subscription(self):
        # Parameters for the API call
        testNumber = str(randint(0,100000000))

        # Declare PayPal Billing Cycle Object
        paypalBillingCycle = PayPalBillingCycle()
        paypalBillingCycle.sequence = 1
        paypalBillingCycle.tenure_type = "REGULAR"
        paypalBillingCycle.total_cycles = 999
        paypalBillingCycle.frequency = PayPalBillingCycleFrequency()
        paypalBillingCycle.frequency.interval_count = 1
        paypalBillingCycle.frequency.interval_unit = "MONTH"
        paypalBillingCycle.pricing_scheme = PayPalBillingCyclePricingScheme()
        paypalBillingCycle.pricing_scheme.fixed_price = PayPalBillingCycleAmount()
        paypalBillingCycle.pricing_scheme.fixed_price.value = 20
        paypalBillingCycle.pricing_scheme.fixed_price.currency_code = "USD"

        # Declare PayPal Payment Preferences Object
        paypalPaymentPreferences = PayPalPaymentPreferences()
        paypalPaymentPreferences.auto_bill_outstanding = True
        paypalPaymentPreferences.setup_fee = PayPalPaymentPreferencesSetUpFee()
        paypalPaymentPreferences.setup_fee.value = 20
        paypalPaymentPreferences.setup_fee.currency_code = "USD"
        paypalPaymentPreferences.setup_fee_failure_action = "CONTINUE"
        paypalPaymentPreferences.Payment_failure_threshold = 3

        # Declare PayPal Taxes Object
        paypalTaxes = PayPalTaxes()
        paypalTaxes.percentage = "10"
        paypalTaxes.inclusive = True

        # Declare PayPal Product Schema Object
        payPalProductSchema = PayPalProductSchema()
        payPalProductSchema.type = "SERVICE"
        payPalProductSchema.category = "SOFTWARE"

        params = {
            "clientId": "<MerchantPayPalClientID>",
            "secret": "<MerchantPayPalSecretID>",
            'amount': "100",
            "productName": "descriptive name for product test_" + testNumber,
            "planName": "descriptive name for plan test_" + testNumber,
            "planDescription": "detailed description for plan_" + testNumber,
            "requestIdProduct": "unique Id for create product request_" + testNumber,
            "requestIdPlan": "unique Id for create plan request_" + testNumber,
            "frequency": "MONTH",
            "billingCycles": json.dumps([paypalBillingCycle]
            ),
            "paymentPreferences": json.dumps(
                paypalPaymentPreferences
            ),
            "taxes": json.dumps(
                paypalTaxes
            ),
            "productSchema": json.dumps(payPalProductSchema)
        }

        # Perfo                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    rm the API call through the SDK function
        response = self.client.recurring.paypal_subscription(params)
        data = response.body
        # Test response code
        self.assertEqual(data['ret_code'], '000100')

unittest = RecurringApiTests()
unittest.setUpClass()
unittest.test_paypal_subscription()