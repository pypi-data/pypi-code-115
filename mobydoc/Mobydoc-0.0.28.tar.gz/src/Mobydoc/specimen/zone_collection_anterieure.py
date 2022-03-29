import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_loop, json_test, json_dump
from ..reference.type_information import TypeInformation
from ..personne.personne import Personne as t_personne

log = logging.getLogger(__name__)

DEBUG = True


class SpecimenZoneCollectionAnterieure(Base):
    # définition de table
    __tablename__ = "SpecimenZoneCollectionAnterieure"

    id = Column("SpecimenZoneCollectionAnterieure_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    id_specimen = Column("SpecimenZoneCollectionAnterieure_Specimen_Id", UUID, ForeignKey("Specimen.Specimen_Id"), nullable=True)

    id_type_collection_anterieure = Column("SpecimenZoneCollectionAnterieure_TypeCollectionAnterieure_Id", UUID, nullable=True)
    id_collection_anterieure = Column("SpecimenZoneCollectionAnterieure_CollectionAnterieure_Id", UUID, ForeignKey(t_personne.id), nullable=True)
    id_vente_publique = Column("SpecimenZoneCollectionAnterieure_VentePublique_Id", UUID, nullable=True)
    id_lieu = Column("SpecimenZoneCollectionAnterieure_Lieu_Id", UUID, nullable=True)

    notes = Column("SpecimenZoneCollectionAnterieure_Notes", String, nullable=True)
    ordre = Column("SpecimenZoneCollectionAnterieure_Ordre", INTEGER, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # 
    # relationships
    #

    specimen = relationship("Specimen", foreign_keys=[id_specimen], back_populates="zones_collections_anterieures")
    collection_anterieure = relationship(t_personne, foreign_keys=[id_collection_anterieure])

    #
    # object properties
    #

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)
        data['ordre'] = self.ordre

        data['id_type_collection_anterieure'] = self.id_type_collection_anterieure
        data['collection_anterieure'] = json_test(self.collection_anterieure)
        data['id vente_publique'] = self.id_vente_publique
        data['id_lieu'] = self.id_lieu

        data['notes'] = self.notes

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s == | '%s'"%(_cln, other))
        if type(other) == self.__class__:
            log.info("%s == | same type")
            other = other.collection_anterieure
        return self.collection_anterieure == other

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s create | %s"%(_cln, data))
        zca = cls()
        zca.t_creation_user = text("(USER)")
        zca.t_write_user = text("(USER)")
        if data:
            up = zca._update(data, db)
            if not up:
                log.error("%s create | error updating zone_collection_anterieure"%(_cln))
                return False
        return zca

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s _update | %s"%(_cln, data))
        if type(data) is str:
            data = { t_personne.VAR_NOM: data }
        p = t_personne.find(data, db)
        log.info("%s _update | %s"%(_cln, p))
        if p == False:
            log.error("%s _update | error looking for '%s'"%(_cln, data))
            return False
        if not p:
            log.error("%s _update | unable to find '%s'"%(_cln, data))
            p = t_personne.create(data, db)
            if not p:
                log.error("%s _update | unable to create personne record with '%s'"%(_cln, data))
                return False
        log.info("%s _update | setting collection_anterieure with %s"%(_cln, p))
        self.collection_anterieure = p
        return True

