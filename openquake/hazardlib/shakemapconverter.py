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
"""\
A converter from Shakemap files (see https://earthquake.usgs.gov/scenario/product/shakemap-scenario/sclegacyshakeout2full_se/us/1465655085705/about_formats.html) to numpy composite arrays.
"""
import numpy
from openquake.baselib.node import node_from_xml


F32 = numpy.float32
SHAKEMAP_FIELDS = set(
    'LON LAT SVEL PGA PSA03 PSA10 PSA30 STDPGA STDPSA03 STDPSHA10 STDPSA30'
    .split())


def get_shakemap_array(grid_file):
    """
    :param grid_file: a shakemap file
    :returns: array with fields lon, lat, vs30, val, std
    """
    grid_node = node_from_xml(grid_file)
    fields = grid_node.getnodes('grid_field')
    lines = grid_node.grid_data.text.strip().splitlines()
    rows = [line.split() for line in lines]

    # the indices start from 1, hence the -1 below
    idx = {f['name']: int(f['index']) - 1 for f in fields
           if f['name'] in SHAKEMAP_FIELDS}
    out = {name: [] for name in idx}
    has_sa = False
    for name in idx:
        i = idx[name]
        if name.startswith('PSA'):
            has_sa = True
        out[name].append([float(row[i]) for row in rows])
    if has_sa:  # expect SA for 0.3, 1.0 and 3.0
        dt = numpy.dtype([('PGA', F32), ('SA(0.3)', F32), ('SA(1.0)', F32),
                          ('SA(3.0)', F32)])
    else:  # expect only PGA
        dt = numpy.dtype([('PGA', F32)])
    dtlist = [('lon', F32), ('lat', F32), ('vs30', F32),
              ('val', dt), ('std', dt)]
    data = numpy.zeros(len(rows), dtlist)
    data['lon'] = F32(out['LON'])
    data['lat'] = F32(out['LAT'])
    data['val']['PGA'] = F32(out['PGA'])
    data['std']['PGA'] = F32(out['STDPGA'])
    data['vs30'] = F32(out['SVEL'])
    if has_sa:
        data['val']['SA(0.3)'] = F32(out['PSA03'])
        data['val']['SA(1.0)'] = F32(out['PSA10'])
        data['val']['SA(3.0)'] = F32(out['PSA30'])
        data['std']['SA(0.3)'] = F32(out.get('STDPSA03', 0))
        data['std']['SA(1.0)'] = F32(out.get('STDPSA10', 0))
        data['std']['SA(3.0)'] = F32(out.get('STDPSA30', 0))
    return data


example_sa = """\
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

example_pga = """\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<shakemap_grid xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://earthquake.usgs.gov/eqcenter/shakemap" xsi:schemaLocation="http://earthquake.usgs.gov http://earthquake.usgs.gov/eqcenter/shakemap/xml/schemas/shakemap.xsd" event_id="18278231" shakemap_id="18278231" shakemap_version="1" code_version="3.5.1489" process_timestamp="2018-02-18T01:38:09Z" shakemap_originator="IV" map_status="RELEASED" shakemap_event_type="ACTUAL">
<event event_id="18278231" magnitude="3.4" depth="17.9" lat="38.477000" lon="14.830000" event_timestamp="2018-02-18T01:13:47UTC" event_network="IV" event_description="Isole Eolie (Messina)" />
<grid_specification lon_min="13.580000" lat_min="37.643666" lon_max="16.080000" lat_max="39.310334" nominal_lon_spacing="0.008333" nominal_lat_spacing="0.008333" nlon="301" nlat="201" />
<event_specific_uncertainty name="pga" value="0.472627" numsta="10" />
<event_specific_uncertainty name="pgv" value="0.527333" numsta="10" />
<event_specific_uncertainty name="mi" value="0.194903" numsta="10" />
<grid_field index="1" name="LON" units="dd" />
<grid_field index="2" name="LAT" units="dd" />
<grid_field index="3" name="PGA" units="pctg" />
<grid_field index="4" name="PGV" units="cms" />
<grid_field index="5" name="MMI" units="intensity" />
<grid_field index="6" name="STDPGA" units="ln(pctg)" />
<grid_field index="7" name="URAT" units="" />
<grid_field index="8" name="SVEL" units="ms" />
<grid_data>
13.5800 39.3103 0 0 1 0.51 1 603
13.5883 39.3103 0 0 1 0.51 1 603
13.5967 39.3103 0 0 1 0.51 1 603
</grid_data>
</shakemap_grid>
"""
