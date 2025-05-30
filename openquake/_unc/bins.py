import numpy as np

SMALL = 1e-20

def get_bins_data(samples: np.ndarray):
    """
    Computes the lowest power of 10 and the number of powers of 10 needed to
    the cover values in the `samples` dataset.

    :param samples:
        A set of values for which we want to obtain the corresponding bins
    :returns:
        A tuple with two floats, the minimum power of 10 and the number of
        powers.
    """

    # If all the values are 0
    if np.all(np.abs(samples) < SMALL):
        return None, None

    # Fixing 0 values
    idx_small = samples < SMALL
    samples[idx_small] = SMALL+SMALL*0.01

    # Find histogram params
    sam = samples[np.abs(samples) > SMALL]
    min_power = np.floor(np.log10(np.min(sam)))
    upv = np.ceil(np.log10(np.max(sam)))
    num_powers = upv - min_power

    return min_power, num_powers


def get_bins_from_params(min_power: int, nsampl_per_power: int,
                         num_powers: int, scale='constant'):
    """
    :param min_power:
        Lowest power i.e. 10^min_power corresponds to the left limit of the
        first bin of the histogram
    :param nsampl_per_power:
        The number of samples in each power
    :param num_powers:
        The range covered by the bins
    """
    assert num_powers > 0
    res = nsampl_per_power
    if scale == 'constant':
        upv = min_power + num_powers
        nint = int(res*(upv-min_power))+1
        bins = np.logspace(min_power, upv, nint)
    else:
        msg = 'The {:s} scaling option is not supported'.format(scale)
        raise ValueError(msg)
    return bins
