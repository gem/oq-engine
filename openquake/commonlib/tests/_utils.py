# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from xml.etree.ElementTree import parse

from openquake.baselib.general import writetmp
from openquake.baselib.node import tostring
from openquake.hazardlib.nrml import PARSE_NS_MAP


def get_path(fname_or_fileobject):
    if isinstance(fname_or_fileobject, str):
        return fname_or_fileobject
    elif hasattr(fname_or_fileobject, 'getvalue'):
        return writetmp(fname_or_fileobject.getvalue())
    elif hasattr(fname_or_fileobject, 'name'):
        return fname_or_fileobject.name
    else:
        return TypeError(fname_or_fileobject)


def assert_xml_equal(a, b):
    """
    Compare two XML artifacts for equality.

    :param a, b:
        Paths to XML files, or a file-like object containing the XML
        contents.
    """
    path_a = get_path(a)
    path_b = get_path(b)
    content_a = tostring(parse(a).getroot(), nsmap=PARSE_NS_MAP)
    content_b = tostring(parse(b).getroot(), nsmap=PARSE_NS_MAP)
    if content_a != content_b:
        # uncomment this to see the differences
        # warnings.warn(content_a, stacklevel=2)
        raise AssertionError('The files %s and %s are different!' %
                             (path_a, path_b))
