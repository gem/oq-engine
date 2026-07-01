# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2026 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""Engine: A collection of fundamental functions for initializing and running
calculations."""

import ast
import copy
import logging
import os
import re
import sys
import time

import numpy
import pandas
import toml

try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"
from openquake.baselib import general, hdf5, sap
from openquake.hazardlib import InvalidFile
from openquake.calculators import views
from openquake.commonlib import datastore, logs, readinput
from openquake.commonlib.oqvalidation import OqParam
from openquake.engine.engine import create_jobs, run_jobs

U32 = numpy.uint32
F32 = numpy.float32
MB = 1024 ** 2

OVERRIDABLE_PARAMS = (
    'area_source_discretization',
    'calculation_mode',
    'cache',
    'concurrent_tasks',
    'complex_fault_mesh_spacing',
    'discard_assets',
    'ground_motion_fields',
    'hazard_calculation_id',
    'number_of_logic_tree_samples',
    'ses_per_logic_tree_path',
    'minimum_magnitude',
    'mosaic_model',
    'ps_grid_spacing',
    'postproc_func',
    'postproc_args',
    'postrisk_func',
    'postrisk_args',
    'return_periods',
    'rupture_mesh_spacing'
    'ses_seed',
    'sites',
    'siteid')


def save_workflow(workflow_hdf5, workflow_toml):
    """
    Save ~/.last-workflow
    """
    fname = os.path.expanduser("~/.last-workflow")
    with open(fname, 'w') as f:
        f.write(f'{workflow_toml}\n')
        f.write(f'{workflow_hdf5}\n')


def load_workflow():
    """
    :returns: the last workflow stored
    """
    fname = os.path.expanduser("~/.last-workflow")
    with open(fname) as f:
        toml, hdf5 = list(f)
    ds = datastore.read(fname)
    ds.toml = toml
    return ds


class _Workflow:
    # workflow objects are instantiated by the function `read_many`
    # prefix is empty unless we are in a multi-workflow
    def __init__(self, workflow_toml, defaults, ddic, prefix=''):
        self.workflow_toml = workflow_toml
        self.workflow_dir = os.path.dirname(workflow_toml)
        self.defaults = defaults
        self.description = defaults.pop('description')
        self.checkout = self.defaults.pop('checkout', {})  # repo->branch
        self.may_fail = self.defaults.pop('may_fail', [])
        self.env = defaults.pop('env', {})
        self.override = defaults.pop('override', {})

        # override feature
        if self.override:
            for _, dic in ddic.items():
                for name in dic:
                    if name in self.override:
                        dic[name] = self.override[name]

        # check the repositories exist
        for value in self.checkout:
            repodir = os.path.join(self.workflow_dir, value)
            if not os.path.exists(repodir):
                raise FileNotFoundError(repodir)

        self.inis, self.names = self._inis_names(ddic, prefix)
        check_unique(self.names, workflow_toml)

    def _inis_names(self, ddic, prefix):
        inis = []
        names = []
        self.success = []
        for k, dic in ddic.items():
            assert len(k) <= 20, k
            if k == 'success':
                if isinstance(dic, dict):
                    self.success = [dic]
                elif isinstance(dic, list):
                    self.success = dic
                else:
                    raise ValueError('"success": %s', dic)
                for s in self.success:
                    s['func']  # each success dictionary must contain a func
                self.fix_paths(self.success)
                continue

            assert k[0].isupper(), k
            assert isinstance(dic, dict), dic
            self.fix_paths([dic])
            inis.append(dic)
            names.append(prefix + k)
        return numpy.array(inis), numpy.array(names)

    def fix_paths(self, dicts):
        """
        Expand relative path names to absolute path names
        """
        for dic in dicts:
            for key, val in dic.items():
                if isinstance(val, str) and val.endswith(
                        ('.ini', '.hdf5', '.sqlite')):
                    dic[key] = path = os.path.abspath(
                        os.path.join(self.workflow_dir, val))
                    if 'out' in key and not os.path.exists(path):
                        open(path, 'w').close()  # touch the file

    def validate(self):
        """
        Convert the .inis dictionaries into validated oqparam instances
        """
        assert len(self.inis), self
        oqs = []
        for i, dic in enumerate(self.inis):
            params = readinput.get_params(dic.pop('ini'))
            for param in OVERRIDABLE_PARAMS:
                val = dic.get(param, self.defaults.get(param))
                if val is not None:
                    params[param] = str(val)
            oq = OqParam(**params)
            oq.validate()
            self.inis[i] = params
            oqs.append(oq)
        if 'classical' in oq.calculation_mode:
            for oq in oqs[1:]:
                if oq.retperiods != oqs[0].retperiods:
                    raise InvalidFile(
                        f'{oq.inputs["job_ini"]}: expected return_periods = '
                        f'{oqs[0].retperiods}, got {oq.retperiods}')
        if 'risk' in oq.calculation_mode or 'damage' in oq.calculation_mode:
            for oq in oqs[1:]:
                if oq.eff_time != oqs[0].eff_time:
                    raise NameError(f'Expected eff_time = {oqs[0].eff_time}, '
                                    f'got {oq.eff_time}')
        return oqs

    def to_toml(self):
        """
        :returns: a TOML representation of the Workflow object
        """
        dic = {'workflow': self.defaults}
        for name, ini in zip(self.names, self.inis):
            dic[name] = ini
        dic['success'] = self.success
        return toml.dumps(dic)

    def kfilter(self, regex):
        """
        Reduce the workflow to the jobs matched by the regular expression
        """
        new = copy.copy(self)
        new.inis, new.names = [], []
        for ini, name in zip(self.inis, self.names):
            if regex.search(name):
                new.inis.append(ini)
                new.names.append(name)
        return new

    def __repr__(self):
        return '<Workflow %s>' % self.workflow_toml


# called twice, internally and also externally to Workflow objects
def check_unique(names, workflow_toml):
    uni, cnt = numpy.unique(names, return_counts=1)
    if (cnt > 1).any():
        raise ValueError(f'There are duplicates in {workflow_toml}: '
                         f'{uni[cnt > 1]}')


def read_many(workflow_toml, params, validate=True):
    """
    Read the workflow file and returns a list of workflow dictionaries.
    Set 'workflow_dir', 'success' and 'inis' on each.
    Also expand relative paths to absolute paths for parameters following
    the `_file` name convention.

    :param workflow_toml: path to a workflow file
    :param params: dictionary containg at least workflow_id
    :param validate: if True, validate the OqParam object
    """
    out = []
    prefix = ''
    try:
        with open(workflow_toml, encoding='utf8') as f:
            wfdict = toml.load(f)

        if 'multi' in wfdict:
            multi = wfdict.pop('multi')['workflow']

            # include case
            fnames = multi.pop('include', [])
            if fnames:
                for fname in fnames:
                    out.extend(read_many(fname, multi | params, validate))
                return out

            # regular case
            for prefix, ddic in wfdict.items():
                key, dic = next(iter(ddic.items()))
                if 'ini' not in dic:
                    raise SyntaxError(
                        f'{workflow_toml}: missing ini in {prefix}.{key}')

                wf = _Workflow(workflow_toml, multi | params, ddic, prefix)
                if validate:
                    wf.validate()
                out.append(wf)
        elif 'workflow' in wfdict:
            defaults = wfdict.pop('workflow') | params
            wf = _Workflow(workflow_toml, defaults, wfdict)
            if validate:
                wf.validate()
            out.append(wf)
        else:
            raise InvalidFile('missing [workflow] or [multi.workflow]')
    except Exception as exc:
        print(f'Error while parsing {workflow_toml} {prefix}',
              file=sys.stderr)
        raise exc
    return out


def prepare_workflow(params, workflow_toml, pdb, kfilter):
    """
    Create or retrieve a workflow record and create or update
    the workflow database
    """
    try:
        # retrieve an old workflow
        workflow_id = params['workflow_id']
    except KeyError:
        # create a new workflow
        [wfjob] = create_jobs([{
            'calculation_mode': 'workflow',
            'description': os.path.basename(workflow_toml)}], pdb=pdb)
        workflow_id = params['workflow_id'] = wfjob.calc_id
        new = True
    else:
        wfjob = logs.init({'job_id': workflow_id})
        new = False
    with wfjob:
        workflows = read_many(workflow_toml, params, validate=True)
        if kfilter:
            rx = re.compile(kfilter)
            workflows = [wf.kfilter(rx) for wf in workflows]
            oks = numpy.array([bool(wf.names) for wf in workflows])
            if not any(oks):
                sys.exit(f'No matches for {kfilter}')
        else:
            oks = numpy.ones(len(workflows), bool)
        names = numpy.concatenate([wf.names for wf in workflows])
        n = len(names)
        check_unique(names, workflow_toml)
        logging.info('Running %d workflows: %s', sum(oks),
                     [[str(x) for x in wf.names] for wf in workflows
                      if len(wf.names)])

        wfdic = dict(base_path=os.path.dirname(workflow_toml),
                     calculation_mode='workflow')
        if new:
            descr = workflows[0].description
            dstore = datastore.read(workflow_id, 'w')
            wf_df = pandas.DataFrame(
                dict(name=names,
                     calc_id=[0] * n,
                     status=['created'] * n,
                     size_mb=[0.0] * n)
            ).set_index('name')
            dstore['workflows'] = numpy.array([w.to_toml() for w in workflows])
            dstore.create_df('workflow', wf_df.reset_index())
            arr = numpy.array(['[]' for _ in range(len(workflows))], hdf5.vstr)
            dstore.create_dset('success', arr)
        else:
            # continue an existing workflow
            wfdic['job_id'] = workflow_id
            dstore = datastore.read(workflow_id, 'r+')
            descr = wfjob.get_job().description
        wfjob.workflows = workflows
    dstore['/'].attrs['engine_version'] = general.engine_version()
    
    logs.dbcmd('update_job', workflow_id,
               {'description': f'{os.path.basename(workflow_toml)}: {descr}'})
    return wfjob, dstore, oks


def format_dic(success):
    """
    Format the success dictionary; for instance::

      {'func': 'openquake.engine.postjobs.import_outputs',
       'out_types': ['hcurves', 'hmaps-stats']} =>
      openquake.engine.postjobs.import_outputs(
        out_types=['hcurves', 'hmaps-stats'])
    """
    dic = success.copy()
    func = dic.pop('func')
    kwargs = ', '.join(f'{k}={v!r}' for k, v in dic.items())
    return f'{func}({kwargs})'


def import_task_info(calc_id, name, dstore):
    """
    Import a task_info view into the workflow datastore
    """
    with datastore.read(calc_id) as ds:
        data = views.view('task_info', ds)
        dic = {col: data[col] for col in data.dtype.names}
        dic['job'] = name
        dic['taskname'] = general.decode(
            dic.pop('operation-duration'))
        dic['stddev'] = dic['mean'].astype(F32)
        dic['counts'] = dic['counts'].astype(U32)
        dic['mean'] = dic['mean'].astype(F32)
        dic['min'] = dic['min'].astype(F32)
        dic['max'] = dic['max'].astype(F32)
        dic['slowfac'] = dic['slowfac'].astype(F32)
        dic['calc_id'] = calc_id
        df = pandas.DataFrame(dic)
        dstore.hdf5.import_df('wtask', df, gzip=None)


def run_workflow(workflow_toml, params, concurrent_jobs=None, nodes=1,
                 sbatch=False, notify_to=None, pdb=False, kfilter=''):
    """
    Run sequentially multiple batches of calculations specified by
    workflow files.
    """
    t0 = time.time()
    wfjob, dstore, oks = prepare_workflow(
        params, workflow_toml, pdb, kfilter)
    names = numpy.concatenate([wf.names for wf in wfjob.workflows])
    name2idx = {name: i for i, name in enumerate(names)}
    calc_dset = dstore['workflow/calc_id']
    status_dset = dstore['workflow/status']
    size_dset = dstore['workflow/size_mb']
    successes = [ast.literal_eval(s.decode('utf8')) for s in dstore['success']]
    expected_failures = set()
    with dstore, wfjob:
        n_wfs = oks.sum()
        for wf_no, wf in enumerate(wfjob.workflows):
            # skip workflows not selected
            if not oks[wf_no]:
                continue

            # set the passed environment variables
            for k, v in wf.env.items():
                if k not in os.environ:  # explicitly set variable must win
                    os.environ[k] = str(v)

            if 'oqparam' not in dstore:  # new workflow
                kw = wf.inis[0].copy()
                kw.update(calculation_mode='workflow')
                dstore['oqparam'] = OqParam(**kw)

            failed, calcs, new, new_names = 0, [], [], []
            for name, ini in zip(wf.names, wf.inis):
                idx = name2idx[name]
                if status_dset[idx] == b'complete':
                    # already done; notice the conversion numpy.int64 -> int
                    calcs.append(int(calc_dset[idx]))
                    logging.info(f'{name} already computed')
                else:
                    new.append(ini)
                    new_names.append(name)
            if new:
                one_job = len(wf.names) == 1
                jobs = create_jobs(new, log_level=logging.INFO if
                                   one_job else logging.WARNING,
                                   workflow_id=wfjob.calc_id)
                run_jobs(jobs, concurrent_jobs, nodes, sbatch, notify_to)
                for job, name in zip(jobs, new_names):
                    rec = job.get_job()
                    idx = name2idx[name]
                    calc_dset[idx] = rec.id
                    status_dset[idx] = rec.status
                    size_dset[idx] = rec.size_mb
                    if rec.status == 'failed':
                        if name in wf.may_fail:
                            expected_failures.add(name)
                        else:
                            failed += 1
                    calcs.append(job.calc_id)
                    import_task_info(job.calc_id, name, dstore)
            may_fails = [name in wf.may_fail for name in new_names]
            for success in wf.success:
                if success in successes[wf_no]:
                    logging.info(f'{format_dic(success)} already called')
                elif not failed:
                    logging.info(f'{format_dic(success)}')
                    successes[wf_no].append(success.copy())
                    success['dstore'] = dstore
                    success['calcs'] = calcs
                    success['may_fails'] = may_fails
                    sap.run_func(success)

            if n_wfs > 1:
                logging.warning(f'{os.path.basename(wf.workflow_toml)}: '
                                f'finished step {wf_no+1} of {n_wfs}')
            if failed:
                break
        for wf_no, succ in enumerate(successes):
            dstore['success'][wf_no] = str(succ)  # list of dictionaries
        dt = (time.time() - t0) / 3600.
        save_workflow(dstore.filename, os.path.abspath(workflow_toml))
        logging.info(f'Finished workflow {dstore.filename} in {dt:.2} hours')
        if failed:
            mask = status_dset[:] == b'failed'
            dic = {str(name): int(calc) for name, calc in
                   zip(names[mask], calc_dset[:][mask])
                   if name not in expected_failures}
            raise RuntimeError(f'Jobs failed unexpectedly: {dic}')
    return wfjob.calc_id
