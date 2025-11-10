import django
from datetime import datetime, timedelta
from django.test import Client
from openquake.commonlib.dbapi import db
from openquake.engine.engine import create_jobs
from openquake.server.tests.views_test import get_or_create_user


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

    def test_calc_list(self):
        """
        Create jobs with different parameters and test that /v1/calc/list
        applies filtering, ACLs, pagination, and ordering correctly.
        """
        job_defs = [
            dict(calculation_mode='event_based', description='calc_user2_complete'),
            dict(calculation_mode='classical', description='calc_user2_running'),
            dict(calculation_mode='scenario', description='calc_user1_complete'),
            dict(calculation_mode='classical', description='calc_user1_shared'),
        ]
        [job1, job2] = create_jobs(job_defs[:2], user_name=self.user2.username)
        [job3, job4] = create_jobs(job_defs[2:], user_name=self.user1.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, job1.calc_id)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'running', 'is_running': 1}, job2.calc_id)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, job3.calc_id)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'shared', 'is_running': 0}, job4.calc_id)

        self.c.login(username=self.user2.username, password=self.password2)

        ret = self.get('list', limit=-1)
        self.assertEqual(ret.status_code, 200)
        all_jobs = ret.json()
        job_ids = {j['id'] for j in all_jobs}
        self.assertIn(job1.calc_id, job_ids)
        self.assertIn(job2.calc_id, job_ids)
        self.assertNotIn(job3.calc_id, job_ids)  # owned by user1
        self.assertIn(job4.calc_id, job_ids)  # shared, even if ACL is off by default

        ret = self.get('list', calculation_mode='classical', include_shared=0)
        self.assertEqual(ret.status_code, 200)
        modes = {j['calculation_mode'] for j in ret.json()}
        self.assertEqual(modes, {'classical'})

        ret = self.get('list', is_running='1', include_shared=0)
        self.assertEqual(ret.status_code, 200)
        self.assertTrue(all(j['is_running'] for j in ret.json()))

        ret = self.get('list', user_name_like='user2', include_shared=0)
        self.assertEqual(ret.status_code, 200)
        self.assertTrue(all('user2' in j['user_name'] for j in ret.json()))

        self.c.login(username=self.user1.username, password=self.password1)
        ret = self.get('list', include_shared='1')
        shared_ids = {j['id'] for j in ret.json()}
        self.assertIn(job4.calc_id, shared_ids)

        self.c.login(username=self.user2.username, password=self.password2)
        ret_all = self.get('list', limit=10)
        all_ids = [j['id'] for j in ret_all.json()]
        self.assertGreaterEqual(len(all_ids), 2)

        ret_page1 = self.get('list', limit=1, offset=0)
        ret_page2 = self.get('list', limit=1, offset=1)
        self.assertEqual(ret_page1.status_code, 200)
        self.assertEqual(ret_page2.status_code, 200)
        page1_id = ret_page1.json()[0]['id']
        page2_id = ret_page2.json()[0]['id']
        self.assertNotEqual(page1_id, page2_id)

        ret_desc = self.get('list', limit=-1, order_by='id', order_dir='DESC')
        ret_asc = self.get('list', limit=-1, order_by='id', order_dir='ASC')
        ids_desc = [j['id'] for j in ret_desc.json()]
        ids_asc = [j['id'] for j in ret_asc.json()]
        self.assertEqual(ids_desc, list(reversed(ids_asc)))

        self.c.login(username=self.user2.username, password=self.password2)
        for job in [job1, job2]:
            self.remove_calc(job.calc_id)
        self.c.login(username=self.user1.username, password=self.password1)
        for job in [job3, job4]:
            self.remove_calc(job.calc_id)

    def test_calc_list_start_time_filter(self):
        """
        Verify that the start_time filter (?x) correctly returns only jobs
        created after a given ISO timestamp.
        """
        job_defs = [
            dict(calculation_mode='event_based', description='older_job'),
            dict(calculation_mode='classical', description='newer_job'),
        ]
        [older_job] = create_jobs([job_defs[0]], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, older_job.calc_id)
        [newer_job] = create_jobs([job_defs[1]], user_name=self.user2.username)
        db("UPDATE job SET ?D WHERE id=?x",
           {'status': 'complete', 'is_running': 0}, newer_job.calc_id)
        rows = db("SELECT id, start_time FROM job WHERE id IN (?X)",
                  [older_job.calc_id, newer_job.calc_id])

        # change the older timestamp to be one day older
        times = {r.id: r.start_time for r in rows}
        newer_ts = times[newer_job.calc_id]
        older_start_time = (datetime.utcnow() - timedelta(days=1)).isoformat()
        db("UPDATE job SET start_time=?x WHERE id=?x",
           older_start_time, older_job.calc_id)

        self.c.login(username=self.user2.username, password=self.password2)

        # without filtering by start time, the list should include both
        ret_all = self.get('list', include_shared='0')
        self.assertEqual(ret_all.status_code, 200)
        ids_all = {j['id'] for j in ret_all.json()}
        self.assertIn(older_job.calc_id, ids_all)
        self.assertIn(newer_job.calc_id, ids_all)

        # filtering by start time, the list should include only the newer job
        filter_date = newer_ts.date().isoformat()
        ret = self.get('list', start_time=filter_date)
        self.assertEqual(ret.status_code, 200)
        filtered_jobs = ret.json()
        ids_filtered = {j['id'] for j in filtered_jobs}
        self.assertIn(newer_job.calc_id, ids_filtered)
        self.assertNotIn(older_job.calc_id, ids_filtered)

        for job in [older_job, newer_job]:
            self.remove_calc(job.calc_id)
