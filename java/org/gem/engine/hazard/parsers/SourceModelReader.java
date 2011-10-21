package org.gem.engine.hazard.parsers;

import java.io.File;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.StringTokenizer;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;
import org.gem.engine.XMLMismatchError;
import org.gem.engine.XMLValidationError;

/**
 * Class for reading source model data in a nrML format file. The constructor of
 * this class takes the path of the file to read from.
 *
 */
public class SourceModelReader {

    private final List<GEMSourceData> sourceList;

    private final String path;
    private final double deltaMFD;

    // border type for area source definition
    private static BorderType borderType = BorderType.GREAT_CIRCLE;

    private static final String SIMPLE_FAULT = "simpleFaultSource";
    private static final String COMPLEX_FAULT = "complexFaultSource";
    private static final String AREA = "areaSource";
    private static final String POINT = "pointSource";

    private static final String SOURCE_NAME = "name";
    private static final String SOURCE_ID = "id";
    private static final String TECTONIC_REGION = "tectonicRegion";

    private static final String SIMPLE_FAULT_GEOMETRY = "simpleFaultGeometry";
    private static final String FAULT_TRACE = "faultTrace";
    private static final String UPPER_SEIMSMOGENIC_DEPTH =
            "upperSeismogenicDepth";
    private static final String LOWER_SEISMOGENIC_DEPTH =
            "lowerSeismogenicDepth";

    private static final String COMPLEX_FAULT_GEOMETRY = "complexFaultGeometry";
    private static final String FAULT_TOP_EDGE = "faultTopEdge";
    private static final String FAULT_BOTTOM_EDGE = "faultBottomEdge";

    private static final String AREA_BOUNDARY = "areaBoundary";
    private static final String EXTERIOR = "exterior";
    private static final String LINEAR_RING = "LinearRing";
    private static final String POS_LIST = "posList";

    private static final String POINT_LOCATION = "Point";
    private static final String POS = "pos";

    private static final String RUPTURE_RATE_MODEL = "ruptureRateModel";

    private static final String HYPOCENTRAL_DEPTH = "hypocentralDepth";

    private static final String FOCAL_MECHANISM = "focalMechanism";
    private static final String STRIKE = "strike";
    private static final String DIP = "dip";
    private static final String RAKE = "rake";

    private static final String RUPTURE_DEPTH_DISTRIBUTION =
            "ruptureDepthDistribution";

    private static final String EVENLY_DISCRETIZED_MAG_FREQ_DIST =
            "evenlyDiscretizedIncrementalMFD";
    private static final String BIN_SIZE = "binSize";
    private static final String MIN_VAL = "minVal";

    private static final String TRUNCATED_GUTENBERG_RICHTER =
            "truncatedGutenbergRichter";
    private static final String a_VALUE_CUMULATIVE = "aValueCumulative";
    private static final String b_VALUE = "bValue";
    private static final String MIN_MAGNITUDE = "minMagnitude";
    private static final String MAX_MAGNITUDE = "maxMagnitude";

    private static final String NODAL_PLANE1 = "nodalPlane1";
    private static final String NODAL_PLANES = "nodalPlanes";
    private static final String VALUE = "value";
    private static final String DEPTH = "depth";
    private static final String MAGNITUDE = "magnitude";
    private static final String LINE_STRING = "LineString";
    private static final String FAULT_EDGES = "faultEdges";
    private static final String POLYGON = "Polygon";
    private static final String LOCATION = "location";
    private static final String SOURCE_MODEL = "sourceModel";

    /**
     * Creates a new SourceModelReader given the path of the file to read from
     * and the bin width for the magnitude frequency distribution definition
     */
    public SourceModelReader(String path, double deltaMFD) {
        this.path = path;
        this.sourceList = new ArrayList<GEMSourceData>();
        this.deltaMFD = deltaMFD;
    }

    /**
     * Reads file and returns source model data. For each source definition, a
     * {@link GEMSourceData} is created and stored in a list.
     */
    @SuppressWarnings("unchecked")
    public List<GEMSourceData> read() {
        if (System.getProperty("openquake.nrml.schema") == null)
            throw new RuntimeException("Set openquake.nrml.schema property  to the NRML schema path");

        this.sourceList.clear();

        File xml = new File(path);
        SAXReader reader = new SAXReader(true);
        Document doc = null;
        try {
            reader.setFeature("http://apache.org/xml/features/validation/schema", true);
            reader.setProperty("http://java.sun.com/xml/jaxp/properties/schemaLanguage", "http://www.w3.org/2001/XMLSchema");
            reader.setProperty("http://java.sun.com/xml/jaxp/properties/schemaSource", "file://" + System.getProperty("openquake.nrml.schema"));
            doc = reader.read(xml);
        } catch (DocumentException e) {
            throw new XMLValidationError(xml.getAbsolutePath(), e);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }

        Element sourceModel = doc.getRootElement().element(SOURCE_MODEL);
        if (sourceModel == null)
        {
            Element child = (Element) doc.getRootElement().elements().get(0);
            String localName = child.getQName().getName();

            throw new XMLMismatchError(null, localName, SOURCE_MODEL);
        }

        Iterator i = sourceModel.elements().iterator();

        while (i.hasNext()) {
            Element elem = (Element) i.next();
            String elemName = elem.getName();
            if (elemName.equalsIgnoreCase(SIMPLE_FAULT)) {
                sourceList.add(getSimpleFaultSourceData(deltaMFD, elem));
            } else if (elemName.equalsIgnoreCase(COMPLEX_FAULT)) {
                sourceList.add(getComplexFaultSourceData(deltaMFD, elem));
            } else if (elemName.equalsIgnoreCase(AREA)) {
                sourceList.add(getAreaSourceData(deltaMFD, elem));
            } else if (elemName.equalsIgnoreCase(POINT)) {
                sourceList.add(getPointSourceData(deltaMFD, elem));
            }
        }
        return sourceList;
    }

    /**
     * Reads and return point source data
     */
    private GEMPointSourceData getPointSourceData(double deltaMFD, Element elem) {
        Location pointLoc =
                getPointLocation(elem.element(LOCATION).element(POINT_LOCATION));
        MagFreqDistsForFocalMechs magfreqDistFocMech =
                getMagFreqDistsForFocalMechs(deltaMFD, elem);
        HypoMagFreqDistAtLoc hypoMagFreqDistAtLoc =
                new HypoMagFreqDistAtLoc(magfreqDistFocMech
                        .getMagFreqDistList(), pointLoc, magfreqDistFocMech
                        .getFocalMechanismList());
        ArbitrarilyDiscretizedFunc rupDepthDist =
                getRuptureDepthDistribution(elem
                        .element(RUPTURE_DEPTH_DISTRIBUTION));
        double hypocentralDepth =
                Double.valueOf((String) elem.element(HYPOCENTRAL_DEPTH)
                        .getData());

        return new GEMPointSourceData(extractIDFrom(elem),
                extractNameFrom(elem), extractTectonicRegionFrom(elem),
                hypoMagFreqDistAtLoc, rupDepthDist, hypocentralDepth);
    }

    /**
     * Returns the type of the tectonic region of the given element.
     */
    private TectonicRegionType extractTectonicRegionFrom(Element elem) {
        return TectonicRegionType.getTypeForName((String) elem.element(
                TECTONIC_REGION).getData());
    }

    /**
     * Returns the ID of the given element.
     */
    private String extractIDFrom(Element elem) {
        return elem.attributeValue(SOURCE_ID);
    }

    /**
     * Returns the name of the given element.
     */
    private String extractNameFrom(Element elem) {
        return (String) elem.element(SOURCE_NAME).getData();
    }

    /**
     * Reads and returns area source data
     */
    private GEMAreaSourceData getAreaSourceData(double deltaMFD, Element elem) {
        Region reg =
                new Region(get2DLocList(elem.element(AREA_BOUNDARY).element(
                        POLYGON).element(EXTERIOR).element(LINEAR_RING)
                        .element(POS_LIST)), borderType);
        MagFreqDistsForFocalMechs magfreqDistFocMech =
                getMagFreqDistsForFocalMechs(deltaMFD, elem);
        ArbitrarilyDiscretizedFunc rupDepthDist =
                getRuptureDepthDistribution(elem
                        .element(RUPTURE_DEPTH_DISTRIBUTION));
        double hypocentralDepth =
                Double.valueOf((String) elem.element(HYPOCENTRAL_DEPTH)
                        .getData());

        return new GEMAreaSourceData(extractIDFrom(elem),
                extractNameFrom(elem), extractTectonicRegionFrom(elem), reg,
                magfreqDistFocMech, rupDepthDist, hypocentralDepth);
    }

    /**
     * Reads and returns complex fault source data
     */
    private GEMSubductionFaultSourceData getComplexFaultSourceData(
            double deltaMFD, Element elem) {
        Element complexFaultGeometry = elem.element(COMPLEX_FAULT_GEOMETRY);

        FaultTrace faultTopEdge =
                getFaultTrace(complexFaultGeometry.element(FAULT_EDGES)
                        .element(FAULT_TOP_EDGE).element(LINE_STRING).element(
                                POS_LIST));
        FaultTrace faultBottomEdge =
                getFaultTrace(complexFaultGeometry.element(FAULT_EDGES)
                        .element(FAULT_BOTTOM_EDGE).element(LINE_STRING)
                        .element(POS_LIST));
        double rake = Double.valueOf((String) elem.element(RAKE).getData());
        IncrementalMagFreqDist magFreqDist = getMagFreqDist(deltaMFD, elem);

        return new GEMSubductionFaultSourceData(extractIDFrom(elem),
                extractNameFrom(elem), extractTectonicRegionFrom(elem),
                faultTopEdge, faultBottomEdge, rake, magFreqDist, true);
    }

    /**
     * Reads and return simple fault source data
     */
    private GEMFaultSourceData getSimpleFaultSourceData(double deltaMFD,
            Element elem) {
        Element simpleFaultGeometry = elem.element(SIMPLE_FAULT_GEOMETRY);
        FaultTrace faultTrace =
                getFaultTrace(simpleFaultGeometry.element(FAULT_TRACE).element(
                        LINE_STRING).element(POS_LIST));
        double dip =
                Double.valueOf((String) simpleFaultGeometry.element(DIP)
                        .getData());
        double upperSeismogenicDepth =
                Double.valueOf((String) simpleFaultGeometry.element(
                        UPPER_SEIMSMOGENIC_DEPTH).getData());
        double lowerSeismogenicDepth =
                Double.valueOf((String) simpleFaultGeometry.element(
                        LOWER_SEISMOGENIC_DEPTH).getData());
        double rake = Double.valueOf((String) elem.element(RAKE).getData());

        IncrementalMagFreqDist magFreqDist = getMagFreqDist(deltaMFD, elem);

        return new GEMFaultSourceData(extractIDFrom(elem),
                extractNameFrom(elem), extractTectonicRegionFrom(elem),
                magFreqDist, faultTrace, dip, rake, lowerSeismogenicDepth,
                upperSeismogenicDepth, true);
    }

    /**
     * Reads fault trace coordinates (Each point being specified by a triplet
     * (longitude, latitude, depth)) and returns {@link FaultTrace}
     */
    private FaultTrace getFaultTrace(Element trace) {
        FaultTrace faultTrace = new FaultTrace("");
        LocationList locList = get3DLocList(trace);
        faultTrace.addAll(locList);
        return faultTrace;
    }

    /**
     * Reads magnitude frequency distribution/focal mechanism pairs and returns
     * {@link MagFreqDistsForFocalMechs}
     */
    @SuppressWarnings("unchecked")
    private MagFreqDistsForFocalMechs getMagFreqDistsForFocalMechs(
            double deltaMFD, Element elem) {
        List<IncrementalMagFreqDist> mfdList =
                new ArrayList<IncrementalMagFreqDist>();
        List<FocalMechanism> focMechList = new ArrayList<FocalMechanism>();
        for (Iterator j = elem.elementIterator(RUPTURE_RATE_MODEL); j.hasNext();) {
            Element e = (Element) j.next();
            IncrementalMagFreqDist magFreqDist = getMagFreqDist(deltaMFD, e);
            mfdList.add(magFreqDist);
            FocalMechanism focMech =
                    getFocalMechanism(e.element(FOCAL_MECHANISM));
            focMechList.add(focMech);
        }
        IncrementalMagFreqDist[] mfdArray =
                new IncrementalMagFreqDist[mfdList.size()];
        FocalMechanism[] fmArray = new FocalMechanism[focMechList.size()];
        for (int ii = 0; ii < mfdList.size(); ii++) {
            mfdArray[ii] = mfdList.get(ii);
            fmArray[ii] = focMechList.get(ii);
        }
        return new MagFreqDistsForFocalMechs(mfdArray, fmArray);
    }

    /**
     * Reads magnitude frequency distribution data (truncated Gutenberg-Richter
     * or incremental evenly discretized) and returns
     * {@link IncrementalMagFreqDist}
     */
    private IncrementalMagFreqDist getMagFreqDist(double deltaMFD, Element elem) {
        IncrementalMagFreqDist magFreqDist = null;
        if (elem.element(TRUNCATED_GUTENBERG_RICHTER) != null) {
            magFreqDist =
                    getGutenbergRichterMagFreqDist(deltaMFD, elem
                            .element(TRUNCATED_GUTENBERG_RICHTER));
        } else if (elem.element(EVENLY_DISCRETIZED_MAG_FREQ_DIST) != null) {
            magFreqDist =
                    getEvenlyDiscretizedMagFreqDist(elem
                            .element(EVENLY_DISCRETIZED_MAG_FREQ_DIST));
        }
        return magFreqDist;
    }

    /**
     * Reads incremental evenly discretized magnitude frequency distribution
     * data and returns {@link IncrementalMagFreqDist}
     */
    private IncrementalMagFreqDist getEvenlyDiscretizedMagFreqDist(
            Element evenlyDiscretizedMagFreqDist) {
        IncrementalMagFreqDist magFreqDist;
        double binSize =
                Double.valueOf(evenlyDiscretizedMagFreqDist
                        .attributeValue(BIN_SIZE));
        double minVal =
                Double.valueOf(evenlyDiscretizedMagFreqDist
                        .attributeValue(MIN_VAL));

        StringTokenizer st =
                new StringTokenizer((String) evenlyDiscretizedMagFreqDist
                        .getData());

        magFreqDist =
                new IncrementalMagFreqDist(minVal, st.countTokens(), binSize);

        int index = 0;

        while (st.hasMoreTokens()) {
            magFreqDist.add(index, Double.valueOf(st.nextToken()));
            index++;
        }

        return magFreqDist;
    }

    /**
     * Reads Gutenberg-Richter magnitude frequency distribution data and returns
     * {@link GutenbergRichterMagFreqDist}
     */
    private GutenbergRichterMagFreqDist getGutenbergRichterMagFreqDist(
            double deltaMFD, Element gutenbergRichter) {
        GutenbergRichterMagFreqDist magFreqDist;
        double aVal =
                Double.valueOf((String) gutenbergRichter.element(
                        a_VALUE_CUMULATIVE).getData());
        double bVal =
                Double.valueOf((String) gutenbergRichter.element(b_VALUE)
                        .getData());
        double minMag =
                Double.valueOf((String) gutenbergRichter.element(MIN_MAGNITUDE)
                        .getData());
        double maxMag =
                Double.valueOf((String) gutenbergRichter.element(MAX_MAGNITUDE)
                        .getData());
        magFreqDist = createGrMfd(aVal, bVal, minMag, maxMag, deltaMFD);
        return magFreqDist;
    }

    /**
     * Reads focal mechanism data (strike, dip and rake) and returns
     * {@link FocalMechanism}
     */
    private FocalMechanism getFocalMechanism(Element focalMech) {
        Element nodalPlane =
                focalMech.element(NODAL_PLANES).element(NODAL_PLANE1);

        double strike =
                Double.valueOf((String) nodalPlane.element(STRIKE).element(
                        VALUE).getData());
        double dip =
                Double.valueOf((String) nodalPlane.element(DIP).element(VALUE)
                        .getData());
        double rake =
                Double.valueOf((String) nodalPlane.element(RAKE).element(VALUE)
                        .getData());
        return new FocalMechanism(strike, dip, rake);
    }

    /**
     * Reads rupture depth distribution data (rupture magnitude vs. rupture
     * depth) and returns an {@link ArbitrarilyDiscretizedFunc}
     */
    private ArbitrarilyDiscretizedFunc getRuptureDepthDistribution(
            Element ruptureDepthDist) {
        ArbitrarilyDiscretizedFunc rupDepthDist =
                new ArbitrarilyDiscretizedFunc();
        String xVals = (String) ruptureDepthDist.element(MAGNITUDE).getData();
        String yVals = (String) ruptureDepthDist.element(DEPTH).getData();
        StringTokenizer xVal = new StringTokenizer(xVals);
        StringTokenizer yVal = new StringTokenizer(yVals);
        while (xVal.hasMoreTokens())
            rupDepthDist.set(Double.valueOf(xVal.nextToken()), Double
                    .valueOf(yVal.nextToken()));
        return rupDepthDist;
    }

    /**
     * Reads location list (each location being specified by a triplet
     * (longitude,latitude,depth)) and returns {@link LocationList}
     */
    private LocationList get3DLocList(Element posList) {
        LocationList locList = new LocationList();
        String positionList = ((String) posList.getData());
        StringTokenizer st = new StringTokenizer(positionList);
        while (st.hasMoreTokens()) {
            double lon = Double.valueOf(st.nextToken());
            double lat = Double.valueOf(st.nextToken());
            double depth = Double.valueOf(st.nextToken());
            locList.add(new Location(lat, lon, depth));
        }
        return locList;
    }

    /**
     * Reads location list (each location being specified by a doublet
     * (longitude,latitude)) and returns a {@link LocationList}
     */
    private LocationList get2DLocList(Element posList) {
        LocationList locList = new LocationList();
        String positionList = (String) posList.getData();
        StringTokenizer st = new StringTokenizer(positionList);
        while (st.hasMoreTokens()) {
            double lon = Double.valueOf(st.nextToken());
            double lat = Double.valueOf(st.nextToken());
            locList.add(new Location(lat, lon));
        }
        return locList;
    }

    /**
     * Reads single location (longitude,latitude). Returns {@link Location}
     */
    private Location getPointLocation(Element pointLocation) {
        String pointCoords = (String) pointLocation.element(POS).getData();
        StringTokenizer st = new StringTokenizer(pointCoords);
        double longitude = Double.valueOf(st.nextToken());
        double latitude = Double.valueOf(st.nextToken());
        return new Location(latitude, longitude);
    }

    /**
     * Defines truncated Gutenberg-Richter magnitude frequency distribution
     *
     * @param aVal
     *            : cumulative a value
     * @param bVal
     *            : b value
     * @param mMin
     *            : minimum magnitude
     * @param mMax
     *            : maximum magnitude
     * @param deltaMFD
     *            : discretization interval
     * @return {@link GutenbergRichterMagFreqDist}
     */
    private GutenbergRichterMagFreqDist createGrMfd(double aVal, double bVal,
            double mMin, double mMax, double deltaMFD) {
        GutenbergRichterMagFreqDist mfd = null;
        // round gap between mMax and mMin with respect to delta bin
        mMax = Math.round((mMax - mMin) / deltaMFD) * deltaMFD + mMin;
        // compute total cumulative rate between minimum and maximum magnitude
        double totCumRate = Double.NaN;
        if (mMin != mMax) {
            totCumRate =
                    Math.pow(10, aVal - bVal * mMin)
                            - Math.pow(10, aVal - bVal * mMax);
        } else {
            // compute incremental a value and calculate rate corresponding to
            // minimum magnitude
            double aIncr = aVal + Math.log10(bVal * Math.log(10));
            totCumRate = Math.pow(10, aIncr - bVal * mMin);
        }
        if (mMax != mMin) {
            // shift to bin center
            mMin = mMin + deltaMFD / 2;
            mMax = mMax - deltaMFD / 2;
        }
        int numVal = (int) Math.round(((mMax - mMin) / deltaMFD + 1));
        mfd =
                new GutenbergRichterMagFreqDist(bVal, totCumRate, mMin, mMax,
                        numVal);
        return mfd;
    }
}
