import logging
import time
from typing import Generator

from rich import print_json
from woocommerce import API

from kiraak import console
from kiraak.api import get_catalog, login
from kiraak.catalog import Catalog
from kiraak.config import Auth

wcapi = API(
    url="https://rgbsocial.redgreenbluemix.com/",
    consumer_key=Auth.WOOCOMMERCE_CONSUMER_KEY,
    consumer_secret=Auth.WOOCOMMERCE_CONSUMER_SECRET,
    wp_api=True,
    version="wc/v3",
)


logger = logging.getLogger(__name__)

class WC_Product:
    def __init__(self, raw_json) -> None:
        self.id = raw_json["id"]
        self.name = raw_json["name"]
        self.status = raw_json["status"]
        self.old_status = raw_json["status"]
        self.description = raw_json["description"]
        self.sku = raw_json["sku"]
        self.price = None
        if raw_json["price"]:
            self.price = int(raw_json["price"])
            self.old_price = int(raw_json["price"])
        else:
            logger.error(f"Product {self.name!r} has no price!")


class WC_Products:
    def __init__(self, raw_json: dict) -> None:
        self.prods = list(filter(lambda x: x.price, [WC_Product(x) for x in raw_json]))

    def update_prods(self, catalog: Catalog):
        for prod in self.prods:
            if cprod := catalog.find_by_id(prod.sku):
                prod.status = "publish"
                prod.price = int(cprod.price)
            else:
                prod.status = "draft"

    def find_by_sku(self, sku):
        return next((x for x in self.prods if x.sku == sku), None)

    @property
    def updated_prods(self) -> Generator[WC_Product, None, None]:
        return iter(filter(lambda x: x.old_price != x.price or x.status != x.old_status, self.prods))

    def __iter__(self) -> Generator[WC_Product, None, None]:
        return iter(self.prods)


def sync():
    # Get and print catalog
    logger.info("Fetching catalog...")
    catalog = Catalog(get_catalog())
    logger.info(f"Recieved catalog (id {catalog.id}) with {len(catalog.products)} products")

    catalog.print_table(console)

    logger.info("Fetching existing WooCommerce Products...")
    prods = []
    i = 1
    while new_prods := wcapi.get("products", json={"page": i, "per_page": 100}).json():
        logger.info(f"Fetching page {i}")
        i += 1
        try:
            if new_prods["data"]["status"] != 200:
                logger.error(new_prods["message"])
        except (KeyError, TypeError):
            pass
        prods.extend(new_prods)

    logger.info(f"Recieved {len(prods)} existing WooCommerce Products")
    woocommerce_products = WC_Products(prods)
    woocommerce_products.update_prods(catalog)
    for prod in catalog:
        if not woocommerce_products.find_by_sku(prod.product_id):
            logger.warning(f"Product not found in WooCommerce: {prod.name} {prod.desc} {prod.quantity} ({prod.product_id})")
    data = {
        "update": [
            {
                "id": x.id,
                "status": x.status,
                "regular_price": x.price,
            }
            for x in woocommerce_products
            if (x.status != x.old_status or x.price != x.old_price)
        ]
    }
    for prod in woocommerce_products.updated_prods:
        logger.info(
            f"Updating [bold]{prod.name}[/] ({prod.old_status!r} -> {prod.status!r}) (₹{prod.old_price!r} -> ₹{prod.old_price!r})",
            extra={"markup": True}
        )
    logger.info(f"Syncing {len(data['update'])} products...")
    returned = wcapi.post("products/batch", data=data).json()
    logger.info("Synced!")

def main(once, time_gap):
    logger.info(f"Logging in as {Auth.MOBILE}")
    partner_info = login(Auth.MOBILE, Auth.PASSWORD)
    logger.info(
        f"Logged in as {partner_info['partnerName']} @ {partner_info['partnerBrand']}"
    )

    sync()
    while not once:
        time.sleep(time_gap)
        sync()

if __name__ == "__main__":
    main()
