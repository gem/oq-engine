# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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
import h5py
import numpy
import unittest
from openquake.hazardlib.imt import PGA, PGV, SA
from openquake.hazardlib.contexts import (DistancesContext,
                                          RuptureContext,
                                          SitesContext)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase
from openquake.hazardlib.gsim.ita04 import (AmbraseysEtAl1996Normal,
                                            AmbraseysEtAl1996Reverse)
from openquake.hazardlib.const import StdDev
ROOT_FOLDER = os.path.dirname(__file__)
TABLE_FOLDER = os.path.join(ROOT_FOLDER, './../../gsim/ita04_tables/')


class Box(object):
    class TestITA04(unittest.TestCase):
        TABLE_FILE = ''
        GMM = None

        def test_mean(self):
            # The shape of the array with distances and with imls is:
            # - number of distances
            # - ?
            # - number of magnitudes
            fle = h5py.File(self.TABLE_FILE, 'r')
            dsts = fle['Distances'][:]
            dsts_metric = fle["Distances"].attrs["metric"]
            mags = fle['Mw'][:]
            stds_types = [StdDev.TOTAL]
            gmm = eval(self.GMM)()
            for idx, mag in enumerate(mags):
                print(mag)
                for imt_label in list(fle['IMLs'].keys()):
                    imls = fle['IMLs'][imt_label][:, 0, idx]
                    # imls = tmp[:, 0, idx]
                    dst = dsts[:, 0, idx]
                    dctx = DistancesContext()
                    sctx = SitesContext()
                    rctx = RuptureContext()
                    setattr(rctx, 'mag', mag)
                    setattr(dctx, dsts_metric, dst)
                    imt = eval(imt_label)()
                    print(imls, dst)
                    mean, std = gmm.get_mean_and_stddevs(sctx, rctx, dctx,
                                                         imt, stds_types)
                numpy.testing.assert_almost_equal(imls, numpy.exp(mean))


class TestAmbraseys1996NormalTest(Box.TestITA04):
    TABLE_FILE = os.path.join(TABLE_FOLDER, 'asb96_normal.hdf5')
    GMM = 'AmbraseysEtAl1996Normal'


class AmbraseysEtAl1996ReverseTest(Box.TestITA04):
    TABLE_FILE = os.path.join(TABLE_FOLDER, 'asb96_reverse.hdf5')
    GMM = 'AmbraseysEtAl1996Reverse'
