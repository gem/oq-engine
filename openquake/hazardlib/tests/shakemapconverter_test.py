import unittest
import numpy
from openquake.baselib.general import writetmp
from openquake.hazardlib.shakemapconverter import (
    get_shakemap_array, example_pga, example_sa)

aae = numpy.testing.assert_almost_equal
F32 = numpy.float32


class ShakemapConverterTestCase(unittest.TestCase):
    def test_pga(self):
        imt_dt = numpy.dtype([('PGA', F32)])
        array = get_shakemap_array(writetmp(example_pga))
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
        array = get_shakemap_array(writetmp(example_sa))
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
        grid_file = writetmp(ghorka_grid)
        uncertainty_file = writetmp(ghorka_uncertainty)
        array = get_shakemap_array(grid_file, uncertainty_file)
        aae(array['std']['SA(0.3)'], [0.57, 0.55, 0.56, 0.52])


ghorka_grid = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
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
'''
ghorka_uncertainty = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
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
<grid_field index="3" name="STDPGA" units="ln(pctg)" />
<grid_field index="4" name="STDPGV" units="ln(cms)" />
<grid_field index="5" name="STDMMI" units="intensity" />
<grid_field index="6" name="STDPSA03" units="ln(pctg)" />
<grid_field index="7" name="STDPSA10" units="ln(pctg)" />
<grid_field index="8" name="STDPSA30" units="ln(pctg)" />
<grid_field index="9" name="GMPE_INTER_STDPGA" units="ln(pctg)" />
<grid_field index="10" name="GMPE_INTRA_STDPGA" units="ln(pctg)" />
<grid_field index="11" name="GMPE_INTER_STDPGV" units="ln(cms)" />
<grid_field index="12" name="GMPE_INTRA_STDPGV" units="ln(cms)" />
<grid_field index="13" name="GMPE_INTER_STDMMI" units="intensity" />
<grid_field index="14" name="GMPE_INTRA_STDMMI" units="intensity" />
<grid_field index="15" name="GMPE_INTER_STDPSA03" units="ln(pctg)" />
<grid_field index="16" name="GMPE_INTRA_STDPSA03" units="ln(pctg)" />
<grid_field index="17" name="GMPE_INTER_STDPSA10" units="ln(pctg)" />
<grid_field index="18" name="GMPE_INTRA_STDPSA10" units="ln(pctg)" />
<grid_field index="19" name="GMPE_INTER_STDPSA30" units="ln(pctg)" />
<grid_field index="20" name="GMPE_INTRA_STDPSA30" units="ln(pctg)" />
<grid_data>
81.7314 30.8735 0.53 0.56 0.72 0.57 0.66 0.73 0.25 0.47 0.24 0.5 0.16 0.7 0.26 0.51 0.33 0.57 0.45 0.58
81.7481 30.8735 0.52 0.55 0.72 0.55 0.65 0.73 0.24 0.46 0.24 0.5 0.16 0.7 0.24 0.5 0.32 0.57 0.44 0.58
81.7647 30.8735 0.52 0.55 0.72 0.56 0.66 0.73 0.24 0.46 0.24 0.5 0.16 0.7 0.24 0.5 0.33 0.57 0.44 0.58
81.7814 30.8735 0.5 0.55 0.72 0.52 0.64 0.73 0.22 0.45 0.24 0.5 0.16 0.7 0.21 0.47 0.31 0.56 0.44 0.58
</grid_data>
</shakemap_grid>
'''
