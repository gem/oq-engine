import unittest
import os

from hmtk.parsers.catalogue.csv_catalogue_parser import CsvCatalogueParser

class CsvCatalogueParserTestCase(unittest.TestCase):
    """ Unit tests for the csv Catalogue Parser Class"""
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    
    def setUp(self):
        filename = os.path.join(self.BASE_DATA_PATH, 'test_catalogue.csv') 
        print filename 
        parser = CsvCatalogueParser(filename)
        self.cat = parser.read_file()

    def test_read_catalogue(self):
        
        self.assertEqual(self.cat.data['eventID'][0], 54)
        self.assertEqual(self.cat.data['Agency'][0], 'sheec')
        self.assertEqual(self.cat.data['Identifier'][0], '')
        self.assertEqual(self.cat.data['year'][0], 1011)
        
    def test_read_catalogue_num_events(self):
        self.assertEqual(self.cat.get_number_events(),8)