# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2026 GEM Foundation
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
from openquake.risklib.scientific import TIME_EVENTS
from openquake.commonlib.outputs import DISPLAY_NAME as DISPLAY_NAME


AGGRISK_FIELD_DESCRIPTION = {
    'contents': 'Contents loss (USD)',
    'nonstructural': 'Nonstructural loss (USD)',
    'structural': 'Structural loss (USD)',
    'economic': 'Economic loss (USD)',
    'occupants': 'Fatalities',
    'occupants_day': 'Daytime fatalities',
    'occupants_night': 'Night-time fatalities',
    'occupants_transit': 'Transit-hours fatalities',
    'occupants_avg': 'Average fatalities',
    'area': 'Floor area lost (m²)',
    'number': 'Buildings destroyed',
    'residents': 'Rendered homeless',
    'injured': 'Number of injured people',
    'injured_day': 'Daytime injured people',
    'injured_night': 'Night-time injured people',
    'injured_transit': 'Transit-hours injured people',
    'injured_avg': 'Average injured people',
    'affectedpop': 'Affected population',
    'embodied_carbon': 'Embodied carbon loss (tCO₂e)',
    'value': 'Exposed value',
    'loss_type': 'Loss type',
    'lossmea': 'Mean',
    'q50': 'Median',
    'q05': '5th percentile',
    'q95': '95th percentile',
}


INJURED = ('Seriously or critically injured people according to the'
           ' Abbreviated Injury Severity (www.aisinjuryscale.org)')

AGGRISK_FIELD_EXPLANATION = {
    'affectedpop': ('Population living in buildings that sustained at least'
                    ' moderate damage'),
    'area': ('Total floor area (in m²) of buildings that sustained complete'
             ' damage'),
    'injured': INJURED,
    # injured_day, injured_night, injured_transit
    **{f'injured_{te}': INJURED for te in TIME_EVENTS},
    'number': ('Number of buildings that sustained a level of damage beyond'
               ' repair (extensive damage or higher)'),
    'occupants': 'Number of fatalities',
    # occupants_day, occupants_night, occupants_transit
    **{f'occupants_{te}': 'Number of fatalities' for te in TIME_EVENTS},
    'residents': ('Population living in buildings that sustained at least'
                  ' extensive damage'),
    'economic': ('Sum of structural and contents economic loss (in USD)'),
}


# meaning of the exposed value, depending on the loss type
EXPOSED_VALUE_EXPLANATION = {
    'residents': ('Population that lives in the area included in the impact'
                  ' analysis'),
    'area': ('Total floor area of buildings, including all storeys, in the'
             ' area included in the impact analysis'),
    'occupants': ('Population assumed to be inside the building stock in the'
                  ' area included in the impact analysis when the event'
                  ' occurs'),
    'number': ('Number of buildings in the area included in the impact'
               ' analysis'),
    'economic': ('Replacement value of buildings and their contents in the'
                 ' area included in the impact analysis'),
}


# meaning of the statistics reported for each impact metric
REPORTED_VALUE_EXPLANATION = {
    'lossmea': ('Arithmetic mean of the estimated impact values, accounting'
                ' for the uncertainties propagated through the impact'
                ' analysis'),
    'q50': ('The 50th percentile of the estimated impact distribution. Half'
            ' of the estimated impact values are below the median and half'
            ' are above it'),
    'q05': ('Value below which 5% of the estimated impact values fall. It'
            ' represents the lower end of the range of plausible impacts'),
    'q95': ('Value below which 95% of the estimated impact values fall. It'
            ' represents the upper end of the range of plausible impacts'),
}


EXPOSURE_FIELD_DESCRIPTION = {
    'number': 'Buildings',
    'contents': 'Contents value (USD)',
    'nonstructural': 'Nonstructural value (USD)',
    'structural': 'Structural value (USD)',
    'residents': 'Residents',
    'area': 'Floor area (m²)',
    'occupants_day': 'Occupants day',
    'occupants_night': 'Occupants night',
    'occupants_transit': 'Occupants transit hours',
    'occupants_avg': 'Average number of occupants',
    'mmi': ('Macroseismic intensity (MMI) to which the given group'
            ' of assets is subjected'),
    'embodied_carbon': 'Embodied carbon (tCO₂e)',
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
