from openquake.hazardlib.contexts import read_cmakers, get_pmap
from openquake.commonlib.datastore import read

dstore = read(-1)  # first run case_1
cmakers = read_cmakers(dstore)
for grp_id, cmaker in enumerate(cmakers):
    ctxs = cmaker.read_ctxs(dstore)
    print(grp_id, len(ctxs), get_pmap(ctxs, cmaker))
