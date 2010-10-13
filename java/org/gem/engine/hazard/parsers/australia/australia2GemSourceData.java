package org.gem.engine.hazard.parsers.australia;

import java.awt.Color;
import java.io.BufferedReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.net.URL;
import java.util.ArrayList;
import java.util.StringTokenizer;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;
import org.w3c.dom.Document;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

public class australia2GemSourceData extends GemFileParser {

    private static BorderType Bordertype = BorderType.GREAT_CIRCLE;

    // magnitude bin width for magnitude frequency distribution
    private static double dm = 0.1;

    // minimum magnitude for hazard calculations
    private static double minMagnitude = 5.0;

    // tectonic region for Australia
    private TectonicRegionType trt = TectonicRegionType.STABLE_SHALLOW;

    // focal mechanism (These values are arbitrarily chosen
    // because the model do not provide this info)
    // This is something that must be improved
    private double strike = 0.0;
    private double dip = 90.0;
    private double rake = 0.0;

    public australia2GemSourceData() {

        // input file containing source definitions
        String inputfile = "australia/nat_source_polygon_corrected.xml";

        // initialize array list of GEMSourceData
        srcDataList = new ArrayList<GEMSourceData>();

        try {

            // create Document object from XML file
            DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
            DocumentBuilder db = dbf.newDocumentBuilder();
            System.out.println(this.getClass().getClassLoader()
                    .getResource(inputfile).getPath());
            Document doc =
                    db.parse(this.getClass().getClassLoader()
                            .getResource(inputfile).getPath());
            doc.getDocumentElement().normalize();

            // source model
            NodeList SourceModel = doc.getElementsByTagName("Source_Model");
            // magnitude type
            String MagnitudeType =
                    SourceModel.item(0).getAttributes().item(0).getNodeValue();
            System.out.print("Source Model Magnitude Type: " + MagnitudeType
                    + "\n\n");

            // list of polygons
            NodeList PolygonLst = doc.getElementsByTagName("polygon");
            // number of polygons
            int NPolygons = PolygonLst.getLength();
            System.out.print("Number of polygons: " + NPolygons + "\n\n");

            // loop over polygons
            for (int i = 0; i < NPolygons; i++) {

                System.out.println("Source: " + (i + 1) + " of " + NPolygons);

                // for each source
                // region coordinates
                Region PolygonRegion = null;
                // array list of regions to be excluded in each area source
                ArrayList<Region> listExReg = new ArrayList<Region>();
                // list of MFD-FocalMechanism pairs
                MagFreqDistsForFocalMechs magfreqDistFocMech = null;
                // average top of rupture depth vs magnitude
                ArbitrarilyDiscretizedFunc aveRupTopVsMag = null;
                // average hypocentral depth
                double aveHypoDepth = Double.NaN;

                // minimum magnitude
                double minMag = Double.NaN;
                // maximum magnitude
                double maxMag = Double.NaN;
                // occurance rate above minimum magnitude
                double lambda = Double.NaN;
                // b value
                double bVal = Double.NaN;
                // depth
                double depth = Double.NaN;

                Node Polygon = PolygonLst.item(i);

                // Polygon area
                double PolygonArea =
                        Double.parseDouble(Polygon.getAttributes()
                                .getNamedItem("area").getNodeValue());
                System.out.println("Polygon area: " + PolygonArea);

                // Polygon child
                NodeList PolygonChildList = Polygon.getChildNodes();

                // loop over childrens
                for (int ic = 0; ic < PolygonChildList.getLength(); ic++) {

                    // Polygon boundary
                    if (PolygonChildList.item(ic).getNodeName()
                            .equalsIgnoreCase("boundary")) {

                        LocationList PolygonBoundary = new LocationList();
                        StringTokenizer st =
                                new StringTokenizer(PolygonChildList.item(ic)
                                        .getFirstChild().getNodeValue());
                        while (st.hasMoreTokens()) {
                            PolygonBoundary.add(new Location(Double.valueOf(st
                                    .nextToken()), Double.valueOf(st
                                    .nextToken())));
                        }
                        // System.out.println("Polygon Boundary"+PolygonBoundary);
                        PolygonRegion = new Region(PolygonBoundary, Bordertype);
                        System.out
                                .println("Polygon Boundary: " + PolygonRegion);

                    } // end polygon boundary

                    // Exclude boundary
                    if (PolygonChildList.item(ic).getNodeName()
                            .equalsIgnoreCase("exclude")) {

                        LocationList PolygonExcludeBoundary =
                                new LocationList();
                        StringTokenizer st =
                                new StringTokenizer(PolygonChildList.item(ic)
                                        .getFirstChild().getNodeValue());
                        while (st.hasMoreTokens()) {
                            PolygonExcludeBoundary.add(new Location(Double
                                    .valueOf(st.nextToken()), Double.valueOf(st
                                    .nextToken())));
                        }

                        // add to list
                        listExReg.add(new Region(PolygonExcludeBoundary,
                                Bordertype));

                    } // end exclude boundary

                    // Recurrence model
                    if (PolygonChildList.item(ic).getNodeName()
                            .equalsIgnoreCase("recurrence")) {

                        minMag =
                                Double.valueOf(PolygonChildList.item(ic)
                                        .getAttributes()
                                        .getNamedItem("min_magnitude")
                                        .getNodeValue());
                        System.out.println("min_magnitude: \"" + minMag + "\"");

                        maxMag =
                                Double.valueOf(PolygonChildList.item(ic)
                                        .getAttributes()
                                        .getNamedItem("max_magnitude")
                                        .getNodeValue());
                        System.out.println("max_magnitude: \"" + maxMag + "\"");

                        lambda =
                                Double.valueOf(PolygonChildList.item(ic)
                                        .getAttributes()
                                        .getNamedItem("Lambda_Min")
                                        .getNodeValue());
                        System.out.println("Lambda_Min: \"" + lambda + "\"");

                        bVal =
                                Double.valueOf(PolygonChildList.item(ic)
                                        .getAttributes().getNamedItem("b")
                                        .getNodeValue());
                        System.out.println("b: \"" + bVal + "\"");

                        System.out.println("min_mag: \""
                                + PolygonChildList.item(ic).getAttributes()
                                        .getNamedItem("min_mag").getNodeValue()
                                + "\"");

                        depth =
                                Double.valueOf(PolygonChildList.item(ic)
                                        .getAttributes().getNamedItem("depth")
                                        .getNodeValue());
                        System.out.println("depth: \"" + depth + "\"");
                        System.out.print("\n\n\n");

                        // compute cumulative a value
                        double aVal = Math.log10(lambda) + bVal * minMag;

                        // compute total cumulative rate between minimum and
                        // maximum magnitude
                        double totCumRate =
                                Math.pow(10, aVal - bVal * minMagnitude)
                                        - Math.pow(10, aVal - bVal * maxMag);

                        // Round magnitude interval extremes (with respect to
                        // default dm) and move to bin center
                        // (if the minimum and maximum magnitudes are different)
                        double mmaxR;
                        double mminR;
                        if (minMag != maxMag) {
                            mminR =
                                    new BigDecimal(
                                            Math.floor(minMagnitude / dm) * dm
                                                    + dm / 2).setScale(2,
                                            BigDecimal.ROUND_HALF_UP)
                                            .doubleValue();
                            mmaxR =
                                    new BigDecimal(Math.ceil(maxMag / dm) * dm
                                            - dm / 2).setScale(2,
                                            BigDecimal.ROUND_HALF_UP)
                                            .doubleValue();
                            // check if this operation makes mmaxR less than
                            // mminR
                            if (mmaxR < mminR) {
                                System.out
                                        .println("Maximum magnitude less than minimum magnitude!!! Check for rounding algorithm!");
                                System.exit(0);
                            }
                        } else {
                            mminR =
                                    new BigDecimal(
                                            Math.floor(minMagnitude / dm) * dm)
                                            .setScale(2,
                                                    BigDecimal.ROUND_HALF_UP)
                                            .doubleValue();
                            mmaxR =
                                    new BigDecimal(Math.ceil(maxMag / dm) * dm)
                                            .setScale(2,
                                                    BigDecimal.ROUND_HALF_UP)
                                            .doubleValue();
                        }

                        // calculate the number of magnitude values
                        int numMag = (int) Math.round((mmaxR - mminR) / dm) + 1;

                        // magnitude frequency distribution
                        IncrementalMagFreqDist mfd =
                                new GutenbergRichterMagFreqDist(bVal,
                                        totCumRate, mminR, mmaxR, numMag);

                        // focal mechanism
                        FocalMechanism fm =
                                new FocalMechanism(strike, dip, rake);

                        // magnitude freq dist for focal mechanism
                        magfreqDistFocMech =
                                new MagFreqDistsForFocalMechs(mfd, fm);

                        // top of rupture distribution
                        // the australia model has a uniform top of rupture
                        // distribution
                        EvenlyDiscretizedFunc topr =
                                new EvenlyDiscretizedFunc(mminR, mmaxR, numMag);
                        for (int im = 0; im < numMag; im++)
                            topr.set(im, depth);

                        // average rupture top depth vs. magnitude
                        aveRupTopVsMag = new ArbitrarilyDiscretizedFunc(topr);

                        aveHypoDepth = depth;

                    } // end recurrence model

                } // end loop over children objects

                // go through the excluded regions and check if there are some
                // that overlaps
                // if so join them
                ArrayList<Region> newExcRegList = new ArrayList<Region>();
                Region newExcReg = null;
                for (int ier = 0; ier < listExReg.size(); ier++) {
                    newExcReg = listExReg.get(ier);
                    // loop over the remaining zones
                    for (int ierr = ier + 1; ierr < listExReg.size(); ierr++) {
                        if (Region.union(newExcReg, listExReg.get(ierr)) != null) {
                            newExcReg =
                                    Region.union(newExcReg, listExReg.get(ierr));
                            listExReg.remove(ierr);
                        }
                    }
                    newExcRegList.add(newExcReg);
                }

                // exclude regions from polygon
                for (int ier = 0; ier < newExcRegList.size(); ier++) {
                    PolygonRegion.addInterior(newExcRegList.get(ier));
                }

                srcDataList.add(new GEMAreaSourceData(Integer.toString(i + 1),
                        Integer.toString(i + 1), trt, PolygonRegion,
                        magfreqDistFocMech, aveRupTopVsMag, aveHypoDepth));

            } // end loop over polygons

        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    // main method for testing
    public static void main(String[] args) throws IOException {

        // read input file and create array list of GEMSourceData
        australia2GemSourceData model = new australia2GemSourceData();

        model.writeAreaSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/AustraliaAreaSources.kml"));

    }

}
