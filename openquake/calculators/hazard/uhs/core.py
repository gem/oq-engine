# Copyright (c) 2010-2012, GEM Foundation.
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
from django.db import transaction
from django.contrib.gis.geos.geometry import GEOSGeometry

from openquake import java
from openquake.engine import CalculationProxy
from openquake.java import list_to_jdouble_array
from openquake.logs import LOG
from openquake.utils import config
from openquake.utils import tasks as utils_tasks
from openquake.db.models import Output
from openquake.db.models import UhSpectra
from openquake.db.models import UhSpectrum
from openquake.db.models import UhSpectrumData
from openquake.calculators.hazard.general import generate_erf
from openquake.calculators.hazard.general import generate_gmpe_map
from openquake.calculators.hazard.general import get_iml_list
from openquake.calculators.hazard.general import set_gmpe_params


@task(ignore_result=True)
def touch_result_file(job_id, path, sites, realizations, n_periods):
    """Given a path (including the file name), create an empty HDF5 result file
    containing 1 empty data set for each site. Each dataset will be a matrix
    with the number of rows = number of samples and number of cols = number of
    UHS periods.

    :param int job_id:
        ID of the job record in the DB/KVS.
    :param str path:
        Location (including a file name) on an NFS where the empty
        result file should be created.
    :param sites:
        List of :class:`openquake.shapes.Site` objects.
    :param int realizations:
        Number of logic tree samples (the y-dimension of each dataset).
    :param int n_periods:
        Number of UHS periods (the x-dimension of each dataset).
    """
    utils_tasks.get_running_calculation(job_id)
    # TODO: Generate the sites, instead of pumping them through rabbit?
    with h5py.File(path, 'w') as h5_file:
        for site in sites:
            ds_name = 'lon:%s-lat:%s' % (site.longitude, site.latitude)
            ds_shape = (realizations, n_periods)
            h5_file.create_dataset(ds_name, dtype=numpy.float64,
                                   shape=ds_shape)


@task(ignore_results=True)
@java.unpack_exception
def compute_uhs_task(job_id, realization, site):
    """Compute Uniform Hazard Spectra for a given site of interest and 1 or
    more Probability of Exceedance values. The bulk of the computation will
    be done by utilizing the `UHSCalculator` class in the Java code.

    UHS results will be written directly to the database.

    :param int job_id:
        ID of the job record in the DB/KVS.
    :param realization:
        Logic tree sample number (from 1 to N, where N is the
        NUMBER_OF_LOGIC_TREE_SAMPLES param defined in the job config.
    :param site:
        The site of interest (a :class:`openquake.shapes.Site` object).
    """
    calc_proxy = utils_tasks.get_running_calculation(job_id)

    log_msg = (
        "Computing UHS for job_id=%s, site=%s, realization=%s."
        " UHS results will be serialized to the database.")
    log_msg %= (calc_proxy.job_id, site, realization)
    LOG.info(log_msg)

    uhs_results = compute_uhs(calc_proxy, site)

    write_uhs_spectrum_data(calc_proxy, realization, site, uhs_results)


def compute_uhs(the_job, site):
    """Given a `CalculationProxy` and a site of interest, compute UHS. The Java
    `UHSCalculator` is called to do perform the core computation.

    :param the_job:
        :class:`openquake.engine.CalculationProxy` instance.
    :param site:
        :class:`openquake.shapes.Site` instance.
    :returns:
        An `ArrayList` (Java object) of `UHSResult` objects, one per PoE.
    """

    periods = list_to_jdouble_array(the_job['UHS_PERIODS'])
    poes = list_to_jdouble_array(the_job['POES'])
    imls = get_iml_list(the_job['INTENSITY_MEASURE_LEVELS'],
                        the_job['INTENSITY_MEASURE_TYPE'])
    max_distance = the_job['MAXIMUM_DISTANCE']

    cache = java.jclass('KVS')(
        config.get('kvs', 'host'),
        int(config.get('kvs', 'port')))

    erf = generate_erf(the_job.job_id, cache)
    gmpe_map = generate_gmpe_map(the_job.job_id, cache)
    set_gmpe_params(gmpe_map, the_job.params)

    uhs_calc = java.jclass('UHSCalculator')(periods, poes, imls, erf, gmpe_map,
                                            max_distance)

    uhs_results = uhs_calc.computeUHS(
        site.latitude,
        site.longitude,
        the_job['VS30_TYPE'],
        the_job['REFERENCE_VS30_VALUE'],
        the_job['DEPTHTO1PT0KMPERSEC'],
        the_job['REFERENCE_DEPTH_TO_2PT5KM_PER_SEC_PARAM'])

    return uhs_results


@transaction.commit_on_success(using='reslt_writer')
def write_uh_spectra(calc_proxy):
    """Write the top-level Uniform Hazard Spectra calculation results records
    to the database.

    In the workflow of the UHS calculator, this should be written prior to the
    execution of the main calculation. (See
    :method:`openquake.calculators.base.Calculator.pre_execute`.)

    This function writes:
    * 1 record to uiapi.output
    * 1 record to hzrdr.uh_spectra
    * 1 record to hzrdr.uh_spectrum, per PoE defined in the calculation config

    :param calc_proxy:
        :class:`openquake.engine.CalculationProxy` instance for the current
        UHS calculation.
    """
    oq_job_profile = calc_proxy.oq_job_profile
    oq_calculation = calc_proxy.oq_calculation

    output = Output(
        owner=oq_calculation.owner,
        oq_calculation=oq_calculation,
        display_name='UH Spectra for calculation id %s' % oq_calculation.id,
        db_backed=True,
        output_type='uh_spectra')
    output.save()

    uh_spectra = UhSpectra(
        output=output,
        timespan=oq_job_profile.investigation_time,
        realizations=oq_job_profile.realizations,
        periods=oq_job_profile.uhs_periods)
    uh_spectra.save()

    for poe in oq_job_profile.poes:
        uh_spectrum = UhSpectrum(uh_spectra=uh_spectra, poe=poe)
        uh_spectrum.save()


@transaction.commit_on_success(using='reslt_writer')
def write_uhs_spectrum_data(calc_proxy, realization, site, uhs_results):
    """Write UHS results for a single ``site`` and ``realization`` to the
    database.

    :param calc_proxy:
        :class:`openquake.engine.CalculationProxy` instance for a UHS
        calculation.
    :param int realization:
       The realization number (from 0 to N, where N is the number of logic tree
        samples defined in the calculation config) for which these results have
        been computed.
    :param site:
        :class:`openquake.shapes.Site` instance.
    :param uhs_results:
        List of `UHSResult` jpype Java objects, one for each PoE defined in the
        calculation configuration.
    """
    # Get the top-level uh_spectra record for this calculation:
    oq_calculation = calc_proxy.oq_calculation
    uh_spectra = UhSpectra.objects.get(
        output__oq_calculation=oq_calculation.id)

    location = GEOSGeometry(site.point.to_wkt())

    for result in uhs_results:
        poe = result.getPoe()
        # Get the uh_spectrum record to which the current result belongs.
        # Remember, each uh_spectrum record is associated with a partiuclar
        # PoE.
        uh_spectrum = UhSpectrum.objects.get(uh_spectra=uh_spectra.id, poe=poe)

        # getUhs() yields a Java Double[] of SA (Spectral Acceleration) values
        sa_values = [x.value for x in result.getUhs()]

        uh_spectrum_data = UhSpectrumData(
            uh_spectrum=uh_spectrum, realization=realization,
            sa_values=sa_values, location=location)
        uh_spectrum_data.save()
