__all__ = ('LoanPoint', 'PayPoint', 'ClosedLoanPoint')

from typing import OrderedDict, Union

from expressmoney.api import *

SERVICE = 'loans'


class CommonLoan(Contract):
    OPEN = "OPEN"  # Customer received money
    OVERDUE = "OVERDUE"
    STOP_INTEREST = "STOP_INTEREST"
    DEFAULT = "DEFAULT"
    CLOSED = "CLOSED"
    STATUS_CHOICES = {
        (OPEN, "Open"),
        (OVERDUE, "Overdue"),
        (STOP_INTEREST, "Stop interest"),
        (DEFAULT, "Default"),
        (CLOSED, "Closed")
    }
    OPEN_STATUSES = (OPEN, OVERDUE, STOP_INTEREST, DEFAULT)

    id = serializers.IntegerField(min_value=1)
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()
    order = serializers.IntegerField(min_value=1)
    interests_charged_date = serializers.DateField(allow_null=True)
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
    sign = serializers.IntegerField()
    ip = serializers.IPAddressField()
    document = serializers.CharField(max_length=256, allow_blank=True)
    comment = serializers.CharField(max_length=2048, allow_blank=True)

    amount = serializers.DecimalField(max_digits=16, decimal_places=0)
    period = serializers.IntegerField(min_value=0)
    free_period = serializers.IntegerField(min_value=0)
    interests = serializers.DecimalField(max_digits=3, decimal_places=2)
    expiry_date = serializers.DateField()
    expiry_period = serializers.IntegerField(min_value=0)
    body_balance = serializers.DecimalField(max_digits=16, decimal_places=0)
    body_paid = serializers.DecimalField(max_digits=16, decimal_places=0)
    interests_total = serializers.DecimalField(max_digits=16, decimal_places=0)
    interests_paid = serializers.DecimalField(max_digits=16, decimal_places=0)
    interests_balance = serializers.DecimalField(max_digits=16, decimal_places=0)


class LoanReadContract(CommonLoan):
    pass


class LoanCreateContract(Contract):
    sign = serializers.IntegerField()


class ClosedLoanContract(CommonLoan):
    pass


class PayUpdateContract(Contract):
    bank_card_id = serializers.IntegerField()


class LoanID(ID):
    _service = SERVICE
    _app = 'loans'
    _view_set = 'loan'


class PayID(ID):
    _service = SERVICE
    _app = 'loans'
    _view_set = 'pay'


class ClosedLoanID(ID):
    _service = SERVICE
    _app = 'loans'
    _view_set = 'closed_loan'


class LoanPoint(ListPointMixin, CreatePointMixin, ContractPoint):
    _point_id = LoanID()
    _read_contract = LoanReadContract
    _create_contract = LoanCreateContract

    def open_loans(self) -> tuple:
        return self.filter(status=self._read_contract.OPEN_STATUSES)

    def open_loans_last(self) -> Union[None, OrderedDict]:
        objects = self.open_loans()
        return objects[-1] if len(objects) > 0 else None


class PayPoint(UpdatePointMixin, ContractObjectPoint):
    _point_id = PayID()
    _update_contract = PayUpdateContract


class ClosedLoanPoint(ListPointMixin, ContractPoint):
    _point_id = ClosedLoanID()
    _read_contract = ClosedLoanContract
