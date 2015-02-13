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
from qa_tests import _utils as qa_utils
from qa_tests.hazard.event_based import sc_utils
from openquake.qa_tests_data.event_based import (
    blocksize, case_1, case_2, case_4, case_5, case_6, case_12, case_13,
    case_17)
from openquake.qa_tests_data.event_based.spatial_correlation import (
    case_1 as sc1, case_2 as sc2, case_3 as sc3)

from openquake.commonlib.writers import scientificformat

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
        'col=00|ses=0001|src=1-296|rup=002-01',
        'col=00|ses=0001|src=2-231|rup=002-01',
        'col=00|ses=0001|src=2-40|rup=001-01',
        'col=00|ses=0001|src=24-72|rup=002-01']

    expected_gmfs = '''\
GMFsPerSES(investigation_time=5.000000, stochastic_event_set_id=1,
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=col=00|ses=0001|src=1-296|rup=002-01
<X=131.00000, Y= 40.00000, GMV=0.0152418>
<X=131.00000, Y= 40.10000, GMV=0.0101317>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=col=00|ses=0001|src=2-231|rup=002-01
<X=131.00000, Y= 40.00000, GMV=0.0017037>
<X=131.00000, Y= 40.10000, GMV=0.0018199>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=col=00|ses=0001|src=2-40|rup=001-01
<X=131.00000, Y= 40.00000, GMV=0.0004525>
<X=131.00000, Y= 40.10000, GMV=0.0000602>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=col=00|ses=0001|src=24-72|rup=002-01
<X=131.00000, Y= 40.00000, GMV=0.0011126>
<X=131.00000, Y= 40.10000, GMV=0.0006756>))'''
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
        expected_curve_poes = [0.4596, 0.05729, 0.01193]

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
        expected_curve_poes = [0.0085348, 0., 0., 0.]

        job = self.run_hazard(cfg)

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

# see the docstring in the test package for more info
EXPECTED_GMFS = [
    ('*_b2_1_*_*', '8.5526E-04 2.2252E-03 2.6027E-03 2.6323E-03 3.5311E-03 3.8909E-03 6.5216E-03 1.6441E-02 2.4064E-02 2.4824E-02 3.0388E-02 4.1106E-02 4.4205E-02 1.6736E-01'),
    ('*_b2_2_*_*', '3.6630E-04 7.2146E-04 9.0327E-04 1.1236E-03 1.2992E-03 1.5111E-03 3.0201E-03 9.7407E-03 1.0662E-02 1.4750E-02 1.6862E-02 2.8004E-02 4.2474E-02 1.9598E-01'),
    ('*_b2_3_*_*', '6.5318E-04 1.9370E-03 2.2189E-03 2.3965E-03 3.0831E-03 3.3025E-03 6.4507E-03 1.5176E-02 2.3726E-02 2.4064E-02 3.2772E-02 3.4458E-02 3.5513E-02 1.2917E-01'),
    ('*_b2_4_*_*', '1.7654E-03 2.9733E-03 3.5309E-03 3.5506E-03 4.8153E-03 5.4332E-03 8.7564E-03 2.3742E-02 2.4962E-02 3.3978E-02 3.7184E-02 6.2524E-02 9.5075E-02 3.8498E-01'),
    ('*_b2_5_*_*', '1.7318E-03 2.8662E-03 3.5210E-03 4.0793E-03 4.3884E-03 5.2238E-03 9.9567E-03 2.3962E-02 3.8131E-02 3.8779E-02 5.4894E-02 5.6851E-02 1.0871E-01 4.2594E-01'),
    ('*_*_*_b4_1', '3.7618E-03 7.6974E-03')]


class EventBasedHazardCase5TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        cfg = os.path.join(os.path.dirname(case_5.__file__), 'job.ini')
        job = self.run_hazard(cfg)
        cursor = models.getcursor('job_init')
        cursor.execute(GET_GMF_OUTPUTS % job.id)
        actual_gmfs = [('_'.join(k), scientificformat(sorted(v), '%8.4E'))
                       for k, v in cursor.fetchall()]
        self.assertEqual(len(actual_gmfs), len(EXPECTED_GMFS))
        for (actual_path, actual_gmf), (expected_path, expected_gmf) in zip(
                actual_gmfs, EXPECTED_GMFS):
            self.assertEqual(actual_path, expected_path)
            self.assertEqual(actual_gmf, expected_gmf)


# a test for the case ground_motion_fields=false, hazard_curves_from_gmvs=true
class EventBasedHazardCase6TestCase(qa_utils.BaseQATestCase):

    @attr('qa', 'hazard', 'event_based')
    def test(self):
        expected_mean_poes = [0.967179166906, 0.941377183559, 0.90128199551,
                              0.851388130568, 0.792993661773]

        expected_q0_1_poes = [0.859337648936, 0.764599653662, 0.648572338491,
                              0.522990178604, 0.408798695783]

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
        expected_curve_poes = [0.73657853, 0.07477126, 0.01079842]

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
        expected_curve_poes = [5.4406271E-01, 2.1564097E-02, 5.99820040E-04]

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
        expected_curves_pga = [[1.0, 1.0, 0.0]]

        job = self.run_hazard(cfg)
        j = job.id
        tags = models.SESRupture.objects.filter(
            rupture__ses_collection__trt_model__lt_model__hazard_calculation=j
        ).values_list('tag', flat=True)

        t1_tags = [t for t in tags if t.startswith('col=01')]
        t2_tags = [t for t in tags if t.startswith('col=02')]
        t3_tags = [t for t in tags if t.startswith('col=03')]
        t4_tags = [t for t in tags if t.startswith('col=04')]
        t5_tags = [t for t in tags if t.startswith('col=05')]

        self.assertEqual(len(t1_tags), 2761)
        self.assertEqual(len(t2_tags), 2724)
        self.assertEqual(len(t3_tags), 2735)
        self.assertEqual(len(t4_tags), 2725)
        self.assertEqual(len(t5_tags), 0)

        curves = [c.poes for c in models.HazardCurveData.objects.filter(
            hazard_curve__output__oq_job=job.id, hazard_curve__imt='PGA'
        ).order_by('hazard_curve')]
        numpy.testing.assert_array_almost_equal(
            expected_curves_pga, curves, decimal=7)
