# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2018-2025 GEM Foundation
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
import numpy
from openquake.hazardlib import nrml
from openquake.hazardlib.geo.geodetic import geodetic_distance
from openquake.commonlib import readinput, logs, datastore
from openquake.calculators.base import calculators
from openquake.calculators.extract import extract, WebExtractor


class OpenQuake(object):
    """
    Singleton object with convenience functions which are aliases over
    engine utilities for work in the interactive interpreter.
    """
    def __init__(self):
        try:
            from matplotlib import pyplot
            self.plt = pyplot
            self.fig, self.ax = pyplot.subplots()
        except Exception:  # for instance, no Tkinter
            pass
        self.extract = extract
        self.read = datastore.read
        self.nrml = nrml
        self.get__exposure = readinput.get_exposure
        self.get_oqparam = readinput.get_oqparam
        self.get_site_collection = readinput.get_site_collection
        self.get_composite_source_model = readinput.get_composite_source_model
        self.get_exposure = readinput.get_exposure
        self.geodetic_distance = geodetic_distance
        # TODO: more utilities will be added when deemed useful

    def get_calc(self, job_ini):
        log = logs.init(job_ini)
        log.__enter__()
        return calculators(log.get_oqparam(), log.calc_id)

    def webex(self, calc_id, what):
        """Extract data from a remote calculation"""
        ex = WebExtractor(calc_id)
        try:
            return ex.get(what)
        finally:
            ex.close()

    def ex(self, calc_id, what):
        """Extract data from a local engine server"""
        ex = WebExtractor(calc_id, 'http://localhost:8800', '', '')
        try:
            return ex.get(what)
        finally:
            ex.close()

    def read_ruptures(self, calc_id, field):
        dstore = datastore.read(calc_id)
        lst = []
        for name, dset in dstore.items():
            if name.startswith('rup_'):
                lst.append(dset[field][:])
        return numpy.concatenate(lst)

    def fix_latin1(self, fname):
        "Try to convert from latin1 to utf8"
        with open(fname, encoding='latin1') as f:
            data = f.read()
        with open(fname, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(data)
        print('Converted %s: WARNING: it may still be wrong' % fname)

    def poe2period(self, poe):
        """
        Converts probabilities into return periods
        """
        return -1/numpy.log(1-poe)

    def period2poe(self, t):
        """
        Converts return periods into probabilities
        """
        return 1-numpy.exp(-1/t)


def main(script=None, args=()):
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


main.script = 'python script to run (if any)'
main.args = dict(help='arguments to pass to the script', nargs='*')
