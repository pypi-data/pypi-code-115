"""Athena Query Utilities"""

def encode_list_as_list_of_strings(items: list):
    """
        Encodes a list as a String list of string items for Athena query.
        
        Adding a list of items to athena query argument requires it to be
        encoded as a string encoded list
    """
    items = ["\'{ITEM}\'".format(ITEM=item) for item in items]
    return ",".join(items)
