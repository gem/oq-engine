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
                intensity_measure_types_and_levels="{'PGA': [0.1, 0.2]}",
                rupture_mesh_spacing='1.5').validate()
        self.assertEqual(
            w.call_args[0][0],
            "The parameter 'not_existing_param' is unknown, ignoring")

    def test_truncation_level_disaggregation(self):
        # for disaggregation, the truncation level cannot be None
        with self.assertRaises(ValueError):
            OqParam(calculation_mode='disaggregation',
                    hazard_calculation_id=None, hazard_output_id=None,
                    inputs=dict(site_model=''), maximum_distance=10, sites='',
                    intensity_measure_types_and_levels="{'PGA': [0.1, 0.2]}",
                    truncation_level=None).validate()

    def test_geometry(self):
        # you cannot have both region and sites
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical_risk',
                hazard_calculation_id=None, hazard_output_id=None,
                maximum_distance=10,
                region='-78.182 15.615, -78.152 15.615, -78.152 15.565, '
                '-78.182 15.565', sites='0.1 0.2', inputs=dict(site_model='')
            ).validate()

    def test_poes(self):
        # if hazard_maps or uniform_hazard_spectra are set, poes
        # cannot be empty
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical_risk',
                hazard_calculation_id=None, hazard_output_id=None,
                inputs=dict(site_model=''), maximum_distance=10, sites='',
                hazard_maps='true',  poes='').validate()
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical_risk',
                hazard_calculation_id=None, hazard_output_id=None,
                inputs=dict(site_model=''), maximum_distance=10, sites='',
                uniform_hazard_spectra='true',  poes='').validate()

    def test_site_model(self):
        # if the site_model_file is missing, reference_vs30_type and
        # the other site model parameters cannot be None
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical_risk', inputs={},
                maximum_distance=10,
                hazard_calculation_id=None, hazard_output_id=None,
                reference_vs30_type=None).validate()

    def test_missing_maximum_distance(self):
        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical_risk', inputs=dict(site_model=''),
                hazard_calculation_id=None, hazard_output_id=None,
                sites='0.1 0.2').validate()

        with self.assertRaises(ValueError):
            OqParam(
                calculation_mode='classical_risk', inputs=dict(site_model=''),
                hazard_calculation_id=None, hazard_output_id=None,
                sites='0.1 0.2', maximum_distance=0).validate()

    def test_imts_and_imtls(self):
        oq = OqParam(
            calculation_mode='event_based', inputs={},
            intensity_measure_types_and_levels="{'PGA': [0.1, 0.2]}",
            intensity_measure_types='PGV', sites='0.1 0.2',
            maximum_distance=400)
        oq.validate()
        self.assertEqual(oq.imtls.keys(), ['PGA'])

    def test_missing_hazard_curves_from_gmfs(self):
        with self.assertRaises(ValueError) as ctx:
            OqParam(
                calculation_mode='event_based', inputs={},
                intensity_measure_types_and_levels="{'PGA': [0.1, 0.2]}",
                mean_hazard_curves='true', sites='0.1 0.2',
                maximum_distance=400).validate()
        self.assertIn('You must set `hazard_curves_from_gmfs`',
                      str(ctx.exception))

    def test_create_export_dir(self):
        EDIR = os.path.join(TMP, 'nonexisting')
        OqParam(
            calculation_mode='event_based', inputs={},
            sites='0.1 0.2',
            intensity_measure_types='PGA',
            maximum_distance=400,
            export_dir=EDIR,
        ).validate()
        self.assertTrue(os.path.exists(EDIR))

    def test_invalid_export_dir(self):
        with self.assertRaises(ValueError) as ctx:
            OqParam(
                calculation_mode='event_based', inputs={},
                sites='0.1 0.2',
                maximum_distance=400,
                intensity_measure_types='PGA',
                export_dir='/non/existing',
            ).validate()
        self.assertIn('The `export_dir` parameter must refer to a '
                      'directory', str(ctx.exception))

    def test_missing_export_dir(self):
        oq = OqParam(
            calculation_mode='event_based', inputs={},
            sites='0.1 0.2',
            intensity_measure_types='PGA',
            maximum_distance=400)
        oq.validate()
        self.assertEqual(oq.export_dir, os.path.expanduser('~'))

    def test_invalid_imt(self):
        with self.assertRaises(ValueError) as ctx:
            OqParam(
                calculation_mode='event_based', inputs={},
                sites='0.1 0.2',
                maximum_distance=400,
                ground_motion_correlation_model='JB2009',
                intensity_measure_types_and_levels='{"PGV": [0.4, 0.5, 0.6]}',
            ).validate()
        self.assertEqual(
            str(ctx.exception),
            'Correlation model JB2009 does not accept IMT=PGV')

    def test_duplicated_levels(self):
        with self.assertRaises(ValueError) as ctx:
            OqParam(
                calculation_mode='classical', inputs={},
                sites='0.1 0.2',
                reference_vs30_type='measured',
                reference_vs30_value=200,
                reference_depth_to_2pt5km_per_sec=100,
                reference_depth_to_1pt0km_per_sec=150,
                maximum_distance=400,
                intensity_measure_types_and_levels='{"PGA": [0.4, 0.4, 0.6]}',
            ).validate()
        self.assertEqual(
            str(ctx.exception),
            'Found duplicated levels for PGA: [0.4, 0.4, 0.6]: could not '
            'convert to intensity_measure_types_and_levels: '
            'intensity_measure_types_and_levels={"PGA": [0.4, 0.4, 0.6]}')

    def test_missing_levels_hazard(self):
        with self.assertRaises(ValueError) as ctx:
            OqParam(
                calculation_mode='classical', inputs={},
                sites='0.1 0.2',
                maximum_distance=400,
                intensity_measure_types='PGA',
            ).validate()
        self.assertIn('`intensity_measure_types_and_levels`',
                      str(ctx.exception))

    def test_missing_levels_event_based(self):
        with self.assertRaises(ValueError) as ctx:
            OqParam(
                calculation_mode='event_based', inputs={},
                sites='0.1 0.2',
                maximum_distance=400,
                intensity_measure_types='PGA',
                hazard_curves_from_gmfs='true',
            ).validate()
        self.assertIn('`intensity_measure_types_and_levels`',
                      str(ctx.exception))

    def test_ambiguous_gsim(self):
        with self.assertRaises(ValueError) as ctx:
            OqParam(
                calculation_mode='scenario', inputs={
                    'gsim_logic_tree': 'something'},
                gsim='AbrahamsonEtAl2014',
                sites='0.1 0.2',
                maximum_distance=400,
                intensity_measure_types='PGA',
            ).validate()
        self.assertIn('there must be no `gsim` key', str(ctx.exception))
