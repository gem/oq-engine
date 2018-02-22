#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2018, GEM Foundation

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

from urllib.request import urlopen
import numpy
from openquake.baselib import sap
from openquake.baselib.node import node_from_xml

URL1 = 'http://shakemap.rm.ingv.it/shake/{}/download/grid.xml'
URL2 = 'http://shakemap.rm.ingv.it/shake/{}/download/uncertainty.xml'


def get_m(gmvs, stddevs):
    m = gmvs / 100.
    return numpy.log(
        m ** 2 / numpy.sqrt((m**2 * (numpy.exp(stddevs ** 2) - 1)) + m ** 2))


def extract_data(grid_node):
    """
    :returns: lons, lats, pgas
    """
    fields = list(grid_node.getnodes('grid_field'))
    assert fields[0]['name'] == 'LON', fields[0]
    assert fields[1]['name'] == 'LAT', fields[1]
    assert fields[2]['name'] == 'PGA', fields[2]
    assert fields[-1]['name'] == 'SVEL', fields[-1]
    lines = grid_node.grid_data.text.strip().splitlines()
    data = [line.split() for line in lines]
    lons = numpy.array([float(line[0]) for line in data])
    lats = numpy.array([float(line[1]) for line in data])
    pgas = numpy.array([float(line[2]) for line in data])
    vs30 = numpy.array([float(line[-1]) for line in data])
    return lons, lats, vs30, pgas


def apply_uncertainty(data, grid_node):
    fields = list(grid_node.getnodes('grid_field'))
    assert fields[0]['name'] == 'LON', fields[0]
    assert fields[1]['name'] == 'LAT', fields[1]
    assert fields[2]['name'] == 'STDPGA', fields[2]
    return get_m(data, stddevs)


@sap.Script
def getshakemap(shakemap_id):
    with urlopen(URL1.format(shakemap_id)) as f1:
        lons, lats, vs30, pgas = extract_data(node_from_xml(f1))

    with urlopen(URL2.format(shakemap_id)) as f2:
        node2 = node_from_xml(f2)
    apply_uncertainty(pgas, grid_node)


getshakemap.arg('shakemap_id', 'USGS shakemap ID')

"""\
See https://earthquake.usgs.gov/scenario/product/shakemap-scenario/sclegacyshakeout2full_se/us/1465655085705/about_formats.html
Here is an example of the format
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<shakemap_grid xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://earthquake.usgs.gov/eqcenter/shakemap" xsi:schemaLocation="http://earthquake.usgs.gov http://earthquake.usgs.gov/eqcenter/shakemap/xml/schemas/shakemap.xsd" event_id="us20002926" shakemap_id="us20002926" shakemap_version="9" code_version="3.5.1440" process_timestamp="2015-07-02T22:50:42Z" shakemap_originator="us" map_status="RELEASED" shakemap_event_type="ACTUAL">
<event event_id="us20002926" magnitude="7.8" depth="8.22" lat="28.230500" lon="84.731400" event_timestamp="2015-04-25T06:11:25UTC" event_network="us" event_description="NEPAL" />
<grid_specification lon_min="81.731400" lat_min="25.587500" lon_max="87.731400" lat_max="30.873500" nominal_lon_spacing="0.016667" nominal_lat_spacing="0.016675" nlon="361" nlat="318" />
<event_specific_uncertainty name="pga" value="0.000000" numsta="" />
<event_specific_uncertainty name="pgv" value="0.000000" numsta="" />
<event_specific_uncertainty name="mi" value="0.000000" numsta="" />
<event_specific_uncertainty name="psa03" value="0.000000" numsta="" />
<event_specific_uncertainty name="psa10" value="0.000000" numsta="" />
<event_specific_uncertainty name="psa30" value="0.000000" numsta="" />
<grid_field index="1" name="LON" units="dd" />
<grid_field index="2" name="LAT" units="dd" />
<grid_field index="3" name="PGA" units="pctg" />
<grid_field index="4" name="PGV" units="cms" />
<grid_field index="5" name="MMI" units="intensity" />
<grid_field index="6" name="PSA03" units="pctg" />
<grid_field index="7" name="PSA10" units="pctg" />
<grid_field index="8" name="PSA30" units="pctg" />
<grid_field index="9" name="STDPGA" units="ln(pctg)" />
<grid_field index="10" name="URAT" units="" />
<grid_field index="11" name="SVEL" units="ms" />
<grid_data>
81.7314 30.8735 0.44 2.21 3.83 1.82 2.8 1.26 0.53 1 400.758
81.7481 30.8735 0.47 2.45 3.88 1.99 3.09 1.41 0.52 1 352.659
81.7647 30.8735 0.47 2.4 3.88 1.97 3.04 1.38 0.52 1 363.687
81.7814 30.8735 0.52 2.78 3.96 2.23 3.51 1.64 0.5 1 301.17
</grid_data>
</shakemap_grid>
"""
