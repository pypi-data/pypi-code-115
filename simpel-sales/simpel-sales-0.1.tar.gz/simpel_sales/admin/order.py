import nested_admin
from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin
from simpel_actions.admin import AdminActivityMixin
from simpel_admin.base import AdminPrintViewMixin, ModelAdminMixin
from simpel_contacts.admin import (
    NestedBillingAddressInline,
    NestedDeliverableAddressInline,
    NestedShippingAddressInline,
)

from ..models import SalesOrderItem, SalesOrderItemBundle, SalesOrderSetting
from ..settings import sales_settings


class SalesOrderItemBundleInline(
    nested_admin.SortableHiddenMixin,
    nested_admin.NestedTabularInline,
):
    model = SalesOrderItemBundle
    extra = 0
    autocomplete_fields = ["product"]
    readonly_fields = ["price", "total"]


class SalesOrderItemInline(
    nested_admin.SortableHiddenMixin,
    nested_admin.NestedStackedInline,
):
    model = SalesOrderItem
    inlines = [NestedDeliverableAddressInline, SalesOrderItemBundleInline]
    extra = 0
    autocomplete_fields = ["product"]
    readonly_fields = ["price", "total"]


class SalesOrderAdmin(
    ExportMixin,
    AdminPrintViewMixin,
    AdminActivityMixin,
    ModelAdminMixin,
    nested_admin.NestedModelAdmin,
):
    form = sales_settings.ORDER_FORM
    handler_class = sales_settings.ORDER_HANDLER
    resource_class = sales_settings.ORDER_RESOURCE
    inlines = [NestedBillingAddressInline, NestedShippingAddressInline, SalesOrderItemInline]
    # autocomplete_fields = ["customer"]
    date_hierarchy = "created_at"
    search_fields = ["inner_id", "customer__name"]
    list_filter = ["group", "status"]
    list_display_links = None
    list_display = ["object_detail", "status", "group", "object_buttons"]
    actions = [
        "compute_action",
        "validate_action",
        "cancel_action",
        "process_action",
        "complete_action",
        "close_action",
    ]

    def get_handler(self):
        return self.handler_class()

    @admin.display(description=_("Detail"))
    def object_detail(self, obj):
        context = {"object": obj}
        template = "admin/simpel_sales/order_line.html"
        return render_to_string(template, context=context)

    @admin.action(description=_("Recalculate selected Sales Order"))
    def compute_action(self, request, queryset):
        for obj in queryset:
            obj.save()

    def get_form(self, request, obj=None, change=False, **kwargs):
        return super().get_form(request, obj, change, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            if request.user.is_superuser:
                self.readonly_fields = []
            else:
                self.readonly_fields = ["status", "group"]
        else:
            self.readonly_fields = ["status"]
        return super().get_readonly_fields(request, obj)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    def has_print_permission(self, request, obj=None):
        return obj.is_printable

    def get_print_template(self):
        db_settings = SalesOrderSetting.for_request(self.request)
        template_item = db_settings.salesorder_template
        if template_item is not None:
            return template_item.get_template()
        else:
            return super().get_print_template()

    def has_change_permission(self, request, obj=None):
        default = super().has_change_permission(request, obj)
        if obj:
            return obj.is_editable and default
        else:
            return default

    def has_create_workorder_permission(self, request, obj):
        default = request.user.has_perm("simpel_projects.add_workorder")
        if obj:
            return obj.is_valid and not obj.has_workorder
        else:
            return default

    def has_create_invoice_permission(self, request, obj=None):
        default = request.user.has_perm("simpel_sales.add_invoice")
        if obj:
            return (obj.is_processed or obj.is_complete) and not obj.is_invoiced and default
        else:
            return default

    def inspect_view(self, request, pk, **kwargs):
        obj = self.get_object(request, pk)
        kwargs.update(
            {
                "has_create_invoice_permission": self.has_create_invoice_permission(request, obj),
                "has_create_workorder_permission": self.has_create_workorder_permission(request, obj),
                "has_print_permission": self.has_print_permission(request, obj),
            }
        )
        return super().inspect_view(request, pk, **kwargs)

    def clone_view(self, request, pk, extra_context=None):
        obj = get_object_or_404(self.model, pk=pk)
        handler = self.get_handler()

        if request.method == "POST":
            try:
                cloned = handler.clone(request, obj)
                msg = _("%s cloned to %s.") % (obj, cloned)
                messages.success(request, msg)
                return redirect(reverse(admin_urlname(self.model._meta, "inspect"), args=(cloned.id,)))
            except Exception as err:
                messages.error(request, err)
            return redirect(self.get_inspect_url(obj.id))
        else:
            context = {
                "title": _("Confirm clone %s %s.") % (self.opts.verbose_name, obj),
                "object": obj,
                "cancel_url": self.get_inspect_url(obj.id),
            }
            return self.confirmation_view(request, extra_context=context)

    def create_invoice_view(self, request, pk):
        obj = get_object_or_404(self.model, pk=pk)
        handler = self.get_handler()

        if not self.has_create_invoice_permission(request, obj):
            messages.error(request, _("Make sure Sales Order status is complete or processed!"))
            return redirect(self.get_inspect_url(obj.id))

        if obj.is_invoiced:
            messages.error(request, _("Invoice for %s has been created!") % obj)
            return redirect(self.get_inspect_url(obj.id))

        if request.method == "POST":
            try:
                # Call SalesOrderHandler.convert
                invoice = handler.convert(request, obj)
                msg = _("Create invoice %s for order %s.") % (invoice, obj)
                messages.success(request, msg)
                return redirect(reverse(admin_urlname(invoice._meta, "inspect"), args=(invoice.id,)))
            except Exception as err:
                messages.error(request, err)
                return redirect(self.get_inspect_url(obj.id))
        else:
            context = {
                "title": _("Create invoice for %s %s.") % (self.opts.verbose_name, obj),
                "object": obj,
                "cancel_url": self.get_inspect_url(obj.id),
            }
            return self.confirmation_view(request, extra_context=context)

    def get_urls(self):
        urls = [
            path(
                "<int:pk>/clone/",
                self.admin_site.admin_view(self.clone_view),
                name="%s_%s_clone" % (self.opts.app_label, self.opts.model_name),
            ),
            path(
                "<int:pk>/create_invoice/",
                self.admin_site.admin_view(self.create_invoice_view),
                name="%s_%s_create_invoice" % (self.opts.app_label, self.opts.model_name),
            ),
        ] + super().get_urls()
        return urls


class SalesOrderItemAdmin(admin.ModelAdmin):
    inlines = [SalesOrderItemBundleInline]
    search_fields = ["inner_id", "salesorder__inner_id"]
    list_display = [
        "inner_id",
        "salesorder",
        "product",
        "quantity",
    ]
