import json
import mock
from django.utils import unittest

from django.test.client import RequestFactory

from engine import views
def _get_haz_calcs():
    return [
        (1, 'executing', 'description 1'),
        (2, 'pre_executing', 'description 2'),
        (3, 'complete', 'description e'),
    ]
views._get_haz_calcs = views._get_haz_calcs


class CalcHazardTestCase(unittest.TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_get(self):
        expected_content = json.dumps([
            {u'url': u'http://www.openquake.org/calc/hazard/1',
             u'status': u'executing',
             u'description': u'description 1',
             u'id': 1},
            {u'url': u'http://www.openquake.org/calc/hazard/2',
             u'status': u'pre_executing',
             u'description': u'description 2',
             u'id': 2},
            {u'url': u'http://www.openquake.org/calc/hazard/3',
             u'status': u'complete',
             u'description': u'description e',
             u'id': 3},
        ])
        with mock.patch('engine.views._get_haz_calcs') as ghc:
            ghc.return_value = [
                (1, 'executing', 'description 1'),
                (2, 'pre_executing', 'description 2'),
                (3, 'complete', 'description e'),
            ]
            request = self.factory.get('/calc/hazard/')
            request.META['HTTP_HOST'] = 'www.openquake.org'
            response = views.calc_hazard(request)

            self.assertEqual(200, response.status_code)
            self.assertEqual(expected_content, response.content)


class CalcRiskTestCase(unittest.TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_get(self):
        expected_content = json.dumps([
            {u'url': u'http://www.openquake.org/calc/risk/1',
             u'status': u'executing',
             u'description': u'description 1',
             u'id': 1},
            {u'url': u'http://www.openquake.org/calc/risk/2',
             u'status': u'pre_executing',
             u'description': u'description 2',
             u'id': 2},
            {u'url': u'http://www.openquake.org/calc/risk/3',
             u'status': u'complete',
             u'description': u'description e',
             u'id': 3},
        ])
        with mock.patch('engine.views._get_risk_calcs') as grc:
            grc.return_value = [
                (1, 'executing', 'description 1'),
                (2, 'pre_executing', 'description 2'),
                (3, 'complete', 'description e'),
            ]
            request = self.factory.get('/calc/risk/')
            request.META['HTTP_HOST'] = 'www.openquake.org'
            response = views.calc_risk(request)

            self.assertEqual(200, response.status_code)
            self.assertEqual(expected_content, response.content)
