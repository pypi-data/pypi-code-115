import uuid
import logging

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text, Boolean)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_test, json_dump

log = logging.getLogger(__name__)

DEBUG = True

class ReferenceZoneGenerale(Base):
    VAR_LABEL = "label"
    # table definitions
    __tablename__ = "ReferenceZoneGenerale"

    id = Column("ReferenceZoneGenerale_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    libelle = Column("ReferenceZoneGenerale_Libelle", String(200), nullable=True)
    note_application = Column("ReferenceZoneGenerale_NoteApplication", String, nullable=True)
    is_protege = Column("ReferenceZoneGenerale_IsProtege", Boolean, nullable=True)
    id_reference_fichier = Column("ReferenceZoneGenerale_ReferenceFichier_Id", UUID, nullable=True)
    
    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['libelle'] = self.libelle
        data['note_application'] = self.note_application
        data['is_protege'] = self.is_protege

        data['t_write'] = self.t_write.isoformat() if self.t_write else None
        data['t_creation'] = self.t_creation.isoformat() if self.t_creation else None
        data['t_write_user'] = str(self.t_write_user) if self.t_write_user is not None else None
        data['t_creation_user'] = str(self.t_creation_user) if self.t_creation_user is not None else None

        return data    

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s - create '%s'"%(_cln, data))
        rzg = cls()
        rzg.t_creation_user = text("(USER)")
        rzg.t_write_user = text("(USER)")
        if data:
            up = rzg._update(data, db)
            if not up:
                return False
        return rzg

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        label = data.get(self.VAR_LABEL, None)
        if not label:
            log.error("%s - can't find %s in data"%(_cln, self.VAR_LABEL))
            return False
        self.libelle = label
        return True


class Reference(Base):
    VAR_REFERENCE_TYPE = "reference_type"
    VAR_LABEL = ReferenceZoneGenerale.VAR_LABEL

    # table definitions
    __tablename__ = "Reference"

    id = Column("Reference_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    code = Column("Reference_CodeReference", INTEGER, nullable=False)
    id_zone_generale = Column("Reference_ZoneGenerale_Id", UUID, ForeignKey(ReferenceZoneGenerale.id), nullable=False)
    type_name = Column("_typeName", String(256), nullable=False)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # liaisons
    zone_generale = relationship(ReferenceZoneGenerale, foreign_keys=[id_zone_generale])

    @property
    def label(self):
        return self.zone_generale.libelle if self.zone_generale else None

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['code'] = self.code
        data['zone_generale'] = json_test(self.zone_generale)
        data['type_name'] = self.type_name

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data   

    def set_system_data(self, ref_class, db):
        _cln = self.__class__.__name__ 
        if not db:
            log.error("%s - find_code - no proper db passed"%(_cln))
            exit(1)
        log.error("%s - looking for %s code"%(_cln, ref_class.__name__))
        c = db.query(ref_class)
        log.info("%s - %d"%(_cln, c.count()))
        if c.count() == 0:
            log.error("%s - find_code - couldn't find any records for %s"%(_cln, ref_class.__name__))
            exit(1)
        # the code should all be the same, so fetch the first one
        other_ref = c.first().reference
        self.code = other_ref.code
        self.type_name = other_ref.type_name
        
    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s - create '%s'"%(_cln, data))
        r = cls()
        r.id = uuid.uuid4()
        r.t_creation_user = text("(USER)")
        r.t_write_user = text("(USER)")
        if not data:
            log.error("%s - create - missing data"%(_cln))
            return False
        ref_class = data.get(cls.VAR_REFERENCE_TYPE, None)
        if not ref_class:
            log.error("%s - create - missing %s"%(_cln, cls.VAR_REFERENCE_TYPE))
            return False
        r.set_system_data(ref_class, db)
        up = r._update(data, db)
        if not up:
            return False
        return r

    def check(self):
        _cln = self.__class__.__name__ 
        zg = self.zone_generale
        if not zg:
            log.error("%s check | missing zone_generale"%(_cln))
            return False
        if zg.id_reference_fichier != self.id:
            log.warn("%s check | zg.ref != self id=%s"%(_cln, self.id))
            zg.id_reference_fichier= self.id
        return True
        

    def _update(self, data, db):
        _cln = self.__class__.__name__
        if self.zone_generale:
            log.error("%s - _update - updating the label of a reference is not implemented"%(_cln))
            return False
        zg = ReferenceZoneGenerale.create(data, db)
        if self.id is None:
            log.error("%s _update | Reference.id is None"%(_cln))
            return False
        zg.id_reference_fichier = self.id
        if not zg:
            log.error("%s - _update - error creating ReferenceZoneGenerale with label '%s'"%(_cln, data))
            return False
        self.zone_generale = zg
        return True

