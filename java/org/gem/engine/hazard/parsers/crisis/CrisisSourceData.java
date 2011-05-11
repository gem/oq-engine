package org.gem.engine.hazard.parsers.crisis;

import java.io.BufferedReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.commons.calc.GaussianDistCalc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

/**
 * <b>Title:</b> InputFileParser
 * <p>
 * 
 * <b>Description:</b> This class extends the GemInput Parser class. It parses a
 * Crisis input file and creates a list of GemSourceData objects.
 * <p>
 * Note that Crisis can associate distinct GMPE to distinct seismic sources of
 * the same input.
 * 
 * @author M.M. Pagani
 * @created 2010-03-01
 * @version 1.0
 */

public class CrisisSourceData extends GemFileParser {

    private static boolean INFO = false;
    private static double MMIN = 5.0;
    private static double MWDT = 0.1;
    private static boolean USEDIPPINGAREAS = true;
    private static boolean USEAREASOURCES = true;

    /**
     * 
     * @param file
     */
    public CrisisSourceData(BufferedReader input) {
        ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();

        int subSrcCounter = 0;

        // Reading the file
        try {
            // Instantiate a BufferedReader
            // BufferedReader input = new BufferedReader(file);
            try {

                // ---------------------------------------------------------------------------------
                // Reading the header
                InputFileHeader head = new InputFileHeader(input);

                // Reading sources
                for (int i = 0; i < head.nRegions; i++) {

                    InputFileSource tmpsrc = new InputFileSource(input);
                    if (INFO) {
                        System.out
                                .println("=====================================================");
                        System.out.printf("Reading source # %d \n", i);
                        System.out.printf("  name: %s \n", tmpsrc.getName());
                    }

                    // Crisis "Poisson" model
                    String name = tmpsrc.getName();
                    LocationList locList = new LocationList();

                    // Hash map with depths
                    HashMap<Double, Integer> depthMap =
                            new HashMap<Double, Integer>();

                    for (int j = 0; j < tmpsrc.getCoords().length; j++) {

                        // Add the location to the list
                        locList.add(new Location(tmpsrc.getCoords()[j][1],
                                tmpsrc.getCoords()[j][0]));

                        // This is a hash map used to identify the number and
                        // values of depths
                        // used to specify the source
                        if (depthMap.containsKey(tmpsrc.getDepth())) {
                            depthMap.put(tmpsrc.getDepth()[j],
                                    depthMap.get(tmpsrc.getDepth()) + 1);
                        } else {
                            depthMap.put(tmpsrc.getDepth()[j], 1);
                        }
                    }

                    // Check how many depths were used
                    if (INFO) {
                        System.out.println("  Number of depths: "
                                + depthMap.keySet().size());
                        Iterator<Double> iterator =
                                depthMap.keySet().iterator();
                        while (iterator.hasNext()) {
                            System.out.println("  Depth: " + iterator.next());
                        }
                    }

                    // -----------------------------------------------------------------------------
                    // Creating the mfd distribution
                    IncrementalMagFreqDist mfd = null;
                    if (tmpsrc.getOccMod() == 1) {

                        if (INFO)
                            System.out.printf("  mmax: %.2f \n",
                                    tmpsrc.getMuUn());
                        double tmpMM =
                                Math.ceil(tmpsrc.getMuUn() / MWDT) * MWDT;
                        if (INFO)
                            System.out.printf("  recomputed mmax: %.2f\n",
                                    tmpMM);

                        // -------------------------------------------------------------------------
                        // Crisis Double truncated GR
                        int num = (int) Math.round((tmpMM - MMIN) / MWDT);
                        mfd =
                                new IncrementalMagFreqDist(MMIN + MWDT / 2,
                                        tmpMM - MWDT / 2, num);

                        double mup = MMIN + MWDT;
                        double betaGR = tmpsrc.getBetaGR();
                        double alphaGR =
                                Math.log(tmpsrc.getOccRate()
                                        / (Math.exp(-betaGR * tmpsrc.getMmin()) - Math
                                                .exp(-betaGR * tmpMM)));

                        int idx = 0;
                        while (mup <= tmpMM + MWDT * 0.1) {
                            double occ =
                                    Math.exp(alphaGR - betaGR * (mup - MWDT))
                                            - Math.exp(alphaGR - betaGR * mup);
                            mup += MWDT;
                            mfd.add(idx, occ);
                            idx++;
                        }

                        //
                        if (INFO) {
                            for (int j = 0; j < mfd.getNum(); j++) {
                                System.out.printf(" %5.2f %7.5f \n",
                                        mfd.getX(j), mfd.getY(j));
                            }
                        }

                    } else if (tmpsrc.getOccMod() == 2) {

                        // -------------------------------------------------------------------------
                        // Crisis Characteristic model
                        double roundMMin =
                                Math.floor(tmpsrc.getMCharMin() / MWDT) * MWDT;
                        double roundMMax =
                                Math.ceil(tmpsrc.getMCharMax() / MWDT) * MWDT;
                        int num =
                                (int) Math
                                        .round((roundMMax - roundMMin) / MWDT);

                        // mfd = new IncrementalMagFreqDist(roundMMin+MWDT/2,
                        // roundMMax-MWDT/2,num);
                        mfd =
                                new IncrementalMagFreqDist(
                                        roundMMin + MWDT / 2, num, MWDT);

                        int idx = 0;
                        // This is the denominator to be used to compute
                        // occurrences
                        double den =
                                GaussianDistCalc
                                        .getCDF((tmpsrc.getMCharMax() - tmpsrc
                                                .getMCharExp())
                                                / tmpsrc.getSigmaMChar())
                                        - GaussianDistCalc.getCDF((tmpsrc
                                                .getMCharMin() - tmpsrc
                                                .getMCharExp())
                                                / tmpsrc.getSigmaMChar());
                        double mmin, mmax;
                        // Expected MChar
                        double mexp = tmpsrc.getMCharExp();
                        // Sigma
                        double sigma = tmpsrc.getSigmaMChar();
                        //
                        double soc = 0.0;
                        double mup = roundMMin + MWDT;
                        while (mup <= roundMMax - MWDT / 2) {
                            mmin = mup - MWDT;
                            if (idx == 1) {
                                mmin = tmpsrc.getMCharMin();
                            }
                            double occ =
                                    1.
                                            / tmpsrc.getMedianRate()
                                            * ((GaussianDistCalc
                                                    .getCDF((mup - mexp)
                                                            / sigma)) - (GaussianDistCalc
                                                    .getCDF((mmin - mexp)
                                                            / sigma))) / den;

                            if (INFO)
                                System.out.printf(
                                        "%5.2f %5.2f %5.2f: %8.5f %8.5f\n",
                                        mmin, mup, den, mup - MWDT / 2, occ);

                            mup += MWDT;
                            soc += occ;
                            mfd.add(idx, occ);
                            idx++;
                        }
                        if (INFO)
                            System.out
                                    .printf(" sum of occ: %7.4f (original rate: %7.4f)\n",
                                            soc, 1. / tmpsrc.getMedianRate());

                    } else {
                        // To do throw an exception
                        System.err
                                .println("Occorrence/mfd model: unsupported option");
                        throw new RuntimeException("");
                    }

                    // if (INFO) {
                    // System.out.println("MFD");
                    // for (int w= 0; w < mfd.getNum(); w++){
                    // System.out.printf(" mag: %5.2f rte: %6.3e\n",mfd.getX(w),mfd.getY(w));
                    // }
                    // }

                    // MFD for focal mechanism
                    FocalMechanism fm = new FocalMechanism();
                    IncrementalMagFreqDist[] arrMfd =
                            new IncrementalMagFreqDist[1];
                    arrMfd[0] = mfd;

                    FocalMechanism[] arrFm = new FocalMechanism[1];
                    arrFm[0] = fm;
                    MagFreqDistsForFocalMechs mfdffm =
                            new MagFreqDistsForFocalMechs(arrMfd, arrFm);

                    // Top of rupture
                    ArbitrarilyDiscretizedFunc depTopRup =
                            new ArbitrarilyDiscretizedFunc();
                    double depth = (Double) depthMap.keySet().toArray()[0];
                    depTopRup.set(MMIN, depth);

                    if (depthMap.keySet().size() == 1) {

                        if (USEAREASOURCES) {
                            // Instantiate the region
                            Region reg = new Region(locList, null);

                            // Shallow active tectonic sources
                            GEMAreaSourceData src =
                                    new GEMAreaSourceData("0", name,
                                            TectonicRegionType.ACTIVE_SHALLOW,
                                            reg, mfdffm, depTopRup, depth);
                            srcList.add(src);
                        }

                    } else if (depthMap.keySet().size() == 2) {

                        if (USEDIPPINGAREAS) {
                            // Fault trace
                            FaultTrace upperTrace = new FaultTrace("");
                            double upperDepth = -1.0;
                            FaultTrace lowerTrace = new FaultTrace("");
                            double lowerDepth = -1.0;

                            // Create a list with depths (depths ordered in
                            // increasing order)
                            ArrayList<Double> depList = new ArrayList<Double>();
                            for (double dep : depthMap.keySet()) {
                                depList.add(dep);
                            }
                            Collections.sort(depList);
                            upperDepth = depList.get(0);
                            lowerDepth = depList.get(1);

                            // Create the upper and lower traces
                            for (int j = 0; j < tmpsrc.getCoords().length; j++) {
                                if (Math.abs(tmpsrc.getDepth()[j] - upperDepth) < 1e-1) {
                                    upperTrace.add(new Location(tmpsrc
                                            .getCoords()[j][1], tmpsrc
                                            .getCoords()[j][0], upperDepth));
                                } else {
                                    lowerTrace.add(new Location(tmpsrc
                                            .getCoords()[j][1], tmpsrc
                                            .getCoords()[j][0], lowerDepth));
                                }
                            }

                            // Find the directions of the two traces and -
                            // eventually - revert one trace
                            if (Math.abs(upperTrace
                                    .getStrikeDirectionDifference(lowerTrace)) > 90.0) {
                                lowerTrace.reverse();
                            }

                            // Fix the rake ???????????????????????????
                            double rake = 90.0;

                            // Do some checks
                            if (upperTrace.getTraceLength() < 1e-2) {
                                // To do throw an exception
                                System.err
                                        .println("Upper trace lenght equal to 0");
                                throw new RuntimeException("");
                            }
                            // Do some checks
                            if (lowerTrace.getTraceLength() < 1e-2) {
                                // To do throw an exception
                                System.err
                                        .println("Lower trace lenght equal to 0");
                                throw new RuntimeException("");
                            }

                            // Information
                            if (INFO) {
                                System.out
                                        .println(" ------------------------------ ");
                                System.out.println(" Name: " + name);
                                System.out.println(" Upper trace: ");

                                // LocationList loclUP = new LocationList();
                                // for (int w=0; w<upperTrace.size(); w++){
                                // loclUP.add(upperTrace.getLocationAt(w));
                                // }
                                // for (Location loc : loclUP){
                                // System.out.printf(" %6.2f %6.2f %5.1f\n",
                                // loc.getLongitude(),loc.getLatitude(),loc.getDepth());
                                // }
                                // System.out.println(" Lower trace: ");
                                // for (Location loc :
                                // lowerTrace.getLocationList){
                                // System.out.printf(" %6.2f %6.2f %5.2f\n",
                                // loc.getLongitude(),loc.getLatitude(),loc.getDepth());
                                // }
                            }

                            // Subduction source
                            GEMSubductionFaultSourceData src =
                                    new GEMSubductionFaultSourceData(
                                            String.format("%d", subSrcCounter),
                                            name,
                                            TectonicRegionType.SUBDUCTION_INTERFACE,
                                            upperTrace, lowerTrace, rake, mfd,
                                            true);
                            srcList.add(src);

                            if (INFO)
                                System.out
                                        .println("Adding subduction ========== "
                                                + name);

                            subSrcCounter++;
                        }

                    } else {
                        // To do throw an exception
                        System.err
                                .println("Source geometry: unsupported option");
                        throw new RuntimeException("");
                    }

                }
            } finally {
                input.close();
                this.setList(srcList);
            }
        } catch (IOException ex) {
            ex.printStackTrace();
        }

    }

}