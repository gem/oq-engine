package org.gem.engine;

import java.io.File;
import java.net.MalformedURLException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.StringTokenizer;

import org.dom4j.Document;
import org.dom4j.DocumentException;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class SourceModelReader {

    private static List<GEMSourceData> sourceList;

    // border type for area source definition
    private static BorderType borderType = BorderType.GREAT_CIRCLE;

    // source typologies
    private static String SIMPLE_FAULT = "simpleFault";
    private static String COMPLEX_FAULT = "complexFault";
    private static String AREA = "area";
    private static String POINT = "point";
    private static String SOURCE_NAME = "sourceName";
    private static String SOURCE_ID = "sourceID";
    private static String TECTONIC_REGION = "tectonicRegion";
    private static String SIMPLE_FAULT_GEOMETRY = "simpleFaultGeometry";
    private static String FAULT_TRACE = "faultTrace";
    private static String UPPER_SEIMSMOGENIC_DEPTH = "upperSeismogenicDepth";
    private static String LOWER_SEISMOGENIC_DEPTH = "lowerSeismogenicDepth";
    private static String COMPLEX_FAULT_GEOMETRY = "complexFaultGeometry";
    private static String FAULT_TOP_EDGE = "faultTopEdge";
    private static String FAULT_BOTTOM_EDGE = "faultBottomEdge";
    private static String AREA_BOUNDARY = "areaBoundary";
    private static String POINT_LOCATION = "pointLocation";
    private static String RUPTURE_RATE_MODEL = "ruptureRateModel";
    private static String FOCAL_MECHANISM = "focalMechanism";
    private static String STRIKE = "strike";
    private static String DIP = "dip";
    private static String RAKE = "rake";
    private static String RUPTURE_DEPTH_DISTRIBUTION =
            "ruptureDepthDistribution";
    private static String XVALUES = "XValues";
    private static String YVALUES = "YValues";
    private static String EVENLY_DISCRETIZED_MAG_FREQ_DIST =
            "evenlyDiscretizedIncrementalMagFreqDist";
    private static String BIN_SIZE = "binSize";
    private static String MIN_VAL = "minVal";
    private static String BIN_COUNT = "binCount";
    private static String DISTRIBUTION_VALUES = "DistributionValues";
    private static String TRUNCATED_GUTENBERG_RICHTER =
            "truncatedGutenbergRichter";
    private static String a_VALUE_CUMULATIVE = "aValueCumulative";
    private static String b_VALUE = "bValue";
    private static String MIN_MAGNITUDE = "minMagnitude";
    private static String MAX_MAGNITUDE = "maxMagnitude";
    private static String LOCATION = "location";
    private static String LATITUDE = "latitude";
    private static String LONGITUDE = "longitude";
    private static String DEPTH = "depth";

    public SourceModelReader(String sourceModelFile, double deltaMFD) {

        sourceList = new ArrayList<GEMSourceData>();

        File xml = new File(sourceModelFile);
        SAXReader reader = new SAXReader();
        Document doc = null;
        try {
            doc = reader.read(xml);
        } catch (MalformedURLException e) {
            e.printStackTrace();
        } catch (DocumentException e) {
            e.printStackTrace();
        }
        Element root = doc.getRootElement();
        for (Iterator i = root.elements().iterator(); i.hasNext();) {
            Element elem = (Element) i.next();
            String elemName = elem.getName();
            if (elemName.equalsIgnoreCase(SIMPLE_FAULT)) {
                sourceList.add(getSimpleFaultSourceData(deltaMFD, elem));
            } else if (elemName.equalsIgnoreCase(COMPLEX_FAULT)) {
                sourceList.add(getComplexFaultSourceData(deltaMFD, elem));
            } else if (elemName.equalsIgnoreCase(AREA)) {

            } else if (elemName.equalsIgnoreCase(POINT)) {
            }
        }

    }

    private GEMSubductionFaultSourceData getComplexFaultSourceData(
            double deltaMFD, Element elem) {
        String srcName = (String) elem.element(SOURCE_NAME).getData();
        String srcID = (String) elem.element(SOURCE_ID).getData();
        TectonicRegionType tectRegType =
                TectonicRegionType.getTypeForName((String) elem.element(
                        TECTONIC_REGION).getData());
        Element complexFaultGeometry = elem.element(COMPLEX_FAULT_GEOMETRY);
        FaultTrace faultTopEdge =
                getFaultTrace(complexFaultGeometry.element(FAULT_TOP_EDGE));
        FaultTrace faultBottomEdge =
                getFaultTrace(complexFaultGeometry.element(FAULT_BOTTOM_EDGE));
        double rake = Double.valueOf((String) elem.element(RAKE).getData());
        IncrementalMagFreqDist magFreqDist = getMagFreqDist(deltaMFD, elem);
        GEMSubductionFaultSourceData src =
                new GEMSubductionFaultSourceData(srcID, srcName, tectRegType,
                        faultTopEdge, faultBottomEdge, rake, magFreqDist, true);
        return src;
    }

    private GEMFaultSourceData getSimpleFaultSourceData(double deltaMFD,
            Element elem) {
        String srcName = (String) elem.element(SOURCE_NAME).getData();
        String srcID = (String) elem.element(SOURCE_ID).getData();
        TectonicRegionType tectRegType =
                TectonicRegionType.getTypeForName((String) elem.element(
                        TECTONIC_REGION).getData());
        Element simpleFaultGeometry = elem.element(SIMPLE_FAULT_GEOMETRY);
        FaultTrace faultTrace =
                getFaultTrace(simpleFaultGeometry.element(FAULT_TRACE));
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
        return new GEMFaultSourceData(srcID, srcName, tectRegType, magFreqDist,
                faultTrace, dip, rake, lowerSeismogenicDepth,
                upperSeismogenicDepth, true);
    }

    private FaultTrace getFaultTrace(Element trace) {
        FaultTrace faultTrace = new FaultTrace("");
        LocationList locList = getLocationList(trace);
        faultTrace.addAll(locList);
        return faultTrace;
    }

    private IncrementalMagFreqDist
            getMagFreqDist(double deltaMFD, Element elem) {
        IncrementalMagFreqDist magFreqDist = null;
        if (elem.element(TRUNCATED_GUTENBERG_RICHTER) != null) {
            magFreqDist =
                    getGutenbergRichterMagFreqDist(deltaMFD,
                            elem.element(TRUNCATED_GUTENBERG_RICHTER));
        } else if (elem.element(EVENLY_DISCRETIZED_MAG_FREQ_DIST) != null) {
            magFreqDist =
                    getEvenlyDiscretizedMagFreqDist(elem
                            .element(EVENLY_DISCRETIZED_MAG_FREQ_DIST));
        }
        return magFreqDist;
    }

    private IncrementalMagFreqDist getEvenlyDiscretizedMagFreqDist(
            Element evenlyDiscretizedMagFreqDist) {
        IncrementalMagFreqDist magFreqDist;
        double binSize =
                Double.valueOf(evenlyDiscretizedMagFreqDist
                        .attributeValue(BIN_SIZE));
        double minVal =
                Double.valueOf(evenlyDiscretizedMagFreqDist
                        .attributeValue(MIN_VAL));
        int binCount =
                Integer.valueOf(evenlyDiscretizedMagFreqDist
                        .attributeValue(BIN_COUNT));
        Element distributionValues =
                evenlyDiscretizedMagFreqDist.element(DISTRIBUTION_VALUES);
        magFreqDist = new IncrementalMagFreqDist(minVal, binCount, binSize);
        String occurrenceRates = (String) distributionValues.getData();
        StringTokenizer st = new StringTokenizer(occurrenceRates);
        int index = 0;
        while (st.hasMoreTokens()) {
            magFreqDist.add(index, Double.valueOf(st.nextToken()));
            index = index + 1;
        }
        return magFreqDist;
    }

    private IncrementalMagFreqDist getGutenbergRichterMagFreqDist(
            double deltaMFD, Element gutenbergRichter) {
        IncrementalMagFreqDist magFreqDist;
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

    private LocationList getLocationList(Element locationList) {
        LocationList locList = new LocationList();
        for (Iterator j = locationList.elements().iterator(); j.hasNext();) {
            Element e = (Element) j.next();
            double lat = Double.valueOf((String) e.element(LATITUDE).getData());
            double lon =
                    Double.valueOf((String) e.element(LONGITUDE).getData());
            double depth = 0.0;
            if (e.element(DEPTH) != null)
                depth = Double.valueOf((String) e.element(DEPTH).getData());
            locList.add(new Location(lat, lon, depth));
        }
        return locList;
    }

    private GutenbergRichterMagFreqDist createGrMfd(double aVal, double bVal,
            double mMin, double mMax, double deltaMFD) {
        GutenbergRichterMagFreqDist mfd = null;
        // round mMin and mMax with respect to delta bin
        mMin = Math.round(mMin / deltaMFD) * deltaMFD;
        mMax = Math.round(mMax / deltaMFD) * deltaMFD;
        // compute total cumulative rate between minimum and maximum magnitude
        double totCumRate = Double.NaN;
        if (mMin != mMax) {
            totCumRate =
                    Math.pow(10, aVal - bVal * mMin)
                            - Math.pow(10, aVal - bVal * mMax);
        } else {
            // compute incremental a value
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
