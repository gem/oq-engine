import json
import mock

from collections import namedtuple
from django.utils import unittest
from django.test.client import RequestFactory

from engine import views

FakeOutput = namedtuple('FakeOutput', 'id, display_name, output_type')


class BaseViewTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.factory = RequestFactory()


class UtilsTestCase(BaseViewTestCase):

    def setUp(self):
        self.request = self.factory.get('does not matter')

    def test__get_base_url_http(self):
        self.request.is_secure = lambda: False
        self.request.META['HTTP_HOST'] = 'www.openquake.org:8080'
        self.assertEqual('http://www.openquake.org:8080',
                         views._get_base_url(self.request))

    def test__get_base_url_https(self):
        self.request.is_secure = lambda: True
        self.request.META['HTTP_HOST'] = 'www.openquake.org'
        self.assertEqual('https://www.openquake.org',
                         views._get_base_url(self.request))


class CalcHazardTestCase(BaseViewTestCase):

    def test_get(self):
        expected_content = [
            {u'url': u'http://www.openquake.org/v1/calc/hazard/1',
             u'status': u'executing',
             u'description': u'description 1',
             u'id': 1},
            {u'url': u'http://www.openquake.org/v1/calc/hazard/2',
             u'status': u'pre_executing',
             u'description': u'description 2',
             u'id': 2},
            {u'url': u'http://www.openquake.org/v1/calc/hazard/3',
             u'status': u'complete',
             u'description': u'description e',
             u'id': 3},
        ]
        with mock.patch('engine.views._get_haz_calcs') as ghc:
            ghc.return_value = [
                (1, 'executing', 'description 1'),
                (2, 'pre_executing', 'description 2'),
                (3, 'complete', 'description e'),
            ]
            request = self.factory.get('/v1/calc/hazard/')
            request.META['HTTP_HOST'] = 'www.openquake.org'
            response = views.calc_hazard(request)

            self.assertEqual(200, response.status_code)
            self.assertEqual(expected_content, json.loads(response.content))


class CalcRiskTestCase(BaseViewTestCase):

    def test_get(self):
        expected_content = [
            {u'url': u'http://www.openquake.org/v1/calc/risk/1',
             u'status': u'executing',
             u'description': u'description 1',
             u'id': 1},
            {u'url': u'http://www.openquake.org/v1/calc/risk/2',
             u'status': u'pre_executing',
             u'description': u'description 2',
             u'id': 2},
            {u'url': u'http://www.openquake.org/v1/calc/risk/3',
             u'status': u'complete',
             u'description': u'description e',
             u'id': 3},
        ]
        with mock.patch('engine.views._get_risk_calcs') as grc:
            grc.return_value = [
                (1, 'executing', 'description 1'),
                (2, 'pre_executing', 'description 2'),
                (3, 'complete', 'description e'),
            ]
            request = self.factory.get('/v1/calc/risk/')
            request.META['HTTP_HOST'] = 'www.openquake.org'
            response = views.calc_risk(request)

            self.assertEqual(200, response.status_code)
            self.assertEqual(expected_content, json.loads(response.content))


class CalcToResponseDataTestCase(unittest.TestCase):
    """
    Tests for `engine.views._calc_to_response_data`.
    """

    def setUp(self):
        Field = namedtuple('Field', 'name')
        self.calc = mock.Mock()
        field_names = [
            'base_path', 'export_dir', 'owner',
            'region', 'sites', 'region_constraint', 'sites_disagg',
            'hazard_calculation', 'hazard_output',
            'description', 'maximum_distance',
        ]
        self.calc._meta.fields = [Field(name) for name in field_names]

        # general stuff
        self.calc.base_path = '/foo/bar/'
        self.calc.export_dir = '/tmp/outputs/'
        self.calc.owner = object()

        # geometry
        self.calc.region.geojson = (
            '{ "type": "Polygon", "coordinates": '
               '[[[1, 1], [2, 3], [3, 1], [1, 1]]] }'
        )
        self.calc.sites.geojson = (
            '{ "type": "MultiPoint", "coordinates": '
               '[[100.0, 0.0], [101.0, 1.0]] }'
        )
        self.calc.region_constraint.geojson = (
            '{ "type": "Polygon", "coordinates": '
               '[[[2, 2], [3, 4], [4, 1], [1, 1]]] }'
        )
        self.calc.sites_disagg.geojson = (
            '{ "type": "MultiPoint", "coordinates": '
               '[[100.1, 0.1], [101.1, 1.1]] }'
        )

        # risk inputs
        self.calc.hazard_calculation = object()
        self.calc.hazard_output = object()

        # some sample parameters
        self.calc.description = 'the description'
        self.calc.maximum_distance = 195.5

    def test(self):
        expected = {
            'description': 'the description',
            'maximum_distance': 195.5,
            'region': {
                'coordinates': [[[1, 1], [2, 3], [3, 1], [1, 1]]],
                'type': 'Polygon',
            },
            'region_constraint': {
                'coordinates': [[[2, 2], [3, 4], [4, 1], [1, 1]]],
                'type': 'Polygon',
            },
            'sites': {
                'coordinates': [[100.0, 0.0], [101.0, 1.0]],
                'type': 'MultiPoint',
            },
            'sites_disagg': {
                'coordinates': [[100.1, 0.1], [101.1, 1.1]],
                'type': 'MultiPoint',
            },
        }

        response_data = views._calc_to_response_data(self.calc)

        self.assertEqual(expected, response_data)


class CalcHazardResultsTestCase(BaseViewTestCase):

    def test(self):
        expected_content = [
            {'id': 1, 'name': 'output1', 'type': 'hazard_curve',
             'url': 'http://www.openquake.org/v1/calc/hazard/result/1'},
            {'id': 2, 'name': 'output2', 'type': 'hazard_curve',
             'url': 'http://www.openquake.org/v1/calc/hazard/result/2'},
            {'id': 3, 'name': 'output3', 'type': 'hazard_map',
             'url': 'http://www.openquake.org/v1/calc/hazard/result/3'},
        ]
        with mock.patch('openquake.engine.engine.get_hazard_outputs') as gho:
            gho.return_value = [
                FakeOutput(1, 'output1', 'hazard_curve'),
                FakeOutput(2, 'output2', 'hazard_curve'),
                FakeOutput(3, 'output3', 'hazard_map'),
            ]
            request = self.factory.get('/v1/calc/hazard/1/results')
            request.META['HTTP_HOST'] = 'www.openquake.org'
            response = views.calc_hazard_results(request, 7)

            self.assertEqual(1, gho.call_count)
            self.assertEqual(((7, ), {}), gho.call_args)
            self.assertEqual(200, response.status_code)
            self.assertEqual(expected_content, json.loads(response.content))


class CalcRiskResultsTestCase(BaseViewTestCase):

    def test(self):
        expected_content = [
            {'id': 1, 'name': 'output1', 'type': 'loss_curve',
             'url': 'http://www.openquake.org/v1/calc/risk/result/1'},
            {'id': 2, 'name': 'output2', 'type': 'loss_curve',
             'url': 'http://www.openquake.org/v1/calc/risk/result/2'},
            {'id': 3, 'name': 'output3', 'type': 'loss_map',
             'url': 'http://www.openquake.org/v1/calc/risk/result/3'},
        ]
        with mock.patch('openquake.engine.engine.get_risk_outputs') as gro:
            gro.return_value = [
                FakeOutput(1, 'output1', 'loss_curve'),
                FakeOutput(2, 'output2', 'loss_curve'),
                FakeOutput(3, 'output3', 'loss_map'),
            ]
            request = self.factory.get('/v1/calc/risk/1/results')
            request.META['HTTP_HOST'] = 'www.openquake.org'
            response = views.calc_risk_results(request, 1)

            self.assertEqual(200, response.status_code)
            self.assertEqual(expected_content, json.loads(response.content))
