from ordersystem.menu import Menu
from ordersystem.custom_exceptions import TooManyItemsException, OrderIncompleteException
import logging

class Breakfast(Menu):
    def __init__(self):
        self.meal = "breakfast"

    def get_food(self, order_list):
        self.meal_menu, self.complimentary_items = Menu.get_menu(self.meal)
        self.course_category = Menu.get_course_category()
        logging.info("Validating Breakfast Order...")
        logging.debug(f"Validating Breakfast Order {order_list}")
        self.validate(order_list)
        logging.info("Getting order")
        return self.aggregate(order_list)
    
    def validate(self, order_list):
        invalid_order = self.mandatory_item_validation(order_list)
        logging.debug(f"Invalid Order: {invalid_order}")
        if invalid_order:
            raise OrderIncompleteException(invalid_order)
        too_many_message = self.too_many_validation(order_list)
        logging.debug(f"Too many items Order: {too_many_message}")
        if too_many_message:
            raise TooManyItemsException(too_many_message)
        return


class Lunch(Menu):
    def __init__(self):
        self.meal = "lunch"

    def get_food(self, order_list):
        self.meal_menu, self.complimentary_items = Menu.get_menu(self.meal)
        self.course_category = Menu.get_course_category()
        logging.info("Validating Lunch Order...")
        logging.debug(f"Validating Lunch Order {order_list}")
        self.validate(order_list)
        logging.info("Getting order")
        return self.aggregate(order_list)

    def validate(self, order_list):
        invalid_order = self.mandatory_item_validation(order_list)
        logging.debug(f"Invalid Order: {invalid_order}")
        if invalid_order:
            raise OrderIncompleteException(invalid_order)
        too_many_message = self.too_many_validation(order_list)
        logging.debug(f"Too many items Order: {too_many_message}")
        if too_many_message:
            raise TooManyItemsException(too_many_message)
        return

class Dinner(Menu):
    def __init__(self):
        self.meal = "dinner"

    def get_food(self, order_list):
        self.meal_menu, self.complimentary_items = Menu.get_menu(self.meal)
        self.course_category = Menu.get_course_category()
        logging.info("Validating Dinner Order...")
        logging.debug(f"Validating Dinner Order {order_list}")
        self.validate(order_list)
        logging.info("Getting order")
        return self.aggregate(order_list)

    def validate(self, order_list):
        invalid_order = self.mandatory_item_validation(order_list)
        logging.debug(f"Invalid Order: {invalid_order}")
        if invalid_order:
            raise OrderIncompleteException(invalid_order)
        too_many_message = self.too_many_validation(order_list)
        logging.debug(f"Too many items Order: {too_many_message}")
        if too_many_message:
            raise TooManyItemsException(too_many_message)
        return