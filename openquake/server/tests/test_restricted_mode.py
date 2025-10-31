import django
from django.test import Client
from openquake.commonlib import logs
from openquake.commonlib.dbapi import db
from openquake.engine.engine import create_jobs
from openquake.server.tests.views_test import get_or_create_user, random_string


class RestrictedModeTestCase(django.test.TestCase):

    @classmethod
    def post(cls, path, data=None):
        return cls.c.post('/v1/calc/%s' % path, data)

    @classmethod
    def get(cls, path, **data):
        return cls.c.get('/v1/calc/%s' % path, data,
                         HTTP_HOST='127.0.0.1')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user0, cls.password0 = get_or_create_user(0)  # level 0
        cls.user1, cls.password1 = get_or_create_user(1)  # level 1
        cls.user2, cls.password2 = get_or_create_user(2)  # level 2
        cls.c = Client()

    @classmethod
    def tearDownClass(cls):
        cls.user0.delete()
        cls.user1.delete()
        cls.user2.delete()
        super().tearDownClass()

    def remove_calc(self, calc_id):
        ret = self.post('%s/remove' % calc_id)
        if ret.status_code != 200:
            raise RuntimeError(
                'Unable to remove job %s:\n%s' % (calc_id, ret))

    def test_share_complete_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_share_complete_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.json(),
                         {'success': f'The status of calculation {job.calc_id} was'
                                     f' changed from "complete" to "shared"'})
        self.remove_calc(job.calc_id)

    def test_share_incomplete_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_share_incomplete_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'created', 'is_running': 1}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.json(),
                         {'error': f'Can not share calculation {job.calc_id} from'
                                   f' status "created"'})
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'failed', 'is_running': 0}, job.calc_id)
        self.remove_calc(job.calc_id)

    def test_share_shared_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_share_shared_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'shared', 'is_running': 0}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.json(),
                         {'success': f'Calculation {job.calc_id} was already shared'})
        self.remove_calc(job.calc_id)

    def test_unshare_complete_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_unshare_complete_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.json(),
                         {'success': f'Calculation {job.calc_id} was already complete'})
        self.remove_calc(job.calc_id)

    def test_unshare_incomplete_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_unshare_incomplete_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'created', 'is_running': 1}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.json(),
                         {'error': f'Can not force the status of calculation'
                                   f' {job.calc_id} from "created" to "complete"'})
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'failed', 'is_running': 0}, job.calc_id)
        self.remove_calc(job.calc_id)

    def test_unshare_shared_job(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_unshare_job')
        [job] = create_jobs([job_dic], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'shared', 'is_running': 0}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.json(),
                         {'success': f'The status of calculation {job.calc_id} was'
                                     f' changed from "shared" to "complete"'})
        self.remove_calc(job.calc_id)

    def test_share_or_unshare_user_level_below_2(self):
        job_dic = dict(calculation_mode='event_based',
                       description='test_unshare_job_levels_below_2')
        [job] = create_jobs([job_dic], user_name=self.user1.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, job.calc_id)

        self.c.login(username=self.user1.username, password=self.password1)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.status_code, 403)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.status_code, 403)

        self.c.login(username=self.user0.username, password=self.password0)
        ret = self.post(f'{job.calc_id}/share')
        self.assertEqual(ret.status_code, 403)
        ret = self.post(f'{job.calc_id}/unshare')
        self.assertEqual(ret.status_code, 403)

        self.c.login(username=self.user1.username, password=self.password1)
        self.remove_calc(job.calc_id)

    # TEST TAGGING
    def test_tagging_job(self):
        job_dic0 = dict(calculation_mode='event_based',
                        description='test_tagging_first_job')
        job_dic1 = dict(calculation_mode='event_based',
                        description='test_tagging_second_job')
        jobs = create_jobs([job_dic0, job_dic1], user_name=self.user2.username)
        for job in jobs:
            db("UPDATE job SET ?D WHERE id=?x",
               {'status': 'complete', 'is_running': 0}, job.calc_id)
        self.c.login(username=self.user2.username, password=self.password2)

        # try to add a tag with a blank name
        tag_name = ''
        ret = self.get(f'{jobs[0].calc_id}/add_tag/{tag_name}')
        self.assertEqual(ret.status_code, 404)
        ret = logs.dbcmd('add_tag_to_job', jobs[0].calc_id, tag_name)
        self.assertIn('error', ret)
        self.assertIn("CHECK constraint failed: LENGTH(tag) > 0", ret['error'])

        # generate random tag names, 10 characters long
        first_tag = random_string(10)
        second_tag = random_string(10)
        for job in jobs:
            for tag in [first_tag, second_tag]:
                # add the same tag to the two jobs
                ret = self.get(f'{job.calc_id}/add_tag/{tag}')
                self.assertEqual(ret.status_code, 200)
                self.assertIn(f'The tag {tag} was added to job {job.calc_id}',
                              ret.content.decode('utf8'))
                # set the first job as preferred
                ret = self.get(f'{job.calc_id}/set_preferred_job_for_tag/{tag}')
                self.assertEqual(ret.status_code, 200)
                # when setting the second job as preferred, the preferred flag should
                # be reset for all jobs sharing that tag and the flag should be set to
                # the second job without raising errors
                self.assertIn(f'Job {job.calc_id} was set as preferred for tag {tag}',
                              ret.content.decode('utf8'))

        # list all the available tags
        ret = self.get('list_tags')
        self.assertEqual(ret.status_code, 200)
        self.assertIn(first_tag, ret.json()['tags'])
        self.assertIn(second_tag, ret.json()['tags'])

        # get the preferred job for the tag
        ret = self.get(f'get_preferred_job_for_tag/{first_tag}')
        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.json()['job_id'], jobs[1].calc_id)

        # list all jobs (preferred and not preferred)
        ret = self.get('list')
        self.assertEqual(ret.status_code, 200)
        n_all_jobs = len(ret.json())
        # list only the preferred jobs
        ret = self.get('list?preferred_only=1')
        self.assertEqual(ret.status_code, 200)
        n_preferred_jobs = len(ret.json())
        # NOTE: we might want to check that all the listed jobs are not preferred, but
        # it is a bit more complex, involving a query on job_tag for each
        self.assertGreater(n_all_jobs, n_preferred_jobs)
        # list only jobs that have the first tag
        ret = self.get(f'list?filter_by_tag={first_tag}')
        self.assertEqual(ret.status_code, 200)
        # check that the query is not returning any job that doesn't have the first tag
        returned_jobs = ret.json()
        expected_jobs = [job for job in ret.json() if first_tag in job['tags']]
        self.assertGreater(len(returned_jobs), 0)
        self.assertEqual(len(returned_jobs), len(expected_jobs))

        # unset the preferred job for the first tag
        ret = self.get(f'unset_preferred_job_for_tag/{first_tag}')
        self.assertEqual(ret.status_code, 200)
        self.assertIn('success', ret.json())
        self.assertIn(f'Tag {first_tag} has no preferred job now',
                      ret.json()['success'])

        # try to re-add the same first_tag to the second job
        ret = self.get(f'{jobs[1].calc_id}/add_tag/{first_tag}')
        self.assertEqual(ret.status_code, 403)
        self.assertIn('error', ret.json())
        self.assertIn("UNIQUE constraint failed", ret.json()['error'])

        # remove the first_tag from the second job
        ret = self.get(f'{jobs[1].calc_id}/remove_tag/{first_tag}')
        self.assertEqual(ret.status_code, 200)
        self.assertIn(f'Tag {first_tag} was removed from job {jobs[1].calc_id}',
                      ret.content.decode('utf8'))

        # get the preferred job for the tag
        ret = self.get(f'get_preferred_job_for_tag/{first_tag}')
        self.assertEqual(ret.status_code, 200)
        self.assertIsNone(ret.json()['job_id'])

        # delete the jobs
        for job in jobs:
            self.remove_calc(job.calc_id)
