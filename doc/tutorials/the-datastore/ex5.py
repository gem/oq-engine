from openquake.hazardlib.contexts import read_cmakers, get_pmap
from openquake.hazardlib.stats import combine_probs
from openquake.commonlib.datastore import read

dstore = read(-1)  # first run LogicTreeCase1ClassicalPSHA
N = len(dstore['sitecol/sids'])
cmakers = read_cmakers(dstore)
weights = dstore['weights'][:]
allpoes = []
for grp_id, cmaker in enumerate(cmakers):
    ctxs = cmaker.read_ctxs(dstore)
    allpoes.append(get_pmap(ctxs, cmaker).array(N))
mean = 0
for rlz, weight in enumerate(weights):
    mean += combine_probs(allpoes, cmakers, rlz) * weight
print(mean)
