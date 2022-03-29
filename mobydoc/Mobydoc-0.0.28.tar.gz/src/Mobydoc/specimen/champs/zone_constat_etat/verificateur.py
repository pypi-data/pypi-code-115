import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ....base import UUID, Base, indent, json_test, json_dump
from ....personne.personne import Personne as t_personne
# not used currently in SnBase
# from ....reference.fonction_role import FonctionRole as t_fonction_role

log = logging.getLogger(__name__)
DEBUG = True

class ChampSpecimenConstatEtatVerificateur(Base):
    VAR_NOM = t_personne.VAR_NOM

    # définition de table
    __tablename__ = "ChampSpecimenConstatEtatVerificateur"

    id = Column("ChampSpecimenConstatEtatVerificateur_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_zone_constat_etat = Column("ChampSpecimenConstatEtatVerificateur_SpecimenZoneConstatEtat_Id", \
        UUID, ForeignKey("SpecimenZoneConstatEtat.SpecimenZoneConstatEtat_Id"), nullable=True)
    
    id_verificateur = Column("ChampSpecimenConstatEtatVerificateur_Verificateur_Id", UUID, \
        ForeignKey(t_personne.id), nullable=True)
    
    # id_fonction_role = Column("ChampSpecimenConstatEtatVerificateur_FonctionRole_Id", UUID, \
    #     ForeignKey(t_fonction_role.id), nullable=True)
    
    ordre = Column("ChampSpecimenConstatEtatVerificateur_Ordre", INTEGER, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    #
    # Links
    # 

    zone_constat_etat = relationship("SpecimenZoneConstatEtat", \
        foreign_keys=[id_zone_constat_etat], back_populates="verificateurs")
    verificateur = relationship(t_personne, foreign_keys=[id_verificateur])
    # fonction_role = relationship(t_fonction_role, foreign_keys=[id_fonction_role])

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

        data['verificateur'] = json_test(self.verificateur)
        # data['fonction_role'] = json_test(self.fonction_role)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s == | %s '%s'"%(_cln, self, other))
        if not self.verificateur:
            return False
        return self.verificateur == other

    @classmethod
    def create(cls, data=None, db=None):
        if DEBUG:
            log.info("create %s: %s"%(cls.__name__, data))
        
        v = cls()
        v.t_creation_user = text("(USER)")
        v.t_write_user = text("(USER)")
        if data:
            up = v._update(data, db)
            if not up:
                return False
        return v

    def update(self, data, db):
        if DEBUG:
            log.info("update %s: %s"%(self.__class__.__name__, data))
        return self._update(data, db)

    def _update(self, data, db):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("_update %s: %s"%(_cln, data))
        
        p = t_personne.find(data, db)
        log.info("%s _update | %s"%(_cln, p))

        if not self.verificateur:
            self.verificateur = t_personne.create(data, db)
            if not self.verificateur:
                return False
        else:
            if not self.verificateur.update(data, db):
                return False

        if DEBUG:
            log.info("%s - updated successfully"%(_cln))
        return True