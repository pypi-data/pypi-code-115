from django.db import models
from django.utils.translation import gettext_lazy as _

from simpel_actions import mixins

from . import const


class SalesQuotationActionMixin(
    mixins.PendingMixin,
    mixins.ValidateMixin,
    mixins.StatusMixin,
):
    """Give model status three step status tracking and action,
    draft -> validate or trash -> approve/reject -> process -> complete
    """

    PENDING = const.PENDING
    VALID = const.VALID
    STATUS_CHOICES = (
        (PENDING, _("Pending")),
        (VALID, _("Valid")),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=const.PENDING)

    class Meta:
        abstract = True

    def get_error_msg(self, action):
        help_text = ""
        msg = _("{}, {} is {}, it can't be {}. {}")
        return str(msg).format(
            self.opts.verbose_name,
            self,
            self.get_status_display(),
            action,
            help_text,
        )

    @property
    def is_editable(self):
        return self.is_pending

    @property
    def validate_ignore_condition(self):
        return self.is_valid

    @property
    def validate_valid_condition(self):
        return self.is_pending

    def post_validate_action(self):
        # Send email to customer
        pass


class SalesOrderActionMixin(
    mixins.PendingMixin,
    mixins.ValidateMixin,
    mixins.CancelMixin,
    mixins.ProcessMixin,
    mixins.CompleteMixin,
    mixins.CloseMixin,
    mixins.StatusMixin,
):
    """Give model status three step status tracking and action,
    draft -> validate or trash -> approve/reject -> process -> complete
    """

    PENDING = const.PENDING
    VALID = const.VALID
    CANCELED = const.CANCELED
    PROCESSED = const.PROCESSED
    COMPLETE = const.COMPLETE
    INVOICED = const.INVOICED
    CLOSED = const.CLOSED
    STATUS_CHOICES = (
        (PENDING, _("Pending")),
        (VALID, _("Valid")),
        (CANCELED, _("Canceled")),
        (PROCESSED, _("Processed")),
        (INVOICED, _("Invoiced")),
        (CLOSED, _("Closed")),
        (COMPLETE, _("Complete")),
    )
    date_invoiced = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("date invoiced"),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=const.PENDING)

    class Meta:
        abstract = True

    def get_error_msg(self, action):
        help_text = ""
        msg = _("{}, {} is {}, it can't be {}. {}")
        if action == "completed":
            help_text = _("You need to process this order by create valid workorder.")
        if action == "invoiced":
            msg = _("{}, {} is {}, it can't be {} {}")
            help_text = _(
                "until it's completed, you can make it complete by create valid final document for this order."
            )
        return str(msg).format(
            self.opts.verbose_name,
            self,
            self.get_status_display(),
            action,
            help_text,
        )

    @property
    def validate_ignore_condition(self):
        return self.is_valid or self.is_processed or self.is_complete or self.is_invoiced or self.is_closed

    @property
    def validate_valid_condition(self):
        return self.is_pending

    @property
    def cancel_ignore_condition(self):
        return self.is_canceled or self.is_processed or self.is_complete or self.is_invoiced or self.is_closed

    @property
    def cancel_valid_condition(self):
        return self.is_valid or self.is_pending

    @property
    def process_ignore_condition(self):
        return self.is_processed or self.is_complete or self.is_invoiced or self.is_closed

    @property
    def process_valid_condition(self):
        return self.is_valid

    @property
    def complete_ignore_condition(self):
        return self.is_complete or self.is_closed

    @property
    def complete_valid_condition(self):
        return self.is_processed

    @property
    def close_ignore_condition(self):
        return self.is_closed

    @property
    def close_valid_condition(self):
        return self.is_invoiced


class InvoiceActionMixin(
    mixins.TrashMixin,
    mixins.PendingMixin,
    mixins.ValidateMixin,
    mixins.CancelMixin,
    mixins.PaidMixin,
    mixins.CloseMixin,
    mixins.StatusMixin,
):
    class Meta:
        abstract = True

    TRASH = const.TRASH
    PENDING = const.PENDING
    VALID = const.VALID
    CANCELED = const.CANCELED
    PAID = const.PAID
    CLOSED = const.CLOSED
    STATUS_CHOICES = (
        (TRASH, _("Trash")),
        (PENDING, _("Pending")),
        (VALID, _("Valid")),
        (CANCELED, _("Canceled")),
        (PAID, _("Paid")),
        (CLOSED, _("Closed")),
    )

    status = models.IntegerField(choices=STATUS_CHOICES, default=const.PENDING)
    date_closed = models.DateTimeField(
        default=None,
        null=True,
        blank=True,
        editable=False,
        verbose_name=_("Date closed"),
    )

    @property
    def trash_ignore_condition(self):
        return self.is_trash

    @property
    def trash_valid_condition(self):
        return self.is_pending or self.is_canceled

    @property
    def validate_ignore_condition(self):
        return self.is_valid or self.is_paid or self.is_closed

    @property
    def validate_valid_condition(self):
        return self.is_pending or self.is_canceled

    @property
    def cancel_ignore_condition(self):
        return self.is_canceled or self.is_paid or self.is_closed

    @property
    def cancel_valid_condition(self):
        return self.is_cancelable

    @property
    def pay_ignore_condition(self):
        return self.is_paid or self.is_closed

    @property
    def pay_valid_condition(self):
        return self.is_valid

    @property
    def close_ignore_condition(self):
        return self.is_payable

    @property
    def close_valid_condition(self):
        return self.is_valid and self.payable == 0
