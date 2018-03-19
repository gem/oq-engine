import os
import tempfile
import unittest
from openquake.hazardlib import nrml
from openquake.engine.tools.correct_complex_sources import fix


class CorrectComplexSourceTestCase(unittest.TestCase):
    def test(self):
        fname = os.path.join(os.path.dirname(__file__),
                             'faults_backg_source_model.xml')
        # check that the input file requires the fix indeed
        with self.assertRaises(ValueError):
            nrml.to_python(fname)
        fd, tmpname = tempfile.mkstemp(suffix='.xml')
        os.close(fd)
        fix(fname, tmpname)  # invoke the fix
        print('meld %s %s' % (fname, tmpname))
