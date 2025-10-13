# The Hazard Library
# Copyright (C) 2012-2025 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
A Magnitude Frequency Distribution (MFD) is a function that describes the rate
(per year) of earthquakes across all magnitudes.

Package `mfd` contains the basic class for MFD --
:class:`openquake.hazardlib.mfd.base.BaseMFD`, and three actual
implementations:
:class:`openquake.hazardlib.mfd.evenly_discretized.EvenlyDiscretizedMFD`
:class:`openquake.hazardlib.mfd.truncated_gr.TruncatedGRMFD` and
:class:`openquake.hazardlib.mfd.youngs_coppersmith_1985.YoungsCoppersmith1985MFD`.
"""
import toml
from openquake.hazardlib.mfd.evenly_discretized import (  # noqa
    EvenlyDiscretizedMFD
)
from openquake.hazardlib.mfd.truncated_gr import TruncatedGRMFD  # noqa
from openquake.hazardlib.mfd.youngs_coppersmith_1985 import (  # noqa
    YoungsCoppersmith1985MFD)
from openquake.hazardlib.mfd.arbitrary_mfd import ArbitraryMFD  # noqa
from openquake.hazardlib.mfd.tapered_gr_mfd import TaperedGRMFD  # noqa
from openquake.hazardlib.mfd import multi_mfd  # noqa


def from_toml(string, bin_width):
    """
    Convert a TOML string into an MFD instance
    """
    [(name, params)] = toml.loads(string).items()
    if name == 'multiMFD':
        return multi_mfd.MultiMFD.from_params(params, bin_width)
    cls, *required = multi_mfd.ASSOC[name]
    kw = {}
    for param, value in params.items():
        kw[multi_mfd.TOML2PY.get(param, param)] = value
    if 'bin_width' in required and bin_width not in kw:
        kw['bin_width'] = bin_width
    return cls(**kw)
