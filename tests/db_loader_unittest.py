# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
    Unittests for NRML/CSV input files loaders to the database
"""

import geoalchemy
import unittest

from openquake import java
from openquake.utils import db
from openquake.utils.db import loader as db_loader
from tests.utils import helpers
import csv

TEST_SRC_FILE = helpers.get_data_path('example-source-model.xml')

SIMPLE_FAULT_OUTLINE_WKT = \
'''SRID=4326;POLYGON((-121.746720468 37.7997646327 8.0,
 -121.755320311 37.8056428874 8.0,
 -121.76392152 37.8115205163 8.0,
 -121.772524094 37.8173975193 8.0,
 -121.781128035 37.823273896 8.0,
 -121.789733343 37.8291496464 8.0,
 -121.798340017 37.83502477 8.0,
 -121.806948059 37.8408992668 8.0,
 -121.815557468 37.8467731364 8.0,
 -121.824168245 37.8526463786 8.0,
 -121.832780391 37.8585189933 8.0,
 -121.841393905 37.8643909801 8.0,
 -121.850008789 37.8702623388 8.0,
 -121.858625042 37.8761330693 8.0,
 -121.867242665 37.8820031712 8.0,
 -121.875861658 37.8878726443 8.0,
 -121.884482021 37.8937414885 8.0,
 -121.893103756 37.8996097034 8.0,
 -121.901726861 37.9054772889 8.0,
 -121.910351339 37.9113442446 8.0,
 -121.918977188 37.9172105704 8.0,
 -121.92760441 37.9230762661 8.0,
 -121.936233004 37.9289413313 8.0,
 -121.944862972 37.934805766 8.0,
 -121.953494313 37.9406695697 8.0,
 -121.962127027 37.9465327424 8.0,
 -121.740857441 37.8051276017 8.61566147533,
 -121.749456817 37.8110058564 8.61566147533,
 -121.758057559 37.8168834853 8.61566147533,
 -121.766659667 37.8227604882 8.61566147533,
 -121.775263141 37.828636865 8.61566147533,
 -121.783867981 37.8345126153 8.61566147533,
 -121.792474188 37.8403877389 8.61566147533,
 -121.801081763 37.8462622356 8.61566147533,
 -121.809690705 37.8521361052 8.61566147533,
 -121.818301014 37.8580093474 8.61566147533,
 -121.826912693 37.863881962 8.61566147533,
 -121.835525739 37.8697539488 8.61566147533,
 -121.844140155 37.8756253075 8.61566147533,
 -121.85275594 37.8814960379 8.61566147533,
 -121.861373095 37.8873661398 8.61566147533,
 -121.869991621 37.8932356129 8.61566147533,
 -121.878611516 37.899104457 8.61566147533,
 -121.887232782 37.9049726719 8.61566147533,
 -121.89585542 37.9108402573 8.61566147533,
 -121.904479429 37.9167072131 8.61566147533,
 -121.91310481 37.9225735389 8.61566147533,
 -121.921731563 37.9284392345 8.61566147533,
 -121.930359689 37.9343042997 8.61566147533,
 -121.938989188 37.9401687343 8.61566147533,
 -121.94762006 37.946032538 8.61566147533,
 -121.956252306 37.9518957107 8.61566147533,
 -121.734993562 37.8104902801 9.23132295065,
 -121.743592472 37.8163685347 9.23132295065,
 -121.752192747 37.8222461635 9.23132295065,
 -121.760794387 37.8281231664 9.23132295065,
 -121.769397394 37.833999543 9.23132295065,
 -121.778001767 37.8398752932 9.23132295065,
 -121.786607507 37.8457504168 9.23132295065,
 -121.795214613 37.8516249134 9.23132295065,
 -121.803823088 37.8574987829 9.23132295065,
 -121.81243293 37.863372025 9.23132295065,
 -121.82104414 37.8692446395 9.23132295065,
 -121.829656719 37.8751166262 9.23132295065,
 -121.838270667 37.8809879849 9.23132295065,
 -121.846885984 37.8868587152 9.23132295065,
 -121.855502671 37.892728817 9.23132295065,
 -121.864120728 37.89859829 9.23132295065,
 -121.872740155 37.904467134 9.23132295065,
 -121.881360953 37.9103353488 9.23132295065,
 -121.889983122 37.9162029341 9.23132295065,
 -121.898606663 37.9220698898 9.23132295065,
 -121.907231575 37.9279362154 9.23132295065,
 -121.91585786 37.933801911 9.23132295065,
 -121.924485517 37.9396669761 9.23132295065,
 -121.933114547 37.9455314106 9.23132295065,
 -121.94174495 37.9513952142 9.23132295065,
 -121.950376727 37.9572583868 9.23132295065,
 -121.729128832 37.8158526679 9.84698442598,
 -121.737727274 37.8217309223 9.84698442598,
 -121.746327082 37.827608551 9.84698442598,
 -121.754928255 37.8334855537 9.84698442598,
 -121.763530794 37.8393619302 9.84698442598,
 -121.772134699 37.8452376802 9.84698442598,
 -121.780739972 37.8511128036 9.84698442598,
 -121.789346611 37.8569873001 9.84698442598,
 -121.797954617 37.8628611694 9.84698442598,
 -121.806563991 37.8687344114 9.84698442598,
 -121.815174734 37.8746070257 9.84698442598,
 -121.823786845 37.8804790123 9.84698442598,
 -121.832400324 37.8863503707 9.84698442598,
 -121.841015173 37.8922211009 9.84698442598,
 -121.849631392 37.8980912025 9.84698442598,
 -121.85824898 37.9039606754 9.84698442598,
 -121.866867939 37.9098295193 9.84698442598,
 -121.875488268 37.9156977339 9.84698442598,
 -121.884109969 37.9215653191 9.84698442598,
 -121.89273304 37.9274322746 9.84698442598,
 -121.901357484 37.9332986001 9.84698442598,
 -121.9099833 37.9391642955 9.84698442598,
 -121.918610488 37.9450293605 9.84698442598,
 -121.927239048 37.9508937948 9.84698442598,
 -121.935868982 37.9567575983 9.84698442598,
 -121.94450029 37.9626207707 9.84698442598,
 -121.72326325 37.8212147648 10.4626459013,
 -121.731861224 37.827093019 10.4626459013,
 -121.740460564 37.8329706475 10.4626459013,
 -121.74906127 37.8388476499 10.4626459013,
 -121.757663341 37.8447240262 10.4626459013,
 -121.766266779 37.8505997761 10.4626459013,
 -121.774871583 37.8564748992 10.4626459013,
 -121.783477754 37.8623493955 10.4626459013,
 -121.792085293 37.8682232646 10.4626459013,
 -121.800694199 37.8740965064 10.4626459013,
 -121.809304473 37.8799691205 10.4626459013,
 -121.817916115 37.8858411068 10.4626459013,
 -121.826529127 37.8917124651 10.4626459013,
 -121.835143507 37.897583195 10.4626459013,
 -121.843759257 37.9034532964 10.4626459013,
 -121.852376377 37.9093227691 10.4626459013,
 -121.860994867 37.9151916127 10.4626459013,
 -121.869614727 37.9210598272 10.4626459013,
 -121.878235958 37.9269274121 10.4626459013,
 -121.886858561 37.9327943674 10.4626459013,
 -121.895482536 37.9386606927 10.4626459013,
 -121.904107882 37.9445263879 10.4626459013,
 -121.912734601 37.9503914526 10.4626459013,
 -121.921362692 37.9562558868 10.4626459013,
 -121.929992157 37.96211969 10.4626459013,
 -121.938622995 37.9679828622 10.4626459013,
 -121.717396815 37.8265765708 11.0783073766,
 -121.725994322 37.8324548247 11.0783073766,
 -121.734593194 37.8383324529 11.0783073766,
 -121.743193432 37.8442094551 11.0783073766,
 -121.751795035 37.8500858311 11.0783073766,
 -121.760398005 37.8559615807 11.0783073766,
 -121.769002341 37.8618367036 11.0783073766,
 -121.777608044 37.8677111996 11.0783073766,
 -121.786215114 37.8735850684 11.0783073766,
 -121.794823551 37.8794583099 11.0783073766,
 -121.803433357 37.8853309237 11.0783073766,
 -121.812044531 37.8912029098 11.0783073766,
 -121.820657074 37.8970742678 11.0783073766,
 -121.829270985 37.9029449974 11.0783073766,
 -121.837886266 37.9088150986 11.0783073766,
 -121.846502917 37.9146845709 11.0783073766,
 -121.855120938 37.9205534143 11.0783073766,
 -121.863740329 37.9264216285 11.0783073766,
 -121.872361091 37.9322892131 11.0783073766,
 -121.880983225 37.9381561681 11.0783073766,
 -121.88960673 37.9440224932 11.0783073766,
 -121.898231607 37.9498881881 11.0783073766,
 -121.906857856 37.9557532525 11.0783073766,
 -121.915485478 37.9616176864 11.0783073766,
 -121.924114473 37.9674814894 11.0783073766,
 -121.932744841 37.9733446613 11.0783073766,
 -121.711529528 37.8319380858 11.693968852,
 -121.720126567 37.8378163394 11.693968852,
 -121.728724971 37.8436939673 11.693968852,
 -121.737324741 37.8495709691 11.693968852,
 -121.745925876 37.8554473448 11.693968852,
 -121.754528377 37.861323094 11.693968852,
 -121.763132244 37.8671982165 11.693968852,
 -121.771737479 37.8730727122 11.693968852,
 -121.78034408 37.8789465807 11.693968852,
 -121.788952049 37.8848198218 11.693968852,
 -121.797561386 37.8906924354 11.693968852,
 -121.806172091 37.8965644211 11.693968852,
 -121.814784165 37.9024357787 11.693968852,
 -121.823397608 37.908306508 11.693968852,
 -121.832012419 37.9141766088 11.693968852,
 -121.840628601 37.9200460809 11.693968852,
 -121.849246153 37.9259149239 11.693968852,
 -121.857865075 37.9317831377 11.693968852,
 -121.866485367 37.9376507221 11.693968852,
 -121.875107031 37.9435176767 11.693968852,
 -121.883730067 37.9493840014 11.693968852,
 -121.892354474 37.9552496959 11.693968852,
 -121.900980253 37.9611147601 11.693968852,
 -121.909607405 37.9669791936 11.693968852,
 -121.91823593 37.9728429963 11.693968852,
 -121.926865828 37.9787061678 11.693968852,
 -121.705661388 37.8372993097 12.3096303273,
 -121.714257959 37.8431775629 12.3096303273,
 -121.722855895 37.8490551904 12.3096303273,
 -121.731455196 37.8549321918 12.3096303273,
 -121.740055862 37.8608085671 12.3096303273,
 -121.748657895 37.8666843159 12.3096303273,
 -121.757261294 37.8725594381 12.3096303273,
 -121.765866059 37.8784339333 12.3096303273,
 -121.774472192 37.8843078014 12.3096303273,
 -121.783079692 37.8901810421 12.3096303273,
 -121.79168856 37.8960536553 12.3096303273,
 -121.800298796 37.9019256406 12.3096303273,
 -121.808910401 37.9077969978 12.3096303273,
 -121.817523374 37.9136677267 12.3096303273,
 -121.826137716 37.9195378271 12.3096303273,
 -121.834753429 37.9254072988 12.3096303273,
 -121.843370511 37.9312761414 12.3096303273,
 -121.851988963 37.9371443548 12.3096303273,
 -121.860608786 37.9430119387 12.3096303273,
 -121.86922998 37.948878893 12.3096303273,
 -121.877852546 37.9547452173 12.3096303273,
 -121.886476483 37.9606109114 12.3096303273,
 -121.895101792 37.9664759752 12.3096303273,
 -121.903728474 37.9723404083 12.3096303273,
 -121.912356529 37.9782042105 12.3096303273,
 -121.920985957 37.9840673817 12.3096303273,
 -121.699792395 37.8426602424 12.9252918026,
 -121.708388497 37.8485384952 12.9252918026,
 -121.716985965 37.8544161221 12.9252918026,
 -121.725584797 37.8602931231 12.9252918026,
 -121.734184995 37.8661694979 12.9252918026,
 -121.742786559 37.8720452463 12.9252918026,
 -121.751389489 37.877920368 12.9252918026,
 -121.759993785 37.8837948628 12.9252918026,
 -121.768599449 37.8896687304 12.9252918026,
 -121.77720648 37.8955419707 12.9252918026,
 -121.785814878 37.9014145834 12.9252918026,
 -121.794424645 37.9072865682 12.9252918026,
 -121.80303578 37.913157925 12.9252918026,
 -121.811648284 37.9190286534 12.9252918026,
 -121.820262157 37.9248987534 12.9252918026,
 -121.828877399 37.9307682245 12.9252918026,
 -121.837494012 37.9366370667 12.9252918026,
 -121.846111994 37.9425052797 12.9252918026,
 -121.854731347 37.9483728631 12.9252918026,
 -121.863352071 37.9542398169 12.9252918026,
 -121.871974167 37.9601061408 12.9252918026,
 -121.880597634 37.9659718344 12.9252918026,
 -121.889222473 37.9718368977 12.9252918026,
 -121.897848684 37.9777013304 12.9252918026,
 -121.906476269 37.9835651322 12.9252918026,
 -121.915105226 37.9894283028 12.9252918026,
 -121.746720468 37.7997646327 8.0))'''.replace('\n', '')

SIMPLE_FAULT_EDGE_WKT = \
    'SRID=4326;LINESTRING(-121.8229 37.7301 0.0, -122.0388 37.8771 0.0)'


class NrmlModelLoaderTestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        """
        One-time setup stuff for this entire test case class.
        """
        super(NrmlModelLoaderTestCase, self).__init__(*args, **kwargs)

        self.src_reader = java.jclass('SourceModelReader')(
            TEST_SRC_FILE, db_loader.SourceModelLoader.DEFAULT_MFD_BIN_WIDTH)
        self.sources = self.src_reader.read()
        self.simple, self.complex, self.area, self.point = self.sources

    def test_get_simple_fault_surface(self):
        surface = db_loader.get_fault_surface(self.simple)
        surface_type = surface.__javaclass__.getName()
        self.assertEqual('org.opensha.sha.faultSurface.StirlingGriddedSurface',
            surface_type)

        # these surfaces are complex objects
        # there is a lot here we can test
        # for now, we only test the overall surface area
        # the test value is derived from our test data
        self.assertEqual(200.0, surface.getSurfaceArea())

    def test_get_complex_fault_surface(self):
        surface = db_loader.get_fault_surface(self.complex)
        surface_type = surface.__javaclass__.getName()
        self.assertEqual(
            'org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface',
            surface_type)

        # as with the simple fault surface, we're only going to test
        # the surface area (for now)
        # the test value is derived from our test data
        self.assertEqual(126615.0, surface.getSurfaceArea())

    def test_get_fault_surface_raises(self):
        """
        Test that the
        :py:function:`openquake.utils.db.loader.get_fault_surface` function
        raises when passed an inappropriate source type.
        """
        self.assertRaises(ValueError, db_loader.get_fault_surface, self.area)
        self.assertRaises(ValueError, db_loader.get_fault_surface, self.point)

    def test_parse_mfd_simple_fault(self):

        expected = {
            'table': 'pshai.mfd_evd',
            'data': {
                'max_val': 6.9500000000000002,
                'total_cumulative_rate': 1.8988435199999998e-05,
                'min_val': 6.5499999999999998,
                'bin_size': 0.10000000000000009,
                'mfd_values': [
                    0.0010614989,
                    0.00088291626999999998,
                    0.00073437776999999999,
                    0.00061082879999999995,
                    0.00050806530000000003],
                'total_moment_rate': 281889786038447.25,
                'owner_id': None}}

        mfd = self.simple.getMfd()

        # Assume that this is an 'evenly discretized' MFD
        # We want to do this check so we know right away if our test data
        # has been altered.
        mfd_type = mfd.__javaclass__.getName()
        self.assertEqual(
            '%s.IncrementalMagFreqDist' % db_loader.MFD_PACKAGE, mfd_type)

        # this is the dict we'll be passing to sqlalchemy to do the db insert
        mfd_insert = db_loader.parse_mfd(self.simple, mfd)

        self.assertEqual(expected, mfd_insert)

    def test_parse_mfd_complex_fault(self):
        expected = {
            'table': 'pshai.mfd_tgr',
            'data': {
                'b_val': 0.80000000000000004,
                'total_cumulative_rate': 4.933442096397671e-10,
                'min_val': 6.5499999999999998,
                'max_val': 8.9499999999999993,
                'total_moment_rate': 198544639016.43918,
                'a_val': 1.0,
                'owner_id': None}}

        mfd = self.complex.getMfd()

        mfd_type = mfd.__javaclass__.getName()
        self.assertEqual(
            '%s.GutenbergRichterMagFreqDist' % db_loader.MFD_PACKAGE, mfd_type)

        mfd_insert = db_loader.parse_mfd(self.complex, mfd)

        self.assertEqual(expected, mfd_insert)

    def test_parse_simple_fault_src(self):

        expected = (
            {'table': 'pshai.mfd_evd', 'data': {
                'max_val': 6.9500000000000002,
                'total_cumulative_rate': 1.8988435199999998e-05,
                'min_val': 6.5499999999999998,
                'bin_size': 0.10000000000000009,
                'mfd_values': [
                    0.0010614989, 0.00088291626999999998,
                    0.00073437776999999999, 0.00061082879999999995,
                    0.00050806530000000003],
                'total_moment_rate': 281889786038447.25,
                'owner_id': None}},
            {'table': 'pshai.simple_fault', 'data': {
                'name': u'Mount Diablo Thrust',
                'upper_depth': 8.0,
                'mgf_evd_id': None,
                'mfd_tgr_id': None,
                'outline': \
                    geoalchemy.WKTSpatialElement(SIMPLE_FAULT_OUTLINE_WKT),
                'edge': geoalchemy.WKTSpatialElement(SIMPLE_FAULT_EDGE_WKT),
                'lower_depth': 13.0,
                'gid': u'src01',
                'owner_id': None,
                'dip': 38.0,
                'description': None}},
            {'table': 'pshai.source', 'data': {
                'r_depth_distr_id': None,
                'name': u'Mount Diablo Thrust',
                'tectonic_region': 'active',
                'rake': 90.0,
                'si_type': 'simple',
                'gid': u'src01',
                'simple_fault_id': None,
                'owner_id': None,
                'hypocentral_depth': None,
                'description': None,
                'input_id': None}})

        simple_data = db_loader.parse_simple_fault_src(self.simple)

        # The WKTSpatialElement objects do not make for nice comparisons.
        # So instead, we'll just test the text element of each object
        # to make sure the coords and spatial reference system match.
        # To do that, we need to remove the WKTSpatialElements so
        # we can compare the rest of the dicts for equality.
        exp_outline = expected[1]['data'].pop('outline')
        actual_outline = simple_data[1]['data'].pop('outline')

        self.assertEqual(exp_outline.geom_wkt, actual_outline.geom_wkt)

        exp_edge = expected[1]['data'].pop('edge')
        actual_edge = simple_data[1]['data'].pop('edge')

        self.assertEqual(exp_edge.geom_wkt, actual_edge.geom_wkt)

        # Now we can test the rest of the data.
        self.assertEqual(expected, simple_data)


class CsvLoaderTestCase(unittest.TestCase):
    """
        Main class to execute tests about CSV
    """

    def setUp(self):
        csv_file = "ISC_sampledata1.csv"
        self.csv_path = helpers.get_data_path(csv_file)
        csv_fd = open(self.csv_path, 'r')
        self.csv_reader = csv.DictReader(csv_fd, delimiter=',')

    def test_input_csv_is_of_the_right_len(self):
        # without the header line is 8892
        expected_len = 8892

        self.assertEqual(len(list(self.csv_reader)), expected_len)

    def test_csv_headers_are_correct(self):
        expected_headers = ['eventid', 'agency', 'identifier', 'year',
            'month', 'day', 'hour', 'minute', 'second', 'time_error',
            'longitude', 'latitude', 'semi_major', 'semi_minor', 'strike',
            'depth', 'depth_error', 'mw_val', 'mw_val_error',
            'ms_val', 'ms_val_error', 'mb_val', 'mb_val_error', 'ml_val',
            'ml_val_error']

        # it's not important that the headers of the csv are in the right or
        # wrong order, by using the DictReader it is sufficient to compare the
        # headers
        expected_headers = sorted(expected_headers)
        csv_headers = sorted(self.csv_reader.next().keys())
        self.assertEqual(csv_headers, expected_headers)

    # Skip the end-to-end test for now, until database on CI system is setup
    # TODO: move the test in db_tests folder
    @helpers.skipit
    def test_csv_to_db_loader_end_to_end(self):
        """
            * Serializes the csv into the database
            * Queries the database for the data just inserted
            * Verifies the data against the csv
            * Deletes the inserted records from the database
        """
        def _pop_date_fields(csv):
            date_fields = ['year', 'month', 'day', 'hour', 'minute', 'second']
            res = [csv.pop(csv.index(field)) for field in date_fields]
            return res

        def _prepare_date(csv_r, date_fields):
            return [int(csv_r[field]) for field in date_fields]

        def _pop_geometry_fields(csv):
            unused_fields = ['longitude', 'latitude']
            [csv.pop(csv.index(field)) for field in unused_fields]

        user = 'kpanic'
        password = 'openquake'
        dbname = 'openquake'

        engine = db.create_engine(dbname=dbname, user=user, password=password)

        csv_loader = db_loader.CsvModelLoader(self.csv_path, engine, 'eqcat')
        csv_loader.serialize()
        soup_db = csv_loader.soup

        # doing some "trickery" with *properties and primary_key, to adapt the
        # code for sqlalchemy 0.7

        # surface join
        surf_join = soup_db.join(soup_db.catalog, soup_db.surface,
            properties={'id_surface': [soup_db.surface.c.id]},
                        exclude_properties=[soup_db.surface.c.id,
                            soup_db.surface.c.last_update],
            primary_key=[soup_db.surface.c.id])

        # magnitude join
        mag_join = soup_db.join(surf_join, soup_db.magnitude,
            properties={'id_magnitude': [soup_db.magnitude.c.id],
                    'id_surface': [soup_db.surface.c.id]},
                        exclude_properties=[soup_db.magnitude.c.id,
                            soup_db.magnitude.c.last_update,
                            soup_db.surface.c.last_update],
            primary_key=[soup_db.magnitude.c.id, soup_db.surface.c.id])

        db_rows = mag_join.order_by(soup_db.catalog.eventid).all()

        # rewind the file
        csv_loader.csv_fd.seek(0)

        # skip the header
        csv_loader.csv_reader.next()
        csv_els = list(csv_loader.csv_reader)
        for csv_row, db_row in zip(csv_els, db_rows):
            csv_keys = csv_row.keys()
            # pops 'longitude', 'latitude' which are used to populate
            # geometry_columns
            _pop_geometry_fields(csv_keys)

            timestamp = _prepare_date(csv_row, _pop_date_fields(csv_keys))
            csv_time = csv_loader._date_to_timestamp(*timestamp)
            # first we compare the timestamps
            self.assertEqual(str(db_row.time), csv_time)

            # then, we cycle through the csv keys and consider some special
            # cases
            for csv_key in csv_keys:
                db_val = getattr(db_row, csv_key)
                csv_val = csv_row[csv_key]
                if not len(csv_val.strip()):
                    csv_val = '-999.0'
                if csv_key == 'agency':
                    self.assertEqual(str(db_val), str(csv_val))
                else:
                    self.assertEqual(float(db_val), float(csv_val))

        # cleaning the db
        for db_row in db_rows:
            soup_db.delete(db_row)
        soup_db.commit()
