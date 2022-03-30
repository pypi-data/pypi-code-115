# -*- coding: utf-8 -*-
class TestHelper(object):

    """A Helper Class for various functions associated with API testing.

    This class contains static and class methods for operations that need to be
    performed during API testing. All of the methods inside this class are
    static or class methods, there is no need to ever initialise an instance of this
    class.
    Attributes:
        cache (Set): Class variable which stores hashes of file URLs so we don't
            download the same file twice in a test session.
    """

    @staticmethod
    def match_body(expected_body,
                   received_body,
                   check_values=False,
                   check_order=False,
                   check_count=False):
        """Static method to compare the received body with the expected body.

        Args:
            expected_body (dynamic): The expected body.
            received_body (dynamic): The received body.
            check_values (Boolean, optional): A flag which determines if we
                check values in dictionaries.
            check_order (Boolean, optional): A flag which determines if we
                check the order of array elements.
            check_count (Boolean, optional): A flag which determines if we
                check the count of array elements.
        Returns:
            Boolean: True if bodies match, False otherwise.

        """
        if type(expected_body) == dict:
            if type(received_body) != dict:
                return False
            for key in expected_body:
                if key not in received_body:
                    return False
                if check_values or type(expected_body[key]) == dict:
                    if TestHelper.match_body(expected_body[key], received_body[key],
                                             check_values, check_order, check_count) == False:
                        return False
        elif type(expected_body) == list:
            if type(received_body) != list:
                return False
            if check_count == True and (len(expected_body) != len(received_body)):
                return False
            else:
                previous_matches = []
                for i, expected_element in enumerate(expected_body):
                    matches = [j for j, received_element
                               in enumerate(received_body)
                               if TestHelper.match_body(expected_element, received_element,
                                                        check_values, check_order, check_count)]
                    if len(matches) == 0:
                        return False
                    if check_order == True:
                        if i != 0 and all([all(y > x for y in previous_matches) for x in matches]):
                            return False
                        previous_matches = matches
        elif expected_body != received_body:
            return False
        return True