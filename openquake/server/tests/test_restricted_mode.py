import django
from django.test import Client
from openquake.commonlib.dbapi import db
from openquake.engine.engine import create_jobs
from openquake.server.tests.views_test import get_or_create_user


class ShareJobTestCase(django.test.TestCase):

    @classmethod
    def post(cls, path, data=None):
        return cls.c.post('/v1/calc/%s' % path, data)

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
