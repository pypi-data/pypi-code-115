import nested_admin
from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.admin.widgets import AdminTextareaWidget
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportMixin
from simpel_actions.admin import AdminActivityMixin
from simpel_admin.base import AdminPrintViewMixin, ModelAdminMixin
from simpel_contacts.admin import NestedBillingAddressInline

from ..models import SalesQuotationItem, SalesQuotationItemBundle, SalesQuotationSetting
from ..settings import sales_settings


class SalesQuotationItemBundleInline(
    nested_admin.SortableHiddenMixin,
    nested_admin.NestedTabularInline,
):
    model = SalesQuotationItemBundle
    extra = 0
    autocomplete_fields = ["product"]

    def has_change_permission(self, request, obj=None):
        return False


class SalesQuotationItemInline(
    nested_admin.SortableHiddenMixin,
    nested_admin.NestedStackedInline,
):
    model = SalesQuotationItem
    widgets = {"note": AdminTextareaWidget(attrs={"cols": 3})}
    inlines = [SalesQuotationItemBundleInline]
    extra = 0
    autocomplete_fields = ["product"]


class SalesQuotationAdmin(
    ExportMixin,
    AdminPrintViewMixin,
    AdminActivityMixin,
    ModelAdminMixin,
    nested_admin.NestedModelAdmin,
):
    form = sales_settings.QUOTATION_FORM
    handler_class = sales_settings.QUOTATION_HANDLER
    resource_class = sales_settings.QUOTATION_RESOURCE
    inlines = [NestedBillingAddressInline, SalesQuotationItemInline]
    list_filter = ["group", "status"]
    # autocomplete_fields = ["customer"]
    search_fields = ["inner_id", "name"]
    date_hierarchy = "created_at"
    list_display_links = None
    list_display = ["object_detail", "status", "object_buttons"]
    actions = ["compute_action", "validate_action"]

    @admin.action(description=_("Recalculate selected Sales Quotation"))
    def compute_action(self, request, queryset):
        for obj in queryset:
            obj.save()

    @admin.display(description=_("Detail"))
    def object_detail(self, obj):
        context = {"object": obj}
        template = "admin/simpel_sales/order_line.html"
        return render_to_string(template, context=context)

    def get_handler(self):
        return self.handler_class()

    def get_inlines(self, request, obj=None):
        return super().get_inlines(request, obj)

    def has_change_permission(self, request, obj=None):
        default = super().has_change_permission(request, obj)
        if obj:
            return obj.is_editable and default
        else:
            return default

    def has_clone_permission(self, request, obj=None):
        default = super().has_add_permission(request)
        if obj:
            return obj.validate_ignore_condition and default
        else:
            return default

    def has_convert_permission(self, request, obj=None):
        default = request.user.has_perm("simpel_sales.add_salesorder")
        if obj:
            return obj.validate_ignore_condition and default
        else:
            return default

    def changelist_view(self, request, extra_context=None):
        self.request = request
        return super().changelist_view(request, extra_context)

    def clone_view(self, request, pk, extra_context=None):
        obj = get_object_or_404(self.model, pk=pk)
        handler = self.get_handler()
        if not obj.validate_ignore_condition:
            messages.error(request, _("Make sure Sales Quotation status is valid!"))
            return redirect(self.get_inspect_url(obj.id))

        if not self.has_clone_permission(request, obj):
            messages.error(request, _("You don't have permission to clone this quotation!"))
            return redirect(self.get_inspect_url(obj.id))

        if request.method == "POST":
            try:
                cloned = handler.clone(request, obj)
                msg = _("%s cloned to %s.") % (obj, cloned)
                messages.success(request, msg)
                return redirect(self.get_inspect_url(cloned.id))
            except PermissionError as err:
                messages.error(request, err)
            return redirect(self.get_inspect_url(obj.id))
        else:
            context = {
                "title": _("Confirm clone %s %s.") % (self.opts.verbose_name, obj),
                "object": obj,
                "cancel_url": self.get_inspect_url(obj.id),
            }
            return self.confirmation_view(request, extra_context=context)

    def convert_view(self, request, pk, extra_context=None):
        obj = self.get_object(request, pk)
        handler = self.get_handler()
        if not obj.validate_ignore_condition:
            messages.error(request, _("Make sure Sales Quotation status is valid!"))
            return redirect(self.get_inspect_url(obj.id))

        if not self.has_convert_permission(request, obj):
            messages.error(request, _("You don't have permission to convert this quotation!"))
            return redirect(self.get_inspect_url(obj.id))

        if request.method == "POST":
            try:
                salesorder = handler.convert(request, obj)
                msg = _("%s convert to %s.") % (obj, salesorder)
                messages.success(request, msg)
                return redirect(reverse(admin_urlname(salesorder._meta, "inspect"), args=(salesorder.id,)))
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

    def get_print_template(self):
        """Return print template from simpel_settings"""
        quo_settings = SalesQuotationSetting.for_request(self.request)
        template_item = quo_settings.salesquotation_template
        if template_item is not None:
            return template_item.get_template()
        else:
            return super().get_print_template()

    def get_urls(self):
        urls = [
            path(
                "<int:pk>/clone/",
                self.admin_site.admin_view(self.clone_view),
                name="%s_%s_clone" % (self.opts.app_label, self.opts.model_name),
            ),
            path(
                "<int:pk>/convert/",
                self.admin_site.admin_view(self.convert_view),
                name="%s_%s_convert" % (self.opts.app_label, self.opts.model_name),
            ),
        ] + super().get_urls()
        return urls
