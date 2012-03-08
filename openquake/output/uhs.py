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
            job. See
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
