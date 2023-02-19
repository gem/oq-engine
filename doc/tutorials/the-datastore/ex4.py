from openquake.hazardlib.contexts import read_cmakers
from openquake.commonlib.datastore import read

dstore = read(-1)  # first run case_1
cmakers = read_cmakers(dstore)
for grp_id, cmaker in enumerate(cmakers):
    ctxt = cmaker.read_ctxt(dstore)
    print(grp_id, len(ctxt), cmaker.get_pmap([ctxt]))
