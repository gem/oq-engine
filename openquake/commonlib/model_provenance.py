# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026, GEM Foundation
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

"""Collect and store model-data repository provenance."""

import json
import logging
import os
import subprocess
from datetime import datetime, timezone

from openquake.baselib import hdf5
from openquake.hazardlib.countries import REGIONS

MODEL_PROVENANCE = 'model_provenance'
SCHEMA_VERSION = 1


class ModelProvenanceError(Exception):
    """Raised when repository provenance cannot be read."""


def _git(path, *args, optional=False):
    """Run Git in *path* and return its stripped standard output."""
    proc = subprocess.run(
        ['git', *args], cwd=path, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode:
        if optional:
            return None
        message = proc.stderr.strip() or 'git command failed'
        raise ModelProvenanceError(f'{path}: {message}')
    return proc.stdout.strip()


def _submodule_paths(path):
    """Return the direct submodule paths declared by a repository."""
    gitmodules = os.path.join(path, '.gitmodules')
    if not os.path.exists(gitmodules):
        return []
    output = _git(
        path, 'config', '--file', '.gitmodules', '--get-regexp',
        r'^submodule\..*\.path$', optional=True)
    if not output:
        return []
    paths = []
    for line in output.splitlines():
        _name, submodule_path = line.split(None, 1)
        paths.append(submodule_path)
    return sorted(paths)


def _repository_status(path, relative_path):
    """Return the provenance of one repository."""
    status = {'path': relative_path}
    try:
        status['commit'] = _git(path, 'rev-parse', 'HEAD')
        ref = _git(path, 'rev-parse', '--abbrev-ref', 'HEAD')
        status['detached'] = ref == 'HEAD'
        status['branch'] = None if status['detached'] else ref
        status['detached_ref'] = (
            _git(path, 'describe', '--tags', '--exact-match', 'HEAD',
                 optional=True) if status['detached'] else None)
        status['dirty'] = bool(
            _git(path, 'status', '--porcelain',
                 '--untracked-files=all'))
    except (OSError, ModelProvenanceError) as exc:
        status['status_error'] = str(exc)
    return status


def _repository_entry(path, relative_path):
    """Return a repository and the statuses of its direct submodules."""
    entry = _repository_status(path, relative_path)
    submodules = []
    for submodule_path in _submodule_paths(path):
        full_path = os.path.join(path, submodule_path)
        relative = os.path.join(relative_path, submodule_path)
        submodules.append(_repository_status(full_path, relative))
    entry['submodules'] = submodules
    return entry


def collect_model_provenance(grm_dir):
    """Collect provenance from the repositories used by the global model."""
    repositories = []
    paths = list(REGIONS) + ['site-models']
    for relative_path in paths:
        path = os.path.join(grm_dir, relative_path)
        if os.path.isdir(path):
            repositories.append(_repository_entry(path, relative_path))
    return {
        'schema_version': SCHEMA_VERSION,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'repositories': repositories,
    }


def _summary_text(summary):
    """Serialize a summary in a stable, human-readable form."""
    return json.dumps(summary, indent=2, sort_keys=True) + '\n'


def store_model_provenance(dstore, grm_dir):
    """Store model repository provenance in an HDF5 datastore."""
    summary = collect_model_provenance(grm_dir)
    text = _summary_text(summary)
    if MODEL_PROVENANCE in dstore.hdf5:
        del dstore.hdf5[MODEL_PROVENANCE]
    dataset = dstore.hdf5.create_dataset(
        MODEL_PROVENANCE, shape=(), dtype=hdf5.vstr)
    dataset[()] = text
    dataset.attrs['format'] = 'json'
    dataset.attrs['schema_version'] = SCHEMA_VERSION
    return summary


def copy_model_provenance(source_path, dstore):
    """Copy model provenance from an exposure HDF5 to a datastore."""
    try:
        with hdf5.File(source_path, 'r') as source:
            if MODEL_PROVENANCE not in source:
                return False
            if MODEL_PROVENANCE in dstore.hdf5:
                del dstore.hdf5[MODEL_PROVENANCE]
            source.copy(MODEL_PROVENANCE, dstore.hdf5)
    except (OSError, KeyError) as exc:
        logging.warning('Could not copy model provenance from %s: %s',
                        source_path, exc)
        return False
    return True


def read_model_provenance(dstore):
    """Read model provenance from a datastore, or return ``None``."""
    try:
        value = dstore.getitem(MODEL_PROVENANCE)[()]
    except KeyError:
        return None
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    return json.loads(value)
