import logging
import uuid
from pathlib import PureWindowsPath

from sqlalchemy import (BIGINT, DATETIME, INTEGER, TIMESTAMP, VARBINARY,
                        Column, DateTime, ForeignKey, String, text)
from sqlalchemy.orm import relationship, object_session

from ..base import UUID, Base, indent, json_loop, json_test, json_dump
from ..moby.champ.date import MobyChampDate as t_champ_date
from .zone_identification import SpecimenZoneIdentification as t_zone_identification

log = logging.getLogger(__name__)

DEBUG = True

class Specimen(Base):
    VAR_IDENTIFICATION = 'identification'

    __tablename__ = "Specimen"

    id = Column("Specimen_Id", UUID, primary_key=True, nullable=False, default=uuid.uuid4)
    
    id_zone_identification = Column("Specimen_ZoneIdentification_Id", UUID, ForeignKey(t_zone_identification.id), nullable=False)
    from .zone_discipline import SpecimenZoneDiscipline as t_zone_discipline
    id_zone_discipline = Column("Specimen_ZoneDiscipline_Id", UUID, ForeignKey(t_zone_discipline.id), nullable=True)
    from .zone_description_physique import SpecimenZoneDescriptionPhysique as t_zone_description_physique
    id_zone_description_physique = Column("Specimen_ZoneDescriptionPhysique_Id", UUID, ForeignKey(t_zone_description_physique.id), nullable=True)
    from .zone_collecte import SpecimenZoneCollecte as t_zone_collecte
    id_zone_collecte = Column("Specimen_ZoneCollecte_Id", UUID, ForeignKey(t_zone_collecte.id), nullable=True)
    from .zone_datation_geologique import SpecimenZoneDatationGeologique as t_zone_datation_geologique
    id_zone_datation_geologique = Column("Specimen_ZoneDatationGeologique_Id", UUID, ForeignKey(t_zone_datation_geologique.id), nullable=True)
    id_zone_donnees_patrimoniales = Column("Specimen_ZoneDonneesPatrimoniales_Id", UUID, nullable=True)
    from .zone_constantes_conservation import SpecimenZoneConstantesConservation as t_zone_constantes_conservation
    id_zone_constantes_conservation = Column("Specimen_ZoneConstantesConservation_Id", UUID, ForeignKey(t_zone_constantes_conservation.id), nullable=True)
    id_zone_reproduction = Column("Specimen_ZoneReproduction_Id", UUID, nullable=True)
    id_zone_objet_associe = Column("Specimen_ZoneObjetAssocie_Id", UUID, nullable=True)
    from .zone_informations_systeme import SpecimenZoneInformationsSysteme as t_zone_informations_systeme
    id_zone_informations_systeme = Column("Specimen_ZoneInformationsSysteme_Id", UUID, ForeignKey(t_zone_informations_systeme.id), nullable=True)

    t_write = Column("_trackLastWriteTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_creation = Column("_trackCreationTime", DateTime, nullable=False, server_default=text("(getdate())"))
    t_write_user = Column("_trackLastWriteUser", String(64), nullable=False)
    t_creation_user = Column("_trackCreationUser", String(64), nullable=False)
    t_version = Column("_rowVersion", TIMESTAMP, nullable=False)

    # 
    # liens internes
    #

    zone_identification = relationship(t_zone_identification, foreign_keys=[id_zone_identification])                                # bidi link ok
    zone_discipline = relationship(t_zone_discipline, foreign_keys=[id_zone_discipline])                                            # bidi link ok
    zone_description_physique = relationship(t_zone_description_physique, foreign_keys=[id_zone_description_physique])
    zone_collecte = relationship(t_zone_collecte, foreign_keys=[id_zone_collecte])
    zone_datation_geologique = relationship(t_zone_datation_geologique, foreign_keys=[id_zone_datation_geologique])
    zone_constantes_conservation = relationship(t_zone_constantes_conservation, foreign_keys=[id_zone_constantes_conservation])
    zone_informations_systeme = relationship(t_zone_informations_systeme, foreign_keys=[id_zone_informations_systeme])

    #
    # Liens externes
    #  

    from .zone_determination import SpecimenZoneDetermination as t_zone_determination
    zones_determination = relationship(t_zone_determination, back_populates="specimen", order_by="SpecimenZoneDetermination.ordre")
    zones_multimedia = relationship("SpecimenZoneMultimedia", back_populates="specimen", order_by="SpecimenZoneMultimedia.ordre")    
    from .zone_bibliographie import SpecimenZoneBibliographie as t_zone_bibliographie
    zones_bibliographie = relationship(t_zone_bibliographie, back_populates="specimen", order_by=t_zone_bibliographie.ordre)
    from .zone_collection_anterieure import SpecimenZoneCollectionAnterieure as t_zone_collection_anterieure
    zones_collections_anterieures = relationship(t_zone_collection_anterieure, back_populates="specimen", order_by=t_zone_collection_anterieure.ordre)
    from .zone_constat_etat import SpecimenZoneConstatEtat as t_zone_constat_etat
    zones_constat_etat = relationship(t_zone_constat_etat, back_populates="specimen", order_by=t_zone_constat_etat.ordre)
    #
    #
    #

    @property
    def json(self):
        data = {}
        data['_type'] = self.__class__.__name__
        data['id'] = self.id

        # many-to-one fields
        

        # one-to-one data segments

        data['zone_identification'] = json_test(self.zone_identification)
        data['zone_discipline'] = json_test(self.zone_discipline)
        data['zone_description_physique'] = json_test(self.zone_description_physique)
        data['zone_collecte'] = json_test(self.zone_collecte)
        data['zone_datatation_geologique'] = json_test(self.zone_datation_geologique)
        data['id_zone_donnees_patrimoniales'] = self.id_zone_donnees_patrimoniales
        data['zone_constantes_conservation'] = json_test(self.zone_constantes_conservation)      
        data['id_zone_reproduction'] = self.id_zone_reproduction
        data['id_zone_objet_associe'] = self.id_zone_objet_associe
        data['zone_informations_systeme'] = json_test(self.zone_informations_systeme)

        # many-to-many data segments

        data['zones_determination'] = json_loop(self.zones_determination)
        data['zones_collections_anterieures'] = json_loop(self.zones_collections_anterieures)
        data['zones_constat_etat'] = json_loop(self.zones_constat_etat)
        data['zones_bibliographie'] = json_loop(self.zones_bibliographie)
        data['zones_multimedia'] = json_loop(self.zones_multimedia)

        data['t_write'] = json_dump(self.t_write)
        data['t_creation'] = json_dump(self.t_creation)
        data['t_write_user'] = json_dump(self.t_write_user)
        data['t_creation_user'] = json_dump(self.t_creation_user)
        data['t_version'] = json_dump(self.t_version)

        return data

    @property
    def inventoryNumber(self):
        if self.zone_identification:
            return self.zone_identification.numero_inventaire
        return None

    @property
    def localisation(self):
        if self.zone_constantes_conservation:
            return self.zone_constantes_conservation.localisation
        return None


    #----------------------------------------------------------------------------------------------
    #
    # Handling photos
    #
    #----------------------------------------------------------------------------------------------
    
    def listPhotos(self):
        """
        attempts to add an image to the specimen with the given windows path
        
        returns:
        None if we couldn't find images
        list of images if we could
        """
        nb_zm = len(self.zones_multimedia)
        zm = None
        if nb_zm == 1:
            zm = self.zones_multimedia[0]
            #log.info("INFO: found one zone_multimedia created %s by %s"%(zm.t_creation.isoformat(), zm.t_creation_user))
        elif nb_zm > 1:
            log.error("ERROR: multiple zone_multimedia")
            return None

        # we have a valid zm return that
        return zm


    @property
    def photos(self):
        iv_num = self.inventoryNumber
        p_list = []
        for zm in self.zones_multimedia:
            for mm in zm.multimedias:
                img = mm.multimedia
                if img:
                    zg = img.zone_generale
                    if zg:
                        w_path = PureWindowsPath(zg.chemin).joinpath(zg.nom_fichier)
                        p_list.append(w_path)
                    else:
                        log.warn("'%s' zm %d image %d has no zone_generale"%(iv_num, zm.ordre, mm.ordre))
                else:
                    log.warn("'%s' zm %d image %d has no image assigned"%(iv_num, zm.ordre, mm.ordre))
        return p_list
    

    def addPhoto(self, order, filename):
        """
        attempts to add an image to the specimen with the given windows path
        
        returns:
        true if the image could be added
        """
        photography_type = "Photographie"
        from .zone_multimedia import SpecimenZoneMultimedia
        session = object_session(self)
        nb_zm = len(self.zones_multimedia)
        zm = None
        if nb_zm == 0:
            # find the type for photography
            # NOTE: should be a passed value...
            from ..reference.reference import Reference, ReferenceZoneGenerale
            from ..reference.type_information import TypeInformation
            type_photo = session.query(TypeInformation)\
                .join(Reference, TypeInformation.id==Reference.id)\
                .join(ReferenceZoneGenerale, Reference.id_zone_generale==ReferenceZoneGenerale.id)\
                .filter(ReferenceZoneGenerale.libelle==photography_type).first()
            # need to create a zone multimedia...
            zm = SpecimenZoneMultimedia(self, type_photo)
            session.add(zm)
            log.info("zone_multimedia created")
        elif nb_zm == 1:
            zm = self.zones_multimedia[0]
            log.info("one zone multimedia %s"%(repr(zm)))
        else:
            log.error("nb_zm = %d - UNSUPPORTED FOR NOW"%(nb_zm))
            return False
        
        return zm.addPhoto(order, filename)



    #----------------------------------------------------------------------------------------------
    #
    # zone_constat_etat
    #
    #----------------------------------------------------------------------------------------------

    def find_zone_constat_etat(self, date):
        date = t_champ_date.parse(date)

        day = date.get('day', None)
        if not day:
            log.error("%s - find_zone_constat_etat - date argument must have day %s"%(self.inventoryNumber, date))
            return False
        month = date.get('month', None)
        if not month:
            log.error("%s - find_zone_constat_etat - date argument must have month %s"%(self.inventoryNumber, date))
            return False
        year = date.get('year', None)
        if not month:
            log.error("%s - find_zone_constat_etat - date argument must have year %s"%(self.inventoryNumber, date))
            return False
        # check for date validity ?
        zones = []
        for zce in self.zones_constat_etat:
            d = zce.date_constat
            if not d:
                log.error("%s - ZoneConstatEtat %s should have date record"%(self.inventoryNumber, zce.id))
                continue
            if (day==d.jour and month==d.mois and year==d.annee):
                # we found a valid date
                zones.append(zce)
        if not zones:
            return None
        if len(zones) == 1:
            return zones[0]
        log.error("%s - found too many ZoneConstatEtat (%d)"%(len(zones)))
        return False

    #----------------------------------------------------------------------------------------------
    # find / create / update
    # 

    @classmethod
    def find(cls, data, db):
        _cln = cls.__name__
        if not data:
            log.error("%s - find - no data was passed"%(_cln))
            return False
        identification = data.get(cls.VAR_IDENTIFICATION, None)
        if not identification:
            log.error("%s - find - no '%s' in data"%(_cln, cls.VAR_IDENTIFICATION))
            return False
        ni = identification.get(t_zone_identification.VAR_INVENTORY_NUMBER, None)
        if not ni:
            log.error("%s - find - no '%s'->'%s'"%(_cln, cls.VAR_IDENTIFICATION, t_zone_identification.VAR_INVENTORY_NUMBER))
            return False
        s = db.query(t_zone_identification).filter(t_zone_identification.numero_inventaire==ni)
        s_nb = s.count()
        if s_nb==0:
            return None
        elif s_nb==1:
            return s.first().specimen
        # more than one ???
        log.error("%s - find - found %d specimen with inventory number '%s' - should not happen !!!"%(_cln, ni))
        return False

    @classmethod
    def create(cls, data, db=None):
        _cln = cls.__name__ 
        if DEBUG:
            log.info("%s - create - %s"%(_cln, data))
        s = cls()
        s.id = uuid.uuid4()
        s.t_creation_user = text("(USER)")
        s.t_write_user = text("(USER)")
        if data:
            up = s._update(data, db)   
            if not up:
                return False
        return s

    def update(self, data, db):
        _cln = self.__class__.__name__
        if DEBUG:
            log.info("%s - update - %s"%(_cln, data))
        return self._update(data, db)

    def _update(self, data, db):
        _cln = self.__class__.__name__ 
        if DEBUG:
            log.info("%s - _update - %s"%(_cln, data))
        
        zi_data = data.get(self.VAR_IDENTIFICATION, None)
        if self.zone_identification:
            # ignore the return value
            self.zone_identification.update(zi_data, db)
            log.info("")
        else:
            if not zi_data:
                log.error("%s - _update - missing zone_identification data"%(_cln))
                return False
            zi = t_zone_identification.create(zi_data, db)
            if not zi:
                log.error("%s - _update - unable to create zone identification"%(_cln))
                return False
            # sets up the bidi link
            zi.id_specimen = self.id
            self.zone_identification = zi
        return True  

  