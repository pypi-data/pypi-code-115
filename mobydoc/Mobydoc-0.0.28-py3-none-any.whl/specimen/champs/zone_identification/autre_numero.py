import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ....base import UUID, Base, indent, json_test, json_dump
from ....reference.autre_numero import AutreNumero as t_autre_numero

log = logging.getLogger(__name__)

DEBUG = True

class ChampSpecimenAutreNumero(Base):
    VAR_ON_LABEL = 'label'
    VAR_ON_NUMBER = 'number'

    # définition de table
    __tablename__ = "ChampSpecimenAutreNumero"

    id = Column("ChampSpecimenAutreNumero_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_zone_identification = Column("ChampSpecimenAutreNumero_SpecimenZoneIdentification_Id", UUID, ForeignKey("SpecimenZoneIdentification.SpecimenZoneIdentification_Id"), nullable=True)
    id_autre_numero = Column("ChampSpecimenAutreNumero_AutreNumero_Id", UUID, ForeignKey("AutreNumero.Reference_Id"), nullable=True)
    valeur = Column("ChampSpecimenAutreNumero_Valeur", String(256), nullable=True)
    ordre = Column("ChampSpecimenAutreNumero_Ordre", INTEGER, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    # liaisons
    zone_identification = relationship("SpecimenZoneIdentification", foreign_keys=[id_zone_identification], back_populates="autres_numeros")
    autre_numero = relationship(t_autre_numero, foreign_keys=[id_autre_numero])

    @property
    def label(self):
        return self.autre_numero.label if self.autre_numero else None

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['autre_numero'] = json_test(self.autre_numero)
            
        data['valeur'] = self.valeur
        data['ordre'] = self.ordre

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data      

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s - create - %s"%(_cln, data))
        label = data.get(cls.VAR_ON_LABEL, None)
        if not label:
            log.info("%s - create - no label passed, not creating AutreNumero"%(_cln))
            return None
        number = data.get(cls.VAR_ON_NUMBER, None)
        if not number:
            log.info("%s - create - no number passed, not creating AutreNumero"%(_cln))
            return None
        an = cls()
        an.t_creation_user = text("(USER)")
        an.t_write_user = text("(USER)")
        if data:
            up = an._update(data, db)
            if not up:
                return False
        return an

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - _update - %s"%(_cln, data))
        
        label = data.get(self.VAR_ON_LABEL, None)
        number = data.get(self.VAR_ON_NUMBER, None)
        
        log.info("%s _update | '%s' -> '%s'"%(_cln, label, number))
        if label and (type(label) is t_autre_numero) and number:
            label.check()
            self.autre_numero = label
            self.valeur = number

        else:
            log.error("%s _update | unable to update %s -> '%s'"%(_cln, label, number))
            return False

        return True