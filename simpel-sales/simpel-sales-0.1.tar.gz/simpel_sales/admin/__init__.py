from django.contrib import admin

from ..models import Invoice, Proforma, SalesOrder, SalesQuotation
from ..settings import sales_settings
from .invoices import *  # NOQA
from .order import *  # NOQA
from .proforma import *  # NOQA
from .quotation import *  # NOQA

admin.site.register(Invoice, sales_settings.INVOICE_ADMIN)
admin.site.register(SalesOrder, sales_settings.ORDER_ADMIN)
admin.site.register(SalesQuotation, sales_settings.QUOTATION_ADMIN)
admin.site.register(Proforma, sales_settings.PROFORMA_ADMIN)
