package org.gem.engine.hazard.parsers.gscFrisk.canada;

import java.io.BufferedReader;
import java.util.ArrayList;

import org.gem.engine.hazard.parsers.GemFileParser;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.FocalMechanism;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;

import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class GscFriskSourceData02 extends GemFileParser {

    private static boolean INFO = false;
    private static double MMIN = 4.5;
    private static double MWDT = 0.1;

    public GscFriskSourceData02(BufferedReader file, boolean skipComm) {
        // public GscFriskSourceData01 (FileReader file, boolean skipComm) {

        ArrayList<GEMSourceData> srclst = new ArrayList<GEMSourceData>();
        SummedMagFreqDist sumMfd = null;
        Region reg = null;
        FaultTrace trace = null;

        // -----------------------------------------------------------------------------------------
        // Reads the file
        GscFriskInputFile gscif = new GscFriskInputFile(file, skipComm);

        // -----------------------------------------------------------------------------------------
        // Get the information contained in the header
        GscFriskInputHeader head = gscif.getHeader();

        // Info: number of global alternatives contained in the input file
        System.out.printf("Number of global alternatives: %d\n", +head.nGloAlt);

        // -----------------------------------------------------------------------------------------
        // Processing global alternatives
        for (int gaIdx = 0; gaIdx < head.nGloAlt; gaIdx++) {

            System.out.printf("Global alternative %d of %d\n", gaIdx,
                    head.nGloAlt);

            // Get the 'gaIdx' global alternative
            GscFriskInputAlternative ga =
                    gscif.getGlobalAlternatives().get(gaIdx);
            int srcSetIdx = 0;

            // -------------------------------------------------------------------------------------
            // Processing the sources into one global alternative
            for (int srcIdx = 0; srcIdx < ga.getSourceSet(0)
                    .getNumberOfSources(); srcIdx++) {
                // for (int srcIdx=0; srcIdx<1; srcIdx++){
                // if (srcIdx > 0) System.exit(0);

                // This contains all the information relative to the current
                // source
                GscFriskInputSource src =
                        ga.getSourceSet(srcSetIdx).getSource(srcIdx);

                // Repeat for all the geometries
                for (int geomIdx = 0; geomIdx < src.geomNum; geomIdx++) {
                    System.out.println("---------" + src.name);

                    // -----------------------------------------------------------------------------
                    // Area sources
                    if (src.geomTyp[geomIdx].matches("area")) {

                        // This is the source region
                        reg = new Region(src.coords.get(geomIdx), null);

                        // Repeat for all the depths
                        for (int depIdx = 0; depIdx < src.geomDepth[geomIdx].length; depIdx++) {

                            // Find the maximum magnitude
                            double mmaxlg = -1e10;
                            double mminlg = MMIN;
                            for (int i = 0; i < src.mMax[geomIdx].length; i++)
                                if (mmaxlg < src.mMax[geomIdx][i])
                                    mmaxlg = src.mMax[geomIdx][i];
                            double magDelta = 2.0;
                            mmaxlg = mmaxlg + magDelta;
                            mminlg = mminlg - magDelta;
                            int num =
                                    (int) Math.round((mmaxlg - mminlg) / MWDT);

                            // Create the summed Mfd
                            sumMfd =
                                    createMfd(ga, src, geomIdx, depIdx, num,
                                            magDelta, mminlg);

                            // Convert the distribution from Mlg to Mo
                            IncrementalMagFreqDist mfdMo =
                                    mfdMlgTomfdMo(sumMfd, mmaxlg, magDelta);

                            // Creates the hash map with depths
                            ArbitrarilyDiscretizedFunc depTopRup =
                                    new ArbitrarilyDiscretizedFunc();
                            depTopRup.set(6.0, src.geomDepth[geomIdx][depIdx]);

                            // Creates the final arrays requested to create the
                            // MagFreqDistsForFocalMechs
                            FocalMechanism[] fmArr = new FocalMechanism[1];
                            IncrementalMagFreqDist[] mfArr =
                                    new IncrementalMagFreqDist[1];
                            mfArr[0] = mfdMo;

                            fmArr[0] = new FocalMechanism();
                            MagFreqDistsForFocalMechs mfdffm =
                                    new MagFreqDistsForFocalMechs(mfArr, fmArr);

                            // ---------------------------------------------------------------------
                            // Creating the GEMAreaSourceData object
                            GEMAreaSourceData srcGem =
                                    new GEMAreaSourceData(String.format("%d",
                                            srcIdx), src.geomName[geomIdx],
                                            TectonicRegionType.STABLE_SHALLOW,
                                            reg, mfdffm, depTopRup,
                                            src.geomDepth[geomIdx][depIdx]);

                            srclst.add(srcGem);
                            System.out
                                    .printf("  Adding source %3d - Tot. rate: %7.4e avg depth: %6.2f \n",
                                            srclst.size(), mfdffm
                                                    .getMagFreqDist(0)
                                                    .getTotalIncrRate(), srcGem
                                                    .getAveHypoDepth());

                        }
                        // -----------------------------------------------------------------------------
                        // Fault sources
                    } else if (src.geomTyp[geomIdx].matches("fault")) {

                        trace = new FaultTrace("trace");
                        trace.addAll(src.coords.get(geomIdx));

                        // Repeat for all the fault dip values
                        for (int depIdx = 0; depIdx < src.geomDip1[geomIdx].length; depIdx++) {

                            // Find the maximum magnitude
                            double mmaxlg = -1e10;
                            double mminlg = MMIN;
                            for (int i = 0; i < src.mMax[geomIdx].length; i++)
                                if (mmaxlg < src.mMax[geomIdx][i])
                                    mmaxlg = src.mMax[geomIdx][i];
                            double magDelta = 2.0;
                            mmaxlg = mmaxlg + magDelta;
                            mminlg = mminlg - magDelta;
                            int num =
                                    (int) Math.round((mmaxlg - mminlg) / MWDT);

                            // Create the summed Mfd
                            sumMfd =
                                    createMfd(ga, src, geomIdx, depIdx, num,
                                            magDelta, mminlg);

                            // Convert the distribution from Mlg to Mo
                            IncrementalMagFreqDist mfdMo =
                                    mfdMlgTomfdMo(sumMfd, mmaxlg, magDelta);

                            GEMFaultSourceData srcGem =
                                    new GEMFaultSourceData(
                                            String.format("%d", srcIdx),
                                            src.geomName[geomIdx],
                                            TectonicRegionType.SUBDUCTION_INTERFACE,
                                            mfdMo,
                                            trace,
                                            (src.geomDip1[geomIdx][depIdx] + src.geomDip2[geomIdx][depIdx]) / 2, // average
                                                                                                                 // dip
                                            90.0,// rake
                                            src.geomZ1[geomIdx][depIdx],
                                            src.geomZ3[geomIdx][depIdx], true);

                            // String.format("%d",srcIdx),
                            // src.geomName[geomIdx],
                            // TectonicRegionType.STABLE_SHALLOW,
                            // reg,
                            // mfdffm,
                            // depTopRup,src.geomDepth[geomIdx][depIdx]);

                            srclst.add(srcGem);

                        }

                    } else {
                        System.err.println("Source model: unsupported option");
                        throw new RuntimeException("");
                    }

                }
            }

        }
        this.setList(srclst);
    }

    private double mlg2mo(double mlg) {
        double mo;
        mo = 2.689 - 0.252 * mlg + 0.127 * mlg * mlg;
        // mo = 1.12*mlg - 1.00;
        return mo;
    }

    /**
     * 
     * @param ga
     * @param src
     * @param geomIdx
     * @param depIdx
     * @param magDelta
     * @param mminlg
     */
    private SummedMagFreqDist createMfd(GscFriskInputAlternative ga,
            GscFriskInputSource src, int geomIdx, int depIdx, int numMfd,
            double magDelta, double mminlg) {

        double sumWei = 0.0;
        SummedMagFreqDist sumMfd =
                new SummedMagFreqDist(mminlg + MWDT / 2, numMfd, MWDT);

        for (int mmaxIdx = 0; mmaxIdx < src.mMax[geomIdx].length; mmaxIdx++) {
            double tmpMMax = src.mMax[geomIdx][mmaxIdx] + magDelta;

            // Repeat for nu-beta couples
            for (int nubIdx = 0; nubIdx < src.beta[geomIdx].length; nubIdx++) {

                // Compute the number of intervals
                int num = (int) Math.round((tmpMMax - mminlg) / MWDT);
                IncrementalMagFreqDist mfdLg =
                        new IncrementalMagFreqDist(mminlg + MWDT / 2, tmpMMax
                                - MWDT / 2, num);

                // Parameters of the Gutenberg-Richter distribution
                double betaGR = src.beta[geomIdx][nubIdx];
                double alphaGR = Math.log(src.nu[geomIdx][nubIdx]);

                // Filling the mfd distribution - This is the Mlg mfd
                double mup = mminlg + MWDT;
                int idx = 0;
                while (mup <= src.mMax[geomIdx][mmaxIdx] - MWDT / 2 + magDelta) {
                    // double occ = Math.exp(alphaGR-betaGR*(mup-MWDT))-
                    // Math.exp(alphaGR-betaGR*mup);
                    double occ = Math.exp(alphaGR - betaGR * (mup - MWDT));
                    if (INFO)
                        System.out.printf("%7.4e %5.2f: %5.2f-%5.2f: %8.4e\n",
                                alphaGR, betaGR, mup - MWDT, mup, occ);
                    mup += MWDT;
                    mfdLg.add(idx, occ);
                    idx++;
                }

                double oldrate = mfdLg.getTotalIncrRate();

                // Compute the scaled value of the total moment rate
                double moRate =
                        mfdLg.getTotalMomentRate()
                                * ga.getNuBetaWeights()[nubIdx]
                                * ga.getMaxMagWeights()[mmaxIdx]
                                * ga.getDepthsWeights()[depIdx];

                sumWei +=
                        ga.getNuBetaWeights()[nubIdx]
                                * ga.getMaxMagWeights()[mmaxIdx]
                                * ga.getDepthsWeights()[depIdx];

                // Scaling the mfd given the Tot. Moment Rate
                mfdLg.scaleToTotalMomentRate(moRate);

                // Updating the final mfd
                sumMfd.addResampledMagFreqDist(mfdLg, true);

                if (INFO)
                    System.out.printf(
                            "old %7.4e scaled %7.4e (sum tot Mo: %7.4e)\n",
                            oldrate, mfdLg.getTotalIncrRate(),
                            sumMfd.getTotalMomentRate());

            }
        }

        //
        return sumMfd;
    }

    /**
     * This method converts an input mfd in terms of Mlg into a mfd in terms of
     * Mo.
     * 
     * @param sumMfd
     * @param mmaxlg
     * @param magDelta
     */
    private IncrementalMagFreqDist mfdMlgTomfdMo(SummedMagFreqDist sumMfd,
            double mmaxlg, double magDelta) {

        // Fixing minimum an
        double mminMo = MMIN;
        double mmaxMo = Math.ceil(mlg2mo(mmaxlg - magDelta) / MWDT) * MWDT;
        int numMo = (int) Math.round((mmaxMo - mminMo) / MWDT);

        if (INFO)
            System.out.printf("-------Maximum magnitude (orig: %5.2f) %5.2f",
                    mmaxlg - magDelta, mmaxMo);

        // New mfd for moment magnitude
        IncrementalMagFreqDist mfdMo =
                new IncrementalMagFreqDist(mminMo + MWDT / 2, numMo, MWDT);

        // Mfd used for the conversion
        ArbitrarilyDiscretizedFunc mfdMoOriginal =
                new ArbitrarilyDiscretizedFunc();

        // Populating the mfd used for conversion
        for (int i = 0; i < sumMfd.getNum(); i++) {
            mfdMoOriginal.set(mlg2mo(sumMfd.getX(i)), sumMfd.getY(i));
        }

        // Populating the mfd for moment magnitude
        for (int i = 0; i < mfdMo.getNum(); i++) {
            double rate =
                    mfdMoOriginal.getInterpolatedY(mfdMo.getX(i) - MWDT / 2)
                            - mfdMoOriginal.getInterpolatedY(mfdMo.getX(i)
                                    + MWDT / 2);
            mfdMo.set(i, rate);
            if (INFO) {
                System.out.printf("%6.2f %6.2f %6.2e \n", mfdMo.getX(i) - MWDT
                        / 2, mfdMo.getX(i) + MWDT / 2, rate);
            }
        }

        return mfdMo;
    }

}
