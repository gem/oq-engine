package org.gem.engine.hazard.parsers;

import org.dom4j.Namespace;
import org.dom4j.QName;

public class NRMLConstants
{

    private NRMLConstants()
    {
        // No need to instantiate this class
    }

    // Namespaces
    public static final Namespace GML_NAMESPACE = new Namespace("gml",
            "http://www.opengis.net/gml");

    public static final Namespace QML_NAMESPACE = new Namespace("qml",
            "http://quakeml.org/xmlns/quakeml/1.1");

    public static final Namespace NRML_NAMESPACE = new Namespace("",
            "http://openquake.org/xmlns/nrml/0.1");

    // Properties are in the form NAMESPACE_PROPERTYNAME

    // GML properties
    public static final QName GML_LINE_STRING = new QName("LineString",
            GML_NAMESPACE);

    public static final QName GML_NAME = new QName("name", GML_NAMESPACE);
    public static final QName GML_SRS_NAME = new QName("srsName", GML_NAMESPACE);
    public static final QName GML_POS_LIST = new QName("posList", GML_NAMESPACE);
    public static final QName GML_ID = new QName("id", GML_NAMESPACE);
    public static final QName GML_POINT = new QName("Point", GML_NAMESPACE);
    public static final QName GML_POS = new QName("pos", GML_NAMESPACE);

    // NRML Properties
    public static final QName NRML_SOURCE_MODEL = new QName("sourceModel",
            NRML_NAMESPACE);

    public static final QName NRML_SIMPLE_FAULT_SOURCE = new QName(
            "simpleFaultSource", NRML_NAMESPACE);

    public static final QName NRML_POINT_SOURCE = new QName("pointSource",
            NRML_NAMESPACE);

    public static final QName NRML_TECTONIC_REGION = new QName(
            "tectonicRegion", NRML_NAMESPACE);

    public static final QName NRML_EDI_MFD = new QName(
            "evenlyDiscretizedIncrementalMFD", NRML_NAMESPACE);

    public static final QName NRML_BIN_SIZE = new QName("binSize",
            NRML_NAMESPACE);

    public static final QName NRML_SIMPLE_FAULT_GEOMETRY = new QName(
            "simpleFaultGeometry", NRML_NAMESPACE);

    public static final QName NRML_FAULT_TRACE = new QName("faultTrace",
            NRML_NAMESPACE);

    public static final QName NRML_UPPER_SEISM_DEP = new QName(
            "upperSeismogenicDepth", NRML_NAMESPACE);

    public static final QName NRML_LOWER_SEISM_DEP = new QName(
            "lowerSeismogenicDepth", NRML_NAMESPACE);

    public static final QName NRML_CONFIG = new QName("config", NRML_NAMESPACE);
    public static final QName NRML = new QName("nrml", NRML_NAMESPACE);
    public static final QName NRML_RAKE = new QName("rake", NRML_NAMESPACE);
    public static final QName NRML_MIN_VAL = new QName("minVal", NRML_NAMESPACE);
    public static final QName NRML_TYPE = new QName("type", NRML_NAMESPACE);
    public static final QName NRML_DIP = new QName("dip", NRML_NAMESPACE);

    public static final QName NRML_POINT_LOCATION = new QName("location",
            NRML_NAMESPACE);

}
