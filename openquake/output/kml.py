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



# vim: tabstop=4 shiftwidth=4 softtabstop=4

""" KML output class

We're cheating a bit with the xml so that we can write stuff as we get it
rather than generating a giant dom and then writing it to file.

"""

from lxml import etree
from lxml.builder import E

from openquake import writer

KML_HEADER = """
<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Paths</name>
    <description>Examples of paths. Note that the tessellate tag is by default
      set to 0. If you want to create tessellated lines, they must be authored
      (or edited) directly in KML.</description>
    <Style id="yellowLineGreenPoly">
      <LineStyle>
        <color>7f00ffff</color>
        <width>4</width>
      </LineStyle>
      <PolyStyle>
        <color>7f00ff00</color>
      </PolyStyle>
    </Style>
"""

KML_FOOTER = """
  </Document>
</kml>
"""


class KmlFile(writer.FileWriter):
    """Example output class.

    Were this a real class it would probably be doing something much more
    interesting.

    """
    def __init__(self, *args, **kw):
        super(KmlFile, self).__init__(*args, **kw)
        self.file.write(KML_HEADER.strip())

    def write(self, cell, value):
        # cell to kml linestring
        linestring = []
        for x, y in cell.coords:
            linestring.append('%f,%f,2357' % (x, y))

        placemark = (E.Placemark(
                        E.name('foo'),
                        E.description('bar'),
                        E.styleUrl('#yellowLineGreenpoly'),
                        E.LineString(
                            E.extrude('1'),
                            E.tesselate('1'),
                            E.altitudeMode('absolute'),
                            E.coordinates('\n'.join(linestring))
                            )
                        )
                     )

        self.file.write(etree.tostring(placemark, pretty_print=True))

    def close(self):
        self.file.write(KML_FOOTER.strip())
        super(KmlFile, self).close()

