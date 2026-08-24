# The Hazard Library
# Copyright (C) 2026 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
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
"""Baker and Bradley (2017) cross-IMT correlation model.

The coefficient matrix is the corrected ``rhoDataPD.csv`` electronic
supplement published by the authors. It contains aggregate total-residual
correlations computed with Equation 2 of the paper. The 2025 corrigendum
corrected erroneous Z1.0 and earthquake-region inputs used in the original
analysis. The authors' corrected analysis is maintained at
https://github.com/bakerjw/NGAW2_correlations.

References
----------
Baker, J. W., and Bradley, B. A. (2017). Intensity measure correlations
observed in the NGA-West2 database, and dependence of correlations on rupture
and site parameters. Earthquake Spectra, 33(1), 145-156.
https://doi.org/10.1193/060716EQS095M

Baker, J. W., and Bradley, B. A. (2025). Corrigendum to "Intensity measure 
correlations observed in the NGA-West2 database, and dependence of 
correlations on rupture and site parameters". Earthquake Spectra,
41(2), 1825-1827. https://doi.org/10.1177/87552930241245554
"""

from pathlib import Path

import numpy

from openquake.hazardlib.correlation_models.base import (
    CrossIMTCorrelationModel, ResidualComponent)
from openquake.hazardlib.correlation_models.registry import register_model
from openquake.hazardlib.imt import PGA, PGV, RSD575, RSD595, SA


_SA_PERIODS = numpy.array([
    0.01, 0.02, 0.022, 0.025, 0.029, 0.03, 0.032, 0.035,
    0.036, 0.04, 0.042, 0.044, 0.045, 0.046, 0.048, 0.05,
    0.055, 0.06, 0.065, 0.067, 0.07, 0.075, 0.08, 0.085,
    0.09, 0.095, 0.1, 0.11, 0.12, 0.13, 0.133, 0.14,
    0.15, 0.16, 0.17, 0.18, 0.19, 0.2, 0.22, 0.24,
    0.25, 0.26, 0.28, 0.29, 0.3, 0.32, 0.34, 0.35,
    0.36, 0.38, 0.4, 0.42, 0.44, 0.45, 0.46, 0.48,
    0.5, 0.55, 0.6, 0.65, 0.667, 0.7, 0.75, 0.8,
    0.85, 0.9, 0.95, 1.0, 1.1, 1.2, 1.3, 1.4,
    1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.2, 2.4,
    2.5, 2.6, 2.8, 3.0, 3.2, 3.4, 3.5, 3.6,
    3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0, 5.5,
    6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5,
    10.0,
], dtype=numpy.float64)

_DATA = Path(__file__).with_name('data') / 'baker_bradley_2017.csv'
_CORRELATION = numpy.loadtxt(_DATA, delimiter=',', dtype=numpy.float64)
if _CORRELATION.shape != (109, 109):
    raise ValueError(
        f'Expected a 109 by 109 Baker-Bradley table, got '
        f'{_CORRELATION.shape}')
_CORRELATION.setflags(write=False)

_OTHER_IMT_INDEX = {
    'RSD575': 105,
    'RSD595': 106,
    'PGA': 107,
    'PGV': 108,
}


def _sa_index(period):
    """Return the table index for a published SA period."""
    indexes = numpy.flatnonzero(numpy.isclose(
        _SA_PERIODS, period, rtol=0.0, atol=1E-12))
    if not indexes.size:
        raise ValueError(
            'BakerBradley2017 does not publish a correlation value for '
            f'SA({period:g}); use one of its 105 tabulated periods')
    return int(indexes[0])


def _imt_index(imt):
    if imt.name in _OTHER_IMT_INDEX:
        return _OTHER_IMT_INDEX[imt.name]
    return _sa_index(imt.period)


@register_model(
    description=('Baker and Bradley (2017) total-residual amplitude and '
                 'duration correlation'))
class BakerBradley2017(CrossIMTCorrelationModel):
    """Corrected total-residual amplitude and duration correlation.

    The paper reports active-shallow-crustal NGA-West2 records with magnitude
    greater than 5 and Joyner-Boore distance below 100 km. SA is supported at
    the 105 published, 5%-damped periods from 0.01 to 10 s. RSD575 and RSD595
    are also directly calibrated. The amplitude IMTs use RotD50, whereas the
    duration GMM uses the geometric mean; model-wide component metadata is
    therefore intentionally unset.
    """

    DEFINED_FOR_RESIDUAL_COMPONENT = ResidualComponent.TOTAL
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {
        PGA, PGV, RSD575, RSD595, SA}
    DEFINED_FOR_SA_DAMPING = 5.0
    DEFINED_FOR_SA_PERIOD_RANGE = (0.01, 10.0)

    def _validate_imt_combination(self, imts):
        for imt in imts:
            if imt.name == 'SA':
                _sa_index(imt.period)

    def _rho(self, from_imt, to_imt, context=None):
        return _CORRELATION[
            _imt_index(from_imt), _imt_index(to_imt)]
