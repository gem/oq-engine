# The Hazard Library
# Copyright (C) 2016-2018 GEM Foundation
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

import os
import unittest
import numpy
import numpy.testing as npt

from openquake.baselib.general import DictArray
from openquake.hazardlib.source import NonParametricSeismicSource
from openquake.hazardlib.source.rupture import BaseRupture
from openquake.hazardlib.sourceconverter import SourceConverter
from openquake.hazardlib.const import TRT
from openquake.hazardlib.geo.surface import PlanarSurface, SimpleFaultSurface
from openquake.hazardlib.geo import Point, Line
from openquake.hazardlib.geo.geodetic import point_at
from openquake.hazardlib.calc.filters import SourceFilter
from openquake.hazardlib.calc.hazard_curve import calc_hazard_curves
from openquake.hazardlib.calc.hazard_curve import classical
from openquake.hazardlib.gsim.sadigh_1997 import SadighEtAl1997
from openquake.hazardlib.gsim.si_midorikawa_1999 import SiMidorikawa1999SInter
from openquake.hazardlib.gsim.campbell_2003 import Campbell2003
from openquake.hazardlib.site import Site, SiteCollection
from openquake.hazardlib.pmf import PMF
from openquake.hazardlib.sourceconverter import SourceGroup
from openquake.hazardlib import nrml


class MutexRupturesTestCase(unittest.TestCase):

    def test(self):
        """ Test rupture calculation in case of mutually exclusive ruptures """
        d = os.path.dirname(os.path.dirname(__file__))
        source_model = os.path.join(d, 'source_model/nonparametric-source-mutex-ruptures.xml')
        groups = nrml.to_python(source_model, SourceConverter(
            investigation_time=50., rupture_mesh_spacing=2.))
        site = Site(Point(143.5, 39.5), 800, z1pt0=100., z2pt5=1.)
        sitecol = SiteCollection([site])
        imtls = DictArray({'PGA': [0.01, 0.1, 0.2, 0.5]})
        gsim_by_trt = {'Some TRT': Campbell2003()}
        hcurves = calc_hazard_curves(groups, sitecol, imtls, gsim_by_trt)
        # expected results obtained with an ipython notebook
        expected = [4.3998728e-01, 1.1011728e-01, 7.5495312e-03, 8.5812844e-06]
        npt.assert_almost_equal(hcurves['PGA'][0], expected)
