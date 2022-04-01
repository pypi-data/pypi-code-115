from actstream import action
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from simpel_contacts.models import (
    AbstractTypedAddress,
    BillingAddress,
    DeliverableAddress,
    ShippingAddress,
)

from . import models
from .settings import sales_settings
from .signals import post_checkout, post_clone, post_convert


def get_allowed_product_groups(group_code):
    group_map = {
        "LAB": [group_code, "PRM", "FEE"],
        "LIT": [group_code, "PRM", "FEE"],
        "KAL": [group_code, "FEE"],
        "KSL": [group_code, "FEE"],
        "PRO": [group_code, "FEE"],
        "LIB": [group_code, "FEE"],
        "SRV": [group_code, "FEE"],
    }
    try:
        return group_map[group_code]
    except KeyError:
        return []


def salesorder_pending_validation(customer, order_group=None):
    # Check for pending order by product contenttype
    filter = {"status": models.SalesOrder.PENDING}
    if order_group:
        filter["code"] = order_group
    pending_orders = customer.sales_orders.filter(**filter)
    pending_count = pending_orders.count()
    pending_limit = sales_settings.SALES["MAX_PENDING_ORDERS_PER_SERVICE"]
    if pending_count >= pending_limit:
        raise ValidationError(_("Maximum order %(max)s reached"), params={"max": pending_limit})


class BaseHandler(object):
    order_class = None
    order_item_class = None
    order_item_bundle_class = None

    def _create_order(self, user, data):
        """Create an order"""
        order = self.order_class(user=user, **data)
        order.save()
        return order

    def _create_item(self, order, item):
        newitem = self.order_item_class(
            **{
                self.order_class._meta.model_name: order,
                "name": item.product.name,
                "alias_name": item.name,
                "product": item.product,
                "quantity": item.quantity,
            }
        )
        newitem.save()
        return newitem

    def _create_item_bundle(self, item, bundle):
        item_bundle = self.order_item_bundle_class(
            item=item,
            name=bundle.product.name,
            product=bundle.product,
            quantity=bundle.quantity,
        )
        item_bundle.save()
        return item_bundle

    def _create_billing_address(self, obj, address):
        new_address = BillingAddress(content=obj)
        for key, item in address.to_dict().items():
            setattr(new_address, key, item)
        new_address.save()
        return new_address

    def _create_shipping_address(self, obj, address):
        new_address = ShippingAddress(content=obj)
        for key, item in address.to_dict().items():
            setattr(new_address, key, item)
        new_address.save()
        return new_address

    def _create_deliverable_address(self, obj, address):
        new_address = DeliverableAddress(content=obj)
        for key, item in address.to_dict().items():
            setattr(new_address, key, item)
        new_address.save()
        return new_address

    def _create(self, user, data, items, billing=None, shipping=None, delete_item=False, from_cart=False):
        with transaction.atomic():
            order = self._create_order(user, data=data)

            # Prepare billing address
            if billing is None:
                billing = order.customer.get_address(AbstractTypedAddress.BILLING)
            if shipping is None:
                shipping = order.customer.get_address(AbstractTypedAddress.SHIPPING) or billing
            if billing:
                self._create_billing_address(order, billing)
            if shipping:
                self._create_shipping_address(order, shipping)

            # Add items
            for item in items:
                orderitem = self._create_item(order, item)
                bundle_ids = []
                bundled_products = getattr(item.product.specific, "bundle_items", None)
                if bundled_products:
                    for bundle in bundled_products.all():
                        self._create_item_bundle(orderitem, bundle)
                        bundle_ids.append(bundle.product.id)

                req_recommends = item.product.recommended_items.filter(required=True)
                for req_recommend in req_recommends:
                    if req_recommend.product.id not in bundle_ids:
                        self._create_item_bundle(orderitem, req_recommend)
                        bundle_ids.append(req_recommend.product.id)

                if from_cart:
                    for cart_bundle in item.bundles.all():
                        if cart_bundle.product.id not in bundle_ids:
                            self._create_item_bundle(orderitem, cart_bundle)
                            bundle_ids.append(cart_bundle.product.id)

                # Attach deliverable information
                del_info = getattr(item, "deliverable_information", None)
                if item.product.is_deliverable and del_info is not None:
                    new_del_info = self._create_deliverable_address(orderitem, del_info)
                    new_del_info.save()

                if delete_item:
                    item.delete()
                orderitem.save()
            order.save()
            return order

    def _clone(self, user, data, obj):
        with transaction.atomic():
            order = self._create_order(user, data)
            # Prepare billing address
            billing = getattr(obj, "billing_address", None)
            shipping = getattr(obj, "shipping_address", None)
            if billing:
                self._create_billing_address(order, billing)
            if shipping:
                self._create_shipping_address(order, shipping)
            # clone order items
            for item in obj.items.all():
                new_item = self._create_item(order, item)
                # clone item bundle
                for bundle in item.bundles.all():
                    bundle = self._create_item_bundle(new_item, bundle)
                    # Attach deliverable information
                del_info = getattr(item, "deliverable_information", None)
                if item.product.is_deliverable and del_info is not None:
                    new_del_info = self.create_deliverable_address(new_item, del_info)
                    new_del_info.save()

                new_item.save()
            order.save()
            return order


class SalesOrderHandler(BaseHandler):
    order_class = models.SalesOrder
    order_item_class = models.SalesOrderItem
    order_item_bundle_class = models.SalesOrderItemBundle

    def checkout(
        self,
        request,
        data,
        items,
        delete_item=False,
        billing=None,
        shipping=None,
        from_cart=False,
    ):
        order = self._create(
            request.user,
            data,
            items,
            billing=billing,
            shipping=shipping,
            delete_item=delete_item,
            from_cart=from_cart,
        )
        post_checkout.send(sender=order.__class__, instance=order, actor=request.user)
        action.send(request.user, verb="create %s" % order._meta.verbose_name, action_object=order)
        return order

    def clone(self, request, obj):
        data = dict(
            group=obj.group,
            customer=obj.customer,
            discount=obj.discount,
            reference=obj.reference,
            note=obj.note,
            data=obj.data,
        )
        cloned = self._clone(request.user, data, obj)
        post_clone.send(sender=cloned.__class__, instance=cloned, actor=request.user)
        action.send(request.user, verb="clone %s" % obj._meta.verbose_name, action_object=cloned, target=obj)
        return cloned

    def convert(self, request, obj):
        """Convert Sales Order to Invoice"""
        data = dict(
            group=obj.group,
            customer=obj.customer,
            discount=obj.discount,
            reference=obj,
            note=obj.note,
            data=obj.data,
        )
        invoice_handler = InvoiceHandler()
        invoice = invoice_handler._clone(request.user, data, obj)
        post_convert.send(sender=invoice.__class__, instance=invoice, actor=request.user)
        action.send(request.user, verb="create %s" % invoice._meta.verbose_name, action_object=invoice, target=obj)
        return invoice


class SalesQuotationHandler(BaseHandler):
    order_class = models.SalesQuotation
    order_item_class = models.SalesQuotationItem
    order_item_bundle_class = models.SalesQuotationItemBundle

    def checkout(self, request, data, items, delete_item=False, billing=None, shipping=None, from_cart=False):
        order = self._create(
            request.user,
            data,
            items,
            billing=billing,
            shipping=shipping,
            delete_item=delete_item,
            from_cart=from_cart,
        )
        post_checkout.send(sender=order.__class__, instance=order, actor=request.user)
        action.send(request.user, verb="create %s" % order._meta.verbose_name, action_object=order)
        return order

    def clone(self, request, obj):
        data = dict(
            group=obj.group,
            customer=obj.customer,
            discount=obj.discount,
            reference=obj.reference,
            note=obj.note,
            data=obj.data,
        )
        cloned = self._clone(request.user, data, obj)
        post_clone.send(sender=cloned.__class__, instance=cloned, actor=request.user)
        action.send(request.user, verb="clone %s" % obj._meta.verbose_name, action_object=cloned, target=obj)
        return cloned

    def convert(self, request, obj):
        """Convert Sales Quotation to Sales Order"""
        data = dict(
            group=obj.group,
            customer=obj.customer,
            discount=obj.discount,
            reference=obj.reference,
            note=obj.note,
            data=obj.data,
        )
        sales_order_handler = SalesOrderHandler()
        invoice = sales_order_handler._clone(request.user, data, obj)
        post_convert.send(sender=obj.__class__, instance=invoice, actor=request.user)
        action.send(
            request.user,
            verb="convert %s to %s" % (obj._meta.verbose_name, invoice._meta.verbose_name),
            action_object=invoice,
            target=obj,
        )
        return invoice


class InvoiceHandler(BaseHandler):
    order_class = models.Invoice
    order_item_class = models.InvoiceItem
    order_item_bundle_class = models.InvoiceItemBundle

    def convert(self, request, obj):
        """Convert Sales Order to Invoice"""
        data = dict(
            group=obj.group,
            customer=obj.customer,
            discount=obj.discount,
            reference=obj,
            note=obj.note,
            data=obj.data,
        )
        salesorder = self.clone(request.user, data, obj)
        post_convert.send(sender=salesorder.__class__, instance=salesorder, actor=request.user)
        action.send(request.user, verb="clone %s" % obj._meta.verbose_name, action_object=obj, target=obj)
        return salesorder
