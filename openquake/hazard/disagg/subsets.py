# Copyright (c) 2010-2011, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# only, as published by the Free Software Foundation.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License version 3 for more details
# (a copy is included in the LICENSE file that accompanied this code).
#
# You should have received a copy of the GNU Lesser General Public License
# version 3 along with OpenQuake.  If not, see
# <http://www.gnu.org/licenses/lgpl-3.0.txt> for a copy of the LGPLv3 License.

"""
Celery tasks for extracting subset data from 5D result matrices.
"""

import shutil

import numpy
from celery.task import task
import h5py

from openquake.shapes import hdistance


FULL_MATRIX_DS_NAME = 'fulldisaggmatrix'
DATA_TYPE = numpy.float64

SUBSET_EXTRACTORS = {}


def pmf(func):
    SUBSET_EXTRACTORS[func.func_name] = func
    return func

@pmf
def magpmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    ds_name = 'magpmf'
    shape = [nmag - 1]
    ds = target_file.create_dataset(ds_name, shape, DATA_TYPE, fillvalue=0)
    for i in xrange(nmag - 1):
        ds[i] = sum(full_matrix[j][k][i][l][m]
                    for j in xrange(nlat - 1)
                    for k in xrange(nlot - 1)
                    for l in xrange(neps - 1)
                    for m in xrange(ntrt))

@pmf
def distpmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    # TODO: implement
    pass

@pmf
def trtpmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    ds_name = 'trtpmf'
    shape = [ntrt]
    ds = target_file.create_dataset(ds_name, shape, DATA_TYPE, fillvalue=0)
    for i in xrange(ntrt):
        ds[i] = sum(full_matrix[j][k][l][m][i]
                    for j in xrange(nlat - 1)
                    for k in xrange(nlot - 1)
                    for l in xrange(nmag - 1)
                    for m in xrange(neps - 1))

@pmf
def magdistpmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    # TODO: implement
    pass

@pmf
def magdistepspmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    # TODO: implement
    pass

@pmf
def latlonpmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    ds_name = 'latlonpmf'
    shape = [nlat - 1, nlon - 1]
    ds = target_file.create_dataset(ds_name, shape, DATA_TYPE, fillvalue=0)
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            ds[i][j] = sum(full_matrix[i][j][k][l][m]
                           for k in xrange(nmag - 1)
                           for l in xrange(neps - 1)
                           for m in xrange(ntrt))

@pmf
def latlonmagpmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    ds_name = 'latlonmagpmf'
    shape = [nlat - 1, nlon - 1, nmag - 1]
    ds = target_file.create_dataset(ds_name, shape, DATA_TYPE, fillvalue=0)
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            for k in xrange(nmag - 1):
                ds[i][j][k] = sum(full_matrix[i][j][k][l][m]
                                  for l in xrange(neps - 1)
                                  for m in xrange(ntrt))

@pmf
def latlonmagepspmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    ds_name = 'latlonmagepspmf'
    shape = [nlat - 1, nlon - 1, nmag - 1, neps - 1]
    ds = target_file.create_dataset(ds_name, shape, DATA_TYPE, fillvalue=0)
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            for k in xrange(nmag - 1):
                for l in xrange(neps - 1):
                    ds[i][j][k][l] = sum(full_matrix[i][j][k][l][m]
                                         for m in xrange(ntrt))

@pmf
def magtrtpmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    ds_name = 'magtrtpmf'
    shape = [nmag - 1, ntrt]
    ds = target_file.create_dataset(ds_name, shape, DATA_TYPE, fillvalue=0)
    for i in xrange(nmag - 1):
        for j in xrange(ntrt):
            ds[i][j] = sum(full_matrix[k][l][i][m][j]
                           for k in xrange(nlat - 1)
                           for l in xrange(nlon - 1)
                           for m in xrange(neps - 1))

@pmf
def latlontrtpmf(full_matrix, target_file, nlat, nlon, nmag, neps, ntrt):
    ds_name = 'latlontrtpmf'
    shape = [nlat - 1, nlon - 1, ntrt]
    ds = target_file.create_dataset(ds_name, shape, DATA_TYPE, fillvalue=0)
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            for k in xrange(ntrt):
                ds[i][j][k] = sum(full_matrix[i][j][l][m][k]
                                  for l in xrange(nmag - 1)
                                  for m in xrange(neps - 1))



@task
def extract_subsets(full_matrix_path, target_path, dims, subsets):
    assert len(dims) == 5
    subsets = set(subsets)
    assert subsets
    assert not subsets - set(SUBSET_EXTRACTORS)
    if FULL_MATRIX_DS_NAME in subsets:
        shutil.copyfile(full_matrix_path, target_path)
    with h5py.File(full_matrix_path, 'r') as source:
        full_matrix = source[FULL_MATRIX_DS_NAME]
        with h5py.File(target_path, 'w+') as target:
            for subset_type in subsets:
                extractor = SUBSET_EXTRACTORS[subset_type]
                extractor(full_matrix, target, *dims)
