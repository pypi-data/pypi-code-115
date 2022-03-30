# Standard lib imports
import abc
import itertools

# Local imports
from qwilfish.results_db.dataclasses import ResultsDbTableDefinition
from qwilfish.results_db.dataclasses import ResultsDbReport

class BaseOracle(abc.ABC):

    newid = itertools.count()

    def __init__(self):
        '''
        Call in subclass to generate a unique identifier for the instance.
        Identifier will be on the form <subclass_name>_<unique_number>.
        '''
        self.uid = f"{self.__class__.__name__}_{next(BaseOracle.newid)}"

    def get_uid(self):
        '''
        Return unique identifier for a subclass instance.
        '''
        return self.uid

    @abc.abstractmethod
    def get_table(self) -> ResultsDbTableDefinition:
        ''' 
        Returns the structure of the table that the reported data will
        adhere to. That is, the name of the table and the names of all
        the columns and their respective data types.
        '''
        pass

    @abc.abstractmethod
    def report(self) -> ResultsDbReport:
        '''
        Returns a report of the oracle's observations in the form of a table.
        '''
        pass

    @abc.abstractmethod
    def needs_holdoff(self) -> bool:
        '''
        Return True to signal signal for a break in the fuzzing session, e.g.
        to reestablish a connection or to restart a process.
        '''
        pass
