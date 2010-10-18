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

import org.junit.After;
import org.junit.Before;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.DataUtils;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.attenRelImpl.CB_2008_AttenRel;
import org.opensha.sha.imr.param.EqkRuptureParams.DipParam;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupTopDepthParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupWidthParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGD_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusDistX_OverRupParam;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusJB_OverRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.HangingWallFlagParam;
import org.opensha.sha.imr.param.PropagationEffectParams.WarningDoublePropagationEffectParameter;
import org.opensha.sha.imr.param.SiteParams.DepthTo1pt0kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.imr.param.SiteParams.Vs30_TypeParam;

public class CB_2008_test extends NGATest implements
        ParameterChangeWarningListener {

    private CB_2008_AttenRel cb_2008 = null;

    private static final String RESULT_SET_PATH = "NGA_ModelsTestFiles/CB08/";

    private final double[] period = { 0.010, 0.020, 0.030, 0.050, 0.075, 0.10,
            0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0,
            5.0, 7.5, 10.0 };

    private String failMetadata = "";
    private String failLine = "";

    private ArrayList<String> testDataLines;

    public static void main(String[] args) {
        org.junit.runner.JUnitCore.runClasses(CB_2008_test.class);
    }

    public CB_2008_test() {
        super(RESULT_SET_PATH);
    }

    @Override
    @Before
    public void setUp() {
        super.setUp();
        // create the instance of the CB_2006
        cb_2008 = new CB_2008_AttenRel(this);
        cb_2008.setParamDefaults();
        // testDataLines = FileUtils.loadFile(CB_2006_RESULTS);
    }

    @Override
    @After
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
        double discrep = 0;

        String fileName = file.getName();

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
            if (fileName.contains("SIGARB")) {
                // Std Dev of arbitrary horizontal component
                cb_2008.getParameter(ComponentParam.NAME).setValue(
                        ComponentParam.COMPONENT_RANDOM_HORZ);
                testValString = "Std Dev of Arb Horz Comp";
            } else {
                // Std dev of geomteric mean
                cb_2008.getParameter(ComponentParam.NAME).setValue(
                        ComponentParam.COMPONENT_GMRotI50);
                testValString = "Std dev of geomteric mean";
            }
        }
        int index1 = fileName.indexOf(".TXT");
        String fltType = fileName.substring(index1 - 2, index1);

        if (fltType.equals("SS"))
            cb_2008.getParameter(FaultTypeParam.NAME).setValue(
                    cb_2008.FLT_TYPE_STRIKE_SLIP);
        else if (fltType.equals("RV"))
            cb_2008.getParameter(FaultTypeParam.NAME).setValue(
                    cb_2008.FLT_TYPE_REVERSE);
        else if (fltType.equals("NM"))
            cb_2008.getParameter(FaultTypeParam.NAME).setValue(
                    cb_2008.FLT_TYPE_NORMAL);
        else
            throw new RuntimeException("Unknown Fault Type");

        try {
            testDataLines = FileUtils.loadFile(file.getAbsolutePath());
            int numLines = testDataLines.size();
            for (int j = 1; j < numLines; ++j) {
                System.out.println("Doing " + j + " of " + numLines);
                String fileLine = testDataLines.get(j);
                StringTokenizer st = new StringTokenizer(fileLine);
                double mag = Double.parseDouble(st.nextToken().trim());
                cb_2008.getParameter(MagParam.NAME).setValue(new Double(mag));

                double rrup = Double.parseDouble(st.nextToken().trim());
                ((WarningDoublePropagationEffectParameter) cb_2008
                        .getParameter(DistanceRupParameter.NAME))
                        .setValueIgnoreWarning(new Double(rrup));

                double rjb = Double.parseDouble(st.nextToken().trim());

                double distRupMinusJB_OverRup;
                if (rrup == 0 && rjb == 0)
                    distRupMinusJB_OverRup = 0;
                else
                    distRupMinusJB_OverRup = (rrup - rjb) / rrup;

                ((WarningDoublePropagationEffectParameter) cb_2008
                        .getParameter(DistRupMinusJB_OverRupParameter.NAME))
                        .setValueIgnoreWarning(new Double(
                                distRupMinusJB_OverRup));

                st.nextToken().trim(); // ignore R(x) ( Horizontal distance from
                                       // top of rupture perpendicular to fault
                                       // strike)

                double dip = Double.parseDouble(st.nextToken().trim());
                cb_2008.getParameter(DipParam.NAME).setValue(new Double(dip));

                st.nextToken().trim(); // ignore W, width of rup plane

                double depthTop = Double.parseDouble(st.nextToken().trim());
                cb_2008.getParameter(RupTopDepthParam.NAME).setValue(
                        new Double(depthTop));

                double vs30 = Double.parseDouble(st.nextToken().trim());
                ((WarningDoubleParameter) cb_2008.getParameter(Vs30_Param.NAME))
                        .setValueIgnoreWarning(new Double(vs30));

                double depth25 = Double.parseDouble(st.nextToken().trim());
                ((WarningDoubleParameter) cb_2008
                        .getParameter(DepthTo2pt5kmPerSecParam.NAME))
                        .setValueIgnoreWarning(new Double(depth25));

                cb_2008.setIntensityMeasure(SA_Param.NAME);
                int num = period.length;
                double openSHA_Val, tested_Val;
                for (int k = 0; k < num; ++k) {
                    cb_2008.getParameter(PeriodParam.NAME).setValue(
                            new Double(period[k]));
                    if (isMedian)
                        openSHA_Val = Math.exp(cb_2008.getMean());
                    else
                        openSHA_Val = cb_2008.getStdDev();
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
                                        + "\nMag =" + (float) mag + " rRup = "
                                        + (float) rrup + "  vs30 = " + vs30
                                        + "  rjb = " + (float) rjb + "\n"
                                        + " depth2pt5 =" + depth25
                                        + " FaultType = " + fltType
                                        + "   depthTop = " + depthTop
                                        + "\n   dip = " + dip + "\n"
                                        + testValString + " from OpenSHA = "
                                        + openSHA_Val + "  should be = "
                                        + tested_Val;

                        failLine = fileLine;
                        failMetadata = "Line: " + fileLine;
                        failMetadata +=
                                "\nTest number= " + "(" + j + "/" + numLines
                                        + ")" + " failed for "
                                        + failedResultMetadata;
                        // System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
                        failMetadata += "\n" + getOpenSHAParams(cb_2008);

                        return -1;
                    }
                }

                cb_2008.setIntensityMeasure(PGA_Param.NAME);
                if (isMedian)
                    openSHA_Val = Math.exp(cb_2008.getMean());
                else
                    openSHA_Val = cb_2008.getStdDev();
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
                                    + " rRup = " + (float) rrup + "  vs30 = "
                                    + vs30 + "  rjb = " + (float) rjb + "\n"
                                    + " depth2pt5 =" + depth25
                                    + " FaultType = " + fltType
                                    + "   depthTop = " + depthTop
                                    + "\n   dip = " + dip + "\n"
                                    + testValString + " from OpenSHA = "
                                    + openSHA_Val + "  should be = "
                                    + tested_Val;

                    failLine = fileLine;
                    failMetadata = "Line: " + fileLine;
                    failMetadata +=
                            "\nTest number= " + "(" + j + "/" + numLines + ")"
                                    + " failed for " + failedResultMetadata;
                    // System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
                    failMetadata += "\n" + getOpenSHAParams(cb_2008);

                    return -1;
                }
                cb_2008.setIntensityMeasure(PGV_Param.NAME);
                if (isMedian)
                    openSHA_Val = Math.exp(cb_2008.getMean());
                else
                    openSHA_Val = cb_2008.getStdDev();
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
                                    + " rRup = " + (float) rrup + "  vs30 = "
                                    + vs30 + "  rjb = " + (float) rjb + "\n"
                                    + " depth2pt5 =" + depth25
                                    + " FaultType = " + fltType
                                    + "   depthTop = " + depthTop
                                    + "\n   dip = " + dip + "\n"
                                    + testValString + " from OpenSHA = "
                                    + openSHA_Val + "  should be = "
                                    + tested_Val;

                    failLine = fileLine;
                    failMetadata = "Line: " + fileLine;
                    failMetadata +=
                            "\nTest number= " + "(" + j + "/" + numLines + ")"
                                    + " failed for " + failedResultMetadata;
                    // System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
                    failMetadata += "\n" + getOpenSHAParams(cb_2008);

                    return -1;
                }
                cb_2008.setIntensityMeasure(PGD_Param.NAME);
                if (isMedian)
                    openSHA_Val = Math.exp(cb_2008.getMean());
                else
                    openSHA_Val = cb_2008.getStdDev();
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
                                    + "  PGD " + "\nMag =" + (float) mag
                                    + " rRup = " + (float) rrup + "  vs30 = "
                                    + vs30 + "  rjb = " + (float) rjb + "\n"
                                    + " depth2pt5 =" + depth25
                                    + " FaultType = " + fltType
                                    + "   depthTop = " + depthTop
                                    + "\n   dip = " + dip + "\n"
                                    + testValString + " from OpenSHA = "
                                    + openSHA_Val + "  should be = "
                                    + tested_Val;

                    failLine = fileLine;
                    failMetadata = "Line: " + fileLine;
                    failMetadata +=
                            "\nTest number= " + "(" + j + "/" + numLines + ")"
                                    + " failed for " + failedResultMetadata;
                    // System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
                    failMetadata += "\n" + getOpenSHAParams(cb_2008);

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

        System.out.println("Maximum Discrepancy: " + discrep);
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
