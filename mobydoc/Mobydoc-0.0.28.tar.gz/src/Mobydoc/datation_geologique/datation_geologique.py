import logging
import uuid

from sqlalchemy import TIMESTAMP, Column, DateTime, ForeignKey, String, text
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_test, json_dump
from .zone_generale import DatationGeologiqueZoneGenerale as t_zone_generale

log = logging.getLogger(__name__)

DEBUG = True

class DatationGeologique(Base):
    __tablename__ = "DatationGeologique"

    id = Column("DatationGeologique_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    
    id_zone_generale = Column("DatationGeologique_ZoneGenerale_Id", UUID, ForeignKey(t_zone_generale.id), nullable=False)
    from .zone_contexte import \
        DatationGeologiqueZoneContexte as t_zone_contexte
    id_zone_contexte = Column("DatationGeologique_ZoneContexte_Id", UUID, ForeignKey(t_zone_contexte.id), nullable=True)

    #from .zone_informations_systeme import DatationGeologiqueZoneInformationsSysteme as t_zone_informations_systeme
    #id_zone_informations_systeme = Column("DatationGeologique_ZoneInformationsSysteme_Id", UUID, ForeignKey(t_zone_informations_systeme.id), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # liaisons
    zone_generale = relationship(t_zone_generale, foreign_keys=[id_zone_generale])
    zone_contexte = relationship(t_zone_contexte, foreign_keys=[id_zone_contexte])
    #zone_informations_systeme = relationship(t_zone_informations_systeme, foreign_keys=[id_zone_informations_systeme])

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['zone_generale'] = json_test(self.zone_generale)
        data['zone_contexte'] = json_test(self.zone_contexte)
        #data['zone_informations_systeme'] = json_test(self.zone_informations_systeme)

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
            log.info("%s - find - looking for '%s'"%(_cln, data))
        dg = db.query(cls).join(t_zone_generale, cls.id==t_zone_generale.id_datation_geologique).\
            filter(t_zone_generale.datation_geologique==data)
        dg_c = dg.count()
        if dg_c == 0:
            return None
        elif dg_c == 1:
            return dg.first()
        else:
            log.error("%s - find - too many records found for '%s'(%d)"%(_cln, data, dg_c))
            return False

    @classmethod
    def create(cls, dg_name):
        _cln = cls.__name__
        if DEBUG:
            log.info("%s - create '%s'"%(_cln, dg_name))
        dg = cls()
        dg.t_creation_user = text("(USER)")
        dg.t_write_user = text("(USER)")
        if dg_name:
            up = dg._update(dg_name)
            if not up:
                return False
        return dg

        #    zone_generale = t_zone_generale()
        #     zone_generale.datation_geologique = dg_name

    def _update(self, dg_name):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s - _update '%s'"%(_cln, dg_name))

        if not self.zone_generale:
            zg = t_zone_generale.create(dg_name)
            self.zone_generale = zg
        else:
            log.error("%s - _update - updating not implemented"%(_cln))
            return False
        
        return True

