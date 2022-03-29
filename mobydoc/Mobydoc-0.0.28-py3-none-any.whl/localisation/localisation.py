import uuid
import logging

from sqlalchemy import TIMESTAMP, Column, DateTime, ForeignKey, String, text, select
from sqlalchemy.orm import backref, relationship, column_property
from sqlalchemy.orm.session import object_session

from ..base import UUID, Base, indent, json_test, scalar, json_dump
from .zone_generale import LocalisationZoneGenerale as t_zone_generale

log = logging.getLogger(__name__)

DEBUG = True

class Localisation(Base):
    VAR_LOCALISATION = t_zone_generale.VAR_LOCALISATION

    __tablename__ = "Localisation"

    id = Column("Localisation_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_zone_generale = Column("Localisation_ZoneGenerale_Id", UUID, ForeignKey(t_zone_generale.id), nullable=False)
    
    id_zone_multimedia = Column("Localisation_ZoneMultimedia_Id", UUID, nullable=True)

    id_zone_contexte = Column("Localisation_ZoneContexte_Id", UUID, nullable=True)

    from .zone_informations_systeme import \
        LocalisationZoneInformationsSysteme as t_zone_informations_systeme
    id_zone_informations_systeme = Column("Localisation_ZoneInformationsSysteme_Id", UUID, ForeignKey(t_zone_informations_systeme.id), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # liaisons
    zone_generale = relationship(t_zone_generale, foreign_keys=[id_zone_generale])
    zone_informations_systeme = relationship(t_zone_informations_systeme, foreign_keys=[id_zone_informations_systeme])

    localisation = column_property(scalar(select(t_zone_generale.localisation).where(id_zone_generale==t_zone_generale.id)))

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['zone_generale'] = json_test(self.zone_generale)
        data['id_zone_multimedia'] = self.id_zone_multimedia
        data['id_zone_contexte'] = self.id_zone_contexte
        data['zone_informations_systeme'] = json_test(self.zone_informations_systeme)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data

    def __repr__(self):
        zg = self.zone_generale
        if zg: 
            l = "'%s'"%(zg.localisation)
        else:
            l = None
        return "Localisation(id='%s',localisation=%s)"%(str(self.id)[-4:], l)

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if type(other) is not self.__class__:
            log.error("%s == | other is '%s'"%(_cln, type(other).__name__))
            test_value = False
        else:
            log.info("%s == | '%s'"%(_cln, self.localisation))
            zg = self.zone_generale
            if not zg:
                log.info("%s == | no self.zone_generale"%(_cln))
                test_value = False
            else:
                ozg = other.zone_generale
                if not ozg:
                    log.info("%s == | no other.zone_generale"%(_cln))
                    test_value = False
                else:
                    test_value = zg == ozg
        log.info("%s == | test => %s"%(_cln, test_value))
        return test_value

    # @property
    # def localisation(self):
    #     if self.zone_generale:
    #         return self.zone_generale.localisation
    #     return None

    @classmethod
    def find(cls, data, db):
        if DEBUG:
            log.info("%s - looking for '%s' %s"%(cls.__name__, data, db))
        if not db:
            log.error("%s - can't find with no database link"%(cls.__name__))
            return False
        localisation = data.get(cls.VAR_LOCALISATION, None)
        if not localisation:
            log.error("%s - need a localisation to find"%(cls.__name__))
            return False
        if DEBUG:
            log.info("%s - searching for '%s'"%(cls.__name__, localisation))
        loc = db.query(cls).where(cls.localisation==localisation)
        if loc.count() == 0:
            return None
        elif loc.count() == 1:
            return loc.first()
        log.error("%s - found %d records for '%s'"%(cls, loc.count(), localisation))
        return False

    @classmethod
    def create(cls, data=None):
        if DEBUG:
            log.info("%s - create %s"%(cls.__name__, data))
        loc = cls()
        loc.id = uuid.uuid4()
        loc.t_creation_user = text("(USER)")
        loc.t_write_user = text("(USER)")
        if data:
            up = loc._update(data)
            if not up:
                return False
        return loc

    def delete(self, db):
        zg = self.zone_generale
        if zg:
            db.delete(zg)
        db.delete(self)
        return True

    def check(self):
        zg = self.zone_generale
        if not zg:
            return False
        if zg.id_localisation != self.id:
            zg.id_localisation = self.id
        return True
    
    def _update(self, data):
        if DEBUG:
            log.info("%s - _update %s"%(self.__class__.__name__, data))
        
        localisation = data.get(self.VAR_LOCALISATION, None)
        if not localisation:
            log.error("%s - unable to update, missing localisation in %s"%(self.__class__.__name__, data))
            return False
        if self.zone_generale:
            log.error("%s - zone generale already exists, not implemented"%(self.__class__.__name__))
            return False
        else:
            loc_zg_data = {
                self.VAR_LOCALISATION: localisation,
            }
            zg = t_zone_generale.create(loc_zg_data)
            if not zg:
                log.error("%s - unable to create zone generale"%(self.__class__.__name__))
                return False
            zg.id_localisation = self.id
            self.zone_generale = zg

        return True