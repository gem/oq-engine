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
import pandas
from openquake.baselib.general import all_equals
from openquake.hazardlib import contexts, imt
from openquake.hazardlib.tests.gsim.check_gsim import check_gsim


def read_cmaker_df(gsim, csvfnames):
    """
    :param gsim:
        a GSIM instance
    :param csvfnames:
        a list of pathnames to CSV files in the format used in
        hazardlib/tests/gsim/data, i.e. with fields rup_XXX, site_XXX,
        dist_XXX, result_type and periods
    :returns: a list RuptureContexts, grouped by rupture parameters
    """
    # build a suitable ContextMaker
    dfs = [pandas.read_csv(fname) for fname in csvfnames]
    if not all_equals([df.columns for df in dfs]):
        p = len(os.path.commonprefix(csvfnames))
        shortnames = [f[p:] for f in csvfnames]
        print('There are different columns across %s' % ', '.join(shortnames))
        cols = set.intersection(*[set(df.columns) for df in dfs])
    else:
        cols = slice(None)
    df = pandas.concat(df[cols] for df in dfs)
    imtls = {}
    cmap = {}
    for col in df.columns:
        try:
            im = str(imt.from_string(col))
        except KeyError:
            pass
        else:
            imtls[im] = [0]
            cmap[col] = im
    cmaker = contexts.ContextMaker(
        gsim.DEFINED_FOR_TECTONIC_REGION_TYPE.value, [gsim], {'imtls': imtls})
    for dist in cmaker.REQUIRES_DISTANCES:
        name = 'dist_' + dist
        df[name] = np.array(df[name].to_numpy(), cmaker.dtype[dist])
    for par in cmaker.REQUIRES_RUPTURE_PARAMETERS:
        name = 'rup_' + par
        if name not in df.columns:  # i.e. missing rake
            df[name] = np.zeros(len(df), cmaker.dtype[par])
        else:
            df[name] = np.array(df[name].to_numpy(), cmaker.dtype[par])
    return cmaker, df.rename(columns=cmap)


def gen_ctxs(df):
    """
    :param df: a DataFrame with a specific structure
    :yields: RuptureContexts
    """
    rrp = [col for col in df.columns if col.startswith('rup_')]
    pars = [col for col in df.columns if col.startswith(('dist_', 'site_'))]
    outs = df.result_type.unique()
    num_outs = len(outs)
    for rup_params, grp in df.groupby(rrp):
        ctx = contexts.RuptureContext()
        for par, rp in zip(rrp, rup_params):
            setattr(ctx, par[4:], rp)
            del grp[par]
        if 'damping' in grp.columns:
            del grp['damping']
        for rtype, gr in grp.groupby('result_type'):
            del gr['result_type']
            setattr(ctx, rtype, gr)
        for par in pars:
            out = grp[grp.result_type == outs[0]][par].to_numpy()
            setattr(ctx, par[5:], out)
        ctx.sids = np.arange(len(gr))
        assert len(gr) == len(grp) / num_outs, (len(gr), len(gr) / num_outs)
        yield ctx


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
        out_types = ["MEAN"]
        for sdt in contexts.STD_TYPES:
            if sdt in gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES:
                out_types.append(sdt.upper().replace(' ', '_') + '_STDDEV')

        cmaker, df = read_cmaker_df(gsim, fnames)
        for ctx in gen_ctxs(df):
            [out] = cmaker.get_mean_stds([ctx])
            for o, out_type in enumerate(out_types):
                if not hasattr(ctx, out_type):
                    # for instance MEAN is missing in zhao_2016_test
                    continue
                discrep = (mean_discrep_percentage if out_type == 'MEAN'
                           else std_discrep_percentage)
                for m, im in enumerate(cmaker.imtls):
                    if out_type == 'MEAN' and im != 'MMI':
                        out[o, m] = np.exp(out[o, m])
                    expected = getattr(ctx, out_type)[im].to_numpy()
                    msg = dict(out_type=out_type, imt=im)
                    for par in cmaker.REQUIRES_RUPTURE_PARAMETERS:
                        msg[par] = getattr(ctx, par)
                    discrep_percent = np.abs(out[o, m] / expected * 100 - 100)
                    if (discrep_percent > discrep).any():
                        msg['expected'] = expected
                        msg['got'] = out[o, m]
                        msg['discrep_percent'] = discrep_percent.max()
                        raise ValueError(msg)
