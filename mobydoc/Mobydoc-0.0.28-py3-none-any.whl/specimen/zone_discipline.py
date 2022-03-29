import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_loop, json_dump
from ..utilities import listGenUpdates, renumber
from .champs.discipline import ChampDiscipline as t_discipline

log = logging.getLogger(__name__)

DEBUG = True

class SpecimenZoneDiscipline(Base):
    VAR_DISCIPLINES = "disciplines"

    # définition de table
    __tablename__ = "SpecimenZoneDiscipline"

    id = Column("SpecimenZoneDiscipline_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    id_specimen = Column("SpecimenZoneDiscipline_Specimen_Id", UUID, ForeignKey("Specimen.Specimen_Id"), nullable=True)

    #specimen = relationship("Specimen", foreign_keys=[id_specimen], back_populates='zone_discipline', post_update=True)

    disciplines = relationship(t_discipline, order_by="ChampDiscipline.ordre")

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = self.id

        data['disciplines'] = json_loop(self.disciplines)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s create | %s"%(_cln, data))
        zd = cls()
        zd.t_creation_user = text("(USER)")
        zd.t_write_user = text("(USER)")
        if data:
            up = zd._update(data, db)
            if not up:
                log.error("%s create | error updating zone_discipline"%(_cln))
                return False
        return zd    
    
    def update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s update | %s"%(_cln, data))
        return self._update(data, db)

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s _update | %s"%(_cln, data))
        
        disciplines = data.get(self.VAR_DISCIPLINES, None)
        if not disciplines:
            log.error("%s _update | missing '%s' in data"%(_cln, self.VAR_DISCIPLINES))
        rem, ok, add = listGenUpdates(self.disciplines, disciplines)
        log.info("rem : %s"%(rem))
        log.info("ok  : %s"%(ok))
        log.info("add : %s"%(add))

        # handle remove

        i = renumber(ok)

        # handle add
        for d in add:
            log.info("%s _update | add '%s'"%(_cln, d))
            d = t_discipline.create(d, db)
            if not d:
                log.error("%s _update | unable to create '%s'"%(_cln, t_discipline.__name__))
                return False
            d.ordre = i
            d.zone_discipline = self
            i += 1

        return True