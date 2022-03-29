import re
import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_loop, json_tags, json_dump
from .champs.zone_identification.autre_numero import ChampSpecimenAutreNumero as t_autre_numero

log = logging.getLogger(__name__)

DEBUG = True

class MobyTag_Specimen_SpecimenZoneIdentification_MobyTag(Base):
    __tablename__ = "MobyTag_Specimen_SpecimenZoneIdentification_MobyTag"

    id_tag = Column("MobyTag_Id", UUID, ForeignKey("MobyTag.MobyTag_Id"), primary_key=True, nullable=False)
    id_zone_identification = Column("SpecimenZoneIdentification_Id", UUID, \
        ForeignKey("SpecimenZoneIdentification.SpecimenZoneIdentification_Id"), primary_key=True, nullable=False)

    from ..moby.tag.mobytag import MobyTag
    tag = relationship(MobyTag)

class SpecimenZoneIdentification(Base):
    VAR_INVENTORY_NUMBER = 'inventory_number'
    VAR_MOBYCLE = 'mobycle'
    VAR_OTHER_NUMBERS = 'other_numbers'

    VAR_ON_LABEL = t_autre_numero.VAR_ON_LABEL
    VAR_ON_NUMBER = t_autre_numero.VAR_ON_NUMBER

    # définition de table
    __tablename__ = "SpecimenZoneIdentification"

    id = Column("SpecimenZoneIdentification_Id", UUID, \
        ForeignKey("Specimen.Specimen_ZoneIdentification_Id"), primary_key=True, nullable=False, default=uuid.uuid4)

    numero_inventaire = Column("SpecimenZoneIdentification_NumeroInventaire", String(200), nullable=True)
    numero_depot = Column("SpecimenZoneIdentification_NumeroDepot", String(200), nullable=True)
    numero_inventaire_deposant = Column("SpecimenZoneIdentification_NumeroInventaireDeposant", String(200), nullable=True)
    id_date_inscription_registre_inventaire = Column("SpecimenZoneIdentification_DateInscriptionRegistreInventaire_Id", UUID, nullable=True)
    nombre_parties = Column("SpecimenZoneIdentification_NombreParties", INTEGER, nullable=True)
    nombre_specimens = Column("SpecimenZoneIdentification_NombreSpecimens", INTEGER, nullable=True)
    existence_sous_inventaire = Column("SpecimenZoneIdentification_ExistenceSousInventaire", INTEGER, nullable=True)
    observations_reference = Column("SpecimenZoneIdentification_ObservationsReference", String, nullable=True)
    notes = Column("SpecimenZoneIdentification_Notes", String, nullable=True)
    moby_cle = Column("SpecimenZoneIdentification_MobyCle", String(201), nullable=True)
    
    id_specimen = Column("SpecimenZoneIdentification_Specimen_Id", UUID, ForeignKey("Specimen.Specimen_Id"), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # liaisons
    #specimen = relationship("Specimen", foreign_keys=[id_specimen], back_populates='zone_identification', post_update=True)
    
    # we never change this list direcly, set as viewonly
    autres_numeros = relationship(t_autre_numero, order_by=t_autre_numero.ordre, back_populates="zone_identification")
    tags = relationship("MobyTag_Specimen_SpecimenZoneIdentification_MobyTag")

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = self.id
         
        data['numero_inventaire'] = self.numero_inventaire
        data['numero_depot'] = self.numero_depot
        data['numero_inventaire_deposant'] = self.numero_inventaire_deposant
        data['date_inscription_registre_inventaire'] = self.id_date_inscription_registre_inventaire # TODO
        data['autres_numeros'] = json_loop(self.autres_numeros)
        data['nombre_parties'] = self.nombre_parties
        data['nombre_specimens'] = self.nombre_specimens
        data['existence_sous_inventaire'] = self.existence_sous_inventaire
        data['observations_reference'] = self.observations_reference
        data['notes'] = self.notes
        data['moby_cle'] = self.moby_cle    
        data['tags'] = json_tags(self.tags)

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
            log.info("%s - create - %s"%(_cln, data))
        zi = cls()
        zi.t_creation_user = text("(USER)")
        zi.t_write_user = text("(USER)")
        if data:
            up = zi._update(data, db)
            if not up:
                return False
        return zi

    def update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - _update - %s"%(_cln, data))
        return self._update(data, db)


    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - _update - %s"%(_cln, data))
        
        updated = False

        inum = data.get(self.VAR_INVENTORY_NUMBER, None)
        if not inum:
            log.error("%s - _upcate - missing %s"%(_cln, self.VAR_INVENTORY_NUMBER))
            return False
        if self.numero_inventaire!=inum:
            self.numero_inventaire = inum
            updated = True
        elif DEBUG:
            log.info("%s - _update - numero_inventaire already set properly"%(_cln))

        mobycle = data.get(self.VAR_MOBYCLE, None)
        if not mobycle:
            log.error("%s _update | missing '%s'"%(_cln, self.VAR_MOBYCLE))
            return False
        if self.moby_cle != mobycle:
            self.moby_cle = mobycle
            updated = True
        elif DEBUG:
            log.info("%s _update | '%s' wasn't changed"%(_cln, self.VAR_MOBYCLE))

        onum = data.get(self.VAR_OTHER_NUMBERS, None)
        if not onum:
            log.info("%s - _update - no other numbers given"%(_cln))
        else:
            if self.autres_numeros:
                log.error("%s - _update - updating other numbers not implemented"%(_cln))
                return False
            else:
                log.info("%s - _update - add other number %s"%(_cln, onum))
                on = t_autre_numero.create(onum, db)
                if on is not None: # we either have an item or False                    
                    if not on:
                        log.error("%s - _update - Unable to create other number")
                        return False
                    on.zone_identification = self
                else:
                    log.info("%s - AutreNumero : nothing to create"%(_cln))
        return True