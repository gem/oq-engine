package org.gem.engine.hazard.parsers;

import org.dom4j.Namespace;
import org.dom4j.QName;

public class NRMLConstants {

    private NRMLConstants() {
        // No need to instantiate this class
    }

    // Namespaces
    public static final Namespace GML_NAMESPACE =
            new Namespace("gml", "http://www.opengis.net/gml");

    public static final Namespace QML_NAMESPACE =
            new Namespace("qml", "http://quakeml.org/xmlns/quakeml/1.1");

    public static final Namespace NRML_NAMESPACE =
            new Namespace("", "http://openquake.org/xmlns/nrml/0.1");

    // Properties are in the form NAMESPACE_PROPERTYNAME

    // GML Properties
    public static final QName GML_LINE_STRING =
            new QName("LineString", GML_NAMESPACE);

    public static final QName GML_NAME = new QName("name", GML_NAMESPACE);

    public static final QName GML_SRS_NAME =
            new QName("srsName", GML_NAMESPACE);

    public static final QName GML_POS_LIST =
            new QName("posList", GML_NAMESPACE);

    public static final QName GML_ID = new QName("id", GML_NAMESPACE);
    public static final QName GML_POINT = new QName("Point", GML_NAMESPACE);
    public static final QName GML_POS = new QName("pos", GML_NAMESPACE);

    public static final QName GML_EXTERIOR =
            new QName("exterior", GML_NAMESPACE);

    public static final QName GML_POLYGON = new QName("Polygon", GML_NAMESPACE);

    public static final QName GML_LINEAR_RING =
            new QName("LinearRing", GML_NAMESPACE);

    // NRML Properties
    public static final QName NRML_SOURCE_MODEL =
            new QName("sourceModel", NRML_NAMESPACE);

    public static final QName NRML_SIMPLE_FAULT_SOURCE =
            new QName("simpleFaultSource", NRML_NAMESPACE);

    public static final QName NRML_POINT_SOURCE =
            new QName("pointSource", NRML_NAMESPACE);

    public static final QName NRML_TECTONIC_REGION =
            new QName("tectonicRegion", NRML_NAMESPACE);

    public static final QName NRML_EDI_MFD =
            new QName("evenlyDiscretizedIncrementalMFD", NRML_NAMESPACE);

    public static final QName NRML_BIN_SIZE =
            new QName("binSize", NRML_NAMESPACE);

    public static final QName NRML_SIMPLE_FAULT_GEOMETRY =
            new QName("simpleFaultGeometry", NRML_NAMESPACE);

    public static final QName NRML_FAULT_TRACE =
            new QName("faultTrace", NRML_NAMESPACE);

    public static final QName NRML_UPPER_SEISM_DEP =
            new QName("upperSeismogenicDepth", NRML_NAMESPACE);

    public static final QName NRML_LOWER_SEISM_DEP =
            new QName("lowerSeismogenicDepth", NRML_NAMESPACE);

    public static final QName NRML_CONFIG = new QName("config", NRML_NAMESPACE);
    public static final QName NRML = new QName("nrml", NRML_NAMESPACE);
    public static final QName NRML_RAKE = new QName("rake", NRML_NAMESPACE);

    public static final QName NRML_MIN_VAL =
            new QName("minVal", NRML_NAMESPACE);

    public static final QName NRML_TYPE = new QName("type", NRML_NAMESPACE);
    public static final QName NRML_DIP = new QName("dip", NRML_NAMESPACE);

    public static final QName NRML_POINT_LOCATION =
            new QName("location", NRML_NAMESPACE);

    public static final QName NRML_COMPLEX_FAULT_SOURCE =
            new QName("complexFaultSource", NRML_NAMESPACE);

    public static final QName NRML_COMPLEX_FAULT_GEOMETRY =
            new QName("complexFaultGeometry", NRML_NAMESPACE);

    public static final QName NRML_FAULT_EDGES =
            new QName("faultEdges", NRML_NAMESPACE);

    public static final QName NRML_FAULT_TOP_EDGE =
            new QName("faultTopEdge", NRML_NAMESPACE);

    public static final QName NRML_FAULT_BOTTOM_EDGE =
            new QName("faultBottomEdge", NRML_NAMESPACE);

    public static final QName NRML_AREA_SOURCE =
            new QName("areaSource", NRML_NAMESPACE);

    public static final QName NRML_AREA_BOUNDARY =
            new QName("areaBoundary", NRML_NAMESPACE);

    public static final QName NRML_RUPTURE_RATE_MODEL =
            new QName("ruptureRateModel", NRML_NAMESPACE);

    public static final QName NRML_FOCAL_MECHANISM =
            new QName("focalMechanism", NRML_NAMESPACE);

    public static final QName NRML_RUPTURE_DEPTH_DISTRIBUTION =
            new QName("ruptureDepthDistribution", NRML_NAMESPACE);

    public static final QName MAGNITUDE =
            new QName("magnitude", NRML_NAMESPACE);

    public static final QName DEPTH = new QName("depth", NRML_NAMESPACE);

    public static final QName NRML_HYPOCENTRAL_DEPTH =
            new QName("hypocentralDepth", NRML_NAMESPACE);

    public static final QName NRML_LOCATION =
            new QName("location", NRML_NAMESPACE);

    // QML Properties
    public static final QName QML_NODAL_PLANES =
            new QName("nodalPlanes", QML_NAMESPACE);

    public static final QName QML_NODAL_PLANE1 =
            new QName("nodalPlane1", QML_NAMESPACE);

    public static final QName QML_STRIKE = new QName("strike", QML_NAMESPACE);
    public static final QName QML_VALUE = new QName("value", QML_NAMESPACE);
    public static final QName QML_DIP = new QName("dip", QML_NAMESPACE);
    public static final QName QML_RAKE = new QName("rake", QML_NAMESPACE);

}
