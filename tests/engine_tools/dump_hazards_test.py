import os
import unittest

from django.db import connections

from openquake.engine.db.models import Output, OqJob, HazardCalculation
from openquake.engine.tools.dump_hazards import HazardDumper
from openquake.engine.tools.restore_hazards import hazard_restore

from tests.utils import data


class DumperTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        connections['admin'].cursor()  # open a connection
        cls.conn = connections['admin'].connection
        data.import_a_gmf_collection(cls.conn)
        cls.output = Output.objects.latest('id')
        cls.hc = HazardCalculation.objects.create(
            owner_id=1, maximum_distance=100, calculation_mode='event_based')
        cls.output.oq_job = OqJob.objects.create(
            owner_id=1, hazard_calculation=cls.hc)  # fake job
        cls.output.save()

    def test_dump_and_restore(self):
        # dump the GmfCollection generated in setUpClass into a tarfile
        hd = HazardDumper(self.conn)
        hd.dump(self.hc.id)
        tar = hd.mktar()
        curs = self.conn.cursor()
        try:
            # delete the original hazard calculation
            curs.execute('DELETE FROM uiapi.hazard_calculation '
                         'WHERE id=%s', (self.hc.id,))
            # restore the deleted GmfCollection
            hazard_restore(self.conn, tar)
            curs.execute('SELECT 1 FROM uiapi.hazard_calculation WHERE id=%s',
                         (self.hc.id,))
            self.assertEqual(curs.fetchall(), [(1,)])
        finally:
            os.remove(tar)
