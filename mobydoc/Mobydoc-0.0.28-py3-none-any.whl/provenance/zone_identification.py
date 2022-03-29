import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, Float, ForeignKey, String, text, select)
from sqlalchemy.orm import relation, relationship, column_property

from ..base import UUID, Base, indent, json_loop, json_tags, json_test, json_dump, scalar
from ..utilities import listGenUpdates
from ..moby.tag.mobytag import MobyTag as t_tag

log = logging.getLogger(__name__)

DEBUG = True

class MobyTag_Provenance_ProvenanceZoneIdentification_MobyTag(Base):
    __tablename__ = "MobyTag_Provenance_ProvenanceZoneIdentification_MobyTag"

    id_tag = Column("MobyTag_Id", UUID, ForeignKey("MobyTag.MobyTag_Id"), primary_key=True, nullable=False)
    id_zone_identification = Column("ProvenanceZoneIdentification_Id", UUID, ForeignKey("ProvenanceZoneIdentification.ProvenanceZoneIdentification_Id"), primary_key=True, nullable=False)

    tag = relationship(t_tag)
    zone_identification = relationship("ProvenanceZoneIdentification", back_populates='tags')

    tag_name = column_property(scalar(select(t_tag.tag).filter(id_tag==t_tag.id)))

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s == | '%s' '%s'"%(_cln, self.tag_name, other))
        if not self.tag:
            return False
        return self.tag_name == other

    @classmethod
    def create(cls, data, db):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s create | '%s'"%(_cln, data))
        t = cls()
        if data:
            up = t._update(data, db)
            if not up:
                log.error("%s create | unable to create tag"%(_cln))
                return False
        return t

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s create | '%s'"%(_cln, data))
        t = db.query(t_tag).filter(t_tag.tag==data)
        t_nb = t.count()
        log.info("%s _update | found %d tag records"%(_cln, t_nb))
        if t_nb == 1:
            t = t.first()
            log.info("%s _update | found tag %s '%s'"%(_cln, t, t.tag))
            self.tag = t
        elif t_nb == 0:
            log.info("%s _update | can't find tag '%s' - need create"%(_cln, data))
            return False
        else:
            log.info("%s _update | found too many tag records for '%s' (%d)"%(_cln, data, t_nb))
            return False
        return True



t_tags = MobyTag_Provenance_ProvenanceZoneIdentification_MobyTag

class ProvenanceZoneIdentification(Base):
    VAR_LIEU = 'lieu'
    VAR_TAGS = 'tags'

    # définition de table
    __tablename__ = "ProvenanceZoneIdentification"

    id = Column("ProvenanceZoneIdentification_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    lieu = Column("ProvenanceZoneIdentification_Lieu", String(50), nullable=False)
    from ..reference.qualificatif_lieu import QualificatifLieu as t_qualificatif_lieu
    id_qualificatif_lieu = Column("ProvenanceZoneIdentification_QualificatifLieu_Id", UUID, ForeignKey(t_qualificatif_lieu.id), nullable=True)
    from ..reference.type_site import TypeSite as t_type_site
    id_type_site = Column("ProvenanceZoneIdentification_TypeSite_Id", UUID, ForeignKey(t_type_site.id), nullable=True)
    from ..reference.statut_collecte import StatutCollecte as t_statut_collecte
    id_statut_collecte = Column("ProvenanceZoneIdentification_StatutCollecte_Id", UUID, ForeignKey(t_statut_collecte.id), nullable=True)
    notes = Column("ProvenanceZoneIdentification_Notes", String, nullable=True)
    id_provenance = Column("ProvenanceZoneIdentification_ProvenanceFichier_Id", UUID, ForeignKey("Provenance.Provenance_Id"), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    latitude = Column("ProvenanceZoneIdentification_Latitude", Float, nullable=True)
    longitude = Column("ProvenanceZoneIdentification_Longitude", Float, nullable=True)

    #
    #
    #

    provenance_obj = relationship("Provenance", foreign_keys=[id_provenance])
    tags = relationship(t_tags)
    qualificatif_lieu = relationship(t_qualificatif_lieu, foreign_keys=[id_qualificatif_lieu])
    type_site = relationship(t_type_site, foreign_keys=[id_type_site])
    statut_collecte = relationship(t_statut_collecte, foreign_keys=[id_statut_collecte])

    #
    #
    #
    
    from .champs.zone_identification.autres_coordonnees import ChampProvenanceZoneIdentificationAutresCoordonnees as t_autres_coordonnees
    autres_coordonnees = relationship(t_autres_coordonnees, back_populates='zone_identification', order_by=t_autres_coordonnees.ordre)

    #
    #
    #

    @property
    def label(self):
        return self.qualificatif_lieu

    @property
    def tags_list(self):
        tl = []
        for t in self.tags:
            tl.append(t.tag_name)
        return tl

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['tags'] = json_tags(self.tags)
        data['lieu'] = self.lieu
        data['qualificatif_lieu'] = json_test(self.qualificatif_lieu)
        data['latitude'] = self.latitude
        data['longitude'] = self.longitude
        data['autres_coordonnees'] = json_loop(self.autres_coordonnees)
        data['type_site'] = json_test(self.type_site)
        data['statut_collecte'] = json_test(self.statut_collecte)
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
            log.info("%s create | %s"%(_cln, data))
        zi = cls()
        zi.t_creation_user = text("(USER)")
        zi.t_write_user = text("(USER)")
        if data:
            up = zi._update(data, db)
            if not up:
                log.error("%s create | error creating zone_identification"%(_cln))
                return False
        return zi

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s _update | %s"%(_cln, data))
        
        lieu = data.get(self.VAR_LIEU, None)
        if not lieu:
            log.error("%s _update | Missing Lieu '%s'"%(_cln, lieu))
            return False
        if len(lieu) > 50:
            log.error("%s _update | value for Lieu too long, 50 max, got %d"%(_cln, len(lieu)))
            return False
        self.lieu = lieu

        tags = data.get(self.VAR_TAGS, None)
        if not tags:
            log.error("%s _update | missing tags %s"%(_cln, tags))
            return False
        if type(tags) is not list:
            tags = [ tags ]
        if not db:
            log.error("%s _update | missing db"%(_cln))
            return False

        rem, ok, add = listGenUpdates(self.tags, tags)
        log.info("rem : %s"%(rem))
        log.info("ok  : %s"%(ok))
        log.info("add : %s"%(add))

        for t in add:
            nt = t_pzi_tag.create(t, db)
            if not nt:
                log.error("%s _update | unable to create tag '%s'"%(_cln, t))
                return False
            nt.zone_identification = self

        return True