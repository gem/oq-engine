package org.gem.engine.hazard.parsers.ecuador;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.ArrayList;
import java.util.ListIterator;
import java.util.StringTokenizer;
import java.util.regex.Pattern;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class ecuador2GemSourceData extends GemFileParser {

    private static BorderType borderType = BorderType.GREAT_CIRCLE;

    // magnitude bin width for magnitude frequency distribution
    private static double dm = 0.1;

    // minimum magnitude for hazard calculations
    private static double minMagnitude = 4.5;

    // tectonic region for Ecuador
    private TectonicRegionType trt = TectonicRegionType.ACTIVE_SHALLOW;

    // focal mechanism (These values are arbitrarily chosen
    // because the model do not provide this info)
    // This is something that must be improved
    private double strike = -999.0;
    private double dip = -999.0;
    private double rake = 0.0;

    // average hypocentral depth
    private double aveHypoDepth = 10.0;

    public ecuador2GemSourceData() throws IOException {

        // input file containing source geometries
        String inputfile1 = "ecuador/fuentes_corticales.txt";
        // input file containing seismicity parameters
        String inputfile2 = "ecuador/tmp-param.txt";

        // initialize array list of GEMSourceData
        srcDataList = new ArrayList<GEMSourceData>();

        String sRecord = null;
        StringTokenizer st = null;

        BufferedReader oReader =
                new BufferedReader(new FileReader(this.getClass()
                        .getClassLoader().getResource(inputfile1).getPath()));

        // array list of source names
        ArrayList<String> sourceNames = new ArrayList<String>();
        // array list of polygon boundaries
        ArrayList<LocationList> sourcePolygons = new ArrayList<LocationList>();

        // source index
        int sourceIndex = 0;
        // start reading
        while ((sRecord = oReader.readLine()) != null) {

            // source name
            String sourceName = null;
            // longitude
            Double lon = null;
            // latitude
            Double lat = null;

            if (sRecord.isEmpty()) {
                continue;
            } else if (isNum(new StringTokenizer(sRecord).nextToken())) {
                // read coordinates
                st = new StringTokenizer(sRecord);
                // longitude
                lon = Double.parseDouble(st.nextToken());
                // latitude
                lat = Double.parseDouble(st.nextToken());
                // add coordinates to list
                sourcePolygons.get(sourceIndex - 1).add(new Location(lat, lon));
            } else {
                // read source name
                sourceName = sRecord;
                // add source name to list
                sourceNames.add(sourceIndex, sourceName);
                // add new location list
                sourcePolygons.add(sourceIndex, new LocationList());
                // increment source index
                sourceIndex = sourceIndex + 1;
            }

        } // end of source geometry file
        oReader.close();

        // read seismicity parameter file
        oReader =
                new BufferedReader(new FileReader(this.getClass()
                        .getClassLoader().getResource(inputfile2).getPath()));

        // array list of cumulative annual rates
        ArrayList<Double> totCumRates = new ArrayList<Double>();
        // array list of b values
        ArrayList<Double> bValues = new ArrayList<Double>();
        // maximum magnitude
        ArrayList<Double> mMax = new ArrayList<Double>();

        // read header
        sRecord = oReader.readLine();
        // read seismicity parameters
        while ((sRecord = oReader.readLine()) != null) {

            st = new StringTokenizer(sRecord);
            // skip source number
            st.nextToken();
            // read total cumulative rate
            totCumRates.add(Double.parseDouble(st.nextToken()));
            // read b value
            bValues.add(Double.parseDouble(st.nextToken()));
            // read maximum magnitude
            mMax.add(Double.parseDouble(st.nextToken()));

        }// end seismicity parameter file
        oReader.close();

        // list source names
        for (String name : sourceNames)
            System.out.println(sourceNames.indexOf(name) + 1 + " " + name);

        // check if number of seismicity parameter sets is the same of source
        // polygons
        System.out.println("Number of polygons: " + sourcePolygons.size()
                + ", number of b values: " + bValues.size());

        // create sources
        // loop over sources
        for (int i = 0; i < sourceNames.size(); i++) {

            System.out.println("Source name: " + sourceNames.get(i));
            System.out.println("Source polygon:");
            for (Location loc : sourcePolygons.get(i)) {
                System.out
                        .println(loc.getLongitude() + " " + loc.getLatitude());
            }

            // create region
            Region reg = new Region(sourcePolygons.get(i), borderType);

            // create magnitude frequency distribution
            // calculate number of values
            int numVal =
                    (int) (((mMax.get(i) - dm / 2) - (minMagnitude + dm / 2))
                            / dm + 1);
            GutenbergRichterMagFreqDist mfd =
                    new GutenbergRichterMagFreqDist(bValues.get(i),
                            totCumRates.get(i), minMagnitude + dm / 2,
                            mMax.get(i) - dm / 2, numVal);

            // focal mechanism
            FocalMechanism fm = new FocalMechanism(strike, dip, rake);

            // pair mfd-fm
            MagFreqDistsForFocalMechs mfdFm =
                    new MagFreqDistsForFocalMechs(mfd, fm);

            // average rupture top vs. magnitude
            ArbitrarilyDiscretizedFunc aveRupTopVsMag =
                    new ArbitrarilyDiscretizedFunc();
            ListIterator<Double> magIter = mfd.getXValuesIterator();
            while (magIter.hasNext())
                aveRupTopVsMag.set(magIter.next(), aveHypoDepth);

            // create GEMAreaSourceData
            srcDataList.add(new GEMAreaSourceData(Integer.toString(i + 1),
                    sourceNames.get(i), trt, reg, mfdFm, aveRupTopVsMag,
                    aveHypoDepth));

        }

    }

    private static boolean isNum(String s) {
        try {
            Double.parseDouble(s);
        } catch (NumberFormatException nfe) {
            return false;
        }
        return true;
    }

    // for testing
    public static void main(String[] args) throws IOException {

        ecuador2GemSourceData model = new ecuador2GemSourceData();
        model.writeAreaSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/EcuadorSource.kml"));
        // model.writeSource2CLformat(new
        // FileWriter("/Users/damianomonelli/Desktop/EcuadorSource.dat"));

    }

}
