"""Processing of json file and adding orders"""
import json
import logging
from math import prod

from rich.table import Table

from kiraak import console
from kiraak.add_orders import add_orders
from kiraak.api import get_catalog, login
from kiraak.catalog import Catalog
from kiraak.config import Auth
from kiraak.order import OrderList

logger = logging.getLogger(__name__)


def main(file: str) -> None:
    """Process files, adds orders"""

    # Login
    logger.info(f"Logging in as {Auth.MOBILE}")
    partner_info = login(Auth.MOBILE, Auth.PASSWORD)
    logger.info(
        f"Logged in as {partner_info['partnerName']} @ {partner_info['partnerBrand']}"
    )

    # Get and print catalog
    logger.info("Fetching catalog...")
    catalog = Catalog(get_catalog())
    logger.info(f"Recieved catalog (id {catalog.id})")
    catalog.print_table()

    # Process json file
    logger.info(f"Processing {file}")
    with open(file, "r") as file_obj:
        orders = OrderList(json.load(file_obj))
    logger.info(f"Processed {len(orders)} orders")

    logger.info(f"Adding {len(orders)} orders...")
    add_orders(orders, catalog)
    logger.info(
        f"Added {len(list(filter(lambda x: x.added, orders)))} orders!\n[bold]All done![/]",
        extra={"markup": True},
    )
