# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2017 GEM Foundation
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

import io
import copy
import pickle
import unittest

from openquake.baselib import node as n


class NodeTestCase(unittest.TestCase):
    """Tests for the Node class and related facilities"""

    def test_setitem(self):
        root = n.Node('root')
        root['a'] = 'A'
        self.assertEqual(root['a'], 'A')
        self.assertEqual(root.attrib['a'], 'A')

    def test_to_str(self):
        # tests the methods .to_str with expandattrs and expandvals off
        root = n.Node('root')
        a = n.Node('a', dict(zz='ZZ'), text="A")
        b = n.Node('b')
        x1 = n.Node('x1')
        x2 = n.Node('x2')
        root.append(a)
        root.append(b)
        root.a.append(x1)
        root.a.append(x2)
        self.assertEqual(
            root.to_str(expandvals=False, expandattrs=False), '''\
root
  a{zz}
    x1
    x2
  b
''')
        self.assertEqual(
            root.to_str(expandvals=True, expandattrs=False), '''\
root
  a{zz} 'A'
    x1
    x2
  b
''')

        self.assertEqual(root.to_str(), '''\
root
  a{zz='ZZ'} 'A'
    x1
    x2
  b
''')

    def test_getitem(self):
        # test the __getitem__ method
        nodes = [n.Node('a', dict(z='Z')), n.Node('b')]
        root = n.Node('root', nodes=nodes)
        self.assertEqual(root.a['z'], 'Z')
        self.assertEqual(root[0], nodes[0])
        self.assertEqual(root[1], nodes[1])
        self.assertEqual(list(root), nodes)

    def test_ini(self):
        # can read and write a .ini file converted into a Node object
        inifile = io.StringIO(u"""\
[general]
a = 1
b = 2
[section1]
param = xxx
[section2]
param = yyy
""")
        node = n.node_from_ini(inifile)
        outfile = io.StringIO()
        n.node_to_ini(node, outfile)
        self.assertEqual(outfile.getvalue(), '''
[general]
a=1
b=2

[section1]
param=xxx

[section2]
param=yyy
''')

    def test_xml(self):
        # can read and write a .xml file converted into a Node object
        xmlfile = io.StringIO(u"""\
<root>
<general>
<a>1</a>
<b>2</b>
</general>
<section1 param="xxx" />
<section2 param="yyy" />
</root>
""")
        node = n.node_from_xml(xmlfile)
        outfile = io.BytesIO()
        n.node_to_xml(node, outfile)
        self.assertEqual(outfile.getvalue(), b"""\
<?xml version="1.0" encoding="utf-8"?>
<root>
    <general>
        <a>
            1
        </a>
        <b>
            2
        </b>
    </general>
    <section1 param="xxx"/>
    <section2 param="yyy"/>
</root>
""")

    def test_reserved_name(self):
        # there are four reserved names: tag, attrib, text, nodes
        # this is an example of what happens for 'tag'
        node = n.Node('tag')
        root = n.Node('root', nodes=[node])
        self.assertEqual(root.tag, 'root')  # not node, use __getattr__
        self.assertEqual(root.__getattr__('tag'), node)

    def test_dict(self):
        # convertion to and from JSON strings
        input_dict = {
            "attrib": {},
            "nodes": [
                {
                    "attrib": {},
                    "tag": "a",
                    "text": "A"
                    }
                ],
            "tag": "root",
            "text": None
            }
        expected_dict = {
            "nodes": [
                {
                    "tag": "a",
                    "text": "A"
                    }
                ],
            "tag": "root",
            }
        node = n.node_from_dict(input_dict)
        output_dict = n.node_to_dict(node)
        self.assertEqual(expected_dict, output_dict)

        # test deepcopy
        self.assertEqual(node, copy.deepcopy(node))

    def test_can_pickle(self):
        node = n.Node('tag')
        self.assertEqual(pickle.loads(pickle.dumps(node)), node)
