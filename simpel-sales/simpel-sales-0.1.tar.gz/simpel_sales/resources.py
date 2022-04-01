from django.contrib.contenttypes.models import ContentType
from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.widgets import DateWidget, ForeignKeyWidget
from simpel_products.models import Group

from .models import Invoice, SalesOrder, SalesQuotation

SO_FIELDS = (
    "id",
    "created_at",
    "user",
    "group",
    "customer_type",
    "customer_id",
    "customer",
    "reference",
    "discount",
    "expired_at",
    "note",
    "total",
    "grand_total",
    "downpayment",
    "payable",
    "data_sampling",
    "data_sampling_schedule",
    "data_sampling_estimation",
    "date_validated",
    "date_processed",
    "date_completed",
    "date_closed",
    "data",
)


class DataFieldMixin:
    def get_data(self, invoice, key, default="unknown"):
        data = getattr(invoice, "data")
        if data is not None:
            return data.get(key)
        return "unknown"

    def dehydrate_data_sampling(self, invoice):
        data = self.get_data(invoice, "sampling_options")
        return data or "unknown"

    def dehydrate_data_sampling_schedule(self, invoice):
        data = self.get_data(invoice, "sampling_schedule")
        return "%s" % data

    def dehydrate_data_sampling_estimation(self, invoice):
        data = self.get_data(invoice, "sampling_estimation")
        return "%s" % data


class SalesOrderResource(DataFieldMixin, ModelResource):
    customer = Field()
    group = Field(
        attribute="group",
        column_name="group",
        widget=ForeignKeyWidget(Group, field="code"),
    )
    customer_type = Field(
        attribute="customer_type",
        column_name="customer_type",
        widget=ForeignKeyWidget(ContentType, field="model"),
    )
    data_sampling = Field()
    data_sampling_schedule = Field(widget=DateWidget())
    data_sampling_estimation = Field()

    class Meta:
        model = SalesOrder
        fields = SO_FIELDS
        export_order = SO_FIELDS
        import_id_fields = ("inner_id",)

    def dehydrate_customer(self, invoice):
        customer = getattr(invoice, "customer", "unknown")
        return "%s" % customer


SQ_FIELDS = (
    "inner_id",
    "group",
    "customer",
    "created_at",
    "expired_at",
    "total",
    "grand_total",
)


class SalesQuotationResource(ModelResource):
    customer = Field()
    group = Field(
        attribute="group",
        column_name="group",
        widget=ForeignKeyWidget(Group, field="code"),
    )
    customer_type = Field(
        attribute="customer_type",
        column_name="customer_type",
        widget=ForeignKeyWidget(ContentType, field="model"),
    )

    class Meta:
        model = SalesQuotation
        fields = SQ_FIELDS
        export_order = SQ_FIELDS
        import_id_fields = ("inner_id",)

    def dehydrate_customer(self, invoice):
        customer = getattr(invoice, "customer", "unknown")
        return "%s" % customer


INV_FIELDS = [
    "id",
    "group",
    "created_at",
    "issued_date",
    "due_date",
    "reg_number",
    "inner_id",
    "customer_type",
    "customer_id",
    "customer",
    "reference_type",
    "reference_id",
    "status",
    "items_count",
    "total",
    "discount",
    "downpayment",
    "grand_total",
    "paid",
    "payable",
    "refund",
    "data",
]


class InvoiceResource(ModelResource):
    customer = Field()
    customer_type = Field(
        attribute="customer_type",
        column_name="customer_type",
        widget=ForeignKeyWidget(ContentType, field="model"),
    )
    group = Field(
        attribute="group",
        column_name="group",
        widget=ForeignKeyWidget(Group, field="code"),
    )

    class Meta:
        model = Invoice
        fields = INV_FIELDS
        export_order = INV_FIELDS
        import_id_fields = ("id",)

    def dehydrate_customer(self, invoice):
        customer = getattr(invoice, "customer", "unknown")
        return "%s" % customer
