import logging
import uuid

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import object_session, relationship

from ..base import UUID, Base, indent, json_loop, json_test, json_dump
from ..localisation.localisation import Localisation as t_localisation
from ..reference.situation import Situation as t_situation

log = logging.getLogger(__name__)

DEBUG = True

class SpecimenZoneConstantesConservation(Base):

    VAR_STATUT = "statut"
    VAR_LOCALISATION = t_localisation.VAR_LOCALISATION
    VAR_SITUATION = "situation"

    STATUT_PRESENT = "Présent"
    STATUT_NON_LOCALISE = "Non localisé"
    STATUT_DISPARU = "Disparu"
    STATUT_DETRUIT = "Détruit"
    STATUT_RENDU = "Rendu"
    STATUT_CEDE = "Cédé"
    STATUT_EMPRUNTE = "Emprunté"
    STATUT_VOLE = "Volé"
    STATUT_PAS_UN_OBJET = "Pas un objet"
    STATUT_MANQUANT = "Manquant"
    STATUT_RETROUVE = "Retrouvé"
    STATUT_MIS_EN_DEPOT = "Mis en dépôt"

    STATUTS = [
        STATUT_PRESENT, STATUT_NON_LOCALISE, STATUT_DISPARU, STATUT_DETRUIT,
        STATUT_RENDU, STATUT_CEDE, STATUT_EMPRUNTE, STATUT_VOLE, 
        STATUT_PAS_UN_OBJET, STATUT_MANQUANT, STATUT_RETROUVE, 
        STATUT_MIS_EN_DEPOT,
    ]

    # définition de table
    __tablename__ = "SpecimenZoneConstantesConservation"

    id = Column("SpecimenZoneConstantesConservation_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    id_specimen = Column("SpecimenZoneConstantesConservation_Specimen_Id", UUID, ForeignKey("Specimen.Specimen_Id"), nullable=True)

    statut_specimen = Column("SpecimenZoneConstantesConservation_StatutSpecimenConstantesConservation", INTEGER, nullable=True)

    id_localisation_permanente = Column("SpecimenZoneConstantesConservation_LocalisationPermanente_Id", UUID, ForeignKey(t_localisation.id), nullable=True)

    id_unite_conditionnement = Column("SpecimenZoneConstantesConservation_UniteConditionnement_Id", UUID, ForeignKey(t_localisation.id), nullable=True)

    id_situation = Column("SpecimenZoneConstantesConservation_Situation_Id", UUID, ForeignKey(t_situation.id), nullable=True)

    from ..moby.champ.date import MobyChampDate as t_champ_date
    id_date_localisation = Column("SpecimenZoneConstantesConservation_DateLocalisation_Id", UUID, ForeignKey(t_champ_date.id), nullable=True)
    
    autorisation_necessaire = Column("SpecimenZoneConstantesConservation_AutorisationNecessaire", String, nullable=True)
    notes = Column("SpecimenZoneConstantesConservation_Notes", String, nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    #
    # Links
    # 

    #specimen = relationship("Specimen", foreign_keys=[id_specimen])
    localisation_permanente = relationship(t_localisation, foreign_keys=[id_localisation_permanente])
    unite_conditionnement = relationship(t_localisation, foreign_keys=[id_unite_conditionnement])

    situation = relationship(t_situation, foreign_keys=[id_situation])
    date_localisation = relationship(t_champ_date, foreign_keys=[id_date_localisation])
    
    #
    # external links
    # we never change this list directly, set as viewonly
    #

    from .champs.zone_constantes_conservation.conditions_pret import \
        ChampSpecimenConstantesConservationConditionsPret as t_conditions_pret
    conditions_pret = relationship(t_conditions_pret, viewonly=True)

    # 
    # generate json representation
    # 

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = str(self.id)

        data['statut_specimen'] = self.STATUTS[self.statut_specimen-1] if self.statut_specimen else None
        data['localisation_permanente'] = json_test(self.localisation_permanente)
        data['unite_conditionnement'] = json_test(self.unite_conditionnement)
        data['situation'] = json_test(self.situation)
        data['date_localisation'] = json_test(self.date_localisation)
        data['conditions_pret'] = json_loop(self.conditions_pret)
        data['autorisation_necessaire'] = self.autorisation_necessaire
        data['notes'] = self.notes

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data

    @property
    def localisation(self):
        if self.localisation_permanente:
            return self.localisation_permanente.localisation
        return None

    @classmethod
    def create(cls, data, db=None):
        if DEBUG:
            log.info("%s create %s"%(cls.__name__, data))
        zcc = cls()
        zcc.t_creation_user = text("(USER)")
        zcc.t_write_user = text("(USER)")
        if data:
            up = zcc._update(db, data)
            if not up:
                return False
        return zcc

    def update(self, data):
        pass

    def _update(self, db, data):
        
        #----------------------------------------
        # statut
        #
        statut = data.get(self.VAR_STATUT, None)
        if not statut:
            log.error("%s - Statut missing"%(self.__class__.__name__))
            return False
        if type(statut) is int:
            log.error("%s - statut as int not implemented"%(self.__class__.__name__))
            return False
        elif type(statut) is str:
            try:
                self.statut_specimen = self.STATUTS.index(statut) + 1 # array indexes start at 0
            except ValueError as e:
                log.error("%s - invalid status string '%s'"%(self.__class__.__name__, statut))
                return False
        else: 
            log.error("%s - invalid type for statut '%s'"%(self.__class__.__name__, statut))
            return False

        #----------------------------------------
        # localisation
        #
        localisation = data.get(self.VAR_LOCALISATION, None)
        if localisation:
            loc_data = {
                self.VAR_LOCALISATION: localisation,
            }
            if self.localisation_permanente:
                log.error("updating localisation is not implemented yet"%(self.__class__.__name__))
                return False
            else:
                loc = t_localisation.find(loc_data, db)
                if loc == False:
                    log.error("%s - FATAL : error looking for localisation '%s'"%(self.__class__.__name__, loc_data))
                    return False
                if not loc:
                    if DEBUG:
                        log.info("%s - creating new localisation %s"%(self.__class__.__name__, loc_data))
                    loc = t_localisation.create(loc_data) 
                # set the localisation of this item to the existing localisation record
                self.localisation_permanente = loc
        
        #----------------------------------------
        # situation
        #


        return True
