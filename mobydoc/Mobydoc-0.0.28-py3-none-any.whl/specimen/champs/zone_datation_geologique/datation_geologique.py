import logging
import uuid

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ....base import UUID, Base, indent, json_test, json_dump
from ....datation_geologique.datation_geologique import \
    DatationGeologique as t_datation_geologique

log = logging.getLogger(__name__)

DEBUG = True


class ChampSpecimenZoneDatationGeologiqueDatationGeologique(Base):
    VAR_DATATION_GEOLOGIQUE = 'datation_geologique'

    # définition de table
    __tablename__ = "ChampSpecimenZoneDatationGeologiqueDatationGeologique"

    id = Column("ChampSpecimenZoneDatationGeologiqueDatationGeologique_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_zone_datation_geologique = Column("ChampSpecimenZoneDatationGeologiqueDatationGeologique_SpecimenZoneDatationGeologique_Id", \
        UUID, ForeignKey("SpecimenZoneDatationGeologique.SpecimenZoneDatationGeologique_Id"), nullable=True)
    id_datation_geologique = Column("ChampSpecimenZoneDatationGeologiqueDatationGeologique_DatationGeologique_Id", UUID, \
        ForeignKey(t_datation_geologique.id), nullable=True)
    from ....reference.qualificatif_date import \
        QualificatifDate as t_qualificatif_date
    id_qualificatif_date = Column("ChampSpecimenZoneDatationGeologiqueDatationGeologique_QualificatifDatation_Id", UUID, \
        ForeignKey(t_qualificatif_date.id), nullable=True)
    ordre = Column("ChampSpecimenZoneDatationGeologiqueDatationGeologique_Ordre", INTEGER, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    #
    # Links
    # 

    zone_datation_geologique = relationship("SpecimenZoneDatationGeologique", \
        foreign_keys=[id_zone_datation_geologique], back_populates="datations_geologiques")
    #datation_geologique = relationship(t_datation_geologique, foreign_keys=[id_datation_geologique])
    datation_geologique = relationship(t_datation_geologique, foreign_keys=[id_datation_geologique])
    qualificatif_datation = relationship(t_qualificatif_date, foreign_keys=[id_qualificatif_date])

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
        data['id'] = str(self.id)
        data['ordre'] = self.ordre

        data['datation_geologique'] = json_test(self.datation_geologique)
        data['qualificatif_datation'] = json_test(self.qualificatif_datation)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - == - %s"%(_cln, other))
        if type(other) is not str:
            log.error("%s - == - expected other as str, got %s"%(_cln, type(other)))
            exit(1)
        dg = self.datation_geologique
        if not dg:
            log.error("%s == | no datation_geologique"%(_cln))
            return False
        zg = dg.zone_generale
        if not zg:
            log.error("%s == | no zone_generale"%(_cln))
            return False

        test_value = zg.datation_geologique == other
        if DEBUG:
            log.info("%s == | '%s' | %s"%(_cln, other, test_value))
        return 

    @classmethod
    def create(cls, data=None, db=None):
        if DEBUG:
            log.info("%s - create %s"%(cls.__name__, data))
        zdg = cls()
        zdg.t_creation_user = text("(USER)")
        zdg.t_write_user = text("(USER)")
        if data:
            up = zdg._update(data, db)
            if not up:
                return False
        return zdg

    def _update(self, data, db):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s - _update %s"%(_cln, data))
        
        dg_data = data.get(self.VAR_DATATION_GEOLOGIQUE, None)
        if not dg_data:
            log.error("%s - _update - missing %s data"%(_cln, self.VAR_DATATION_GEOLOGIQUE))
            return False

        if self.datation_geologique:
            log.error("%s - _update - not implemented yet"%(_cln))
            return False
        else:
            dg = t_datation_geologique.find(dg_data, db)
            log.info("%s"%(dg))
            if dg == False:
                log.error("%s - _update - error looking for datation_geologique record '%s'"%(_cln, dg_data))
                # not found, will he created below
                
            if dg:
                log.info("%s - _update - found new record %s"%(_cln, dg))
            else:
                log.info("%s - _update - need to create record for '%s'"%(_cln, dg_data))
                dg = t_datation_geologique.create(dg_data)

            # set datation_geologique as the record either found or created
            self.datation_geologique = dg
        
        return True

