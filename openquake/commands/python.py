# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018 GEM Foundation
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
import sys
from openquake.baselib import sap


class _OQ(object):
    def __init__(self):
        from openquake.baselib.datastore import read
        from openquake.commonlib import readinput
        self.read = read
        self.get_oqparam = readinput.get_oqparam


@sap.Script
def python():
    """
    Start an embedded ipython instance if possible
    """
    try:
        import IPython
    except ImportError:
        sys.exit('IPython is not available')
    oq = _OQ()  # noqa
    IPython.embed(banner1='IPython shell with a global oq object')
