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
jpype config stuff for Java NSHMP stuff
"""


import os
from openquake import logs

LOG = logs.LOG

JAVA_NAMESPACE = "org.gem.engine.hazard.models.nshmp.us."
JAVA_CLASS = JAVA_NAMESPACE+ "NshmpUsData"
BOUNDING_BOX = (24.6, 50.0, -125.0, -65.5)
# BOUNDING_BOX = (35.0, 35.0, -120, -120.0)

JAVA_MODELS = [(JAVA_NAMESPACE +"NshmpWusFaultData", "WUS/WUSfaults"),
                (JAVA_NAMESPACE +"NshmpCaliforniaFaultData", "CA/CA_faults"),
                (JAVA_NAMESPACE +"NshmpCascadiaSubductionData", "Cascadia"),
                (JAVA_NAMESPACE +"NshmpCeusFaultData", "CEUS/CEUS.faults"),
                (JAVA_NAMESPACE +"NewNshmpWusGridData", "WUS/WUSmap"),
                (JAVA_NAMESPACE +"NewNshmpCaliforniaGridData", "CA/CA_map"),
                (JAVA_NAMESPACE +"NewNshmpCeusGridData", "CEUS/CEUS.map.input"),
                ]

def init_paths(base_path, jpype):
    """ Init the java paths """

    for class_name, subdir in JAVA_MODELS:
        path = os.path.abspath(os.path.join(base_path, subdir))
        java_class = jpype.JClass(class_name)
        LOG.debug("Setting inDir on %s to %s", class_name, path+"/")
        java_class.inDir = path+"/"

