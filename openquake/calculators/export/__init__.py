# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2025 GEM Foundation
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
import zipfile
import logging
from openquake.baselib.general import CallableDict
from openquake.baselib.writers import write_csv


DISPLAY_NAME = {
    'asce07': 'ASCE 7 Parameters',
    'asce41': 'ASCE 41 Parameters',
    'mag_dst_eps_sig': "Deterministic Earthquake Scenarios",
    'job': 'job.zip',
    'asset_risk': 'Exposure + Risk',
    'exposure': 'Exposure',
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
    'aggcurves': 'Aggregate Risk Curves',
    'aggcurves-stats': 'Aggregate Risk Curves Statistics',
    'avg_gmf': 'Average Ground Motion Field',
    'bcr-rlzs': 'Benefit Cost Ratios',
    'bcr-stats': 'Benefit Cost Ratios Statistics',
    'cs-stats': 'Mean Conditional Spectra',
    'mce': 'MCE calculations',
    'mce_governing': 'ASCE7: MCEr SRAs',
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
}


AGGRISK_FIELD_DESCRIPTION = {
    'contents': 'Contents loss (USD)',
    'nonstructural': 'Nonstructural loss (USD)',
    'structural': 'Structural loss (USD)',
    'occupants': 'Fatalities',
    'area': 'Floor area lost (m2)',
    'number': 'Buildings beyond repair',
    'residents': 'Rendered homeless',
    'injured': 'Number of injured people',
    'affectedpop': ('Number of people living in buildings '
                    'with moderate or higher damage'),
}

EXPOSURE_FIELD_DESCRIPTION = {
    'number': 'Buildings',
    'contents': 'Contents value (USD)',
    'nonstructural': 'Nonstructural value (USD)',
    'structural': 'Structural value (USD)',
    'residents': 'Residents',
    'area': 'Floor area (m2)',
    'occupants_day': 'Occupants day',
    'occupants_night': 'Occupants night',
    'occupants_transit': 'Occupants transit hours',
    'occupants_avg': 'Average number of occupants',
    'mmi': ('Macroseismic intensity (MMI) to which the given group'
            ' of assets is subjected'),
}


class MissingExporter(Exception):
    """
    Raised when there is not exporter for the given pair (dskey, fmt)
    """


def export_csv(ekey, dstore):
    """
    Default csv exporter for arrays stored in the output.hdf5 file

    :param ekey: export key
    :param dstore: datastore object
    :returns: a list with the path of the exported file
    """
    name = ekey[0] + '.csv'
    try:
        array = dstore[ekey[0]][()]
    except AttributeError:
        # this happens if the key correspond to a HDF5 group
        return []  # write a custom exporter in this case
    if len(array.shape) == 1:  # vector
        array = array.reshape((len(array), 1))
    return [write_csv(dstore.export_path(name), array)]


def keyfunc(ekey):
    """
    Extract the name before the slash:

    >>> keyfunc(('risk_by_event', 'csv'))
    ('risk_by_event', 'csv')
    >>> keyfunc(('risk_by_event/1', 'csv'))
    ('risk_by_event', 'csv')
    >>> keyfunc(('risk_by_event/1/0', 'csv'))
    ('risk_by_event', 'csv')
    """
    fullname, ext = ekey
    return (fullname.split('/', 1)[0], ext)


export = CallableDict(keyfunc)
export.sanity_check = False  # overridden in the tests
export.from_db = False  # overridden when exporting from db


@export.add(('input', 'zip'))
def export_input_zip(ekey, dstore):
    """
    Export the data in the `input` datagroup as a .zip file
    """
    dest = dstore.export_path('input.zip')
    with zipfile.ZipFile(
            dest, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for k, data in dstore.retrieve_files():
            logging.info('Archiving %s' % k)
            z.writestr(k, data)
    return [dest]
