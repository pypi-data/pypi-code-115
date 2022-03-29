import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_loop, json_test, json_dump

from .zone_identification import ProvenanceZoneIdentification as t_zone_identification

log = logging.getLogger(__name__)

DEBUG = True

class Provenance(Base):
    VAR_PROVENANCE = 'provenance'
    VAR_TYPE_SITE = 'type_site'

    # définition de table
    __tablename__ = "Provenance"

    id = Column("Provenance_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_zone_identification = Column("Provenance_ZoneIdentification_Id", UUID, ForeignKey(t_zone_identification.id), nullable=False)

    from .zone_description import ProvenanceZoneDescription as t_zone_description
    id_zone_description = Column("Provenance_ZoneDescription_Id", UUID, ForeignKey(t_zone_description.id), nullable=False)

    from .zone_contexte import ProvenanceZoneContexte as t_zone_contexte
    id_zone_contexte = Column("Provenance_ZoneContexte_Id", UUID, ForeignKey(t_zone_contexte.id), nullable=False)

    from .zone_informations_systeme import ProvenanceZoneInformationsSysteme as t_zone_informations_systeme
    id_zone_informations_systeme = Column("Provenance_ZoneInformationsSysteme_Id", UUID, ForeignKey(t_zone_informations_systeme.id), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    #
    #
    #

    zone_identification = relationship(t_zone_identification, foreign_keys=[id_zone_identification])
    zone_description = relationship(t_zone_description, foreign_keys=[id_zone_description])
    zone_contexte = relationship(t_zone_contexte, foreign_keys=[id_zone_contexte])
    zone_informations_systeme = relationship(t_zone_informations_systeme, foreign_keys=[id_zone_informations_systeme])

    #
    # we never change this list directly, set as viewonly
    #

    from .zone_bibliographie import ProvenanceZoneBibliographie as t_zone_bibliographie
    zones_bibliographie = relationship(t_zone_bibliographie, order_by=t_zone_bibliographie.ordre, viewonly=True)    


    #
    # we never change this list directly, set as viewonly
    #

    children_zone_contexte = relationship(t_zone_contexte, primaryjoin=id==t_zone_contexte.id_parent, viewonly=True)
    
    @property
    def children(self):
        c = []
        for c_zc in self.children_zone_contexte:
            c.append(c_zc.provenance_obj)
        return c
    
    @property
    def types(self):
        zi = self.zone_identification
        if zi:
            return zi.tags_list
        return None
    
    @property
    def tree(self):
        names = []
        if self.zone_contexte and self.zone_contexte.parent_obj:
            names = self.zone_contexte.parent_obj.tree

        data = {}
        if self.zone_identification:
            data['name'] = self.zone_identification.lieu
            data['label'] = self.zone_identification.label
            data['tags'] = self.zone_identification.tags_list
        names.append(data)
        return names

    @property
    def name_tree(self):
        names = []
        if self.zone_contexte and self.zone_contexte.parent_obj:
            names = self.zone_contexte.parent_obj.name_tree
        if self.zone_identification.lieu:
            names.append(self.zone_identification.lieu)
        else:
            names.append("(unknown)")
        return names

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['zone_identification'] = json_test(self.zone_identification)
        data['zone_description'] = json_test(self.zone_description)
        data['zones_bibliographie'] = json_loop(self.zones_bibliographie)
        data['zone_contexte'] = json_test(self.zone_contexte)
        data['zone_informations_systeme'] = json_test(self.zone_informations_systeme)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data

    @classmethod
    def find(cls, data, db):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s - find - %s"%(_cln, data))
        if not data:
            log.error("%s - find - data missing")
            return False
        
        provenance = data.get(cls.VAR_PROVENANCE, None)
        if type(provenance) is not list:
            # do something with provenance 
            log.error("%s - find - %s should be a list"%(_cln, cls.VAR_PROVENANCE))
            return False

        prov = provenance[-1]
        log.info("%s - find - looking for '%s'"%(_cln, prov))
        p = db.query(cls).\
            join(t_zone_identification, cls.id==t_zone_identification.id_provenance).\
            filter(t_zone_identification.lieu==prov)

        p_nb = p.count()
        log.info("%s - find - found %d provenances"%(_cln, p_nb))
        
        if p_nb == 0:
            return None
        if p_nb == 1:
            return p.first()

        # multiple solutions, look for the correct tag
        
        type_site = data.get(cls.VAR_TYPE_SITE, None)
        log.error("%s - find - multiple provenances found - not implemented"%(_cln))
        return False

    @classmethod
    def create(cls, data, db):
        _cln = cls.__name__
        if DEBUG:
            log.info("%s create | %s"%(_cln, data))
        p = cls()
        p.t_creation_user = text("(USER)")
        p.t_write_user = text("(USER)")
        if data:
            up = p._update(data, db)
            if not up:
                log.error("%s create | error creating new provenance")
                return False
        return p
 
    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s _update | %s"%(_cln, data))
        if not data:
            log.error("%s _update | missing data")
            return False
        if not db:
            log.error("%s _update | missing db"%(_cln))
            return False
        
        provenance = data.get(self.VAR_PROVENANCE, None)
        if not provenance:
            log.error("%s _update | missing %s"%(_cln, self.VAR_PROVENANCE))
            return False
        p0 = provenance[-1]
        parents = provenance[:-1]

        tags = data.get(self.VAR_TYPE_SITE, None)
        if not tags:
            log.error("%s _update | missing %s"%(_cln, self.VAR_TYPE_SITE))
            return False
        if type(tags) is not list:
            tags = [ tags ]
        if self.zone_identification:
            log.info("%s _update | updating existing provenance not implemented"%(_cln))
            return False
        else:
            log.info("%s _update | setting '%s'('%s') as provenance"%(_cln, p0, tags))
            zi_data = { t_zone_identification.VAR_LIEU: p0, t_zone_identification.VAR_TAGS: tags}
            zi = t_zone_identification.create(zi_data, db)
            if not zi:
                log.error("%s _update | unable to create zone_identification")
                return False
            self.zone_identification = zi

        log.info("%s _update | take care of parents %s"%(_cln, parents))

        return True