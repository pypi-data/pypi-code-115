from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from .handlers import ActionHandler


class ActionableAdminMixin(admin.ModelAdmin):

    action_handler_class = ActionHandler

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        if self.action_handler_class is None:
            raise ImproperlyConfigured("%s missing action_handler_class!" % self.__class__.__name__)

    def get_action_redirect_url(self):
        return reverse(admin_urlname(self.opts, "changelist"))

    def perfom_action(self, action, request, queryset):
        try:
            for instance in queryset:
                self.action_handler.perform(action, instance, request)
            msg = "Successfully %s %s %s" % ("validate", queryset.count(), self.opts.verbose_name)
            self.message_user(request, msg, level="success")
        except Exception as err:
            self.message_user(request, err, level="error")
