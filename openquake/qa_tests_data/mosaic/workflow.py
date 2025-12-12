import os
from openquake.baselib import sap
from openquake.risklib.countries import REGIONS, country2code

MODELS = sorted('''
ALS AUS CEA EUR HAW KOR NEA PHL ARB IDN MEX NWA PNG SAM TWN
CND CHN IND MIE NZL SEA USA ZAF CCA JPN NAF PAC SSA WAF GLD
OAT OPA'''.split())

TOML = '''\
[workflow]
calculation_mode = "event_based"
ground_motion_fields = false
number_of_logic_tree_samples = {}
ses_per_logic_tree_path = {}
minimum_magnitude = {}

[success]
func = "openquake.engine.postjobs.build_ses"
out_file = "{}"
{}
'''

def save(mosaic_dir, name, toml):
    "Helper function"
    fname = os.path.join(mosaic_dir, name)
    with open(fname, 'w') as f:
        f.write(toml)
    print(f'Saved {fname}')
    return fname


def add_checkout(lst, models):
    for mod in models:
        lst.append(f'checkout.{mod} = "master"')


def aelo(mosaic_dir):
    "Build AELO.toml"
    lst = ['[workflow]']
    models = [mod for mod in MODELS if mod not in {'USA', 'ALS', 'HAW'}]
    add_checkout(lst, models)
    for mod in models:
        lst.append(f'[{mod}]\nini = "{mod}/in/job_vs30.ini"')
    return save(mosaic_dir, 'AELO.toml', '\n'.join(lst))


def ghm(mosaic_dir):
    "Build GHM.toml"
    lst = ['[workflow]']
    add_checkout(lst, MODELS)
    for mod in MODELS:
        lst.append(f'[{mod}]\nini = "{mod}/in/job_vs30.ini"')
    lst.append('[success]')
    lst.append('func = "openquake.mbt.build_map"')
    lst.append('out_file = "global_hazard_map.svg"')
    return save(mosaic_dir, 'GHM.toml', '\n'.join(lst))


def grm(mosaic_dir):
    "Build GRM.toml"
    haz = ['[multi.workflow]']
    add_checkout(haz, MODELS)
    risk = []
    add_checkout(risk, REGIONS + ['Exposure', 'Vulnerability'])
    num_countries = 0
    for region in REGIONS:
        jobs_dir = os.path.join(mosaic_dir, region, 'Jobs')
        for fname in os.listdir(jobs_dir):
            # find job_XXX.ini files
            if fname.endswith('.ini') and not 'optimized' in fname:
                country = fname[4:-4]
                if len(country) == 3:
                    # mosaic model
                    if country in MODELS:
                        haz.append(f'[{region}.{country}]')
                        haz.append(f'ini = "{region}/Jobs/{fname}"')
                else:
                    risk.append(f'[.{country2code[country]}]')
                    risk.append(f'ini = "{region}/Jobs/{fname}"')
                    risk.append(f'hazard_calculation_id = "{region}.hdf5"')
                    num_countries += 1
        haz.append(f'[{region}.success]')
        haz.append('func = "openquake.engine.postjobs.build_ses"')
        haz.append(f'out_file = "{region}.hdf5"')
        haz.append('')
        risk.append('')
    risk.append('[success]')
    risk.append('func = "openquake.engine.postjobs.import_risk"')
    print(f'Found {num_countries=}')
    return save(mosaic_dir, 'GRM.toml', '\n'.join(haz + risk))


def ses(mosaic_dir, out='global_ses.hdf5',
        number_of_logic_tree_samples:int=2000,
        ses_per_logic_tree_path:int=50, minimum_magnitude:float=5):
    "Build SES.toml"
    lst = []
    for model in MODELS:
        ini = os.path.join(mosaic_dir, model, 'in', 'job_vs30.ini')
        if os.path.exists(ini):
            lst.append(f'\n[{model}]')
            lst.append(f'ini = "{model}/in/job_vs30.ini"')
            if model in ("JPN", "KOR"):
                # these models have an investigation time of 50, not 1 year
                s = ses_per_logic_tree_path // 50
                lst.append(f'ses_per_logic_tree_path={s}')
    return save(mosaic_dir, 'SES.toml',
         TOML.format(number_of_logic_tree_samples,
                     ses_per_logic_tree_path,
                     minimum_magnitude,
                     out, '\n'.join(lst)))

main = dict(AELO=aelo, GHM=ghm, GRM=grm, SES=ses)
    
if __name__ == '__main__':
    sap.run(main)
