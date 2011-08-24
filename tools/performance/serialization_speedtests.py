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


# simple non-automated speed tests; run with
# nosetests -s to see timing for single tests
#
# some indicative timings:
# GMFDBWriterTestCase.test_serialize_small            2.71 sec
# HazardCurveDBWriterTestCase.test_deserialize_small 24.32 sec
# HazardCurveDBWriterTestCase.test_serialize_small   17.48 sec
# HazardMapDBWriterTestCase.test_serialize_small      3.48 sec
# LossCurveDBWriterTestCase.test_serialize_small     11.24 sec
# LossMapDBWriterTestCase.test_serialize_small       12.80 sec


import unittest

from openquake.db.alchemy.db_utils import get_db_session
from openquake.output.hazard import *
from openquake.output.risk import *
from openquake.shapes import Site, Curve

from tests.utils import helpers


def HAZARD_MAP_DATA(r1, r2):
    data = []
    poes = imls = [0.1] * 20

    for lon in xrange(-179, -179 + r1):
        for lat in xrange(-90, + r2):
            data.append((Site(lon, lat),
                         {'IML': 1.9266716959669603,
                          'IMT': 'PGA',
                          'investigationTimeSpan': '50.0',
                          'poE': 0.01,
                          'statistics': 'mean',
                          'vs30': 760.0}))

    return data


def HAZARD_CURVE_DATA(branches, r1, r2):
    data = []
    poes = imls = [0.1] * 20

    for lon in xrange(-179, -179 + r1):
        for lat in xrange(-90, + r2):
            for branch in branches:
                data.append((Site(lon, lat),
                             {'investigationTimeSpan': '50.0',
                              'IMLValues': imls,
                              'PoEValues': poes,
                              'IMT': 'PGA',
                              'endBranchLabel': branch}))

            data.append((Site(lon, lat),
                         {'investigationTimeSpan': '50.0',
                          'IMLValues': imls,
                          'PoEValues': poes,
                          'IMT': 'PGA',
                          'statistics': 'mean'}))

    return data


def GMF_DATA(r1, r2):
    data = {}

    for lon in xrange(-179, -179 + r1):
        for lat in xrange(-90, + r2):
            data[Site(lon, lat)] = {'groundMotion': 0.0}

    return data


def LOSS_CURVE_DATA(r1, r2):
    data = []
    poes = imls = [0.1] * 20

    for lon in xrange(-179, -179 + r1):
        for lat in xrange(-90, + r2):
            data.append((Site(lon, lat),
                         (Curve(zip(imls, poes)),
                          {'assetValue': 5.07,
                           'assetID': 'a5625',
                           'listDescription': 'Collection of exposure values',
                           'structureCategory': 'RM1L',
                           'lon': -118.077721,
                           'assetDescription': 'LA building',
                           'vulnerabilityFunctionReference': 'HAZUS_RM1L_LC',
                           'listID': 'LA01',
                           'assetValueUnit': 'EUR',
                           'lat': 33.852034})))

    return data


def LOSS_MAP_DATA(assets, r1, r2):
    data = [{'deterministic': True}]

    for lon in xrange(-179, -179 + r1):
        for lat in xrange(-90, + r2):
            data.append((Site(lon, lat), []))

            for asset in assets:
                data[-1][-1].append(({'mean_loss': 120000.0,
                                      'stddev_loss': 2000.0},
                                     {'assetID': asset}))

    return data


class HazardCurveDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    @helpers.timeit
    def test_serialize_small(self):
        data = HAZARD_CURVE_DATA(['1_1', '1_2', '2_2', '2'], 20, 4)

        self.job = self.setup_classic_job()
        session = get_db_session("reslt", "writer")
        output_path = self.generate_output_path(self.job)

        for i in xrange(0, 10):
            hcw = HazardCurveDBWriter(session, output_path + str(i),
                                       self.job.id)

            # Call the function under test.
            hcw.serialize(data)

        session.commit()

    @helpers.timeit
    def test_deserialize_small(self):
        data = HAZARD_CURVE_DATA(['1_1', '1_2', '2_2', '2'], 20, 4)

        self.job = self.setup_classic_job()
        session = get_db_session("reslt", "writer")
        output_path = self.generate_output_path(self.job)

        hcw = HazardCurveDBWriter(session, output_path, self.job.id)
        hcw.serialize(data)

        session.commit()

        # deserialize
        hcr = HazardCurveDBReader()

        for i in xrange(0, 10):
            # Call the function under test.
            hcr.deserialize(hcw.output.id)


class HazardMapDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    @helpers.timeit
    def test_serialize_small(self):
        data = HAZARD_MAP_DATA(20, 4)

        self.job = self.setup_classic_job()
        output_path = self.generate_output_path(self.job)

        for i in xrange(0, 10):
            hmw = HazardMapDBWriter(output_path + str(i), self.job.id)

            # Call the function under test.
            hmw.serialize(data)


class GMFDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    @helpers.timeit
    def test_serialize_small(self):
        data = GMF_DATA(20, 4)

        self.job = self.setup_classic_job()
        session = get_db_session("reslt", "writer")
        output_path = self.generate_output_path(self.job)

        for i in xrange(0, 10):
            gmfw = GMFDBWriter(session, output_path + str(i), self.job.id)

            # Call the function under test.
            gmfw.serialize(data)

        session.commit()


class LossCurveDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    @helpers.timeit
    def test_serialize_small(self):
        data = LOSS_CURVE_DATA(20, 4)

        self.job = self.setup_classic_job()
        session = get_db_session("reslt", "writer")
        output_path = self.generate_output_path(self.job)

        for i in xrange(0, 20):
            lcw = LossCurveDBWriter(session, output_path + str(i), self.job.id)

            # Call the function under test.
            lcw.serialize(data)

        session.commit()


class LossMapDBWriterTestCase(unittest.TestCase, helpers.DbTestMixin):
    def tearDown(self):
        if hasattr(self, "job") and self.job:
            self.teardown_job(self.job)
        if hasattr(self, "output") and self.output:
            self.teardown_output(self.output)

    @helpers.timeit
    def test_serialize_small(self):
        data = LOSS_MAP_DATA(['a%d' % i for i in range(5)], 20, 4)

        self.job = self.setup_classic_job()
        session = get_db_session("reslt", "writer")
        output_path = self.generate_output_path(self.job)

        for i in xrange(0, 10):
            lmw = LossMapDBWriter(session, output_path + str(i), self.job.id)

            # Call the function under test.
            lmw.serialize(data)

        session.commit()
