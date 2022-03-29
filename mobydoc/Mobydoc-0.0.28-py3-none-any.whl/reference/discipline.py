import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text, select)
from sqlalchemy.orm import relationship, column_property

from ..base import UUID, Base, indent, json_test, scalar
from .reference import Reference as t_reference
from .reference import ReferenceZoneGenerale as t_reference_zone_generale

log = logging.getLogger(__name__)

DEBUG = True

class Discipline(Base):
    # table definitions
    __tablename__ = "Discipline"

    id = Column("Reference_Id", UUID, ForeignKey("Reference.Reference_Id"), primary_key=True, nullable=False, default=uuid.uuid4)
    id_zone_contexte = Column("Discipline_ZoneContexte_Id", UUID, ForeignKey("DisciplineZoneContexte.DisciplineZoneContexte_Id"), nullable=True)

    # liaisons
    reference = relationship(t_reference, foreign_keys=[id])
    zone_contexte = relationship("DisciplineZoneContexte", foreign_keys=[id_zone_contexte], post_update=True)

    label = column_property(scalar(\
        select(t_reference_zone_generale.libelle).join(t_reference).where(t_reference.id==id)))

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['reference'] = json_test(self.reference)
        data['zone_contexte'] = json_test(self.zone_contexte)

        return data

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s == | '%s' '%s'"%(_cln, self.reference.label, other))
        return self.reference.label == other

    @classmethod
    def find(cls, data, db):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s find | '%s'"%(_cln, data))
        if not db:
            log.error("%s find | no db specified"%(_cln))
            return None
        d = db.query(cls).where(cls.label==data)
        d_nb = d.count()
        if d_nb == 0:
            log.error("%s find | found no ref for '%s'"%(_cln, data))
            return None
        if d_nb == 1:
            return d.first()
        log.error("%s find | too many refs %d"%(_cln, d_nb))
        return None


class DisciplineZoneContexte(Base):
    __tablename__ = "DisciplineZoneContexte"

    id = Column("DisciplineZoneContexte_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    
    id_discipline_fichier = Column("DisciplineZoneContexte_DisciplineFichier_Id", UUID, nullable=True)
    id_parent = Column("DisciplineZoneContexte_Parent_Id", UUID, nullable=True)
    id_voir = Column("DisciplineZoneContexte_Voir_Id", UUID, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = self.id

        data['id_discipline_fichier'] = self.id_discipline_fichier
        data['id_parent'] = self.id_parent
        data['id_voir'] = self.id_voir

        data['t_write'] = self.t_write.isoformat()
        data['t_creation'] = self.t_creation.isoformat()
        data['t_write_user'] = self.t_write_user
        data['t_creation_user'] = self.t_creation_user

        return data

    @property
    def xml(self):
        s = "<%s id=\"%s\">\n"%(self.__class__.__name__, self.id)
        
        s+= "</%s>\n"%(self.__class__.__name__)
        return s

