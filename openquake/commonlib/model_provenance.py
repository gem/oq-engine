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

"""Collect and store model-data repository provenance.

The stored JSON has the following structure (with other regions and
submodules omitted):

    {
      "schema_version": 1,
      "generated_at": "2026-09-24T08:12:03+00:00",
      "repositories": [
        {
          "path": "South_America",
          "branch": "v2026.0.0",
          "commit": "d2d1a490fb7c84655120c9ea248ca7c43003181d",
          "detached": false,
          "detached_ref": null,
          "dirty": true,
          "submodules": [
            {
              "path": "South_America/Exposure",
              "branch": null,
              "commit": "2939c61b885f915199dc915ddf3b6f0825b30242",
              "detached": true,
              "detached_ref": "v2026.0.0",
              "dirty": false
            },
            {
              "path": "South_America/Hazard/SAM",
              "branch": "v2026_updates",
              "commit": "8fc4892a514903688207d58fc6135505d3771848",
              "detached": false,
              "detached_ref": null,
              "dirty": false
            },
            {
              "path": "South_America/Vulnerability",
              "branch": null,
              "commit": "f707a91aacc575312a4be729882791f58829ce9c",
              "detached": true,
              "detached_ref": "v2026.0.0",
              "dirty": false
            }
          ]
        },
        {
          "path": "site-models",
          "branch": "master",
          "commit": "c7990624c64dc721b0bfdc1319eba06e11b6b415",
          "detached": false,
          "detached_ref": null,
          "dirty": false,
          "submodules": []
        },
        ...
      ]
    }

The ``dirty`` flag records whether the repository had local changes when
this snapshot was collected. A detached repository is valid; its commit
SHA is authoritative and ``detached_ref`` contains a tag or other readable
reference when one is available.
"""

import json
import logging
import os
from datetime import datetime, timezone

from openquake.baselib import hdf5
from openquake.baselib.gitwrapper import git
from openquake.hazardlib.countries import REGIONS

MODEL_PROVENANCE_KEY = 'model_provenance'
SCHEMA_VERSION = 1


def _submodule_paths(path):
    """Return the direct submodule paths declared by a repository."""
    gitmodules = os.path.join(path, '.gitmodules')
    if not os.path.exists(gitmodules):
        return []
    try:
        output = git(
            path, ['config', '--file', '.gitmodules', '--get-regexp',
                   r'^submodule\..*\.path$'])
    except SystemExit:
        return []
    output = output.strip()
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
        status['commit'] = git(path, ['rev-parse', 'HEAD']).strip()
        ref = git(path, ['rev-parse', '--abbrev-ref', 'HEAD']).strip()
        status['detached'] = ref == 'HEAD'
        status['branch'] = None if status['detached'] else ref
        description = git(
            path, ['describe', '--tags', '--always', 'HEAD']).strip()
        status['detached_ref'] = (
            description if status['detached'] and
            not status['commit'].startswith(description) else None)
        status['dirty'] = bool(git(
            path, ['status', '--porcelain', '--untracked-files=all']).strip())
    except (OSError, SystemExit) as exc:
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
    """Serialize the model provenance as stable, human-readable JSON.

    The document contains a schema version, its UTC generation timestamp,
    and a ``repositories`` list. Each repository entry contains its path,
    full commit SHA, branch, detached-head state, detached reference, and
    dirty-working-tree flag. Regional repositories also contain a
    ``submodules`` list with the same information. If a repository cannot
    be inspected, the entry contains ``status_error`` instead.
    """
    return json.dumps(summary, indent=2, sort_keys=True) + '\n'


def store_model_provenance(dstore, grm_dir):
    """Store model repository provenance in an HDF5 datastore."""
    summary = collect_model_provenance(grm_dir)
    text = _summary_text(summary)
    if MODEL_PROVENANCE_KEY in dstore.hdf5:
        del dstore.hdf5[MODEL_PROVENANCE_KEY]
    dataset = dstore.hdf5.create_dataset(
        MODEL_PROVENANCE_KEY, shape=(), dtype=hdf5.vstr)
    dataset[()] = text
    dataset.attrs['format'] = 'json'
    dataset.attrs['schema_version'] = SCHEMA_VERSION
    return summary


def copy_model_provenance(source_path, dstore):
    """Copy model provenance from an exposure HDF5 to a datastore."""
    try:
        with hdf5.File(source_path, 'r') as source:
            if MODEL_PROVENANCE_KEY not in source:
                return False
            if MODEL_PROVENANCE_KEY in dstore.hdf5:
                del dstore.hdf5[MODEL_PROVENANCE_KEY]
            source.copy(MODEL_PROVENANCE_KEY, dstore.hdf5)
    except (OSError, KeyError) as exc:
        logging.warning('Could not copy model provenance from %s: %s',
                        source_path, exc)
        return False
    return True


def read_model_provenance(dstore):
    """Read model provenance from a datastore, or return ``None``."""
    try:
        value = dstore.getitem(MODEL_PROVENANCE_KEY)[()]
    except KeyError:
        return None
    if isinstance(value, bytes):
        value = value.decode('utf-8')
    return json.loads(value)
