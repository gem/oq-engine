# Copyright (c) 2010-2012, GEM Foundation.
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


"""Functionality for writing UHS NRML artifacts."""


from lxml import etree

from openquake import xml


class UHSXMLWriter(object):
    """Writes UHS results to the defined NRML format."""

    def __init__(self, path, periods, timespan):
        """
        :param path:
            Full path to the resulting XML file (including file name).
        :param periods:
            List of UHS periods (`float` types) associated with the calculation
            which produced these results.
        :param timespan:
            The value of the INVESTIGATION_TIME parameter used in the
            calculation. See
            :data:`openquake.db.models.OqJobProfile.investigation_time`
        """
        self.path = path
        self.periods = periods
        self.timespan = timespan

    def serialize(self, data):
        """Write the poe, path (to result file) pairs to the XML file.

        :param data:
            List of (poe, path) pairs. `poe` is a `float`, `path` is a `str`.
        """
        with open(self.path, 'w') as fh:

            root = etree.Element('nrml', nsmap=xml.NSMAP)
            root.set('%sid' % xml.GML, 'n1')

            uhs_rs = etree.SubElement(root, 'uhsResultSet')

            uhs_periods = etree.SubElement(uhs_rs, 'uhsPeriods')
            uhs_periods.text = ' '.join([str(x) for x in self.periods])

            timespan = etree.SubElement(uhs_rs, 'timeSpan')
            timespan.text = str(self.timespan)

            for poe, path in data:
                result_node = etree.SubElement(uhs_rs, 'uhsResult')
                result_node.set('poE', str(poe))
                result_node.set('path', path)

            fh.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding='UTF-8'))
