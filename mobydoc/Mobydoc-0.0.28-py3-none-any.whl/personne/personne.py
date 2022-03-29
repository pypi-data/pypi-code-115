import logging
import uuid

from sqlalchemy import TIMESTAMP, Column, DateTime, ForeignKey, String, text
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_test, json_dump
from .zone_identification import \
    PersonneZoneIdentification as t_zone_identification

log = logging.getLogger(__name__)
DEBUG = False

class Personne(Base):
    VAR_PRENOM = t_zone_identification.VAR_PRENOM
    VAR_NOM = t_zone_identification.VAR_NOM
    VAR_TAGS = t_zone_identification.VAR_TAGS

    __tablename__ = "Personne"

    id = Column("Personne_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_zone_identification = Column("Personne_ZoneIdentification_Id", UUID, ForeignKey("PersonneZoneIdentification.PersonneZoneIdentification_Id"), nullable=False)
    id_zone_donnees_biographiques = Column("Personne_ZoneDonneesBiographiques_Id", UUID, nullable=True)
    id_zone_droit_moral = Column("Personne_ZoneDroitMoral_Id", UUID, nullable=True)
    id_zone_p_adherent = Column("Personne_ZonePAdherent_Id", UUID, nullable=True)
    id_zone_contexte = Column("Personne_ZoneContexte_Id", UUID, nullable=True)
    id_zone_informations_systeme = Column("Personne_ZoneInformationsSysteme_Id", UUID, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # liaisons
    zone_identification = relationship(t_zone_identification, foreign_keys=[id_zone_identification])

    @property
    def nom_entier(self):
        return self.zone_identification.nom_entier

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['zone_identification'] = json_test(self.zone_identification)
        data['id_zone_donnees_biographiques'] = str(self.id_zone_donnees_biographiques)
        data['id_zone_droit_moral'] = str(self.id_zone_droit_moral)
        data['id_zone_p_adherent'] = str(self.id_zone_p_adherent)
        data['id_zone_contexte'] = str(self.id_zone_contexte)
        data['id_zone_informations_systeme'] = str(self.id_zone_informations_systeme)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data        

    def __repr__(self):
        if not self.zone_identification:
            s = str(None)
        else:
            s = repr(self.zone_identification)
        return "Personne{id:'%s',%s}"%(str(self.id)[-4:],s)

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s == | %s '%s'"%(_cln, self, other))
        if not self.zone_identification:
            log.error("%s == | no zone_identification defined for %s"%(_cln, self))
            return False
        if type(other) == self.__class__:
            if DEBUG:
                log.info("%s == | other is type %s"%(_cln, type(other)))
            if not other.zone_identification:
                log.error("%s == | no zone_identification defined for %s"%(_cln, other))
                return False
            other = other.zone_identification
        same = self.zone_identification == other
        if DEBUG:
            log.info("%s == | %s"%(_cln, same))
        return same

    @classmethod
    def find(cls, data, db):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s find | '%s'"%(_cln, data))
        if not db:
            log.error("%s find: no db specified"%(_cln))
            return False
        prenom = data.get(cls.VAR_PRENOM, None)
        nom = data.get(cls.VAR_NOM, None)
        tags = data.get(cls.VAR_TAGS, None)
        if not nom:
            log.error("%s find | %s not specified in data"%(_cln, cls.VAR_NOM))
            return False
        p = db.query(cls).join(t_zone_identification, cls.id_zone_identification==t_zone_identification.id)
        p = p.filter(t_zone_identification.nom==nom)
        if prenom:
            p = p.filter(t_zone_identification.prenom==prenom)

        p_nb = p.count()
        if p_nb == 0:
            log.info("%s find | found no entries for '%s'"%(_cln, data))
            return None
        if p_nb == 1:
            p = p.first()
            log.info("%s find | found %s"%(_cln, p))
            return p
            
        # filter by tags
        p_list = p.all()
        if tags:
            _pl = []
            for p in p_list:
                zi = p.zone_identification
                for t in tags:
                    if t in zi.tags_list and p not in _pl:
                        _pl.append(p)
            p_nb = len(_pl)
            p_list = _pl

        log.error("%s find | found %d entries for '%s'"%(_cln, p_nb, data))
        valid_persons = []
        # filter with nom / prenom
        for p in p_list:
            zi = p.zone_identification
            ok = True
            if zi.nom != nom:
                ok = False
            if zi.prenom != prenom:
                ok = False
            s_ok = ('T' if ok else 'F')
            if ok:
                valid_persons.append(p)
            log.info("    * %s '%s' '%s' '%s'"%(s_ok, zi.nom, zi.prenom, zi.tags_list))

        p_nb = len(valid_persons)

        if p_nb == 0:
            log.info("not found")
            return None
        # success, we have ONE !
        if p_nb == 1:
            return valid_persons[0]

        return False
        

# Personne find | found 6 entries for '{'nom': 'Lory'}'
#     * 'Lory' 'None' '['Auteur']'
#     * 'Lory' 'Charles' '['Collecteur (collection)']'
#     * 'Lory' 'Pierre' '['Collecteur (collection)']'
#     * 'Lory' 'Charles' '['Déterminateur']'
#     * 'Lory' 'Charles' '['Collecteur (collecte)']'
#     * 'Lory' 'Pierre' '['Collecteur (collecte)']'


    @classmethod
    def create(cls, data=None, db=None):
        if DEBUG:
            log.info("create %s: %s"%(cls.__name__, data))
        p = cls()
        p.id = uuid.uuid4()
        p.t_creation_user = text("(USER)")
        p.t_write_user = text("(USER)")
        if data:
            up = p._update(data, db)
            if not up:
                return False
        return p

    def check(self):
        _cln = self.__class__.__name__ 
        zi = self.zone_identification
        if zi:
            if zi.id_personne_fichier != self.id:
                log.info("%s check | updating backlink => '%s'"%(_cln, self.id))
                zi.id_personne_fichier = self.id

    def delete(self, db):
        if self.zone_identification:
            db.delete(self.zone_identification)
        db.delete(self)
        return True

    def update(self, data, db):
        if DEBUG:
            log.info("update %s: %s"%(self.__class__.__name__, data))
        return self._update(data, db)

    def _update(self, data, db):
        if DEBUG:
            log.info("_update %s: %s"%(self.__class__.__name__, data))

        if not self.zone_identification:
            self.zone_identification = t_zone_identification.create(data)
            if not self.zone_identification:
                return False
        else:
            if not self.zone_identification.update(data):
                return False
            # set the reverse link - necessary for search (stupid design, don't get me started)
            self.zone_identification.id_personne_fichier = self.id

        if DEBUG:
            log.info("%s - updated successfully"%(self.__class__.__name__))
        return True      
