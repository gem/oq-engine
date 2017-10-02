# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation
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

import os
# keep the following line to have a __version__
from openquake.baselib import __version__, config
from openquake.hazardlib import valid
d = os.path.dirname

# we must read the configuration file at the level of commonlib
# to be able to set the DATADIR used by the datastore; we should fix this
config.read(os.path.join(d(d(__file__)), 'engine', 'openquake.cfg'),
            multi_user=valid.boolean, port=valid.positiveint,
            terminate_workers_on_revoke=valid.boolean,
            soft_mem_limit=valid.positiveint,
            hard_mem_limit=valid.positiveint)
