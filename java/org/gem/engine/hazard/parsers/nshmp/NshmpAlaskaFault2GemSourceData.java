package org.gem.engine.hazard.parsers.nshmp;

import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.URL;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class NshmpAlaskaFault2GemSourceData extends GemFileParser {

    // array list of GEMFaultSourceData objects
    // private ArrayList<GEMFaultSourceData> srcDataList;

    // magnitude bin width used to compute the final mfd
    private static double dm = 0.1;

    // truncation type for characteristic model
    private static int truncType = 2;

    // if true print out MFDs
    private static boolean printMFD = false;
    // directory where to print out the MFDs
    private String outDirMFD = "/Users/damianomonelli/Desktop/WusFaultMFD/";

    private static double borderThickness = 2.0;

    // bidimensional array storing faults in a cluster
    // first index is the group, second index the segment
    private GEMFaultSourceData[][] clusterFault;

    /**
     * 
     * @param inputfile
     *            : name of the file containing input fault model
     * @param trt
     *            : tectonic region
     * @param fileWeight
     *            : weight of the fault model in the logic tree
     * @throws FileNotFoundException
     */
    // constructor
    public NshmpAlaskaFault2GemSourceData(String inputfile,
            TectonicRegionType trt, double fileWeight, double latmin,
            double latmax, double lonmin, double lonmax)
            throws FileNotFoundException {

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

        // create file where to output the magnitude frequency distribution
        String inputfileMFD = null;
        FileOutputStream oOutFIS = null;
        BufferedOutputStream oOutBIS = null;
        BufferedWriter oWriter = null;
        if (printMFD) {
            inputfileMFD =
                    outDirMFD
                            + inputfile
                                    .substring(inputfile.lastIndexOf("/") + 1)
                            + ".mfd";
            oOutFIS = new FileOutputStream(inputfileMFD);
            oOutBIS = new BufferedOutputStream(oOutFIS);
            oWriter = new BufferedWriter(new OutputStreamWriter(oOutBIS));
        }

        // start reading
        try {

            double minLatSites = 0.0;
            double maxLatSites = 0.0;
            double deltaLatSites = 0.0;
            double minLonSites = 0.0;
            double maxLonSites = 0.0;
            double deltaLonSites = 0.0;
            // site grid definition
            // (minimum latitude, maximum latitude, delta latitude)
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            minLatSites = Double.valueOf(st.nextToken()).doubleValue();
            maxLatSites = Double.valueOf(st.nextToken()).doubleValue();
            deltaLatSites = Double.valueOf(st.nextToken()).doubleValue();
            // (minimum longitude, maximum longitude, delta longitude)
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            minLonSites = Double.valueOf(st.nextToken()).doubleValue();
            maxLonSites = Double.valueOf(st.nextToken()).doubleValue();
            deltaLonSites = Double.valueOf(st.nextToken()).doubleValue();

            // Distance increment that is no longer used, maximum distance
            // beyond which sources are ignored
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            double distIncr = Double.valueOf(st.nextToken()).doubleValue();
            double maxDist = Double.valueOf(st.nextToken()).doubleValue();

            // line 6. Number of periods.
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            int nPeriod = Integer.valueOf(st.nextToken()).intValue();

            // start loop over periods
            for (int ip = 0; ip < nPeriod; ip++) {

                // read period and wind parameter
                // (the wind parameter is used to determine if additional
                // epistemic uncertainty will be added or subtracted from the
                // log(median) of each relation for that period)
                // Note: there is a third parameter in this line but I do not
                // know the meaning
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                double period = Double.valueOf(st.nextToken()).doubleValue();
                double sigmanf = Double.valueOf(st.nextToken()).doubleValue();
                double distnf = Double.valueOf(st.nextToken()).doubleValue();

                // name of the corresponding output file
                sRecord = oReader.readLine();

                // number of ground motion levels
                sRecord = oReader.readLine();

                // ground motion levels
                sRecord = oReader.readLine();

                // number of attenuation relationships for this period
                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);
                int nAttenRel = Integer.valueOf(st.nextToken()).intValue();

                // loop over attenuation relationships
                for (int iar = 0; iar < nAttenRel; iar++) {

                    // type of attenuation relation, weight, wtdist (?),
                    // weight2 (?), mv to M conversion (?)
                    sRecord = oReader.readLine();
                    st = new StringTokenizer(sRecord);

                    // type of attenuation relation
                    int iatten = Integer.valueOf(st.nextToken()).intValue();

                    if (iatten == 1) {
                        sRecord = oReader.readLine();
                    } else if (iatten == 2) {
                        sRecord = oReader.readLine();
                    } else if (iatten == 3) {
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                    } else if (iatten == 4) {
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                    } else if (iatten == 5) {
                        sRecord = oReader.readLine();
                    } else if (iatten == 6) {
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                    } else if (iatten == 7) {
                        sRecord = oReader.readLine();
                    } else if (iatten == 8) {
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                    } else if (iatten == 9) {
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                    } else if (iatten == 10) {
                        sRecord = oReader.readLine();
                        sRecord = oReader.readLine();
                    } else if (iatten == 11) {
                        sRecord = oReader.readLine();
                    } else if (iatten == 12) {
                        sRecord = oReader.readLine();
                    }
                }
            }

            // dlen (fault discretization) and dmove (floating offset)
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            double dlen = Double.valueOf(st.nextToken()).doubleValue();
            double dmove = Double.valueOf(st.nextToken()).doubleValue();

            // number of branches for Mchar/Mmax epistemic uncertainties
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            int nEpiUnc = Integer.valueOf(st.nextToken()).intValue();
            double[] dmM = new double[nEpiUnc];

            // loop over branches
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            for (int iepi = 0; iepi < nEpiUnc; iepi++) {
                // dM for each branch
                dmM[iepi] = Double.valueOf(st.nextToken()).doubleValue();
            }

            // loop over branches
            double[] dmW = new double[nEpiUnc];
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            for (int iepi = 0; iepi < nEpiUnc; iepi++) {
                // weight for each branch
                dmW[iepi] = Double.valueOf(st.nextToken()).doubleValue();
            }

            // standard deviation of Mchar and num samples of Gauss dist on each
            // side of Mchar in units of (2/5)*sigma
            // for example, for stdMchar=0.12 and widthMchar=5 means it's
            // trucated at +/- 2sigma
            // NOTE: is Mchar is negative maintain total rate as given on input,
            // otherwise maintain moment rate
            sRecord = oReader.readLine();
            st = new StringTokenizer(sRecord);
            // this is the sdal in the USGS code
            double stdMchar = Double.valueOf(st.nextToken()).doubleValue();
            // number of samples on each side in terms of units of 2/5 of sigma
            double widthMchar = Double.valueOf(st.nextToken()).doubleValue();

            // source index
            int sourceIndex = 0;

            // loop over fault sources
            while ((sRecord = oReader.readLine()) != null) {

                // this variable tries to mimic what is done by the itest
                // variable defined in hazFXnga7c.f
                // itest = 0 -> apply epistemic uncertainties
                // itest = 1 -> do not apply epistemic uncertainties
                // for each fault the default is 0
                int itest = 0;

                // true if rupture floating is allowed (that is for GR)
                // false if not (that is for Characteristic faults)
                // default is true. It is changed to false only if
                // the fault is treated as characteristic.
                boolean floatRuptureFlag = true;

                st = new StringTokenizer(sRecord);

                // fault type
                // 1= Characteristic
                // 2= GR
                // -2= is a trick number, it means n branches are specified,
                // and n others with b value=0 are derived.
                int FType = Integer.valueOf(st.nextToken()).intValue();

                // fault mechanism
                // 1= strike slip (rake=0)
                // 2= reverse (rake=90)
                // 3= normal (rake=-90)
                int FMechanism = Integer.valueOf(st.nextToken()).intValue();
                // rake angle
                double rake = 0.0;
                if (FMechanism == 1) {
                    rake = 0.0;
                } else if (FMechanism == 2) {
                    rake = 90.0;
                } else if (FMechanism == 3) {
                    rake = -90.0;
                }

                // number of magnitude branches
                // in the alaska model there are no magnitude branches
                // so I put it to 1
                int NMagBranches = 1;

                // other integer (?) (to describe recurrance model origin?)
                // int undefinedInt1 =
                // Integer.valueOf(st.nextToken()).intValue();

                // fault id
                // int FId = Integer.valueOf(st.nextToken()).intValue();

                // fault name (it may also contains the fault ID) - NEED TO
                // CLEAN THIS LATER
                String FName = "";
                while (st.hasMoreTokens()) {
                    String token = st.nextToken();
                    // if(checkIfNumber(token.substring(0, 1))){
                    // continue;
                    // }
                    // else if(token.substring(0, 1).equalsIgnoreCase("!") ||
                    // token.equalsIgnoreCase("combined") ||
                    // token.substring(0, 1).equalsIgnoreCase("'")){
                    // break;
                    // }
                    // else{
                    FName = FName + " " + token;
                    // }
                }

                // array list storing mfds for each magnitude model
                ArrayList<IncrementalMagFreqDist> mfds =
                        new ArrayList<IncrementalMagFreqDist>();

                // System.out.println("Fault: "+FName);

                // parameters for GR
                double[] aVal = null;
                double[] bVal = null;
                double[] minMag = null;
                double[] maxMag = null;
                double[] dMag = null;
                double[] magWeight = null;
                int[] nmag = null;

                // parameters for Characteristic
                // array of characteristic magnitudes
                double[] CharM = null;
                // array of characteristic rates
                double[] CharRate = null;

                if (FType == 2 || FType == -2) {

                    if (FType == 2) { // GR fault

                        // array of a values
                        aVal = new double[NMagBranches];
                        // array of b values
                        bVal = new double[NMagBranches];
                        // array of minimum magnitudes
                        minMag = new double[NMagBranches];
                        // array of maximum magnitudes
                        maxMag = new double[NMagBranches];
                        // array of bin widths
                        dMag = new double[NMagBranches];
                        // array of relative weights
                        magWeight = new double[NMagBranches];
                        // array list of number of magnitude values
                        nmag = new int[NMagBranches];

                        // loop over mag-area relationships
                        for (int imag = 0; imag < NMagBranches; imag++) {

                            sRecord = oReader.readLine();
                            st = new StringTokenizer(sRecord);

                            if (st.countTokens() == 5) {

                                // incremental a value
                                aVal[imag] =
                                        Double.valueOf(st.nextToken())
                                                .doubleValue();

                                // b value
                                bVal[imag] =
                                        Double.valueOf(st.nextToken())
                                                .doubleValue();

                                // minimum magnitude
                                minMag[imag] =
                                        Double.valueOf(st.nextToken())
                                                .doubleValue();

                                // maximum magnitude
                                maxMag[imag] =
                                        Double.valueOf(st.nextToken())
                                                .doubleValue();

                                // magnitude bin width
                                dMag[imag] =
                                        Double.valueOf(st.nextToken())
                                                .doubleValue();

                                // magnitude model weight
                                magWeight[imag] = 1.0;

                            } else if (st.countTokens() == 4) {
                                // with this option the a value is not given in
                                // this line
                                // but a values are given with the fault trace
                                // coordinates

                                // incremental a value
                                aVal[imag] = Double.NaN;

                                // b value
                                bVal[imag] =
                                        Double.valueOf(st.nextToken())
                                                .doubleValue();

                                // minimum magnitude
                                minMag[imag] =
                                        Double.valueOf(st.nextToken())
                                                .doubleValue();

                                // maximum magnitude
                                maxMag[imag] =
                                        Double.valueOf(st.nextToken())
                                                .doubleValue();

                                // magnitude bin width
                                dMag[imag] =
                                        Double.valueOf(st.nextToken())
                                                .doubleValue();

                                // magnitude model weight
                                magWeight[imag] = 1.0;

                            }

                            // line 1269
                            // c---- But first, check that dmag(ift,imag) is
                            // valid. If not valid, fix it.
                            // if(dmag(ift,imag).le.0.004)then
                            // write(6,*)dmag(ift,imag),' invalid dmag for
                            // ',adum
                            // write(6,*)"Code reset this fault's dmag to 0.1"
                            // dmag(ift,imag)=0.1
                            // endif
                            // I reproduce the above check
                            if (dMag[imag] <= 0.004)
                                dMag[imag] = 0.1;

                            // if the minimum magnitude and the maximum
                            // magnitude are different
                            // I move this values to bin center
                            // the corresponding code in hazFXnga7c.f is the
                            // following (line 1276)
                            // if(magmin(ift,imag).ne.magmax(ift,imag)) then
                            // magmin(ift,imag)=
                            // magmin(ift,imag)+dmag(ift,imag)/2.
                            // magmax(ift,imag)=
                            // magmax(ift,imag)-dmag(ift,imag)/2.+.0001
                            if (minMag[imag] != maxMag[imag]) {
                                minMag[imag] = minMag[imag] + dMag[imag] / 2.0;
                                maxMag[imag] =
                                        maxMag[imag] - dMag[imag] / 2.0
                                                + 0.0001;
                            }

                            // now I calculate the number of magnitude values in
                            // the mfd line 1294
                            // nmag0(ift,imag)=
                            // int((magmax(ift,imag)-magmin(ift,imag))/dmag(ift,imag)
                            // + 1.4)
                            nmag[imag] =
                                    (int) ((maxMag[imag] - minMag[imag])
                                            / dMag[imag] + 1.4);

                            // line 1296
                            // itest(ift)=0
                            // test= magmax(ift,imag)+dmbranch(1)
                            // if((test.lt.6.5).and.(nmag0(ift,imag).gt.1)) then
                            // itest(ift)=1
                            // now I reproduce the above test
                            double test = maxMag[imag] + dmM[0];
                            if (test < 6.5 && nmag[imag] > 1)
                                itest = 1;

                            // line 1305
                            // if(nmag0(ift,imag).eq.1) then
                            // test= magmax(ift,imag)+dmbranch(1)-mwid*dma
                            // if(test.lt.6.5) then
                            // itest(ift)=1
                            // write(6,*) "test.lt.6.5 for fault #", ift, '
                            // itest ',itest(ift)
                            // endif
                            // endif
                            // now I reproduce the above test
                            if (nmag[imag] == 1) {
                                double dma = 0.4 * stdMchar; // line 1105
                                test = maxMag[imag] + dmM[0] - widthMchar * dma;
                                if (test < 6.5)
                                    itest = 1;
                            }

                        } // end loop over mag-area relationships

                    }

                    if (FType == -2) { // GR fault with extra branching on b
                                       // value

                        // redefine number of branches
                        NMagBranches = 2 * NMagBranches;

                        // array of a values
                        aVal = new double[NMagBranches];
                        // array of b values
                        bVal = new double[NMagBranches];
                        // array of minimum magnitudes
                        minMag = new double[NMagBranches];
                        // array of maximum magnitudes
                        maxMag = new double[NMagBranches];
                        // array of bin widths
                        dMag = new double[NMagBranches];
                        // array of relative weights
                        magWeight = new double[NMagBranches];
                        // array list of number of magnitude values
                        nmag = new int[NMagBranches];

                        // loop over mag-area relationships
                        for (int imag = 0; imag < NMagBranches / 2; imag++) {

                            sRecord = oReader.readLine();
                            st = new StringTokenizer(sRecord);

                            // incremental a value
                            aVal[imag] =
                                    Double.valueOf(st.nextToken())
                                            .doubleValue();

                            // b value
                            bVal[imag] =
                                    Double.valueOf(st.nextToken())
                                            .doubleValue();

                            // minimum magnitude
                            minMag[imag] =
                                    Double.valueOf(st.nextToken())
                                            .doubleValue();

                            // maximum magnitude
                            maxMag[imag] =
                                    Double.valueOf(st.nextToken())
                                            .doubleValue();

                            // magnitude bin width
                            dMag[imag] =
                                    Double.valueOf(st.nextToken())
                                            .doubleValue();

                            // magnitude model weight
                            // and reduce by a 0.5 factor
                            magWeight[imag] =
                                    Double.valueOf(st.nextToken())
                                            .doubleValue() * 0.5;

                            // line 1269
                            // c---- But first, check that dmag(ift,imag) is
                            // valid. If not valid, fix it.
                            // if(dmag(ift,imag).le.0.004)then
                            // write(6,*)dmag(ift,imag),' invalid dmag for
                            // ',adum
                            // write(6,*)"Code reset this fault's dmag to 0.1"
                            // dmag(ift,imag)=0.1
                            // endif
                            // I reproduce the above check
                            if (dMag[imag] <= 0.004)
                                dMag[imag] = 0.1;

                            // if the minimum magnitude and the maximum
                            // magnitude are different
                            // I move this values to bin center
                            // the corresponding code in hazFXnga7c.f is the
                            // following (line 1276)
                            // if(magmin(ift,imag).ne.magmax(ift,imag)) then
                            // magmin(ift,imag)=
                            // magmin(ift,imag)+dmag(ift,imag)/2.
                            // magmax(ift,imag)=
                            // magmax(ift,imag)-dmag(ift,imag)/2.+.0001
                            if (minMag[imag] != maxMag[imag]) {
                                minMag[imag] = minMag[imag] + dMag[imag] / 2.0;
                                maxMag[imag] =
                                        maxMag[imag] - dMag[imag] / 2.0
                                                + 0.0001;
                            }

                            // now I calculate the number of magnitude values in
                            // the mfd line 1294
                            // nmag0(ift,imag)=
                            // int((magmax(ift,imag)-magmin(ift,imag))/dmag(ift,imag)
                            // + 1.4)
                            nmag[imag] =
                                    (int) ((maxMag[imag] - minMag[imag])
                                            / dMag[imag] + 1.4);

                            // line 1296
                            // itest(ift)=0
                            // test= magmax(ift,imag)+dmbranch(1)
                            // if((test.lt.6.5).and.(nmag0(ift,imag).gt.1)) then
                            // itest(ift)=1
                            // now I reproduce the above test
                            double test = maxMag[imag] + dmM[0];
                            if (test < 6.5 && nmag[imag] > 1)
                                itest = 1;

                            // line 1305
                            // if(nmag0(ift,imag).eq.1) then
                            // test= magmax(ift,imag)+dmbranch(1)-mwid*dma
                            // if(test.lt.6.5) then
                            // itest(ift)=1
                            // write(6,*) "test.lt.6.5 for fault #", ift, '
                            // itest ',itest(ift)
                            // endif
                            // endif
                            // now I reproduce the above test
                            if (nmag[imag] == 1) {
                                double dma = 0.4 * stdMchar; // line 1105
                                test =
                                        maxMag[imag] + dmM[0] - widthMchar
                                                * stdMchar;
                                if (test < 6.5)
                                    itest = 1;
                            }

                        } // end loop over mag-area relationships

                        // loop over remaining mag-area relationships
                        // the b value is set to 0 and the a value is
                        // recomputed in order to conserve the total moment rate
                        for (int imag = NMagBranches / 2; imag < NMagBranches; imag++) {

                            // compute total seismic moment rate of the original
                            // model
                            double tmr =
                                    totMoRate(minMag[imag - NMagBranches / 2],
                                            nmag[imag - NMagBranches / 2],
                                            dMag[imag - NMagBranches / 2],
                                            aVal[imag - NMagBranches / 2],
                                            bVal[imag - NMagBranches / 2]);

                            // compute total seismic moment (by putting aVal = 0
                            // and bVal = 0)
                            double tsm =
                                    totMoRate(minMag[imag - NMagBranches / 2],
                                            nmag[imag - NMagBranches / 2],
                                            dMag[imag - NMagBranches / 2], 0.0,
                                            0.0);

                            // recompute new a value so that the total moment
                            // rate is conserved
                            double a = Math.log10(tmr / tsm);

                            // incremental a value
                            aVal[imag] = a;

                            // b value
                            bVal[imag] = 0.0;

                            // minimum magnitude
                            minMag[imag] = minMag[imag - NMagBranches / 2];

                            // maximum magnitude
                            maxMag[imag] = maxMag[imag - NMagBranches / 2];

                            // magnitude bin width
                            dMag[imag] = dMag[imag - NMagBranches / 2];

                            // magnitude model weight
                            magWeight[imag] =
                                    magWeight[imag - NMagBranches / 2];

                            nmag[imag] = nmag[imag - NMagBranches / 2];

                        }

                        // change fault type to -2 to 2 because then is treated
                        // as normal GR
                        FType = 2;

                    }

                    // if(sdal.eq.0. .and. itype(ift).eq.2 .and. nbranch.eq.1)
                    // itest(ift)=1 !line added feb28 2008
                    // now I reproduce the above test
                    if (stdMchar == 0 && dmM.length == 1) {
                        itest = 1;
                    }

                    // Case 1
                    // line 1868
                    // c---- GR with nmag0>1 with Mmax uncertainties
                    // if((itype(ift).eq.2).and.(nmag0(ift,1).gt.1).and.
                    // & (itest(ift).eq.0)) then
                    // in applying epistemic uncertainty keep the same total
                    // moment rate

                    if (FType == 2 && nmag[0] > 1 && itest == 0
                            && !Double.isNaN(aVal[0])) {

                        if (printMFD) {
                            oWriter.write("Fault: " + (sourceIndex + 1) + "\n");
                            oWriter.write("Case: 1\n");
                        }

                        // System.out.println("Case 1: FType==2 && nmag[0]>1 && itest==0");
                        // System.out.println("Fault name: "+FName);

                        // loop over magnitude models
                        for (int imag = 0; imag < NMagBranches; imag++) {

                            if (printMFD) {
                                oWriter.write("Magnitude model: " + (imag + 1)
                                        + "\n");
                            }

                            // System.out.println("Magnitude branch: "+(imag+1));

                            // compute total moment rate
                            double tmr =
                                    totMoRate(minMag[imag], nmag[imag],
                                            dMag[imag], aVal[imag], bVal[imag]);

                            // loop over epistemic uncertainties
                            for (int iepi = 0; iepi < nEpiUnc; iepi++) {

                                if (printMFD) {
                                    oWriter.write("Epistemic branch: "
                                            + (iepi + 1) + "\n");
                                }

                                // System.out.println("Epistemic branch: "+(iepi+1));

                                // update mmax
                                double mmax = maxMag[imag] + dmM[iepi];

                                // compute number of magnitude values
                                // nmag= (mmax- magmin(ift,imag))/dmag(ift,imag)
                                // + 1.4 line 1884
                                int nmagv =
                                        (int) ((mmax - minMag[imag])
                                                / dMag[imag] + 1.4);

                                // it can happen that by applying epistemic
                                // uncertainties on the maximum magnitude
                                // (alredy corrected by half bin width) the
                                // resulting value is still larger than 6.5
                                // and therefore the fault gets itest = 0.
                                // However this value can be still smaller than
                                // the minimum magnitude once this is corrected
                                // for the half bin width.
                                // Example: Buffalo Creek fault zone in nv.gr
                                // minMag = 6.5
                                // maxMag = 6.77
                                // dMag = 0.1350
                                // minMag+dMag/2 = 6.5675
                                // maxMag-dMag/2 = 6.7025
                                // maxMag-dMag/2-0.2 = 6.5025 > 6.5 -> itest = 0
                                // (note the test on the epistemic uncertainties
                                // is done
                                // with respect to the value 6.5 which is not
                                // corrected for half bin width!)
                                // however maxMag-dMag/2-0.2 = 6.5025 <
                                // minMag+dMag/2 = 6.5675. Therefore the number
                                // of magnitude
                                // values results to be 0, that us nmagv = 0.
                                // This creates a problem in the construction of
                                // the MFD. I saw that when this happens
                                // hazFXnga7c.f ignore the problem by simply not
                                // constructing the corresponding MFD, but still
                                // keeping the MFDs coming from the remaining
                                // epistemic uncertainties branches. That's why
                                // I put
                                // an if statement below.
                                // define mfd
                                if (nmagv != 0) {
                                    GutenbergRichterMagFreqDist mfd =
                                            new GutenbergRichterMagFreqDist(
                                                    minMag[imag], nmagv,
                                                    dMag[imag]);
                                    // set total moment rate
                                    mfd.setAllButTotCumRate(minMag[imag],
                                            minMag[imag] + (nmagv - 1)
                                                    * dMag[imag], fileWeight
                                                    * dmW[iepi]
                                                    * magWeight[imag] * tmr,
                                            bVal[imag]);
                                    if (printMFD) {
                                        for (int ii = 0; ii < mfd.getNum(); ii++) {
                                            oWriter.write(mfd.getX(ii) + " "
                                                    + mfd.getIncrRate(ii)
                                                    / fileWeight + "\n");
                                            // System.out.println(mfd.getX(ii)+" "+mfd.getIncrRate(ii)/fileWeight);
                                        }
                                    }
                                    // add to array list
                                    mfds.add(mfd);
                                }

                            }

                        }

                    }

                    // Case 2
                    // line 2135
                    // ccc---- GR with nmag0=1, one magnitude floated, with
                    // uncertainties,
                    // c used for some faults outside of CA and in 2002 Maacama
                    // northern CA
                    // ccc--- for very long faults when Mmmax set to 7.5. In
                    // 2007 Maacama char has itype 1
                    // if((itype(ift).eq.2).and.(nmag0(ift,1).eq.1).and.
                    // & (itest(ift).eq.0)) then
                    if (FType == 2 && nmag[0] == 1 && itest == 0
                            && !Double.isNaN(aVal[0])) {

                        if (printMFD) {
                            oWriter.write("Fault: " + (sourceIndex + 1) + "\n");
                            oWriter.write("Case: 2 \n");
                        }

                        // System.out.println("Case 2: FType==2 && nmag[0]==1 && itest==0");
                        // System.out.println("Fault name: "+FName);

                        // loop over magnitude models
                        for (int imag = 0; imag < NMagBranches; imag++) {

                            if (printMFD) {
                                oWriter.write("Magnitude model: " + (imag + 1)
                                        + "\n");
                            }

                            // System.out.println("Magnitude model: "+(imag+1));

                            // compute total moment rate
                            double tmr =
                                    Math.pow(10.0, aVal[imag] - bVal[imag]
                                            * minMag[imag] + 1.5 * minMag[imag]
                                            + 9.05);

                            // compute total cumulative rate
                            double tcr =
                                    Math.pow(10.0, aVal[imag] - bVal[imag]
                                            * minMag[imag]);

                            // loop over epistemic uncertainties
                            for (int iepi = 0; iepi < nEpiUnc; iepi++) {

                                if (printMFD) {
                                    oWriter.write("Epistemic branch: "
                                            + (iepi + 1) + "\n");
                                }

                                // System.out.println("Epistemic branch: "+(iepi+1));

                                // update magnitude value
                                double mag = maxMag[imag] + dmM[iepi];

                                // define charcateristic model
                                double charMinMag =
                                        mag - widthMchar * 2 * stdMchar / 5;
                                double charMaxMag =
                                        mag + widthMchar * 2 * stdMchar / 5;
                                double charDeltaMag = 2 * stdMchar / 5;
                                int numMag =
                                        (int) Math
                                                .round((charMaxMag - charMinMag)
                                                        / charDeltaMag) + 1;
                                double truncLevel =
                                        (charMaxMag - mag) / stdMchar;

                                // gaussian magnitude frequency distribution
                                GaussianMagFreqDist mfdChar =
                                        new GaussianMagFreqDist(charMinMag,
                                                charMaxMag, numMag);

                                if (stdMchar > 0) {
                                    // set gaussian mfd by balancing moment
                                    // rate, that is I take the original total
                                    // moment rate
                                    mfdChar.setAllButCumRate(mag, stdMchar,
                                            fileWeight * dmW[iepi]
                                                    * magWeight[imag] * tmr,
                                            truncLevel, truncType);
                                    // System.out.println("mean magnitude, total rate: "+mfdChar.getMean()+", "+mfdChar.getTotalIncrRate());
                                    if (printMFD) {
                                        for (int ii = 0; ii < mfdChar.getNum(); ii++) {
                                            oWriter.write(mfdChar.getX(ii)
                                                    + " "
                                                    + mfdChar.getIncrRate(ii)
                                                    / fileWeight + "\n");
                                            // System.out.println(mfdChar.getX(ii)+" "+mfdChar.getIncrRate(ii)/fileWeight);
                                        }
                                    }
                                } else if (stdMchar < 0) {
                                    // set gaussian mfd by balancing rate, that
                                    // is I take the original rate
                                    mfdChar.setAllButTotMoRate(mag, stdMchar,
                                            fileWeight * dmW[iepi]
                                                    * magWeight[imag] * tcr,
                                            truncLevel, truncType);
                                    // System.out.println("mean magnitude, total rate: "+mfdChar.getMean()+", "+mfdChar.getTotalIncrRate());
                                    if (printMFD) {
                                        for (int ii = 0; ii < mfdChar.getNum(); ii++) {
                                            oWriter.write(mfdChar.getX(ii)
                                                    + " "
                                                    + mfdChar.getIncrRate(ii)
                                                    / fileWeight + "\n");
                                            // System.out.println(mfdChar.getX(ii)+" "+mfdChar.getIncrRate(ii)/fileWeight);
                                        }
                                    }
                                }
                                mfds.add(mfdChar);

                            }

                        }

                    }

                    // Case 3
                    // line 2322
                    // c---------------------
                    // c------ all GR without uncertainties, with possible
                    // downdip ruptures, z=dtor1
                    // if((itype(ift).eq.2).and.(itest(ift).eq.1)) then
                    if (FType == 2 && itest == 1 && !Double.isNaN(aVal[0])) {

                        if (printMFD) {
                            oWriter.write("Fault: " + (sourceIndex + 1) + "\n");
                            oWriter.write("Case: 3 \n");
                        }

                        // System.out.println("Case 3: FType==2 && itest==1");
                        // System.out.println("Fault name: "+FName);

                        // loop over magnitude models
                        for (int imag = 0; imag < NMagBranches; imag++) {

                            if (printMFD) {
                                oWriter.write("Magnitude model: " + (imag + 1)
                                        + "\n");
                            }

                            // System.out.println("Magnitude branch: "+(imag+1));

                            // compute total moment rate
                            double tmr =
                                    totMoRate(minMag[imag], nmag[imag],
                                            dMag[imag], aVal[imag], bVal[imag]);

                            // define mfd
                            GutenbergRichterMagFreqDist mfd =
                                    new GutenbergRichterMagFreqDist(
                                            minMag[imag], nmag[imag],
                                            dMag[imag]);
                            // set total moment rate
                            mfd.setAllButTotCumRate(minMag[imag], minMag[imag]
                                    + (nmag[imag] - 1) * dMag[imag], fileWeight
                                    * magWeight[imag] * tmr, bVal[imag]);
                            if (printMFD) {
                                for (int ii = 0; ii < mfd.getNum(); ii++) {
                                    oWriter.write(mfd.getX(ii) + " "
                                            + mfd.getIncrRate(ii) / fileWeight
                                            + "\n");
                                    // System.out.println(mfd.getX(ii)+" "+mfd.getIncrRate(ii)/fileWeight);
                                }
                            }

                            mfds.add(mfd);

                        }
                    }

                }

                if (FType == 1) { // Characteristic fault

                    // for characteristic faults no floating
                    floatRuptureFlag = false;

                    // array of characteristic magnitudes
                    CharM = new double[NMagBranches];
                    // array of characteristic rates
                    CharRate = new double[NMagBranches];
                    // array of relative weights
                    magWeight = new double[NMagBranches];

                    // loop over mag-area relationships
                    for (int imag = 0; imag < NMagBranches; imag++) {

                        sRecord = oReader.readLine();
                        st = new StringTokenizer(sRecord);

                        // characteristic magnitude
                        CharM[imag] =
                                Double.valueOf(st.nextToken()).doubleValue();

                        // characteristic rate
                        CharRate[imag] =
                                Double.valueOf(st.nextToken()).doubleValue();

                        // magnitude model weight
                        magWeight[imag] = 1.0;

                    }

                    // line 1384
                    // if(sdal.eq.0. .and. itype(ift).eq.1) itest(ift)=1
                    // now I reproduce the above test
                    if (stdMchar == 0) {
                        itest = 1;
                    }

                    // Case 4
                    // line 2595
                    // c---------------------------
                    // c--- for characteristic event, modified to include
                    // multiple mags per fault
                    // c---- characteristic with uncertainties
                    // c To some extent diff M(RA) uncertainties take care of
                    // mag. variation. We seem to
                    // c be repeating some mag uncertainty here.
                    // c characteristic events fill the fault by definition. no
                    // variation in top of rup.
                    // c discuss with colleagues? nov 15 2006
                    // if((itype(ift).eq.1).and.(itest(ift).eq.0)) then
                    if (FType == 1 && itest == 0) {

                        if (printMFD) {
                            oWriter.write("Fault: " + (sourceIndex + 1) + "\n");
                            oWriter.write("Case: 4 \n");
                        }

                        // System.out.println("Case 4: FType==1 && itest==0");
                        // System.out.println("Fault name: "+FName);

                        // loop over mag-area relationships
                        for (int imag = 0; imag < NMagBranches; imag++) {

                            if (printMFD) {
                                oWriter.write("Magnitude model: " + (imag + 1)
                                        + "\n");
                            }

                            // System.out.println("Magnitude model: "+(imag+1));

                            // compute total moment rate
                            double tmr =
                                    CharRate[imag]
                                            * Math.pow(10.0,
                                                    1.5 * CharM[imag] + 9.05);

                            // total cumulative rate
                            double tcr = CharRate[imag];

                            // loop over epistemic uncertainties
                            for (int iepi = 0; iepi < nEpiUnc; iepi++) {

                                if (printMFD) {
                                    oWriter.write("Epistemic branch: "
                                            + (iepi + 1) + "\n");
                                }
                                // System.out.println("Epistemic branch: "+(iepi+1));

                                // update magnitude value
                                double mag = CharM[imag] + dmM[iepi];

                                // define characteristic model
                                double charMinMag =
                                        mag - widthMchar * 2
                                                * Math.abs(stdMchar) / 5;
                                double charMaxMag =
                                        mag + widthMchar * 2
                                                * Math.abs(stdMchar) / 5;
                                double charDeltaMag =
                                        2 * Math.abs(stdMchar) / 5;
                                int numMag =
                                        (int) Math
                                                .round((charMaxMag - charMinMag)
                                                        / charDeltaMag) + 1;
                                double truncLevel =
                                        (charMaxMag - mag) / Math.abs(stdMchar);
                                // gaussian magnitude frequency distribution
                                GaussianMagFreqDist mfdChar =
                                        new GaussianMagFreqDist(charMinMag,
                                                charMaxMag, numMag);

                                if (stdMchar > 0) {
                                    // set gaussian mfd by balancing moment rate
                                    mfdChar.setAllButCumRate(mag, stdMchar,
                                            fileWeight * dmW[iepi]
                                                    * magWeight[imag] * tmr,
                                            truncLevel, truncType);
                                    if (printMFD) {
                                        for (int ii = 0; ii < mfdChar.getNum(); ii++) {
                                            oWriter.write(mfdChar.getX(ii)
                                                    + " "
                                                    + mfdChar.getIncrRate(ii)
                                                    / fileWeight + "\n");
                                            // System.out.println(mfdChar.getX(ii)+" "+mfdChar.getIncrRate(ii)/fileWeight);
                                        }
                                    }
                                } else if (stdMchar < 0) {
                                    // set gaussian mfd by balancing rate
                                    mfdChar.setAllButTotMoRate(mag,
                                            Math.abs(stdMchar), fileWeight
                                                    * dmW[iepi]
                                                    * magWeight[imag] * tcr,
                                            truncLevel, truncType);
                                    if (printMFD) {
                                        for (int ii = 0; ii < mfdChar.getNum(); ii++) {
                                            oWriter.write(mfdChar.getX(ii)
                                                    + " "
                                                    + mfdChar.getIncrRate(ii)
                                                    / fileWeight + "\n");
                                            // System.out.println(mfdChar.getX(ii)+" "+mfdChar.getIncrRate(ii)/fileWeight);
                                        }
                                    }
                                }
                                mfds.add(mfdChar);
                            }

                        }

                    }

                    // Case 5
                    // cc-- characteristic without uncertainties
                    // if((itype(ift).eq.1).and.(itest(ift).eq.1)) then 
                    if (FType == 1 && itest == 1) {

                        if (printMFD) {
                            oWriter.write("Fault: " + (sourceIndex + 1) + "\n");
                            oWriter.write("Case: 5 \n");
                        }

                        // System.out.println("Case 5: FType==1 && itest==1");
                        // System.out.println("Fault name: "+FName);

                        // loop over mag-area relationships
                        for (int imag = 0; imag < NMagBranches; imag++) {

                            if (printMFD) {
                                oWriter.write("Magnitude model: " + (imag + 1)
                                        + "\n");
                            }

                            // System.out.println("Magnitude model: "+(imag+1));

                            IncrementalMagFreqDist mfd =
                                    new IncrementalMagFreqDist(CharM[imag],
                                            CharM[imag], 1);

                            mfd.set(CharM[imag], fileWeight * magWeight[imag]
                                    * CharRate[imag]);

                            if (printMFD) {
                                oWriter.write(mfd.getX(0) + " "
                                        + mfd.getIncrRate(0) / fileWeight
                                        + "\n");
                            }

                            mfds.add(mfd);

                        }

                    }
                }

                // System.out.println(FName);

                // NOW SUM UP ALL THE MFDs FOR THIS SOURCE
                SummedMagFreqDist finalMFD = null;
                if (mfds.size() > 0) {
                    finalMFD = sumMagFreqDist(mfds);
                }

                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);

                // dip
                double dip = Double.valueOf(st.nextToken()).doubleValue();

                // width
                double width = Double.valueOf(st.nextToken()).doubleValue();

                // depth0 (depth to top of rupture)
                double depth0 = Double.valueOf(st.nextToken()).doubleValue();

                sRecord = oReader.readLine();
                st = new StringTokenizer(sRecord);

                // number of segment points
                int NSegPoints = Integer.valueOf(st.nextToken()).intValue();

                // loop over segment points
                FaultTrace faultT = new FaultTrace(FName);
                // mean a value
                double meanAValue = 0;
                for (int isp = 0; isp < NSegPoints; isp++) {
                    sRecord = oReader.readLine();
                    st = new StringTokenizer(sRecord);

                    double lat = Double.NaN;
                    double lon = Double.NaN;

                    if (FType == 2 && Double.isNaN(aVal[0])) {
                        // coordinates of segment points and a value
                        lat = Double.valueOf(st.nextToken()).doubleValue();
                        lon = Double.valueOf(st.nextToken()).doubleValue();
                        meanAValue =
                                meanAValue
                                        + Double.valueOf(st.nextToken())
                                                .doubleValue();
                    } else {
                        lat = Double.valueOf(st.nextToken()).doubleValue();
                        lon = Double.valueOf(st.nextToken()).doubleValue();
                    }

                    // from Ned mail 23/02/2010
                    // So, when you create the locations for the faultTrace, you
                    // need to set the depths as the upper seismogenic depth.
                    faultT.add(new Location(lat, lon, depth0));
                }

                meanAValue = meanAValue / faultT.getNumLocations();

                if (FType == 2 && Double.isNaN(aVal[0])) {

                    // loop over magnitude models
                    for (int imag = 0; imag < NMagBranches; imag++) {

                        if (printMFD) {
                            oWriter.write("Magnitude model: " + (imag + 1)
                                    + "\n");
                        }

                        // System.out.println("Magnitude branch: "+(imag+1));

                        // compute total moment rate
                        double tmr =
                                totMoRate(minMag[imag], nmag[imag], dMag[imag],
                                        meanAValue, bVal[imag]);

                        // loop over epistemic uncertainties
                        for (int iepi = 0; iepi < nEpiUnc; iepi++) {

                            if (printMFD) {
                                oWriter.write("Epistemic branch: " + (iepi + 1)
                                        + "\n");
                            }

                            // System.out.println("Epistemic branch: "+(iepi+1));

                            // update mmax
                            double mmax = maxMag[imag] + dmM[iepi];

                            // compute number of magnitude values
                            // nmag= (mmax- magmin(ift,imag))/dmag(ift,imag) +
                            // 1.4 line 1884
                            int nmagv =
                                    (int) ((mmax - minMag[imag]) / dMag[imag] + 1.4);

                            // it can happen that by applying epistemic
                            // uncertainties on the maximum magnitude
                            // (alredy corrected by half bin width) the
                            // resulting value is still larger than 6.5
                            // and therefore the fault gets itest = 0. However
                            // this value can be still smaller than
                            // the minimum magnitude once this is corrected for
                            // the half bin width.
                            // Example: Buffalo Creek fault zone in nv.gr
                            // minMag = 6.5
                            // maxMag = 6.77
                            // dMag = 0.1350
                            // minMag+dMag/2 = 6.5675
                            // maxMag-dMag/2 = 6.7025
                            // maxMag-dMag/2-0.2 = 6.5025 > 6.5 -> itest = 0
                            // (note the test on the epistemic uncertainties is
                            // done
                            // with respect to the value 6.5 which is not
                            // corrected for half bin width!)
                            // however maxMag-dMag/2-0.2 = 6.5025 <
                            // minMag+dMag/2 = 6.5675. Therefore the number of
                            // magnitude
                            // values results to be 0, that us nmagv = 0.
                            // This creates a problem in the construction of the
                            // MFD. I saw that when this happens
                            // hazFXnga7c.f ignore the problem by simply not
                            // constructing the corresponding MFD, but still
                            // keeping the MFDs coming from the remaining
                            // epistemic uncertainties branches. That's why I
                            // put
                            // an if statement below.
                            // define mfd
                            if (nmagv != 0) {
                                GutenbergRichterMagFreqDist mfd =
                                        new GutenbergRichterMagFreqDist(
                                                minMag[imag], nmagv, dMag[imag]);
                                // set total moment rate
                                mfd.setAllButTotCumRate(
                                        minMag[imag],
                                        minMag[imag] + (nmagv - 1) * dMag[imag],
                                        fileWeight * dmW[iepi]
                                                * magWeight[imag] * tmr,
                                        bVal[imag]);
                                if (printMFD) {
                                    for (int ii = 0; ii < mfd.getNum(); ii++) {
                                        oWriter.write(mfd.getX(ii) + " "
                                                + mfd.getIncrRate(ii)
                                                / fileWeight + "\n");
                                        // System.out.println(mfd.getX(ii)+" "+mfd.getIncrRate(ii)/fileWeight);
                                    }
                                }
                                // add to array list
                                mfds.add(mfd);
                            }

                        }

                    }

                    // sum the mfds
                    finalMFD = sumMagFreqDist(mfds);

                }

                // if dip is negative take the absolute value of dip
                // and reverse trace. Is this correct?
                if (dip < 0) {
                    dip = Math.abs(dip);
                    faultT.reverse();
                }

                boolean includeSrc = false;
                // loop over fault trace coordinates
                // if one is inside the region of interest take it
                for (int isp = 0; isp < NSegPoints; isp++) {
                    double faultTraceLat = faultT.get(isp).getLatitude();
                    double faultTraceLon = faultT.get(isp).getLongitude();
                    if (faultTraceLat >= latmin - borderThickness
                            && faultTraceLat <= latmax + borderThickness
                            && faultTraceLon >= lonmin - borderThickness
                            && faultTraceLon <= lonmax + borderThickness) {
                        includeSrc = true;
                        break;
                    }
                }

                if (includeSrc) {

                    // NOW CREATE AND SAVE THE SOURCE DATA OBJECT
                    // update source index
                    sourceIndex = sourceIndex + 1;
                    // compute lower seismogenic depth
                    double seismDepthLow =
                            depth0 + width * Math.sin(dip * Math.PI / 180.0);

                    System.out.println(FName);
                    System.out.println(finalMFD.getCumRate(0));
                    System.out.println(faultT);

                    // create GEMFaultSourceData abject
                    GEMFaultSourceData fsd =
                            new GEMFaultSourceData(
                                    Integer.toString(sourceIndex), FName, trt,
                                    finalMFD, faultT, dip, rake, seismDepthLow,
                                    depth0, floatRuptureFlag);

                    // insert source data into container
                    srcDataList.add(fsd);

                }

            } // end loop over fault sources

            if (printMFD) {
                oWriter.close();
                oOutBIS.close();
                oOutFIS.close();
            }

        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    /**
     * compute total moment rate as done by NSHMP code
     * 
     * @param minMag
     *            : minimum magnitude (rounded to multiple of deltaMag and moved
     *            to bin center)
     * @param numMag
     *            : number of magnitudes
     * @param deltaMag
     *            : magnitude bin width
     * @param aVal
     *            : incremental a value (defined with respect to deltaMag)
     * @param bVal
     *            : b value
     * @return
     */

    private double totMoRate(double minMag, int numMag, double deltaMag,
            double aVal, double bVal) {
        double moRate = 0;
        double mag;
        for (int imag = 0; imag < numMag; imag++) {
            mag = minMag + imag * deltaMag;
            moRate += Math.pow(10, aVal - bVal * mag + 1.5 * mag + 9.05);
        }
        return moRate;
    }

    private boolean checkIfNumber(String in) {

        try {

            Integer.parseInt(in);

        } catch (NumberFormatException ex) {
            return false;
        }

        return true;
    }

    private SummedMagFreqDist sumMagFreqDist(
            ArrayList<IncrementalMagFreqDist> mfds) {

        // find lowest and highest mag from mfds
        // find also the lowest dmag
        double lowestMag = Double.MAX_VALUE;
        double highestMag = 0;
        double lowestDeltaM = Double.MAX_VALUE;
        for (int i = 0; i < mfds.size(); i++) {
            IncrementalMagFreqDist mfd = mfds.get(i);
            if (mfd.getMaxX() > highestMag)
                highestMag = mfd.getMaxX();
            if (mfd.getMinX() < lowestMag)
                lowestMag = mfd.getMinX();
            if (mfd.getDelta() < lowestDeltaM)
                lowestDeltaM = mfd.getDelta();
        }

        // calculate number of magnitude values
        int num = 0;
        if (lowestDeltaM != 0) {
            num = (int) Math.round((highestMag - lowestMag) / lowestDeltaM) + 1;
        } else {
            lowestDeltaM = dm;
            num = (int) Math.round((highestMag - lowestMag) / lowestDeltaM) + 1;
        }

        SummedMagFreqDist finalMFD =
                new SummedMagFreqDist(lowestMag, num, lowestDeltaM);

        for (int i = 0; i < mfds.size(); i++) {
            // add mfds conserving total moment rate
            finalMFD.addResampledMagFreqDist(mfds.get(i), false);
        }

        // make this check
        if (finalMFD.getCumRate(0) == 0) {
            System.out
                    .println("Summation of magnitude frequency distribution gives total cumulative rate = 0!");
            System.exit(0);
        }

        return finalMFD;
    }

    public static void main(String[] args) throws IOException {

        String inDir = "../../data/nshmp/alaska/fault/";
        String inFile = "AKF2.out_revF.in";

        NshmpAlaskaFault2GemSourceData model =
                new NshmpAlaskaFault2GemSourceData(inDir + inFile,
                        TectonicRegionType.ACTIVE_SHALLOW, 1.0,
                        -Double.MAX_VALUE, Double.MAX_VALUE, -Double.MAX_VALUE,
                        Double.MAX_VALUE);

        model.writeFaultSources2KMLfile(new FileWriter(
                "/Users/damianomonelli/Desktop/AlaskaFaultSources.kml"));

    }

}
