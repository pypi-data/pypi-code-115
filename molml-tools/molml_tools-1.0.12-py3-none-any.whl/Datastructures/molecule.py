""" Molecule class that holds everything about a molecule. Based on RDkit"""
from rdkit import Chem
from molml.Representations.descriptors import ecfp


class Molecule:
    def __init__(self, smiles: str, y: float = None, id: str = None):
        self.smiles = smiles
        self.y = y
        self.id = id

    def mol(self):
        return Chem.MolFromSmiles(self.smiles)

    def ecfp(self, to_array: bool = True, radius: int = 2, nbits: int = 1024):
        # Calculate the morgan fingerprint
        return ecfp(self.smiles, to_array, radius, nbits)

    def show(self, size: tuple = (500, 500), kekulize: bool = True):
        """ Plot an image of the molecule """
        from rdkit.Chem import Draw
        Draw.ShowMol(self.mol(), size=size, kekulize=kekulize)

    def __repr__(self):
        return self.smiles
