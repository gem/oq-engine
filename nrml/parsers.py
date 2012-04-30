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

import re

from lxml import etree

import nrml

from nrml import exceptions
from nrml import models
from nrml import utils


def _xpath(elem, expr, namespaces=nrml.NS_MAP):
    return elem.xpath(expr, namespaces=namespaces)


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
    def _parse_mfd(cls, src_elem):
        [mfd_elem] = _xpath(src_elem, ('.//nrml:truncGutenbergRichterMFD | '
                                       './/nrml:incrementalMFD'))

        if mfd_elem.tag == '{%s}truncGutenbergRichterMFD' % nrml.NAMESPACE:
            mfd = models.TGRMFD()
            mfd.a_val = float(mfd_elem.get('aValue'))
            mfd.b_val = float(mfd_elem.get('bValue'))
            mfd.min_mag = float(mfd_elem.get('minMag'))
            mfd.max_mag = float(mfd_elem.get('maxMag'))

        elif mfd_elem.tag == '{%s}incrementalMFD' % nrml.NAMESPACE:
            mfd = models.IncrementalMFD()
            mfd.min_mag = float(mfd_elem.get('minMag'))
            mfd.bin_width = float(mfd_elem.get('binWidth'))

            [occur_rates] = _xpath(mfd_elem, './nrml:occurRates')
            mfd.occur_rates = [float(x) for x in occur_rates.text.split()]

        return mfd

    @classmethod
    def _parse_nodal_plane_dist(cls, src_elem):
        npd = []

        for elem in _xpath(src_elem, './/nrml:nodalPlane'):
            np = models.NodalPlane()
            np.probability = float(elem.get('probability'))
            np.strike = float(elem.get('strike'))
            np.dip = float(elem.get('dip'))
            np.rake = float(elem.get('rake'))

            npd.append(np)

        return npd

    @classmethod
    def _parse_hypo_depth_dist(cls, src_elem):
        hdd = []

        for elem in _xpath(src_elem, './/nrml:hypoDepth'):
            hd = models.HypocentralDepth()
            hd.probability = float(elem.get('probability'))
            hd.depth = float(elem.get('depth'))

            hdd.append(hd)

        return hdd

    @classmethod
    def _parse_point(cls, elem):
        return None

    @classmethod
    def _parse_area(cls, src_elem):
        area = models.AreaSource()
        area.id = src_elem.get('id')
        area.name = src_elem.get('name')
        area.trt = src_elem.get('tectonicRegion')

        area_geom = models.AreaGeometry()
        area.geometry = area_geom

        [gml_pos_list] = src_elem.xpath(
            './/nrml:areaGeometry//gml:posList', namespaces=nrml.NS_MAP)
        coords = gml_pos_list.text.split()
        # Area source polygon geometries are always 2-dimensional and on the
        # Earth's surface (depth == 0.0).
        area_geom.wkt = utils.coords_to_poly_wkt(coords, 2)

        area_geom.upper_seismo_depth = float(src_elem.xpath(
            './/nrml:areaGeometry/nrml:upperSeismoDepth',
            namespaces=nrml.NS_MAP)[0].text.strip())
        area_geom.lower_seismo_depth = float(src_elem.xpath(
            './/nrml:areaGeometry/nrml:lowerSeismoDepth',
            namespaces=nrml.NS_MAP)[0].text.strip())

        area.mag_scale_rel = src_elem.xpath(
            './/nrml:magScaleRel', namespaces=nrml.NS_MAP)[0].text.strip()
        area.rupt_aspect_ratio = float(src_elem.xpath(
            './/nrml:ruptAspectRatio', namespaces=nrml.NS_MAP)[0].text.strip())

        area.mfd = cls._parse_mfd(src_elem)
        area.nodal_plane_dist = cls._parse_nodal_plane_dist(src_elem)
        area.hypo_depth_dist = cls._parse_hypo_depth_dist(src_elem)

        import nose; nose.tools.set_trace()
        return area

    @classmethod
    def _parse_simple(cls, elem):
        return None

    @classmethod
    def _parse_complex(cls, elem):
        return None

    def parse(self):
        src_model = models.SourceModel()

        tree = etree.iterparse(self.source, events=('start', 'end'))

        # First thing, validate the nrml namespace version. If it not the
        # version we expected, stop immediately and raise an error.

        # The first node should be the <nrml> element.
        _, nrml_elem = tree.next()
        # Extract the namespace url and the element name.
        ns, el_name = re.search('^{(.+)}(.+)', nrml_elem.tag).groups()
        if not el_name == 'nrml':
            raise exceptions.UnexpectedElementError('nrml', el_name)
        if not ns == nrml.NAMESPACE:
            raise exceptions.UnexpectedNamespaceError(nrml.NAMESPACE, ns)

        # TODO(larsbutler): Run schema validation here. In a sense, that means
        # we techincally have to traverse the file twice (once to validate,
        # once to parse), but it's simple enough. With large files there may be
        # a performance hit, but that remains to be seen.

        for event, element in tree:
            # Find the <sourceModel> element and get the 'name' attr.
            if event == 'start':
                if element.tag == self._SM_TAG:
                    src_model.name = element.get('name')
                    break
            else:
                # If we get to here, we didn't find the <sourceModel> element.
                raise exceptions.NrmlError('<sourceModel> element not found.')

        src_model.sources = self._source_gen(tree)

        return src_model
