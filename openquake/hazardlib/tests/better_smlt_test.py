# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
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
import os
import shutil
import tempfile
import unittest
import zipfile
import xml.etree.ElementTree as ET
from openquake.hazardlib import better_smlt
from openquake.qa_tests_data.event_based import case_7

CASE7 = os.path.dirname(case_7.__file__)


class BetterSmltTestCase(unittest.TestCase):
    # the two source models of event_based/case_7 contain the same sources
    # with different MFDs: the variants are moved into the logic tree and
    # the converted logic tree is checked against the original one
    def test_case_7(self):
        with tempfile.TemporaryDirectory() as tmp:
            dname = shutil.copytree(CASE7, os.path.join(tmp, 'case_7'))
            self.assertTrue(better_smlt.main(os.path.join(dname, 'job.ini')))
            # job.zip contains a job with the converted logic tree, saved
            # with the name of the original one, and the rewritten sources
            with zipfile.ZipFile(os.path.join(dname, 'job.zip')) as z:
                names = z.namelist()
                ini = z.read('job.ini').decode()
                new = z.read('source_model_logic_tree.xml').decode()
            self.assertIn('source_model_logic_tree.xml', ini)
            # a single source: no correlated element is needed
            self.assertIn('applyToSources="1"', new)
            self.assertNotIn('correlated', new)
            self.assertIn('source_model2.xml', names)
            self.assertNotIn('_fixed/', new)
            self.assertNotIn('source_model_logic_tree_mfd.xml', names)
            # the folder _fixed and the converted logic tree are removed
            self.assertFalse(os.path.exists(os.path.join(dname, '_fixed')))
            self.assertFalse(os.path.exists(os.path.join(
                dname, 'source_model_logic_tree_mfd.xml')))

    def test_existing_folder(self):
        # a pre-existing folder _fixed is never overwritten
        with tempfile.TemporaryDirectory() as tmp:
            dname = shutil.copytree(CASE7, os.path.join(tmp, 'case_7'))
            os.mkdir(os.path.join(dname, '_fixed'))
            with self.assertRaises(FileExistsError):
                better_smlt.main(os.path.join(dname, 'job.ini'))


class MultiWriterTestCase(unittest.TestCase):
    # the multiMFD elements are written with one array per line, wrapped
    # to avoid extra-long lines in the XML
    def test_wrap(self):
        values = ' '.join('%.7E' % (i / 7) for i in range(893))
        arrays = (('a_val', values), ('b_val', values), ('min_mag', '4.5'))
        params = ('truncGutenbergRichterMFD', '893', arrays)
        text = better_smlt._multi('', params, '    ')
        self.assertLessEqual(max(map(len, text.splitlines())), 79)
        self.assertGreater(len(text.splitlines()), 20)
        # the element is parsed back to the same arrays
        root = ET.fromstring(text)
        self.assertEqual(root.attrib, {'kind': 'truncGutenbergRichterMFD',
                                       'size': '893'})
        got = tuple((c.tag, ' '.join(c.text.split())) for c in root)
        self.assertEqual(got, arrays)
