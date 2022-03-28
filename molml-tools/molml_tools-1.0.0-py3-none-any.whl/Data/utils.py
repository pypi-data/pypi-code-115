from molml.Data.datastructures import Molecule
import pandas as pd

def read_csv(filename: str, smiles_col: str, label_col: str = None, id_col: str = None,
                 remove_empty_rows: bool = True):

    # Read the data
    df = pd.read_csv(filename, low_memory=True, usecols=list(filter(None, [smiles_col, id_col, label_col])))

    df.columns = list(filter(None, ['smiles',
                                    'id' if id_col is not None else None,
                                    'y' if label_col is not None else None]))

    # remove rows containing na's
    if remove_empty_rows:
        df.dropna(axis=0, inplace=True)

    molecules = []
    for idx, smiles in enumerate(df.smiles):

        y = df.loc[idx, 'y'] if label_col is not None else None
        id = df.loc[idx, 'id'] if id_col is not None else None
        molecules.append(Molecule(smiles, y, id))

    return molecules