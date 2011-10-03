# -*- coding: utf-8 -*-
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


import unittest

from openquake.job.params import sequence_map_enum


class ParamsTestCase(unittest.TestCase):
    """Tests for utilities in :module:`openquake.job.params`."""

    EXPECTED = 'magpmf, magdistpmf, magdistepspmf'

    def test_sequence_map_enum(self):
        """Tests :function:`openquake.job.params.sequence_map_enum`
        using commas as delimiters in the input."""
        test_input = 'MagPMF, MagDistPMF, MagDistEpsPMF'

        self.assertEqual(self.EXPECTED, sequence_map_enum(test_input))

    def test_sequence_map_enum_no_commas(self):
        """Tests :function:`openquake.job.params.sequence_map_enum`
        using spaces as delimiters in the input."""

        test_input = 'MagPMF MagDistPMF MagDistEpsPMF'

        self.assertEqual(self.EXPECTED, sequence_map_enum(test_input))


    def test_sequence_map_enum_mixed(self):
        """tests :function:`openquake.job.params.sequence_map_enum`
        with mixed delimiters (spaces and commas)."""

        test_input = 'MagPMF, MagDistPMF MagDistEpsPMF'

        self.assertEqual(self.EXPECTED, sequence_map_enum(test_input))
