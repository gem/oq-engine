# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2019 GEM Foundation
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
import runpy
from functools import partial
import numpy
from openquake.baselib import sap
from openquake.hazardlib import nrml


class OpenQuake(object):
    """
    Singleton object with convenience functions which are aliases over
    engine utilities for work in the interactive interpreter.
    """
    def __init__(self):
        from openquake.baselib.datastore import read
        from openquake.hazardlib.geo.geodetic import geodetic_distance
        from openquake.commonlib import readinput, calc
        from openquake.calculators.extract import extract
        try:
            from matplotlib import pyplot
            self.plt = pyplot
            self.fig, self.ax = pyplot.subplots()
        except Exception:  # for instance, no Tkinter
            pass
        self.lookfor = partial(numpy.lookfor, module='openquake')
        self.extract = extract
        self.read = read
        self.nrml = nrml
        self.get__exposure = readinput.get_exposure
        self.get_oqparam = readinput.get_oqparam
        self.get_site_collection = readinput.get_site_collection
        self.get_composite_source_model = readinput.get_composite_source_model
        self.get_exposure = readinput.get_exposure
        self.make_hmap = calc.make_hmap
        self.geodetic_distance = geodetic_distance
        # TODO: more utilities when be added when deemed useful


@sap.script
def shell(script=None, args=()):
    """
    Start an embedded (i)python instance with a global object "o" or
    run a Python script in the engine environment.
    """
    if script:
        sys.argv = sys.argv[2:]  # strip ['oq', 'shell']
        runpy.run_path(script, run_name='__main__')
        return
    o = OpenQuake()  # noqa
    try:
        import IPython
        IPython.embed(banner1='IPython shell with a global object "o"')
    except ImportError:
        import code
        code.interact(banner='Python shell with a global object "o"',
                      local=dict(o=o))


shell.arg('script', 'python script to run (if any)')
shell.arg('args', 'arguments to pass to the script', nargs='*')
