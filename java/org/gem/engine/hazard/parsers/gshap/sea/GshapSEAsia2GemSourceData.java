package org.gem.engine.hazard.parsers.gshap.sea;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.net.URL;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

/**
 * Parser for GSHAP Models
 * 
 * @author l.danciu
 * 
 */
public class GshapSEAsia2GemSourceData extends GemFileParser {

    // magnitude bin width used to compute the final mfd
    private static double dm = 0.1;

    // MinMag for calculation
    private static double minMag = 5.5;

    // MinMag for calculation
    private static double calcMinMag = 5.0;

    // specifies how lines connecting two points on the earth's surface should
    // be represented
    // used as argument for default method in Region class
    private static BorderType borderType = BorderType.GREAT_CIRCLE;

    // tectonic regions defined in the model

    private TectonicRegionType trt1 = TectonicRegionType.STABLE_SHALLOW;
    private TectonicRegionType trt2 = TectonicRegionType.ACTIVE_SHALLOW;
    private TectonicRegionType trt3 = TectonicRegionType.SUBDUCTION_SLAB;

    // focal mechanism (default values)
    private double strike = 0.0;
    private double dip = 90.0;
    private double rake = 0.0;

    /**
     * 
     * @param inputfile
     *            : name of the file containing input model
     * @param trt
     *            : tectonic region
     * @throws FileNotFoundException
     */

    // constructor
    public GshapSEAsia2GemSourceData(String inputfile)
            throws FileNotFoundException {

        // ArrayList of GEM area sources
        srcDataList = new ArrayList<GEMSourceData>();

        BufferedReader oReader =
                new BufferedReader(new FileReader(this.getClass()
                        .getClassLoader().getResource(inputfile).getPath()));

        String sRecord = null;
        StringTokenizer st = null;

        // start reading
        try {

            int srcIndex = 0;

            double minLat = Double.MAX_VALUE;
            double maxLat = Double.MIN_VALUE;
            double minLon = Double.MAX_VALUE;
            double maxLon = Double.MIN_VALUE;

            // start loop over sources
            while ((sRecord = oReader.readLine()) != null) {

                st = new StringTokenizer(sRecord);

                // Source name
                String sourceName = "";
                while (st.hasMoreTokens())
                    sourceName = sourceName + " " + st.nextToken();

                System.out.println(sourceName);

                // Read 2nd Line
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);

                double bVal, occRate, aVal, maxMag, minMag;
                double aveHypoDepth;

                // b-value value (GuttenberRichter law)
                bVal = Double.valueOf(st.nextToken()).doubleValue();

                // occurrence rate above minimum magnitude
                occRate = Double.valueOf(st.nextToken()).doubleValue();

                // depth
                aveHypoDepth = Double.valueOf(st.nextToken()).doubleValue();

                // Maximum Magnitude
                maxMag = Double.valueOf(st.nextToken()).doubleValue();

                // Maximum Magnitude
                minMag = Double.valueOf(st.nextToken()).doubleValue();

                if (minMag == 5.0) {
                    // compute aVal (GuttenberRichter law)
                    aVal =
                            Math.log10(occRate
                                    / (Math.pow(10, -bVal * minMag) - Math.pow(
                                            10, -bVal * maxMag)));
                } else {
                    // compute aVal (GuttenberRichter law)
                    aVal =
                            Math.log10(occRate
                                    / (Math.pow(10, -bVal * minMag) - Math.pow(
                                            10, -bVal * maxMag)));
                    // recalculation of the occRate considering the calcMinMag
                    occRate =
                            Math.pow(10, aVal - bVal * calcMinMag)
                                    - Math.pow(10, aVal - bVal * maxMag);
                }

                System.out.println(bVal + " " + occRate + " " + aVal + " "
                        + maxMag + " " + minMag);

                // read polygon coordinates
                Region srcRegion = null;
                LocationList srcBoundary = new LocationList();
                while ((sRecord = oReader.readLine()) != null
                        && (new StringTokenizer(sRecord).nextToken()
                                .equalsIgnoreCase("source")) == false) {

                    st = new StringTokenizer(sRecord);

                    double lon = Double.valueOf(st.nextToken()).doubleValue();
                    double lat = Double.valueOf(st.nextToken()).doubleValue();

                    System.out.println(lon + " " + lat);

                    if (lat < minLat)
                        minLat = lat;
                    if (lat > maxLat)
                        maxLat = lat;
                    if (lon < minLon)
                        minLon = lon;
                    if (lon > maxLon)
                        maxLon = lon;

                    oReader.mark(1000);

                    // Polygon Boundary
                    srcBoundary.add(new Location(lat, lon));

                }
                oReader.reset();

                // create region
                srcRegion = new Region(srcBoundary, borderType);

                // Round magnitude interval extremes (with respect to default
                // dm) and move to bin center
                // (if the minimum and maximum magnitudes are different)
                double mmaxR;
                double mminR;
                if (minMag != maxMag) {
                    mminR =
                            new BigDecimal(Math.round(minMag / dm) * dm + dm
                                    / 2).setScale(2, BigDecimal.ROUND_HALF_UP)
                                    .doubleValue();
                    mmaxR =
                            new BigDecimal(Math.round(maxMag / dm) * dm - dm
                                    / 2).setScale(2, BigDecimal.ROUND_HALF_UP)
                                    .doubleValue();
                    // check if this operation makes mmaxR less than mminR
                    if (mmaxR < mminR) {
                        System.out
                                .println("Maximum magnitude less than minimum magnitude!!! Check for rounding algorithm!");
                        System.exit(0);
                    }
                } else {
                    mminR =
                            new BigDecimal(Math.round(minMag / dm) * dm)
                                    .setScale(2, BigDecimal.ROUND_HALF_UP)
                                    .doubleValue();
                    mmaxR =
                            new BigDecimal(Math.round(maxMag / dm) * dm)
                                    .setScale(2, BigDecimal.ROUND_HALF_UP)
                                    .doubleValue();
                }

                // calculate the number of magnitude values
                int numMag = (int) Math.round((mmaxR - mminR) / dm) + 1;

                // magnitude frequency distribution
                GutenbergRichterMagFreqDist mfd =
                        new GutenbergRichterMagFreqDist(mminR, numMag, dm);
                // compute mfd setting the total cumulative rate (occRate
                // defined
                // with respect to a minimum magnitude of 3.8)
                mfd.setAllButTotMoRate(mminR, mmaxR, occRate, bVal);
                // setAllButTotCumRate(minX, maxX, totMoRate, bValue);

                // Definiton of top of rupture depth vs magnitude
                EvenlyDiscretizedFunc topr =
                        new EvenlyDiscretizedFunc(mminR, mmaxR, numMag);
                for (int im = 0; im < numMag; im++)
                    topr.set(im, aveHypoDepth);
                ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                        new ArbitrarilyDiscretizedFunc(topr);

                // Create a MFD array
                IncrementalMagFreqDist[] mfdArr = new IncrementalMagFreqDist[1];
                mfdArr[0] = mfd;

                // ArrayList of mfds and focal mechanisms
                FocalMechanism[] focMechArr = new FocalMechanism[1];
                focMechArr[0] = new FocalMechanism(strike, dip, rake);

                // create list of (mag freq dist, focal mechanism)
                // In this case there is only one pair
                MagFreqDistsForFocalMechs mfdffm =
                        new MagFreqDistsForFocalMechs(mfdArr, focMechArr);

                TectonicRegionType trt = null;
                // set tectonics to stable continental regions
                if (aveHypoDepth == 5)
                    trt = trt1;
                if (aveHypoDepth == 15)
                    trt = trt2;
                if (aveHypoDepth == 80)
                    trt = trt3;

                // create GEMAreaSource
                srcIndex = srcIndex + 1;
                GEMAreaSourceData srctmp =
                        new GEMAreaSourceData(Integer.toString(srcIndex),
                                sourceName, trt1, srcRegion, mfdffm,
                                aveRupTopVsMag, aveHypoDepth);

                // System.out.println("Area: " + area_srctmp);

                srcDataList.add(srctmp);

            } // end loop over sources

            System.out.println("minLat: " + minLat + " maxLat: " + maxLat
                    + " minLon: " + minLon + " maxLon: " + maxLon);

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

}
