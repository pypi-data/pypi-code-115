# -*- coding: utf-8 -*-
from yuansfer.exception import RequireParamsError
import collections
import hashlib

class APIHelper(object):

    @staticmethod
    def merge_dicts(dict1, dict2):
        """Merges two dictionaries into one as a shallow copy.
        Args:
            dict1 (dict): The first dictionary.
            dict2 (dict): The second dictionary.
        Returns:
            dict: A dictionary containing key value pairs
            from both the argument dictionaries. In the case
            of a key conflict, values from dict2 are used
            and those from dict1 are lost.
        """
        temp = dict1.copy()
        temp.update(dict2)
        return temp

    @staticmethod
    def to_dictionary(dictionary):
        """Create a key value pair dictionary
        Args:
            obj: The dictionary.
        Returns:
            dictionary: A ordered dictionary form of the model with properties in
            their API formats.
        """

        # Return the result
        dictionary.pop('verifySign', None)
        return collections.OrderedDict(sorted(dictionary.items()))

    @staticmethod
    def append_parameters(parameters):
        """Conconcate parameters
        Args:
            parameters (OrderedDict): The parameters to append.
        Returns:
            str: string with appended parameters.
        """
        # Parameter validation
        if parameters is None:
            raise RequireParamsError('Parameters')

        queryString = ""

        # Loop through all parameters and concatenate the parameter names and values using '=' and '&' character
        for key, value in parameters.items():
            seperator = '&'
            if value is not None:
                queryString += "{0}{1}={2}".format(seperator, key, str(value))
        queryString = queryString[1:]
        return queryString

    @staticmethod
    def verify_signature(parameters,token):
        """Verify MD5 signature
        Args:
            parameters (OrderedDict): The parameters to verify
            token: The merchant token
        Returns:
            bool: true if valid signature.
        """
        if not parameters['verifySign']:
            return False

        verifySign = parameters['verifySign']

        dictionaryParams = APIHelper.to_dictionary(parameters)
        stringParams = APIHelper.append_parameters(dictionaryParams)
        md5TokenStr =hashlib.md5(token.encode("utf-8")).hexdigest()
        resVerifySign = hashlib.md5((stringParams + '&' + md5TokenStr).encode("utf-8")).hexdigest()

        return verifySign == resVerifySign


