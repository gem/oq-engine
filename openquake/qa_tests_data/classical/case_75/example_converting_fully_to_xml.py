from openquake.hazardlib import sourcewriter
from openquake.hazardlib import nrml
from openquake.hazardlib.sourceconverter import SourceConverter
conv = SourceConverter(50., 1., 20, 0.1, 10.)
smodel = nrml.to_python('ruptures_0.xml', conv)
written = sourcewriter.write_source_model(
    'converted.xml', smodel, to_hdf5=False)
print(written)
