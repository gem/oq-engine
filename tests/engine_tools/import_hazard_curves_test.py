import os
import unittest

from openquake.engine.tools.import_hazard_curves import import_hazard_curves
from openquake import nrmllib
from openquake.engine.db.models import HazardCurve, HazardCurveData


class ImportHazardCurvesTestCase(unittest.TestCase):

    def test_import_hazard_curves_pga(self):
        repodir = os.path.dirname(os.path.dirname(nrmllib.__path__[0]))
        fileobj = open(os.path.join(
                       repodir, 'examples', 'hazard-curves-pga.xml'))
        out = import_hazard_curves(fileobj)
        [hc] = HazardCurve.objects.filter(output=out)
        data = HazardCurveData.objects.filter(hazard_curve=hc)
        self.assertEqual(len(data), 2)  # 2 rows entered
        self.assertEqual(out.oq_job.hazard_calculation.description,
                         'HazardCurve importer, file hazard-curves-pga.xml')

    def test_import_hazard_curves_sa(self):
        repodir = os.path.dirname(os.path.dirname(nrmllib.__path__[0]))
        fileobj = open(os.path.join(
                       repodir, 'examples', 'hazard-curves-sa.xml'))
        out = import_hazard_curves(fileobj)
        [hc] = HazardCurve.objects.filter(output=out)
        data = HazardCurveData.objects.filter(hazard_curve=hc)
        self.assertEqual(len(data), 2)  # 2 rows entered
        self.assertEqual(out.oq_job.hazard_calculation.description,
                         'HazardCurve importer, file hazard-curves-sa.xml')
