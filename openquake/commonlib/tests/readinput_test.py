#-*- encoding: utf-8 -*-
import mock
import unittest
from StringIO import StringIO

from openquake.hazardlib import geo
from openquake.commonlib.readinput import get_site_model
from openquake.commonlib.valid import SiteParam


class ClosestSiteModelTestCase(unittest.TestCase):

    def test_get_site_model(self):
        data = StringIO('''\
<?xml version="1.0" encoding="utf-8"?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <siteModel>
        <site lon="0.0" lat="0.0" vs30="1200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" />
        <site lon="0.0" lat="0.1" vs30="600.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" />
        <site lon="0.0" lat="0.2" vs30="200.0" vs30Type="inferred" z1pt0="100.0" z2pt5="2.0" />
    </siteModel>
</nrml>''')
        oqparam = mock.Mock()
        oqparam.inputs = dict(site_model=data)
        expected = [
            SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False, vs30=1200.0,
                      lon=0.0, lat=0.0),
            SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False, vs30=600.0,
                      lon=0.0, lat=0.1),
            SiteParam(z1pt0=100.0, z2pt5=2.0, measured=False, vs30=200.0,
                      lon=0.0, lat=0.2)]
        self.assertEqual(list(get_site_model(oqparam)), expected)

    def test_get_closest_site_model_data(self):
        # This test scenario is the following:
        # Site model data nodes arranged 2 degrees apart (longitudinally) along
        # the same parallel (indicated below by 'd' characters).
        #
        # The sites of interest are located at (-0.0000001, 0) and
        # (0.0000001, 0) (from left to right).
        # Sites of interest are indicated by 's' characters.
        #
        # To illustrate, a super high-tech nethack-style diagram:
        #
        # -1.........0.........1
        #  d        s s        d

        sm1 = SiteParam(
            measured=True, vs30=0.0000001,
            z1pt0=0.0000001, z2pt5=0.0000001, lon=-1, lat=0)
        sm2 = SiteParam(
            measured=False, vs30=0.0000002,
            z1pt0=0.0000002, z2pt5=0.0000002, lon=1, lat=0)

        siteparams = geo.geodetic.GeographicObjects([sm1, sm2])

        res1 = siteparams.get_closest(-0.0000001, 0)
        res2 = siteparams.get_closest(0.0000001, 0)

        self.assertEqual(res1, (sm1, 111.19491552506607))
        self.assertEqual(res2, (sm2, 111.19491552506607))

        # here the first params are taken, even if both sm1 and sm2
        # are at the same distance from (0, 0)
        res0 = siteparams.get_closest(0, 0)
        self.assertEqual(res0, (sm1, 111.19492664455873))
