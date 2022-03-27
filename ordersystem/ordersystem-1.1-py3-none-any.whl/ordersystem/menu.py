import abc, os, json, logging
from collections import Counter

from ordersystem.custom_exceptions import UnknownItemException

class Menu:
    def __init__(self, meal):
        self.meal_menu = None
        self.complimentary_items = None
        self.meal = None
        self.course_category = None
    
    @staticmethod
    def get_menu(meal):
        meal = meal.lower()
        logging.debug(f"Retrieving menu from environment for {meal}")
        menu = json.loads(os.getenv("MENU"))
        logging.debug(f"Retrieved menu from environment for meal {meal} /n /t {menu}")
        complimentary_items = json.loads(os.getenv("COMPLIMENTARY"))
        logging.debug(f"Retrieved complimentary menu from environment for {meal} /n /t {complimentary_items}")
        return menu[meal], complimentary_items[meal]
    
    @staticmethod
    def get_course_category():
        logging.debug(f"Retrieving Course Category from environment")
        course_category = json.loads(os.getenv("COURSE_CATEGORY_MAPPING"))
        logging.debug(f"Retrieved course category from environment")
        return course_category

    
    def mandatory_item_validation(self, order_list):
        logging.info("Getting mandatory course list...")
        mandatory_course_list = json.loads(os.getenv("MANDATORY_COURSE"))[self.meal]
        logging.info(f"These courses must be ordered: {mandatory_course_list}")
        invalid_order = None

        logging.info("Checking order...")
        for course in mandatory_course_list:
            if self.course_category[course] not in order_list:
                if invalid_order is None:
                    invalid_order = f"{course.capitalize()}"
                else:
                    invalid_order += f" and {course.capitalize()}"
        logging.info(f"These courses were not ordered: {invalid_order}.")
        
        return invalid_order

    
    def too_many_validation(self, order_list):
        message = None
        self.meal = self.meal.lower()
        logging.debug(f"Retrieving items that could only be ordered once from environment for {self.meal}")
        single_item_list = json.loads(os.getenv("SINGLE_ITEM"))[self.meal]
        logging.debug(f"Retrieved items that could only be ordered once from environment for {self.meal} \n \t {single_item_list}")
        for i in single_item_list:
            if order_list.count(i) > 1:
                if message is None:
                    message = f"{self.meal_menu[i]}"
                else:
                    message += f" and {self.meal_menu[i]}"
        logging.debug(f"Error Message for too many items: {message}")
        return message

    def aggregate(self, order_list):
        def aggregator(food_tuple):
            return self.meal_menu[food_tuple[0]] if food_tuple[1]< 2 else f"{self.meal_menu[food_tuple[0]]}({food_tuple[1]})"
        logging.info("Counting the list of items")
        counter_list = Counter(order_list)
        logging.debug(f"Breakdown of the order:{counter_list}")
        food_amount_list = [(item, amount) for item, amount in counter_list.items()]
        logging.debug(f"Food item and the number of times ordered tuple: \n \t {food_amount_list}")

        logging.debug(f"Course category mapping:{self.course_category}")

        return_order_category = {}
        logging.info("Retrieving complimentary items for this meal...")
        for course in self.course_category.keys():
            return_order_category[course] = self.complimentary_items.get(course, "")

        logging.debug(f"Complimentary items for the meal {self.meal} \n \t {return_order_category}")
        logging.info(f"Complimentary items for the meal {self.meal} \n \t {return_order_category}")
        for item_num, amount in food_amount_list:
            if item_num in self.meal_menu:
                for course in return_order_category.keys():
                    if self.course_category[course] == item_num:
                        return_order_category[course] = aggregator((item_num,amount)) if return_order_category[course] == "" else return_order_category[course] + ", " +  aggregator((item_num,amount))
            elif item_num == "Water":
                return_order_category["drink"] = item_num
            else:
                logging.info("Unknown Item")
                raise UnknownItemException(item_num)
        logging.info(f"Order for the meal {self.meal} \n \t {return_order_category}")
        
        logging.info("Formatting order")
        order = ""
        logging.info(return_order_category)
        for course in return_order_category.keys():
            if return_order_category[course]:
                logging.info(return_order_category[course])
                order = order + return_order_category[course] + ", "
        order = order.strip(", ")
        return order

    @abc.abstractmethod
    def validate(self, order_list):
        return
    
    @abc.abstractmethod
    def get_food(self, order_list):
        return