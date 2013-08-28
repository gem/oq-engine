import io
import os
import zipfile
import unittest
import tempfile
from lxml import etree
from openquake.nrmllib.convert import (
    convert_nrml_to_zip, build_node, InvalidFile)

DATADIR = os.path.join(os.path.dirname(__file__), 'data')


def fakefile(name, data):
    f = io.StringIO(unicode(data))
    f.name = name
    return f


class ConvertGoodFilesTestCase(unittest.TestCase):
    """
    These are the tests for well formed files. They check that it is
    possible to start from a valid NRML file, convert into into a .zip
    archive of flat files and the convert back the archive to the
    original .xml file.
    """
    def check_round_trip(self, name):
        fname = os.path.join(DATADIR, name)
        f = convert_nrml_to_zip(fname)
        z = zipfile.ZipFile(f)
        files = [z.open(i) for i in z.infolist()
                 if i.filename.endswith(('.json', '.csv'))]
        with open(fname + '~', 'wb') as out:
            build_node(files, out)
        if open(fname).read() != open(out.name).read():
            raise ValueError('Files %s and %s are different' %
                             (fname, out.name))

    def test_vulnerability(self):
        self.check_round_trip('vulnerability-model-discrete.xml')

    def test_fragility_discrete(self):
        self.check_round_trip('fragility-model-discrete.xml')

    def test_fragility_continuous(self):
        self.check_round_trip('fragility-model-continuous.xml')

    def test_exposure_population(self):
        self.check_round_trip('exposure-population.xml')

    def test_exposure_buildings(self):
        self.check_round_trip('exposure-buildings.xml')


class ConvertBadFilesTestCase(unittest.TestCase):

    def vuln_json(self):
        return fakefile('vm.json', '''\
{"tag": "vulnerabilityModel",
 "vulnerabilitysetid": "PAGER",
 "assetcategory": "population",
 "losscategory": "fatalities",
 "vulnerabilityfunctionids": ["IR", "PK"],
 "probabilitydistributions": ["LN", "LN"],
 "fieldnames": ["IML", "IR.lossRatio", "IR.coefficientsVariation",
                "PK.lossRatio", "PK.coefficientsVariation"],
 "imt": "MMI"}
''')

    def test_empty(self):
        files = [fakefile('empty.json', ''),
                 fakefile('empty.csv', '')]
        with self.assertRaises(InvalidFile):
            build_node(files)

    def test_no_header(self):
        files = [fakefile('some.json', '''{"tag": "vulnerabilityModel",
 "fieldnames": ["a","b"]}'''), fakefile('some.csv', '')]
        with self.assertRaises(ValueError):
            build_node(files)

    def test_no_data(self):
        files = [fakefile('some.json', '''{"tag": "vulnerabilityModel",
 "fieldnames": ["a","b"], "vulnerabilityfunctionids": [],
 "probabilitydistributions": [], "imt": "PGA", "vulnerabilitysetid": "PAGER",
 "assetcategory": "category", "losscategory": "category"
}'''), fakefile('some.csv', 'a,b')]
        with self.assertRaises(etree.DocumentInvalid):
            with tempfile.TemporaryFile() as out:
                build_node(files, out)

    def test_bad_data_1(self):
        files = [self.vuln_json(),
                 fakefile('vm.csv', '''\
IML,IR.lossRatio,IR.coefficientsVariation,PK.lossRatio,PK.coefficientsVariation
5.00,0.00,0.30,0.00,0.30
5.50,0.00,0.30,0.00,0.30
6.00,0.00,0.30,0.00,
''')]
        with self.assertRaises(InvalidFile):
            with tempfile.NamedTemporaryFile() as out:
                build_node(files, out)

    def test_bad_data_2(self):
        files = [self.vuln_json(),
                 fakefile('vm.csv', '''\
IML,IR.lossRatio,IR.coefficientsVariation,PK.lossRatio,PK.coefficientsVariation
5.00,0.00,0.30,0.00,0.30
5.50,0.00,0.30,0.00,0.30
6.00,0.00,0.30,0.00
''')]
        with self.assertRaises(InvalidFile):
            with tempfile.NamedTemporaryFile() as out:
                build_node(files, out)


class EXPOSURE_POPULATION_OK:
    JSON = fakefile('ep.json', '''\
{"category": "population",
"taxonomysource": "fake population datasource",
"description": "Sample population",
"fieldnames": ["id", "taxonomy", "lon", "lat", "number"],
"id": "my_exposure_model_for_population"},
"tag": "exposureModel"
''')
    CSV = fakefile('ep.csv', '''\
id,taxonomy,lon,lat,number
asset_01,IT-PV,9.15000,45.16667,7
asset_02,IT-CE,9.15333,45.12200,7
''')


class EXPOSURE_BULDINGS_OK:
    JSON = fakefile('eb.json', '''\
{"category": "buildings",
"description": "Sample buildings", "insuranceLimit": {"isAbsolute": "false"},
"fieldnames": ["id", "taxonomy", "lon", "lat", "number", "area",
               "business_interruption.value",
               "business_interruption.deductible",
               "business_interruption.insurancelimit",
               "business_interruption.retrofitted",
               "contents.value", "contents.deductible",
               "contents.insurancelimit", "contents.retrofitted",
               "non_structural.value", "non_structural.deductible",
               "non_structural.insurancelimit", "non_structural.retrofitted",
               "structural.value", "structural.deductible",
               "structural.insurancelimit", "structural.retrofitted",
               "night", "day", "transit"],
"costtypes": [{"type": "per_area", "name": "business_interruption",
               "unit": "EUR"},
              {"type": "per_area", "name": "contents", "unit": "USD"},
              {"type": "aggregated", "name": "non_structural", "unit": "YEN"},
              {"retrofittedUnit": "EUR", "type": "aggregated",
               "name": "structural", "unit": "YEN",
                "retrofittedType": "aggregated"}],
"deductible": {"isAbsolute": "false"},
"taxonomysource": "PAGER", "id": "my_exposure_model"}
''')

    CSV = fakefile('eb.csv', '''\
id,taxonomy,lon,lat,number,area,business_interruption.value,business_interruption.deductible,business_interruption.insurancelimit,business_interruption.retrofitted,contents.value,contents.deductible,contents.insurancelimit,contents.retrofitted,non_structural.value,non_structural.deductible,non_structural.insurancelimit,non_structural.retrofitted,structural.value,structural.deductible,structural.insurancelimit,structural.retrofitted,night,day,transit
asset_01,RC/DMRF-D/LR,9.15000,45.16667,7,120,40,.5,,,12.95,.5,,,25000,.09,,,150000,.1,,109876,100,50,20
asset_02,RC/DMRF-D/HR,9.15333,45.12200,7,119,40,,,,21.95,,,,21000,,,,250000,,,,12,50,20
asset_03,RC/DMRF-D/LR,9.14777,45.17999,5,118,,,,,30.95,,,,,,,,500000,,,,,,
''')
