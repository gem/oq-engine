#!/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2023, GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import csv
import os
import logging
import pandas
import numpy
import h5py
from openquake.baselib import sap, general, performance, hdf5
from openquake.hazardlib import nrml, gsim_lt, site
from openquake.risklib.riskmodels import CompositeRiskModel, RiskFuncList
from openquake.risklib.asset import _get_exposure
from openquake.risklib.countries import country2code, REGIONS
from openquake.commonlib.datastore import create_job_dstore
from openquake.commonlib.oqvalidation import OqParam
from openquake.commonlib import expo_to_hdf5

U16 = numpy.uint16
F32 = numpy.float32


def collect_exposures(grm_dir, redfactor=1):
    """
    Collect the files of kind Exposure_<Country>.xml.

    :returns: xmlfiles
    """
    country_region = []
    out = []
    for region in os.listdir(grm_dir):
        expodir = os.path.join(grm_dir, region, 'Exposure')
        if not os.path.exists(expodir):
            continue
        for country in os.listdir(expodir):
            if country in country2code:
                country_region.append((country2code[country], region))
                fullcountry = os.path.join(expodir, country)
                for f in os.listdir(fullcountry):
                    if f.startswith('Exposure_') and f.endswith('.xml'):
                        # i.e. Exposure_ZMB.xml
                        fullname = os.path.join(expodir, country, f)
                        out.append(fullname)
    return general.random_filter(out, redfactor), country_region


# tested in crmodel_test.py
def read_crmodel(vulndir):
    """
    Read the vulnerability files of kind vulnerability_<KIND>.xml
    """
    vfuncs = RiskFuncList()
    L = len('vulnerability_')
    for name in os.listdir(vulndir):
        kind = name[L:].split('.')[0]
        # vulnerability_area.xml -> area
        fname = os.path.join(vulndir, name)
        logging.info(f'Reading {fname}')
        for vf in nrml.to_python(fname).values():
            vf.loss_type = 'occupants' if kind == 'fatalities' else kind
            vf.kind = 'vulnerability'
            vfuncs.append(vf)
    logging.info(f'Read {len(vfuncs)} functions')
    oq = OqParam(calculation_mode='custom')
    return CompositeRiskModel(oq, vfuncs)

    
def get_gsim_lt(cwd):
    """
    :returns: a GsimLogicTree instance
    """
    f1 = os.path.join(cwd, 'gmmLTrisk.xml')
    if os.path.exists(f1):
        return gsim_lt.GsimLogicTree(f1)
    f2 = os.path.join(cwd, 'gmmLT.xml')
    return gsim_lt.GsimLogicTree(f2)


def discard_dupl(records):
    # discard duplicate sites
    assert len(records)
    acc = {}
    for rec in records:
        lonlat = rec['lon'], rec['lat']
        if lonlat not in acc:
            acc[lonlat] = rec
    return numpy.array(list(acc.values()), dtype=rec.dtype)


def build_site_model(grm_dir):
    """
    Build the global site model starting from the CSV files in the
    global_risk_model directory
    """
    factor = float(os.environ.get('OQ_SAMPLE_ASSETS', 1))
    dfs = []
    for cwd, dirs, files in os.walk(grm_dir):
        for f in files:
            if f.startswith('Site_model_') and f.endswith('.csv'):
                print('Reading %s' % f)
                df = pandas.read_csv(os.path.join(cwd, f))
                if factor < 1:
                    df = general.random_filter(df, factor*10)
                if len(df):
                    dfs.append(df)
    columns = set()
    n = 0
    for df in dfs:
        columns.update(df.columns)
        n += len(df)
    dt = [(col, site.site_param_dt[col]) for col in sorted(columns)]
    sm = numpy.zeros(n, dt)
    row = 0
    for df in dfs:
        n = len(df)
        recs = sm[row:row + n]
        for col in df.columns:
            val = df[col].to_numpy()
            if col in ('lon', 'lat'):
                recs[col] = numpy.round(val, 5)
            else:
                recs[col] = val
        row += n
    return discard_dupl(sm)


def build_site_model_gsims(grm_dir, dstore):
    """
    Storing the global site_model and gsim table
    """
    rows = []
    for region in REGIONS:
        for cwd, dirs, files in os.walk(os.path.join(grm_dir, region)):
            for f in files:
                if f == 'job_vs30.ini':
                    model = cwd.split('/')[-2]
                    gsim_lt = get_gsim_lt(cwd)
                    for trt, gsims in gsim_lt.values.items():
                        for gsim in gsims:
                            q = (model, trt, str(gsim), gsim.weight['default'])
                            rows.append(q)
    smodel = build_site_model(grm_dir)
    dstore['site_model'] = smodel
    dtlist = [('model', '<S3'), ('trt', '<S61'), ('gsim', hdf5.vstr),
              ('weight', float)]
    dstore['model_trt_gsim_weight'] = numpy.array(rows, dtlist)
    return len(smodel)


def find_long_strings_and_export(csv_paths, fieldname, output_csv_path,
                                 min_length=32):
    results = []
    for file_path in csv_paths:
        try:
            with open(file_path, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if not headers or fieldname not in headers:
                    continue  # skip if the field is missing
                field_index = headers.index(fieldname)
                for i, row in enumerate(reader, start=2):  # skip header
                    if len(row) > field_index:
                        value = row[field_index]
                        if len(value) > min_length:
                            results.append({
                                "filename": file_path,
                                "linenumber": i,
                                fieldname: value,
                                f"{fieldname}_len": len(value)
                            })
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    if results:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as out:
            fieldnames = ["filename", "linenumber", fieldname,
                          f"{fieldname}_len"]
            writer = csv.DictWriter(out, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print(f"Results saved to {output_csv_path}")
    else:
        print("No strings longer than {} characters found.".format(min_length))


def main(grm_dir, wfp=False, action='build'):
    """
    If action='build' (the default) stores the global exposure and tmap.
    If action='zip' zips the global exposure in a single file exposures.zip
    If action='find_long_XXX' find the fields XXX longer than 32 chars
    """
    if action.startswith('find_long'):  # i.e. find_long_NAME_2
        fieldname = action[10:]
        exposures_xml, _ = collect_exposures(grm_dir)
        csv_files = []
        for xml in exposures_xml:
            exposure, _ = _get_exposure(xml, stop='asset')
            csv_files.extend(exposure.datafiles)
        output_file = "long_strings.csv"
        find_long_strings_and_export(csv_files, fieldname, output_file)
        return
    elif action == 'zip':
        tmaps = sorted(expo_to_hdf5.read_world_tmap(grm_dir))
        exposures_xml, _ = collect_exposures(grm_dir)
        csv_files = []
        for xml in exposures_xml:
            print(f'Reading {xml}')
            exposure, _ = _get_exposure(xml, stop='asset')
            csv_files.extend(exposure.datafiles)
        n = len(tmaps) + len(exposures_xml) + len(csv_files)
        print(f'Zipping {n} files')
        a = general.zipfiles(tmaps + exposures_xml + csv_files, 'exposures.zip')
        print(f'Saved {a} [{general.humansize(os.path.getsize(a))}]')
        return
    elif action == 'debug':
        redfactor = .01  # sample 1 file each 100
    else:
        redfactor = 1
    mon = performance.Monitor(measuremem=True)
    description = 'Storing global exposure to hdf5'
    if wfp:
        description += ' (only for WFP countries)'
    job, dstore = create_job_dstore(description=description)
    sample = os.environ.get('OQ_SAMPLE_ASSETS')
    with dstore, job:
        with mon:
            n = build_site_model_gsims(grm_dir, dstore)
            logging.info('Stored {:_d} sites'.format(n))
            vulndir = os.path.join(
                grm_dir, 'Vulnerability', 'Global', 'vulnerability')
            for i, region in enumerate(REGIONS):
                crmodel = read_crmodel(os.path.join(vulndir, region))
                logging.info(f'Creating crm{region}')
                if sample and i > 0:
                    # make a soft link to the first region to save space
                    dstore[f'crm{region}'] = h5py.SoftLink(f'crm{REGIONS[0]}')
                else:
                    dstore.create_df(f'crm{region}', crmodel.to_dframe(),
                                     'gzip', **crmodel.get_attrs())
            fnames, country_region = collect_exposures(grm_dir, redfactor)
            countries, regions = zip(*country_region)
            dstore['countries'] = numpy.array(countries)
            dstore['regions'] = numpy.array(regions)
            expo_to_hdf5.store(fnames, grm_dir, wfp, dstore)
        logging.info(mon)


main.grm_dir = 'Directory containing the global risk model'
main.wfp = 'If true, consider only 7 countries for the World Food Program'
main.action = 'Perform an action (build, debug, zip, find_long_<FIELD>)'

if __name__ == '__main__':
    sap.run(main)
