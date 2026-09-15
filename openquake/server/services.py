# -*- coding: utf-8 -*-
"""Framework-neutral server services shared by API adapters."""

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

from openquake.baselib import config, parallel
from openquake.calculators.getters import NotFound
from openquake.commonlib import logs, oqvalidation, readinput
from openquake.engine import aelo, engine
from openquake.engine.aelo import get_params_from
from openquake.hazardlib import valid

UTC = timezone.utc
CWD = os.path.dirname(__file__)
KUBECTL = 'kubectl apply -f -'.split()
ENGINE = 'python -m openquake.engine.engine'.split()

def store(request_files, ini, calc_id):
    """Store uploaded files and return the selected input file path."""
    calc_dir = parallel.calc_dir(calc_id)
    input_files = request_files.getlist('archive')
    named_files = [
        (file, getattr(file, 'name', None) or getattr(file, 'filename', ''))
        for file in input_files]
    zip_file = next(
        (file for file, name in named_files if name.endswith('.zip')), None)
    if zip_file is None:
        inifiles = []
        for input_file, name in named_files:
            new_path = os.path.join(calc_dir, name)
            source = getattr(input_file, 'file', None)
            if source is None:
                shutil.copy2(input_file.temporary_file_path(), new_path)
            else:
                source.seek(0)
                with open(new_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
            if name.endswith(ini):
                inifiles.append(new_path)
    else:
        source = getattr(zip_file, 'file', zip_file)
        source.seek(0)
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
            if name == 'site_name' and len(values[name]) > max_site_name_length:
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

