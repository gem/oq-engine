# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2025 GEM Foundation
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
from openquake.baselib.python3compat import decode
from openquake.baselib import writers
from openquake.calculators.post_risk import get_loss_builder


class LossCurveExporter(object):
    """
    Exporter for the loss curves. The most important method is
    `.export(export_type, what)` where `export_type` is a string like 'csv',
    and `what` is a string called export specifier. Here are some examples
    for the export specifier:

    rlzs/sid-42   # export loss curves of site #42 for all realizations
    rlz-003/sid-42   # export all loss curves of site #42, realization #3
    stats/sid-42   # export statistical loss curves of site #42
    mean/sid-42   # export mean loss curves of site #42
    quantile-0.1/sid-42   # export quantile loss curves of site #42

    rlzs/ref-a1         # export loss curves of asset a1 for all realizations
    rlz-003/ref-a1      # export loss curves of asset a1, realization 3
    stats/ref-a1        # export statistical loss curves of asset a1
    mean/ref-a1         # export mean loss curves of asset a1
    quantile-0.1/ref-a1 # export quantile loss curves of asset a1
    """
    def __init__(self, dstore):
        self.dstore = dstore
        self.oq = dstore['oqparam']
        try:
            self.builder = get_loss_builder(dstore, self.oq)
        except KeyError:  # no 'events' for non event_based_risk
            pass
        self.assetcol = dstore['assetcol']
        arefs = decode(self.assetcol['id'])
        self.str2asset = dict(zip(arefs, self.assetcol))
        self.asset_refs = arefs
        self.loss_types = dstore.get_attr('crm', 'loss_types')
        self.R = dstore['full_lt'].get_num_paths()

    def parse(self, what):
        """
        :param what:
            can be 'rlz-1/ref-asset1', 'rlz-2/sid-1', ...
        """
        if '/' not in what:
            key, spec = what, ''
        else:
            key, spec = what.split('/')
        if spec and not spec.startswith(('ref-', 'sid-')):
            raise ValueError('Wrong specification in %s' % what)
        elif spec == '':  # export losses for all assets
            aids = slice(0, len(self.assetcol.array))
            arefs = self.asset_refs
        elif spec.startswith('sid-'):  # passed the site ID
            sid = int(spec[4:])
            aids = []
            arefs = []
            for aid, rec in enumerate(self.assetcol.array):
                if rec['site_id'] == sid:
                    aids.append(aid)
                    arefs.append(self.asset_refs[aid])
        elif spec.startswith('ref-'):  # passed the asset name
            arefs = [spec[4:]]
            aids = [self.str2asset[arefs[0]]['ordinal']]
        else:
            raise ValueError('Wrong specification in %s' % what)
        return aids, arefs, spec, key

    def export_csv(self, spec, asset_refs, curves_dict):
        """
        :param asset_refs: names of the asset
        :param curves_dict: a dictionary tag -> loss curves
        """
        aval = self.assetcol.arr_value(self.loss_types)
        writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
        ebr = hasattr(self, 'builder')
        for key in sorted(curves_dict):
            recs = curves_dict[key]
            if ebr:
                data = [['asset_id', 'loss_type', 'loss_value', 'loss_ratio',
                         'return_period', 'annual_frequency_of_exceedence']]
            else:
                data = [['asset_id', 'loss_type', 'loss_value', 'loss_ratio',
                         'poe']]
            for li, lt in enumerate(self.loss_types):
                if ebr:  # event_based_risk
                    array = recs[:, :, li]  # shape (A, P, LI)
                    periods = self.builder.return_periods
                    for aref, losses, val in sorted(zip(
                            asset_refs, array, aval[:, li])):
                        for period, loss in zip(periods, losses):
                            data.append((aref, lt, loss, loss/val,
                                         period, 1. / period))
                else:  # classical_risk
                    array = recs[lt]  # shape (A,) loss_curve_dt
                    for aref, losses, poes, val in sorted(zip(
                            asset_refs, array['losses'],
                            array['poes'], aval[:, li])):
                        for loss, poe in zip(losses, poes):
                            data.append((aref, lt, loss, loss/val, poe))
            dest = self.dstore.build_fname(
                'loss_curves', '%s-%s' % (spec, key) if spec else key, 'csv')
            com = dict(
                kind=key,
                risk_investigation_time=self.oq.risk_investigation_time
                or self.oq.investigation_time)
            writer.save(data, dest, comment=com,
                        renamedict=dict(id='asset_id'))
        return writer.getsaved()

    def export(self, export_type, what):
        """
        :param export_type: 'csv', 'json', ...
        :param what: string describing what to export
        :returns: list of exported file names
        """
        aids, arefs, spec, key = self.parse(what)
        if key.startswith('rlz'):
            curves = self.export_curves_rlzs(aids, key)
        else:  # statistical exports
            curves = self.export_curves_stats(aids, key)
        return getattr(self, 'export_' + export_type)(spec, arefs, curves)

    def export_curves_rlzs(self, aids, key):
        """
        :returns: a dictionary key -> record of dtype loss_curve_dt
        """
        if 'loss_curves-stats' in self.dstore:  # classical_risk
            if self.R == 1:
                data = self.dstore['loss_curves-stats'][aids]  # shape (A, 1)
            else:
                data = self.dstore['loss_curves-rlzs'][aids]  # shape (A, R)
            if key.startswith('rlz-'):
                rlzi = int(key[4:])
                return {key: data[:, rlzi]}
            # else key == 'rlzs', returns all data
            return {'rlz-%03d' % rlzi: data[:, rlzi] for rlzi in range(self.R)}

        # otherwise event_based
        curves = self.dstore['curves-rlzs'][aids]  # shape (A, R, P)
        if key.startswith('rlz-'):
            rlzi = int(key[4:])
            return {'rlz-%03d' % rlzi: curves[:, rlzi]}
        else:  # key is 'rlzs', return a dictionary will all realizations
            # this may be disabled in the future unless an asset is specified
            dic = {}
            for rlzi in range(self.R):
                dic['rlz-%03d' % rlzi] = curves[:, rlzi]
            return dic

    def export_curves_stats(self, aids, key):
        """
        :returns: a dictionary rlzi -> record of dtype loss_curve_dt
        """
        oq = self.dstore['oqparam']
        stats = oq.hazard_stats().items()  # pair (name, func)
        stat2idx = {stat[0]: s for s, stat in enumerate(stats)}
        if 'loss_curves-stats' in self.dstore:  # classical_risk
            dset = self.dstore['loss_curves-stats']
            data = dset[aids]  # shape (A, S)
            if key == 'stats':
                return {stat[0]: data[:, s] for s, stat in enumerate(stats)}
            else:  # a specific statistics
                return {key: data[:, stat2idx[key]]}
        elif 'curves-stats' in self.dstore:  # event_based_risk
            dset = self.dstore['curves-stats']
            data = dset[aids]
            if key == 'stats':
                return {stat[0]: data[:, s] for s, stat in enumerate(stats)}
            else:  # a specific statistics
                return {key: data[:, stat2idx[key]]}
        else:
            raise KeyError('no loss curves in %s' % self.dstore)
