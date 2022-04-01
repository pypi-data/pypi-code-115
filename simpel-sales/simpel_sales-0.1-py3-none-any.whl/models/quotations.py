from datetime import timedelta

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
from simpel_contacts.models import BillingAddress, DeliverableAddress
from simpel_numerators.models import NumeratorMixin, NumeratorReset
from simpel_products.models import Group, Product
from simpel_qrcodes.models import LinkedQRCode
from simpel_utils.models.paranoid import ParanoidMixin
from simpel_utils.urls import reverse

from ..settings import sales_settings
from .managers import QuotationManager

__all__ = ["SalesQuotation", "SalesQuotationItem", "SalesQuotationItemBundle"]


def quotation_expired_limit():
    return timezone.now() + timedelta(
        days=sales_settings.QUOTATION_EXPIRATION_LIMIT,
    )


class SalesQuotationActionMixin(
    mixins.PendingMixin,
    mixins.ValidateMixin,
    mixins.StatusMixin,
):
    """Give model status three step status tracking and action,
    draft -> validate or trash -> approve/reject -> process -> complete
    """

    PENDING, VALID = range(2)
    STATUS_CHOICES = (
        (PENDING, _("Pending")),
        (VALID, _("Valid")),
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)

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


class SalesQuotation(
    PolymorphicModel,
    NumeratorMixin,
    SalesQuotationActionMixin,
    ParanoidMixin,
):

    user = models.ForeignKey(
        get_user_model(),
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="quotations",
        verbose_name=_("User"),
    )

    # Reference & Meta Fields
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="salesquotations",
        verbose_name=_("Group"),
    )
    expired_at = models.DateTimeField(
        default=quotation_expired_limit,
        null=True,
        blank=True,
    )

    customer_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="salesorder_customers",
        verbose_name=_("Customer Type"),
    )
    customer_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Customer ID"),
    )
    customer = GenericForeignKey("customer_type", "customer_id")

    discount = models.DecimalField(
        default=0,
        max_digits=15,
        decimal_places=2,
        verbose_name=_("Discount"),
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
    note = models.TextField(
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

    addresses = GenericRelation(
        BillingAddress,
        content_type_field="content_type",
        object_id_field="content_id",
    )

    qrcodes = GenericRelation(
        LinkedQRCode,
        content_type_field="linked_object_type",
        object_id_field="linked_object_id",
    )

    allow_comments = models.BooleanField(default=True)

    doc_prefix = "SQ"
    objects = QuotationManager()
    reset_mode = NumeratorReset.MONTHLY

    class Meta:
        db_table = "simpel_sales_quotation"
        verbose_name = _("Sales Quotation")
        verbose_name_plural = _("Sales Quotations")
        index_together = (
            "user",
            "group",
            "customer_type",
            "customer_id",
            "status",
        )
        permissions = (
            ("import_salesquotation", _("Can import Sales Quotation")),
            ("export_salesquotation", _("Can export Sales Quotation")),
            ("validate_salesquotation", _("Can validate Sales Quotation")),
            ("process_salesquotation", _("Can process Sales Quotation")),
            ("accept_salesquotation", _("Can accept Sales Quotation")),
        )

    def __str__(self):
        return "%s - %s" % (str(self.inner_id), self.customer)

    @cached_property
    def opts(self):
        return self.__class__._meta

    @cached_property
    def admin_url(self):
        view_name = "admin:simpel_sales_salesquotation_inspect"
        return reverse(view_name, args=(self.id,), host="admin")

    def get_absolute_url(self):
        return reverse(sales_settings.QUOTATION_ABSOLUTE_URL_NAME, kwargs={"pk": self.pk})

    @cached_property
    def qrcode(self):
        return self.qrcodes.first()

    @cached_property
    def items_count(self):
        return self.get_items_count()

    @cached_property
    def total_items(self):
        return self.get_total_items()

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

    def compute(self):
        self.total = self.get_total_items()
        self.grand_total = self.get_grand_total()

    def delete(self, *args, **kwargs):
        if self.qrcodes is not None:
            self.qrcodes.all().delete()
        if self.addresses.count():
            self.addresses.all().delete()
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.compute()
        return super().save(*args, **kwargs)


class SalesQuotationItem(NumeratorMixin, ParanoidMixin):
    # Reference & Meta Fields
    salesquotation = models.ForeignKey(
        SalesQuotation,
        related_name="items",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name="quotation_items",
        limit_choices_to={"is_sellable": True},
        null=False,
        blank=False,
        on_delete=models.PROTECT,
    )
    position = models.IntegerField(
        default=0,
        verbose_name=_("position"),
        help_text=_("Enable sortable position"),
    )
    name = models.CharField(
        verbose_name=_("name"),
        max_length=255,
        null=True,
        blank=True,
        editable=False,
        db_index=True,
    )
    alias_name = models.CharField(
        verbose_name=_("alias name"),
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Quantity"),
        validators=[
            MinValueValidator(1, message=_("Minimal value: 1")),
            MaxValueValidator(500, message=_("Maximal value: 500")),
        ],
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

    deliverable_informations = GenericRelation(
        DeliverableAddress,
        content_type_field="content_type",
        object_id_field="content_id",
    )

    doc_prefix = "QUI"
    reset_mode = NumeratorReset.MONTHLY

    class Meta:
        db_table = "simpel_sales_quotation_item"
        ordering = ("position",)
        index_together = ("salesquotation", "product")
        verbose_name = _("Quotation Item")
        verbose_name_plural = _("Quotations Items")
        permissions = (
            ("import_salesquotationitem", _("Can import Sales Quotation Item")),
            ("export_salesquotationitem", _("Can export Sales Quotation Item")),
        )

    def format_inner_id(self):
        """Inner ID final format"""
        form = [self.get_doc_prefix(), self.format_date(form="%m%y"), self.format_number()]
        inner_id = "{}.{}.{}".format(*form)
        return setattr(self, self.inner_id_field, inner_id)

    def __str__(self):
        return "#%s:%s - %s" % (self.inner_id, self.salesquotation.inner_id, self.name)

    @cached_property
    def opts(self):
        return self.__class__._meta

    @cached_property
    def deliverable_information(self):
        return self.deliverable_informations.first()

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


class SalesQuotationItemBundle(NumeratorMixin, ParanoidMixin):
    # Reference & Meta Fields
    position = models.IntegerField(
        default=0,
        verbose_name=_("position"),
        help_text=_("Enable sortable position"),
    )
    item = models.ForeignKey(
        SalesQuotationItem,
        related_name="bundles",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name="quotation_item_bundles",
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

    doc_prefix = "SQI"
    reset_mode = NumeratorReset.MONTHLY

    class Meta:
        db_table = "simpel_sales_quotation_item_bundle"
        ordering = ("position", "reg_number")
        index_together = ("item", "product")
        unique_together = ("item", "product")
        verbose_name = _("Quotation Item Bundle")
        verbose_name_plural = _("Quotation Item Bundles")
        permissions = (
            ("import_salesquotationitembundle", _("Can import Sales Quotation Item Bundle")),
            ("export_salesquotationitembundle", _("Can export Sales Quotation Item Bundle")),
        )

    def __str__(self):
        return "%s" % self.name

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
