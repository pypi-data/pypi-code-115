"""
Code to one-hot encode SMILES strings
Derek van Tilborg, Eindhoven University of Technology, March 2022

Adapted from:

Moret, M., Grisoni, F., Katzberger, P. & Schneider, G.
Perplexity-based molecule ranking and bias estimation of chemical language models.
ChemRxiv (2021) doi:10.26434/chemrxiv-2021-zv6f1-v2.
"""

import re
import numpy as np
import random
from rdkit import Chem
from typing import Dict


SMILES_ENCODING_ = {'end_char': 'E', 'pad_char': 'A', 'start_char': 'G',
                    'indices_token': {0: 'c', 1: 'C', 2: '(', 3: ')', 4: 'O', 5: '1', 6: '2', 7: '=', 8: 'N', 9: '@',
                                      10: '[', 11: ']', 12: 'n', 13: '3', 14: 'H', 15: 'F', 16: '4', 17: '-', 18: 'S',
                                      19: 'Cl', 20: '/', 21: 's', 22: 'o', 23: '5', 24: '+', 25: '#', 26: '\\',
                                      27: 'Br', 28: 'P', 29: '6', 30: 'I', 31: '7', 32: 'G', 33: 'E', 34: 'A'},
                    'token_indices': {'#': 25, '(': 2, ')': 3, '+': 24, '-': 17, '/': 20, '1': 5, '2': 6, '3': 13,
                                      '4': 16, '5': 23, '6': 29, '7': 31, '=': 7, '@': 9, 'A': 34, 'Br': 27, 'C': 1,
                                      'Cl': 19, 'E': 33, 'F': 15, 'G': 32, 'H': 14, 'I': 30, 'N': 8, 'O': 4, 'P': 28,
                                      'S': 18, '[': 10, '\\': 26, ']': 11, 'c': 0, 'n': 12, 'o': 22, 's': 21},
                    'vocab_size': 35, 'max_smiles_len': 200, 'min_smiles_len': 5}


class OneHotEncode:
    def __init__(self, max_len_model, n_chars, indices_token, token_indices, pad_char, start_char, end_char):
        """Initialization"""
        self.max_len_model = max_len_model
        self.n_chars = n_chars

        self.pad_char = pad_char
        self.start_char = start_char
        self.end_char = end_char

        self.indices_token = indices_token
        self.token_indices = token_indices

    def one_hot_encode(self, token_list, n_chars):
        output = np.zeros((token_list.shape[0], n_chars))
        for j, token in enumerate(token_list):
            output[j, token] = 1
        return output

    def smi_to_int(self, smi: str):
        """
        this will turn a list of smiles in string format
        and turn them into a np array of int, with padding
        """
        token_list = smi_tokenizer(smi)
        token_list = [self.start_char] + token_list + [self.end_char]
        padding = [self.pad_char] * (self.max_len_model - len(token_list))
        token_list.extend(padding)
        int_list = [self.token_indices[x] for x in token_list]
        return np.asarray(int_list)

    def int_to_smile(self, array):
        """
        From an array of int, return a list of
        molecules in string smile format
        Note: remove the padding char
        """
        all_smi = []
        for seq in array:
            new_mol = [self.indices_token[int(x)] for x in seq]
            all_smi.append(''.join(new_mol).replace(self.pad_char, ''))
        return all_smi

    def smile_to_onehot(self, smiles: str):

        lines = smiles
        n_data = len(lines)

        x = np.empty((n_data, self.max_len_model, self.n_chars), dtype=int)

        for i, smi in enumerate(lines):
            # remove return line symbols
            smi = smi.replace('\n', '')
            # tokenize
            int_smi = self.smi_to_int(smi)
            # one hot encode
            x[i] = self.one_hot_encode(int_smi, self.n_chars)

        return x

    def generator_smile_to_onehot(self, smi: str):

        smi = smi.replace('\n', '')
        int_smi = self.smi_to_int(smi)
        one_hot = self.one_hot_encode(int_smi, self.n_chars)
        return one_hot


def onehot_to_smiles(array, indices_token: dict, start_char: str, end_char: str):
    """ Convert one-hot encoded array of SMILES back to a SMILES string

    Args:
        array: (np.array) one-hot encoded numpy array with shape (mol_length, vocab_length)
        indices_token: (dict) the location of each token in the vocab. {0: 'c', 1: 'C', 2: '(', etc}
        start_char: (str) character that signals the start of the sequence
        end_char: (str) character that signals the end of the sequence

    Returns: (str) SMILES string

    """
    smiles_string = ''
    for row in array:
        token = indices_token[int(np.where(row == 1)[0])]  # Find the corresponding token to this row
        if token == end_char:  # stop if you reach the end character
            break
        if token != start_char:
            smiles_string += token
    return smiles_string


def smi_tokenizer(smi: str):
    """
    Tokenize a SMILES
    """
    pattern = "(\[|\]|Xe|Ba|Rb|Ra|Sr|Dy|Li|Kr|Bi|Mn|He|Am|Pu|Cm|Pm|Ne|Th|Ni|Pr|Fe|Lu|Pa|Fm|Tm|Tb|Er|Be|Al|Gd|Eu|te|As|Pt|Lr|Sm|Ca|La|Ti|Te|Ac|Si|Cf|Rf|Na|Cu|Au|Nd|Ag|Se|se|Zn|Mg|Br|Cl|U|V|K|C|B|H|N|O|S|P|F|I|b|c|n|o|s|p|\(|\)|\.|=|#|-|\+|\\\\|\/|:|~|@|\?|>|\*|\$|\%\d{2}|\d)"
    regex = re.compile(pattern)
    tokens = [token for token in regex.findall(smi)]

    return tokens


def is_acceptable_smiles(smile: str, allowed_chars=SMILES_ENCODING_['indices_token'].values(),
                         min_len=SMILES_ENCODING_['min_smiles_len'], max_len=SMILES_ENCODING_['max_smiles_len']):
    """ Checks which smiles

    Args:
        smile: (str) smiles string
        allowed_chars: (lst) list of allowed smiles characters ['c', 'C', '(', ')', 'O', '1', '2', '=', 'N', ... ]
        min_len: (int) minimal smiles character length (default = 5)
        max_len: (int) minimal smiles character length (default = 200)

    Returns: (bool) True = allowed smile, False = weird smile

    """
    tokens = smi_tokenizer(smile)
    return len(tokens) >= min_len and len(tokens) <= max_len and all([tok in allowed_chars for tok in tokens])


def random_smiles(smiles: str):
    """ Generate a random non-canonical SMILES string from a molecule"""
    # https://github.com/michael1788/virtual_libraries/blob/master/experiments/do_data_processing.py

    mol = Chem.MolFromSmiles(smiles)
    mol.SetProp("_canonicalRankingNumbers", "True")
    idxs = list(range(0, mol.GetNumAtoms()))
    random.shuffle(idxs)
    for i, v in enumerate(idxs):
        mol.GetAtomWithIdx(i).SetProp("_canonicalRankingNumber", str(v))
    return Chem.MolToSmiles(mol)


def smile_augmentation(smiles: str, augmentation: int = 10, max_len: int = None, try_for: int = 1000):
    """Generate n random non-canonical SMILES strings from a SMILES string with length constraints"""
    # https://github.com/michael1788/virtual_libraries/blob/master/experiments/do_data_processing.py

    if max_len is None:
        max_len = len(smiles)*1.5

    s = set()
    for i in range(try_for):
        smiles_ = random_smiles(smiles)
        if len(smiles_) <= max_len:
            s.add(smiles_)
            if len(s) == augmentation:
                break

    return list(s)


def smiles_one_hot(smiles: str, max_len_model: int = SMILES_ENCODING_['max_smiles_len'],
                     n_chars: int = SMILES_ENCODING_['vocab_size'],
                     indices_token: Dict[int, str] = SMILES_ENCODING_['indices_token'],
                     token_indices: Dict[str, int] = SMILES_ENCODING_['token_indices'],
                     pad_char: str = SMILES_ENCODING_['pad_char'],
                     start_char: str = SMILES_ENCODING_['start_char'],
                     end_char: str = SMILES_ENCODING_['end_char'],
                     min_len=SMILES_ENCODING_['min_smiles_len'],
                     max_len=SMILES_ENCODING_['max_smiles_len']):

    # if not is_acceptable_smiles(smiles, allowed_chars=indices_token.values(), min_len=min_len, max_len=max_len):
    #     raise ValueError(f"")

    OneHotEncoder = OneHotEncode(max_len_model=max_len_model+ 2,
                                 n_chars=n_chars,
                                 indices_token=indices_token,
                                 token_indices=token_indices,
                                 pad_char=pad_char,
                                 start_char=start_char,
                                 end_char=end_char)

    onehot = OneHotEncoder.smile_to_onehot([smiles])
    return onehot.reshape(-1, n_chars)
