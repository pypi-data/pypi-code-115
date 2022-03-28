from typing import Callable, List
from molml.Data.datastructures import Molecule
import numpy as np


def tanimoto_matrix(molecules: List[Molecule], scaffold: bool = False):
    """Get an affinity matrix of Tanimoto similarity"""
    from molml.Representations.descriptors import ecfp
    from rdkit import DataStructs

    if scaffold:
        from rdkit.Chem.Scaffolds.MurckoScaffold import GetScaffoldForMol
        from rdkit.Chem import AllChem
        # Make Murcko scaffolds
        scaffolds = [GetScaffoldForMol(m.mol()) for m in molecules]
        fps = [AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=1024) for m in scaffolds]
    else:
        fps = [ecfp(m.smiles, to_array=False) for m in molecules]

    n_mols = len(molecules)
    m = np.zeros([n_mols, n_mols])
    # Calculate pairwise ditances of the upper triagnle, then copy-paste into the lower triangle of matrix (faster)
    for i in range(n_mols):
        for j in range(i, n_mols):
            m[i, j] = DataStructs.TanimotoSimilarity(fps[i], fps[j])
    m = m + m.T - np.diag(np.diag(m))

    return m


def butina(molecules: List[Molecule], cutoff: float = 0.4, scaffold: bool = True):
    """ Cluster molecules using the Butina algorithm:
        D Butina 'Unsupervised Database Clustering Based on Daylight's Fingerprint and Tanimoto Similarity:
        A Fast and Automated Way to Cluster Small and Large Data Sets', JCICS, 39, 747-750 (1999)

    Args:
        molecules: (List[Molecule]) molecules
        cutoff: (float) Tanimoto cutoff for determining clusters
        scaffold: (bool) Use ECFPs computed on Murcko scaffolds (default = True)

    Returns: (List[int]) cluster labels for each molecule

    """
    from rdkit.ML.Cluster import Butina
    from rdkit import DataStructs

    if scaffold:
        from rdkit.Chem.Scaffolds.MurckoScaffold import GetScaffoldForMol
        from rdkit.Chem import AllChem
        # Make Murcko scaffolds
        scaffolds = [GetScaffoldForMol(m.mol()) for m in molecules]
        fps = [AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=1024) for m in scaffolds]
    else:
        from molml.Representations.descriptors import ecfp
        fps = [ecfp(m.smiles, to_array=False) for m in molecules]

    # first generate the distance matrix:
    dists = []
    nfps = len(fps)
    for i in range(1, nfps):
        sims = DataStructs.BulkTanimotoSimilarity(fps[i], fps[:i])
        dists.extend([1 - x for x in sims])

    # now cluster the data:
    clusters = Butina.ClusterData(dists, nfps, cutoff, isDistData=True)

    labels = [None for _ in molecules]
    for idx, clust in enumerate(clusters):
        for i in clust:
            labels[i] = idx

    return labels


def spectral(molecules: List[Molecule], k: int = 10, random_state: int = 42, scaffold: bool = False):
    """ Perform spectral clustering using their tanimoto similarity as distance matrix

    Args:
        molecules: (List[Molecule]) list of molecules
        k: (int) number of clusters
        random_state: (int) random seed

    Returns: (List[int]) cluster labels for each molecule

    """
    from sklearn.cluster import SpectralClustering

    clustering = SpectralClustering(n_clusters=k, assign_labels='kmeans', random_state=random_state,
                                    affinity='precomputed')
    # Use a tanimoto distance matrix to fit the clusters
    clustering.fit(tanimoto_matrix(molecules, scaffold=scaffold))

    return clustering.labels_


def kmeans(molecules: List[Molecule], k: int = 10, transform: Callable = None, random_state: int = 42):
    """ Cluster molecules using kmeans clustering. Uses ECFP by default.

    Args:
        molecules: (List[Molecule]) molecules
        k: (int) number of clusters
        transform: (Callable) Any function that transforms a SMILES string to a numpy array
        random_state: (int) random seed

    Returns: (List[int]) cluster labels for each molecule

    """
    from sklearn.cluster import KMeans

    if transform is None:
        x = np.array([m.ecfp() for m in molecules])
    else:
        x = np.array([transform(m.smiles) for m in molecules])

    clust = KMeans(n_clusters=k, random_state=random_state).fit(x)

    return clust.labels_


def wards():
    raise NotImplementedError
