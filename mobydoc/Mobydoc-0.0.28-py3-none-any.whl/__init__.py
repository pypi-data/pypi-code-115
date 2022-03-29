from .base import Version, checkVersion, dumps
from .caracteristiques_physiques.zone_generale import \
    CaracteristiquesPhysiquesZoneGenerale
from .classification.champs.auteur import \
    ChampClassificationZoneIdentificationAuteur
from .classification.classification import Classification
from .classification.zone_contexte import ClassificationZoneContexte
from .classification.zone_identification import (
    ClassificationZoneIdentification,
    ClassificationZoneIdentification_MobyTag_MobyTag_Classification)
from .datation_geologique.datation_geologique import DatationGeologique
from .localisation.localisation import Localisation
from .localisation.zone_generale import LocalisationZoneGenerale
from .moby.tag.mobytag import MobyTag
from .multimedia.multimedia import Multimedia
from .multimedia.zone_generale import MultimediaZoneGenerale
from .personne.personne import Personne
from .provenance.provenance import Provenance
from .provenance.zone_contexte import ProvenanceZoneContexte
from .provenance.zone_identification import ProvenanceZoneIdentification
from .reference.autre_numero import AutreNumero
from .reference.nature_specimen import NatureSpecimen
from .reference.reference import Reference, ReferenceZoneGenerale
from .specimen.champs.multimedia import ChampSpecimenZoneMultimediaMultimedia
from .specimen.champs.zone_collecte.autres_coordonnees import \
    ChampSpecimenZoneCollecteAutresCoordonnees
from .specimen.champs.zone_collecte.collecteur import \
    ChampSpecimenZoneCollecteCollecteur
from .specimen.champs.zone_collecte.provenance import \
    ChampSpecimenZoneCollecteProvenance
from .specimen.champs.zone_constat_etat.verificateur import \
    ChampSpecimenConstatEtatVerificateur
from .specimen.champs.zone_datation_geologique.datation_geologique import \
    ChampSpecimenZoneDatationGeologiqueDatationGeologique
from .specimen.champs.zone_description_physique.caracteristiques_physiques import \
    ChampSpecimenZoneDescriptionPhysiqueCaracteristiquesPhysiques
from .specimen.champs.zone_description_physique.nature_specimen import \
    ChampSpecimenZoneDescriptionPhysiqueNatureSpecimen
from .specimen.champs.zone_determination.determinateur import \
    ChampSpecimenZoneDeterminationDeterminateur
from .specimen.champs.zone_identification.autre_numero import \
    ChampSpecimenAutreNumero
from .specimen.specimen import Specimen
from .specimen.zone_collecte import SpecimenZoneCollecte
from .specimen.zone_collection_anterieure import \
    SpecimenZoneCollectionAnterieure
from .specimen.zone_constantes_conservation import \
    SpecimenZoneConstantesConservation
from .specimen.zone_constat_etat import SpecimenZoneConstatEtat
from .specimen.zone_datation_geologique import SpecimenZoneDatationGeologique
from .specimen.zone_description_physique import SpecimenZoneDescriptionPhysique
from .specimen.zone_determination import SpecimenZoneDetermination
from .specimen.zone_discipline import SpecimenZoneDiscipline
from .specimen.zone_identification import SpecimenZoneIdentification
