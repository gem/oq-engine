from openquake.hazardlib.contexts import read_cmakers, read_ctx_by_grp
from openquake.commonlib.datastore import read

dstore = read(-1)  # first run case_1
cmakers = read_cmakers(dstore)

for grp_id, ctx in read_ctx_by_grp(dstore).items():
    print(grp_id, len(ctx), cmakers[grp_id].get_pmap([ctx]))
