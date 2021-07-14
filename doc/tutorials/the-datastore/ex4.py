from openquake.hazardlib.contexts import read_cmakers
from openquake.commonlib.datastore import read

dstore = read(-1)  # first run case_1
cmakers = read_cmakers(dstore)
for grp_id, cmaker in enumerate(cmakers):
    ctxs = cmaker.read_ctxs(dstore)
    print(grp_id, len(ctxs), cmaker.get_pmap(ctxs))
