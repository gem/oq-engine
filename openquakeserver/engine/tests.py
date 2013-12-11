import json
import mock
import os
import StringIO
import shutil
import tempfile

from collections import namedtuple
from django.utils.datastructures import MultiValueDict
from django.core.exceptions import ObjectDoesNotExist
from django.test.client import RequestFactory
from django.utils import unittest

from engine import views
from engine import _test_utils as utils

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

    def setUp(self):
        self.request = self.factory.get('/v1/calc/hazard/')
        self.request.META['HTTP_HOST'] = 'www.openquake.org'

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
            response = views.calc_hazard(self.request)

            self.assertEqual(200, response.status_code)
            self.assertEqual(expected_content, json.loads(response.content))

    def test_404_no_calcs(self):
        with mock.patch('engine.views._get_haz_calcs') as ghc:
            ghc.return_value = []
            response = views.calc_hazard(self.request)

        self.assertEqual(404, response.status_code)


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
            'owner': self.calc.owner,
            'region': {
                u'coordinates': [[[1, 1], [2, 3], [3, 1], [1, 1]]],
                u'type': u'Polygon',
            },
            'region_constraint': {
                u'coordinates': [[[2, 2], [3, 4], [4, 1], [1, 1]]],
                u'type': u'Polygon',
            },
            'sites': {
                u'coordinates': [[100.0, 0.0], [101.0, 1.0]],
                u'type': u'MultiPoint',
            },
            'sites_disagg': {
                u'coordinates': [[100.1, 0.1], [101.1, 1.1]],
                u'type': u'MultiPoint',
            },
        }

        response_data = views._calc_to_response_data(self.calc)

        self.assertEqual(expected, response_data)


class CalcHazardResultsTestCase(BaseViewTestCase):

    def setUp(self):
        self.request = self.factory.get('/v1/calc/hazard/1/results')
        self.request.META['HTTP_HOST'] = 'www.openquake.org'

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
            with mock.patch('openquake.engine.db.models'
                            '.HazardCalculation.objects.get') as hc_get:
                hc_get.return_value.oqjob.status = 'complete'
                gho.return_value = [
                    FakeOutput(1, 'output1', 'hazard_curve'),
                    FakeOutput(2, 'output2', 'hazard_curve'),
                    FakeOutput(3, 'output3', 'hazard_map'),
                ]
                self.request = self.factory.get('/v1/calc/hazard/1/results')
                self.request.META['HTTP_HOST'] = 'www.openquake.org'
                response = views.calc_hazard_results(self.request, 7)

                self.assertEqual(1, gho.call_count)
                self.assertEqual(((7, ), {}), gho.call_args)
                self.assertEqual(200, response.status_code)
                self.assertEqual(expected_content,
                                 json.loads(response.content))

    def test_404_no_outputs(self):
        with mock.patch('openquake.engine.engine.get_hazard_outputs') as gho:
            with mock.patch('openquake.engine.db.models'
                            '.HazardCalculation.objects.get') as hc_get:
                hc_get.return_value.oqjob.status = 'complete'
                gho.return_value = []
                response = views.calc_hazard_results(self.request, 7)

        self.assertEqual(404, response.status_code)

    def test_404_calc_not_exists(self):
        with mock.patch('openquake.engine.db.models'
                        '.HazardCalculation.objects.get') as hc_get:
            hc_get.side_effect = ObjectDoesNotExist
            response = views.calc_hazard_results(self.request, 7)

        self.assertEqual(404, response.status_code)


    def test_404_calc_not_complete(self):
        with mock.patch('openquake.engine.db.models'
                        '.HazardCalculation.objects.get') as hc_get:
            hc_get.return_value.oqjob.status = 'pre_executing'
            response = views.calc_hazard_results(self.request, 7)

        self.assertEqual(404, response.status_code)


class CalcRiskResultsTestCase(BaseViewTestCase):

    def setUp(self):
        self.request = self.factory.get('/v1/calc/risk/1/results')
        self.request.META['HTTP_HOST'] = 'www.openquake.org'

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
            with mock.patch('openquake.engine.db.models'
                                        '.RiskCalculation.objects.get') as rc_get:
                rc_get.return_value.oqjob.status = 'complete'

                gro.return_value = [
                    FakeOutput(1, 'output1', 'loss_curve'),
                    FakeOutput(2, 'output2', 'loss_curve'),
                    FakeOutput(3, 'output3', 'loss_map'),
                ]
                response = views.calc_risk_results(self.request, 1)

            self.assertEqual(200, response.status_code)
            self.assertEqual(expected_content, json.loads(response.content))

    def test_404_no_outputs(self):
        with mock.patch('openquake.engine.engine.get_risk_outputs') as gro:
            with mock.patch('openquake.engine.db.models'
                            '.RiskCalculation.objects.get') as rc_get:
                rc_get.return_value.oqjob.status = 'complete'
                gro.return_value = []
                response = views.calc_risk_results(self.request, 1)

        self.assertEqual(404, response.status_code)

    def test_404_calc_not_exists(self):
        with mock.patch('openquake.engine.db.models'
                        '.RiskCalculation.objects.get') as hc_get:
            hc_get.side_effect = ObjectDoesNotExist
            response = views.calc_risk_results(self.request, 1)

        self.assertEqual(404, response.status_code)


    def test_404_calc_not_complete(self):
        with mock.patch('openquake.engine.db.models'
                        '.RiskCalculation.objects.get') as hc_get:
            hc_get.return_value.oqjob.status = 'pre_executing'
            response = views.calc_risk_results(self.request, 1)

        self.assertEqual(404, response.status_code)



class GetResultTestCase(BaseViewTestCase):
    """
    Tests for :func:`engine.views.get_hazard_result`,
    :func:`engine.views.get_risk_result`, and the helper function
    :func:`engine.views._get_result`.
    """

    def test_hazard_default_export_type(self):
        with mock.patch('openquake.engine.export.hazard.export') as export:
            with mock.patch('openquake.engine.db.models'
                            '.Output.objects.get') as output_get:
                output_get.return_value.oq_job.status = 'complete'
                ret_val = StringIO.StringIO()
                ret_val.write('Fake result file content')
                ret_val.close()
                export.return_value = ret_val

                request = self.factory.get('/v1/calc/hazard/result/37')
                response = views.get_hazard_result(request, 37)

                self.assertEqual(200, response.status_code)
                self.assertEqual('Fake result file content', response.content)

                # Test the call to the export function, including the handling for
                # the default export type:
                self.assertEqual(1, export.call_count)
                self.assertEqual(37, export.call_args[0][0])
                self.assertEqual('xml', export.call_args[1]['export_type'])

    def test_hazard(self):
        with mock.patch('openquake.engine.export.hazard.export') as export:
            with mock.patch('openquake.engine.db.models'
                            '.Output.objects.get') as output_get:
                output_get.return_value.oq_job.status = 'complete'

                ret_val = StringIO.StringIO()
                ret_val.write('Fake result file content')
                ret_val.close()
                export.return_value = ret_val

                request = self.factory.get(
                    '/v1/calc/hazard/result/37?export_type=csv'
                )
                response = views.get_hazard_result(request, 37)

                self.assertEqual(200, response.status_code)
                self.assertEqual('Fake result file content', response.content)

                self.assertEqual(1, export.call_count)
                self.assertEqual(37, export.call_args[0][0])
                self.assertEqual('csv', export.call_args[1]['export_type'])

    def test_risk_default_export_type(self):
        with mock.patch('openquake.engine.export.risk.export') as export:
            with mock.patch('openquake.engine.db.models'
                            '.Output.objects.get') as output_get:
                output_get.return_value.oq_job.status = 'complete'

                ret_val = StringIO.StringIO()
                ret_val.write('Fake result file content')
                ret_val.close()
                export.return_value = ret_val

                request = self.factory.get('/v1/calc/risk/result/37')
                response = views.get_risk_result(request, 37)

                self.assertEqual(200, response.status_code)
                self.assertEqual('Fake result file content', response.content)

                self.assertEqual(1, export.call_count)
                self.assertEqual(37, export.call_args[0][0])
                self.assertEqual('xml', export.call_args[1]['export_type'])

    def test_risk(self):
        with mock.patch('openquake.engine.export.risk.export') as export:
            with mock.patch('openquake.engine.db.models'
                            '.Output.objects.get') as output_get:
                output_get.return_value.oq_job.status = 'complete'

                ret_val = StringIO.StringIO()
                ret_val.write('Fake result file content')
                ret_val.close()
                export.return_value = ret_val

                request = self.factory.get(
                    '/v1/calc/risk/result/37?export_type=csv'
                )
                response = views.get_risk_result(request, 37)

                self.assertEqual(200, response.status_code)
                self.assertEqual('Fake result file content', response.content)

                self.assertEqual(1, export.call_count)
                self.assertEqual(37, export.call_args[0][0])
                self.assertEqual('csv', export.call_args[1]['export_type'])


class IsSourceModelTestCase(unittest.TestCase):

    def test_true(self):
        content = '''<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">
    <sourceModel name="Some Source Model">
        <pointSource id="1" name="point" tectonicRegion="Stable Continental Crust">
            <pointGeometry>
                <gml:Point>
                    <gml:pos>-122.0 38.0</gml:pos>
                </gml:Point>
                <upperSeismoDepth>0.0</upperSeismoDepth>
                <lowerSeismoDepth>10.0</lowerSeismoDepth>
            </pointGeometry>
            <magScaleRel>WC1994</magScaleRel>
            <ruptAspectRatio>0.5</ruptAspectRatio>
            <truncGutenbergRichterMFD aValue="-3.5" bValue="1.0" minMag="5.0" maxMag="6.5" />
            <nodalPlaneDist>
                <nodalPlane probability="0.3" strike="0.0" dip="90.0" rake="0.0" />
                <nodalPlane probability="0.7" strike="90.0" dip="45.0" rake="90.0" />
            </nodalPlaneDist>
            <hypoDepthDist>
                <hypoDepth probability="0.5" depth="4.0" />
                <hypoDepth probability="0.5" depth="8.0" />
            </hypoDepthDist>
        </pointSource>
    </sourceModel>
</nrml>
'''
        xml_file = StringIO.StringIO(content)

        self.assertTrue(views._is_source_model(xml_file))

    def test_false(self):
        content = '''<?xml version='1.0' encoding='utf-8'?>
<nrml xmlns:gml="http://www.opengis.net/gml"
      xmlns="http://openquake.org/xmlns/nrml/0.4">

    <pointRupture>
        <magnitude type="Mw">6.5</magnitude>
        <strike>20.0</strike>
        <dip>90.0</dip>
        <rake>10.0</rake>

        <hypocenterLocation>
            <gml:Point srsName="urn:ogc:def:crs:EPSG::4979">
                <gml:pos>-124.704 40.363 30.0</gml:pos>
            </gml:Point>
        </hypocenterLocation>
    </pointRupture>
</nrml>
'''
        xml_file = StringIO.StringIO(content)

        self.assertFalse(views._is_source_model(xml_file))

    def test_not_nrml(self):
        content = '''<html><head></head><body></body></html>'''
        xml_file = StringIO.StringIO(content)

        with self.assertRaises(AssertionError) as ar:
            views._is_source_model(xml_file)
        self.assertEqual('Input file is not a NRML artifact',
                         ar.exception.message)


class FakeTempUploadedFile(object):

    def __init__(self, path, name):
        self.path = path
        self.name = name

    def temporary_file_path(self):
        return self.path

FakeUser = namedtuple('FakeUser', 'id')
FakeJob = namedtuple(
    'FakeJob', 'status, owner, hazard_calculation, risk_calculation'
)
FakeCalc = namedtuple('FakeCalc', 'id, description')


class RunHazardCalcTestCase(BaseViewTestCase):

    def test(self):
        # Test job file inputs:
        fake_job_file = FakeTempUploadedFile('/foo/bar/tmpHfJv16tmp.upload',
                                             'job.ini')
        fake_model_1 = FakeTempUploadedFile('/foo/bar/tmpHmcdv2tmp.upload',
                                            'source_model_logic_tree.xml')
        fake_model_2 = FakeTempUploadedFile('/foo/bar/tmpI66zIGtmp.upload',
                                            'gsim_logic_tree.xml')
        fake_model_3 = FakeTempUploadedFile('/foo/bar/tmpHGa9Whtmp.upload',
                                            'source_model.xml')

        request = mock.Mock()
        request.user.username = 'openquake'
        request.method = 'POST'
        request.get_type.return_value = 'http'
        request.META = dict(HTTP_HOST='www.openquake.org')
        request.FILES = MultiValueDict({
            'job_config': [fake_job_file],
            'input_model_1': [fake_model_1],
            'input_model_2': [fake_model_2],
            'input_model_3': [fake_model_3]})
        request.POST = dict(database="platform")

        # Set up the mocks:
        mocks = dict(
            mkdtemp='tempfile.mkdtemp',
            move='shutil.move',
            job_from_file='openquake.engine.engine.haz_job_from_file',
            run_hazard_task='engine.tasks.run_hazard_calc',
        )
        multi_mock = utils.MultiMock(**mocks)

        temp_dir = tempfile.mkdtemp()

        # Set up expected test values:
        pathjoin = os.path.join
        jff_exp_call_args = (
            (pathjoin(temp_dir, fake_job_file.name), 'openquake', 'progress',
             []),
            {}
        )

        try:
            # For `apply_async` mock function. See below.
            aa_call_data = dict(count=0, args=None)

            with multi_mock:
                multi_mock['mkdtemp'].return_value = temp_dir

                def apply_async(*args):
                    aa_call_data['args'] = args
                    aa_call_data['count'] += 1

                multi_mock['run_hazard_task'].apply_async = apply_async

                fake_job = FakeJob(
                    'pending', FakeUser(1), FakeCalc(666, 'Fake Calc Desc'),
                    None,
                )
                multi_mock['job_from_file'].return_value = fake_job

                # Call the function under test
                print views.run_hazard_calc(request)

            self.assertEqual(1, multi_mock['mkdtemp'].call_count)

            self.assertEqual(4, multi_mock['move'].call_count)
            self.assertEqual(1, multi_mock['job_from_file'].call_count)
            self.assertEqual(jff_exp_call_args,
                             multi_mock['job_from_file'].call_args)

            self.assertEqual(
                {'count': 1,
                 'args': (
                     (666, temp_dir),
                     {'foreign_calc_id': None,
                      'dbname': 'platform',
                      'callback_url': None})},
                aa_call_data
            )

        finally:
            shutil.rmtree(temp_dir)


class RunRiskCalcTestCase(BaseViewTestCase):

    def setUp(self):
        self.request = mock.Mock()
        self.request.user.username = 'openquake'
        self.request.method = 'POST'
        self.request.POST = dict(database="platform")
        self.request.POST['hazard_calculation_id'] = 666
        self.request.META = dict()
        self.request.META['HTTP_HOST'] = 'www.openquake.org'

    def test(self):
        # Test job file inputs:
        fake_job_file = FakeTempUploadedFile('/foo/bar/tmpHfJv16tmp.upload',
                                             'job.ini')
        fake_model_1 = FakeTempUploadedFile('/foo/bar/tmpHmcdv2tmp.upload',
                                            'vulnerability.xml')
        fake_model_2 = FakeTempUploadedFile('/foo/bar/tmpI66zIGtmp.upload',
                                            'exposure.xml')
        self.request.FILES = MultiValueDict({
            'job_config': [fake_job_file, fake_model_1, fake_model_2]})

        # Set up the mocks:
        mocks = dict(
            mkdtemp='tempfile.mkdtemp',
            move='shutil.move',
            job_from_file='openquake.engine.engine.risk_job_from_file',
            run_risk_task='engine.tasks.run_risk_calc',
        )
        multi_mock = utils.MultiMock(**mocks)

        temp_dir = tempfile.mkdtemp()

        # Set up expected test values:
        pathjoin = os.path.join
        move_exp_call_args = [
            ((fake_job_file.path, pathjoin(temp_dir, fake_job_file.name)), {}),
            ((fake_model_1.path, pathjoin(temp_dir, fake_model_1.name)), {}),
            ((fake_model_2.path, pathjoin(temp_dir, fake_model_2.name)), {}),
        ]
        jff_exp_call_args = (
            (pathjoin(temp_dir, fake_job_file.name), 'openquake', 'progress',
             []),
            {'hazard_calculation_id': 666, 'hazard_output_id': None}
        )

        try:
            # For `apply_async` mock function. See below.
            aa_call_data = dict(count=0, args=None)

            with multi_mock:
                multi_mock['mkdtemp'].return_value = temp_dir

                def apply_async(*args):
                    aa_call_data['args'] = args
                    aa_call_data['count'] += 1

                multi_mock['run_risk_task'].apply_async = apply_async

                fake_job = FakeJob(
                    'pending', FakeUser(1), None,
                    FakeCalc(777, 'Fake Calc Desc'),
                )
                multi_mock['job_from_file'].return_value = fake_job

                # Call the function under test
                views.run_risk_calc(self.request)

            self.assertEqual(1, multi_mock['mkdtemp'].call_count)

            self.assertEqual(3, multi_mock['move'].call_count)
            self.assertEqual(move_exp_call_args,
                             multi_mock['move'].call_args_list)

            self.assertEqual(1, multi_mock['job_from_file'].call_count)
            self.assertEqual(jff_exp_call_args,
                             multi_mock['job_from_file'].call_args)

            self.assertEqual(
                {'count': 1,
                 'args': (
                     (777, temp_dir),
                     {'foreign_calc_id': None,
                      'dbname': 'platform',
                      'callback_url': None})},
                aa_call_data
            )
        finally:
            shutil.rmtree(temp_dir)
