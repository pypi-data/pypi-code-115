import uuid

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, func, select,
                        text)
from sqlalchemy.orm import column_property, relationship

from ..base import UUID, Base, indent, json_test, scalar

class AutreNumero(Base):
    # table definitions
    __tablename__ = "AutreNumero"


    id = Column("Reference_Id", UUID, ForeignKey("Reference.Reference_Id"), primary_key=True, nullable=False, default=uuid.uuid4)
    id_zone_contexte = Column("AutreNumero_ZoneContexte_Id", UUID, ForeignKey("AutreNumeroZoneContexte.AutreNumeroZoneContexte_Id"), nullable=True)

    # liaisons
    from .reference import Reference as t_reference
    reference = relationship(t_reference, foreign_keys=[id])
    zone_contexte = relationship("AutreNumeroZoneContexte", foreign_keys=[id_zone_contexte], post_update=True)

    from .reference import ReferenceZoneGenerale as t_reference_zone_generale
    label = column_property(scalar(\
        select(t_reference_zone_generale.libelle).join(t_reference).where(t_reference.id==id)))

    # @property
    # def label(self):
    #     return self.reference.label if self.reference else None

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['reference'] = json_test(self.reference)
        data['zone_contexte'] = json_test(self.zone_contexte)

        return data

    def check(self):
        _cln = self.__class__.__name__ 
        self.reference.check()

class AutreNumeroZoneContexte(Base):
    __tablename__ = "AutreNumeroZoneContexte"

    id = Column("AutreNumeroZoneContexte_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    
    id_autre_numero_fichier = Column("AutreNumeroZoneContexte_AutreNumeroFichier_Id", UUID, nullable=True)
    id_parent = Column("AutreNumeroZoneContexte_Parent_Id", UUID, nullable=True)
    id_voir = Column("AutreNumeroZoneContexte_Voir_Id", UUID, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['id_autre_numero_fichier'] = self.id_autre_numero_fichier
        data['id_parent'] = self.id_parent
        data['id_voir'] = self.id_voir

        data['t_write'] = self.t_write.isoformat() if self.t_write else None
        data['t_creation'] = self.t_creation.isoformat() if self.t_creation else None
        data['t_write_user'] = self.t_write_user
        data['t_creation_user'] = self.t_creation_user

        return data
