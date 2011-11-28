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


"""Core functionality of the Uniform Hazard Spectra calculator."""


import h5py
import numpy

from celery.task import task

from openquake import java


@task(ignore_result=True)
def touch_result_file(path, sites, n_samples, n_periods):
    """Given a path (including the file name), create an empty HDF5 result file
    containing 1 empty data set for each site. Each dataset will be a matrix
    with the number of rows = number of samples and number of cols = number of
    UHS periods.

    :param str path:
        Location (including a file name) on an NFS where the empty
        result file should be created.
    :param sites:
        List of :class:`openquake.shapes.Site` objects.
    :param int n_samples:
        Number of logic tree samples (the y-dimension of each dataset).
    :param int n_periods:
        Number of UHS periods (the x-dimension of each dataset).
    """
    with h5py.File(path, 'w') as h5_file:
        for site in sites:
            ds_name = 'lon:%s-lat:%s' % (site.longitude, site.latitude)
            ds_shape = (n_samples, n_periods)
            h5_file.create_dataset(ds_name, dtype=numpy.float64,
                                   shape=ds_shape)


@task(ignore_results=True)
@java.unpack_exception
def compute_uhs(result_path, sample, site, poes):
    """Compute Uniform Hazard Spectra for a given site of interest and 1 or
    more Probability of Exceedance values. The bulk of the computation will
    be done by utilizing the `UHSCalculator` class in the Java code.

    UHS results (for each poe) will be written as a 1D array into temporary
    HDF5 files. (The files will later be collected and 'reduced' into final
    result files.)

    :param result_dir:
        NFS result directory path. For each poe, a subfolder will be created to
        contain intermediate calculation results. (Each call to this task will
        generate 1 result file per poe.
    :param sample:
        Logic tree sample number (from 1 to N, where N is the
        NUMBER_OF_LOGIC_TREE_SAMPLES param defined in the job config.
    :param site:
        The site of interest (a :class:`openquake.shapes.Site` object).
    :param poes:
        List of Probability of Exceedance values (as floats). This function
        will compute 1 UHS curve per poe.
    :returns:
        A list of the resulting file names (1 per poe).
    """
