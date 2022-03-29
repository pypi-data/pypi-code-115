import logging
import uuid

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, Float, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_loop
from ..utilities import listGenUpdates, renumber
from .champs.zone_datation_geologique.datation_geologique import \
    ChampSpecimenZoneDatationGeologiqueDatationGeologique as \
    t_datation_geologique

log = logging.getLogger(__name__)

DEBUG = True


class SpecimenZoneDatationGeologique(Base):
    VAR_DATATION_GEOLOGIQUE = t_datation_geologique.VAR_DATATION_GEOLOGIQUE

    # définition de table
    __tablename__ = "SpecimenZoneDatationGeologique"

    id = Column("SpecimenZoneDatationGeologique_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    notes = Column("SpecimenZoneDatationGeologique_Notes", String, nullable=True)
    id_specimen = Column("SpecimenZoneDatationGeologique_Specimen_Id", UUID, ForeignKey("Specimen.Specimen_Id"), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    #
    # Links
    # 

    specimen = relationship("Specimen", foreign_keys=[id_specimen])
    
    #
    # external links
    #
    
    # datation_geologique
    datations_geologiques = relationship(t_datation_geologique, back_populates='zone_datation_geologique', order_by=t_datation_geologique.ordre)
    # référence bibliographique
    # from .champs.zone_collecte.autres_coordonnees import ChampSpecimenZoneCollecteAutresCoordonnees as t_autres_coordonnees
    # autres_coordonnees = relationship(t_autres_coordonnees, back_populates='zone_collecte', order_by=t_autres_coordonnees.ordre)

    # 
    # generate json representation
    # 

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['datations_geologiques'] = json_loop(self.datations_geologiques)
        data['notes'] = self.notes

        data['t_write'] = self.t_write.isoformat() if self.t_write else None
        data['t_creation'] = self.t_creation.isoformat() if self.t_creation else None
        data['t_write_user'] = str(self.t_write_user) if self.t_write_user is not None else None
        data['t_creation_user'] = str(self.t_creation_user) if self.t_creation_user is not None else None

        return data

    @classmethod
    def create(cls, data, db=None):
        if DEBUG:
            log.info("%s - create %s"%(cls.__name__, data))
        zdg = cls()
        zdg.t_creation_user = text("(USER)")
        zdg.t_write_user = text("(USER)")
        if data:
            up = zdg._update(data, db)
            if not up:
                return None
        return zdg

    def update(self, data, db):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s - update - %s"%(_cln, data))
        return self._update(data, db)

    def _update(self, data, db=None):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s - _update %s"%(_cln, data))
        
        dg = data.get(self.VAR_DATATION_GEOLOGIQUE, None)
        if dg:
            if type(dg) is not list:
                dg = [ dg ]
            rem, ok, add = listGenUpdates(self.datations_geologiques, dg)
            if DEBUG:
                log.info("    rem : %s"%(rem))
                log.info("    ok  : %s"%(ok))
                log.info("    add : %s"%(add))

            # handle removed bits
            if not db:
                log.error("%s update | missing db argument"%(_cln))
                return False
            for r in rem:
                log.info("%s update | deleting %s"%(_cln, r))
                db.delete(r)
            
            i = renumber(ok)

            # handle add
            for datation in add:             
                if DEBUG:
                    log.info("%s - _update - add new %s('%s')"%(_cln, self.VAR_DATATION_GEOLOGIQUE, datation))
                dg = t_datation_geologique.create(data, db)
                if not dg:
                    log.error("%s - _update - unable to create %s"%(_cln, t_datation_geologique.__name__))
                    return False
                log.info("%s - _update - datation geologique created %s"%(_cln, dg))
                dg.zone_datation_geologique = self
            
        else:         
            log.error("%s - %s missing in data"%(_cln, self.VAR_DATATION_GEOLOGIQUE))
            return False
 
        return True
