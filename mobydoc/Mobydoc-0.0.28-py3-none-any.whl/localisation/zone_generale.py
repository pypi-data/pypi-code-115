import uuid
import logging

from sqlalchemy import TIMESTAMP, Column, DateTime, ForeignKey, String, text
from sqlalchemy.orm import relationship, backref

from ..base import UUID, Base, indent, json_loop, json_test, json_dump

log = logging.getLogger(__name__)

DEBUG = True

class LocalisationZoneGenerale(Base):
    VAR_LOCALISATION = "localisation"

    __tablename__ = "LocalisationZoneGenerale"

    id = Column("LocalisationZoneGenerale_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    localisation = Column("LocalisationZoneGenerale_Localisation", String(200), nullable=True)
    id_type_localisation = Column("LocalisationZoneGenerale_TypeLocalisation_Id", UUID, nullable=True)
    id_numero_marquage = Column("LocalisationZoneGenerale_NumeroMarquage_Id", UUID, nullable=True)
    id_adresse = Column("LocalisationZoneGenerale_Adresse_Id", UUID, nullable=True)
    notes = Column("LocalisationZoneGenerale_Notes", String, nullable=True)
    id_localisation = Column("LocalisationZoneGenerale_LocalisationFichier_Id", UUID, 
        ForeignKey("Localisation.Localisation_Id"), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    # liaisons
    # we don't update this list directly, set as viewonly
    from .champ.zone_generale.multimedia import ChampLocalisationZoneGeneraleMultimedia as t_champ_multimedia
    multimedias = relationship(t_champ_multimedia, viewonly=True)

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['localisation'] = self.localisation
        data['id_type_localisation'] = self.id_type_localisation
        data['id_numero_marquage'] = self.id_numero_marquage
        
        data['id_adresse'] = self.id_adresse
        data['multimedias'] = json_loop(self.multimedias)
        data['notes'] = self.notes
        

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if type(other) is not self.__class__:
            log.error("%s == | other is '%s'"%(_cln, type(other).__name__))
            test_value = False
        else:
            log.info("%s == | self '%s'"%(_cln, self.localisation))
            log.info("%s == | other '%s'"%(_cln, other.localisation))
            test_value = self.localisation == other.localisation
        log.info("%s == | test value => %s"%(_cln, test_value))
        return test_value
        

    @classmethod
    def create(cls, data=None):
        if DEBUG:
            log.info("%s - create %s"%(cls.__name__, data))
        zg = cls()
        zg.t_write_user = text("(USER)")
        zg.t_creation_user = text("(USER)")
        if data:
            up = zg._update(data)
            if not up:
                return False
        return zg

    def _update(self, data):
        if DEBUG:
            log.info("%s - _update %s"%(self.__class__.__name__, data))

        localisation = data.get(self.VAR_LOCALISATION, None)
        if not localisation:
            log.error("%s - unable to update, missing localisation in %s"%(self.__class__.__name__, data))
            return False
        self.localisation = localisation

        return True