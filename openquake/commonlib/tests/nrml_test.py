# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2016 GEM Foundation
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

import unittest
import io
from openquake.baselib.general import writetmp
from openquake.commonlib.nrml import read, node_to_xml, get_tag_version


class NrmlTestCase(unittest.TestCase):

    def test_nrml(self):
        # can read and write a NRML file converted into a Node object
        xmlfile = io.BytesIO(b"""\
<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.4"
      xmlns:gml="http://www.opengis.net/gml">
  <exposureModel
      id="my_exposure_model_for_population"
      category="population"
      taxonomySource="fake population datasource">

    <description>
      Sample population
    </description>

    <assets>
      <asset id="asset_01" number="7" taxonomy="IT-PV">
          <location lon="9.15000" lat="45.16667" />
      </asset>

      <asset id="asset_02" number="7" taxonomy="IT-CE">
          <location lon="9.15333" lat="45.12200" />
      </asset>
    </assets>
  </exposureModel>
</nrml>
""")
        root = read(xmlfile)

        tag, version = get_tag_version(root[0])
        self.assertEqual(tag, 'exposureModel')
        self.assertEqual(version, 'nrml/0.4')

        outfile = io.BytesIO()
        node_to_xml(root, outfile, {})

        expected = b"""\
<?xml version="1.0" encoding="utf-8"?>
<nrml
xmlns="http://openquake.org/xmlns/nrml/0.4"
xmlns:gml="http://www.opengis.net/gml"
>
    
    <exposureModel
    category="population"
    id="my_exposure_model_for_population"
    taxonomySource="fake population datasource"
    >
        
        <description>
            Sample population
        </description>
        <assets>
            
            <asset
            id="asset_01"
            number="7.000000000E+00"
            taxonomy="IT-PV"
            >
                
                <location lat="4.516667000E+01" lon="9.150000000E+00"/>
            </asset>
            <asset
            id="asset_02"
            number="7.000000000E+00"
            taxonomy="IT-CE"
            >
                
                <location lat="4.512200000E+01" lon="9.153330000E+00"/>
            </asset>
        </assets>
    </exposureModel>
</nrml>
"""
        self.assertEqual(outfile.getvalue(), expected)

    def test_invalid(self):
        fname = writetmp('''\
<?xml version="1.0" encoding="UTF-8"?>
<nrml xmlns="http://openquake.org/xmlns/nrml/0.5">
  <fragilityModel id="Ethiopia" assetCategory="buildings"
        lossCategory="structural">
    <description>structural_vul_ethiopia</description>
    <limitStates> slight moderate extensive collapse</limitStates>
    <fragilityFunction id="CR/LFINF/H:1,2" format="continuous" shape="logncdf">
       <imls imt="SA" noDamageLimit="0.1" minIML="0.01" maxIML="1.2"/>
       <params ls="slight" mean="0.184422723" stddev="0.143988438"/>
       <params ls="moderate" mean="1.659007804" stddev="3.176361273"/>
       <params ls="extensive" mean="9.747745727" stddev="38.54171001"/>
       <params ls="collapse" mean="247.1792873" stddev="4014.774504"/>
     </fragilityFunction>
  </fragilityModel>
</nrml>''')
        with self.assertRaises(ValueError) as ctx:
            read(fname)
        self.assertIn('Could not convert imt->intensity_measure_type: '
                      "Invalid IMT: 'SA', line 8", str(ctx.exception))
