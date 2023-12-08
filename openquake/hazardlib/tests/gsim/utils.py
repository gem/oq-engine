# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2023 GEM Foundation
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

import os
import csv
import logging
import unittest

import numpy as np
import pandas
from openquake.baselib.general import all_equals, RecordBuilder
from openquake.hazardlib import contexts, imt

NORMALIZE = False


def _normalize(float_string):
    try:
        return str(float(float_string))
    except ValueError:  # the string was not a float (i.e. is a siteclass)
        return float_string


def normalize(csvfnames):
    """
    Fix headers and input rows of the given files
    """
    allcols = []
    ifield = {}
    data = {}
    idata = {}
    for fname in csvfnames:
        with open(fname) as f:
            reader = csv.reader(f)
            fields = []
            for f in next(reader):
                try:
                    im = imt.from_string(f)
                except KeyError:
                    fields.append(f)
                else:
                    fields.append(str(im.period) if im.period else f)
            allcols.append(fields)
            ifield[fname] = {f: i for i, f in enumerate(fields)}
            data[fname] = list(reader)
            assert len(data[fname])
            idata[fname] = set()
            for row in data[fname]:
                tup = tuple(_normalize(v) for v, f in zip(row, fields)
                            if f.startswith(('site_', 'rup_', 'dist_')))
                idata[fname].add(tup)
    colset = set.intersection(*[set(cols) for cols in allcols])
    commonset = set.intersection(*[idata[fname] for fname in csvfnames])
    assert commonset, 'No common inputs in ' + ' '.join(csvfnames)
    for fname, cols in zip(csvfnames, allcols):
        idx = ifield[fname]
        cols = [c for c in cols if c in colset]
        writer = csv.writer(open(fname, 'w', newline='', encoding='utf-8'))
        writer.writerow(cols)
        for row in data[fname]:
            tup = tuple(_normalize(v) for v, f in zip(row, cols)
                        if f.startswith(('site_', 'rup_', 'dist_')))
            if tup in commonset:
                writer.writerow([row[idx[c]] for c in cols])


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
    num_rows = sum(len(df) for df in dfs)
    if num_rows == 0:
        raise ValueError('The files %s are empty!' % ' '.join(csvfnames))
    logging.info('\n%s' % gsim)
    logging.info('num_checks = {:_d}'.format(num_rows))
    if not all_equals([sorted(df.columns) for df in dfs]):
        colset = set.intersection(*[set(df.columns) for df in dfs])
        cols = [col for col in dfs[0].columns if col in colset]
        extra = set()
        ncols = []
        for df in dfs:
            ncols.append(len(df.columns))
            extra.update(set(df.columns) - colset)
        print('\n%s\nThere are %d extra columns %s over a total of %s' %
              (csvfnames[0], len(extra), extra, ncols))
    else:
        cols = slice(None)
    df = pandas.concat(d[cols] for d in dfs)
    sizes = {r: len(d) for r, d in df.groupby('result_type')}
    if not all_equals(list(sizes.values())):
        raise ValueError('Inconsistent number of rows: %s' % sizes)
    imts = []
    cmap = {}
    for col in df.columns:
        try:
            im = str(imt.from_string(col if col.startswith("AvgSA")
                                     else col.upper()))
        except KeyError:
            pass
        else:
            imts.append(im)
            cmap[col] = im
    assert imts
    imtls = {im: [0] for im in sorted(imts)}
    trt = gsim.DEFINED_FOR_TECTONIC_REGION_TYPE
    mags = ['%.2f' % mag for mag in df.rup_mag.unique()]
    cmaker = contexts.ContextMaker(
        trt.value if trt else "*", [gsim], {'imtls': imtls, 'mags': mags},
        extraparams={col[5:] for col in df.columns if col.startswith('site_')})
    dtype = RecordBuilder(**cmaker.defaultdict).zeros(0).dtype
    for dist in cmaker.REQUIRES_DISTANCES:
        name = 'dist_' + dist
        df[name] = np.array(df[name].to_numpy(), dtype[dist])
    for sitepar in cmaker.REQUIRES_SITES_PARAMETERS:
        name = 'site_' + sitepar
        df[name] = np.array(df[name].to_numpy(), dtype[sitepar])
    for par in cmaker.REQUIRES_RUPTURE_PARAMETERS:
        name = 'rup_' + par
        if name not in df.columns:  # i.e. missing rake
            df[name] = np.zeros(len(df), dtype[par])
        else:
            df[name] = np.array(df[name].to_numpy(), dtype[par])
    return cmaker, df.rename(columns=cmap)


def gen_ctxs(df):
    """
    :param df: a DataFrame with a specific structure
    :returns: a list of RuptureContexts
    """
    ctxs = []
    rrp = [col for col in df.columns if col.startswith('rup_')]
    pars = [col for col in df.columns if col.startswith(('dist_', 'site_'))]
    if 'dist_rrup' not in pars:
        dist_type = [p for p in pars if p.startswith('dist_')][0][5:]
    else:
        dist_type = 'rrup'
    outs = df.result_type.unique()
    num_outs = len(outs)
    rup_id = 0
    for rup_params, grp in df.groupby(rrp):
        inputs = [gr[rrp + pars].to_numpy()
                  for _, gr in grp.groupby('result_type')]
        if len(inputs) < num_outs:
            dic = dict(zip(rrp + pars, inputs[0][0]))
            print('\nMissing some data for %s' % dic)
            continue
        assert all_equals(inputs), 'Use NORMALIZE=True'
        if len(rrp) == 1:
            rup_params = [rup_params]
        ctx = contexts.RuptureContext()
        ctx.src_id = 0
        ctx.rup_id = rup_id
        rup_id += 1
        for par, rp in zip(rrp, rup_params):
            setattr(ctx, par[4:], rp)
            del grp[par]
        if 'damping' in grp.columns:
            del grp['damping']
        for rtype, gr in grp.groupby('result_type'):
            del gr['result_type']
            setattr(ctx, rtype, gr)
        for par in pars:
            value = grp[grp.result_type == outs[0]][par].to_numpy()
            setattr(ctx, par[5:], value)  # dist_, site_ parameters
        ctx.sids = np.arange(len(gr))
        if dist_type != 'rrup':
            ctx.rrup = getattr(ctx, dist_type)
        assert len(gr) == len(grp) / num_outs, (len(gr), len(gr) / num_outs)
        ctxs.append(ctx)
    return ctxs


class BaseGSIMTestCase(unittest.TestCase):
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    GSIM_CLASS = None

    def check(self, *filenames, max_discrep_percentage,
              std_discrep_percentage=None, truncation_level=99., **kwargs):
        if std_discrep_percentage is None:
            std_discrep_percentage = max_discrep_percentage
        fnames = [os.path.join(self.BASE_DATA_PATH, filename)
                  for filename in filenames]
        if NORMALIZE:
            normalize(fnames)
            return
        gsim = self.GSIM_CLASS(**kwargs)
        out_types = ["MEAN"]
        for sdt in contexts.STD_TYPES:
            if sdt in gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES:
                out_types.append(sdt.upper().replace(' ', '_') + '_STDDEV')
        cmaker, df = read_cmaker_df(gsim, fnames)
        if truncation_level != 99.:
            cmaker.truncation_level = truncation_level
        for ctx in gen_ctxs(df):
            ctx.occurrence_rate = 0
            out = cmaker.get_mean_stds([ctx], split_by_mag=False)[:, 0]
            for o, out_type in enumerate(out_types):
                if not hasattr(ctx, out_type):
                    # for instance MEAN is missing in zhao_2016_test
                    continue
                discrep = (max_discrep_percentage if out_type == 'MEAN'
                           else std_discrep_percentage)
                for m, im in enumerate(cmaker.imtls):
                    if out_type == 'MEAN' and im != 'MMI':
                        out[o, m] = np.exp(out[o, m])
                    expected = getattr(ctx, out_type)[im].to_numpy()
                    msg = dict(out_type=out_type, imt=im)
                    discrep_percent = np.abs(out[o, m] / expected * 100 - 100)
                    idxs, = np.where(discrep_percent > discrep)
                    if len(idxs):
                        idx = idxs[0]
                        msg['expected'] = expected[idx]
                        msg['got'] = out[o, m, idx]
                        msg['discrep_percent'] = discrep_percent[idx]
                        for par in (cmaker.REQUIRES_DISTANCES |
                                    cmaker.REQUIRES_SITES_PARAMETERS):
                            msg[par] = getattr(ctx, par)[idx]
                        for par in cmaker.REQUIRES_RUPTURE_PARAMETERS:
                            msg[par] = getattr(ctx, par)
                        raise ValueError(msg)
