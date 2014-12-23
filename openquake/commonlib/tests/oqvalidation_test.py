import os
import mock
import unittest
import tempfile
from openquake.commonlib.oqvalidation import OqParam

TMP = tempfile.gettempdir()


class OqParamTestCase(unittest.TestCase):

    def test_unknown_parameter(self):
        # if the job.ini file contains an unknown parameter, print a warning
        with mock.patch('logging.warn') as w:
            OqParam(
                calculation_mode='classical', inputs=dict(site_model=''),
                hazard_calculation_id=None, hazard_output_id=None,
                maximum_distance=10, sites='0.1 0.2',
                not_existing_param='XXX', export_dir=TMP,
                rupture_mesh_spacing='1.5')
        self.assertEqual(
            w.call_args[0][0],
            "The parameter 'not_existing_param' is unknown, ignoring")

    def test_truncation_level_disaggregation(self):
        # for disaggregation, the truncation level cannot be None
        with self.assertRaises(ValueError):
            OqParam(calculation_mode='disaggregation',
                    hazard_calculation_id=None, hazard_output_id=None,
                    inputs=dict(site_model=''), maximum_distance=10, sites='',
                    truncation_level=None)

    def test_geometry(self):
        # you cannot have both region and sites
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical',
                hazard_calculation_id=None, hazard_output_id=None,
                maximum_distance=10,
                region='-78.182 15.615, -78.152 15.615, -78.152 15.565, '
                '-78.182 15.565', sites='0.1 0.2', inputs=dict(site_model=''))

    def test_poes(self):
        # if hazard_maps or uniform_hazard_spectra are set, poes
        # cannot be empty
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical',
                hazard_calculation_id=None, hazard_output_id=None,
                inputs=dict(site_model=''), maximum_distance=10, sites='',
                hazard_maps='true',  poes='')
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical',
                hazard_calculation_id=None, hazard_output_id=None,
                inputs=dict(site_model=''), maximum_distance=10, sites='',
                uniform_hazard_spectra='true',  poes='')

    def test_site_model(self):
        # if the site_model_file is missing, reference_vs30_type and
        # the other site model parameters cannot be None
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical', inputs={},
                maximum_distance=10,
                hazard_calculation_id=None, hazard_output_id=None,
                reference_vs30_type=None)

    def test_missing_maximum_distance(self):
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical', inputs=dict(site_model=''),
                hazard_calculation_id=None, hazard_output_id=None,
                sites='0.1 0.2')

        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical', inputs=dict(site_model=''),
                hazard_calculation_id=None, hazard_output_id=None,
                sites='0.1 0.2', maximum_distance=0)

    def test_missing_hazard_curves_from_gmfs(self):
        with self.assertRaises(ValueError) as ctx:
            OqParam(
                calculation_mode='event_based', inputs={},
                mean_hazard_curves='true', sites='0.1 0.2',
                reference_vs30_type='measured',
                reference_vs30_value=200,
                reference_depth_to_2pt5km_per_sec=100,
                reference_depth_to_1pt0km_per_sec=150,
                maximum_distance=400)
        self.assertIn('You must set `hazard_curves_from_gmfs`',
                      str(ctx.exception))

    def test_invalid_export_dir(self):
        with self.assertRaises(ValueError) as ctx:
            OqParam(
                calculation_mode='event_based', inputs={},
                sites='0.1 0.2',
                reference_vs30_type='measured',
                reference_vs30_value=200,
                reference_depth_to_2pt5km_per_sec=100,
                reference_depth_to_1pt0km_per_sec=150,
                maximum_distance=400,
                export_dir='/non/existing',
            )
        self.assertIn('The `export_dir` parameter must refer to a '
                      'directory', str(ctx.exception))

    def test_missing_export_dir(self):
        oq = OqParam(
            calculation_mode='event_based', inputs={},
            sites='0.1 0.2',
            reference_vs30_type='measured',
            reference_vs30_value=200,
            reference_depth_to_2pt5km_per_sec=100,
            reference_depth_to_1pt0km_per_sec=150,
            maximum_distance=400)
        self.assertEqual(oq.export_dir, os.path.expanduser('~'))
