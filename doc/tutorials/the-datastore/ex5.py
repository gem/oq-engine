from openquake.hazardlib.contexts import read_cmakers, read_ctx_by_grp
from openquake.hazardlib.stats import combine_probs
from openquake.commonlib.datastore import read

dstore = read(-1)  # first run LogicTreeCase1ClassicalPSHA
N = len(dstore['sitecol/sids'])
cmakers = read_cmakers(dstore)
weights = dstore['weights'][:]
allpoes = []
for grp_id, ctxt in read_ctx_by_grp(dstore).items():
    allpoes.append(cmakers[grp_id].get_pmap([ctxt]).array)
mean = 0
for rlz, weight in enumerate(weights):
    mean += combine_probs(allpoes, cmakers, rlz) * weight
print(mean)
