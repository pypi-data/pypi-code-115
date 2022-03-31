from django.contrib.auth import get_permission_codename
from django.utils.translation import gettext_lazy as _

from actstream import action



class ActionDoesNotExist(Exception):
    pass


class ActionHandler(object):

    action_logger_class = None

    def perform(self, action, instance, request=None, action_function=None):
        if action_function is None:
            try:
                action_function = getattr(self, "do_%s" % action)
            except Exception:
                raise ActionDoesNotExist(
                    _("%s doesn't have do_%s handler!") % (self.__class__.__name__, action),
                )
        return action_function(request, instance)

    def log(self, *args, **kwargs):
        """
        Log that an object action, override this action if using job queee.
        """
        action.send(**kwargs)

    def has_object_permission(self, request, code, obj=None):
        opts = obj.__class__._meta
        codename = get_permission_codename(code, opts)
        return request.user.has_perm("%s.%s" % (opts.app_label, codename))

    def has_action_permission(self, request, action, obj=None):
        perm_func = getattr(self, "has_%s_permission" % action, None)
        if perm_func is None:
            perm_func = self.has_object_permission
        return perm_func(request, action, obj)
