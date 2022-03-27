from ordersystem.meals import Breakfast, Lunch, Dinner
import logging, os, json
from ordersystem.custom_exceptions import UnknownItemException

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=LOG_LEVEL)

class OrderSystem:
    def __init__(self):
        self.menu_mapping = {
            "breakfast": Breakfast(),
            "lunch" : Lunch(),
            "dinner" : Dinner()
        }

    def get_order(self, menu_type, order):
        order = order.replace(" ", "")
        order_list = order.split(",")
        logging.debug(f"Received order: {menu_type} List of items: {order_list}")
        course_category = json.loads(os.getenv("COURSE_CATEGORY_MAPPING"))
        drink = course_category["drink"]

        if drink not in order_list:
            logging.info("Drink is not included. Adding water...")
            order_list.append("Water")
        
        logging.info("Getting the menu")
        try:
            menu = self.menu_mapping[menu_type.lower()]
        except KeyError as e:
            raise UnknownItemException(menu_type)

        logging.info(f"Getting the food for {menu}")
        return menu.get_food(order_list)