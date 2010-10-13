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

import static org.junit.Assert.assertTrue;

import java.io.File;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;

public abstract class NGATest implements ParameterChangeWarningListener {

    public static double tolerance = 0.5;

    private final String dir;

    public NGATest(String dir) {
        this.dir =
                "java_tests" + File.separator + "data" + File.separator + dir;
    }

    @Before
    public void setUp() {

    }

    @After
    public void tearDown() {

    }

    /**
     * Tests a single file
     * 
     * @param filePath
     * @return discrepancy, or negative number for failure
     */
    public abstract double doSingleFileTest(File file);

    public abstract String getLastFailMetadata();

    public abstract String getLastFailLine();

    private ArrayList<File> getTestFiles() {
        File f = new File(dir);
        File[] fileList = f.listFiles();

        ArrayList<File> files = new ArrayList<File>();

        for (int i = 0; i < fileList.length; ++i) {

            String fileName = fileList[i].getName();

            if (fileName.contains("README")
                    || fileName.contains("COEF")
                    || !(fileName.contains(".OUT") || fileName.contains(".TXT")))
                continue; // skip the README/COEF/Fortran files

            files.add(fileList[i]);
        }

        return files;
    }

    @Test
    public void testAll() {
        double maxDisc = 0;
        for (File file : getTestFiles()) {
            double discrep = doSingleFileTest(file);
            assertTrue(discrep >= 0);
            if (discrep > maxDisc)
                maxDisc = discrep;
        }
        System.out.println("Maximum discrepancy: " + maxDisc);
    }

    public void runDiagnostics() throws Exception {
        this.setUp();
        double maxDisc = 0;
        String summary = "";
        for (File file : getTestFiles()) {
            double discrep = doSingleFileTest(file);
            if (discrep > maxDisc)
                maxDisc = discrep;

            if (discrep < 0) { // fail
                summary += "\n" + file.getName() + ": FAILED for line:";
                summary += "\n" + this.getLastFailLine();
            } else { // good
                summary +=
                        "\n" + file.getName() + ": PASSED for discrepancey: "
                                + discrep;
            }
        }
        System.out.println(summary);
        System.out.println("Maximum discrepancy: " + maxDisc);
    }

    protected double[] loadPeriods(String line) {
        StringTokenizer tok = new StringTokenizer(line);

        // skip the first 9
        for (int i = 0; i < 9; i++) {
            tok.nextToken();
        }

        String col = tok.nextToken();

        ArrayList<Double> periodList = new ArrayList<Double>();

        while (!col.contains("PGA")) {
            periodList.add(Double.parseDouble(col));

            col = tok.nextToken();
        }

        double periods[] = new double[periodList.size()];

        String str = "";

        for (int i = 0; i < periodList.size(); i++) {
            periods[i] = periodList.get(i);
            str += " " + periods[i];
        }

        System.out.println("Periods:" + str);

        return periods;
    }

    @Override
    public void parameterChangeWarning(ParameterChangeWarningEvent e) {
        System.err.println("Parameter change warning!");
        System.err.flush();
        return;
    }

}
