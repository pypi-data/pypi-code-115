import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ....base import UUID, Base, indent, json_test, json_dump
from ....provenance.provenance import Provenance as t_provenance

log = logging.getLogger(__name__)

DEBUG = True


class ChampSpecimenZoneCollecteProvenance(Base):
    VAR_PROVENANCE = 'provenance'

    # définition de table
    __tablename__ = "ChampSpecimenZoneCollecteProvenance"

    id = Column("ChampSpecimenZoneCollecteProvenance_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_zone_collecte = Column("ChampSpecimenZoneCollecteProvenance_SpecimenZoneCollecte_Id", UUID, \
        ForeignKey("SpecimenZoneCollecte.SpecimenZoneCollecte_Id"), nullable=True)
    id_provenance = Column("ChampSpecimenZoneCollecteProvenance_Provenance_Id", UUID, ForeignKey(t_provenance.id), nullable=True)
    ordre = Column("ChampSpecimenZoneCollecteProvenance_Ordre", INTEGER, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    #
    # Links
    # 

    zone_collecte = relationship("SpecimenZoneCollecte", foreign_keys=[id_zone_collecte], back_populates='provenances')
    provenance = relationship(t_provenance, foreign_keys=[id_provenance])

    #
    # external links
    #

    # 
    # generate json representation
    # 

    @property
    def tree(self):
        return self.provenance.tree

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)
        data['ordre'] = self.ordre

        data['provenance'] = json_test(self.provenance)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - == - %s"%(_cln, other))
        if type(other) is self.__class__:
            log.info("%s == | other is same class"%(_cln))
            prov = other.provenance.name_tree
            log.info("%s == | %s"%(_cln, prov))
        else:
            prov = other.get(self.VAR_PROVENANCE, None)
        if prov and type(prov) is list:
            if not self.provenance:
                # we have prov, but no provenance... not equal
                return False
            else:
                nt = self.provenance.name_tree[-len(prov):]
                log.info(nt)
                is_same = prov[-1] == nt[-1]
                log.info("%s == | is_same %s"%(_cln, is_same))
                return is_same
        return False

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__
        if DEBUG:
            log.info("%s - create - %s"%(_cln, data))
        cp = cls()
        cp.t_creation_user = text("(USER)")
        cp.t_write_user = text("(USER)")
        if data:
            up = cp._update(data, db)
            if not up:
                return False
        return cp

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - _update - %s"%(_cln, data))

        provenance = data.get(self.VAR_PROVENANCE, None)
        if provenance:
            if self.provenance:
                log.error("%s - _update - updating provenance is not implemented"%(_cln))
                return False
            else:
                p = t_provenance.find(data, db)
                log.info("%s - _update - found provenance %s"%(_cln, p))
                if p is None:
                    # create a new provenance
                    p = t_provenance.create(data, db)
                if p is False:
                    log.error("%s - _update - unable to find a single provenance"%(_cln))
                    return False
                log.info("%s - _update - setting provenance %s"%(_cln, p))
                self.provenance = p
        
        return True
    
