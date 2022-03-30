"""
Helper functions for the Matrix Product State-based state preparation
--------------------------------------------
Helper functions that are used in the MPS technique, or just generally
helpful when using this technique.
"""

import numpy as np
from tqdm import tqdm


def get_max_s_val_ratio(s_vals):
    max_ratio_idx = np.zeros((len(s_vals), 3))

    for i, s_vals_core in enumerate(s_vals):
        if len(s_vals_core) == 1:
            max_ratio_idx[i][:] = i, 0, 0
        else:
            ratio = (s_vals_core[0] / s_vals_core)
            max_ratio_idx[i][:] = i, np.argmax(ratio), np.max(ratio)

    return max_ratio_idx


def truncate_s_vals(s_vals, index_to_drop):
    s_vals_truncated = []
    for m, s_vals_core in enumerate(s_vals):
        if m == int(index_to_drop[0]):
            s_vals_truncated.append(s_vals_core[:int(index_to_drop[1])])
        else:
            s_vals_truncated.append(s_vals_core)
    return s_vals_truncated


def coarse_truncate_s_vals(s_vals, threshold=1e-15):
    coarse_truncated_s_vals = []
    for s_vals_core in s_vals:
        coarse_truncated_s_vals.append(s_vals_core[s_vals_core > threshold])

    return coarse_truncated_s_vals


def generate_ranks_from_s_vals(s_vals):
    ranks = np.zeros(len(s_vals), dtype=np.int32)
    for i, s_vals_core in enumerate(s_vals):
        ranks[i] = len(s_vals_core)
    return ranks


def get_best_valid_s_val_truncation_idx(s_vals):
    ranks = generate_ranks_from_s_vals(s_vals)
    valid_trunc_mask = np.insert(2 * (ranks[1:] - 1) >= ranks[:-1], 0, True)
    valid_s_val_truncations = get_max_s_val_ratio(s_vals)[valid_trunc_mask]
    max_idx = valid_s_val_truncations.argmax(axis=0)[-1]

    return valid_s_val_truncations[max_idx][:-1]


def mean_fractional_entropy(y_amp):
    assert len(y_amp.shape) == 1, "y_amp should be 1-D."
    num_qubits = np.log2(y_amp.shape[0])
    assert np.round(num_qubits) == int(num_qubits), "len(y_amp) should be 2^N."
    num_qubits = int(num_qubits)

    entropies = np.zeros((num_qubits - 1))
    frac_entropies = np.zeros((num_qubits - 1))
    for bond in range(num_qubits - 1):
        yamp_unfolded = np.reshape(y_amp, (2**(bond + 1), -1), "F")
        qubits_A = bond + 1
        qubits_B = num_qubits - qubits_A
        qubits = min(qubits_A, qubits_B)
        maximal_entropy = qubits
        s = np.linalg.svd(yamp_unfolded, compute_uv=False)
        s2 = np.abs(s)**2
        nonzero_mask = s2 != 0
        temp = np.zeros(s2.shape)
        temp[nonzero_mask] = s2[nonzero_mask]*np.log2(s2[nonzero_mask])
        entropies[bond] = -np.sum(temp)
        frac_entropies[bond] = entropies[bond]/maximal_entropy

    mean_frac_entropy = np.mean(frac_entropies)
    return mean_frac_entropy


def entropy_of_random_sparse(num_qubits, sparsity, num_to_generate, seed=None):

    generator = np.random.default_rng(seed)

    x = np.arange(2**num_qubits)
    all_entropies = []
    for _ in tqdm(range(num_to_generate)):
        rand_indices = generator.choice(x,
                                        int(np.round((1 - sparsity)*len(x))),
                                        False)
        y_amp = np.zeros(len(x))
        y_amp[rand_indices] = generator.random(len(rand_indices))

        # Normalize amplitude
        M = 1/np.sqrt(np.sum(np.abs(y_amp)**2))
        y_amp *= M

        all_entropies.append(mean_fractional_entropy(y_amp))

    return all_entropies


def bit_string(nqubits, decimal):
    """
    Returns a binary string that is nqubits wide, with the least significant
    bit at the right.

    Parameters
    ----------
    nqubits : int
        Number of qubits. This is necessary to determine the width of the
        bit string.
    decimal : int
        Decimal integer between 0 and 2**nqubits - 1 to convert into a binary
        bit string.

    Returns
    -------
    out : string
        Binary bit string of decimal with the least significant bit at the
        right.
    """

    # Error checking on range of decimals
    if not isinstance(decimal, (int, np.integer)):
        ermsg = "decimal must be an integer."
        raise TypeError(ermsg)
    if np.abs(decimal) > (2**nqubits-1):
        ermsg = (f"For a bit string of size {nqubits}" +
                 f", |decimal| must be smaller than {2**nqubits-1}.")
        raise ValueError(ermsg)

    str1 = f"{{:0>{nqubits}b}}"
    out = str1.format(decimal)

    return out


def update_kwargs_dict(default_kwargs, kwargs=None):
    """
    Given a kwargs dict, this function updates it with the key, value pair
    of default_kwargs if the key in default_kwargs is not found in kwargs.
    Otherwise, that particular key in kwargs is not updated.

    Parameters
    ----------
    default_kwargs : dict
        Dictionary of default keyword arguments.
    kwargs : dict, optional
        Keyword arguments supplied to some function. The default is None.

    Returns
    -------
    kwargs : dict
        kwargs that has been updated by with default_kwargs.
    """

    if kwargs is not None:
        options = {key: val for (key, val) in default_kwargs.items()
                   if key not in kwargs.keys()}
        kwargs.update(options)
    else:
        kwargs = default_kwargs

    return kwargs


def state_fidelity(statevec_a, statevec_b):
    return np.abs(statevec_b.conj().dot(statevec_a)) ** 2
