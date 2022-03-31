from django.apps import AppConfig
from django.utils.translation import gettext_lazy


class PluginApp(AppConfig):
    name = 'pretix_saferpay'
    verbose_name = 'Saferpay (SIX) implementation for pretix'

    class PretixPluginMeta:
        name = gettext_lazy('Saferpay (SIX)')
        author = 'Raphael Michel'
        category = 'PAYMENT'
        description = gettext_lazy('Accept payments through Saferpay, a payment method offered by Worldline (formerly SIX Payment Services).')
        visible = True
        picture = "pretix_saferpay/logo.svg"
        version = '1.3.1'

    def ready(self):
        from . import signals, tasks  # NOQA


default_app_config = 'pretix_saferpay.PluginApp'
