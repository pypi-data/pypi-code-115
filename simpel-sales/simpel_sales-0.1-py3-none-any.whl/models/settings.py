from django.db import models
from django.utils.translation import gettext_lazy as _
from simpel_settings.models import BaseSetting
from simpel_settings.registries import register_setting
from simpel_themes.models import PathModelTemplate

__all__ = ["SalesOrderSetting", "SalesQuotationSetting"]


@register_setting
class SalesOrderSetting(BaseSetting):

    salesorder_template = models.ForeignKey(
        PathModelTemplate,
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.SET_NULL,
        verbose_name=_("Order Template"),
        help_text=_("Custom Order template."),
    )
    salesorder_expiration = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Order Expiration"),
    )
    salesorder_signer_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Order Signer"),
    )
    salesorder_signer_position = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Order Signer Position"),
    )
    salesorder_signer_eid = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Order Signer EID"),
    )


@register_setting
class SalesQuotationSetting(BaseSetting):
    salesquotation_template = models.ForeignKey(
        PathModelTemplate,
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.SET_NULL,
        verbose_name=_("Quotation Template"),
        help_text=_("Custom Quotation template."),
    )
    salesquotation_expiration = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Quotation Expiration"),
    )
    salesquotation_signer_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Quotation Signer"),
    )
    salesquotation_signer_position = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Quotation Signer Position"),
    )
    salesquotation_signer_eid = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Quotation Signer EID"),
    )


@register_setting
class InvoiceSetting(BaseSetting):
    invoice_expiration = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Invoice Expiration"),
    )
