# coding=utf-8
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

"""
Module containing writers for risk output artifacts.
"""

from lxml import etree

import nrml


class LossCurveXMLWriter(object):

    def __init__(self, path, model_id="1"):
        self._path = path
        self._model_id = model_id

    def serialize(self, data):
        with open(self._path, "w") as output:
            root = etree.Element("nrml", nsmap=nrml.SERIALIZE_NS_MAP)

            for _ in data:
                pass

            output.write(etree.tostring(
                root, pretty_print=True, xml_declaration=True,
                encoding="UTF-8"))
