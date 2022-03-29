import logging
import uuid

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship

from ..base import UUID, Base, indent, json_loop, json_test, json_dump
from ..classification.classification import Classification as t_classification
from ..reference.type_information import TypeInformation

log = logging.getLogger(__name__)

DEBUG = True 

class SpecimenZoneDetermination(Base):
    VAR_NOM_SCIENTIFIQUE = "nom_scientifique"

    # définition de table
    __tablename__ = "SpecimenZoneDetermination"

    id = Column("SpecimenZoneDetermination_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)

    # Determination.Reference_Id
    # Reference.Reference_Id
    from ..reference.determination import Determination as t_determination
    id_determination = Column("SpecimenZoneDetermination_Determination_Id", UUID, ForeignKey(t_determination.id), nullable=True)

    # Classification.Classification_Id
    id_nom_scientifique = Column("SpecimenZoneDetermination_NomScientifique_Id", UUID, ForeignKey(t_classification.id), nullable=True)

    # ChampSpecimenZoneDeterminationDateDetermination.ChampSpecimenZoneDeterminationDateDetermination_Id
    from .champs.zone_determination.date_determination import \
        ChampSpecimenZoneDeterminationDateDermination as t_date_determination
    id_date_determination = Column("SpecimenZoneDetermination_DateDetermination_Id", UUID, ForeignKey(t_date_determination.id), nullable=True)

    notes = Column("SpecimenZoneDetermination_Notes", String, nullable=True)
    # Specimen.Specimen_Id
    id_specimen = Column("SpecimenZoneDetermination_Specimen_Id", UUID, ForeignKey("Specimen.Specimen_Id"), nullable=True)
    ordre = Column("SpecimenZoneDetermination_Ordre", INTEGER, nullable=True, default=1)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)

    #
    # Links
    # 

    determination = relationship(t_determination, foreign_keys=[id_determination])
    nom_scientifique = relationship(t_classification, foreign_keys=[id_nom_scientifique])
    date_determination = relationship(t_date_determination, foreign_keys=[id_date_determination])
    specimen = relationship("Specimen", foreign_keys=[id_specimen], back_populates="zones_determination")
    
    #
    # external links
    #

    from .champs.zone_determination.statut_specimen import \
        ChampSpecimenZoneDeterminationStatutSpecimen as t_statut_specimen
    statuts_specimen = relationship(t_statut_specimen, back_populates="zone_determination", order_by=t_statut_specimen.ordre)

    from .champs.zone_determination.determinateur import \
        ChampSpecimenZoneDeterminationDeterminateur as t_determinateur
    determinateurs = relationship(t_determinateur, back_populates="zone_determination", order_by=t_determinateur.ordre) 

    from .champs.zone_determination.reference_bibliographique import \
        ChampSpecimenZoneDeterminationReferenceBibliographique as \
        t_reference_bibliographique
    references_bibliographiques = relationship(t_reference_bibliographique, back_populates="zone_determination", order_by=t_reference_bibliographique.ordre) 

    # 
    # generate json representation
    # 

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = self.id
        data['ordre'] = self.ordre

        data['determination'] = json_test(self.determination)
        data['nom_scientifique'] = json_test(self.nom_scientifique)
        data['statuts_specimen'] = json_loop(self.statuts_specimen)
        data['determinateurs'] = json_loop(self.determinateurs)
        data['date_determination'] = json_test(self.date_determination)
        data['references_bibliographiques'] = json_loop(self.references_bibliographiques)
        data['notes'] = self.notes

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)

        return data

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s - create - '%s'"%(_cln, data))
        zd = cls()
        zd.t_creation_user = text("(USER)")
        zd.t_write_user = text("(USER)")
        if data:
            up = zd._update(data, db)
            if not up:
                return False
        return zd

    def check(self):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s check"%(_cln))
        if self.nom_scientifique:
            self.nom_scientifique.check()
        elif DEBUG:
            log.info("%s check | no nom_scientifique to check"%(_cln))

    def _update(self, data, db):
        _cln = self.__class__.__name__ 

        ns = data.get(self.VAR_NOM_SCIENTIFIQUE, None)
        if ns:
            if self.nom_scientifique:
                log.error("%s - _update: updating nom scientifique not implemented yet"%(_cln))
                return False
            else:
                _ns = t_classification.find(ns, db)
                if _ns == False:
                    log.error("%s - _update - error while looking for classification %s"%(_cln, ns))
                    return False
                if not _ns:
                    log.info("%s - _update - could not find classification %s"%(_cln, ns))
                    _ns = t_classification.create(ns, db)
                    log.info("%s "%(_ns))
                # add the nom_scientifique to the zone_determination
                self.nom_scientifique = _ns

        return True
