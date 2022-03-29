import logging
import uuid

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, Float, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_loop, json_test, json_dump
from ..moby.champ.date import MobyChampDate as t_champ_date
from .champs.zone_constat_etat.verificateur import ChampSpecimenConstatEtatVerificateur as t_verificateur

log = logging.getLogger(__name__)
DEBUG = True

class SpecimenZoneConstatEtat(Base):

    VAR_STATUT = "statut"
    VAR_DATE = "date"
    VAR_VERIFICATEUR = "verificateur"

    STATUT_PREVU = "Prévu"
    STATUT_ACTUEL = "Actuel"
    STATUT_ANTERIEUR = "Antérieur"

    STATUTS = [STATUT_PREVU, STATUT_ACTUEL, STATUT_ANTERIEUR]

    __tablename__ = "SpecimenZoneConstatEtat"

    id = Column("SpecimenZoneConstatEtat_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_specimen = Column("SpecimenZoneConstatEtat_Specimen_Id", UUID, ForeignKey("Specimen.Specimen_Id"), nullable=True)

    # Prévu / Actuel / Antérieur
    #
    # 2 - Actuel
    # 
    statut = Column("SpecimenZoneConstatEtat_Statut", INTEGER, nullable=True)
    # pas présent dans le formulaire
    id_motif_constat_etat = Column("SpecimenZoneConstatEtat_MotifConstatEtat_Id", UUID, nullable=True) #ForeignKey [dbo].[MotifConstatEtat]
    # pas présent dans le formulaire
    id_campagne_recolement = Column("SpecimenZoneConstatEtat_CampagneRecolement_Id", UUID, nullable=True) # ForeignKey [dbo].[CampagneRecolement]
    from ..reference.etat import Etat as t_etat
    id_etat = Column("SpecimenZoneConstatEtat_Etat_Id", UUID, ForeignKey(t_etat.id), nullable=True)
    # ChampSpecimenConstatEtatIntegrite
    # ChampSpecimenConstatEtatVerificateur
    id_date_constat = Column("SpecimenZoneConstatEtat_DateConstat_Id", UUID, ForeignKey(t_champ_date.id), nullable=True)  
    # n'est pas affiché dans le formulaire
    id_degre_urgence = Column("SpecimenZoneConstatEtat_DegreUrgence_Id", UUID, nullable=True) #ForeignKey [dbo].[DegreUrgence]
    # NOTE:
    # une table ChampSpecimenZoneConstatEtatMultimedia existe, mais n'est pas utilisé à Grenoble
    notes = Column("SpecimenZoneConstatEtat_Notes", String, nullable=True)
    ordre = Column("SpecimenZoneConstatEtat_Ordre", INTEGER, nullable=True, default=1)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # liaisons

    specimen = relationship("Specimen", foreign_keys=[id_specimen], back_populates="zones_constat_etat", post_update=True)
    # non présent : motif_constat_etat
    # non présent : campagne_recollement
    # etat (un seul)
    etat = relationship(t_etat, foreign_keys=[id_etat])
    # intégrités (plusieurs)
    verificateurs = relationship(t_verificateur)

    date_constat = relationship(t_champ_date, foreign_keys=[id_date_constat])
    # non présent : degre_urgence
    # multimedias

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        
        data['statut'] = self.STATUTS[self.statut-1] if self.statut else None
        data['date_constat'] = json_test(self.date_constat)
        data['verificateurs'] = json_loop(self.verificateurs)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data        

    def find_verificateur(self, nom):
        vs = []
        for v in self.verificateurs:
            if v.nom_entier == nom:
                vs.append(v)
        if not vs:
            return None
        if len(vs) == 1:
            return vs[0]
        log.error("%s - found too many verificateurs with the same name '%s' (%d)"%(self.__class__.__name__, nom, len(vs)))
        return False

    def __eq__(self, other):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s == | %s %s"%(_cln, self, other))
        # statut
        o_statut = other.get(self.VAR_STATUT, None)
        if self.statut:
            try:
                id_statut = self.STATUTS.index(o_statut)+1
            except ValueError as e:
                # can't find the value passed
                return False
            if id_statut != self.statut:
                return False
        else:
            if o_statut is not None:
                return False
        # date 
        o_date = other.get(self.VAR_DATE, None)
        if self.date_constat:
            log.info("testing date_constat")
            if self.date_constat != o_date:
                return False 
        else:
            if o_date is not None:
                return False
        # verificateur
        o_verif = other.get(self.VAR_VERIFICATEUR, None)
        if self.verificateurs:
            if type(o_verif) is not list:
                o_verif = [ o_verif ]
            if len(o_verif) != len(self.verificateurs):
                return False
            for v in self.verificateurs:
                ok = False
                for o in o_verif:
                    if v == o:
                        ok = True
                if not ok:
                    return False
        else:
            if o_verif is not None:
                return False
        return True

    @classmethod
    def create(cls, data=None):
        if DEBUG:
            log.info("create %s: %s"%(cls.__name__, data))
        zce = cls()
        zce.t_creation_user = text("(USER)")
        zce.t_write_user = text("(USER)")
        if data:
            up = zce._update(data)
            if not up:
                return False
        return zce

    def update(self, data):
        if DEBUG:
            log.info("update %s: %s"%(self.__class__.__name__, data))
        return self._update(data)

    def _update(self, data):
        if DEBUG:
            log.info("_update %s: %s"%(self.__class__.__name__, data))
        updated = False

        statut = data.get(self.VAR_STATUT, None)
        if statut:
            if DEBUG:
                log.info("%s - _update statut '%s'"%(self.__class__.__name__, statut))
            if statut not in self.STATUTS:
                log.error("%s - _update : invalid statut '%s'"%(self.__class__.__name__, statut))
                return False
            # index is 0 based
            new_statut = self.STATUTS.index(statut) + 1
            if self.statut != new_statut:
                if DEBUG:
                    if not self.statut:
                        log.info("%s - statut was set to %s(%d)"%(\
                            self.__class__.__name__,\
                            self.STATUTS[new_statut-1], new_statut))
                    else:
                        log.info("%s - statut changed from %s(%d) to %s(%d)"%(\
                            self.__class__.__name__, \
                            self.STATUTS[self.statut-1], self.statut, \
                            self.STATUTS[new_statut-1], new_statut))
                self.statut = new_statut
                updated = True
        else:
            log.error("%s - _update: statut data missing in %s"%(self.__class__.__name__, data))
            return False
            
        date = data.get(self.VAR_DATE, None)
        if date:
            if self.date_constat:
                old_date = self.date_constat.isoformat()
                up = self.date_constat.update(date)
                if not up:
                    log.error("%s - FATAL: unable to update date with data %s"%(self.__name__.__class__, date))
                    return False
                if DEBUG:
                    if old_date:
                        log.info("%s - date updated from '%s' to '%s'"%(self.__name__.__class__, old_date, self.date_constat.isoformat()))
                    else:
                        log.info("%s - date set to '%s'"%(self.__class__.__name__, self.date_constat.isoformat()))
                updated = True
            else:
                d = t_champ_date.create(date)
                if d:
                    self.date_constat = d
                    if DEBUG:
                        log.info("%s - date set to '%s'"%(self.__class__.__name__, self.date_constat.isoformat()))
                    updated = True
                else:
                    log.error("%s - FATAL: unable to create new date with data %s"%(self.__class__.__name__, date))
                    return False
        else:
            # we don't have a date specified, and there is no date yet in the object
            if not self.date_constat:
                log.error("%s - FATAL: we have no date"%(self.__class__.__name__))
                return False

        verificateur = data.get(self.VAR_VERIFICATEUR, None)
        if verificateur:
            v = self.find_verificateur(verificateur)

            data = {
                t_verificateur.VAR_NOM: verificateur    
            }

            if v == False:
                log.error("%s - FATAL: Unable to find a proper verificateur to use")
                return False
            if v:
                up = v.update(data, db)
                if not up:
                    log.error("%s - FATAL: unable to update verificateur with data %s"%(self.__class__.__name__, data))
                    return False  
                updated = True
            else:
                v = t_verificateur.create(data, db)
                if not v:
                    log.error("%s - FATAL: unable to create verificateur with data %s"%(self.__class__.__name__, data))
                    return False
                v.zone_constat_etat = self

        if updated and DEBUG:
            log.info("%s - some data was modified"%(self.__class__.__name__))
        
        return True
