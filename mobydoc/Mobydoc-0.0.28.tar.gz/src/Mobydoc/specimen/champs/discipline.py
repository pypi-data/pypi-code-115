import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship


from ...base import UUID, Base, indent, json_test, json_dump
from ...reference.discipline import Discipline

log = logging.getLogger(__name__)

DEBUG = True

class ChampDiscipline(Base):
    # définition de table
    __tablename__ = "ChampDiscipline"

    id = Column("ChampDiscipline_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_specimen = Column("ChampDiscipline_Specimen_Id", UUID, ForeignKey("SpecimenZoneDiscipline.SpecimenZoneDiscipline_Id"), nullable=True)
    id_discipline = Column("ChampDiscipline_Discipline_Id", UUID, ForeignKey("Discipline.Reference_Id"), nullable=True)
    ordre = Column("ChampDiscipline_Ordre", INTEGER, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    # liaisons

    discipline = relationship(Discipline, foreign_keys=[id_discipline])
    zone_discipline = relationship("SpecimenZoneDiscipline", foreign_keys=[id_specimen], back_populates="disciplines")

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['discipline'] = json_test(self.discipline)
        data['ordre'] = self.ordre

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data


    @property
    def xml(self):
        s = "<%s id=\"%s\""%(self.__class__.__name__, self.id)
        if self.ordre:
            s+= " ordre=\"%d\""%(self.ordre)
        s+= ">\n"
        if self.discipline:
            s+= indent(self.discipline.xml)
        s+= "</%s>\n"%(self.__class__.__name__)
        return s
        
    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s == | '%s'"%(_cln, other))
        if not self.discipline:
            return False
        if not self.discipline.label:
            return False
        log.info("%s == | '%s' '%s' ?"%(_cln, self.discipline.label, other))
        if self.discipline.label == other:
            return True
        return False        
        
    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s create | '%s'"%(_cln, data))
        d = cls()
        d.t_creation_user = text("(USER)")
        d.t_write_user = text("(USER)")
        if data:
            up = d._update(data, db)
            if not up:
                log.error("unable to create discipline")
                return False
        return d

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s _update | '%s'"%(_cln, data))
        if self.discipline:
            if self.discipline == data:
                log.info("%s _update | discipline '%s' already set"%(_cln, data))
                return True
        
        log.info("%s _update | need to add '%s'"%(_cln, data))
        d = Discipline.find(data, db)
        if d is None:
            log.error("%s _update | unable to find discipline '%s'"%(_cln, data))
        log.info("%s _update | found %s"%(_cln, d))  
        self.discipline = d
        return True
    