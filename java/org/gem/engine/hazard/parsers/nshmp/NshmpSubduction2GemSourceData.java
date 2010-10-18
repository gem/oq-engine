package org.gem.engine.hazard.parsers.nshmp;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.net.URL;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.geo.Location;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.util.FaultTraceUtils;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.ApproxEvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

/**
 * This class reads a NSHMP subduction input file and returns a list of
 * GEMFaultSourceData. The user must provide the file name, the tectonic region,
 * and the file weight (as derived by the logic tree)
 * 
 * @author damianomonelli
 * 
 */

public class NshmpSubduction2GemSourceData extends GemFileParser {

    // array list of GEMFaultSourceData objects
    // private ArrayList<GEMSubductionFaultSourceData> srcDataList;

    // magnitude bin width used in calculations
    private static double dm = 0.1;

    private static double borderThickness = 2.0;

    // constructor
    public NshmpSubduction2GemSourceData(String inputfile,
            TectonicRegionType trt, double fileWeight, double latmin,
            double latmax, double lonmin, double lonmax) throws IOException {

        srcDataList = new ArrayList<GEMSourceData>();

        // allows floating of rupture
        // default is true
        // becomes false only for characteristic faults
        // and for cascadia faults with minimumaMag>=8.8
        boolean floatRuptureFlag = true;

        BufferedReader oReader = new BufferedReader(new FileReader(inputfile));

        String sRecord = null;
        StringTokenizer st = null;

        // ******************** start reading *********************//

        // Integer value indicating where to compute hazard.
        // 0 = grid of sites; 1-31 = list of sites
        sRecord = oReader.readLine();
        st = new StringTokenizer(sRecord);
        int site = Integer.valueOf(st.nextToken()).intValue();
        double minLatSites = 0.0;
        double maxLatSites = 0.0;
        double deltaLatSites = 0.0;
        double minLonSites = 0.0;
        double maxLonSites = 0.0;
        double deltaLonSites = 0.0;
        if (site == 0) {
            // site grid definition
            // minimum latitude, maximum latitude, delta latitude
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            minLatSites = Double.valueOf(st.nextToken()).doubleValue();
            maxLatSites = Double.valueOf(st.nextToken()).doubleValue();
            deltaLatSites = Double.valueOf(st.nextToken()).doubleValue();
            // line 3. (minimum longitude, maximum longitude, delta longitude)
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            minLonSites = Double.valueOf(st.nextToken()).doubleValue();
            maxLonSites = Double.valueOf(st.nextToken()).doubleValue();
            deltaLonSites = Double.valueOf(st.nextToken()).doubleValue();
        } else if (site != 0) {
            double[] staLat = new double[site];
            double[] staLon = new double[site];
            String[] staName = new String[site];
            // loop over stations
            for (int is = 0; is < site; is++) {
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                staLat[is] = Double.valueOf(st.nextToken()).doubleValue();
                staLon[is] = Double.valueOf(st.nextToken()).doubleValue();
                staName[is] = st.nextToken();
            }
        }

        // vs30 (m/s)
        sRecord = oReader.readLine();
        st = new StringTokenizer(sRecord);
        double vs30 = Double.valueOf(st.nextToken()).doubleValue();

        // Number of periods.
        sRecord = oReader.readLine();
        st = new StringTokenizer(sRecord);
        int nPeriod = Integer.valueOf(st.nextToken()).intValue();

        // start loop over periods
        for (int ip = 0; ip < nPeriod; ip++) {

            // read period
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            double period = Double.valueOf(st.nextToken()).doubleValue();

            // name of output file for this period
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            String outFileName = st.nextToken();

            // number of attenuation relationships for this period
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            int nAttenRelPeriod = Integer.valueOf(st.nextToken()).intValue();

            // loop over attenuation relationships
            for (int iar = 0; iar < nAttenRelPeriod; iar++) {

                // type of attenuation relationship, weight, mb to M conv
                sRecord = oReader.readLine();

            } // end loop over attenuation relationship

            // number of ground motion values
            sRecord = oReader.readLine();

            // ground motion values
            sRecord = oReader.readLine();

        }// end loop over periods

        // increment for source elements (floating rupture)
        sRecord = oReader.readLine();

        // distance increment and dmax
        sRecord = oReader.readLine();

        // array list storing subduction faults
        ArrayList<GEMSubductionFaultSourceData> sourceList =
                new ArrayList<GEMSubductionFaultSourceData>();

        // start reading fault info
        int indexSource = 0;

        while ((sRecord = oReader.readLine()) != null) {

            double charMag = Double.NaN;
            double charRate = Double.NaN;

            double minimumMag = Double.NaN;
            double maximumMag = Double.NaN;
            int numMag = 0;
            double aValue = Double.NaN;
            double bValue = Double.NaN;
            double dMag = Double.NaN;

            st = new StringTokenizer(sRecord);
            // System.out.println(st.nextToken());
            // System.out.println(st.nextToken());
            // System.out.println(st.nextToken());

            // fault type
            // 1= Characteristic
            // 2= GR
            int fType = Integer.valueOf(st.nextToken()).intValue();

            // fault mechanism
            // 1= strike slip (rake=0)
            // 2= reverse (rake=90)
            // 3= normal (rake=-90)
            int fMechanism = Integer.valueOf(st.nextToken()).intValue();
            // rake angle
            double rake = 0.0;
            if (fMechanism == 1) {
                rake = 0.0;
            } else if (fMechanism == 2) {
                rake = 90.0;
            } else if (fMechanism == 3) {
                rake = -90.0;
            }

            // read number of magnitude models?

            // fault name
            String fName = "";
            while (st.hasMoreTokens())
                fName = fName + " " + st.nextToken();

            System.out.println("Processing subduction fault: " + fName);

            IncrementalMagFreqDist mfd = null;

            if (fType == 1) {

                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);

                // chracteristic magnitude
                charMag = Double.valueOf(st.nextToken()).doubleValue();

                // characteristic rate
                charRate = Double.valueOf(st.nextToken()).doubleValue();

                // line 620
                // read(1,*) cmag(ift),crate(ift)
                // magmin(ift)=cmag(ift); magmax(ift)=cmag(ift)
                minimumMag = charMag;
                maximumMag = charMag;
                numMag = 1;
            }

            if (fType == 2) { // GR fault

                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);

                // a value
                aValue = Double.valueOf(st.nextToken()).doubleValue();

                // b value
                bValue = Double.valueOf(st.nextToken()).doubleValue();

                // minimum magnitude
                minimumMag = Double.valueOf(st.nextToken()).doubleValue();

                // maximum magnitude
                maximumMag = Double.valueOf(st.nextToken()).doubleValue();

                // magnitude bin width
                dMag = Double.valueOf(st.nextToken()).doubleValue();

                // NOTE! no half bin width correction
                // line 636
                // nmag0(ift)= nint((magmax(ift)-magmin(ift))/dmag(ift)) + 1
                numMag = (int) ((maximumMag - minimumMag) / dMag + 1);
            }

            if (fType == 1) { // Characteristic fault
                mfd =
                        new IncrementalMagFreqDist(minimumMag, maximumMag,
                                numMag);
                mfd.set(minimumMag, fileWeight * charRate);
                floatRuptureFlag = false;
            } else if (fType == 2) { // GR fault
                // mfd = new IncrementalMagFreqDist(minimumMag,maximumMag,dMag);
                mfd = new IncrementalMagFreqDist(minimumMag, numMag, dMag);
                // System.out.println(mfd);
                for (int iv = 0; iv < mfd.getNum(); iv++) {
                    double mag = minimumMag + iv * dMag;
                    // System.out.println(mag);
                    // line 730
                    // rate(m)= a(ift) - b(ift)*xmag
                    mfd.set(mag,
                            fileWeight * Math.pow(10, aValue - bValue * mag));
                }
            }
            // System.exit(0);

            // if Cascadia with minimumMag>8.8
            if (inputfile.startsWith("cascadia") && minimumMag >= 8.8) {
                floatRuptureFlag = false;
            }

            // number of fault top edge coordinates
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            int NTopCoord = Integer.valueOf(st.nextToken()).intValue();

            // loop over top edge coordinates
            FaultTrace faultTopTrace = new FaultTrace(fName);
            for (int itc = 0; itc < NTopCoord; itc++) {
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                double lat = Double.valueOf(st.nextToken()).doubleValue();
                double lon = Double.valueOf(st.nextToken()).doubleValue();
                double depth = Double.valueOf(st.nextToken()).doubleValue();
                faultTopTrace.add(new Location(lat, lon, depth));
            }

            // number of fault bottom edge coordinates
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            int NBotCoord = Integer.valueOf(st.nextToken()).intValue();

            // loop over bottom edge coordinates
            FaultTrace faultBottomTrace = new FaultTrace(fName);
            for (int itc = 0; itc < NBotCoord; itc++) {
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                double lat = Double.valueOf(st.nextToken()).doubleValue();
                double lon = Double.valueOf(st.nextToken()).doubleValue();
                double depth = Double.valueOf(st.nextToken()).doubleValue();
                faultBottomTrace.add(new Location(lat, lon, depth));
            }

            boolean includeSrc = false;
            // loop over top fault trace coordinates
            // if one is inside the region of interest take it
            for (int isp = 0; isp < NTopCoord; isp++) {
                double faultTraceLat = faultTopTrace.get(isp).getLatitude();
                double faultTraceLon = faultTopTrace.get(isp).getLongitude();
                if (faultTraceLat >= latmin - borderThickness
                        && faultTraceLat <= latmax + borderThickness
                        && faultTraceLon >= lonmin - borderThickness
                        && faultTraceLon <= lonmax + borderThickness) {
                    includeSrc = true;
                    break;
                }
            }

            if (includeSrc) {
                // create subduction fault
                GEMSubductionFaultSourceData GEMsf =
                        new GEMSubductionFaultSourceData(faultTopTrace,
                                faultBottomTrace, rake, mfd, floatRuptureFlag);

                // set name
                GEMsf.setName(fName);

                srcDataList.add(GEMsf);
            }

        } // end loop over faults

    }

    /**
     * compute total moment rate
     * 
     * @param mminR
     *            : minimum magnitude (rounded to multiple of mwdt and moved to
     *            bin center)
     * @param numMag
     *            : number of magnitudes
     * @param mwdt
     *            : magnitude bin width
     * @param aVal
     *            : incremental a value (check that it is defined with respect
     *            to mwdt)
     * @param bVal
     *            : b value
     * @return
     */

    public double totMoRate(double mminR, int numMag, double mwdt, double aVal,
            double bVal) {
        double mo = 0;
        double mag;
        for (int imag = 0; imag < numMag; imag++) {
            mag = mminR + imag * mwdt;
            mo += Math.pow(10, aVal - bVal * mag + 1.5 * mag + 9.05);
        }
        return mo;
    }

    /**
     * 
     * @param aVal
     *            : incremental
     * @param bVal
     * @param minMag
     * @param maxMag
     * @param deltaMag
     *            : magnitude bin width used to compute a value
     * @param weight
     *            : to scale the mfd
     * @return
     */
    public IncrementalMagFreqDist computeGRmfd(double aVal, double bVal,
            double minMag, double maxMag, double deltaMag, double weight) {

        // Round magnitude interval extremes (with respect to default dm) and
        // move to bin center
        // (if the minimum and maximum magnitudes are different)
        double mmaxR;
        double mminR;
        if (minMag != maxMag) {
            mminR =
                    new BigDecimal(Math.floor(minMag / dm) * dm + dm / 2)
                            .setScale(2, BigDecimal.ROUND_HALF_UP)
                            .doubleValue();
            mmaxR =
                    new BigDecimal(Math.ceil(maxMag / dm) * dm - dm / 2)
                            .setScale(2, BigDecimal.ROUND_HALF_UP)
                            .doubleValue();
            // check if this operation makes mmaxR less than mminR
            if (mmaxR < mminR) {
                System.out
                        .println("Maximum magnitude less than minimum magnitude!!! Check for rounding algorithm!");
                System.exit(0);
            }
        } else {
            mminR =
                    new BigDecimal(Math.floor(minMag / dm) * dm).setScale(2,
                            BigDecimal.ROUND_HALF_UP).doubleValue();
            mmaxR =
                    new BigDecimal(Math.ceil(maxMag / dm) * dm).setScale(2,
                            BigDecimal.ROUND_HALF_UP).doubleValue();
        }

        // Calculate the number of magnitude intervals
        int numMag = (int) Math.round((mmaxR - mminR) / dm) + 1;

        // recompute a value according to the default dm
        aVal = aVal + Math.log10(dm / deltaMag);

        // compute the total moment rate
        double tmr = totMoRate(mminR, numMag, dm, aVal, bVal);

        GutenbergRichterMagFreqDist mfd =
                new GutenbergRichterMagFreqDist(mminR, mmaxR, numMag);
        mfd.setAllButTotCumRate(mminR, mmaxR, tmr * weight, bVal);

        return mfd;
    }

    // for testing
    public static void main(String[] args) throws IOException {

        String inDir = "../../data/nshmp/south_america/subduction/";

        String inFile = "pan.sub100n.new.in";

        NshmpSubduction2GemSourceData model =
                new NshmpSubduction2GemSourceData(inDir + inFile,
                        TectonicRegionType.SUBDUCTION_INTERFACE, 1.0, -90.0,
                        90.0, -180.0, 180.0);

        model.writeSubductionFaultSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/PanamaSubduction.kml"));

    }

}
