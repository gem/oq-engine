import os
from nose.tools import assert_equal

from openquake.engine.tools.import_hazard_curves import import_hazard_curves
from openquake import nrmllib
from openquake.engine.db.models import HazardCurve, HazardCurveData


# this is testing that the import does not break, to save us from
# changes in the schema
def test_import_hazard_curves():
    repodir = os.path.dirname(os.path.dirname(nrmllib.__path__[0]))
    fileobj = open(os.path.join(repodir, 'examples', 'hazard-curves-pga.xml'))
    out = import_hazard_curves(fileobj, 'openquake')
    [hc] = HazardCurve.objects.filter(output=out)
    data = HazardCurveData.objects.filter(hazard_curve=hc)
    assert_equal(len(data), 2)  # 2 rows entered
