import os
import pandas
from openquake.baselib import sap
from openquake.hazardlib.geo.utils import geolocate
from openquake.risklib.countries import REGIONS, country2code
from openquake.hazardlib.geo.spatial_index import get_mosaic_spatial_index

MODELS = sorted('''
ALS AUS CEA EUR HAW KOR NEA PHL ARB IDN MEX NWA PNG SAM TWN
CND CHN IND MIE NZL SEA USA ZAF CCA JPN NAF PAC SSA WAF GLD
OAT OPA'''.split())

TOML = '''\
[workflow]
description = "Building SES"
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
    lst.append('')


def get_aelo_sites(site_file):
    sites_df = pandas.read_csv(site_file)  # header ID,Latitude,Longitude
    lonlats = sites_df[['Longitude', 'Latitude']].to_numpy()
    mosaic_spatial_index = get_mosaic_spatial_index()
    sites_df['model'] = geolocate(lonlats, mosaic_spatial_index)
    sites = {}
    siteid = {}
    for model, df in sites_df.groupby('model'):
        sites[model] = ', '.join(
            f'{lon:.5f} {lat:.5f}'
            for lon, lat in zip(df.Longitude, df.Latitude))
        siteid[model] = ', '.join(map(str, df.ID))
    return sites, siteid


def aelo(mosaic_dir):
    "Build AELO.toml"
    site_file = os.path.join(mosaic_dir, 'merged_sites.csv')
    assert os.path.exists(site_file), site_file
    sites, siteid = get_aelo_sites(site_file)
    lst = ['[workflow]\ndescription="AELO"']
    models = [mod for mod in MODELS if mod not in {'USA', 'ALS', 'HAW'}]
    add_checkout(lst, models)
    for mod in models:
        if mod == 'CND':
            mod = 'CAN'
        elif mod in ('GLD', 'OAT', 'OPA'):
            continue
        lst.append(f'[{mod}]\nini = "{mod}/in/job_vs30.ini"')
        lst.append(f'sites = "{sites[mod]}"')
        lst.append(f'siteid = "{siteid[mod]}"')
    return save(mosaic_dir, 'AELO.toml', '\n'.join(lst))


def ghm(mosaic_dir, legacy=False):
    "Build GHM.toml"
    lst = ['[workflow]\ndescription="GHM"']
    add_checkout(lst, MODELS)
    for mod in MODELS:
        if legacy:  # to support unzipped_mosaic_run
            if mod == 'CND':
                mod = 'CAN'
            elif mod in 'GLD OAT OPA':
                continue
        lst.append(f'[{mod}]\nini = "{mod}/in/job_vs30.ini"')
        if legacy and mod == 'ARB':
            # speedup slow sources
            lst.append('area_source_discretization = 50')

    lst.append('\n[success]')
    lst.append('func = "openquake.engine.postjobs.import_outputs"')
    lst.append('out_types = ["hcurves", "hmaps-stats"]')
    return save(mosaic_dir, 'GHM.toml', '\n'.join(lst))


def grm(mosaic_dir, number_of_logic_tree_samples: int=2000,
        ses_per_logic_tree_path: int=50):
    "Build GRM.toml"
    haz = ['[multi.workflow]\ndescription="GRM"']
    haz.append(f'{number_of_logic_tree_samples=}')
    haz.append(f'{ses_per_logic_tree_path=}')
    add_checkout(haz, MODELS + REGIONS + ['Exposure', 'Vulnerability'])
    risk = []
    num_countries = 0
    for region in REGIONS:
        jobs_dir = os.path.join(mosaic_dir, region, 'Jobs')
        for fname in os.listdir(jobs_dir):
            # find job_XXX.ini files
            if fname.endswith('.ini') and 'optimized' not in fname:
                country = fname[4:-4]
                if len(country) == 3:
                    # mosaic model
                    if country in MODELS:
                        haz.append(f'[{region}.{country}]')
                        haz.append(f'ini = "{region}/Jobs/{fname}"')
                        if country in ('JPN', 'KOR'):
                            # here the investigation_time is 50
                            haz.append('ses_per_logic_tree_path = 1')
                else:
                    risk.append(f'[risk.{country2code[country]}]')
                    risk.append(f'ini = "{region}/Jobs/{fname}"')
                    risk.append(f'hazard_calculation_id = "{region}.hdf5"')
                    num_countries += 1
        haz.append(f'\n[{region}.success]')
        haz.append('func = "openquake.engine.postjobs.build_ses"')
        haz.append(f'out_file = "{region}.hdf5"')
        haz.append('')
        risk.append('')
    risk.append('\n[success]')
    risk.append('func = "openquake.engine.postjobs.import_outputs"')
    risk.append('out_types = ["aggexp_tags", "aggrisk", '
                '"avg_losses_by", "aggcurves"]')
    print(f'Found {num_countries=}')
    return save(mosaic_dir, 'GRM.toml', '\n'.join(haz + risk))


def ses(mosaic_dir, out='global_ses.hdf5', models=['ALL'],
        number_of_logic_tree_samples:int=2000,
        ses_per_logic_tree_path:int=50, minimum_magnitude:float=5):
    "Build SES.toml"
    lst = []
    if models == ['ALL']:
        models = MODELS
    for model in models:
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
