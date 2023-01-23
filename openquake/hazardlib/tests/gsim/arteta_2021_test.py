# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
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

from openquake.hazardlib.gsim.arteta_2021 import (
    ArtetaEtAl2021InterVs30, ArtetaEtAl2021Inter, ArtetaEtAl2021SlabVs30,
    ArtetaEtAl2021Slab)
from openquake.hazardlib.tests.gsim.utils import BaseGSIMTestCase

"""
Module exports :class:`ArtetaEtAl2021Inter`, 'ArtetaEtAl2021Slab'
The test tables were created from a *.xlsx file created by the authors
"""


class ArtetaEtAl2021InterVs30Test(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation and the within-event
    standard deviation. The between events std is implicitly tested
    """

    GSIM_CLASS = ArtetaEtAl2021InterVs30

    def test_median(self):
        self.check('arteta_2021/ARTETAETAL2021_Vs30_SINTER_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std(self):
        pass
        self.check('arteta_2021/ARTETAETAL2021_Vs30_SINTER_Sigma.csv',
                   'arteta_2021/ARTETAETAL2021_Vs30_SINTER_Phi.csv',
                   'arteta_2021/ARTETAETAL2021_Vs30_SINTER_Tau.csv',
                   max_discrep_percentage=0.1)


class ArtetaEtAl2021InterTest(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation and the within-event
    standard deviation. The between events std is implicitly tested
    """

    GSIM_CLASS = ArtetaEtAl2021Inter

    def test_median(self):
        self.check('arteta_2021/ARTETAETAL2021_SINTER_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std(self):
        self.check('arteta_2021/ARTETAETAL2021_SINTER_Sigma.csv',
                   'arteta_2021/ARTETAETAL2021_SINTER_Phi.csv',
                   'arteta_2021/ARTETAETAL2021_SINTER_Tau.csv',
                   max_discrep_percentage=0.1)


class ArtetaEtAl2021Slab_Vs30(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation and the within-event
    standard deviation. The between events std is implicitly tested
    """

    GSIM_CLASS = ArtetaEtAl2021SlabVs30

    def test_median(self):
        self.check('arteta_2021/ARTETAETAL2021_Vs30_SSLAB_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std(self):
        self.check('arteta_2021/ARTETAETAL2021_Vs30_SSLAB_Sigma.csv',
                   'arteta_2021/ARTETAETAL2021_Vs30_SSLAB_Phi.csv',
                   'arteta_2021/ARTETAETAL2021_Vs30_SSLAB_Tau.csv',
                   max_discrep_percentage=0.1)


class ArtetaEtAl2021SlabTest(BaseGSIMTestCase):
    """
    Test the default model, the total standard deviation and the within-event
    standard deviation. The between events std is implicitly tested
    """

    GSIM_CLASS = ArtetaEtAl2021Slab

    def test_median(self):
        self.check('arteta_2021/ARTETAETAL2021_SSLAB_MEAN.csv',
                   max_discrep_percentage=0.1)

    def test_std(self):
        self.check('arteta_2021/ARTETAETAL2021_SSLAB_Sigma.csv',
                   'arteta_2021/ARTETAETAL2021_SSLAB_Phi.csv',
                   'arteta_2021/ARTETAETAL2021_SSLAB_Tau.csv',
                   max_discrep_percentage=0.1)
