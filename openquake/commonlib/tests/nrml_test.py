import unittest
import io
from openquake.commonlib.nrml import read, node_to_xml


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
        outfile = io.BytesIO()
        node_to_xml(root, outfile, {})
        self.assertEqual(outfile.getvalue(), """\
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
""")
