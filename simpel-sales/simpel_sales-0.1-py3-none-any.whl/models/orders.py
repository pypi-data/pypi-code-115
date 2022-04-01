from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from polymorphic.models import PolymorphicModel
from simpel_actions import mixins
from simpel_contacts.models import BillingAddress, DeliverableAddress, ShippingAddress
from simpel_numerators.models import NumeratorMixin, NumeratorReset
from simpel_products.models import Group, Product
from simpel_qrcodes.models import LinkedQRCode
from simpel_utils.models.paranoid import ParanoidMixin
from simpel_utils.urls import reverse

from simpel_sales import const

from ..settings import sales_settings
from .managers import OrderItemBundleManager, OrderItemManager, OrderManager

__all__ = ["SalesOrder", "SalesOrderItem", "SalesOrderItemBundle", "order_expired_limit"]


def order_expired_limit():
    return timezone.now() + timedelta(
        days=sales_settings.ORDER_EXPIRATION_LIMIT,
    )


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
    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)

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


class SalesOrder(PolymorphicModel, NumeratorMixin, SalesOrderActionMixin, ParanoidMixin):

    # Reference & Meta Fields
    user = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="sales_orders",
        verbose_name=_("Created By"),
    )
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="salesorders",
        verbose_name=_("Group"),
    )
    customer_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="salesorders",
        verbose_name=_("Customer Type"),
    )
    customer_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Customer ID"),
    )
    customer = GenericForeignKey(
        "customer_type",
        "customer_id",
    )
    reference = models.CharField(
        _("PO Number"),
        max_length=50,
        null=True,
        blank=True,
        help_text=_(
            "Purchase Order number.",
        ),
    )
    discount = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        verbose_name=_("Discount"),
    )
    expired_at = models.DateTimeField(
        default=order_expired_limit,
        null=True,
        blank=True,
        editable=False,
    )

    note = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Note"),
    )
    data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Extra data"),
    )
    total = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Total"),
    )
    grand_total = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Grand Total"),
    )
    downpayment = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Down Payment"),
    )
    payable = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Payable"),
    )

    billing_addresses = GenericRelation(
        BillingAddress,
        content_type_field="content_type",
        object_id_field="content_id",
    )
    shipping_addresses = GenericRelation(
        ShippingAddress,
        content_type_field="content_type",
        object_id_field="content_id",
    )

    qrcodes = GenericRelation(
        LinkedQRCode,
        content_type_field="linked_object_type",
        object_id_field="linked_object_id",
    )

    allow_comments = models.BooleanField(default=True)

    objects = OrderManager()

    doc_prefix = "SO"
    reset_mode = NumeratorReset.MONTHLY

    class Meta:
        db_table = "simpel_sales_order"
        verbose_name = _("Sales Order")
        verbose_name_plural = _("Sales Orders")
        index_together = (
            "user",
            "group",
            "customer_type",
            "customer_id",
            "status",
        )
        permissions = (
            ("import_salesorder", _("Can import Sales Order")),
            ("export_salesorder", _("Can export Sales Order")),
            ("validate_salesorder", _("Can validate Sales Order")),
            ("process_salesorder", _("Can process Sales Order")),
            ("complete_salesorder", _("Can complete Sales Order")),
            ("close_salesorder", _("Can close Sales Order")),
        )

    def __str__(self):
        return "%s - %s" % (str(self.inner_id), self.customer)

    @cached_property
    def is_printable(self):
        return self.validate_ignore_condition

    @cached_property
    def is_editable(self):
        return self.is_pending

    @cached_property
    def is_invoiced(self):
        """Check object status is closed"""
        return self.invoice is not None

    @cached_property
    def is_payable(self):
        """Check object status is closed"""
        return self.is_printable and not self.is_invoiced and self.payable > 0

    @cached_property
    def has_workorder(self):
        return self.workorder is not None

    @cached_property
    def admin_url(self):
        view_name = "admin:simpel_sales_salesorder_inspect"
        return reverse(view_name, args=(self.id,), host="admin")

    def get_absolute_url(self):

        return reverse(sales_settings.ORDER_ABSOLUTE_URL_NAME, kwargs={"pk": self.pk})

    @cached_property
    def billing_address(self):
        return self.billing_addresses.first()

    @cached_property
    def shipping_address(self):
        return self.shipping_addresses.first()

    @cached_property
    def content_type(self):
        return ContentType.objects.get_for_model(self.__class__)

    @cached_property
    def workorder(self):
        workorders = getattr(self.content_type, "workorders", None)
        if workorders is not None:
            return workorders.filter(reference_id=self.inner_id).first()
        else:
            return None

    @cached_property
    def qrcode(self):
        return self.qrcodes.first()

    @cached_property
    def payments(self):
        ctype = ContentType.objects.get_for_model(self.__class__)
        payments = getattr(ctype, "payments", None)
        if payments is not None:
            return payments.filter(reference_id=self.inner_id)
        return None

    @cached_property
    def invoice(self):
        invoices = getattr(self.content_type, "invoices", None)
        if invoices is None:
            return None
        invoice = self.content_type.invoices.filter(reference_id=self.inner_id).first()
        return invoice

    @cached_property
    def items_count(self):
        return self.get_items_count()

    @cached_property
    def total_items(self):
        return self.get_total_items()

    @cached_property
    def final_document(self):
        return self.final_documents.first()

    def format_inner_id(self):
        """Inner ID final format"""
        form = [self.get_doc_prefix(), self.format_date(form="%m%y"), self.format_number()]
        inner_id = "{}.{}.{}".format(*form)
        return setattr(self, self.inner_id_field, inner_id)

    def get_items_count(self):
        return self.items.count()

    def get_total_items(self):
        return self.items.all().aggregate(total=models.Sum("total"))["total"] or 0

    def get_grand_total(self):
        return self.total - self.discount

    def get_downpayment(self):
        downpayment = Decimal("0.00")
        if self.payments is not None:
            downpayment = (
                self.payments.filter(status__in=[self.payments.model.APPROVED]).aggregate(total=models.Sum("amount"))
            )["total"] or Decimal("0.00")
        return downpayment

    def get_payable(self):
        return self.grand_total - self.downpayment

    def compute(self):
        self.total = self.get_total_items()
        self.grand_total = self.get_grand_total()
        self.downpayment = self.get_downpayment()
        self.payable = self.get_payable()

    def delete(self, *args, **kwargs):
        if self.qrcodes is not None:
            self.qrcodes.delete()
        if self.addresses is not None:
            self.addresses.delete()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.compute()
        return super().save(*args, **kwargs)


class SalesOrderItem(NumeratorMixin, ParanoidMixin):
    # Reference & Meta Fields
    salesorder = models.ForeignKey(
        SalesOrder,
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name="order_items",
        limit_choices_to={"is_sellable": True},
        null=False,
        blank=False,
        on_delete=models.PROTECT,
    )
    name = models.CharField(
        verbose_name=_("name"),
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
    )
    alias_name = models.CharField(
        verbose_name=_("alias name"),
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
    )
    note = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Note"),
    )

    price = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Price"),
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Quantity"),
        validators=[
            MinValueValidator(1, message=_("Minimal value: 1")),
            MaxValueValidator(500, message=_("Maximal value: 500")),
        ],
    )
    total_bundles = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Total Bundles"),
    )
    subtotal = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Sub Total"),
    )
    total = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Total"),
    )

    # Meta Fields
    position = models.IntegerField(
        default=0,
        verbose_name=_("position"),
        help_text=_("Enable sortable position"),
    )
    deliverable_informations = GenericRelation(
        DeliverableAddress,
        content_type_field="content_type",
        object_id_field="content_id",
    )

    doc_prefix = "SOI"
    objects = OrderItemManager()
    reset_mode = NumeratorReset.MONTHLY

    class Meta:
        db_table = "simpel_sales_order_item"
        ordering = ("position", "reg_number")
        index_together = ("salesorder", "product")
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        permissions = (
            ("import_salesorderitem", _("Can import Sales Order Item")),
            ("export_salesorderitem", _("Can export Sales Order Item")),
        )

    def __str__(self):
        return "%s Order #%s" % (self.inner_id, self.salesorder.inner_id)

    @cached_property
    def deliverable_information(self):
        return self.deliverable_informations.first()

    def format_inner_id(self):
        """Inner ID final format"""
        form = [self.get_doc_prefix(), self.format_date(form="%m%y"), self.format_number()]
        inner_id = "{}.{}.{}".format(*form)
        return setattr(self, self.inner_id_field, inner_id)

    @cached_property
    def group(self):
        return self.product.group

    @cached_property
    def group_verbose(self):
        return str(self.group)

    def get_total_bundles(self):
        return self.bundles.all().aggregate(total=models.Sum("total"))["total"] or 0

    def get_subtotal(self):
        return self.price + self.get_total_bundles()

    def get_total(self):
        return self.get_subtotal() * self.quantity

    def compute(self):
        if self._state.adding and self.product is not None:
            self.name = self.product.name
            self.price = self.product.specific.price
        self.total_bundles = self.get_total_bundles()
        self.subtotal = self.get_subtotal()
        self.total = self.get_total()

    def save(self, *args, **kwargs):
        self.compute()
        return super().save(*args, **kwargs)


class SalesOrderItemBundle(ParanoidMixin):
    # Reference & Meta Fields
    position = models.IntegerField(
        default=0,
        verbose_name=_("position"),
        help_text=_("Enable sortable position"),
    )
    item = models.ForeignKey(
        SalesOrderItem,
        related_name="bundles",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name="order_item_bundles",
        null=False,
        blank=False,
        limit_choices_to={
            "is_partial": True,
            "is_sellable": True,
        },
        on_delete=models.PROTECT,
    )
    name = models.CharField(
        verbose_name=_("name"),
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        editable=False,
    )
    price = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Price"),
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Quantity"),
        validators=[
            MinValueValidator(1, message=_("Minimal value: 1")),
            MaxValueValidator(500, message=_("Maximal value: 500")),
        ],
    )
    total = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        editable=False,
        verbose_name=_("Total"),
    )

    objects = OrderItemBundleManager()

    class Meta:
        db_table = "simpel_sales_order_item_bundle"
        ordering = ("position",)
        unique_together = ("item", "product")
        index_together = ("item", "product")
        verbose_name = _("Order Item Bundle")
        verbose_name_plural = _("Order Item Bundles")
        permissions = (
            ("import_salesorderitembundle", _("Can import Sales Order Item Bundle")),
            ("export_salesorderitembundle", _("Can export Sales Order Item Bundle")),
        )

    def get_total(self):
        return self.price * self.quantity

    def compute(self):
        if self._state.adding and self.product is not None:
            self.name = self.product.name
            self.price = self.product.specific.total_price
        self.total = self.get_total()

    def save(self, *args, **kwargs):
        self.compute()
        return super().save(*args, **kwargs)
