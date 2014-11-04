import os
import unittest

from openquake.engine.tools.import_hazard_curves import import_hazard_curves
from openquake.commonlib import nrml_examples
from openquake.engine.db.models import HazardCurve, HazardCurveData


class ImportHazardCurvesTestCase(unittest.TestCase):

    def test_import_hazard_curves_pga(self):
        repodir = os.path.dirname(nrml_examples.__file__)
        fileobj = open(os.path.join(repodir, 'hazard-curves-pga.xml'))
        out = import_hazard_curves(fileobj)
        [hc] = HazardCurve.objects.filter(output=out)
        data = HazardCurveData.objects.filter(hazard_curve=hc)
        self.assertEqual(len(data), 2)  # 2 rows entered
        self.assertEqual(out.oq_job.get_param('description'),
                         'HazardCurve importer, file hazard-curves-pga.xml')

    def test_import_hazard_curves_sa(self):
        repodir = os.path.dirname(nrml_examples.__file__)
        fileobj = open(os.path.join(repodir, 'hazard-curves-sa.xml'))
        out = import_hazard_curves(fileobj)
        [hc] = HazardCurve.objects.filter(output=out)
        data = HazardCurveData.objects.filter(hazard_curve=hc)
        self.assertEqual(len(data), 2)  # 2 rows entered
        self.assertEqual(out.oq_job.get_param('description'),
                         'HazardCurve importer, file hazard-curves-sa.xml')
