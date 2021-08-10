# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
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
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import os

import numpy as np
from openquake.hazardlib import contexts
from openquake.hazardlib.tests.gsim.check_gsim import check_gsim


class BaseGSIMTestCase(unittest.TestCase):
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    GSIM_CLASS = None

    def check(self, filename, max_discrep_percentage, **kwargs):
        gsim = self.GSIM_CLASS(**kwargs)
        with open(os.path.join(self.BASE_DATA_PATH, filename)) as f:
            errors, stats = check_gsim(gsim, f, max_discrep_percentage)
        if errors:
            raise AssertionError(stats)
        print()
        print(stats)

    def check_all(self, *filenames, mean_discrep_percentage,
                  std_discrep_percentage, **kwargs):
        fnames = [os.path.join(self.BASE_DATA_PATH, filename)
                  for filename in filenames]
        gsim = self.GSIM_CLASS(**kwargs)
        cmaker, df = contexts.read_cmaker_df(gsim, fnames)
        for ctx in cmaker.from_df(df):
            [out] = cmaker.get_mean_stds([ctx])
            for o, out_type in enumerate(cmaker.out_types):
                discrep = (mean_discrep_percentage if out_type == 'MEAN'
                           else std_discrep_percentage)
                for m, imt in enumerate(cmaker.imtls):
                    if out_type == 'MEAN' and imt != 'MMI':
                        out[o, m] = np.exp(out[o, m])
                    expected = getattr(ctx, out_type)[imt].to_numpy()
                    msg = dict(out_type=out_type, imt=imt)
                    for par in cmaker.REQUIRES_RUPTURE_PARAMETERS:
                        msg[par] = getattr(ctx, par)
                    discrep_percent = np.abs(out[o, m] / expected * 100 - 100)
                    if (discrep_percent > discrep).any():
                        msg['expected'] = expected
                        msg['got'] = out[o, m]
                        msg['discrep_percent'] = discrep_percent.max()
                        raise ValueError(msg)
