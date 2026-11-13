# -*- coding: utf-8 -*-
"""
The logic of the WebUI, called in-process by :mod:`openquake.server.views`:
running, aborting and removing calculations, reading their logs and
exporting their results. The functions raise
:class:`openquake.server.internal_api.ApiError` on failure, which
:func:`openquake.server.internal_api.run` turns into a JSON response.
"""

import ast
import json
import logging
import multiprocessing as mp
import os
import pickle
import shutil
import signal
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail.backends.filebased import (
    EmailBackend as FileEmailBackend)
from django.http import FileResponse, JsonResponse
from django.urls import reverse
from django.utils.datastructures import MultiValueDict

from openquake.baselib import config, parallel
from openquake.baselib.general import gettemp, zipfiles
from openquake.calculators import base
from openquake.calculators.extract import extract as extract_output
from openquake.calculators.getters import NotFound
from openquake.commonlib import datastore, logs, oqvalidation, readinput
from openquake.commonlib.model_provenance import read_model_provenance
from openquake.engine import aelo, engine, impact
from openquake.engine.aelo import get_params_from
from openquake.engine.export.core import DataStoreExportError, export_from_db
from openquake.hazardlib import valid
from openquake.hazardlib.shakemap.validate import (
    IMPACT_APPROACHES, impact_validate)
from openquake.calculators.postproc.plots import plot_shakemap, plot_rupture
from openquake.server.internal_api import ApiError, json_response
from openquake.server.papers import base as papers

UTC = timezone.utc
AELO_FORM_LABELS = {
    'lon': 'Longitude',
    'lat': 'Latitude',
    'site_class': 'Site class',
    'vs30': 'Vs30 (m/s)',
    'site_name': 'Site name',
    'asce_version': 'ASCE standards',
}
AELO_VALID_VS30_RANGE = [150, 1525]


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
            # input_file is a Django UploadedFile, whose .file is a file object
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
    # same logger as the logins (signals.py): the line goes to webui-access.log
    logging.getLogger('openquake.server.signals').info(
        'User "%s" submitted calculation %d', username, job.calc_id)
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
    if submit_cmd == ENGINE:
        subprocess.Popen(submit_cmd + [save_pik(job, custom_tmp)])
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


class ExportResponse(FileResponse):
    """Stream an exported file and remove its directory once closed."""

    def __init__(self, fname, **kwargs):
        super().__init__(open(fname, 'rb'), **kwargs)
        self.fname = fname

    def close(self):
        super().close()
        remove_exported(self.fname)


def _pairs(source):
    """Return the (key, value) pairs of a dictionary or a MultiValueDict."""
    if hasattr(source, 'lists'):
        return [(key, value) for key, values in source.lists()
                for value in values]
    return list(source.items())


def make_form(*sources):
    """
    Merge plain fields (dictionaries or QueryDicts) and uploaded files into
    a single MultiValueDict, the form accepted by the internal functions.
    """
    form = MultiValueDict()
    for source in sources:
        for key, value in _pairs(source):
            form.appendlist(key, value)
    return form


def _split(form):
    """Return the plain fields and the uploaded files of a form."""
    fields, files = MultiValueDict(), MultiValueDict()
    for key, value in _pairs(form):
        (files if hasattr(value, 'file') else fields).appendlist(key, value)
    return fields, files


def _uri_builder(base_url):
    """Return a function building absolute URIs from paths on the server."""
    def build_absolute_uri(path):
        return urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))
    return build_absolute_uri


def calc_info(calc_id):
    """Return the information about a calculation."""
    return logs.dbcmd('calc_info', calc_id)


def get_impact_resource_data(dstore):
    """Return available IMPACT resources without presentation URLs."""
    png_names = list(dstore['png']) if 'png' in dstore else []
    try:
        extract_output(dstore, 'aggrisk_tags')
    except KeyError:
        aggrisk_tags = False
    else:
        aggrisk_tags = True
    avg_gmf_plots = {}
    for name in png_names:
        if name.startswith('avg_gmf-') and name.endswith('.png'):
            imt = name[len('avg_gmf-'):-len('.png')]
            avg_gmf_plots[imt] = name
    return {
        'avg_gmf_plots': avg_gmf_plots,
        'assets': 'assets.png' in png_names,
        'aggrisk': 'aggrisk' in dstore,
        'aggrisk_tags': aggrisk_tags,
        'exposure_by_mmi': 'mmi_tags' in dstore,
        'exposure_by_lse': {
            peril: f'exposure_by_{peril}_lse' in dstore
            for peril in ('liquefaction', 'landslide')},
        'country_reports': (list(dstore['impact'])
                            if 'impact' in dstore else []),
    }


def _no_provenance():
    """Return the answer for calculations without model provenance."""
    return {
        'available': False,
        'reason': 'Model provenance metadata is not available',
    }


def model_provenance(calc_id):
    """Return the model provenance of a calculation."""
    job = logs.dbcmd('get_job', calc_id)
    if job is None:
        raise ApiError(404)
    path = job.ds_calc_dir + '.hdf5'
    if not os.path.exists(path):
        return _no_provenance()
    try:
        with datastore.read(path) as dstore:
            summary = read_model_provenance(dstore)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logging.exception('Could not read model provenance')
        raise ApiError(500, str(exc)) from exc
    if summary is None:
        return _no_provenance()
    return {'available': True, 'summary': summary}


def get_uploaded_file_path(files, filename):
    """Copy an uploaded file to a temporary path and return its location."""
    file = files.get(filename)
    if file:
        # NOTE: we could not find a reliable way to avoid the deletion of the
        # uploaded file right after the request is consumed, therefore we need
        # to store a copy of it
        suffix = file.name[-4:]
        source = getattr(file, 'file', None)
        if source is None:
            with open(file.temporary_file_path(), 'rb') as stream:
                content = stream.read()
        else:
            source.seek(0)
            content = source.read()
        return gettemp(content, suffix=suffix)


def validate_job(job_file):
    """Validate a calculation input and return its JSON-compatible result."""
    try:
        oq = readinput.get_oqparam(job_file)
        with patch.dict(os.environ, {'OQ_CHECK_INPUT': '1'}):
            base.calculators(oq, calc_id=None).run()
    except Exception as exc:
        return dict(error_msg=str(exc), error_line=None, valid=False)
    return dict(error_msg=None, error_line=None, valid=True)


def validate_upload(form, field, missing_message):
    """Validate the calculation file stored under the given field."""
    fields, files = _split(form)
    if field in files:
        path = get_uploaded_file_path(files, field)
    else:
        path = fields.get(field)
    if not path:
        raise ApiError(400, missing_message)
    return validate_job(path)


def calc_run(form):
    """Submit a calculation, using the archive in the form if present."""
    ini = form.get('ini') or form.get('job_ini') or '.ini'
    hazard_job_id = form.get('hazard_job_id') or None
    username = form.get('username')
    if not username:
        raise ApiError(400, 'Missing calculation owner')
    notify_to = form.get('notify_to') or None
    request_files = form if form.getlist('archive') else []
    try:
        job_id = submit_job(
            request_files, ini, username, hazard_job_id, notify_to)
    except Exception as exc:
        exc_msg = traceback.format_exc() + str(exc)
        logging.error(exc_msg)
        raise ApiError(500, content={
            'traceback': exc_msg.splitlines(),
            'job_id': getattr(exc, 'job_id', None)}) from exc
    return logs.get_job_info(job_id)


def calc_abort(calc_id):
    """Abort a running calculation."""
    job = logs.dbcmd('get_job', calc_id)
    if job is None:
        return {'error': 'Unknown job %s' % calc_id}
    if job.status not in ('submitted', 'executing'):
        return {'error': 'Job %s is not running' % job.id}
    if job.pid:
        try:
            os.kill(job.pid, signal.SIGINT)
        except OSError as exc:
            logging.error(exc)
            # An exiting process may have persisted its final status since
            # the first lookup. Preserve that result and report it normally.
            current = logs.dbcmd('get_job', job.id)
            if current is not None and current.status not in (
                    'submitted', 'executing'):
                return {'error': 'Job %s is not running' % job.id}
            return {'error': 'Unable to abort job %s: %s' % (job.id, exc)}
        # Completion and this conditional UPDATE compete atomically: never
        # turn an already completed or failed calculation into an aborted one.
        if not logs.dbcmd('set_aborted', job.id):
            current = logs.dbcmd('get_job', job.id)
            # The worker may handle SIGINT before our UPDATE: MasterKilled
            # is recorded as failed by LogContext.__exit__, while other exit
            # paths record aborted. Preserve either result.
            if current is None or current.status not in ('failed', 'aborted'):
                return {'error': 'Job %s is not running' % job.id}
        logging.warning('Aborting job %d, pid=%d', job.id, job.pid)
        # Success acknowledges signal delivery, not the final job outcome.
        # A concurrent failure may be unrelated to SIGINT, and the worker
        # can still persist successful completion after this response.
        return {'success': 'Killing job %d' % job.id}
    return {'error': 'PID for job %s not found' % job.id}


def calc_remove(calc_id, username):
    """Remove a calculation on behalf of its owner."""
    message = logs.dbcmd('del_calc', calc_id, username)
    if 'success' in message or 'error' in message:
        return message
    raise ApiError(500, str(message))


def aelo_run(form):
    """Run an AELO calculation from the given form."""
    username = form.get('username')
    base_url = form.get('base_url')
    if not username or not base_url:
        raise ApiError(400, 'Missing AELO caller information')
    result = aelo_validate(SimpleNamespace(POST=form))
    if hasattr(result, 'status_code'):
        raise ApiError(result.status_code,
                       content=json.loads(result.content))
    lon, lat, site_name, asce_version, site_class, vs30 = result
    response_data, status = _run_aelo(
        lon, lat, site_name, asce_version, site_class, vs30, username,
        form.get('email') or '', _uri_builder(base_url),
        form.get('email_file_path'))
    return json_response(response_data, status)


def run_scenario_calc_from_ses_rupture(rup_id, form):
    """Run a PAPERS scenario calculation for an SES rupture."""
    if not form.get('username'):
        raise ApiError(400, 'Missing calculation owner')
    try:
        job_ctx = get_papers_job_ctx(papers, rup_id, form)
        mp.Process(target=engine.run_jobs, args=([job_ctx],), kwargs={
            'notify_to': form.get('notify_to')}).start()
        return logs.get_job_info(job_ctx.calc_id)
    except Exception as exc:
        exc_msg = traceback.format_exc() + str(exc)
        logging.error(exc_msg)
        raise ApiError(500, content={
            'traceback': exc_msg.splitlines(),
            'job_id': getattr(exc, 'job_id', None)}) from exc


def _user(form):
    """Return the user, with the level given in the form, of an IMPACT job."""
    try:
        level = int(form.get('user_level', 0))
    except (TypeError, ValueError) as exc:
        raise ApiError(400, 'Invalid IMPACT user level') from exc
    return SimpleNamespace(level=level, testdir=None)


def _station(files, post):
    """Return the station data path and its source, if any."""
    station_path = get_uploaded_file_path(files, 'station_data_file')
    if station_path:
        return station_path, 'user-provided'
    station_from_usgs = post.get('station_data_file_from_usgs', '')
    if station_from_usgs:
        return station_from_usgs, 'USGS'
    return station_path, None


def _impact_urls(base_url):
    """Return a function building the URLs of an IMPACT job."""
    build_absolute_uri = _uri_builder(base_url)

    def build_urls(job_id):
        return {
            'outputs_uri_web': build_absolute_uri(
                f'/engine/{job_id}/outputs_impact'),
            'outputs_uri': build_absolute_uri(
                f'/v1/calc/result/{job_id}'),
            'log_uri': build_absolute_uri(
                f'/v1/calc/{job_id}/log/0:'),
            'traceback_uri': build_absolute_uri(
                f'/v1/calc/{job_id}/traceback'),
        }
    return build_urls


def impact_run(form):
    """Run an IMPACT calculation from the given form."""
    fields, files = _split(form)
    user = _user(form)
    post = {key: value for key, value in fields.items()
            if key not in ('user_level', 'username', 'email', 'base_url')}
    rupture_path = get_uploaded_file_path(files, 'rupture_file')
    if not rupture_path:
        rupture_path = post.get('rupture_from_usgs') or ''
    if rupture_path == 'None':
        rupture_path = ''
    station_path, station_source = _station(files, post)
    _rup, _rupdic, params, err = impact_validate(
        post, user, rupture_path, station_path)
    if err:
        return json_response(
            err, 400 if 'invalid_inputs' in err else 500)
    if station_source is not None:
        params['station_source'] = station_source
    if params.get('make_impact_reports'):
        params['postrisk_func'] = 'make_impact_reports.main'
    params['export_dir'] = (
        config.directory.custom_tmp or tempfile.gettempdir())
    response_data = create_impact_job(
        params, form.get('username'), form.get('email') or '',
        _impact_urls(form.get('base_url', '')), impact_callback,
        form.get('email_file_path'))
    return json_response(response_data)


def impact_get_rupture_data(form):
    """Build the rupture data of an IMPACT job from the given form."""
    post = {key: value for key, value in _pairs(form)
            if key not in ('rupture_file', 'user_level')}
    user = _user(form)
    _, files = _split(form)
    rupture_path = get_uploaded_file_path(files, 'rupture_file')
    response_data, status = get_impact_rupture_data(
        post, user, rupture_path)
    return json_response(response_data, status)


def calc_list_count(params, valid_users, acl_on):
    """Count the calculations matching the filters of the list view."""
    params = dict(params, count_only='1')
    return logs.dbcmd(
        'get_calcs', params, valid_users, valid.boolean(acl_on or '1'))


def calc_log(calc_id, start, stop):
    """Return a slice of the log of a calculation."""
    return logs.dbcmd('get_log_slice', calc_id, start, stop)


def calc_log_size(calc_id):
    """Return the number of log lines of a calculation."""
    return logs.dbcmd('get_log_size', calc_id)


def calc_traceback(calc_id):
    """Return the traceback of a calculation."""
    return logs.dbcmd('get_traceback', calc_id)


def calc_result(result_id, export_type=None):
    """Export a result in the requested format, as a downloadable file."""
    try:
        exported = export_result(result_id, export_type)
    except DataStoreExportError as exc:
        # TODO: there should be a better error page
        raise ApiError(500, '%s: %s' % (exc.__class__.__name__, exc)) from exc
    if exported is None:  # the requested format is not supported
        raise ApiError(404)
    fname, content_type, exportname = exported
    response = ExportResponse(fname, content_type=content_type)
    # NB: the Content-Disposition is set manually, since the one generated
    # by FileResponse would quote the file name
    response['Content-Disposition'] = (
        'attachment; filename=%s' % exportname)
    return response


def aelo_callback(
        job_id, job_owner_email, outputs_uri, inputs,
        exc=None, warnings=None, email_file_path=None):
    if not job_owner_email:
        return
    from_email = settings.EMAIL_HOST_USER
    to = [job_owner_email]
    reply_to = settings.EMAIL_SUPPORT
    # e.g. 'AELO for CCA'->'CCA'
    site_name = inputs['description'][9:]
    lon, lat = inputs['sites'].split()
    site_class = inputs['site_class']
    vs30s = inputs['vs30'].split()
    vs30 = vs30s[0] if site_class != 'default' else 'default'
    asce_version = inputs['asce_version']
    asce_version_str = oqvalidation.ASCE_VERSIONS[asce_version]
    if site_class is None or site_class == 'custom':
        site_class_vs30_str = f'Site Class: Vs30 = {vs30} m/s'
    else:
        site_class_display_name = oqvalidation.SITE_CLASSES[
            asce_version][site_class]['display_name']
        site_class_vs30_str = f'Site Class: {site_class_display_name}'
    aelo_version = base.get_aelo_version()
    body = (f"Site name: {site_name}\n"
            f"Latitude: {lat}, Longitude: {lon}\n"
            f"{site_class_vs30_str}\n"
            f"ASCE standard: {asce_version_str}\n"
            f"AELO version: {aelo_version}\n\n")
    if warnings is not None:
        for warning in warnings:
            body += warning + '\n'
    if exc:
        subject = f'Job {job_id} failed'
        body += f'There was an error running job {job_id}:\n{exc}'
    else:
        subject = f'Job {job_id} finished correctly'
        body += (f'Please find the results here:\n{outputs_uri}')
    connection = None
    if email_file_path:
        # NOTE: file_path is actually a directory where Django stores each
        # email with a unique name like: file_path/20260319-123456-abcdefg.log
        connection = FileEmailBackend(file_path=email_file_path)
    EmailMessage(subject, body, from_email, to,
                 reply_to=[reply_to],
                 connection=connection).send()


def impact_callback(
        job_id, params, job_owner_email, outputs_uri,
        exc=None, warnings=None, email_file_path=None):
    if not job_owner_email:
        return

    # Example of body:
    # Input parameters:
    # {'lon': 37.0143, 'lat': 37.2256, 'dep': 10.0, 'mag': 7.8, 'rake': 0.0,
    #  'usgs_id': 'us6000jllz', 'rupture_file': None}
    # maximum_distance: 20.0
    # tectonic_region_type: Active Shallow Crust
    # truncation_level: 3.0
    # number_of_ground_motion_fields: 100
    # asset_hazard_distance: 15.0
    # ses_seed: 42
    # station_data_file: None
    # maximum_distance_stations: None
    # countries: TUR
    # description: us6000jllz (37.2256, 37.0143) M7.8 TUR

    params_to_print = ''
    exclude_from_print = ['rupture_from_usgs', 'postrisk_func', 'export_dir']
    if 'shakemap_uri' in params:
        exclude_from_print.extend([
            'station_data_file', 'station_data_issue',
            'station_data_file_from_usgs',
            'trts', 'mosaic_models', 'mosaic_model', 'tectonic_region_type',
            'gsim', 'shakemap_uri', 'rupture_file', 'title', 'mmi_file',
            'rake'])
    for key, val in params.items():
        if key not in ['calculation_mode', 'inputs', 'job_ini',
                       'hazard_calculation_id']:
            if key == 'rupture_dict':
                # NOTE: params['rupture_dict'] is a string representation of a
                # dictionary, not a JSON string, so we can't use json.loads
                rupdic = ast.literal_eval(params['rupture_dict'])
                for rupkey, rupval in rupdic.items():
                    if rupkey not in exclude_from_print:
                        if rupkey == 'approach':
                            rupval = IMPACT_APPROACHES[rupval]
                        if rupval is not None and str(rupval).strip() != '':
                            if rupkey not in params:
                                # e.g. avoid writing the description twice
                                params_to_print += f'{rupkey}: {rupval}\n'
            elif key not in exclude_from_print:
                if val is not None and str(val).strip() != '':
                    params_to_print += f'{key}: {val}\n'
    if 'station_data' in params['inputs']:
        with open(params['inputs']['station_data'], 'r',
                  encoding='utf-8') as file:
            n_stations = sum(1 for line in file) - 1  # excluding the header
        params_to_print += (
            f'{n_stations} seismic stations were loaded (please see'
            f'in the calculation log if any of them were discarded)\n')
    elif 'shakemap_uri' not in params:
        params_to_print += 'No seismic stations were considered\n'

    from_email = settings.EMAIL_HOST_USER
    to = [job_owner_email]
    reply_to = settings.EMAIL_SUPPORT
    body = (f"Input parameters:\n{params_to_print}\n\n")
    if warnings is not None:
        for warning in warnings:
            body += warning + '\n'
    if exc:
        subject = f'Job {job_id} failed'
        body += f'There was an error running job {job_id}:\n{exc}'
    else:
        subject = f'Job {job_id} finished correctly'
        body += (f'Please find the results here:\n{outputs_uri}')
    connection = None
    if email_file_path:
        # NOTE: file_path is actually a directory where Django stores each
        # email with a unique name like: file_path/20260319-123456-abcdefg.log
        connection = FileEmailBackend(file_path=email_file_path)
    EmailMessage(subject, body, from_email, to,
                 reply_to=[reply_to],
                 connection=connection).send()


def aelo_validate(request):
    validation_errs = {}
    invalid_inputs = []
    validate_vs30 = valid.FloatRange(*AELO_VALID_VS30_RANGE, 'vs30')
    try:
        lon = valid.longitude(request.POST.get('lon'))
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['lon']] = str(exc)
        invalid_inputs.append('lon')
    try:
        lat = valid.latitude(request.POST.get('lat'))
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['lat']] = str(exc)
        invalid_inputs.append('lat')
    try:
        site_name = request.POST.get('site_name')
        if not site_name:
            raise ValueError("can not be empty")
        if len(site_name) > settings.MAX_AELO_SITE_NAME_LEN:
            raise ValueError(
                "site name can not be longer than %s characters" %
                settings.MAX_AELO_SITE_NAME_LEN)
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['site_name']] = str(exc)
        invalid_inputs.append('site_name')
    try:
        asce_version = request.POST.get(
            'asce_version', oqvalidation.OqParam.asce_version.default)
        oqvalidation.OqParam.asce_version.validator(asce_version)
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['asce_version']] = str(exc)
        invalid_inputs.append('asce_version')
    try:
        site_class = request.POST.get('site_class')
        oqvalidation.OqParam.site_class.validator(site_class)
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['site_class']] = str(exc)
        invalid_inputs.append('site_class')
    try:
        vs30s_in = sorted(
            float(val) for val in request.POST.get('vs30').split())
        if not vs30s_in:
            raise ValueError('can not be empty')
        vs30s_out = []
        for vs30 in vs30s_in:
            vs30s_out.append(validate_vs30(vs30))
        vs30 = ' '.join(str(val) for val in vs30s_out)
    except Exception as exc:
        validation_errs[AELO_FORM_LABELS['vs30']] = str(exc)
        invalid_inputs.append('vs30')
    if site_class is not None and site_class != 'custom':
        valid_vs30 = oqvalidation.SITE_CLASSES[
            asce_version][site_class]['vs30']
        if isinstance(valid_vs30, list):
            expected_vs30 = ' '.join(str(float(value)) for value in valid_vs30)
        else:
            expected_vs30 = str(float(valid_vs30))
        if vs30 != expected_vs30:
            # NOTE: this should never happen when using the web form, but it
            # could happen calling the 'aelo_run' API endpoint programmatically
            err_msg = (f'For site class {site_class} the expected Vs30 is'
                       f' {expected_vs30} instead of {vs30}')
            validation_errs[AELO_FORM_LABELS['vs30']] = err_msg
            invalid_inputs.append('vs30')
    if validation_errs:
        err_msg = 'Invalid input value'
        err_msg += 's\n' if len(validation_errs) > 1 else '\n'
        err_msg += '\n'.join(
            [f'{field.split(" (")[0]}: "{validation_errs[field]}"'
             for field in validation_errs])
        logging.error(err_msg)
        response_data = {"status": "failed", "error_msg": err_msg,
                         "invalid_inputs": invalid_inputs}
        return JsonResponse(response_data, status=400)
    return lon, lat, site_name, asce_version, site_class, vs30


def _run_aelo(lon, lat, site_name, asce_version, site_class, vs30,
              username, job_owner_email, build_absolute_uri,
              email_file_path):
    """Create and start an AELO job after Django has authenticated it."""
    description = f'AELO for {site_name}'
    try:
        params = get_params_from(
            dict(sites='%s %s' % (lon, lat),
                 asce_version=asce_version, site_class=site_class, vs30=vs30,
                 description=description),
            config.directory.mosaic_dir, exclude=['USA'])
        logging.root.handlers = []  # avoid breaking the logs
    except Exception as exc:
        response_data = {'status': 'failed', 'error_cls': type(exc).__name__,
                         'error_msg': str(exc)}
        logging.exception(str(exc))
        return response_data, 400
    params['export_dir'] = config.directory.custom_tmp or tempfile.gettempdir()
    [jobctx] = engine.create_jobs(
        [params], config.distribution.log_level, None, username, None)
    job_id = jobctx.calc_id
    outputs_uri_web = build_absolute_uri(
        reverse('outputs_aelo', args=[job_id]))
    outputs_uri_api = build_absolute_uri(
        reverse('results', args=[job_id]))
    log_uri = build_absolute_uri(reverse('log', args=[job_id, '0', '']))
    traceback_uri = build_absolute_uri(reverse('traceback', args=[job_id]))
    response_data = dict(
        status='created', job_id=job_id, outputs_uri=outputs_uri_api,
        log_uri=log_uri, traceback_uri=traceback_uri)
    if not job_owner_email:
        response_data['WARNING'] = (
            'No email address is specified for your user account,'
            ' therefore email notifications will be disabled. As soon as'
            ' the job completes, you can access its outputs at the following'
            ' link: %s. If the job fails, the error traceback will be'
            ' accessible at the following link: %s'
            % (outputs_uri_api, traceback_uri))
    args = (
        lon, lat, vs30, params['siteid'], description, asce_version,
        site_class, jobctx, job_owner_email, outputs_uri_web,
        config.directory.mosaic_dir, aelo_callback, email_file_path)
    if 'pytest' in sys.argv[0] and os.getenv('OQ_DISTRIBUTE') == 'no':
        aelo.main(*args)
    else:
        mp.Process(target=aelo.main, args=args).start()
    return response_data, 200
