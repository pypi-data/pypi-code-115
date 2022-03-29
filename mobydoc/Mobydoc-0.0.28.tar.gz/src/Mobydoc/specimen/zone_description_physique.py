import logging
import uuid

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_loop, json_test, json_dump
from ..utilities import listGenUpdates, renumber
from ..reference.type_information import TypeInformation
from .champs.zone_description_physique.nature_specimen import \
    ChampSpecimenZoneDescriptionPhysiqueNatureSpecimen as t_nature_specimen

log = logging.getLogger(__name__)

DEBUG = True


class SpecimenZoneDescriptionPhysique(Base):
    VAR_NOTES = 'notes'
    VAR_NATURES_SPECIMEN = 'natures_specimen'

    # définition de table
    __tablename__ = "SpecimenZoneDescriptionPhysique"

    id = Column("SpecimenZoneDescriptionPhysique_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    id_specimen = Column("SpecimenZoneDescriptionPhysique_Specimen_Id", UUID, ForeignKey("Specimen.Specimen_Id"), nullable=True)

    sexe = Column("SpecimenZoneDescriptionPhysique_Sexe", String(20), nullable=True)
    notes = Column("SpecimenZoneDescriptionPhysique_Notes", String, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # 
    # relationships
    #

    specimen = relationship("Specimen", foreign_keys=[id_specimen], back_populates='zone_description_physique')

    from .champs.zone_description_physique.caracteristiques_physiques import \
        ChampSpecimenZoneDescriptionPhysiqueCaracteristiquesPhysiques as \
        t_caracteristiques_physiques
    caracteristiques_physiques = relationship(t_caracteristiques_physiques, order_by=t_caracteristiques_physiques.ordre,
        back_populates='zone_description_physique')

    natures_specimen = relationship(t_nature_specimen, order_by=t_nature_specimen.ordre, back_populates='zone_description_physique')
    #
    # object properties
    #

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = self.id
        
        data['caracteristiques_physiques'] = json_loop(self.caracteristiques_physiques)
        data['natures_specimen'] = json_loop(self.natures_specimen)

        data['sexe'] = self.sexe
        data['notes'] = self.notes

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data

    @classmethod
    def create(cls, data=None, db=None):
        _cln = cls.__name__
        if DEBUG:
            log.info("%s - create %s"%(_cln, data))
        zdp = cls()
        zdp.t_creation_user = text("(USER)")
        zdp.t_write_user = text("(USER)")
        if data:
            up = zdp._update(data, db)
            if not up:
                return False
        return zdp

    def update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - _update - %s"%(_cln, data))
        return self._update(data, db)

    def _update(self, data, db):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s - _update - %s"%(_cln, data))

        notes = data.get(self.VAR_NOTES, None)
        if notes:
            if self.notes != notes:
                self.notes = notes
        
        # the list can be empty...
        ns = data.get(self.VAR_NATURES_SPECIMEN, None)
        if type(ns) is not list:
            ns = [ ns ]
        rem, ok, add = listGenUpdates(self.natures_specimen, ns)
        if DEBUG:
            log.info("    rem : %s"%(rem))
            log.info("    ok  : %s"%(ok))
            log.info("    add : %s"%(add))

        for r in rem:
            log.info("%s _update | removing %s"%(_cln, r))
            db.delete(r)

        i = renumber(ok)
        for o in ok:
            o.check()

        if add:
            log.info("%s _update | add the contents of add starting %d"%(_cln, i))
            for n in add:
                ns = t_nature_specimen.create(n, db)
                if not ns:
                    log.error("%s - _update - unable to create champ_nature_specimen record"%(_cln))
                    return False

                log.info("%s _update | we have : %s"%(_cln, ns.nature_specimen.label))
                ns.ordre = i
                i += 1
                ns.zone_description_physique = self
        else:
            log.info("%s _update | nothing to add"%(_cln))
 
        return True

 