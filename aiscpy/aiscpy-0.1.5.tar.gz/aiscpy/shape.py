'''
*******************************************
*                                         *
* author : Rodrigo Jimenez                *
* E-mail : jimenezhuancarodrigo@gmail.com *
* copyright : (c) 2022                    *
* date : 2022                             *
*                                         *
*******************************************
'''

import sqlite3

from aiscpy.core import QueryingToDB, selectTable


class Shape():
    """A object with a determinate shape
    """    
    def __init__(self, typeShape: str,name: str) -> None:
        """Querying for shape objects

        Args:
            typeShape (str): type of the section ('W')
            name (str): name of the shape object or name of section ('W44X335')

        Raises:
            TypeError: Shape must be a string
        """        
        
        if not isinstance(name, str):
            raise TypeError("Shape must be a string")
        if not isinstance(typeShape, str):
            raise TypeError("Type must be a string")
        
        self.__name = name
        self.__typeShape = typeShape
        self.__table = selectTable(self.__typeShape)
        
        self.__queryStr: str = "SELECT * FROM "+ self.__table +" WHERE Shape= '" + self.__name + "' "
        
        self.__query = QueryingToDB(self.__queryStr, fetchone=True)
        
    @property    
    def query(self):
        """a method for return data of a shape

        Returns:
            Query: Data of a shape
        """        
        return self.__query
    
    @property
    def table(self):
        """return table name

        Returns:
            str: name of the table
        """        
        return self.__table
