# Copyright (c) 2010-2012, GEM Foundation.
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.


"""Functions for export Uniform Hazard Spectra results from the OpenQuake
database.
"""


import h5py
import numpy
import os

from openquake.db import models
from openquake.export.core import makedirs
from openquake.utils import round_float


#: Format string for HDF5 dataset names
_DS_NAME_FMT = 'lon:%s-lat:%s'
_HDF5_FILE_NAME_FMT = 'uhs_poe:%s.hdf5'
_XML_FILE_NAME = 'uhs.xml'


def _point_to_ds_name(point):
    """Generate a dataset name from a
    :class:`django.contrib.gis.geos.point.Point`. This dataset name is meant to
    be used in UHS HDF5 result files.

    :param point:
        :class:`django.contrib.gis.geos.point.Point` object.
    :returns:
        A dataset name generated from the point's lat/lon values. Example::

            "lon:-179.45-lat:-20.75"

    A simple example:

    >>> from django.contrib.gis.geos.point import Point
    >>> pt = Point(-179.45, -20.75)
    >>> _point_to_ds_name(pt)
    'lon:-179.45-lat:-20.75'

    This function uses :func:`openquake.utils.round_float` to round
    coordinate values. Thus, any coordinate value with more than 7 digits after
    the decimal will be rounded to 7 digits:

    >>> pt = Point(-179.12345675, 79.12345674)
    >>> _point_to_ds_name(pt)
    'lon:-179.1234568-lat:79.1234567'
    """
    return _DS_NAME_FMT % (round_float(point.x), round_float(point.y))


@makedirs
def export_uhs(output, target_dir):
    """Export the specified ``output`` to the ``target_dir``.

    :param output:
        :class:`openquake.db.models.Output` associated with UHS calculation
        results.
    :param str target_dir:
        Destination directory location of the exported files.

    :returns:
        A list of exported file names (including the absolute path to each
        file).
    """
    file_names = []

    uh_spectra = models.UhSpectra.objects.get(output=output.id)

    uh_spectrums = models.UhSpectrum.objects.filter(uh_spectra=uh_spectra.id)

    # accumulate a list of (poe, path) pairs to serialize to NRML XML
    # each `path` is the full path to a result hdf5 file
    nrml_data = []

    for spectrum in uh_spectrums:
        # create a file for each spectrum/poe
        uhs_data = models.UhSpectrumData.objects.filter(
            uh_spectrum=spectrum.id)

        # If there are multiple LT samples/realizations, we'll have multiple
        # records for each site. However, there should only be a 1 dataset per
        # site so we need to 'uniquify'.
        ds_names = list(set([_point_to_ds_name(datum.location)
                             for datum in uhs_data]))

        # Create the empty result file
        file_name = touch_result_hdf5_file(
            target_dir, spectrum.poe, ds_names, uh_spectra.realizations,
            len(uh_spectra.periods))
        file_name = os.path.abspath(file_name)

        nrml_data.append((spectrum.poe, file_name))

        # Now write the actual data
        write_uhs_data(file_name, uhs_data)
        file_names.append(file_name)

    nrml_file_path = os.path.join(target_dir, _XML_FILE_NAME)

    # TODO (lp) port uhs writer to nrml
    nrml_writer.serialize(nrml_data)

    # Don't forget the nrml file:
    file_names.append(os.path.abspath(nrml_file_path))

    return file_names


def touch_result_hdf5_file(target_dir, poe, ds_names, n_realizations,
                           n_periods):
    """Create an empty HDF5 file with appropriately sized datasets. The quanity
    of datasets created is equal to the length of ``ds_names``. Each dataset
    will be a 2D matrix with a number of rows == ``n_realizations`` and number
    of columns == ``n_periods``. Each dataset will be created 'empty'
    (all values == 0.0).

    The datatype for each value is `numpy.float64`.

    :param str target_dir:
        Location to place the new file.
    :param float poe:
        Probability of Exceedance associated with this file. The PoE will be
        used to generate the resulting file name.
    :param list ds_names:
        List strings representing dataset names. 1 dataset will be created for
        each name.

        Note: Each dataset name should be unique.
    :param int n_realizations:
        Number of rows in each dataset.
    :param int n_periods:
        Number of columns in each dataset.

    :returns:
        The full path of the created file.
    """
    file_name = _HDF5_FILE_NAME_FMT % poe
    full_path = os.path.join(target_dir, file_name)

    ds_shape = (n_realizations, n_periods)

    with h5py.File(full_path, 'w') as h5_file:
        for name in ds_names:
            h5_file.create_dataset(name, dtype=numpy.float64, shape=ds_shape)

    return full_path


def write_uhs_data(hdf5_file, uhs_data):
    """Given a path to an empty UHS HDF5 file (see
    :func:`touch_result_hdf5_file`), write data (spectral acceleration
    values) into the correct row in the correct dataset.

    :param str h5df_file:
        Path to the empty HDF5 file. The datasets should already be created.
    :param uhs_data:
        An iterable of :class:`openquake.db.models.UhSpectrumData` objects.
    """
    with h5py.File(hdf5_file, 'a') as h5_file:
        for datum in uhs_data:
            ds_name = _point_to_ds_name(datum.location)
            # The `realization` is the row in the dataset.
            # Each dataset is a 2D matrix of floats.
            h5_file[ds_name][datum.realization] = datum.sa_values
