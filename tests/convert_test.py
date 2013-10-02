# -*- encoding: utf-8 -*-
import os
import unittest
import tempfile
from openquake.nrmllib import InvalidFile
from openquake.nrmllib.converter import Converter
from openquake.nrmllib.record import ZipArchive, DirArchive, MemArchive

DATADIR = os.path.join(os.path.dirname(__file__), 'data')

DVSet = '''\
vulnerabilitySetID,assetCategory,lossCategory,IMT
PAGER,population,fatalities,MMI
NPAGER,population,fatalities,MMI
'''

DVFun = '''\
vulnerabilitySetID,vulnerabilityFunctionID,probabilisticDistribution
PAGER,IR,LN
PAGER,PK,LN
NPAGER,AA,LN
NPAGER,BB,LN
'''


def fake_archive(dvs=DVSet, dvf=DVFun, dvd=''):
    return MemArchive(
        ('test__Vulnerability__DiscreteVulnerabilitySet.csv', dvs),
        ('test__Vulnerability__DiscreteVulnerability.csv', dvf),
        ('test__Vulnerability__DiscreteVulnerabilityData.csv', dvd),
        )


class ConvertGoodFilesTestCase(unittest.TestCase):
    """
    These are the tests for well formed files. They check that it is
    possible to start from a valid NRML file, convert into into a .zip
    archive of flat files and the convert back the archive to the
    original .xml file.
    """
    def check_round_trip(self, xmlname):
        # from nrml -> zip an back
        name = xmlname[:-4]
        fname = os.path.join(DATADIR, xmlname)
        zipname = fname[:-4] + '.zip'
        archive = DirArchive(zipname, 'w')
        try:
            conv = Converter(name, archive)
            conv.nrml_to_csv(fname)
            #archive.opened = set()
            #archive.close()
            outname = os.path.join(tempfile.gettempdir(), xmlname)
            with open(outname, 'w') as out:
                conv.get().csv_to_nrml(out)
            if open(fname).read() != open(outname).read():
                raise ValueError('Files %s and %s are different' %
                                 (fname, outname))
        finally:
            archive.close()
            #os.remove(zipname)

    def test_vulnerability(self):
        self.check_round_trip('vulnerability-model-discrete.xml')

    def test_fragility_discrete(self):
        self.check_round_trip('fragility-model-discrete.xml')

    def test_fragility_continuous(self):
        self.check_round_trip('fragility-model-continuous.xml')

    ## TEMPORARILY COMMENTED OUT TESTS

    #def test_exposure_population(self):
    #    self.check_round_trip('exposure-population.xml')

    #def test_exposure_buildings(self):
    #    self.check_round_trip('exposure-buildings.xml')

    def test_gmf_scenario(self):
        self.check_round_trip('gmf-scenario.xml')

    def test_gmf_event_based(self):
        self.check_round_trip('gmf-event-based.xml')


class ConvertBadFilesTestCase(unittest.TestCase):

    def test_empty_archive(self):
        empty_archive = MemArchive()
        with self.assertRaises(RuntimeError):
            Converter('', empty_archive).get()

    def test_empty_files(self):
        archive = fake_archive('', '', '')
        conv = Converter('', archive).get()
        self.assertEqual(conv.csv_to_node().to_str(), 'vulnerabilityModel\n')

    def test_no_header(self):
        archive = fake_archive(dvd='5.00,0.00,0.30')
        conv = Converter('', archive).get()
        with self.assertRaises(InvalidFile):
            conv.csv_to_node().to_str()

    def test_no_data(self):
        archive = fake_archive(
            dvd='vulnerabilitySetID,vulnerabilityFunctionID,'
            'IML,lossRatio,coefficientsVariation')
        conv = Converter('', archive).get()
        with self.assertRaises(InvalidFile):
            conv.csv_to_node()

    def test_bad_data_1(self):
        archive = fake_archive(dvd='''\
vulnerabilitySetID,vulnerabilityFunctionID,IML,lossRatio,coefficientsVariation
PAGER,IR,5.00,0.00,0.30
PAGER,IR,5.50,0.00,0.30
PAGER,IR,6.00,0.00,''')
        conv = Converter('', archive).get()
        with self.assertRaises(InvalidFile):
            conv.csv_to_node()

    def test_bad_data_2(self):
        archive = fake_archive(dvd='''\
vulnerabilitySetID,vulnerabilityFunctionID,IML,lossRatio,coefficientsVariation
PAGER,IR,5.00,0.00,0.30
PAGER,IR,5.50,0.00,0.30
PAGER,IR,6.00,0.00''')
        conv = Converter('', archive).get()
        with self.assertRaises(InvalidFile):
            conv.csv_to_node()
