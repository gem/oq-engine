# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import tempfile
import unittest

import nrml

from nose.plugins.attrib import attr

from openquake.db import models
from openquake.export import core as export_core
from openquake.export import risk

from tests.utils import helpers


def _number_of(elem_name, tree):
    """
    Given an element name (including the namespaces prefix, if applicable),
    return the number of occurrences of the element in a given XML document.
    """
    expr = '//%s' % elem_name
    return len(tree.xpath(expr, namespaces=nrml.PARSE_NS_MAP))


class BaseExportTestCase(unittest.TestCase):

    def _test_exported_file(self, filename):
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(os.path.isabs(filename))
        self.assertTrue(os.path.getsize(filename) > 0)


class ClassicalExportTestcase(BaseExportTestCase):

    @attr('slow')
    def test_classical_risk_export(self):
        # Tests that outputs of a risk classical calculation are exported
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('classical_psha_based_risk/job.ini')

            # run the calculation to create something to export
            retcode = helpers.run_risk_job_sp(cfg, silence=True)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)
            expected_outputs = 4  # 1 loss curve set + 3 loss curve map set
            self.assertEqual(expected_outputs, len(outputs))

            # Export the loss curves:
            curves = outputs.filter(output_type='loss_curve')
            rc_files = []
            for curve in curves:
                rc_files.extend(risk.export(curve.id, target_dir))

            self.assertEqual(1, len(rc_files))

            for f in rc_files:
                self._test_exported_file(f)

            # Test loss map export as well.
            maps = outputs.filter(output_type='loss_map')
            lm_files = sum(
                [risk.export(loss_map.id, target_dir)
                 for loss_map in maps], [])

            self.assertEqual(3, len(lm_files))

            for f in lm_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)

    @attr('slow')
    def test_bcr_risk_export(self):
        # Tests that outputs of a risk classical calculation are
        # exported

        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('classical_bcr/job.ini')

            # run the calculation to create something to export
            retcode = helpers.run_risk_job_sp(cfg, silence=True)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)
            expected_outputs = 1  # 1 bcr distribution
            self.assertEqual(expected_outputs, len(outputs))

            # Export the loss curves:
            distribution = outputs.filter(output_type='bcr_distribution')[0]
            rc_files = risk.export(distribution.id, target_dir)

            self.assertEqual(1, len(rc_files))

            for f in rc_files:
                self._test_exported_file(f)
        finally:
            shutil.rmtree(target_dir)


class EventBasedExportTestcase(BaseExportTestCase):

    @attr('slow')
    def test_event_based_risk_export(self):
        # Tests that outputs of a risk classical calculation are exported
        target_dir = tempfile.mkdtemp()

        try:
            cfg = helpers.demo_file('event_based_risk/job.ini')

            # run the calculation to create something to export

            # at the moment, only gmf for a specific realization are
            # supported as hazard input
            retcode = helpers.run_risk_job_sp(
                cfg, silence=True,
                hazard_id=models.GmfCollection.objects.filter(
                    complete_logic_tree_gmf=False)[0].output.id)
            self.assertEqual(0, retcode)

            job = models.OqJob.objects.latest('id')

            outputs = export_core.get_outputs(job.id)
            # 1 loss curve set + 3 loss curve map set + 1 insured + 1 aggregate
            expected_outputs = 6
            self.assertEqual(expected_outputs, len(outputs))

            # Export the loss curves...
            curves = outputs.filter(output_type='loss_curve')
            rc_files = []
            for curve in curves:
                rc_files.extend(risk.export(curve.id, target_dir))

            self.assertEqual(1, len(rc_files))

            for f in rc_files:
                self._test_exported_file(f)

            # ... loss map ...
            maps = outputs.filter(output_type='loss_map')
            lm_files = sum(
                [risk.export(loss_map.id, target_dir)
                 for loss_map in maps], [])

            self.assertEqual(3, len(lm_files))

            for f in lm_files:
                self._test_exported_file(f)

            # ... aggregate losses...
            maps = outputs.filter(output_type='agg_loss_curve')
            lm_files = sum(
                [risk.export(loss_map.id, target_dir)
                 for loss_map in maps], [])

            self.assertEqual(1, len(lm_files))

            for f in lm_files:
                self._test_exported_file(f)

            # and insured losses.
            maps = outputs.filter(output_type='ins_loss_curve')
            lm_files = sum(
                [risk.export(loss_map.id, target_dir)
                 for loss_map in maps], [])

            self.assertEqual(1, len(lm_files))

            for f in lm_files:
                self._test_exported_file(f)

        finally:
            shutil.rmtree(target_dir)
