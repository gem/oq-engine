# Copyright (c) 2010-2012, GEM Foundation.
#
# NRML is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# NRML is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with NRML.  If not, see <http://www.gnu.org/licenses/>.


import StringIO
import unittest

from nrml import exceptions
from nrml import models
from nrml import parsers


class SourceModelParserTestCase(unittest.TestCase):
    """Tests for the :class:`nrml.parsers.SourceModelParser` parser."""

    SAMPLE_FILE = 'nrml/schema/examples/source_model/mixed.xml'
    BAD_NAMESPACE = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.3"
      gml:id="n1">
</nrml>'''

    # The NRML element should be first
    NO_NRML_ELEM_FIRST = '''\
<?xml version='1.0' encoding='utf-8'?>
<sourceModel xmlns="http://openquake.org/xmlns/nrml/0.4" name="test">
    <nrml xmlns:gml="http://www.opengis.net/gml"
          xmlns="http://openquake.org/xmlns/nrml/0.3"
          gml:id="n1">
    </nrml>
</sourceModel>'''

    NO_SRC_MODEL = '''\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4"
      gml:id="n1">
</nrml>'''

    @classmethod
    def _expected_source_model(cls):
        area_src = models.AreaSource()
        point_src = models.PointSource()
        simple_src = models.SimpleFaultSource()
        complex_src = models.ComplexFaultSource()

        source_model = models.SourceModel()
        source_model.name = 'Some Source Model'
        source_model.sources = [area_src, point_src, simple_src, complex_src]
        return source_model

    def test_wrong_namespace(self):
        test_file = StringIO.StringIO(self.BAD_NAMESPACE)

        parser = parsers.SourceModelParser(test_file)

        self.assertRaises(exceptions.UnexpectedNamespaceError, parser.parse)

    def test_nrml_elem_not_found(self):
        test_file = StringIO.StringIO(self.NO_NRML_ELEM_FIRST)

        parser = parsers.SourceModelParser(test_file)

        self.assertRaises(exceptions.UnexpectedElementError, parser.parse)

    def test_no_source_model_elem(self):
        test_file = StringIO.StringIO(self.NO_SRC_MODEL)

        parser = parsers.SourceModelParser(test_file)

        try:
            parser.parse()
        except exceptions.NrmlError, err:
            self.assertEqual('<sourceModel> element not found.', err.message)
        else:
            self.fail('NrmlError not raised.')

    def test_parse(self):
        parser = parsers.SourceModelParser(self.SAMPLE_FILE)

        exp_src_model = self._expected_source_model()
        src_model = parser.parse()

        self.assertEqual('Some Source Model', src_model.name)
