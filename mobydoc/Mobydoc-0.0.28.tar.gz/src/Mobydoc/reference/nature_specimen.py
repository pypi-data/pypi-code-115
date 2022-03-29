import logging
import uuid

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, func, select,
                        text)
from sqlalchemy.orm import column_property, relationship

from ..base import UUID, Base, indent, json_test, scalar
from .reference import Reference, ReferenceZoneGenerale

log = logging.getLogger(__name__)

DEBUG = True

class NatureSpecimen(Base):
    # table definitions
    __tablename__ = "NatureSpecimen"


    id = Column("Reference_Id", UUID, ForeignKey("Reference.Reference_Id"), primary_key=True, nullable=False, default=uuid.uuid4)
    id_zone_contexte = Column("NatureSpecimen_ZoneContexte_Id", UUID, 
        ForeignKey("NatureSpecimenZoneContexte.NatureSpecimenZoneContexte_Id"), nullable=True)

    # liaisons
    from .reference import Reference as t_reference
    reference = relationship(t_reference, foreign_keys=[id])
    zone_contexte = relationship("NatureSpecimenZoneContexte", foreign_keys=[id_zone_contexte], post_update=True)

    from .reference import ReferenceZoneGenerale as t_reference_zone_generale
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

    @classmethod
    def find(cls, label, db):
        ns = db.query(cls).filter(cls.label==label)
        nb_ns = ns.count()
        if nb_ns == 0:
            return None
        elif nb_ns == 1:
            return ns.first()
        else:
            return False

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__
        if DEBUG:
            log.info("%s - create '%s' "%(_cln, data))
        ns = cls()
        if data:
            up = ns._update(data, db)
            if not up:
                return False
        return ns

    def check(self):
        r = self.reference
        if r:
            r.check()

    def _update(self, data, db):
        _cln = self.__class__.__name__
        if self.reference:
            log.error("%s - _update - not implemented"%(_cln))
            return False
        ref_data = {
            Reference.VAR_REFERENCE_TYPE: self.__class__,
            Reference.VAR_LABEL: data,
        }
        self.reference = Reference.create(ref_data, db)
        if not self.reference:
            log.error("%s - _update - error while creating a new reference"%(_cln))
            return False
        return True


class NatureSpecimenZoneContexte(Base):
    __tablename__ = "NatureSpecimenZoneContexte"

    id = Column("NatureSpecimenZoneContexte_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    
    id_nature_specimen_fichier = Column("NatureSpecimenZoneContexte_NatureSpecimenFichier_Id", UUID, nullable=True)
    id_parent = Column("NatureSpecimenZoneContexte_Parent_Id", UUID, nullable=True)
    id_voir = Column("NatureSpecimenZoneContexte_Voir_Id", UUID, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['id_nature_specimen_fichier'] = self.id_nature_specimen_fichier
        data['id_parent'] = self.id_parent
        data['id_voir'] = self.id_voir

        data['t_write'] = self.t_write.isoformat() if self.t_write else None
        data['t_creation'] = self.t_creation.isoformat() if self.t_creation else None
        data['t_write_user'] = str(self.t_write_user) if self.t_write_user is not None else None
        data['t_creation_user'] = str(self.t_creation_user) if self.t_creation_user is not None else None

        return data
