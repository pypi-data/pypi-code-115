import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY, Float,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_loop, json_dump
from ..utilities import listGenUpdates, renumber
from .champs.zone_collecte.provenance import ChampSpecimenZoneCollecteProvenance as t_provenance

log = logging.getLogger(__name__)

DEBUG = True

class SpecimenZoneCollecte(Base):
    VAR_PROVENANCE = 'provenance'

    # définition de table
    __tablename__ = "SpecimenZoneCollecte"

    id = Column("SpecimenZoneCollecte_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_methode_collecte = Column("SpecimenZoneCollecte_MethodeCollecte_Id", UUID, nullable=True)
    notes = Column("SpecimenZoneCollecte_Notes", String, nullable=True)
    id_specimen = Column("SpecimenZoneCollecte_Specimen_Id", UUID, ForeignKey("Specimen.Specimen_Id"), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    latitude = Column("SpecimenZoneCollecte_Latitude", Float, nullable=True)
    longitude = Column("SpecimenZoneCollecte_Longitude", Float, nullable=True)

    #
    # Links
    # 

    specimen = relationship("Specimen", foreign_keys=[id_specimen], back_populates='zone_collecte')
    
    #
    # external links
    #
    
    provenances = relationship(t_provenance, back_populates='zone_collecte', order_by=t_provenance.ordre)
    from .champs.zone_collecte.autres_coordonnees import ChampSpecimenZoneCollecteAutresCoordonnees as t_autres_coordonnees
    autres_coordonnees = relationship(t_autres_coordonnees, back_populates='zone_collecte', order_by=t_autres_coordonnees.ordre)

    from .champs.zone_collecte.collecteur import ChampSpecimenZoneCollecteCollecteur as t_collecteur
    collecteurs = relationship(t_collecteur, back_populates='zone_collecte', order_by=t_collecteur.ordre)

    # 
    # generate json representation
    # 

    @property
    def provenance_list(self):
        data = []
        for p in self.provenances:
            data.append(p.tree)
        return data

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['provenances'] = json_loop(self.provenances)
        data['latitude'] = self.latitude
        data['longitude'] = self.longitude
        data['autres_coordonnees'] = json_loop(self.autres_coordonnees)

        # biotope

        # collecteur

        # date de collecte

        data['id_methode_collecte'] = str(self.id_methode_collecte)
        data['notes'] = self.notes

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__
        if DEBUG:
            log.info("%s - create - %s"%(_cln, data))
        zc = cls()
        zc.t_creation_user = text("(USER)")
        zc.t_write_user = text("(USER)")
        if data:
            up = zc._update(data, db)
            if not up:
                return False
        return zc

    def update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - update - %s"%(_cln, data))
        return self._update(data, db)


    def _update(self, data, db):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s - _update - %s"%(_cln, data))
        
        # add or find champs_provenance
        provenance = data.get(self.VAR_PROVENANCE, None)
        if provenance:
            if type(provenance) is not list:
                provenances = [ provenance ]
            rem, ok, add = listGenUpdates(self.provenances, provenances, dupes=True)
            if DEBUG:
                log.info("    rem : %s"%(rem))
                log.info("    ok  : %s"%(ok))
                log.info("    add : %s"%(add))

            # handle rem
            for p in rem:
                log.info("DEL * %s"%(p))
                p.zone_collecte = None
                db.delete(p)

            i = renumber(ok)

            # handle add
            for provenance in add:
                # create a new provenance
                log.info("%s - _update - create provenance %s"%(_cln, provenance))
                p = t_provenance.create(provenance, db)
                if not p:
                    log.error("%s - _update - problem creating provenance"%(_cln))
                    return False
                log.info("%s - _update - we have a provenance %s"%(_cln, p))
                p.zone_collecte = self

                # set ordre
                log.info("renum * %d"%(i))
                p.ordre = i
                i += 1
        
        return True


    