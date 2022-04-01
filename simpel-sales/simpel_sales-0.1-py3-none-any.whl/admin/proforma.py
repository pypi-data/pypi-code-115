from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from simpel_admin.base import AdminPrintViewMixin, ModelAdminMixin


class ProformaAdmin(AdminPrintViewMixin, ModelAdminMixin):
    date_hierarchy = "created_at"
    list_display = ["inner_id", "salesorder", "col_group", "created_at"]
    list_filter = ["salesorder__group"]

    @admin.display(description=_("Group"))
    def col_group(self, obj):
        return obj.salesorder.group
