import os.path
import sqlite3

from aiscpy.info import nameTables, nameTablesDict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR,'shapes_AISC.db')

class QueryingToDB():
    """Class for querying to DB's AISC
    """    
    def __init__(self, query: str, fetchone:bool = False) -> None:
        """class for querying to DB's AISC

        Args:
            query (str): Intruction in str
            fetchone (bool, optional): Is the method for selection of results. Defaults to False.

        Raises:
            TypeError: TypeError
        """         
        if not isinstance(fetchone, bool):
            raise TypeError('"fetchone" not in a bool')
        
        self.__fetchoneStatus = fetchone
        
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        self.__query_execute = cur.execute(query)
        self.__keysQuery = [tuple[0] for tuple in self.__query_execute.description]
        
        if(fetchone):
            self.__query_list = list(self.__query_execute.fetchone())
        else:
            self.__query_list = list(self.__query_execute.fetchall())
            
        
        con.close()
    
    def __len__(self) -> int:
        return len(self.__query_list)
    
    @property
    def query(self):
        """return the query class

        Returns:
            queryClass: queryClass
        """        
        return self.__query_execute
    
    @property
    def queryToList(self):
        return self.__query_list
    
    @property
    def fetchoneStatus(self):
        return self.__fetchoneStatus
    
    @property
    def keysQuery(self):
        return self.__keysQuery
    
    def toDict(self):
        if (self.__fetchoneStatus):
            return dict(zip(self.__keysQuery, self.__query_list))
        else:
            raise ValueError('"fetchoneStatus" is False, not supported')

def updateTablesName():
    """update the name of the tables in the DB

    Returns:
        list: list of the name of the tables in the DB
    """    
    query_str = ''' SELECT name FROM sqlite_master
                    WHERE type='table' 
                '''
    tables = QueryingToDB(query_str)
    nameTables = []
    for i in range(0, len(tables)):
        nameTables.append(tables.queryToList[i][0])
        
    return nameTables

def selectTable(type: str)->str:
    """select a table of a type of shapes

    Args:
        type (str): Type of the shape, example: W, C, MC, Pipe, ...

    Raises:
        ValueError: not found table

    Returns:
        str: name of the table in ``
    """    
    for i in nameTables:
        if(type in nameTablesDict[i]):
            return i
    raise ValueError('not found table')

def strForSelect(table: str ,name = 'Shape', all = False):
    """is a method for generate a execute command for select

    Args:
        table (str): table's name. Return of the method ``selectTable``
        name (str, optional): name of the shape. Defaults to 'Shape'.
        all (bool, optional): all is True if SELECT * or SELECT 'name: str'. Defaults to False.

    Raises:
        TypeError: table must be a string
        TypeError: name must be a string
        TypeError: all must be a bool

    Returns:
        str: a string for execute command
    """    
    if not isinstance(table, str):
        raise TypeError("table must be a string")
    if not isinstance(name, str):
        raise TypeError("name must be a string")
    if not isinstance(all, bool):
        raise TypeError("all must be a boolean")
    
    if all:
        instruction = "SELECT * FROM {} ".format(table)
    else:
        instruction = "SELECT `{}` FROM {} ".format(name, table)
    
    return instruction

def strForWhere(prop:str, value: float|int, type: str )->str:
    """a string for execute command for where

    Args:
        prop (str): property of the shape
        value (float | int): a criteria value for the SELECT and WHERE
        type (str): type of the criteria, [min, max, equal]

    Raises:
        TypeError: prop must be a string
        TypeError: value must be a float or int
        TypeError: type must be a string
        ValueError: type not in ['min', 'max', 'equal']

    Returns:
        str: a string for execute command
    """    
    if not isinstance(prop, str):
        raise TypeError('prop must be a string')
    if not isinstance(value, (float, int)):
        raise TypeError('value must be a number')
    if not (type in ['min', 'max', 'equal']):
        raise TypeError('type must be a string in ["max", "min", "equal"]')
    
    if type == 'min':
        commandText = "WHERE `{}` >= {} ".format(prop, value)
    elif type == 'max' :
        commandText = "WHERE `{}` <= {} ".format(prop, value)
    elif type == 'equal':
        commandText = "WHERE `{}` = {} ".format(prop, value)
    else:
        raise ValueError('type not is "max" or "min" or "equal"')
    
    return commandText

def ascOrDesc(type: str)->bool:
    """a method for generate a execute command for order by

    Args:
        type (str): a string in ['min', 'max']

    Raises:
        TypeError: type , must be a string [min, max]

    Returns:
        bool: True or False, True if ASC, False if DESC
    """    
    if not isinstance(type, str):
        raise TypeError('type must be a string')
    if (type == 'min'):
        return True
    elif (type == 'max'):
        return False

def strForOrdered(prop: str, asc: bool= True)->str:
    """a method for generate a execute command for order by

    Args:
        prop (str): property of the shape
        asc (bool, optional): if is asc is true, please use method arcOrDesc. Defaults to True.

    Raises:
        TypeError: prop must be a string
        TypeError: asc must be a boolean

    Returns:
        str: string for execute command
    """    
    if not isinstance(prop, str):
        raise TypeError('prop must be a string')
    if not isinstance(asc, bool):
        raise TypeError('asc must be a boolean')
    
    if asc:
        commandText = "ORDER BY `{}` ASC ".format(prop)
    else:
        commandText = "ORDER BY `{}` DESC ".format(prop)
        
    return commandText