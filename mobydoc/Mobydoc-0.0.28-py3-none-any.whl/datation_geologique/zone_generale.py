import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_tags, json_dump

log = logging.getLogger(__name__)

DEBUG = True


class DatationGeologiqueZoneGenerale_MobyTag_MobyTag_DatationGeologique(Base):
    __tablename__ = "DatationGeologiqueZoneGenerale_MobyTag_MobyTag_DatationGeologique"

    id_tag = Column("MobyTag_Id", UUID, ForeignKey("MobyTag.MobyTag_Id"), primary_key=True, nullable=False)
    id_datation_geologique = Column("DatationGeologiqueZoneGenerale_Id", UUID, \
        ForeignKey("DatationGeologiqueZoneGenerale.DatationGeologiqueZoneGenerale_Id"), primary_key=True, nullable=False)

    from ..moby.tag.mobytag import MobyTag
    tag = relationship(MobyTag)


class DatationGeologiqueZoneGenerale(Base):
    __tablename__ = "DatationGeologiqueZoneGenerale"

    id = Column("DatationGeologiqueZoneGenerale_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    id_datation_geologique = Column("DatationGeologiqueZoneGenerale_DatationGeologiqueFichier_Id", UUID, \
        ForeignKey("DatationGeologique.DatationGeologique_Id"), nullable=True)

    datation_geologique = Column("DatationGeologiqueZoneGenerale_DatationGeologique", String(50), nullable=True)
    note_application = Column("DatationGeologiqueZoneGenerale_NoteApplication", String, nullable=True)
    
    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    #t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    #
    # internal links
    #

    datation_geologique_obj = relationship("DatationGeologique", foreign_keys=[id_datation_geologique])

    # 
    # external links
    # 

    tags = relationship(DatationGeologiqueZoneGenerale_MobyTag_MobyTag_DatationGeologique)

    #
    # dumps json
    #

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['datation_geologique'] = self.datation_geologique
        data['note_application'] = self.note_application
        
        data['tags'] = json_tags(self.tags)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        #data['t_version'] = self.t_version.hex()

        return data

    @classmethod
    def create(cls, data):
        _cln = cls.__name__
        if DEBUG:
            log.info("%s - create '%s'"%(_cln, data))
        
        zg = cls()
        zg.t_creation_user = text("(USER)")
        zg.t_write_user = text("(USER)")
        if data:
            up = zg._update(data)
            if not up:
                return False
        return zg

    def _update(self, data):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s - _update '%s'"%(_cln, data))

        if self.datation_geologique != data:
            self.datation_geologique = data

        return True