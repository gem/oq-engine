# The Hazard Library
# Copyright (C) 2020-2026, GEM Foundation
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

"""
Module :mod:`openquake.hazardlib.gsim.mgmpe.swiss_amplification` implements
Swiss amplification modifiers and their site parameter requirements for
:class:`~openquake.hazardlib.gsim.mgmpe.modifiable_gmpe.ModifiableGMPE`.
"""

import numpy as np

from openquake.hazardlib.const import StdDev


ADJUSTMENT_REQUIREMENTS = {
    'apply_swiss_amplification': {
        'gmpe_sites': frozenset(['amplfactor']),
    },
    'apply_swiss_site_specific_amplification_sa': {
        'requires_gmpe_stddev': StdDev.INTER_EVENT,
    },
}


# These are natural-log amplification and uncertainty columns, not rock-model
# coefficients. Register new period columns in site.py before adding them here.
SWISS_SITE_SPECIFIC_FIELDS = {
    0.2: ('ch_ampl02', 'ch_phis2s02', 'ch_phiss02'),
    0.3: ('ch_ampl03', 'ch_phis2s03', 'ch_phiss03'),
    0.4: ('ch_ampl04', 'ch_phis2s04', 'ch_phiss04'),
    0.6: ('ch_ampl06', 'ch_phis2s06', 'ch_phiss06'),
}
SWISS_SITE_SPECIFIC_PERIODS = tuple(SWISS_SITE_SPECIFIC_FIELDS)


def _swiss_site_specific_periods(periods):
    # Explicit selection makes requirements available before site CSV loading;
    # it must not depend on the job IMTs, which are resolved separately.
    if not isinstance(periods, (list, tuple)) or not periods:
        raise ValueError('Swiss site-specific periods must be a nonempty list')
    for period in periods:
        if (isinstance(period, (bool, np.bool_)) or not isinstance(
                period, (int, float, np.integer, np.floating)) or
                period not in SWISS_SITE_SPECIFIC_FIELDS):
            raise ValueError('Unsupported Swiss site-specific period: '
                             f'{period!r}')
    if len(set(periods)) != len(periods):
        raise ValueError('Duplicate Swiss site-specific periods')
    return tuple(periods)


def _swiss_site_specific_fields(imt, periods):
    # Period-specific columns describe 5%-damped SA; PGA is handled separately.
    # Rock SA support does not imply interpolation of these site corrections.
    if imt.name != 'SA' or imt.damping != 5.0:
        raise ValueError('Swiss site-specific amplification supports PGA and '
                         f'selected 5%-damped SA: {imt}')
    if imt.period not in periods:
        raise ValueError('No selected Swiss site-specific correction for '
                         f'{imt}')
    return SWISS_SITE_SPECIFIC_FIELDS[imt.period]


def get_site_parameters(params):
    """
    Validate Swiss modifier options and return selected site columns.
    """
    # Only the new modifier advertises its selected correction columns.
    # Do not extend the legacy Swiss context requirements or mutate the
    # caller's options: nested kwargs also determine the GSIM's TOML
    # identity.
    name = 'apply_swiss_site_specific_amplification_sa'
    if name not in params:
        return set()
    options = params[name]
    if not isinstance(options, dict) or set(options) - {'periods'}:
        raise ValueError('Swiss site-specific options only accept periods')
    if 'apply_swiss_amplification_sa' in params:
        raise ValueError('Swiss and Swiss site-specific SA amplification '
                         'cannot be applied together')
    periods = _swiss_site_specific_periods(
        options.get('periods', SWISS_SITE_SPECIFIC_PERIODS))
    return {field for period in periods
            for field in SWISS_SITE_SPECIFIC_FIELDS[period]}


def apply_swiss_amplification(ctx, imt, me, si, ta, ph):
    """
    Adds amplfactor to mean
    """
    me[:] += ctx.amplfactor


def _check_stddevs(**stddevs):
    # Zero uncertainty is valid. Include the component or site column name
    # in errors so invalid inputs can be traced to their source.
    for name, values in stddevs.items():
        if not np.all(np.isfinite(values)) or np.any(values < 0):
            raise ValueError(f'Swiss site-specific {name} must be finite '
                             'and nonnegative')


def _apply_swiss_sa_correction(amplification, phis2s, phiss, me, si, ta, ph):
    # Add the site correction to the log mean; keep the current
    # const.StdDev.INTER_EVENT (ta/tau) unchanged.
    me[:] += amplification
    # Store phi_star in const.StdDev.INTRA_EVENT through the output view ph.
    # This replaces rock phi; its original variance is not added again.
    ph[:] = np.hypot(phis2s, phiss)
    # Store sqrt(tau**2 + phi_star**2) in const.StdDev.TOTAL
    # through the output view si.
    si[:] = np.hypot(ta, ph)


def apply_swiss_amplification_sa(ctx, imt, me, si, ta, ph):
    """
    Adjust Swiss GMPEs to add amplification and correct intra-event residuals
    """

    if imt.period not in (0.3, 0.6):
        raise ValueError(f'No Swiss SA correction for {imt}; '
                         'supported periods are 0.3 and 0.6 s')
    fields = SWISS_SITE_SPECIFIC_FIELDS[imt.period]
    amplification, phis2s, phiss = (getattr(ctx, name) for name in fields)
    _apply_swiss_sa_correction(amplification, phis2s, phiss, me, si, ta, ph)


def apply_swiss_site_specific_amplification_sa(
        ctx, imt, me, si, ta, ph, periods=SWISS_SITE_SPECIFIC_PERIODS):
    """
    Apply supplied natural-log site corrections at explicitly selected periods.

    The inputs have the same meaning as the Swiss SA correction: amplification
    shifts the log mean, phi combines site-to-site and single-station terms,
    and the current between-event uncertainty is retained. PGA keeps its mean,
    phi and tau and only recomputes total uncertainty from those current terms.
    """
    _check_stddevs(tau=ta)

    # PGA keeps the mean, const.StdDev.INTRA_EVENT (ph) and
    # const.StdDev.INTER_EVENT (ta); only const.StdDev.TOTAL is rebuilt.
    # This follows the reference implementation passed by L. Danciu.
    if imt.name == 'PGA':
        _check_stddevs(phi=ph)
        si[:] = np.hypot(ta, ph)
        return

    # Select the amplification and two phi columns for this SA period.
    fields = _swiss_site_specific_fields(imt, periods)
    amplification, phis2s, phiss = (getattr(ctx, name) for name in fields)
    if not np.all(np.isfinite(amplification)):
        raise ValueError(f'Nonfinite site correction in {fields[0]}')
    _check_stddevs(**{fields[1]: phis2s, fields[2]: phiss})
    _apply_swiss_sa_correction(amplification, phis2s, phiss, me, si, ta, ph)
