import logging
import uuid
import json

import sqlalchemy
from sqlalchemy import (TIMESTAMP, Column, DateTime, ForeignKey, String,
                        column, func, select, text)
from sqlalchemy.orm import column_property, relationship

from ..base import UUID, Base, indent, json_test, scalar, json_dump
from .zone_contexte import ClassificationZoneContexte as t_zone_contexte
from .zone_identification import ClassificationZoneIdentification as t_zone_identification
from .zone_identification import ClassificationZoneIdentification_MobyTag_MobyTag_Classification as tag_zi

log = logging.getLogger(__name__)

DEBUG = True

class Classification(Base):
    VAR_NOMENCLATURE = t_zone_identification.VAR_NOMENCLATURE
    VAR_NOM_SCIENTIFIQUE = t_zone_identification.VAR_NOM_SCIENTIFIQUE
    VAR_TYPE_CLASSIFICATION = t_zone_identification.VAR_TYPE_CLASSIFICATION

    NOM_AUTRE = t_zone_identification.NOM_AUTRE
    NOM_BOTANIQUE = t_zone_identification.NOM_BOTANIQUE
    NOM_ZOOLOGIE = t_zone_identification.NOM_ZOOLOGIE

    __tablename__ = "Classification"

    id = Column("Classification_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    # ClassificationZoneIdentification.ClassificationZoneIdentification_Id
    id_zone_identification = Column("Classification_ZoneIdentification_Id", UUID, ForeignKey("ClassificationZoneIdentification.ClassificationZoneIdentification_Id"), nullable=False)
    id_zone_donnees_geographiques = Column("Classification_ZoneDonneesGeographiques_Id", UUID, nullable=True)
    id_zone_datation_geologique = Column("Classification_ZoneDatationGeologique_Id", UUID, nullable=True)
    id_zone_protection = Column("Classification_ZoneProtection_Id", UUID, nullable=True)
    id_zone_mot_cle = Column("Classification_ZoneMotCle_Id", UUID, nullable=True)
    # ClassificationZoneContexte.ClassificationZoneContexte_Id
    id_zone_contexte = Column("Classification_ZoneContexte_Id", UUID, ForeignKey("ClassificationZoneContexte.ClassificationZoneContexte_Id"), nullable=True)
    id_zone_informations_systeme = Column("Classification_ZoneInformationsSysteme_Id", UUID, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # liaisons
    zone_identification = relationship(t_zone_identification, foreign_keys=[id_zone_identification])        # bidi link ok
    zone_contexte = relationship(t_zone_contexte, foreign_keys=[id_zone_contexte])

    # for now, gives the zone_contextes to which this classification is a parent
    # we never change this set of items, so this is viewonly
    children_zone_contexte = relationship(t_zone_contexte, primaryjoin=id==t_zone_contexte.id_parent, viewonly=True)

    # query for the number of children of this classification
    nb_children = column_property(scalar(select([func.count(t_zone_contexte.id)])\
        .where(t_zone_contexte.id_parent==id)\
        .correlate_except(t_zone_contexte)))

    # children_b = relationship("Classification", secondary=t_zone_contexte,
    #                         primaryjoin="id==ClassificationZoneContexte.id_parent",
    #                         secondaryjoin="ClassificationZoneContexte.id_classification_fichier==id")

    # @property
    # def nb_children(self):
    #     if self.children_zone_contexte:
    #         return len(self.children_zone_contexte)
    #     return 0

    @property
    def children(self):
        c = []
        for c_zc in self.children_zone_contexte:
            c.append(c_zc.classification)
        return c


    @property
    def parent(self):
        if self.zone_contexte:
            if self.zone_contexte.parent:
                return self.zone_contexte.parent
        return None

    @property
    def parent_name(self):
        if self.zone_contexte and self.zone_contexte.parent:
            return str(self.zone_contexte.parent)
        return ''

    @property
    def tree(self):
        tree_data = []
        if self.zone_contexte and self.zone_contexte.parent:
            tree_data = self.zone_contexte.parent.tree
        tree_data.append(self)
        return tree_data

    @property
    def name_tree(self):
        names = []
        if self.zone_contexte and self.zone_contexte.parent:
            names = self.zone_contexte.parent.name_tree
        if self.zone_identification.nom:
            names.append(self.zone_identification.nom)
        else:
            names.append("(unknown)")
        return names

    @property
    def name_tree_detailed(self):
        names = []
        if self.zone_contexte and self.zone_contexte.parent:
            names = self.zone_contexte.parent.name_tree_detailed
        data = {}
        data['name'] = self.zone_identification.nom
        data['date'] = self.zone_identification.date
        if data['date']:
            data['date'] = str(data['date'])
        authors = []
        for a in self.zone_identification.auteurs:
            author = {}
            author['last_name'] = a.personne.zone_identification.nom
            author['first_name'] = a.personne.zone_identification.prenom
            authors.append(author)
        data['authors'] = authors
        names.append(data)
        return names


    def __str__(self):
        if self.zone_identification.nom:
            return self.zone_identification.nom  
        return '(unknown)'

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['zone_identification'] = json_test(self.zone_identification)
        data['id_zone_donnes_geographiques'] = str(self.id_zone_donnees_geographiques)
        data['id_zone_datation_geologique'] = str(self.id_zone_datation_geologique)
        data['id_zone_protection'] = str(self.id_zone_protection)
        data['id_zone_mot_cle'] = str(self.id_zone_mot_cle)
        data['zone_contexte'] = json_test(self.zone_contexte)
        data['id_zone_informations_systeme'] = str(self.id_zone_informations_systeme)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data

    @classmethod
    def find(cls, data, db):
        _cln = cls.__name__ 

        nom = data.get(cls.VAR_NOM_SCIENTIFIQUE, None)

        if not nom:
            log.error("%s - find - %s not provided"%(_cln, cls.VAR_NOM_SCIENTIFIQUE))
            return False

        nomenclature = data.get(cls.VAR_NOMENCLATURE, None)
        if not nomenclature:
            log.error("%s find | missing nomenclature"%(_cln))
            exit(1)
        if nomenclature not in t_zone_identification.TYPES_NOMENCLATURE:
            log.error("%s find | '%s' not in %s"%(_cln, nomenclature, t_zone_identification.TYPES_NOMENCLATURE))
            exit(1)
        id_nom = t_zone_identification.TYPES_NOMENCLATURE.index(nomenclature) + 1

        c = db.query(cls).join(t_zone_identification).filter(t_zone_identification.nom==nom)
        if c.count() == 0:
            return None
        elif c.count() == 1:
            return c.first()
        else:
            log.error("%s found too many classifications for %s %d"%(_cln, nom, c.count()))
            cl = c.all()
            cl_ok = []
            for c in cl:
                zi = c.zone_identification
                if zi and zi.id_type_nomenclature == id_nom:
                    log.info("%s find | found nomenclature '%s' %s"%(_cln, nomenclature, c))
                    cl_ok.append(c)
                log.info("%s find | '%s' doesn't match '%s'"%(_cln, \
                    t_zone_identification.TYPES_NOMENCLATURE[zi.id_type_nomenclature -1], \
                    nomenclature))

            log.info("%s find | cl_ok %s"%(_cln, cl_ok))
            if len(cl_ok) == 0:
                return None
            elif len(cl_ok) == 1:
                return cl_ok[0]
            else:
                return False

    @classmethod
    def create(cls, data=None, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s - create %s"%(_cln, data))
        c = cls()
        c.t_creation_user = text("(USER)")
        c.t_write_user = text("(USER)")
        if data:
            up = c._update(data, db)
            if not up:
                return False
        return c

    def check(self):
        _cln = self.__class__.__name__
        if self.zone_identification:
            if self.zone_identification.classification != self:
                if DEBUG:
                    log.info("%s check | fixing link to zone_identification to '%s'"%(_cln, self.id))
                self.zone_identification.classification = self
            elif DEBUG:
                log.info("%s check | all clear"%(_cln))
        elif DEBUG:
            log.info("%s check | no zone_identification")

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        
        if self.zone_identification:
            log.error("%s - _update - updating zone identification not implemented"%(_cln))
            return False
        else:
            zi = t_zone_identification.create(data, db)
            if not zi:
                log.error("%s - _update - error creating new zone_identification"%(_cln))
                return False
            zi.classification = self
        return True
