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

See :module:`models`.
"""


from lxml import etree

import __init__
import models


class SiteModelParser(object):
    """NRML site model parser. Reads site-specific parameters from a given
    source.

    :param source:
        Filename or file-like object containing the XML data.
    :param bool schema_validation:
        If set to `True`, validate the input source against the current XML
        schema. Otherwise, we will try to parse the ``source``, even if the
        document structure or content is incorrect.
    """

    def __init__(self, source, schema_validation=True):
        self.source = source
        self.schema_validation = schema_validation

    def parse(self):
        """Parse the site model XML content and generate
        :class:`model.SiteModel` objects.

        :returns:
            A iterable of :class:`model.SiteModel` objects.
        """
        if self.schema_validation:
            schema = etree.XMLSchema(etree.parse(__init__.nrml_schema_file()))
        else:
            schema = None
        tree = etree.iterparse(self.source, events=('start',),
                               schema=schema)

        for _, element in tree:
            if element.tag == '{http://openquake.org/xmlns/nrml/0.3}site':
                site = models.SiteModel()
                site.vs30 = float(element.get('vs30'))
                site.vs30_type = element.get('vs30Type').strip()
                site.z1pt0 = float(element.get('z1pt0'))
                site.z2pt5 = float(element.get('z2pt5'))
                lonlat = dict(lon=element.get('lon').strip(),
                              lat=element.get('lat').strip())
                site.wkt = 'POINT(%(lon)s %(lat)s)' % lonlat

                yield site

                # Now do some clean up to free memory.
                while element.getprevious() is not None:
                    # Delete previous sibling elements.
                    # We need to loop here in case there are comments in
                    # the input file which are considered siblings to
                    # source elements.
                    del element.getparent()[0]
