import logging
import uuid

from sqlalchemy import (TIMESTAMP, Column, DateTime, ForeignKey, String, Table,
                        text, select)
from sqlalchemy.orm import backref, relationship, column_property

from ..base import UUID, Base, indent, json_tags, json_test, json_dump, scalar
from ..moby.tag.mobytag import MobyTag as t_tag

log = logging.getLogger(__name__)
DEBUG = False

class MobyTag_Personne_PersonneZoneIdentification_MobyTag(Base):
    __tablename__ = "MobyTag_Personne_PersonneZoneIdentification_MobyTag"

    id_tag = Column("MobyTag_Id", UUID, ForeignKey("MobyTag.MobyTag_Id"), primary_key=True, nullable=False)
    id_zone_identification = Column("PersonneZoneIdentification_Id", UUID, ForeignKey("PersonneZoneIdentification.PersonneZoneIdentification_Id"), primary_key=True, nullable=False)

    tag = relationship(t_tag)
    zone_identification = relationship("PersonneZoneIdentification", back_populates="tags")

    tag_name = column_property(scalar(select(t_tag.tag).where(t_tag.id==id_tag)))

t_tags = MobyTag_Personne_PersonneZoneIdentification_MobyTag


class PersonneZoneIdentification(Base):
    VAR_PRENOM = 'prenom'
    VAR_NOM = 'nom'
    VAR_TAGS = 'tags'

    __tablename__ = "PersonneZoneIdentification"

    id = Column("PersonneZoneIdentification_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_type_personne = Column("PersonneZoneIdentification_TypePersonne_Id", UUID, nullable=True)
    id_civilite_prefixe = Column("PersonneZoneIdentification_CivilitePrefixe_Id", UUID, nullable=True)
    nom = Column("PersonneZoneIdentification_Nom", String(256), nullable=False)
    prenom = Column("PersonneZoneIdentification_Prenom", String(256), nullable=True)
    complement_nom = Column("PersonneZoneIdentification_ComplementNom", String, nullable=True)
    sexe = Column("PersonneZoneIdentification_Sexe", String(1), nullable=True)
    
    # wtf are those 3 things doing here ??
    numero_adherent = Column("PersonneZoneIdentification_NumeroAdherent", String, nullable=True)
    validite_cotisation = Column("PersonneZoneIdentification_ValiditeCotisation", String, nullable=True)
    id_autorisation_pret = Column("PersonneZoneIdentification_AutorisationPret_Id", UUID, nullable=True)

    # Personne.Personne_Id
    id_personne_fichier = Column("PersonneZoneIdentification_PersonneFichier_Id", UUID, ForeignKey("Personne.Personne_Id"), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    # liaisons
    #import mobydoc.personne.personne as m_personne
    #l_personne = relationship("Personne", foreign_keys=[id_personne_fichier])

    tags = relationship(t_tags)

    @property
    def nom_entier(self):
        nom = []
        if self.prenom:
            nom.append(self.prenom)
        if self.nom: 
            nom.append(self.nom)
        return ' '.join(nom)

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['id_type_personne'] = self.id_type_personne
        data['id_civilite_prefixe'] = self.id_civilite_prefixe
        data['nom'] = self.nom
        data['prenom'] = self.prenom
        data['complement_nom'] = self.complement_nom
        data['sexe'] = self.sexe
        data['numero_adherent'] = self.numero_adherent
        data['validite_cotisation'] = self.validite_cotisation
        data['id_autorisation_pret'] = self.id_autorisation_pret
        data['id_personne_fichier'] = self.id_personne_fichier
        # data['backlink_to_personne'] = (self.l_personne.id_zone_identification == self.id)

        data['tags'] = json_tags(self.tags)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data        

    @property
    def tags_list(self):
        tl = []
        for t in self.tags:
            tl.append(t.tag_name)
        return tl

    def __repr__(self):
        return "nom:'%s',prenom:'%s',tags:%s"%(self.nom, self.prenom, self.tags_list)

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s == | %s '%s'"%(_cln, self, other))
            log.info("%s == | %s"%(_cln, type(other)))
        to = type(other)
        if to is self.__class__:
            nom = other.nom
            prenom = other.prenom
            tags = other.tags_list
        elif to is str:
            nom = other
            prenom = None
            tags = None
        elif to is dict:
            nom = other.get("nom", None)
            prenom = other.get("prenom", None)
            tags = other.get("tags", None)
        else:
            log.error("unhandled type %s"%(to))
            exit(1)
        # compare
        if self.nom:
            if self.nom != nom:
                if DEBUG:
                    log.info("%s == | nom is different, return False"%(_cln))
                return False
            if DEBUG:
                log.info("%s == | nom is the same"%(_cln))
        if self.prenom:
            if self.prenom != prenom:
                if DEBUG:
                    log.info("%s == | prenom is different, return False"%(_cln))
                return False
            if DEBUG:
                log.info("%s == | prenom is the same"%(_cln))
        if DEBUG:
            log.info("%s == | should check tags list, not implemented"%(_cln))
            log.info("%s == | return True"%(_cln))
        return True   

    @classmethod
    def create(cls, data=None):
        if DEBUG:
            log.info("create %s: %s"%(cls.__name__, data))
        zi = cls()
        zi.t_creation_user = text("(USER)")
        zi.t_write_user = text("(USER)")
        if data:
            up = zi._update(data)
            if not up:
                return False
        return zi

    def update(self, data):
        if DEBUG:
            log.info("update %s: %s"%(self.__class__.__name__, data))
        return self._update(data)

    def _update(self, data):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("_update %s: %s"%(_cln, data))

        prenom = data.get(self.VAR_PRENOM, None)
        if self.prenom != prenom:
            self.prenom = prenom

        nom = data.get(self.VAR_NOM, None)
        if self.nom != nom:
            self.nom = nom

        if DEBUG:
            log.info("%s _update | not handling tags at the moment"%(_cln))

        if DEBUG:
            log.info("%s - updated successfully"%(_cln))
        return True       
