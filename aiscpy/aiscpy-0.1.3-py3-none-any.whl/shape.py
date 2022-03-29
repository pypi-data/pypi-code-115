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
    def __init__(self, typeShape: str,name: str) -> None:
        """Querying for shape objects

        Args:
            type (str): type of the section ('W')
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
        return self.__query
    
    @property
    def table(self):
        return self.__table
