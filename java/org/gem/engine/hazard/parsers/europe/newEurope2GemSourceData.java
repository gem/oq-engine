package org.gem.engine.hazard.parsers.europe;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class newEurope2GemSourceData extends GemFileParser {

    // Minimum Magnitude reported in the model
    private static double mmin = 3.8;

    // Minimum Magnitude used in the hazard computation
    private static double calcMMIN = 5.0;

    // tectonic regions defined in the model
    private TectonicRegionType trt1 = TectonicRegionType.ACTIVE_SHALLOW;
    private TectonicRegionType trt2 = TectonicRegionType.SUBDUCTION_SLAB;

    // focal mechanism (default values. In the model no info about that)
    // this choice may have effect on the results because B&A2008 use rake angle
    // to define faulting type
    private double strike = 0.0;
    private double dip = 90.0;
    private double rake = 0.0;

    // magnitude frequency distribution discretization interval
    private double mwid = 0.1;

    public newEurope2GemSourceData() throws FileNotFoundException {

        HashMap<String, Integer> excludeList = new HashMap<String, Integer>();
        excludeList.put("Apn14", 1);
        excludeList.put("BI02", 1);
        excludeList.put("Hu15", 1);
        excludeList.put("Mag30", 1);
        excludeList.put("DS12", 1);
        excludeList.put("Ib16", 1);

        String pathInp = "data/europe/";
        // source geometry
        String srcfle = pathInp + "EuropeSeismicSources.dat";
        // seismicity parameters
        String seifle = pathInp + "eurSeis.dat";

        String myClass =
                '/' + getClass().getName().replace('.', '/') + ".class";
        URL myClassURL = getClass().getResource(myClass);
        if ("jar" == myClassURL.getProtocol()) {
            srcfle = srcfle.substring(srcfle.lastIndexOf("./") + 1);
            seifle = seifle.substring(seifle.lastIndexOf("./") + 1);

        }
        BufferedReader oReaderSrc =
                new BufferedReader(new FileReader(this.getClass()
                        .getClassLoader().getResource(srcfle).getPath()));
        BufferedReader oReaderSei =
                new BufferedReader(new FileReader(this.getClass()
                        .getClassLoader().getResource(seifle).getPath()));

        // Read data from files
        ArrayList<EuropeSourceGeometry> srcGeomList = null;
        try {
            srcGeomList = getSourceGeometry(oReaderSrc);
        } catch (IOException e) {

            e.printStackTrace();
        }
        HashMap<String, EuropeSourceSeismicity> seiList = null;
        try {
            seiList = getSourceSeismicity(oReaderSei);
        } catch (NumberFormatException e) {
            e.printStackTrace();

        } catch (IOException e) {
            e.printStackTrace();
        }

        // List of Data source
        ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();

        // Processing sources
        for (int i = 0; i < srcGeomList.size(); i++) {

            EuropeSourceGeometry srcGeo = srcGeomList.get(i);

            String id = String.format("%4d", i);
            String name = String.format("%7s", srcGeo.getId()).trim();

            if (!excludeList.containsKey(name)) {
                LocationList locList = new LocationList();

                for (Location loc : srcGeo.getVertexes()) {
                    locList.add(loc);
                }

                System.out.println("Source >" + name + "<");

                double bVal = seiList.get(srcGeo.getId()).getBVal();
                // System.out.println("  bVal: %6.3f\n"+bVal);
                double occRate = seiList.get(srcGeo.getId()).getOccRate();
                // System.out.printf("  occRate: ",occRate);
                double depth = seiList.get(srcGeo.getId()).getDepth();
                // System.out.printf("  depth: ",depth);
                double mmax = seiList.get(srcGeo.getId()).getMMax();
                // System.out.printf("  mmax: ",mmax);

                // Calculate the Cumulative Magnitude-Frequency Distribution
                int num =
                        (int) Math
                                .round(((mmax - mwid / 2) - (calcMMIN + mwid / 2))
                                        / mwid) + 1;
                GutenbergRichterMagFreqDist mfd =
                        new GutenbergRichterMagFreqDist(calcMMIN + mwid / 2,
                                mmax - mwid / 2, num);

                // computation of aVal considering unbounded GR law
                double aVal = bVal * mmin + Math.log10(occRate);
                // recalculation of the occRate considering the calcMinMag
                occRate = Math.pow(10, aVal - bVal * calcMMIN);

                // compute mfd setting the total cumulative rate (occRate
                // defined
                // with respect to a minimum magnitude of 3.8)
                mfd.setAllButTotMoRate(calcMMIN + mwid / 2, mmax - mwid / 2,
                        occRate, bVal);
                // System.out.println(mfd);

                // Define the discretized function to store the average depth to
                // the top of rupture
                // the top of rupture depth is assumed to be equal to the
                // hypocentral depth
                // reported in the model (no info about top of rupture depth in
                // the original model)
                ArbitrarilyDiscretizedFunc depTopRup =
                        new ArbitrarilyDiscretizedFunc();
                for (int j = 0; j < mfd.getNum(); j++) {
                    depTopRup.set(calcMMIN + j * mwid, depth);
                }

                // array list of mfds
                IncrementalMagFreqDist[] arrMfd = new IncrementalMagFreqDist[1];
                arrMfd[0] = mfd;
                // array list of focal mechanisms
                FocalMechanism[] arrFm = new FocalMechanism[1];
                arrFm[0] = new FocalMechanism(strike, dip, rake);
                // definition of the MagFreqDistForFocalMechs object
                MagFreqDistsForFocalMechs mfdffm =
                        new MagFreqDistsForFocalMechs(arrMfd, arrFm);

                // Instantiate the region
                Region reg = new Region(locList, null);

                TectonicRegionType trt = null;
                if (depth <= 12)
                    trt = trt1;
                if (depth > 12)
                    trt = trt2;

                // Shallow active tectonic sources
                GEMAreaSourceData src =
                        new GEMAreaSourceData(Integer.toOctalString(i), name,
                                trt, reg, mfdffm, depTopRup, depth);

                srcList.add(src);
            } else {
                System.out.println("skipping " + name);
            }

        }
        this.setList(srcList);

    }

    /**
     * @throws IOException
     * @throws NumberFormatException
     * 
     */
    public static HashMap<String, EuropeSourceSeismicity> getSourceSeismicity(
            BufferedReader oReaderSei) throws NumberFormatException,
            IOException {

        String line;
        String[] aa;
        HashMap<String, EuropeSourceSeismicity> seiMap =
                new HashMap<String, EuropeSourceSeismicity>();

        // Open Read buffer
        BufferedReader input = new BufferedReader(oReaderSei);
        try {
            while ((line = input.readLine()) != null) {
                aa = line.split("          ");
                String id = aa[0];
                double bVal = Double.valueOf(aa[1]).doubleValue();
                double lambda = Double.valueOf(aa[2]).doubleValue();
                double depth = Double.valueOf(aa[3]).doubleValue();
                double mmax = Double.valueOf(aa[4]).doubleValue();
                // double mmin = Double.valueOf(aa[1]).doubleValue();

                // System.out.println("-->"+id+" "+mmin+" "+mmax+" "+beta+" "+lambda);
                EuropeSourceSeismicity eurmod =
                        new EuropeSourceSeismicity(id, bVal, lambda, depth,
                                mmax);
                seiMap.put(id, eurmod);
            }
        } finally {
            input.close();
        }
        return seiMap;
    }

    /**
     * 
     * @param fleName
     * @throws IOException
     */
    public static ArrayList<EuropeSourceGeometry> getSourceGeometry(
            BufferedReader oReaderSrc) throws IOException {

        String line;
        Matcher matcher;
        String id;
        String[] aa;
        double lon, lat;

        // Open Read buffer
        BufferedReader input = new BufferedReader(oReaderSrc);

        // Patterns
        Pattern isSource = Pattern.compile("^[sS]ource\\s+(.*)");
        Pattern isFloat =
                Pattern.compile("(-*\\d+\\.*\\d*|-*\\d*\\.*\\d+)\\s+(-*\\d+\\.*\\d*)");

        // Instantiate the container for the sources
        ArrayList<EuropeSourceGeometry> sourceGeom =
                new ArrayList<EuropeSourceGeometry>();
        EuropeSourceGeometry geom = null;
        LocationList locList = null;

        try {
            while ((line = input.readLine()) != null) {
                matcher = isSource.matcher(line);
                if (matcher.find()) {
                    // Add the geometry to the container
                    if (geom != null) {
                        geom.setVertexes(locList);
                        sourceGeom.add(geom);
                    }
                    // Get the source ID
                    // id = String.valueOf(matcher.group(1)).intValue();
                    id = matcher.group(1).toString();
                    System.out.printf("Source: %s\n", id);
                    // Instantiate a new EuropeSourceGeometry
                    geom = new EuropeSourceGeometry();
                    // Set the ID
                    geom.setId(id);
                    // Prepare the arraylist of Locations
                    locList = new LocationList();
                } else {
                    matcher = isFloat.matcher(line);
                    if (matcher.find()) {
                        lon = Double.valueOf(matcher.group(2)).doubleValue();
                        lat = Double.valueOf(matcher.group(1)).doubleValue();
                        System.out.printf("lon: %5.2f lat %5.2f\n", lon, lat);
                        locList.add(new Location(lon, lat));
                    }
                }
            }
        } finally {
            if (geom != null) {
                geom.setVertexes(locList);
                sourceGeom.add(geom);
            }
            input.close();
        }
        return sourceGeom;
    }

    // // for testing
    public static void main(String[] args) throws IOException,
            ClassNotFoundException {

        newEurope2GemSourceData europeModel = new newEurope2GemSourceData();

        FileWriter file =
                new FileWriter(
                        "/Users/laurentiudanciu/Desktop/EuropeAreaGMT.dat");

        europeModel.writeAreaGMTfile(file);

    }
}
