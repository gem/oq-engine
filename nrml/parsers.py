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


"""These parsers read NRML XML files and produce object representations of the
data.

See :module:`nrml.models`.
"""

from lxml import etree

import nrml

from nrml import models


class SourceModelParser(object):
    """NRML source model parser. Reads point sources, area sources, simple
    fault sources, and complex fault sources from a given source.

    :param source:
        Filename or file-like object containing the XML data.
    """

    _SM_TAG = '{%s}sourceModel' % nrml.NAMESPACE
    _PT_TAG = '{%s}pointSource' % nrml.NAMESPACE
    _AREA_TAG = '{%s}areaSource' % nrml.NAMESPACE
    _SIMPLE_TAG = '{%s}simpleFaultSource' % nrml.NAMESPACE
    _COMPLEX_TAG = '{%s}complexFaultSource' % nrml.NAMESPACE

    def __init__(self, source):
        self.source = source

        self._parse_fn_map = {
            self._PT_TAG: self._parse_point,
            self._AREA_TAG: self._parse_area,
            self._SIMPLE_TAG: self._parse_simple,
            self._COMPLEX_TAG: self._parse_complex,
        }

    def _source_gen(self, tree):
        """Returns a generator which yields source model objects."""
        for event, element in tree:
            # We only want to parse data from the 'end' tag, otherwise there is
            # no guarantee the data will actually be present. We've run into
            # this issue in the past. See http://bit.ly/lxmlendevent for a
            # detailed description of the issue.
            if event == 'end':
                parse_fn = self._parse_fn_map.get(element.tag, None)
                if parse_fn is not None:
                    yield parse_fn(element)

    @classmethod
    def _parse_point(cls, element):
        return element.tag

    @classmethod
    def _parse_area(cls, element):
        area = models.AreaSource()
        return area

    @classmethod
    def _parse_simple(cls, element):
        return element.tag

    @classmethod
    def _parse_complex(cls, element):
        return element.tag

    def parse(self):
        src_model = models.SourceModel()

        tree = etree.iterparse(self.source, events=('start', 'end'))

        while src_model.name is None:
            try:
                event, element = tree.next()
                if event == 'start':
                    if element.tag == self._SM_TAG:
                        src_model.name = element.get('name')
                        break
            except StopIteration:
                # Worst case, we parse the entire file without ever finding the
                # <sourceModel> element. This prevents an infinite loop.
                break

        src_model.sources = self._source_gen(tree)

        return src_model
