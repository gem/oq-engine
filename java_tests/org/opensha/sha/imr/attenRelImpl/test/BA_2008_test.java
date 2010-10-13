/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with the Southern California
 * Earthquake Center (SCEC, http://www.scec.org) at the University of Southern
 * California and the UnitedStates Geological Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 * 
 * http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 ******************************************************************************/

package org.opensha.sha.imr.attenRelImpl.test;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.DataUtils;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.param.EqkRuptureParams.DipParam;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupTopDepthParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupWidthParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusDistX_OverRupParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusJB_OverRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.HangingWallFlagParam;
import org.opensha.sha.imr.param.PropagationEffectParams.WarningDoublePropagationEffectParameter;
import org.opensha.sha.imr.param.SiteParams.DepthTo1pt0kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam;

public class BA_2008_test extends NGATest implements
        ParameterChangeWarningListener {

    private BA_2008_AttenRel ba_2008 = null;

    private static final String RESULT_SET_PATH = "NGA_ModelsTestFiles/BA08/";

    private final double[] period = { 0.010, 0.020, 0.030, 0.050, 0.075, 0.10,
            0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0,
            5.0, 7.5, 10.0 };

    private String failMetadata = "";
    private String failLine = "";

    private ArrayList<String> testDataLines;

    public static void main(String[] args) {
        BA_2008_test test = new BA_2008_test();
        try {
            test.runDiagnostics();
        } catch (Exception e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
        }
    }

    public BA_2008_test() {
        super(RESULT_SET_PATH);
    }

    @Override
    public void setUp() {
        super.setUp();
        // create the instance of the CB_2006
        ba_2008 = new BA_2008_AttenRel(this);
        ba_2008.setParamDefaults();
        // testDataLines = FileUtils.loadFile(CB_2006_RESULTS);
    }

    @Override
    public void tearDown() {
        super.tearDown();
    }

    /*
     * Test method for
     * 'org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel.getMean()' Also Test
     * method for
     * 'org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel.getStdDev()'
     */
    @Override
    public double doSingleFileTest(File file) {
        String fileName = file.getName();

        double discrep = 0;

        boolean isMedian = false;
        String testValString = "Std Dev";
        if (fileName.contains("MEDIAN")) { // test mean
            isMedian = true;
            testValString = "Mean";
        } else { // test Standard Deviation
            isMedian = false;
            /*
             * set whether we are testing Std dev of geomteric mean or standard
             * deviation of arbitrary horizontal component
             */
            if (fileName.contains("SIGTM")) {
                // Std Dev of arbitrary horizontal component
                ba_2008.getParameter(FaultTypeParam.NAME).setValue(
                        BA_2008_AttenRel.FLT_TYPE_STRIKE_SLIP);
                testValString = "Std Dev of geometric mean for known faulting";
            } else {
                // Std dev of geomteric mean
                ba_2008.getParameter(FaultTypeParam.NAME).setValue(
                        BA_2008_AttenRel.FLT_TYPE_UNKNOWN);
                testValString =
                        "Std dev of geomteric mean for unspecified faulting";
            }
        }
        int index1 = fileName.indexOf(".TXT");
        String fltType = fileName.substring(index1 - 2, index1);
        fltType.replaceAll("_", "");

        if (fileName.contains("SS.TXT") && !fileName.contains("SIGTU"))
            ba_2008.getParameter(FaultTypeParam.NAME).setValue(
                    ba_2008.FLT_TYPE_STRIKE_SLIP);
        else if (fileName.contains("RV.TXT"))
            ba_2008.getParameter(FaultTypeParam.NAME).setValue(
                    ba_2008.FLT_TYPE_REVERSE);
        else if (fileName.contains("NM.TXT"))
            ba_2008.getParameter(FaultTypeParam.NAME).setValue(
                    ba_2008.FLT_TYPE_NORMAL);
        else
            // throw new RuntimeException("Unknown Fault Type");
            ba_2008.getParameter(FaultTypeParam.NAME).setValue(
                    ba_2008.FLT_TYPE_UNKNOWN);

        try {
            testDataLines = FileUtils.loadFile(file.getAbsolutePath());
            int numLines = testDataLines.size();
            for (int j = 1; j < numLines; ++j) {
                System.out.println("Doing " + j + " of " + numLines);
                String fileLine = testDataLines.get(j);
                StringTokenizer st = new StringTokenizer(fileLine);
                double mag = Double.parseDouble(st.nextToken().trim());
                ((WarningDoubleParameter) ba_2008.getParameter(MagParam.NAME))
                        .setValueIgnoreWarning(new Double(mag));

                // Rrup not used, skipping
                st.nextToken();
                // ((WarningDoublePropagationEffectParameter)ba_2008.getParameter(DistanceRupParameter.NAME)).setValueIgnoreWarning(new
                // Double(rrup));

                double rjb = Double.parseDouble(st.nextToken().trim());
                ((WarningDoublePropagationEffectParameter) ba_2008
                        .getParameter(DistanceJBParameter.NAME))
                        .setValueIgnoreWarning(new Double(rjb));

                st.nextToken().trim(); // ignore R(x) ( Horizontal distance from
                                       // top of rupture perpendicular to fault
                                       // strike)

                st.nextToken(); // ignore dip
                // ba_2008.getParameter(ba_2008.DIP_NAME).setValue(new
                // Double(dip));

                st.nextToken(); // ignore W, width of rup plane

                st.nextToken(); // ignore Ztor, depth of top

                double vs30 = Double.parseDouble(st.nextToken().trim());
                ((WarningDoubleParameter) ba_2008.getParameter(Vs30_Param.NAME))
                        .setValueIgnoreWarning(new Double(vs30));

                st.nextToken(); // ignore Zsed, sediment/basin depth

                ba_2008.setIntensityMeasure(SA_Param.NAME);
                int num = period.length;
                double openSHA_Val, tested_Val;
                for (int k = 0; k < num; ++k) {
                    ba_2008.getParameter(PeriodParam.NAME).setValue(
                            new Double(period[k]));
                    if (isMedian)
                        openSHA_Val = Math.exp(ba_2008.getMean());
                    else
                        openSHA_Val = ba_2008.getStdDev();
                    tested_Val = Double.parseDouble(st.nextToken().trim());
                    double result =
                            DataUtils.getPercentDiff(openSHA_Val, tested_Val);
                    if (result > discrep)
                        discrep = result;
                    if (result > tolerance) {
                        String failedResultMetadata =
                                "Results from file "
                                        + fileName
                                        + "failed for  calculation for "
                                        + "CB-2008 attenuation with the following parameter settings:"
                                        + "  SA at period = " + period[k]
                                        + "\nMag =" + (float) mag + "  vs30 = "
                                        + vs30 + "  rjb = " + (float) rjb
                                        + "\n" + " FaultType = " + fltType
                                        + "\n" + testValString
                                        + " from OpenSHA = " + openSHA_Val
                                        + "  should be = " + tested_Val;

                        failLine = fileLine;
                        failMetadata = "Line: " + fileLine;
                        failMetadata +=
                                "\nTest number= " + "(" + j + "/" + numLines
                                        + ")" + " failed for "
                                        + failedResultMetadata;
                        // System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
                        failMetadata += "\n" + getOpenSHAParams(ba_2008);

                        return -1;
                    }
                }

                ba_2008.setIntensityMeasure(PGA_Param.NAME);
                if (isMedian)
                    openSHA_Val = Math.exp(ba_2008.getMean());
                else
                    openSHA_Val = ba_2008.getStdDev();
                tested_Val = Double.parseDouble(st.nextToken().trim());
                double result =
                        org.opensha.commons.util.DataUtils.getPercentDiff(
                                openSHA_Val, tested_Val);
                if (result > discrep)
                    discrep = result;
                if (result > tolerance) {
                    String failedResultMetadata =
                            "Results from file "
                                    + fileName
                                    + "failed for  calculation for "
                                    + "CB-2008 attenuation with the following parameter settings:"
                                    + "  PGA " + "\nMag =" + (float) mag
                                    + "  vs30 = " + vs30 + "  rjb = "
                                    + (float) rjb + "\n" + " FaultType = "
                                    + fltType + "\n" + testValString
                                    + " from OpenSHA = " + openSHA_Val
                                    + "  should be = " + tested_Val;

                    failLine = fileLine;
                    failMetadata = "Line: " + fileLine;
                    failMetadata +=
                            "\nTest number= " + "(" + j + "/" + numLines + ")"
                                    + " failed for " + failedResultMetadata;
                    // System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
                    failMetadata += "\n" + getOpenSHAParams(ba_2008);

                    return -1;
                }
                ba_2008.setIntensityMeasure(PGV_Param.NAME);
                if (isMedian)
                    openSHA_Val = Math.exp(ba_2008.getMean());
                else
                    openSHA_Val = ba_2008.getStdDev();
                tested_Val = Double.parseDouble(st.nextToken().trim());
                result =
                        org.opensha.commons.util.DataUtils.getPercentDiff(
                                openSHA_Val, tested_Val);
                if (result > discrep)
                    discrep = result;
                if (result > tolerance) {
                    String failedResultMetadata =
                            "Results from file "
                                    + fileName
                                    + "failed for calculation for "
                                    + "CB-2008 attenuation with the following parameter settings:"
                                    + "  PGV " + "\nMag =" + (float) mag
                                    + "  vs30 = " + vs30 + "  rjb = "
                                    + (float) rjb + "\n" + " FaultType = "
                                    + fltType + "\n" + testValString
                                    + " from OpenSHA = " + openSHA_Val
                                    + "  should be = " + tested_Val;

                    failLine = fileLine;
                    failMetadata = "Line: " + fileLine;
                    failMetadata +=
                            "\nTest number= " + "(" + j + "/" + numLines + ")"
                                    + " failed for " + failedResultMetadata;
                    // System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
                    failMetadata += "\n" + getOpenSHAParams(ba_2008);

                    return -1;
                }

            }
        } catch (FileNotFoundException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            return -1;
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            return -1;
        }

        System.out.println("Maximum Discrepancy: " + (float) discrep + "%");
        return discrep;
    }

    private String getOpenSHAParams(AttenuationRelationship attenRel) {
        String str = "";

        str += "OpenSHA params:";
        if (attenRel.getIntensityMeasure().getName().equals(SA_Param.NAME))
            str +=
                    "\nSA period = "
                            + attenRel.getParameter(PeriodParam.NAME)
                                    .getValue();
        else
            str += "\nIM Type = " + attenRel.getIntensityMeasure().getName();
        str += "\nMag = " + attenRel.getParameter(MagParam.NAME).getValue();
        str +=
                "\tRrup = "
                        + attenRel.getParameter(DistanceRupParameter.NAME)
                                .getValue();
        str +=
                "\t(Rrup-Rjb)/Rrup = "
                        + attenRel.getParameter(
                                DistRupMinusJB_OverRupParameter.NAME)
                                .getValue();
        str +=
                "\nFault Type = "
                        + attenRel.getParameter(FaultTypeParam.NAME).getValue();
        str +=
                "\t(distRup-distX)/distRup = "
                        + attenRel.getParameter(
                                DistRupMinusDistX_OverRupParam.NAME).getValue();
        str += "\tDip = " + attenRel.getParameter(DipParam.NAME).getValue();
        str +=
                "\nDDWidth = "
                        + attenRel.getParameter(RupWidthParam.NAME).getValue();
        str +=
                "\tzTor = "
                        + attenRel.getParameter(RupTopDepthParam.NAME)
                                .getValue();
        str += "\tVs30 = " + attenRel.getParameter(Vs30_Param.NAME).getValue();
        str +=
                "\tVs30 flag = "
                        + attenRel.getParameter(Vs30_TypeParam.NAME).getValue();
        str +=
                "\nDepthto1km/sec = "
                        + attenRel.getParameter(DepthTo1pt0kmPerSecParam.NAME)
                                .getValue();
        str +=
                "\tHanging Wall Flag: = "
                        + attenRel.getParameter(HangingWallFlagParam.NAME)
                                .getValue();
        str += "\n";

        return str;
    }

    @Override
    public void parameterChangeWarning(ParameterChangeWarningEvent e) {
        return;
    }

    @Override
    public String getLastFailLine() {
        return failLine;
    }

    @Override
    public String getLastFailMetadata() {
        return failMetadata;
    }
}
