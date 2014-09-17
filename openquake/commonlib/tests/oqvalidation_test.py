import mock
import unittest
from openquake.commonlib.oqvalidation import OqParam


class OqParamTestCase(unittest.TestCase):

    def test_unknown_parameter(self):
        # if the job.ini file contains an unknown parameter, print a warning
        with mock.patch('logging.warn') as w:
            OqParam(
                calculation_mode='classical', inputs=dict(site_model=''),
                hazard_calculation_id=None, hazard_output_id=None,
                sites='0.1 0.2', not_existing_param='XXX')
        self.assertEqual(
            w.call_args[0][0],
            "The parameter 'not_existing_param' is unknown, ignoring")

    def test_truncation_level_disaggregation(self):
        # for disaggregation, the truncation level cannot be None
        with self.assertRaises(ValueError):
            OqParam(calculation_mode='disaggregation',
                    hazard_calculation_id=None, hazard_output_id=None,
                    inputs=dict(site_model=''), sites='',
                    truncation_level=None)

    def test_geometry(self):
        # you cannot have both region and sites
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical',
                hazard_calculation_id=None, hazard_output_id=None,
                region='-78.182 15.615, -78.152 15.615, -78.152 15.565, '
                '-78.182 15.565', sites='0.1 0.2', inputs=dict(site_model=''))

    def test_poes(self):
        # if hazard_maps or uniform_hazard_spectra are set, poes
        # cannot be empty
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical',
                hazard_calculation_id=None, hazard_output_id=None,
                inputs=dict(site_model=''), sites='',
                hazard_maps='true',  poes='')
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical',
                hazard_calculation_id=None, hazard_output_id=None,
                inputs=dict(site_model=''), sites='',
                uniform_hazard_spectra='true',  poes='')

    def test_site_model(self):
        # if the site_model_file is missing, reference_vs30_type and
        # the other site model parameters cannot be None
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical', inputs={},
                hazard_calculation_id=None, hazard_output_id=None,
                reference_vs30_type=None)
