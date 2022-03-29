import uuid
import logging

from sqlalchemy import (INTEGER, TIMESTAMP, Column, DateTime, ForeignKey,
                        String, select, text)
from sqlalchemy.orm import relationship, column_property

from ..base import UUID, Base, indent, json_loop, json_test, scalar, json_dump
from ..datation.datation import Datation as t_datation
from ..reference.rang_taxonomique import RangTaxonomique as t_rang_taxonomique

log = logging.getLogger(__name__)

DEBUG = True 

class ClassificationZoneIdentification_MobyTag_MobyTag_Classification(Base):
    VAR_TYPE_CLASSIFICATION = "type_classification"

    __tablename__ = "ClassificationZoneIdentification_MobyTag_MobyTag_Classification"

    id_tag = Column("MobyTag_Id", UUID, ForeignKey("MobyTag.MobyTag_Id"), primary_key=True, nullable=False)
    id_zone_identification = Column("ClassificationZoneIdentification_Id", UUID, \
        ForeignKey("ClassificationZoneIdentification.ClassificationZoneIdentification_Id"), primary_key=True, nullable=False)

    from ..moby.tag.mobytag import MobyTag
    tag = relationship(MobyTag)
    tag_name = column_property(scalar(select(MobyTag.tag).where(MobyTag.id==id_tag)))
    zone_identification = relationship("ClassificationZoneIdentification", back_populates='tags')

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['tag'] = json_test(self.tag)
        
        return data

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s - create %s"%(_cln, data))
        t = cls()
        if data:
            up = t._update(data, db)
            if not up:
                return False
        return t

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - _update - %s"%(_cln, data))
        
        class_type = data.get(self.VAR_TYPE_CLASSIFICATION, None)
        if class_type:
            if self.tag:
                log.error("%s - _update - Updating tag not yet implemented"%(_cln))
                return False
            self.tag = class_type

        return True


t_classification_tag = ClassificationZoneIdentification_MobyTag_MobyTag_Classification
    

class ClassificationZoneIdentification(Base):
    NOM_AUTRE = "Autre"
    NOM_BOTANIQUE = "Botanique"
    NOM_ZOOLOGIE = "Zoologie"

    TYPES_NOMENCLATURE = [ NOM_AUTRE, NOM_BOTANIQUE, NOM_ZOOLOGIE]

    VAR_NOMENCLATURE = "nomenclature"
    VAR_NOM_SCIENTIFIQUE = "nom_scientifique"
    VAR_TYPE_CLASSIFICATION = "type_classification"


    __tablename__ = "ClassificationZoneIdentification"

    id = Column("ClassificationZoneIdentification_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    # 1. Autre
    # 2. Botanique
    # 3. Zoologie
    id_type_nomenclature = Column("ClassificationZoneIdentification_TypeNomenclature", INTEGER, nullable=False)
    nom = Column("ClassificationZoneIdentification_Nom", String, nullable=True)
    # Datation.Datation_Id
    id_date = Column("ClassificationZoneIdentification_Date_Id", UUID, ForeignKey("Datation.Datation_Id"), nullable=True)
    # Fossile.Reference_Id
    id_fossile = Column("ClassificationZoneIdentification_Fossile_Id", UUID, nullable=True)
    id_rang_taxonomique = Column("ClassificationZoneIdentification_RangTaxonomique_Id", UUID, ForeignKey("RangTaxonomique.Reference_Id"), nullable=True)
    # Classification.Classification_Id
    id_classification_fichier = Column("ClassificationZoneIdentification_ClassificationFichier_Id", UUID, 
        ForeignKey("Classification.Classification_Id"), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    # liaisons
    date = relationship(t_datation, foreign_keys=[id_date])
    rang_taxonomique = relationship(t_rang_taxonomique, foreign_keys=[id_rang_taxonomique])
    classification = relationship("Classification", foreign_keys=[id_classification_fichier], 
        back_populates="zone_identification", post_update=True)                                             # bidi link ok


    # ChampClassificationZoneIdentificationAuteur
    from .champs.auteur import ChampClassificationZoneIdentificationAuteur as t_auteur
    auteurs = relationship(t_auteur, back_populates="zone_identification", order_by="ChampClassificationZoneIdentificationAuteur.ordre")

    # tags
    tags  = relationship(ClassificationZoneIdentification_MobyTag_MobyTag_Classification)

    @property
    def type_nomenclature(self):
        if self.id_type_nomenclature in range(1, len(self.TYPES_NOMENCLATURE) + 1):
            return self.TYPES_NOMENCLATURE[self.id_type_nomenclature - 1]
        else:
            return "UNKNOWN"

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        type_nomenclature = {}
        type_nomenclature['id'] = str(self.id_type_nomenclature)
        type_nomenclature['name'] = self.type_nomenclature
        data['type_nomenclature'] = type_nomenclature

        data['nom'] = self.nom
        data['date'] = json_test(self.date)
        data['id_fossile'] = str(self.id_fossile)
        data['rang_taxonomique'] = json_test(self.rang_taxonomique)
        data['auteurs'] = json_loop(self.auteurs)

        data['tags'] = json_loop(self.tags)

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
        zi = cls()
        zi.t_write_user = text("(USER)")
        zi.t_creation_user = text("(USER)")
        if data:
            up = zi._update(data, db)
            if not up:
                return False
        return zi 

    def _find_tag(self, tag):
        log.info("looking for %s"%(tag.id))
        for t in self.tags:
            log.info("    %s"%(t.id_tag))
            if t.id_tag==tag.id:
                return t
        return None 

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        updated = False

        nomenclature = data.get(self.VAR_NOMENCLATURE, None).strip()
        if nomenclature:
            if nomenclature not in self.TYPES_NOMENCLATURE:
                log.error("%s - _update - unknown nomenclature '%s'"%(_cln, nomenclature))
                return False
            id_nom = self.TYPES_NOMENCLATURE.index(nomenclature) + 1
            if self.id_type_nomenclature!=id_nom:
                if DEBUG:
                    log.info("%s - _update - updating id_type_nomenclature from %s to %s"%(_cln, self.id_type_nomenclature, id_nom))
                self.id_type_nomenclature = id_nom
                updated = True
        
        nom = data.get(self.VAR_NOM_SCIENTIFIQUE, None).strip()
        if nom:
            if self.nom!=nom:
                self.nom = nom
                updated = True

        class_type = data.get(self.VAR_TYPE_CLASSIFICATION, None)
        if class_type:
            tag_data = { self.VAR_TYPE_CLASSIFICATION: class_type, }
            t = self._find_tag(class_type)
            if not t:
                t = t_classification_tag.create(data, db)
                t.zone_identification = self
                updated = True
        
        if updated:
            self.t_write = text("(getdate())")
            self.t_write_user = text("(USER)")

        return True
