# -*- coding: utf-8 -*-
"""Framework-neutral server services shared by API adapters."""

import ast
import csv
from contextlib import contextmanager
import json
import logging
import multiprocessing as mp
import os
import pickle
import shutil
import string
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from threading import RLock

from openquake.baselib import config, hdf5, parallel
from openquake.baselib.general import zipfiles
from openquake.calculators import views as calculator_views
from openquake.calculators.export import (
    AGGRISK_FIELD_DESCRIPTION, EXPOSURE_FIELD_DESCRIPTION, export)
from openquake.calculators.extract import extract as _extract
from openquake.calculators.getters import NotFound
from openquake.commonlib import datastore, logs, oqvalidation, readinput
from openquake.engine import aelo, engine, impact
from openquake.engine.aelo import get_params_from
from openquake.engine.export.core import export_from_db
from openquake.hazardlib import valid
from openquake.hazardlib.shakemap.validate import impact_validate
from openquake.calculators.postproc.plots import plot_shakemap, plot_rupture

UTC = timezone.utc

# FastAPI sync handlers use a threadpool; serialize HDF5 reads per process.
HDF5_READ_LOCK = RLock()


def _reset_hdf5_read_lock():
    """Reset the lock in forked children if another thread held it."""
    global HDF5_READ_LOCK
    HDF5_READ_LOCK = RLock()


if hasattr(os, 'register_at_fork'):
    os.register_at_fork(after_in_child=_reset_hdf5_read_lock)


@contextmanager
def hdf5_read_lock():
    """Acquire the current process's HDF5 read lock."""
    with HDF5_READ_LOCK:
        yield


def get_impact_rupture_data(post, user, rupture_path):
    """Validate a rupture and build the data needed by the IMPACT UI."""
    rup, rupdic, _oqparams, err = impact_validate(
        post, user, rupture_path)
    if err:
        return err, 400 if 'invalid_inputs' in err else 500
    if rupdic.get('shakemap_array') is not None:
        shakemap_array = rupdic['shakemap_array']
        figsize = (6.3, 6.3)
        rupdic['pga_map_png'] = plot_shakemap(
            shakemap_array, 'PGA', backend='Agg', figsize=figsize,
            with_cities=False, return_base64=True, rupture=rup)
        rupdic['mmi_map_png'] = plot_shakemap(
            shakemap_array, 'MMI', backend='Agg', figsize=figsize,
            with_cities=False, return_base64=True, rupture=rup)
        del rupdic['shakemap_array']
    elif rup is not None:
        rupdic['rupture_png'] = plot_rupture(
            rup, backend='Agg', figsize=(8, 8), with_region_labels=True,
            return_base64=True)
    if user.level < 2 and 'warning_msg' in rupdic:
        del rupdic['warning_msg']
    return rupdic, 200


CWD = os.path.dirname(__file__)
KUBECTL = 'kubectl apply -f -'.split()
ENGINE = 'python -m openquake.engine.engine'.split()

XML = 'application/xml'
JSON = 'application/json'
ZIP = 'application/x-zip'

#: For exporting calculation outputs, the client can request a specific format
#: (xml, geojson, csv, etc.). If the client does not specify, give them (NRML)
#: XML by default.
DEFAULT_EXPORT_TYPE = 'xml'
EXPORT_CONTENT_TYPE_MAP = dict(xml=XML, geojson=JSON)
DEFAULT_CONTENT_TYPE = 'text/plain'


def remove_exported(fname):
    """Remove the temporary directory containing an exported file."""
    shutil.rmtree(os.path.dirname(fname), ignore_errors=True)


def remove_temp_file(fname):
    """Remove a temporary output file after it has been sent."""
    try:
        os.remove(fname)
    except FileNotFoundError:
        pass


def create_png_file(ds_path, what, calc_id):
    """Render a stored PNG resource to a temporary file."""
    # Pillow is optional and only needed when this endpoint is called.
    from PIL import Image

    temp_dir = config.directory.custom_tmp or tempfile.gettempdir()
    fd, fname = tempfile.mkstemp(
        prefix='calc_%s_' % calc_id, suffix='.png', dir=temp_dir)
    os.close(fd)
    try:
        with hdf5_read_lock():
            with datastore.read(ds_path) as dstore:
                arr = dstore['png/%s' % what][:]
        Image.fromarray(arr).save(fname, format='png')
    except Exception:
        remove_temp_file(fname)
        raise
    return fname


def create_impact_report_file(ds_path, iso3, file_format):
    """Copy a stored country report to a temporary file."""
    with hdf5_read_lock():
        with datastore.read(ds_path) as dstore:
            impact_group = dstore['impact']
            if iso3 not in impact_group:
                raise ValueError("ISO3 '%s' not found" % iso3)
            report = bytes(impact_group[iso3][f'report_{file_format}'][()])
    temp_dir = config.directory.custom_tmp or tempfile.gettempdir()
    fd, fname = tempfile.mkstemp(
        prefix='impact_report_', suffix='.' + file_format, dir=temp_dir)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(report)
    except Exception:
        remove_temp_file(fname)
        raise
    return fname


def extract_datastore_table(ds_path, resource):
    """Extract a table from the calculation datastore."""
    with hdf5_read_lock():
        with datastore.read(ds_path) as dstore:
            return _extract(dstore, resource)


def get_exposure_by_lse(ds_path, secondary_peril, discard_empty=True):
    """Return exposure by secondary-peril tiers and selected columns."""
    resource = (
        f'exposure_by_lse?secondary_peril={secondary_peril}'
        f'&discard_empty={discard_empty}')
    with hdf5_read_lock():
        with datastore.read(ds_path) as dstore:
            exposure = _extract(dstore, resource)
    column_descriptions = {
        col: description
        for col, description in EXPOSURE_FIELD_DESCRIPTION.items()
        if col in exposure.columns}
    return {
        'column_descriptions': column_descriptions,
        'exposure_by_lse': exposure.to_dict(),
    }


def get_exposure_by_mmi(ds_path):
    """Return MMI-aggregated exposure data and column descriptions."""
    with hdf5_read_lock():
        with datastore.read(ds_path) as dstore:
            exposure = _extract(dstore, 'mmi_tags')
    return {
        'column_descriptions': EXPOSURE_FIELD_DESCRIPTION,
        'exposure_by_mmi': exposure.to_dict(),
    }


def get_impact_results(ds_path):
    """Return the aggregate-risk data and its column descriptions."""
    with hdf5_read_lock():
        with datastore.read(ds_path) as dstore:
            impact = _extract(dstore, 'aggrisk_tags')
    return {
        'loss_type_descriptions': AGGRISK_FIELD_DESCRIPTION,
        'impact': impact.to_dict(),
    }


def create_aggrisk_csv(ds_path, calc_id):
    """Write aggregate risk data to a temporary CSV file."""
    temp_dir = config.directory.custom_tmp or tempfile.gettempdir()
    fd, fname = tempfile.mkstemp(
        prefix='aggrisk_%s_' % calc_id, suffix='.csv', dir=temp_dir)
    os.close(fd)
    try:
        with hdf5_read_lock():
            with datastore.read(ds_path) as ds:
                losses = calculator_views.view('aggrisk', ds)
        with open(fname, 'w', encoding='utf-8', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(losses.dtype.names)
            writer.writerows(losses)
    except Exception:
        remove_temp_file(fname)
        raise
    return fname


def create_job_zip(ds_path, job_id):
    """Create a job archive in a temporary directory and return its path."""
    with hdf5_read_lock():
        with datastore.read(ds_path) as ds:
            exported = export(('job', 'zip'), ds)
    temp_dir = config.directory.custom_tmp or tempfile.gettempdir()
    tmpdir = tempfile.mkdtemp(dir=temp_dir)
    fname = os.path.join(tmpdir, 'job_%s.zip' % job_id)
    try:
        zipfiles(exported, fname, cleanup=True)
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    return fname


def create_extract_file(ds_path, resource):
    """Extract a datastore resource to a temporary NPZ file."""
    # NOTE: TMPDIR is sometimes ignored, so prefer custom_tmp when configured.
    temp_dir = config.directory.custom_tmp or tempfile.gettempdir()
    prefix = resource.split('?', 1)[0].replace('/', '-')
    fd, fname = tempfile.mkstemp(
        prefix=prefix, suffix='.npz', dir=temp_dir)
    os.close(fd)
    try:
        with hdf5_read_lock():
            with datastore.read(ds_path) as ds:
                extracted = _extract(ds, resource)
                hdf5.save_npz(extracted, fname)
    except Exception:
        remove_temp_file(fname)
        raise
    return fname


def export_result(result_id, export_type=None):
    """
    Export a calculation result in the requested format.

    :param result_id: ID of the result to export
    :param export_type: export format, NRML XML by default
    :returns: a triple (fname, content_type, exportname) where `fname` is
        the path of a file inside a fresh temporary directory, or None if
        the result cannot be exported in the given format
    :raises: DataStoreExportError if the export fails
    """
    export_type = export_type or DEFAULT_EXPORT_TYPE
    job_id, _, _, datadir, ds_key = logs.dbcmd('get_result', result_id)
    # NOTE: for some reason, in some cases, the environment variable TMPDIR is
    # ignored, so we need to use config.directory.custom_tmp if defined
    temp_dir = config.directory.custom_tmp or tempfile.gettempdir()
    tmpdir = tempfile.mkdtemp(dir=temp_dir)
    try:
        with hdf5_read_lock():
            exported = export_from_db(
                (ds_key, export_type), job_id, datadir, tmpdir)
        if not exported:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return None
        if len(exported) > 1:
            # build an archive, so that there is a single file to download
            archname = ds_key + '-' + export_type + '.zip'
            fname = os.path.join(tmpdir, archname)
            zipfiles(exported, fname, cleanup=True)
            content_type = EXPORT_CONTENT_TYPE_MAP.get(export_type, ZIP)
        else:  # single file
            fname = exported[0]
            content_type = EXPORT_CONTENT_TYPE_MAP.get(
                export_type, DEFAULT_CONTENT_TYPE)
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise
    return fname, content_type, 'output-%s-%s' % (
        result_id, os.path.basename(fname))


def store(request_files, ini, calc_id):
    """
    Store the uploaded files in calc_dir and select the job file by looking
    at the .ini extension.

    :returns: full path of the ini file
    """
    calc_dir = parallel.calc_dir(calc_id)
    input_files = request_files.getlist('archive')
    named_files = [
        (input_file, getattr(input_file, 'name', None) or
         getattr(input_file, 'filename', ''))
        for input_file in input_files]
    zip_file = next(
        (input_file for input_file, name in named_files
         if name.endswith('.zip')), None)
    if zip_file is None:
        # move each file to calc_dir using the upload file names
        inifiles = []
        for input_file, name in named_files:
            # input_file is a starlette.datastructures.UploadFile
            # which contains a .file of kind tempfile.SpooledTemporaryFile
            new_path = os.path.join(calc_dir, name)
            with open(new_path, 'wb') as target:
                shutil.copyfileobj(input_file.file, target)
            if name.endswith(ini):
                inifiles.append(new_path)
    else:  # extract the files from the archive into calc_dir
        source = getattr(zip_file, 'file', zip_file)
        inifiles = readinput.extract_from_zip(source, ini, calc_dir)
    if not inifiles:
        raise NotFound('There are no %s files in the archive' % ini)
    return inifiles[0]


def save_pik(job, dirname):
    """Save a calculation job context for an external submit command."""
    path = os.path.join(dirname, 'calc%d.pik' % job.calc_id)
    with open(path, 'wb') as fobj:
        pickle.dump([job], fobj)
    return path


def submit_job(request_files, ini, username, hc_id, notify_to=None):
    """Create a calculation job and submit it without Django dependencies."""
    [job] = engine.create_jobs(
        [dict(calculation_mode='custom',
              description='Calculation waiting to start')],
        config.distribution.log_level, None, username, hc_id)
    try:
        job_ini = (store(request_files, ini, job.calc_id)
                   if request_files else ini)
        job.oqparam = oq = readinput.get_oqparam(
            job_ini, kw={'hazard_calculation_id': hc_id,
                         'export_dir': (config.directory.custom_tmp or
                                        tempfile.gettempdir())})
        logs.dbcmd('update_job', job.calc_id, dict(
            calculation_mode=oq.calculation_mode, description=oq.description,
            hazard_calculation_id=hc_id))
    except Exception as exc:
        logs.dbcmd('log', job.calc_id, datetime.now(UTC), 'CRITICAL',
                   'before starting', traceback.format_exc())
        logs.dbcmd('finish', job.calc_id, 'failed')
        exc.job_id = job.calc_id
        raise
    custom_tmp = os.path.dirname(job_ini)
    submit_cmd = config.distribution.submit_cmd.split()
    big_job = oq.get_input_size() > int(config.distribution.min_input_size)
    if submit_cmd == ENGINE:
        subprocess.Popen(submit_cmd + [save_pik(job, custom_tmp)])
    elif submit_cmd == KUBECTL and big_job:
        with open(os.path.join(CWD, 'job.yaml')) as fobj:
            yaml = string.Template(fobj.read()).substitute(
                DATABASE='%(host)s:%(port)d' % config.dbserver,
                CALC_PIK=save_pik(job, custom_tmp),
                CALC_NAME='calc%d' % job.calc_id)
        subprocess.run(submit_cmd, input=yaml.encode('ascii'))
    else:
        kwargs = {'notify_to': notify_to} if notify_to is not None else {}
        proc = mp.Process(target=engine.run_jobs, args=([job], 1),
                          kwargs=kwargs)
        proc.start()
        if config.webapi.calc_timeout:
            mp.Process(
                target=engine.watchdog,
                args=(job.calc_id, proc.pid,
                      int(config.webapi.calc_timeout))).start()
    return job.calc_id


def get_papers_job_ctx(papers, rup_id, form):
    """Build a PAPERS job context using an injected papers adapter."""
    consequence_model = form.get('consequence_model')
    consequence = (json.loads(consequence_model)
                   if consequence_model else papers.CONSEQUENCE)
    return papers.get_job_ctx(
        rup_id, papers.FNAME, papers.GMM_LT, papers.SITE_MODEL,
        papers.IMTS_RISK, papers.INTEGRATION_DISTANCE, papers.TRUNCATION,
        papers.NGMFS, form.get('exposure_filepath', papers.EXPOSURE),
        form.get('mapping', papers.MAPPING),
        form.get('fragility_curves', papers.FRAGILITY), consequence,
        papers.HAZARD_ONLY, form.get('username'))


def create_impact_job(params, username, job_owner_email, build_urls,
                      callback, email_file_path):
    """Create and start an IMPACT job using injected adapters."""
    rupdic = ast.literal_eval(params['rupture_dict'])
    if rupdic['approach'] == 'use_shakemap_from_usgs':
        params['secondary_perils'] = (
            'AllstadtEtAl2022Landslides, AllstadtEtAl2022Liquefaction')
        params['intensity_measure_types'] = (
            'PGA, PGV, SA(0.3), SA(0.6), SA(1.0)')
    [jobctx] = engine.create_jobs(
        [params], config.distribution.log_level, user_name=username)
    urls = build_urls(jobctx.calc_id)
    response = {jobctx.calc_id: dict(status='created', job_id=jobctx.calc_id,
                                     **urls)}
    if not job_owner_email:
        response[jobctx.calc_id]['WARNING'] = (
            'No email address is specified for your user account, therefore '
            'email notifications will be disabled. As soon as the job '
            'completes, you can access its outputs at: %s. The traceback is '
            'available at: %s' % (urls['outputs_uri'], urls['traceback_uri']))
    args = ([params], [jobctx], job_owner_email, urls['outputs_uri_web'],
            callback, email_file_path)
    if 'pytest' in sys.argv[0] and os.getenv('OQ_DISTRIBUTE') == 'no':
        impact.main_web(*args)
    else:
        mp.Process(target=impact.main_web, args=args).start()
    return response


def validate_aelo_data(post, form_labels, max_site_name_length):
    """Validate AELO form data without depending on Django."""
    errors = {}
    invalid = []
    validate_vs30 = valid.FloatRange(150, 1525, 'vs30')
    checks = (
        ('lon', lambda: valid.longitude(post.get('lon'))),
        ('lat', lambda: valid.latitude(post.get('lat'))),
        ('site_name', lambda: post.get('site_name') or
         (_ for _ in ()).throw(ValueError('can not be empty'))),
    )
    values = {}
    for name, check in checks:
        try:
            values[name] = check()
            if (name == 'site_name'
                    and len(values[name]) > max_site_name_length):
                raise ValueError(
                    'site name can not be longer than %s characters' %
                    max_site_name_length)
        except Exception as exc:
            errors[form_labels[name]] = str(exc)
            invalid.append(name)
    try:
        asce = post.get(
            'asce_version', oqvalidation.OqParam.asce_version.default)
        oqvalidation.OqParam.asce_version.validator(asce)
        values['asce_version'] = asce
    except Exception as exc:
        errors[form_labels['asce_version']] = str(exc)
        invalid.append('asce_version')
    try:
        site_class = post.get('site_class')
        oqvalidation.OqParam.site_class.validator(site_class)
        values['site_class'] = site_class
    except Exception as exc:
        errors[form_labels['site_class']] = str(exc)
        invalid.append('site_class')
    try:
        vs30s = sorted(float(value) for value in post.get('vs30').split())
        values['vs30'] = ' '.join(str(validate_vs30(value)) for value in vs30s)
    except Exception as exc:
        errors[form_labels['vs30']] = str(exc)
        invalid.append('vs30')
    if (not errors and values['site_class'] is not None and
            values['site_class'] != 'custom'):
        expected = oqvalidation.SITE_CLASSES[
            values['asce_version']][values['site_class']]['vs30']
        expected = expected if isinstance(expected, list) else [expected]
        expected = ' '.join(str(float(value)) for value in expected)
        if values['vs30'] != expected:
            errors[form_labels['vs30']] = (
                'For site class %s the expected Vs30 is %s instead of %s' %
                (values['site_class'], expected, values['vs30']))
            invalid.append('vs30')
    if errors:
        message = 'Invalid input value%s\n' % ('s' if len(errors) > 1 else '')
        message += '\n'.join(
            '%s: "%s"' % (field.split(' (')[0], value)
            for field, value in errors.items())
        return {'status': 'failed', 'error_msg': message,
                'invalid_inputs': invalid}, 400
    return (values['lon'], values['lat'], values['site_name'],
            values['asce_version'], values['site_class'], values['vs30']), 200


def run_aelo(lon, lat, site_name, asce_version, site_class, vs30,
             username, job_owner_email, build_urls, callback,
             email_file_path):
    """Create and start an AELO job using injected URL and callback helpers."""
    description = f'AELO for {site_name}'
    try:
        params = get_params_from(
            dict(sites='%s %s' % (lon, lat), asce_version=asce_version,
                 site_class=site_class, vs30=vs30, description=description),
            config.directory.mosaic_dir, exclude=['USA'])
        logging.root.handlers = []
    except Exception as exc:
        logging.exception(str(exc))
        return {'status': 'failed', 'error_cls': type(exc).__name__,
                'error_msg': str(exc)}, 400
    params['export_dir'] = config.directory.custom_tmp or tempfile.gettempdir()
    [jobctx] = engine.create_jobs(
        [params], config.distribution.log_level, None, username, None)
    urls = build_urls(jobctx.calc_id)
    response = dict(status='created', job_id=jobctx.calc_id, **urls)
    if not job_owner_email:
        response['WARNING'] = (
            'No email address is specified for your user account, therefore '
            'email notifications will be disabled. As soon as the job '
            'completes, you can access its outputs at: %s. The traceback is '
            'available at: %s' % (urls['outputs_uri'], urls['traceback_uri']))
    args = (
        lon, lat, vs30, params['siteid'], description, asce_version,
        site_class, jobctx, job_owner_email, urls['outputs_uri_web'],
        config.directory.mosaic_dir, callback, email_file_path)
    if 'pytest' in sys.argv[0] and os.getenv('OQ_DISTRIBUTE') == 'no':
        aelo.main(*args)
    else:
        mp.Process(target=aelo.main, args=args).start()
    return response, 200
