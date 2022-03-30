
from aiscpy.core import QueryingToDB, ascOrDesc, selectTable, strForOrdered, strForSelect, strForWhere

class SelectByCriteria():
    def __init__(self, typeShape: str, prop: str, criteria: float | int, typeCriteria: str) -> None:

        if not isinstance(typeShape, str):
            raise TypeError('typeShape must be a string')
        if not isinstance(prop, str):
            raise TypeError('property name must be a string, example: "Sx" ')
        if not isinstance(criteria, (int, float)):
            raise TypeError('Criteria must be a number')
        if not typeCriteria in ['max', 'min', 'equal']:
            raise ValueError(
                'typeCriteria must be a string in ["max", "min", "equal"]')

        self.__typeShape: str = typeShape
        self.__prop = prop
        self.__criteria = criteria
        self.__typeCriteria = typeCriteria

        self.__table: str = selectTable(self.__typeShape)
        self.__strSelect: str = strForSelect(self.__table, all=True)
        self.__strWhere: str = strForWhere(
            self.__prop, self.__criteria, self.__typeCriteria)
        self.__strType: str = "AND Type = '{}'".format(self.__typeShape)
        self.__strOrderedAsc: str = ""

        if self.__typeCriteria != 'equal':
            self.__strOrderedAsc += strForOrdered(
                self.__prop, asc=ascOrDesc(self.__typeCriteria))

        self.__command = self.__strSelect + self.__strWhere + self.__strOrderedAsc

        self.__primaryQuery = QueryingToDB(self.__command, fetchone=True)
        self.__secondaryQuery = QueryingToDB(self.__command)

    @property
    def query(self):
        return self.__primaryQuery
