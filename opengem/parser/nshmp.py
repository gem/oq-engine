
import os
from opengem import logs

LOG = logs.LOG

JAVA_NAMESPACE = "org.gem.engine.hazard.models.nshmp.us."
JAVA_CLASS = JAVA_NAMESPACE+ "NshmpUsData"
BOUNDING_BOX = (24.6, 50.0, -125.0, -65.5)
# BOUNDING_BOX = (35.0, 35.0, -120, -120.0)

def init_paths(base_path, jpype):
    for class_name, subdir in [("NshmpWusFaultData", "WUS/WUSfaults"), 
                                ("NshmpCaliforniaFaultData", "CA/CA_faults"),
                                ("NshmpCascadiaSubductionData", "Cascadia"),
                                ("NshmpCeusFaultData", "CEUS/CEUS.faults"),
                                ("NewNshmpWusGridData", "WUS/WUSmap"),
                                ("NewNshmpCaliforniaGridData", "CA/CA_maps"),
                                ("NewNshmpCeusGridData", "CEUS/CEUS.map.input"),
                                ]:
        path = os.path.abspath("%s/%s" % (base_path, subdir))
        java_class = jpype.JClass(JAVA_NAMESPACE + class_name)
        LOG.debug("Setting inDir on %s to %s", class_name, path+"/")
        java_class.inDir = path+"/"
    
