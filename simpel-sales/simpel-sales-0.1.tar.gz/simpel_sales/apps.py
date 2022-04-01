from django.apps import AppConfig
from django.db.models.signals import post_migrate


class SimpelSalesConfig(AppConfig):
    icon = "handshake-outline"
    default_auto_field = "django.db.models.BigAutoField"
    name = "simpel_sales"
    label = "simpel_sales"
    verbose_name = "Sales"

    def ready(self):

        from actstream import registry

        from simpel_sales import signals  # NOQA

        registry.register(self.get_model("SalesOrder"))
        registry.register(self.get_model("SalesQuotation"))
        registry.register(self.get_model("Invoice"))
        registry.register(self.get_model("Proforma"))
        post_migrate.connect(init_app, sender=self)
        return super().ready()


def init_app(**kwargs):
    pass
