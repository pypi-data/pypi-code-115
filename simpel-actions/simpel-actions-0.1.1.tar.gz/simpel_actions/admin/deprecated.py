from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry
from django.contrib.admin.options import get_content_type_for_model
from django.contrib.admin.utils import unquote
from django.db import transaction
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from actstream.models import any_stream
from simpel_admin.base import BaseModelAdmin


class AdminActivityMixin(BaseModelAdmin):
    def get_history_template(self):
        return self.object_history_template or [
            "admin/%s/%s/history.html" % (self.opts.app_label, self.opts.model_name),
            "admin/%s/%s_history.html" % (self.opts.app_label, self.opts.model_name),
            "admin/%s/object_history.html" % self.opts.app_label,
            "admin/object_history.html",
        ]

    def get_history_context(self, **kwargs):
        action_list = LogEntry.objects.filter(
            object_id=self.object.id,
            content_type=get_content_type_for_model(self.model)
        ).select_related().order_by('action_time')
        activity_list = any_stream(self.object).order_by("-timestamp")
        kwargs.update(
            {
                "opts": self.opts,
                "object": self.object,
                "title": self.get_inspect_title(self.object),
                "subtitle": None,
                "action_list": action_list,
                "activity_list": activity_list,
                "module_name": str(capfirst(self.opts.verbose_name_plural)),
                "preserved_filters": self.get_preserved_filters(self.request),
                "available_apps": admin.site.get_app_list(self.request),
                "has_change_permission": self.has_change_permission(self.request, self.object),
                "has_add_permission": self.has_add_permission(self.request),
                "has_delete_permission": self.has_delete_permission(self.request, self.object),
                "has_view_permission": self.has_view_permission(self.request, self.object),
                **self.admin_site.each_context(self.request),
            }
        )
        has_print_permission = getattr(self, "has_print_permission", None)
        if has_print_permission:
            kwargs["has_print_permission"] = has_print_permission(self.request, self.object)
        return kwargs

    def history_view(self, request, object_id, extra_context=dict()):
        """The 'history' admin view for this model. replaced by activity log"""
        # First check if the user can see this history.
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(request, self.opts, object_id)

        self.request = request
        self.object = obj
        self.opts = self.model._meta

        if not self.has_view_or_change_permission(request, obj):
            messages.warning(request, _("You don't have permission to view %s history.") % obj)
            return redirect(self.get_changelist_url())

        # Then get the history for this object.
        context = self.get_history_context(**extra_context)
        request.current_app = self.admin_site.name
        return TemplateResponse(request, self.get_history_template(), context)

    def has_trash_permission(self, request, obj=None):
        return self.has_action_permission(request, "trash")

    def has_validate_permission(self, request, obj=None):
        return self.has_action_permission(request, "validate")

    def has_cancel_permission(self, request, obj=None):
        return self.has_action_permission(request, "cancel")

    def has_pay_permission(self, request, obj=None):
        return self.has_action_permission(request, "pay")

    def has_approve_permission(self, request, obj=None):
        return self.has_action_permission(request, "approve")

    def has_reject_permission(self, request, obj=None):
        return self.has_action_permission(request, "reject")

    def has_process_permission(self, request, obj=None):
        return self.has_action_permission(request, "process")

    def has_complete_permission(self, request, obj=None):
        return self.has_action_permission(request, "complete")

    def has_close_permission(self, request, obj=None):
        return self.has_action_permission(request, "close")

    def action_view(self, request, object_id, action=None, extra_context=None):
        # get objects
        if isinstance(object_id, self.model):
            obj = object_id
        else:
            obj = self.get_object(request, object_id)

        # Ignore action if status is not valid
        ignore_condition = getattr(obj, "%s_ignore_condition" % action)
        if ignore_condition:
            messages.warning(request, _("%s %s ignored.") % (action.title(), obj))
            return redirect(self.get_changelist_url())

        # Check action permission
        permission = getattr(self, "has_%s_permission" % action)
        if not permission(request, obj):
            messages.warning(request, _("You don't have %s permission.") % action)
            return redirect(self.get_changelist_url())

        # Perform action
        if request.method == "POST":
            try:
                with transaction.atomic():
                    object_action = getattr(obj, action)
                    object_action(request)
                messages.success(request, _("%s %s.") % (obj, action))
            except PermissionError as err:
                messages.error(request, err)
            return redirect(self.get_changelist_url())
        else:
            extra_context.update(
                {
                    "title": _("%s %s confirmation.") % (action.title(), self.opts.verbose_name, obj),
                    "object": obj,
                    "cancel_url": self.get_inspect_url(obj.id),
                }
            )
            return self.confirmation_view(request, extra_context=extra_context)

    @admin.action(
        permissions=["validate"],
        description=_("Validate selected %(verbose_name_plural)s"),
    )
    def validate_action(self, request, queryset):
        if queryset.count() != 1:
            err = _("Please select only one record.")
            messages.error(request, err)
            return
        obj = queryset.first()
        return self.action_view(request, obj, action="validate")

    @admin.action(
        permissions=["cancel"],
        description=_("Cancel selected %(verbose_name_plural)s"),
    )
    def cancel_action(self, request, queryset):
        if queryset.count() != 1:
            err = _("Please select only one record.")
            messages.error(request, err)
            return
        obj = queryset.first()
        return self.action_view(request, obj, action="cancel")

    @admin.action(
        permissions=["trash"],
        description=_("Trash selected %(verbose_name_plural)s"),
    )
    def trash_action(self, request, queryset):
        if queryset.count() != 1:
            err = _("Please select only one record.")
            messages.error(request, err)
            return
        obj = queryset.first()
        return self.action_view(request, obj, action="trash")

    @admin.action(
        permissions=["pay"],
        description=_("Pay selected %(verbose_name_plural)s"),
    )
    def pay_action(self, request, queryset):
        if queryset.count() != 1:
            err = _("Please select only one record.")
            messages.error(request, err)
            return
        obj = queryset.first()
        return self.action_view(request, obj, action="pay")

    @admin.action(
        permissions=["approve"],
        description=_("Approve selected %(verbose_name_plural)s"),
    )
    def approve_action(self, request, queryset):
        if queryset.count() != 1:
            err = _("Please select only one record.")
            messages.error(request, err)
            return
        obj = queryset.first()
        return self.action_view(request, obj, action="approve")

    @admin.action(
        permissions=["reject"],
        description=_("Reject selected %(verbose_name_plural)s"),
    )
    def reject_action(self, request, queryset):
        if queryset.count() != 1:
            err = _("Please select only one record.")
            messages.error(request, err)
            return
        obj = queryset.first()
        return self.action_view(request, obj, action="reject")

    @admin.action(
        permissions=["process"],
        description=_("Process selected %(verbose_name_plural)s"),
    )
    def process_action(self, request, queryset):
        if queryset.count() != 1:
            err = _("Please select only one record.")
            messages.error(request, err)
            return
        obj = queryset.first()
        return self.action_view(request, obj, action="process")

    @admin.action(
        permissions=["complete"],
        description=_("Complete selected %(verbose_name_plural)s"),
    )
    def complete_action(self, request, queryset):
        if queryset.count() != 1:
            err = _("Please select only one record.")
            messages.error(request, err)
            return
        obj = queryset.first()
        return self.action_view(request, obj, action="complete")

    @admin.action(
        permissions=["close"],
        description=_("Close selected %(verbose_name_plural)s"),
    )
    def close_action(self, request, queryset):
        if queryset.count() != 1:
            err = _("Please select only one record.")
            messages.error(request, err)
            return
        obj = queryset.first()
        return self.action_view(request, obj, action="close")
