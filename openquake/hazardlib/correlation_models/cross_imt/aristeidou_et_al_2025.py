# The Hazard Library
# Copyright (C) 2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""Aristeidou et al. (2025) cross-IMT correlation models.

The correlations between amplitude and cumulative intensity measures were
predicted with one small feed-forward artificial neural network (ANN) per
pair of intensity measures, trained on NGA-West2 residuals. The inputs of a
network are the periods of the period-dependent IMTs of the pair, so
correlations can be evaluated at any period inside the calibrated range.

Only the weights, biases and layer description of the 24 networks are kept
in ``data/aristeidou_et_al_2025.hdf5`` (float32 values, exactly those of the
authors' Keras models); no machine-learning library is needed. A network
is evaluated with a few matrix products on NumPy arrays.

The supported pairs are the ones published by the authors: SA, Sa_avg2,
Sa_avg3 and FIV3 among themselves (SA-SA, SA-Sa_avg2, SA-Sa_avg3, SA-FIV3,
Sa_avg2-Sa_avg2, Sa_avg2-Sa_avg3, Sa_avg2-FIV3, Sa_avg3-Sa_avg3,
Sa_avg3-FIV3, FIV3-FIV3), each of SA, Sa_avg2, Sa_avg3 and FIV3 with RSD575
and RSD595 (SA is not paired with PGA or PGV), and each of Sa_avg2, Sa_avg3
and FIV3 with PGA and PGV. A pair that is not listed (for instance PGA and
PGV, or RSD575 and RSD595) raises a ``ValueError``.

References
----------
Aristeidou, S., Shahnazaryan, D., and O'Reilly, G. J. (2025). Correlation
models for next-generation amplitude and cumulative intensity measures
using artificial neural networks. Earthquake Spectra, 41(1), 851-875.
https://doi.org/10.1177/87552930241270563

Authors' implementation:
https://github.com/Savvinos-Aristeidou/ANN_correlation_models
"""

from pathlib import Path
from typing import NamedTuple

import h5py
import numpy

from openquake.hazardlib.correlation_models.base import (
    CrossIMTCorrelationModel, ResidualComponent)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import (
    FIV3, PGA, PGV, RSD575, RSD595, SA, Sa_avg2, Sa_avg3)

_DATA = Path(__file__).with_name('data') / 'aristeidou_et_al_2025.hdf5'
EPS = 1E-10

# name of the IMTs in the file with the networks
_NAMES = {'SA': 'SA', 'Sa_avg2': 'Sa_avg2', 'Sa_avg3': 'Sa_avg3',
          'FIV3': 'FIV3', 'PGA': 'PGA', 'PGV': 'PGV',
          'RSD575': 'Ds575', 'RSD595': 'Ds595'}
_PERIOD_DEPENDENT = ('SA', 'Sa_avg2', 'Sa_avg3', 'FIV3')
# the periods of the networks' training data, in seconds
_PERIOD_RANGES = {'SA': (0.01, 5.0), 'Sa_avg2': (0.1, 4.0),
                  'Sa_avg3': (0.1, 4.0), 'FIV3': (0.1, 4.0)}


def _softmax(x):
    exp_x = numpy.exp(x - x.max(axis=-1, keepdims=True))
    return exp_x / exp_x.sum(axis=-1, keepdims=True)


def _sigmoid(x):
    return 1 / (1 + numpy.exp(-x))


_ACTIVATIONS = {'linear': lambda x: x, 'softmax': _softmax,
                'tanh': numpy.tanh, 'sigmoid': _sigmoid}


class _Network(NamedTuple):
    """Dense layers of one ANN, with one weight matrix per layer."""

    weights: list
    biases: list
    activations: list
    log_input: bool  # True if the (single) input is a log-period

    def predict(self, periods):
        """Return the correlation for a ``(1, n_inputs)`` array."""
        x = numpy.log(periods) if self.log_input else periods
        for w, b, name in zip(self.weights, self.biases, self.activations):
            x = _ACTIVATIONS[name](x @ w + b)
        return float(x[0, 0])


def _read_network(group):
    # weights and biases are stored flat, layer after layer
    layers = group.attrs['layers']
    flat_w = group['weights'][:].astype(numpy.float64)
    flat_b = group['biases'][:].astype(numpy.float64)
    weights, biases = [], []
    w_start = b_start = 0
    for n_in, n_out in zip(layers[:-1], layers[1:]):
        size = n_in * n_out
        weights.append(flat_w[w_start:w_start + size].reshape(n_in, n_out))
        biases.append(flat_b[b_start:b_start + n_out])
        w_start += size
        b_start += n_out
    acts = [a.decode('ascii') for a in group.attrs['activations']]
    return _Network(weights, biases, acts, bool(group.attrs['log_input']))


def _read_networks():
    # dictionary pair -> network, for instance 'SA-FIV3' -> _Network
    with h5py.File(_DATA, 'r') as h5:
        return {pair: _read_network(group) for pair, group in h5.items()}


def _find_pair(networks, imt1, imt2):
    # return the key of the network and the IMTs in the order it expects
    name1, name2 = _NAMES[imt1.name], _NAMES[imt2.name]
    if f'{name1}-{name2}' in networks:
        return f'{name1}-{name2}', imt1, imt2
    if f'{name2}-{name1}' in networks:
        return f'{name2}-{name1}', imt2, imt1
    return None, imt1, imt2


def _periods(imt1, imt2):
    """Return the ``(1, n_inputs)`` array of periods feeding the network."""
    periods = [imt.period for imt in (imt1, imt2)
               if imt.name in _PERIOD_DEPENDENT]
    if imt1.name == imt2.name:
        # the networks of equal IMTs are symmetric: longest period first
        periods.sort(reverse=True)
    return numpy.array([periods], dtype=numpy.float64)


@register_model(
    description=('Aristeidou et al. (2025) ANN correlation of amplitude '
                 'and cumulative intensity measures'))
class AristeidouEtAl2025(CrossIMTCorrelationModel):
    """Correlation of SA, Sa_avg2, Sa_avg3, FIV3, PGA, PGV and durations.

    The models were calibrated on NGA-West2 total residuals of
    active shallow crustal earthquakes. SA is supported from 0.01 to 5 s
    and Sa_avg2, Sa_avg3 and FIV3 from 0.1 to 4 s. Only the pairs of IMTs
    listed in the module documentation are defined, therefore a set of IMTs
    is accepted only if every pair of different IMTs in it is defined.
    The horizontal components are those of the
    :class:`~openquake.hazardlib.gsim.aristeidou_2024.AristeidouEtAl2024`
    GMMs (RotD50 for PGA, PGV, SA and Sa_avg; geometric mean for the
    durations and FIV3), so the model-wide component is intentionally
    unset.
    """

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.TOTAL
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {
        PGA, PGV, RSD575, RSD595, SA, Sa_avg2, Sa_avg3, FIV3}
    DEFINED_FOR_DAMPING = 5.0
    DEFINED_FOR_PERIOD_RANGE = (0.01, 5.0)

    def __init__(self):
        # read the weights and biases of the networks from the HDF5 file
        self.networks = _read_networks()

    def _validate_imt_combination(self, imts):
        name = self.__class__.__name__
        unique = tuple(dict.fromkeys(imts))
        for imt in unique:
            if imt.name not in _PERIOD_RANGES:
                continue
            minimum, maximum = _PERIOD_RANGES[imt.name]
            if not minimum - EPS <= imt.period <= maximum + EPS:
                raise ValueError(
                    f'{name} supports {imt.name} periods from '
                    f'{minimum:g} to {maximum:g} s, not {imt.period:g} s')
        for i, imt1 in enumerate(unique):
            for imt2 in unique[i + 1:]:
                if _find_pair(self.networks, imt1, imt2)[0] is None:
                    raise ValueError(
                        f'{name} does not define a correlation between '
                        f'{imt1.string} and {imt2.string}')

    def _rho(self, from_imt, to_imt, context=None):
        if from_imt == to_imt:
            return 1.0
        key, imt1, imt2 = _find_pair(self.networks, from_imt, to_imt)
        correlation = self.networks[key].predict(_periods(imt1, imt2))
        # the ANN output is not bounded, as opposed to a correlation
        return min(max(correlation, -1.0), 1.0)
