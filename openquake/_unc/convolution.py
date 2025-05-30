import numpy as np
from numba import jit
from openquake._unc.bins import get_bins_data, get_bins_from_params

TOLERANCE = 1e-6


def get_pmf(vals: np.ndarray, wei: np.ndarray = None, res: int = 10,
            scaling: str = None):
    """
    Returns a probability mass funtion from a set of values plus the bins data.

    :param vals:
        An instance of :class:`numpy.ndarray` with the values to use for the
        calculation of the PMF
    :param wei:
        An instance of :class:`numpy.ndarray` with the same cardinality of
        `vals`
    :param res:
        Resolution (i.e. number of bins per logaritmic interval)
    :param scaling:
        The way in which the resolution scales per each order of magnitude.
    """
    # Compute weights is not provided
    wei = wei if wei is not None else np.ones_like(vals) * 1. / len(vals)

    # Compute bins data and bins
    min_power, num_powers = get_bins_data(vals)
    bins = get_bins_from_params(min_power, res, num_powers)

    # Compute the histogram
    his, _ = np.histogram(vals, bins=bins, weights=wei)
    assert len(his) == num_powers*res

    return min_power, num_powers, his


@jit(nopython=True)
def _get_vals(pmfa, pmfb, midsa, midsb):
    # Outputs
    yvals = np.zeros(len(pmfa)*len(pmfb))
    xvals = np.zeros_like(yvals)
    cnt = 0
    for i, a in enumerate(pmfa):
        for j, b in enumerate(pmfb):
            xvals[cnt] = midsa[i] + midsb[j]
            yvals[cnt] = a * b
            cnt += 1
    xvals = xvals[:cnt+1]
    yvals = yvals[:cnt+1]
    return xvals, yvals


def conv(pmfa, min_power_a, res_a, num_powers_a,
         pmfb, min_power_b, res_b, num_powers_b, res=None):
    """
    Computing the convolution of the two histograms

    :param pmfa:
    :param min_power_a:
    :param res_a:
    :param num_powers_a:
    :param pmfb:
    :param min_power_b:
    :param res_b:
    :param num_powers_b:
    :returns:
        min_power_o, res, num_powers_o, pmfo
    """

    # Checking input
    num = num_powers_a*res_a
    if len(pmfa) != num:
        fmt = '|pmfa| {:d} ≠ (number of powers * resolution) {:d}*{:d}={:d}'
        msg = fmt.format(len(pmfa), num_powers_a, res_a, num)
        raise ValueError(msg)

    # Checking input
    num = num_powers_b*res_b
    if len(pmfb) != num:
        fmt = '|pmfb| {:d} ≠ (number of powers * resolution) {:d}*{:d}={:d}'
        msg = fmt.format(len(pmfb), num_powers_b, res_b, int(num))
        raise ValueError(msg)

    # Checking input
    if np.abs(1.0-np.sum(pmfa)) > TOLERANCE and len(pmfa):
        smm = np.sum(pmfa)
        print(np.abs(1.0-smm))
        raise ValueError(f'Sum of elements pmfa not equal to 1 {smm:8.4e}')
    if np.abs(1.0-np.sum(pmfb)) > TOLERANCE and len(pmfb):
        smm = np.sum(pmfb)
        print(np.abs(1.0-smm))
        raise ValueError(f'Sum of elements pmfb not equal to 1 {smm:8.4e}')

    # Defining the resolution of output
    if res is None:
        res = np.amin([res_a, res_b])

    # Compute bin data and bins for output
    vmin = np.floor(np.log10(10**min_power_a + 10**min_power_b))
    vmax = np.ceil(np.log10(10**(min_power_a + num_powers_a) +
                            10**(min_power_b + num_powers_b)))
    min_power_o = int(vmin)
    num_powers_o = int(vmax - vmin)
    try:
        bins_o = get_bins_from_params(min_power_o, res, num_powers_o)
    except:
        breakpoint()

    # Compute mid points
    bins_a = get_bins_from_params(min_power_a, res_a, num_powers_a)
    bins_b = get_bins_from_params(min_power_b, res_b, num_powers_b)
    midsa = bins_a[:-1] + np.diff(bins_a)/2
    midsb = bins_b[:-1] + np.diff(bins_b)/2

    xvals, yvals = _get_vals(pmfa, pmfb, midsa, midsb)
    idxs = np.digitize(xvals, bins_o)
    idxs -= 1
    pmfo = np.zeros(len(bins_o)-1, dtype=np.float64)

    # For DEBUGGING
    # for i, x, y in zip(idxs, xvals, yvals):
    #    print(i, x, y)

    for i in np.unique(idxs):
        pmfo[i] = np.sum(yvals[idxs == i])
        msg = "The sum of pmfo is {:f}".format(sum(pmfo))

    assert len(pmfo) == res*num_powers_o

    if not np.abs(1.0-np.sum(pmfo)) < TOLERANCE:
        print(msg)
        print(pmfa)
        print(pmfb)
        print(pmfo)

    return min_power_o, res, num_powers_o, pmfo
