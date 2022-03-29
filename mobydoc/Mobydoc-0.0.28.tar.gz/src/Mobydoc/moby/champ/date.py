import logging
import uuid
import datetime
import re

from sqlalchemy import (TIMESTAMP, Column, DateTime, ForeignKey, Integer,
                        String, text)
from sqlalchemy.dialects.mssql import TINYINT
from sqlalchemy.orm import relationship

from ...base import UUID, Base, indent, json_dump

log = logging.getLogger(__name__)
DEBUG = True

class MobyChampDate(Base):

    VAR_DAY = 'day'
    VAR_MONTH = 'month'
    VAR_YEAR = 'year'

    __tablename__ = "MobyChampDate"

    id = Column("MobyChampDate_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    jour = Column("MobyChampDate_Jour", TINYINT, nullable=True)
    mois = Column("MobyChampDate_Mois", TINYINT, nullable=True)
    annee = Column("MobyChampDate_Année", Integer, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)


    def isoformat(self):
        if self.jour and self.mois and self.annee:
            return ('%04d-%02d-%02d'%(self.annee, self.mois, self.jour))
        return None

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['jour'] = self.jour
        data['mois'] = self.mois
        data['annee'] = self.annee

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data

    @classmethod
    def parse(cls, data):
        if type(data) is str:
            if DEBUG:
                log.info("%s - data '%s' is string format, attempt to extract date data"%(cls.__name__, data))
            # expected date format: dd/mm/yyyy
            m = re.match(r'(?P<day>\d{2})/(?P<month>\d{2})/(?P<year>\d{4})', data)
            if not m:
                log.error("%s - Invalid date format, expected dd/mm/yyyy '%s'"%(cls.__name__, data))
                exit(1)
            data = m.groupdict()

        return data

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        d = self.parse(other)
        if DEBUG:
            log.info("%s == | %s %s"%(_cln, self, d))
        day = int(d.get("day", "0"))
        if self.jour != day:
            return False
        month = int(d.get("month", "0"))
        if self.mois != month:
            return False
        year = int(d.get("year", "0"))
        if self.annee != year:
            return False
        return True

    @classmethod
    def create(cls, data=None):
        if DEBUG:
            log.info("create %s: %s"%(cls.__name__, data))
        d = cls()
        d.t_creation_user = text("(USER)")
        d.t_write_user = text("(USER)")
        if data:
            up = d._update(data)
            if not up:
                return False
        return d

    def update(self, data):
        if DEBUG:
            log.info("update %s: %s"%(self.__class__.__name__, data))
        return self._update(data)

    def _update(self, data):
        if DEBUG:
            log.info("_update %s: %s"%(self.__class__.__name__, data))
        updated = False

        data = self.parse(data)

        # check if we have all bits of date
        day = data.get(self.VAR_DAY, None)
        month = data.get(self.VAR_MONTH, None)
        year = data.get(self.VAR_YEAR, None)

        if not day:
            log.error("%s - missing day data for date"%(self.__class__.__name__))
            return False
        else:
            if not day.isnumeric():
                log.error("%s - day data is not a number '%s'"%(self.__class__.__name__, day))
                return False
            day = int(day)
        if not month:
            log.error("%s - missing month data for date"%(self.__class__.__name__))
            return False
        else:
            if not month.isnumeric():
                log.error("%s - month data is not a number '%s'"%(self.__class__.__name__, month))
                return False
            month = int(month)
        if not year:
            log.error("%s - missing year data for date"%(self.__class__.__name__))
            return False
        else:
            if not year.isnumeric():
                log.error("%s - year data is not a number '%s'"%(self.__class__.__name__, year))
                return False
            year = int(year)

        # check if date is valid
        try:
            d = datetime.date(year, month, day)
        except ValueError as e:
            log.error("%s - '%04d-%02d-%02d' is an invalid date"%( \
                self.__class__.__name__, \
                year, month, day))
            return False
        
        if DEBUG:
            log.info("%s - all checks ok, setting new date"%(self.__class__.__name__))
        self.jour = day
        self.mois = month
        self.annee = year

        return True