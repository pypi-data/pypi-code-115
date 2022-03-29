# Load dependencies.
import ovito.extensions.pyscript
import ovito.extensions.stdobj
import ovito.extensions.stdmod
import ovito.extensions.mesh
import ovito.extensions.grid

# Load the C extension module.
import ovito.plugins.ParticlesPython

# Load class add-ons.
import ovito.modifiers.structure_identification_modifier
import ovito.modifiers.compute_property_modifier
import ovito.data.bonds_class
import ovito.data.particles_class
import ovito.data.trajectory_lines
import ovito.data.cutoff_neighbor_finder
import ovito.data.nearest_neighbor_finder
import ovito.data.ptm_neighbor_finder
import ovito.nonpublic.lammps_data_io

# Publish classes.
ovito.vis.__all__ += ['ParticlesVis', 'VectorVis', 'BondsVis', 'TrajectoryVis']
ovito.pipeline.__all__ += ['ReferenceConfigurationModifier']
ovito.modifiers.__all__ += [
            'AmbientOcclusionModifier',
            'WrapPeriodicImagesModifier',
            'ExpandSelectionModifier',
            'StructureIdentificationModifier',
            'CommonNeighborAnalysisModifier',
            'AcklandJonesModifier',
            'CreateBondsModifier',
            'CentroSymmetryModifier',
            'ClusterAnalysisModifier',
            'CoordinationAnalysisModifier',
            'CalculateDisplacementsModifier',
            'AtomicStrainModifier',
            'WignerSeitzAnalysisModifier',
            'VoronoiAnalysisModifier',
            'IdentifyDiamondModifier',
            'LoadTrajectoryModifier',
            'PolyhedralTemplateMatchingModifier',
            'CoordinationPolyhedraModifier',
            'SmoothTrajectoryModifier',
            'GenerateTrajectoryLinesModifier',
            'UnwrapTrajectoriesModifier',
            'ChillPlusModifier',
            'ConstructSurfaceModifier']
ovito.data.__all__ += ['ParticleType', 'BondType', 'BondsEnumerator',
            'CutoffNeighborFinder', 'NearestNeighborFinder', 'PTMNeighborFinder',
            'Particles', 'Bonds', 'TrajectoryLines']

# Register import formats.
ovito.io.import_file._formatTable["lammps/dump"] = ovito.nonpublic.LAMMPSTextDumpImporter
ovito.io.import_file._formatTable["lammps/dump/bin"] = ovito.nonpublic.LAMMPSBinaryDumpImporter
ovito.io.import_file._formatTable["lammps/dump/local"] = ovito.nonpublic.LAMMPSDumpLocalImporter
ovito.io.import_file._formatTable["lammps/data"] = ovito.nonpublic.LAMMPSDataImporter
ovito.io.import_file._formatTable["imd"] = ovito.nonpublic.IMDImporter
ovito.io.import_file._formatTable["vasp"] = ovito.nonpublic.POSCARImporter
ovito.io.import_file._formatTable["xyz"] = ovito.nonpublic.XYZImporter
ovito.io.import_file._formatTable["fhi-aims"] = ovito.nonpublic.FHIAimsImporter
ovito.io.import_file._formatTable["fhi-aims/log"] = ovito.nonpublic.FHIAimsLogFileImporter
ovito.io.import_file._formatTable["gsd/hoomd"] = ovito.nonpublic.GSDImporter
ovito.io.import_file._formatTable["castep/cell"] = ovito.nonpublic.CastepCellImporter
ovito.io.import_file._formatTable["castep/md"] = ovito.nonpublic.CastepMDImporter
ovito.io.import_file._formatTable["cfg"] = ovito.nonpublic.CFGImporter
ovito.io.import_file._formatTable["cif"] = ovito.nonpublic.CIFImporter
ovito.io.import_file._formatTable["mmcif"] = ovito.nonpublic.mmCIFImporter
ovito.io.import_file._formatTable["gaussian/cube"] = ovito.nonpublic.GaussianCubeImporter
ovito.io.import_file._formatTable["dlpoly"] = ovito.nonpublic.DLPOLYImporter
ovito.io.import_file._formatTable["gro"] = ovito.nonpublic.GroImporter
ovito.io.import_file._formatTable["xtc"] = ovito.nonpublic.XTCImporter
ovito.io.import_file._formatTable["reaxff/bonds"] = ovito.nonpublic.ReaxFFBondImporter
ovito.io.import_file._formatTable["parcas"] = ovito.nonpublic.ParcasFileImporter
ovito.io.import_file._formatTable["pdb"] = ovito.nonpublic.PDBImporter
ovito.io.import_file._formatTable["quantumespresso"] = ovito.nonpublic.QuantumEspressoImporter
ovito.io.import_file._formatTable["vtk/vtp/particles"] = ovito.nonpublic.ParaViewVTPParticleImporter
ovito.io.import_file._formatTable["xsf"] = ovito.nonpublic.XSFImporter

# Register export formats.
ovito.io.export_file._formatTable["lammps/dump"] = ovito.nonpublic.LAMMPSDumpExporter
ovito.io.export_file._formatTable["lammps/data"] = ovito.nonpublic.LAMMPSDataExporter
ovito.io.export_file._formatTable["imd"] = ovito.nonpublic.IMDExporter
ovito.io.export_file._formatTable["vasp"] = ovito.nonpublic.POSCARExporter
ovito.io.export_file._formatTable["xyz"] = ovito.nonpublic.XYZExporter
ovito.io.export_file._formatTable["fhi-aims"] = ovito.nonpublic.FHIAimsExporter
ovito.io.export_file._formatTable["gsd/hoomd"] = ovito.nonpublic.GSDExporter

# For backward compatibility with OVITO 2.9.0:
ovito.io.export_file._formatTable["lammps_dump"] = ovito.nonpublic.LAMMPSDumpExporter
ovito.io.export_file._formatTable["lammps_data"] = ovito.nonpublic.LAMMPSDataExporter

# For backward compatibility with OVITO 2.9.0:
ovito.modifiers.CoordinationNumberModifier = ovito.modifiers.CoordinationAnalysisModifier
ovito.modifiers.InterpolateTrajectoryModifier = ovito.modifiers.SmoothTrajectoryModifier
ovito.modifiers.__all__ += ['CoordinationNumberModifier', 'InterpolateTrajectoryModifier']

from ovito.data import DataCollection, Particles, TrajectoryLines

# Implementation of the DataCollection.particles attribute.
def _DataCollection_particles(self):
    """
    Returns the :py:class:`Particles` object from this data collection, which stores the particle properties and -as a sub-object- the 
    :py:attr:`~Particles.bonds` between particles. ``None`` is returned if the data collection does not contain any particle data.

    Note that the :py:class:`Particles` object may be marked as read-only if it is currently shared by several data collections.
    If you intend to modify the particles container or its sub-objects in any way, e.g. add, remove or modify particle properties, 
    you must request a mutable version of the particles object using the :py:attr:`!particles_` accessor instead.
    """
    return self._find_object_type(Particles)
# Implement the assignment of a Particles object to the DataCollection.particles field.
def _DataCollection_set_particles(self, obj):
    assert(obj is None or isinstance(obj, Particles)) # Must assign a Particles data object to this field.
    # Check if there already is an existing Particles object in the DataCollection. 
    # If yes, first remove it from the collection before adding the new one. 
    existing = self._find_object_type(Particles)
    if existing is not obj:
        if not existing is None: self.objects.remove(existing)
        if not obj is None: self.objects.append(obj)
DataCollection.particles = property(_DataCollection_particles, _DataCollection_set_particles)

# Implementation of the DataCollection.particles_ attribute.
DataCollection.particles_ = property(lambda self: self.make_mutable(self.particles), _DataCollection_set_particles)

# Implementation of the DataCollection.trajectories attribute.
def _DataCollection_trajectories(self):
    """
    Returns the :py:class:`TrajectoryLines` object, which holds the continuous particle trajectories traced 
    by the :py:class:`~ovito.modifiers.GenerateTrajectoryLinesModifier`. 
    ``None`` is returned if the data collection does not contain a :py:class:`TrajectoryLines` object.
    """
    return self._find_object_type(TrajectoryLines)
DataCollection.trajectories = property(_DataCollection_trajectories)

# Implementation of the DataCollection.trajectories_ attribute.
DataCollection.trajectories_ = property(lambda self: self.make_mutable(self.trajectories))
