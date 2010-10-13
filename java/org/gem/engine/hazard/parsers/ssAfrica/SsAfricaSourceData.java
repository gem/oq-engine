package org.gem.engine.hazard.parsers.ssAfrica;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class SsAfricaSourceData extends GemFileParser {

    private static double MMIN = 5.0;

    public SsAfricaSourceData() throws FileNotFoundException {
        double mwid = 0.1;

        String pathInp = "gshap/africa/ssAfrica/";
        String srcfle = pathInp + "source.dat";
        String seifle = pathInp + "sourceSeismicity.dat";

        BufferedReader oReaderSrc =
                new BufferedReader(new FileReader(this.getClass()
                        .getClassLoader().getResource(srcfle).getPath()));
        BufferedReader oReaderSei =
                new BufferedReader(new FileReader(this.getClass()
                        .getClassLoader().getResource(seifle).getPath()));

        // Read data from files
        ArrayList<SsAfricaSourceGeometry> srcGeomList = null;
        try {
            srcGeomList = getSourceGeometry(oReaderSrc);
        } catch (IOException e) {

            e.printStackTrace();
        }
        HashMap<Integer, SsAfricaSourceSeismicity> seiList = null;
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
            SsAfricaSourceGeometry srcGeo = srcGeomList.get(i);

            String id = String.format("%4d", i);
            String name = String.format("%3d", srcGeo.getId());
            LocationList locList = new LocationList();

            for (Location loc : srcGeo.getVertexes()) {
                locList.add(loc);
            }

            System.out.println("Source " + srcGeo.getId());
            double lambda = seiList.get(srcGeo.getId()).getLambda();
            System.out.println("  lambda: " + lambda);
            double bGR =
                    seiList.get(srcGeo.getId()).getBeta() * Math.log10(Math.E);
            System.out.printf("  bGR: %6.3f\n", bGR);
            double mmin = seiList.get(srcGeo.getId()).getMMin();
            double mmax = seiList.get(srcGeo.getId()).getMMax();

            // Define the discretized function to store the average depth to the
            // top of rupture
            ArbitrarilyDiscretizedFunc depTopRup =
                    new ArbitrarilyDiscretizedFunc();

            // Calculate the Incremental magnitude-frequency distribution
            int num =
                    (int) Math
                            .round((seiList.get(srcGeo.getId()).getMMax() - MMIN)
                                    / mwid);
            IncrementalMagFreqDist mfd =
                    new IncrementalMagFreqDist(MMIN + mwid / 2, seiList.get(
                            srcGeo.getId()).getMMax()
                            - mwid / 2, num);

            double aGR =
                    Math.log10(lambda
                            / (Math.pow(10, -bGR * mmin) - Math.pow(10, -bGR
                                    * mmax)));
            for (int j = 0; j < mfd.getNum() - 1; j++) {
                double rate =
                        Math.pow(10, aGR - bGR * (j * mwid + MMIN))
                                - Math.pow(10, aGR - bGR
                                        * ((j + 1) * mwid + MMIN));
                mfd.add(j, rate);
                System.out.printf("%5.2f %7.5f\n", mfd.getX(j), rate);
                depTopRup.set(MMIN + j * mwid, 5.0);
            }

            // MFD for focal mechanism
            FocalMechanism fm = new FocalMechanism();
            IncrementalMagFreqDist[] arrMfd = new IncrementalMagFreqDist[1];
            arrMfd[0] = mfd;

            FocalMechanism[] arrFm = new FocalMechanism[1];
            arrFm[0] = fm;
            MagFreqDistsForFocalMechs mfdffm =
                    new MagFreqDistsForFocalMechs(arrMfd, arrFm);

            // Instantiate the region
            Region reg = new Region(locList, null);

            // Shallow active tectonic sources
            GEMAreaSourceData src =
                    new GEMAreaSourceData("0", name,
                            TectonicRegionType.ACTIVE_SHALLOW, reg, mfdffm,
                            depTopRup, 5.0);
            srcList.add(src);
        }
        this.setList(srcList);

    }

    /**
     * @throws IOException
     * @throws NumberFormatException
     * 
     */
    public static HashMap<Integer, SsAfricaSourceSeismicity>
            getSourceSeismicity(BufferedReader oReaderSei)
                    throws NumberFormatException, IOException {

        String line;
        String[] aa;
        HashMap<Integer, SsAfricaSourceSeismicity> seiMap =
                new HashMap<Integer, SsAfricaSourceSeismicity>();

        // Open Read buffer
        BufferedReader input = new BufferedReader(oReaderSei);
        try {
            while ((line = input.readLine()) != null) {
                aa = line.split(" ");
                int id = Integer.valueOf(aa[0]).intValue();
                double mmin = Double.valueOf(aa[1]).doubleValue();
                double mmax = Double.valueOf(aa[2]).doubleValue();

                double beta = Double.valueOf(aa[3]).doubleValue();
                double lambda = Double.valueOf(aa[4]).doubleValue();
                // System.out.println("-->"+id+" "+mmin+" "+mmax+" "+beta+" "+lambda);
                SsAfricaSourceSeismicity ss =
                        new SsAfricaSourceSeismicity(id, mmin, mmax, beta,
                                lambda);
                seiMap.put(id, ss);
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
    public static ArrayList<SsAfricaSourceGeometry> getSourceGeometry(
            BufferedReader oReaderSrc) throws IOException {

        String line;
        Matcher matcher;
        int id;
        String[] aa;
        double lon, lat;

        // Open Read buffer
        BufferedReader input = new BufferedReader(oReaderSrc);

        // Patterns
        Pattern isSource = Pattern.compile("^source(\\d+)");
        Pattern isFloat =
                Pattern.compile("(-*\\d+\\.*\\d*|-*\\d*\\.*\\d+)\\s+(-*\\d+\\.*\\d*)");

        // Instantiate the container for the sources
        ArrayList<SsAfricaSourceGeometry> sourceGeom =
                new ArrayList<SsAfricaSourceGeometry>();
        SsAfricaSourceGeometry geom = null;
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
                    id = Integer.valueOf(matcher.group(1)).intValue();
                    // System.out.printf("Source: %d\n",id);
                    // Instantiate a new SsAfricaSourceGeometry
                    geom = new SsAfricaSourceGeometry();
                    // Set the ID
                    geom.setId(id);
                    // Prepare the arraylist of Locations
                    locList = new LocationList();
                } else {
                    matcher = isFloat.matcher(line);
                    if (matcher.find()) {
                        lat = Double.valueOf(matcher.group(1)).doubleValue();
                        lon = Double.valueOf(matcher.group(2)).doubleValue();
                        // System.out.printf("lat: %5.2f lon %5.2f\n",lat,lon);
                        locList.add(new Location(lat, lon));
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

}
