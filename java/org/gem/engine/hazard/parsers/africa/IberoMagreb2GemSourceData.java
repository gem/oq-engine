package org.gem.engine.hazard.parsers.africa;

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
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;

import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Region;

import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This parser reads the GSHAP input mode for Ibero-Magreb Region. The original
 * input reports the following seismcity parameters: earthquakes/year km2 b-val
 * Mmax
 * 
 * @author l.danciu
 * 
 * */

public class IberoMagreb2GemSourceData extends GemFileParser {

    // magnitude bin width used to compute the final mfd
    private static double dm = 0.1;

    // reported minimum magnitude
    private static double minMag = 4.00;

    // Minimum magnitude used in calculation of the hazard
    private static double calcMinMag = 5.00;

    // specifies how lines connecting two points on the earth's surface should
    // be represented
    // used as argument for default method in Region class
    private static BorderType borderType = BorderType.GREAT_CIRCLE;

    // tectonic regions defined in the model
    private TectonicRegionType trt1 = TectonicRegionType.ACTIVE_SHALLOW;

    // focal mechanism (default values)
    private double strike = 0.0;
    private double dip = 90.0;
    private double rake = 0.0;

    // constructor
    public IberoMagreb2GemSourceData(String inputfile)
            throws FileNotFoundException {

        // ArrayList of GEM area sources
        srcDataList = new ArrayList<GEMSourceData>();

        String myClass =
                '/' + getClass().getName().replace('.', '/') + ".class";
        URL myClassURL = getClass().getResource(myClass);
        if ("jar" == myClassURL.getProtocol()) {
            inputfile = inputfile.substring(inputfile.lastIndexOf("./") + 1);
        }
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
                // bVal(GR); occRateN/year/km2; aValN - aVal normalized per
                // year/km2, Maximum Magnitude
                // aValN is used to recompute the occRate/year
                double bGR, occRateNor, aGRNor, maxMag;
                double aveHypoDepth = 15;

                // provided occurrence rate above minimum magnitude
                occRateNor = Double.valueOf(st.nextToken()).doubleValue();

                // b-value value (GuttenberRichter law)
                bGR = Double.valueOf(st.nextToken()).doubleValue();

                // Maximum Magnitude
                maxMag = Double.valueOf(st.nextToken()).doubleValue();

                // compute aVal (GuttenberRichter law)
                aGRNor =
                        Math.log10(occRateNor
                                / (Math.pow(10, -bGR * minMag) - Math.pow(10,
                                        -bGR * maxMag)));

                // System.out.println(" " + occRateNor + " " + bGR + " " +
                // maxMag + " " +aGRNor);

                // read polygon coordinates
                Region srcRegion = null;
                LocationList srcBoundary = new LocationList();
                while ((sRecord = oReader.readLine()) != null
                        && (new StringTokenizer(sRecord).nextToken()
                                .equalsIgnoreCase("source")) == false) {

                    st = new StringTokenizer(sRecord);

                    double lat = Double.valueOf(st.nextToken()).doubleValue();
                    double lon = Double.valueOf(st.nextToken()).doubleValue();
                    // System.out.println(lat+" "+lon);

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
                // Remove Sources with Mmax<Mmin(5.0)
                if (maxMag < calcMinMag)
                    continue;

                // Create a temp src.object in order to obtain the area in km2
                GEMAreaSourceData srctmp =
                        new GEMAreaSourceData(Integer.toString(srcIndex),
                                sourceName, null, srcRegion, null, null,
                                aveHypoDepth);
                double area_srctmp = srctmp.getArea();
                // Recompute the aGR from aGRNor
                // relationship used: aGRNor = aGR-log10(area)
                double aGR = aGRNor + Math.log10(area_srctmp);
                double occRate =
                        Math.pow(10, aGR - bGR * (calcMinMag))
                                - Math.pow(10, aGR - bGR * ((maxMag)));
                // System.out.println("aGR: " + aGR);
                // System.out.println("Area: " + area_srctmp);
                // System.out.println("occRate: " + occRate);

                // Round magnitude interval extremes (with respect to default
                // dm) and move to bin center
                // (if the minimum and maximum magnitudes are different)
                double mmaxR;
                double mminR;
                if (calcMinMag != maxMag) {
                    mminR =
                            new BigDecimal(Math.round(calcMinMag / dm) * dm
                                    + dm / 2).setScale(2,
                                    BigDecimal.ROUND_HALF_UP).doubleValue();
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
                            new BigDecimal(Math.round(calcMinMag / dm) * dm)
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
                mfd.setAllButTotMoRate(mminR, mmaxR, occRate, bGR);
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

                // create GEMAreaSource
                srcIndex = srcIndex + 1;
                GEMAreaSourceData src =
                        new GEMAreaSourceData(Integer.toString(srcIndex),
                                sourceName, trt1, srcRegion, mfdffm,
                                aveRupTopVsMag, aveHypoDepth);

                srcDataList.add(src);

            } // end loop over sources

        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    // for testing
    // public static void main(String[] args) throws IOException,
    // ClassNotFoundException {
    //
    // IberoMagreb2GemSourceData IberoMagrebModel = new
    // IberoMagreb2GemSourceData
    // ("../../data/IberoMagreb/IberoMagrebInput.dat");
    //
    // // FileWriter file = new FileWriter("IberoMagrebAreaGMT.dat");
    // //
    // // IberoMagrebModel.writeAreaGMTfile (file);
    // }
}
