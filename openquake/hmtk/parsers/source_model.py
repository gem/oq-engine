def nrmlSourceModelParser(*args):
    raise Exception('''\
The nrmlSourceModelParser is no more. The right way to parse a source model
is as in the following example:

from openquake.hazardlib import nrml
from openquake.hazardlib.sourceconverter import SourceConverter
conv = SourceConverter(
    investigation_time=50., rupture_mesh_spacing=5.,
    complex_fault_mesh_spacing=10., width_of_mfd_bin=1.,
    area_source_discretization=10.)
source_groups = nrml.parse(fname, conv)
''')
