#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2017, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
from openquake.baselib.python3compat import decode
from openquake.commonlib import writers
from openquake.risklib import riskinput


class LossCurveExporter(object):
    """
    Exporter for the loss curves. The most important method is
    `.export(export_type, what)` where `export_type` is a string like 'csv',
    and `what` is a string called export specifier. Here are some examples
    for the export specifier:

    sid-42/   # export loss curves of site #42 for all realizations
    sid-42/rlz-003   # export all loss curves of site #42, realization #3
    sid-42/stats   # export statistical loss curves of site #42
    sid-42/mean   # export mean loss curves of site #42
    sid-42/quantile-0.1   # export quantile loss curves of site #42

    ref-a1/   # export loss curves of asset a1 for all realizations
    ref-a1/rlz-003   # export loss curves of asset a1, realization 3
    ref-a1/stats     # export statistical loss curves of asset a1
    ref-a1/mean     # export mean loss curves of asset a1
    ref-a1/quantile-0.1    # export quantile loss curves of asset a1
    """
    def __init__(self, dstore):
        self.dstore = dstore
        self.assetcol = dstore['assetcol']
        arefs = [decode(aref) for aref in self.dstore['asset_refs']]
        self.str2asset = {arefs[asset.idx]: asset for asset in self.assetcol}
        self.asset_refs = self.dstore['asset_refs'].value
        self.loss_types = dstore.get_attr('composite_risk_model', 'loss_types')
        self.R = len(dstore['realizations'])

    def parse(self, what):
        """
        :param what:
            can be 'ref-asset1/rlz-1', 'sid-1/rlz-2', ...
        """
        spec, key = what.split('/')
        if not spec.startswith(('ref-', 'sid-')):
            raise ValueError('Wrong specification in %s' % what)
        if not (key in ('', 'stats', 'mean') or key.startswith(('rlz-')) or
                key.startswith('quantile-')):
            raise ValueError('Wrong export key in %s' % what)
        if spec.startswith('sid-'):  # passed the site ID
            sid = int(spec[4:])
            aids = []
            arefs = []
            for aid, rec in enumerate(self.assetcol.array):
                if rec['site_id'] == sid:
                    aids.append(aid)
                    arefs.append(self.asset_refs[rec['idx']])
        else:  # passed the asset name
            arefs = [spec[4:]]
            aids = [self.str2asset[arefs[0]].ordinal]
        return aids, arefs, spec, key

    def export_csv(self, spec, asset_refs, curves_dict):
        """
        :param asset_ref: name of the asset
        :param curves_dict: a dictionary tag -> loss curves
        """
        writer = writers.CsvWriter(fmt=writers.FIVEDIGITS)
        for key in sorted(curves_dict):
            recs = curves_dict[key]
            data = [['asset', 'loss_type', 'loss', 'poe']]
            for loss_type in self.loss_types:
                array = recs[loss_type]
                for aref, losses, poes in zip(
                        asset_refs, array['losses'], array['poes']):
                    for loss, poe in zip(losses, poes):
                        data.append((aref, loss_type, loss, poe))
            dest = self.dstore.build_fname(
                'loss_curves', '%s-%s' % (spec, key), 'csv')
            writer.save(data, dest)
        return writer.getsaved()

    def export(self, export_type, what):
        """
        :param export_type: 'csv', 'json', ...
        :param what: string describing what to export
        :returns: list of exported file names
        """
        aids, arefs, spec, key = self.parse(what)
        if not key or key.startswith('rlz-'):
            curves = self.export_curves_rlzs(aids, key)
        else:  # statistical exports
            curves = self.export_curves_stats(aids, key)
        return getattr(self, 'export_' + export_type)(spec, arefs, curves)

    def export_curves_rlzs(self, aids, key):
        """
        :returns: a dictionary key -> record of dtype loss_curve_dt
        """
        if 'loss_curves-rlzs' in self.dstore:  # classical_risk
            data = self.dstore['loss_curves-rlzs'][aids]  # shape (A, R)
            if key:
                rlzi = int(key[4:])
                return {key: data[:, rlzi]}
            return {'rlz-%03d' % rlzi: data[:, rlzi] for rlzi in range(self.R)}

        # otherwise event_based
        builder = self.dstore['riskmodel'].curve_builder
        assets = [self.assetcol[aid] for aid in aids]
        rlzi = int(key[4:]) if key else None  # strip rlz-
        ratios = riskinput.LossRatiosGetter(self.dstore).get(aids, rlzi)
        if rlzi:
            return {rlzi: builder.build_curves(assets, ratios, rlzi)}
        # return a dictionary will all realizations
        return {'rlz-%03d' % rlzi: builder.build_curves(assets, ratios, rlzi)
                for rlzi in range(self.R)}

    def export_curves_stats(self, aids, key):
        """
        :returns: a dictionary rlzi -> record of dtype loss_curve_dt
        """
        oq = self.dstore['oqparam']
        stats = ['mean'] + ['quantile-%s' % q for q in oq.quantile_loss_curves]
        stat2idx = {stat: s for s, stat in enumerate(stats)}
        if 'loss_curves-stats' in self.dstore:  # classical_risk
            dset = self.dstore['loss_curves-stats']
            data = dset[aids]  # shape (A, S)
            if key == 'stats':
                return {stat: data[:, s] for s, stat in enumerate(stats)}
            else:  # a specific statistics
                return {key: data[stat2idx[key]]}
        # otherwise event_based
        raise NotImplementedError
