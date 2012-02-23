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


from openquake.db import models

def export_uhs(output, target_dir):
    """ """

    uh_spectra = models.UhSpectra.objects.get(output=output.id)

    calculation = output.oq_calculation
    job_profile = oq_calculation.oq_job_profile

    uh_spectrums = models.UhSpectrum.objects.filter(uh_spectra=uh_spectra.id)

    for spectrum in uh_spectrums:
        # create a file for each spectrum/poe
        spectrum.poe


def touch_result_hdf5_file():
    pass
