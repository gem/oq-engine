# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2025 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""
Checks on the risk inputs
=========================

In the regular workflow the engine processes the inputs in the following order:

1. the risk functions are read
2. the site collection is read
3. the exposure is read and associated to the sites
4. the taxonomy mapping is read, the taxonomies are checked against the
   exposure taxonomies and the risk IDs checked against the risk functions
5. the consequence functions are checked in set_tmap

The perils are checked and you can get errors like

ValueError: Invalid key in job_r.ini: groundshking_fragility_file

The keys are checked and you can get errors like

ValueError: Unknown key groundshaking_fraglity_file in job_r.ini

The consequences are checked and for an unknown peril you will get an error

InvalidFile: consequences.csv: unknown peril='groundsaking' at line=1

The consequences are checked and for an unknown taxonomy you will get
a warning:

In consequences.csv there are taxonomies missing in the exposure: {'Concrete'}
"""

from openquake.baselib import __version__  # noqa
from openquake.risklib import read_nrml
read_nrml.update_validators()
