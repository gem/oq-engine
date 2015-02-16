# Copyright (c) 2010-2014, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import numpy
import os
import shutil
import tempfile

from nose.plugins.attrib import attr
from openquake.engine.db import models
from openquake.engine.utils import config
from openquake.engine.export import core
from qa_tests import _utils as qa_utils
from qa_tests.hazard.event_based import sc_utils
from openquake.qa_tests_data.event_based import (
    blocksize, case_1, case_2, case_4, case_5, case_6, case_12, case_13,
    case_17)
from openquake.qa_tests_data.event_based.spatial_correlation import (
    case_1 as sc1, case_2 as sc2, case_3 as sc3)

aaae = numpy.testing.assert_array_almost_equal


class EventBasedHazardTestCase(qa_utils.BaseQATestCase):
    """
    This is a regression test with the goal of avoiding the reintroduction
    of a dependence from the configuration parameter `concurrent_tasks`.
    We use a source model with 398 sources and a single SES.
    Due to the distance filtering only 7 sources are relevant, but some
    of them are area sources generating a lot of point sources.
    We test the independence from the parameter `concurrent_tasks`
    """
    DEBUG = False
    # if the test fails and you want to debug it, set this flag:
    # then you will see in /tmp a few files which you can diff
    # to see the problem
    expected_tags = [
        'trt=00|ses=0001|src=1-296|rup=002-01',
        'trt=00|ses=0001|src=2-231|rup=002-01',
        'trt=00|ses=0001|src=2-40|rup=001-01',
        'trt=00|ses=0001|src=24-72|rup=002-01',
    ]
    expected_gmfs = '''\
GMFsPerSES(investigation_time=5.000000, stochastic_event_set_id=1,
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=trt=00|ses=0001|src=1-296|rup=002-01
<X=131.00000, Y= 40.00000, GMV=0.0068590>
<X=131.00000, Y= 40.10000, GMV=0.0066422>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=trt=00|ses=0001|src=2-231|rup=002-01
<X=131.00000, Y= 40.00000, GMV=0.0009365>
<X=131.00000, Y= 40.10000, GMV=0.0009827>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=trt=00|ses=0001|src=2-40|rup=001-01
<X=131.00000, Y= 40.00000, GMV=0.0001138>
<X=131.00000, Y= 40.10000, GMV=0.0001653>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=trt=00|ses=0001|src=24-72|rup=002-01
<X=131.00000, Y= 40.00000, GMV=0.0005475>
<X=131.00000, Y= 40.10000, GMV=0.0007085>))'''

    @attr('qa', 'hazard', 'event_based')
    def test_4(self):
        tags_4, gmfs_4 = self.run_with_concurrent_tasks(4)
        self.assertEqual(tags_4, self.expected_tags)
        if self.DEBUG:  # write the output on /tmp so you can diff it
            open('/tmp/4-got.txt', 'w').write(gmfs_4)
            open('/tmp/4-exp.txt', 'w').write(self.expected_gmfs)
        self.assertEqual(gmfs_4, self.expected_gmfs)

    @attr('qa', 'hazard', 'event_based')
    def test_8(self):
        tags_8, gmfs_8 = self.run_with_concurrent_tasks(8)
        self.assertEqual(tags_8, self.expected_tags)
        if self.DEBUG:  # write the output on /tmp so you can diff it
            open('/tmp/8-got.txt', 'w').write(gmfs_8)
            open('/tmp/8-exp.txt', 'w').write(self.expected_gmfs)
        self.assertEqual(gmfs_8, self.expected_gmfs)

    def run_with_concurrent_tasks(self, n):
        with config.context('celery', concurrent_tasks=n):
            cfg = os.path.join(os.path.dirname(blocksize.__file__), 'job.ini')
            job = self.run_hazard(cfg)
            tags = models.SESRupture.objects.filter(
                rupture__ses_collection__output__oq_job=job
                ).values_list('tag', flat=True)
            # gets the GMFs for all the ruptures in the only existing SES
            [gmfs_per_ses] = list(models.Gmf.objects.get(output__oq_job=job))
        return map(str, tags), str(gmfs_per_ses)


class EBHazardSpatialCorrelCase1TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(sc1.__file__), 'job.ini')

        job = self.run_hazard(cfg)
        hc = job.get_oqparam()

        site_1 = 'POINT(0.0 0.0)'
        site_2 = 'POINT(0.008993 0.0)'

        gmvs_site_1 = sc_utils.get_gmvs_for_location(site_1, job)
        gmvs_site_2 = sc_utils.get_gmvs_for_location(site_2, job)

        joint_prob_0_5 = sc_utils.joint_prob_of_occurrence(
            gmvs_site_1, gmvs_site_2, 0.5, hc.investigation_time,
            hc.ses_per_logic_tree_path
        )
        joint_prob_1_0 = sc_utils.joint_prob_of_occurrence(
            gmvs_site_1, gmvs_site_2, 1.0, hc.investigation_time,
            hc.ses_per_logic_tree_path
        )

        numpy.testing.assert_almost_equal(joint_prob_0_5, 0.99, decimal=1)
        numpy.testing.assert_almost_equal(joint_prob_1_0, 0.41, decimal=1)


class EBHazardSpatialCorrelCase2TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(sc2.__file__), 'job.ini')

        job = self.run_hazard(cfg)
        hc = job.get_oqparam()

        site_1 = 'POINT(0.0 0.0)'
        site_2 = 'POINT(0.008993 0.0)'

        gmvs_site_1 = sc_utils.get_gmvs_for_location(site_1, job)
        gmvs_site_2 = sc_utils.get_gmvs_for_location(site_2, job)

        joint_prob_0_5 = sc_utils.joint_prob_of_occurrence(
            gmvs_site_1, gmvs_site_2, 0.5, hc.investigation_time,
            hc.ses_per_logic_tree_path
        )
        joint_prob_1_0 = sc_utils.joint_prob_of_occurrence(
            gmvs_site_1, gmvs_site_2, 1.0, hc.investigation_time,
            hc.ses_per_logic_tree_path
        )

        numpy.testing.assert_almost_equal(joint_prob_0_5, 0.99, decimal=1)
        numpy.testing.assert_almost_equal(joint_prob_1_0, 0.64, decimal=1)


class EBHazardSpatialCorrelCase3TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(sc3.__file__), 'job.ini')

        job = self.run_hazard(cfg)
        hc = job.get_oqparam()

        site_1 = 'POINT(0.0 0.0)'
        site_2 = 'POINT(0.008993 0.0)'

        gmvs_site_1 = sc_utils.get_gmvs_for_location(site_1, job)
        gmvs_site_2 = sc_utils.get_gmvs_for_location(site_2, job)

        joint_prob_0_5 = sc_utils.joint_prob_of_occurrence(
            gmvs_site_1, gmvs_site_2, 0.5, hc.investigation_time,
            hc.ses_per_logic_tree_path
        )
        joint_prob_1_0 = sc_utils.joint_prob_of_occurrence(
            gmvs_site_1, gmvs_site_2, 1.0, hc.investigation_time,
            hc.ses_per_logic_tree_path
        )

        numpy.testing.assert_almost_equal(joint_prob_0_5, 0.95, decimal=1)
        numpy.testing.assert_almost_equal(joint_prob_1_0, 0.22, decimal=1)


class EventBasedHazardCase1TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_1.__file__), 'job.ini')
        expected_curve_poes = [0.4570, 0.0587, 0.0069]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [actual_curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id,
            hazard_curve__imt__isnull=False)

        numpy.testing.assert_array_almost_equal(
            expected_curve_poes, actual_curve.poes, decimal=2)

        shutil.rmtree(result_dir)


class EventBasedHazardCase2TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        result_dir = tempfile.mkdtemp()

        cfg = os.path.join(os.path.dirname(case_2.__file__), 'job.ini')
        expected_gmf = os.path.join(os.path.dirname(case_2.__file__),
                                    'expected', '0-SadighEtAl1997.csv')
        expected_curve_poes = [0.00853479861, 0., 0., 0.]

        job = self.run_hazard(cfg)

        # Test the GMF exported values
        gmf_output = models.Output.objects.get(
            output_type='gmf', oq_job=job)

        fname = core.export(gmf_output.id, result_dir, 'csv')
        gotlines = sorted(open(fname).readlines())
        expected = sorted(open(expected_gmf).readlines())
        self.assertEqual(gotlines, expected)

        # Test the poe values of the single curve:
        [actual_curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id,
            hazard_curve__imt__isnull=False)

        self.assert_equals_var_tolerance(
            expected_curve_poes, actual_curve.poes
        )
        shutil.rmtree(result_dir)


class EventBasedHazardCase4TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_4.__file__), 'job.ini')
        expected_curve_poes = [0.63212, 0.61186, 0.25110]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [actual_curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id,
            hazard_curve__imt__isnull=False)

        # NOTE(LB): The expected/actual results are precise, however Dr.
        # Monelli has intructed use that 1 digits of tolerance in this case
        # still tells us something useful.
        numpy.testing.assert_array_almost_equal(
            expected_curve_poes, actual_curve.poes, decimal=1)


GET_GMF_OUTPUTS = '''
select gsim_lt_path, array_concat(gmvs order by site_id, task_no) as gmf
from hzrdr.gmf_data as a, hzrdr.lt_realization as b, hzrdr.gmf as c
where lt_realization_id=b.id and a.gmf_id=c.id and c.output_id in
(select id from uiapi.output where oq_job_id=%d and output_type='gmf')
group by gsim_lt_path, c.output_id, imt, sa_period, sa_damping
order by c.output_id;
'''

# this is an example with 0 realization for source_model 1
# 5 realizations for source model 2
# (for TRT=Stable Shallow Crust) and 0 realizations
# for source model 3, i.e. a total of 5 realizations
EXPECTED_GMFS = [
    # (gsim_lt_path, gmf) pairs
    (['*', 'b2_1', '*', '*'],
     [0.00822917040699, 0.0034042851599, 0.00428337018622,
      0.0025270726635, 0.00606112335209, 0.0112245743761,
      0.0179907692793, 0.0173946859667, 0.00922980939898,
      0.726593190686, 0.00495477503721, 0.0415099434432,
      0.0125880009831, 0.0124495516475]),
    (['*', 'b2_2', '*', '*'],
        [0.00288537938821, 0.00107995958217, 0.00142877779947,
         0.000724092064875, 0.00221523273814, 0.00783122282702,
         0.00491624227026, 0.00665180766619, 0.00469543848075,
         0.00310630748453, 0.423926958129, 0.022738208891,
         0.00518327577291, 0.00589077454912]),
    (['*', 'b2_3', '*', '*'],
        [0.00795512355585, 0.00305068332773, 0.00386916664508,
         0.00230772046628, 0.00551261356351, 0.0100154584429,
         0.0192898688711, 0.00799975891393, 0.0200084979633,
         0.768238309158, 0.00376526374305, 0.0439684332239,
         0.013332105199, 0.0119999914465]),
    (['*', 'b2_4', '*', '*'],
     [0.0096913860471, 0.00411106304155, 0.00520803315284,
      0.00297152070044, 0.00745986019708, 0.0195767577423,
      0.0151584294161, 0.0156128323892, 0.0173448581516,
      1.0342310621, 0.0101958545893, 0.0478640962161,
      0.0135769826018, 0.0143048207197]),
    (['*', 'b2_5', '*', '*'],
        [0.00929127217018, 0.00405983191645, 0.00494117277395,
         0.00290638690174, 0.0067144964127, 0.0225768116043,
         0.0204078758048, 0.0212867716314, 0.01879161511,
         0.941450341214, 0.00951592753892, 0.0477618047224,
         0.0139189584458, 0.0142090106379]),
    (['*', '*', '*', 'b4_1'], [0.00638234839428, 0.00481213194677])]


class EventBasedHazardCase5TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_5.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        cursor = models.getcursor('job_init')
        cursor.execute(GET_GMF_OUTPUTS % job.id)
        actual_gmfs = cursor.fetchall()
        self.assertEqual(len(actual_gmfs), len(EXPECTED_GMFS))
        for (actual_path, actual_gmf), (expected_path, expected_gmf) in zip(
                actual_gmfs, EXPECTED_GMFS):
            self.assertEqual(actual_path, expected_path)
            self.assertEqual(len(actual_gmf), len(expected_gmf))
            numpy.testing.assert_almost_equal(
                sorted(actual_gmf), sorted(expected_gmf))


# a test for the case ground_motion_fields=false, hazard_curves_from_gmvs=true
class EventBasedHazardCase6TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        expected_mean_poes = [0.962621437215, 0.934650031955, 0.894381466273,
                              0.837844843687, 0.782933836463]

        expected_q0_1_poes = [0.838637792751, 0.749373612177, 0.623662070173,
                              0.496434891584, 0.385987239512]

        job = self.run_hazard(
            os.path.join(os.path.dirname(case_6.__file__), 'job.ini'))

        # mean
        [mean_curve] = models.HazardCurveData.objects \
            .filter(hazard_curve__output__oq_job=job.id,
                    hazard_curve__statistics='mean')
        # print mean_curve.poes
        aaae(expected_mean_poes, mean_curve.poes, decimal=7)

        # quantiles
        [quantile_0_1_curve] = \
            models.HazardCurveData.objects.filter(
                hazard_curve__output__oq_job=job.id,
                hazard_curve__statistics='quantile').order_by(
                'hazard_curve__quantile')
        # print quantile_0_1_curve.poes
        aaae(expected_q0_1_poes, quantile_0_1_curve.poes, decimal=7)


class EventBasedHazardCase12TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        result_dir = tempfile.mkdtemp()
        aaae = numpy.testing.assert_array_almost_equal

        cfg = os.path.join(os.path.dirname(case_12.__file__), 'job.ini')
        expected_curve_poes = [0.75421006, 0.08098179, 0.00686616]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id,
            hazard_curve__imt__isnull=False)

        aaae(expected_curve_poes, curve.poes, decimal=2)

        shutil.rmtree(result_dir)


class EventBasedHazardCase13TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        aaae = numpy.testing.assert_array_almost_equal

        cfg = os.path.join(os.path.dirname(case_13.__file__), 'job.ini')
        expected_curve_poes = [0.54736, 0.02380, 0.00000]

        job = self.run_hazard(cfg)

        # Test the poe values of the single curve:
        [curve] = models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id,
            hazard_curve__imt__isnull=False)

        aaae(expected_curve_poes, curve.poes, decimal=2)


class EventBasedHazardCase17TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_17.__file__), 'job.ini')
        expected_curves_pga = [[1.0, 1.0, 0.0],
                               [1.0, 1.0, 0.0],
                               [0.0, 0.0, 0.0],
                               [1.0, 1.0, 0.0],
                               [1.0, 1.0, 0.0]]

        job = self.run_hazard(cfg)
        j = job.id
        tags = models.SESRupture.objects.filter(
            rupture__ses_collection__trt_model__lt_model__hazard_calculation=j
        ).values_list('tag', flat=True)

        t1_tags = [t for t in tags if t.startswith('trt=00')]
        t2_tags = [t for t in tags if t.startswith('trt=01')]
        t3_tags = [t for t in tags if t.startswith('trt=02')]
        t4_tags = [t for t in tags if t.startswith('trt=03')]
        t5_tags = [t for t in tags if t.startswith('trt=04')]

        self.assertEqual(len(t1_tags), 2742)
        self.assertEqual(len(t2_tags), 2761)
        self.assertEqual(len(t3_tags), 1)
        self.assertEqual(len(t4_tags), 2735)
        self.assertEqual(len(t5_tags), 2725)

        curves = [c.poes for c in models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id, hazard_curve__imt='PGA'
        ).order_by('hazard_curve')]
        numpy.testing.assert_array_almost_equal(
            expected_curves_pga, curves, decimal=7)
