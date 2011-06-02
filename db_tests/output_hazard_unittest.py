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


import os
import unittest

from db.alchemy import models
from openquake.output.hazard import HazardMapDBWriter
from openquake.shapes import Site

# The data below was captured (and subsequently modified for testing purposes)
# by running
#
#   bin/openquake --config_file=smoketests/classical_psha_simple/config.gem
#
# and putting a breakpoint in openquake/writer.py, line 86
HAZARD_MAP_DATA = [
    (Site(-121.7, 37.6),
     {'IML': 1.9266716959669603,
      'IMT': 'PGA',
      'investigationTimeSpan': '50.0',
      'poE': 0.01,
      'statistics': 'mean',
      'vs30': 760.0}),
    (Site(-121.8, 38.0),
     {'IML': 1.9352164637194078,
      'IMT': 'PGA',
      'investigationTimeSpan': '50.0',
      'poE': 0.01,
      'statistics': 'mean',
      'vs30': 760.0}),
    (Site(-122.1, 37.8),
     {'IML': 1.9459475420737888,
      'IMT': 'PGA',
      'investigationTimeSpan': '50.0',
      'poE': 0.01,
      'statistics': 'mean',
      'vs30': 760.0}),
    (Site(-121.9, 37.7),
     {'IML': 1.9566716959669603,
      'IMT': 'PGA',
      'investigationTimeSpan': '50.0',
      'poE': 0.01,
      'statistics': 'mean',
      'vs30': 760.0})]


class HazardMapDBWriterTestCase(unittest.TestCase):
    """
    Unit tests for the HazardMapDBWriter class, which serializes
    hazard maps to the database.
    """

    def test_init_session(self):
        """A valid SQLAlchemy session is initialized."""
        writer = HazardMapDBWriter("/a/b/c", 11)
        writer.init_session()
        org = writer.session.query(models.Organization).filter(models.Organization.name.like("GEM%")).one()
        self.assertTrue(isinstance(org, models.Organization))
        self.assertEqual("GEM Foundation", org.name)
