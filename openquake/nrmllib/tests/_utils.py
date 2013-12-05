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

import collections
from nose import tools
from lxml import etree
from xml.etree.ElementTree import parse

import openquake.nrmllib
from openquake.nrmllib.writers import tostring


def deep_eq(a, b):
    """Deep compare two objects for equality by traversing __dict__s.

    :returns:
        Returns a tuple of (True/False, and an error message if an assertion
        fails). True if the two objects are deeply equal, otherwise false.
    """
    try:
        _deep_eq(a, b)
    except AssertionError, err:
        return False, err.message
    return True, ''


def _deep_eq(a, b):
    """Do the actual deep comparison. If two items up for comparison is not
    equal, a :exception:`AssertionError` is raised (to :function:`deep_eq`).
    """
    if isinstance(a, (list, tuple)):
        _test_seq(a, b)
    elif isinstance(a, dict):
        _test_dict(a, b)
    elif hasattr(a, '__dict__'):
        assert a.__class__ == b.__class__, (
            'Class mismatch. Expected %s, got %s' % (a.__class__, b.__class__)
        )
        _test_dict(a.__dict__, b.__dict__)
    elif isinstance(a, collections.Iterable) and not isinstance(a, str):
        # If there's a generator or another type of iterable, treat it as a
        # `list`. NOTE: Generators will be exhausted if you do this.
        _test_seq(list(a), list(b))
    else:
        # must be a 'primitive'
        assert a == b, 'Expected %s, got %s' % (a, b)


def _test_dict(a, b):
    """Compare `dict` types recursively."""
    assert len(a) == len(b)

    for key in a:
        _deep_eq(a[key], b[key])


def _test_seq(a, b):
    """Compare `list` or `tuple` types recursively."""
    assert len(a) == len(b), ('Sequence length mismatch. Expected %s, got %s'
                              % (len(a), len(b)))
    for i, item in enumerate(a):
        _deep_eq(item, b[i])


def assert_xml_equal(a, b):
    """
    Compare two XML artifacts for equality.

    :param a, b:
        Paths to XML files, or a file-like object containing the XML
        contents.
    """
    tools.assert_equal(tostring(parse(a).getroot()),
                       tostring(parse(b).getroot()))


def validates_against_xml_schema(
        xml_instance_path,
        schema_path=openquake.nrmllib.nrml_schema_file()):
    """
    Check whether an XML file validates against an XML schema.
    """

    xml_doc = etree.parse(xml_instance_path)
    xmlschema = etree.XMLSchema(etree.parse(schema_path))
    return xmlschema.validate(xml_doc)
