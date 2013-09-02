import os
import unittest
import tempfile
from openquake.nrmllib import InvalidFile
from openquake.nrmllib.convert import (
    convert_nrml_to_zip, convert_zip_to_nrml, build_node)
from openquake.nrmllib.readers import FakeReader

DATADIR = os.path.join(os.path.dirname(__file__), 'data')


class ConvertGoodFilesTestCase(unittest.TestCase):
    """
    These are the tests for well formed files. They check that it is
    possible to start from a valid NRML file, convert into into a .zip
    archive of flat files and the convert back the archive to the
    original .xml file.
    """
    def check_round_trip(self, name):
        fname = os.path.join(DATADIR, name)
        z = convert_nrml_to_zip(fname)
        tmp = tempfile.gettempdir()
        [outname] = convert_zip_to_nrml(z, tmp)
        if open(fname).read() != open(outname).read():
            raise ValueError('Files %s and %s are different' %
                             (fname, outname))

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
    JSON = '''\
{"tag": "vulnerabilityModel",
 "vulnerabilitysetid": "PAGER",
 "assetcategory": "population",
 "losscategory": "fatalities",
 "vulnerabilityfunctionids": ["IR", "PK"],
 "probabilitydistributions": ["LN", "LN"],
 "fieldnames": ["IML", "IR.lossRatio", "IR.coefficientsVariation",
                "PK.lossRatio", "PK.coefficientsVariation"],
 "imt": "MMI"}
'''

    def test_empty(self):
        with self.assertRaises(InvalidFile):
            build_node([FakeReader('empty', '', '')])

    def test_no_header(self):
        with self.assertRaises(ValueError):
            FakeReader('some', '''{"tag": "vulnerabilityModel",
 "fieldnames": ["a","b"]}''', '')

    def test_no_data(self):
        reader = FakeReader('some', '''{"tag": "vulnerabilityModel",
 "fieldnames": ["a","b"], "vulnerabilityfunctionids": [],
 "probabilitydistributions": [], "imt": "PGA", "vulnerabilitysetid": "PAGER",
 "assetcategory": "category", "losscategory": "category"
}''', 'a,b')
        with self.assertRaises(InvalidFile):
            with tempfile.TemporaryFile() as out:
                build_node([reader], out)

    def test_bad_data_1(self):
        reader = FakeReader('vm', self.JSON, '''\
IML,IR.lossRatio,IR.coefficientsVariation,PK.lossRatio,PK.coefficientsVariation
5.00,0.00,0.30,0.00,0.30
5.50,0.00,0.30,0.00,0.30
6.00,0.00,0.30,0.00,
''')
        with self.assertRaises(InvalidFile):
            with tempfile.NamedTemporaryFile() as out:
                build_node([reader], out)

    def test_bad_data_2(self):
        reader = FakeReader('vm', self.JSON, '''\
IML,IR.lossRatio,IR.coefficientsVariation,PK.lossRatio,PK.coefficientsVariation
5.00,0.00,0.30,0.00,0.30
5.50,0.00,0.30,0.00,0.30
6.00,0.00,0.30,0.00
''')
        with self.assertRaises(InvalidFile):
            with tempfile.NamedTemporaryFile() as out:
                build_node([reader], out)
