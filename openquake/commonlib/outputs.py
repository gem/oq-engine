# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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

"""Display names of calculation outputs."""

DISPLAY_NAME = {
    'asce07': 'ASCE 7 Parameters',
    'asce41': 'ASCE 41 Parameters',
    'asce41_sa_final': 'ASCE 41 Response Spectra',
    'spectra_asce41': 'ASCE 41 Calculations',
    'mag_dst_eps_sig': "Deterministic Earthquake Scenarios",
    'job': 'job.zip',
    'asset_risk': 'Exposure + Risk',
    'exposure': 'Exposure',
    'exposure_by_liquefaction_lse':
        'Exposure grouped by Region and by Liquefaction LSE',
    'exposure_by_landslide_lse':
        'Exposure grouped by Region and by Landslide LSE',
    'gmf_data': 'Ground Motion Fields',
    'damages-rlzs': 'Asset Risk Distributions',
    'damages-stats': 'Asset Risk Statistics',
    'mean_rates_by_src': 'Hazard Curves per Source',
    'mean_disagg_by_src': 'Mag-Dist-Eps Disaggregation per Source',
    'risk_by_event': 'Aggregated Risk By Event',
    'events': 'Events',
    'event_based_mfd': 'Annual Frequency of Events',
    'avg_losses-rlzs': 'Average Asset Losses',
    'avg_losses-stats': 'Average Asset Losses Statistics',
    'loss_curves-rlzs': 'Asset Loss Curves',
    'loss_curves-stats': 'Asset Loss Curves Statistics',
    'loss_maps-rlzs': 'Asset Loss Maps',
    'loss_maps-stats': 'Asset Loss Maps Statistics',
    'aggexp_tags': 'Aggregated Exposure Values',
    'aggrisk': 'Aggregate Risk',
    'aggrisk-stats': 'Aggregate Risk Statistics',
    'agg_risk': 'Total Risk',
    'avg_losses_by': 'Average Losses By',
    'aggcurves': 'Aggregate Risk Curves',
    'aggcurves-stats': 'Aggregate Risk Curves Statistics',
    'avg_gmf': 'Average Ground Motion Field',
    'bcr-rlzs': 'Benefit Cost Ratios',
    'bcr-stats': 'Benefit Cost Ratios Statistics',
    'cs-stats': 'Mean Conditional Spectra',
    'mce': 'MCE calculations',
    'mce_governing': 'ASCE 7 MCEr Response Spectrum',
    'median_spectra': 'Median Spectra per Site and PoE',
    'median_spectrum_disagg': 'Median Spectrum Disaggregation',
    'mmi_tags': 'Exposure grouped by Admin1 and MMI',
    'reinsurance-avg_policy': 'Average Reinsurance By Policy',
    'reinsurance-avg_portfolio': 'Average Reinsurance',
    'reinsurance-risk_by_event': 'Reinsurance By Event',
    'reinsurance-aggcurves': 'Aggregated Reinsurance Curves',
    'ruptures': 'Earthquake Ruptures',
    'site_model': 'Site Model',
    'hcurves': 'Hazard Curves',
    'hmaps': 'Hazard Maps',
    'hmaps-stats': 'Hazard Maps Statistics',
    'uhs': 'Uniform Hazard Spectra',
    'disagg-rlzs': 'Disaggregation Outputs Per Realization',
    'disagg-stats': 'Statistical Disaggregation Outputs',
    'realizations': 'Realizations',
    'rtgm': 'Risk Targeted Ground Motion',
    'src_loss_table': 'Source Loss Table',
    'fullreport': 'Full Report',
    'input': 'Input Files',
    'infra-avg_loss': 'Average Infrastructure Loss',
    'infra-node_el': 'Efficiency Loss Of Nodes',
    'infra-taz_cl': 'Connectivity Loss Of TAZ Nodes',
    'infra-dem_cl': 'Connectivity Loss Of Demand Nodes',
    'infra-event_ccl': 'Complete Connectivity Loss By Event',
    'infra-event_pcl': 'Partial Connectivity Loss By Event',
    'infra-event_wcl': 'Weighted Connectivity Loss By Event',
    'infra-event_efl': 'Efficiency Loss by Event',
    'inter-avg_loss': 'Average Infrastructure Loss with Interdependencies',
    'inter-node_el': 'Efficiency Loss Of Nodes with Interdependencies',
    'inter-taz_cl': 'Connectivity Loss Of TAZ Nodes with Interdependencies',
    'inter-dem_cl': 'Connectivity Loss Of Demand Nodes with Interdependencies',
    'inter-event_ccl':
        'Complete Connectivity Loss By Event with Interdependencies',
    'inter-event_pcl':
        'Partial Connectivity Loss By Event with Interdependencies',
    'inter-event_wcl':
        'Weighted Connectivity Loss By Event with Interdependencies',
    'inter-event_efl': 'Efficiency Loss by Event with Interdependencies',
}
