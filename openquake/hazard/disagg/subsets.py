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
def magpmf(site, full_matrix,
           lat_bin_edges, lon_bin_edges, distance_bin_edges,
           nlat, nlon, nmag, neps, ntrt, ndist):
    shape = [nmag - 1]
    ds = numpy.zeros(shape, DATA_TYPE)
    for i in xrange(nmag - 1):
        ds[i] = sum(full_matrix[j][k][i][l][m]
                    for j in xrange(nlat - 1)
                    for k in xrange(nlon - 1)
                    for l in xrange(neps - 1)
                    for m in xrange(ntrt))
    return ds

@pmf
def distpmf(site, full_matrix,
            lat_bin_edges, lon_bin_edges, distance_bin_edges,
            nlat, nlon, nmag, neps, ntrt, ndist):
    ndist = len(distance_bin_edges)
    shape = [ndist - 1]
    ds = numpy.zeros(shape, DATA_TYPE)
    slat, slon = site
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            for k in xrange(nmag - 1):
                for l in xrange(neps - 1):
                    for m in xrange(ntrt):
                        meanlat = (lat_bin_edges[i] + lat_bin_edges[i + 1]) / 2
                        meanlon = (lon_bin_edges[j] + lon_bin_edges[j + 1]) / 2
                        dist = hdistance(meanlat, meanlon, slat, slon)
                        if dist < distance_bin_edges[0] \
                                or dist > distance_bin_edges[-1]:
                            continue
                        for ii in xrange(ndist - 1):
                            if dist >= distance_bin_edges[ii] \
                                    and dist < distance_bin_edges[ii + 1]:
                                break
                        ds[ii] += full_matrix[i][j][k][l][m]
    return ds

@pmf
def trtpmf(site, full_matrix,
           lat_bin_edges, lon_bin_edges, distance_bin_edges,
           nlat, nlon, nmag, neps, ntrt, ndist):
    shape = [ntrt]
    ds = numpy.zeros(shape, DATA_TYPE)
    for i in xrange(ntrt):
        ds[i] = sum(full_matrix[j][k][l][m][i]
                    for j in xrange(nlat - 1)
                    for k in xrange(nlon - 1)
                    for l in xrange(nmag - 1)
                    for m in xrange(neps - 1))
    return ds

@pmf
def magdistpmf(site, full_matrix,
               lat_bin_edges, lon_bin_edges, distance_bin_edges,
               nlat, nlon, nmag, neps, ntrt, ndist):
    ndist = len(distance_bin_edges)
    shape = [nmag - 1, ndist - 1]
    ds = numpy.zeros(shape, DATA_TYPE)
    slat, slon = site
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            for k in xrange(nmag - 1):
                for l in xrange(neps - 1):
                    for m in xrange(ntrt):
                        meanlat = (lat_bin_edges[i] + lat_bin_edges[i + 1]) / 2
                        meanlon = (lon_bin_edges[j] + lon_bin_edges[j + 1]) / 2
                        dist = hdistance(meanlat, meanlon, slat, slon)
                        if dist < distance_bin_edges[0] \
                                or dist > distance_bin_edges[-1]:
                            continue
                        for ii in xrange(ndist - 1):
                            if dist >= distance_bin_edges[ii] \
                                    and dist < distance_bin_edges[ii + 1]:
                                break
                        ds[k][ii] += full_matrix[i][j][k][l][m]
    return ds

@pmf
def magdistepspmf(site, full_matrix,
                  lat_bin_edges, lon_bin_edges, distance_bin_edges,
                  nlat, nlon, nmag, neps, ntrt, ndist):
    shape = [nmag - 1, ndist - 1, ntrt - 1]
    ds = numpy.zeros(shape, DATA_TYPE)
    slat, slon = site
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            for k in xrange(nmag - 1):
                for l in xrange(neps - 1):
                    for m in xrange(ntrt):
                        meanlat = (lat_bin_edges[i] + lat_bin_edges[i + 1]) / 2
                        meanlon = (lon_bin_edges[j] + lon_bin_edges[j + 1]) / 2
                        dist = hdistance(meanlat, meanlon, slat, slon)
                        if dist < distance_bin_edges[0] \
                                or dist > distance_bin_edges[-1]:
                            continue
                        for ii in xrange(ndist - 1):
                            if dist >= distance_bin_edges[ii] \
                                    and dist < distance_bin_edges[ii + 1]:
                                break
                        ds[k][ii][l] += full_matrix[i][j][k][l][m]
    return ds

@pmf
def latlonpmf(site, full_matrix,
              lat_bin_edges, lon_bin_edges, distance_bin_edges,
              nlat, nlon, nmag, neps, ntrt, ndist):
    shape = [nlat - 1, nlon - 1]
    ds = numpy.zeros(shape, DATA_TYPE)
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            ds[i][j] = sum(full_matrix[i][j][k][l][m]
                           for k in xrange(nmag - 1)
                           for l in xrange(neps - 1)
                           for m in xrange(ntrt))
    return ds

@pmf
def latlonmagpmf(site, full_matrix,
                 lat_bin_edges, lon_bin_edges, distance_bin_edges,
                 nlat, nlon, nmag, neps, ntrt, ndist):
    shape = [nlat - 1, nlon - 1, nmag - 1]
    ds = numpy.zeros(shape, DATA_TYPE)
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            for k in xrange(nmag - 1):
                ds[i][j][k] = sum(full_matrix[i][j][k][l][m]
                                  for l in xrange(neps - 1)
                                  for m in xrange(ntrt))
    return ds

@pmf
def latlonmagepspmf(site, full_matrix,
                    lat_bin_edges, lon_bin_edges, distance_bin_edges,
                    nlat, nlon, nmag, neps, ntrt, ndist):
    shape = [nlat - 1, nlon - 1, nmag - 1, neps - 1]
    ds = numpy.zeros(shape, DATA_TYPE)
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            for k in xrange(nmag - 1):
                for l in xrange(neps - 1):
                    ds[i][j][k][l] = sum(full_matrix[i][j][k][l][m]
                                         for m in xrange(ntrt))
    return ds

@pmf
def magtrtpmf(site, full_matrix,
              lat_bin_edges, lon_bin_edges, distance_bin_edges,
              nlat, nlon, nmag, neps, ntrt, ndist):
    shape = [nmag - 1, ntrt]
    ds = numpy.zeros(shape, DATA_TYPE)
    for i in xrange(nmag - 1):
        for j in xrange(ntrt):
            ds[i][j] = sum(full_matrix[k][l][i][m][j]
                           for k in xrange(nlat - 1)
                           for l in xrange(nlon - 1)
                           for m in xrange(neps - 1))
    return ds

@pmf
def latlontrtpmf(site, full_matrix,
                 lat_bin_edges, lon_bin_edges, distance_bin_edges,
                 nlat, nlon, nmag, neps, ntrt, ndist):
    shape = [nlat - 1, nlon - 1, ntrt]
    ds = numpy.zeros(shape, DATA_TYPE)
    for i in xrange(nlat - 1):
        for j in xrange(nlon - 1):
            for k in xrange(ntrt):
                ds[i][j][k] = sum(full_matrix[i][j][l][m][k]
                                  for l in xrange(nmag - 1)
                                  for m in xrange(neps - 1))
    return ds


@task
def extract_subsets(site, full_matrix_path,
                    lat_bin_edges, lon_bin_edges,
                    mag_bin_edges, eps_bin_edges,
                    distance_bin_edges,
                    target_path, subsets):
    nlat = len(lat_bin_edges)
    nlon = len(lon_bin_edges)
    nmag = len(mag_bin_edges)
    neps = len(eps_bin_edges)
    ntrt = 5
    ndist = len(distance_bin_edges)
    subsets = set(subsets)
    assert subsets
    assert not subsets - set(SUBSET_EXTRACTORS)
    if FULL_MATRIX_DS_NAME in subsets:
        shutil.copyfile(full_matrix_path, target_path)
    with h5py.File(full_matrix_path, 'r') as source:
        full_matrix = source[FULL_MATRIX_DS_NAME]
        with h5py.File(target_path, 'a') as target:
            for subset_type in subsets:
                extractor = SUBSET_EXTRACTORS[subset_type]
                dataset = extractor(
                    site, full_matrix,
                    lat_bin_edges, lon_bin_edges, distance_bin_edges,
                    nlat, nlon, nmag, neps, ntrt, ndist
                )
                target.create_dataset(subset_type, data=dataset)
