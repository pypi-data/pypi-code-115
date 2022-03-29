import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ....base import UUID, Base, indent, json_test, json_dump
from ....reference.nature_specimen import NatureSpecimen as t_nature_specimen

log = logging.getLogger(__name__)

DEBUG = True

class ChampSpecimenZoneDescriptionPhysiqueNatureSpecimen(Base):
    # définition de table
    __tablename__ = "ChampSpecimenZoneDescriptionPhysiqueNatureSpecimen"

    id = Column("ChampSpecimenZoneDescriptionPhysiqueNatureSpecimen_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_zone_description_physique = Column("ChampSpecimenZoneDescriptionPhysiqueNatureSpecimen_SpecimenZoneDescriptionPhysique_Id", \
        UUID, ForeignKey("SpecimenZoneDescriptionPhysique.SpecimenZoneDescriptionPhysique_Id"), nullable=True)

    id_nature_specimen = Column("ChampSpecimenZoneDescriptionPhysiqueNatureSpecimen_NatureSpecimen_Id", 
        UUID, ForeignKey(t_nature_specimen.id), nullable=True)

    ordre = Column("ChampSpecimenZoneDescriptionPhysiqueNatureSpecimen_Ordre", INTEGER, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)



    #
    # Links
    # 

    zone_description_physique = relationship("SpecimenZoneDescriptionPhysique", 
        foreign_keys=[id_zone_description_physique],
        back_populates='natures_specimen')
    nature_specimen = relationship(t_nature_specimen, foreign_keys=[id_nature_specimen])

    #
    # external links
    #

    # 
    # generate json representation
    # 

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = self.id
        data['ordre'] = self.ordre

        #data['id_caracteristique_physique'] = self.id_nature_specimen
        data['nature_specimen'] = json_test(self.nature_specimen)
        
        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data
        
    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        ns = self.nature_specimen
        if not ns:
            log.info("%s == | no nature_specimen"%(_cln))
            return False
        if ns.label:
            if ns.label==other:
                if DEBUG:
                    log.info("%s == | match '%s' '%s'"%(_cln, ns.label, other))
                return True
            else:
                log.info("%s == | no match '%s' '%s'"%(_cln, ns.label, other))
        else:
            log.info("%s == | no ns.label"%(_cln))
        return False

    @classmethod
    def create(cls, data=None, db=None):
        _cln = cls.__name__
        if DEBUG:
            log.info("%s - create '%s'"%(_cln, data))
        cns = cls()
        cns.t_creation_user = text("(USER)")
        cns.t_write_user = text("(USER)")
        if data:
            up = cns._update(data, db)
            if not up:
                return False
        return cns

    def check(self):
        ns = self.nature_specimen
        if ns:
            ns.check()

    def _update(self, data, db):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s - _update '%s'"%(_cln, data))
        if self.nature_specimen:
            log.error("%s - _update - not implemented"%(_cln))
            return False
        else:
            ns = t_nature_specimen.find(data, db)
            log.info("%s - _update - found %s"%(_cln, ns))
            if ns == False:
                log.error("%s - _update - found too many records for %s"%(_cln, ns))
                return False

            # we couldn't  find the appropriate nature_specimen
            if not ns:
                log.info("creating new ns")
                ns = t_nature_specimen.create(data, db)
                if not ns:
                    log.error("%s - _update - error creating NatureSpecimen reference"%(_cln))
                    return False
            elif DEBUG:
                log.info("%s _update: found nature_specimen '%s'"%(_cln, ns.label))

            self.nature_specimen = ns
        return True