import os.path
import unittest
import numpy
try:
    import shapefile  # optional dependency
except ImportError:
    shapefile = None

from openquake.baselib.general import gettemp
from openquake.hazardlib.shakemap.parsers import \
    get_shakemap_array, get_array_shapefile

aae = numpy.testing.assert_almost_equal
F32 = numpy.float32
CDIR = os.path.dirname(__file__)
FIELDMAP = {
    'MMI': ('val', 'MMI'),
    'PGA': ('val', 'PGA'),
    'PSA03': ('val', 'SA(0.3)'),
    'PSA10': ('val', 'SA(1.0)'),
    'PSA30': ('val', 'SA(3.0)'),
}


class ShakemapConverterTestCase(unittest.TestCase):
    def test_pga(self):
        imt_dt = numpy.dtype([('PGA', F32)])
        array = get_shakemap_array(gettemp(example_pga))
        n = 3  # number of sites
        self.assertEqual(len(array), n)
        self.assertEqual(array.dtype.names,
                         ('lon', 'lat', 'vs30', 'val', 'std'))
        dec = 4  # four digits
        aae(array['lon'], [13.580, 13.5883, 13.5967], dec)
        aae(array['lat'], [39.3103, 39.3103, 39.3103], dec)
        aae(array['vs30'], [603, 603, 603], dec)
        val = numpy.zeros(n, imt_dt)
        std = numpy.array([(0.51,), (0.51,), (0.51,)], imt_dt)
        for imt in imt_dt.names:
            aae(array['val'][imt], val[imt])
            aae(array['std'][imt], std[imt])

    def test_sa(self):
        imt_dt = numpy.dtype([('PGA', F32), ('SA(0.3)', F32),
                              ('SA(1.0)', F32), ('SA(3.0)', F32)])
        array = get_shakemap_array(gettemp(example_sa))
        n = 4  # number of sites
        self.assertEqual(len(array), n)
        self.assertEqual(array.dtype.names,
                         ('lon', 'lat', 'vs30', 'val', 'std'))
        dec = 4  # four digits
        aae(array['lon'], [81.7314, 81.7481, 81.7647, 81.7814], dec)
        aae(array['lat'], [30.8735, 30.8735, 30.8735, 30.8735], dec)
        aae(array['vs30'], [400.758, 352.659, 363.687, 301.17], dec)
        val = numpy.array([(0.44, 1.82, 2.80, 1.26),
                           (0.47, 1.99, 3.09, 1.41),
                           (0.47, 1.97, 3.04, 1.38),
                           (0.52, 2.23, 3.51, 1.64)], imt_dt)
        std = numpy.array([(0.53, 0.00, 0.00, 0.00),
                           (0.52, 0.00, 0.00, 0.00),
                           (0.52, 0.00, 0.00, 0.00),
                           (0.50, 0.00, 0.00, 0.0)], imt_dt)
        for imt in imt_dt.names:
            aae(array['val'][imt], val[imt])
            aae(array['std'][imt], std[imt])

    def test_ghorka(self):
        # this is a test considering also the uncertainty
        grid_file = os.path.join(CDIR, 'ghorka_grid.xml')
        uncertainty_file = os.path.join(CDIR, 'ghorka_uncertainty.xml')
        array = get_shakemap_array(grid_file, uncertainty_file)
        aae(array['std']['SA(0.3)'], [0.57, 0.55, 0.56, 0.52])

    @unittest.skipUnless(shapefile, 'Missing dependency pyshp')
    def test_shapefile(self):
        dt = sorted((imt[1], F32)
                    for key, imt in FIELDMAP.items() if imt[0] == 'val')
        bbox = [('minx', F32), ('miny', F32), ('maxx', F32), ('maxy', F32)]
        dtlist = [('bbox', bbox), ('vs30', F32), ('val', dt), ('std', dt)]
        test_data = numpy.array(
            [((6.679133333333334, 47.007911201914766,
               6.6874666666666664, 47.01246666666667),
              0.5, (2.12, 0.44, 1.82, 2.80, 1.26),
              (0.8376, 0.53, 0.0, 0.0, 0.0)),
             ((6.6875333333333336, 47.01170211247184,
               6.689462114996358, 47.01246666666667),
              0.5, (2.12, 0.47, 1.99, 3.09, 1.41),
              (0.8376, 0.52, 0.0, 0.0, 0.0)),
             ((6.529133333333333, 46.95413333333333,
               6.537466666666666, 46.95899903054027),
              0.5, (2.02, 0.47, 1.97, 3.04, 1.38),
              (0.8146, 0.52, 0.0, 0.0, 0.0)),
             ((6.5625333333333336, 46.961963065996876,
               6.563892498238765, 46.96246666666667),
              0.5, (2.02, 0.52, 2.23, 3.51, 1.64),
              (0.8146, 0.50, 0.0, 0.0, 0.0)),
             ((6.604133333333333, 46.98241563219726,
               6.612466666666666, 46.986979614004284),
              0.5, (2.02, 0.47, 2.23, 3.51, 1.64),
              (0.8146, 0.52, 0.0, 0.0, 0.0))], dtype=dtlist)

        _, data = get_array_shapefile(
            'shapefile', os.path.join(CDIR, 'shapefiles_test/output.shp'))
        aae(test_data['val']['PGA'], data['val']['PGA'])
        aae(test_data['bbox']['minx'], data['bbox']['minx'])


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
