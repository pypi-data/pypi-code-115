import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem


def rdkit_numpy_convert(fp):
    output = []
    for f in fp:
        arr = np.zeros((1,))
        DataStructs.ConvertToNumpyArray(f, arr)
        output.append(arr)
    return np.asarray(output)


def ecfp(smiles: str, to_array: bool = True, radius: int = 2, nbits: int = 1024):
    # Calculate the morgan fingerprint
    fp = AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(smiles), radius, nBits=nbits)
    if to_array:
        arr = np.zeros((1,))
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    else:
        return fp


def maccs(smiles: str, to_array: bool = True):
    from rdkit.Chem import MACCSkeys
    fp = MACCSkeys.GenMACCSKeys(Chem.MolFromSmiles(smiles))
    if to_array:
        arr = np.zeros((1,))
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    else:
        return fp


def rdkit(smiles: str, to_array: bool = True):
    fp = Chem.RDKFingerprint(Chem.MolFromSmiles(smiles))
    if to_array:
        arr = np.zeros((1,))
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    else:
        return fp


def atom_pair(smiles: str, to_array: bool = True):
    fp = AllChem.GetHashedAtomPairFingerprintAsBitVect(Chem.MolFromSmiles(smiles))
    if to_array:
        arr = np.zeros((1,))
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    else:
        return fp


def topological_torsion(smiles: str, to_array: bool = True):
    fp = AllChem.GetHashedTopologicalTorsionFingerprintAsBitVect(Chem.MolFromSmiles(smiles))
    if to_array:
        arr = np.zeros((1,))
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    else:
        return fp


def smarts(smiles: str, to_array: bool = True):
    fp = Chem.PatternFingerprint(Chem.MolFromSmiles(smiles))
    if to_array:
        arr = np.zeros((1,))
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    else:
        return fp


def drug_like_descriptor(smiles: str):
    from rdkit.Chem.Descriptors import ExactMolWt
    from rdkit.Chem import Descriptors, rdMolDescriptors, rdmolops, QED, Crippen, rdchem

    # https://sharifsuliman1.medium.com/understanding-drug-likeness-filters-with-rdkit-and-exploring-the-withdrawn-database-ebd6b8b2921e
    mol = Chem.MolFromSmiles(smiles)
    weight = ExactMolWt(mol)
    logp = Descriptors.MolLogP(mol)
    h_bond_donor = Descriptors.NumHDonors(mol)
    h_bond_acceptors = Descriptors.NumHAcceptors(mol)
    rotatable_bonds = Descriptors.NumRotatableBonds(mol)
    atoms = rdchem.Mol.GetNumAtoms(mol)
    heavy_atoms = rdchem.Mol.GetNumHeavyAtoms(mol)
    molar_refractivity = Crippen.MolMR(mol)
    topological_polar_surface_area = QED.properties(mol).PSA
    formal_charge = rdmolops.GetFormalCharge(mol)
    rings = rdMolDescriptors.CalcNumRings(mol)

    descr = np.array([weight, logp, h_bond_donor, h_bond_acceptors, rotatable_bonds, atoms, heavy_atoms,
                      molar_refractivity, topological_polar_surface_area, formal_charge, rings])
    return descr


def whim_descriptor(smiles: str, seed=0xf00d):
    from rdkit import Chem
    from rdkit.Chem import AllChem, rdMolDescriptors
    mol = Chem.MolFromSmiles(smiles)
    # Add hydrogens
    mh = Chem.AddHs(mol)
    # Use distance geometry to obtain initial coordinates for a molecule
    AllChem.EmbedMolecule(mh, useRandomCoords=True, useBasicKnowledge=True, randomSeed=seed,
                          clearConfs=True, maxAttempts=5)
    # Do a quick force field optimization
    AllChem.MMFFOptimizeMolecule(mh, maxIters=1000, mmffVariant='MMFF94')

    # calculate WHIM 3D descriptor
    whim = rdMolDescriptors.CalcWHIM(mh)

    return np.array(whim)
