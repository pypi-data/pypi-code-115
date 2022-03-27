# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/14_display.ipynb (unless otherwise specified).

__all__ = ['calculate_sequence_coverage']

# Cell

import re

def calculate_sequence_coverage(target_sequence:str, peptide_list:list)->(int, int, float, list):
    """
    Calculate the percentage of a target protein covered by a list of peptides.
    Args:
        target_sequence (str): the protein sequence against which the peptide_list should be compared.
        peptide_list (List[str]): the list of peptides (str) to be compared against the target_sequence.
    return:
        int: number of residues in target_sequence.
        int: number of residues in target_sequence covered by peptides in peptide_list.
        float: percentage of residues in target_sequence covered by peptides in peptide_list.
        list (dict{str:bool}): list of dicts where keys are residue one-letter codes and values are bool (covered = True, not-covered = False).
    """
    residues = [
        {'res': res, 'covered': False} for res in target_sequence
    ]
    for peptide in peptide_list:
        # remove lowercase PTM markers if present
        peptide = ''.join(_ for _ in peptide if not _.islower() and _.isalpha())
        matches = [m.start() for m in re.finditer('(?=%s)' %peptide, target_sequence)]
        for m in matches:
            for index in range(m, m+len(peptide)):
                residues[index]['covered'] = True

    total = len(residues)
    total_covered = len([r for r in residues if r['covered'] == True])
    coverage_percent = total_covered / total * 100

    return total, total_covered, coverage_percent, residues
