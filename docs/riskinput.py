import sys
from openquake.commonlib import readinput
from openquake.commonlib.calculators.calc import calc_gmfs

if __name__ == '__main__':
    job_ini = sys.argv[1:]
    o = readinput.get_oqparam(job_ini)
    exposure = readinput.get_exposure(o)
    sitecol, assets_by_site = readinput.get_sitecol_assets(o, exposure)
    risk_model = readinput.get_risk_model(o)
    gmfs_by_imt = calc_gmfs(o, sitecol)

    for imt in gmfs_by_imt:
        ri = risk_model.build_input(imt, gmfs_by_imt[imt], assets_by_site)
        print ri
        for out in risk_model.gen_outputs([ri]):
            import pdb; pdb.set_trace()
