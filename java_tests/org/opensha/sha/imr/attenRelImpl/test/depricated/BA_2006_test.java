/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.imr.attenRelImpl.test.depricated;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.StringTokenizer;

import static org.junit.Assert.*;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;
import org.opensha.commons.param.WarningDoubleParameter;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.imr.attenRelImpl.depricated.BA_2006_AttenRel;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceJBParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.WarningDoublePropagationEffectParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

public class BA_2006_test implements ParameterChangeWarningListener{


	private BA_2006_AttenRel ba_2006 = null;

	private static final String RESULT_SET_PATH = "test/org/opensha/sha/imr/attenRelImpl/test/AttenRelResultSetFiles/NGA_ModelsTestFiles/depricated/BA06/";
	//private static final String BA_2006_RESULTS = RESULT_SET_PATH +"BA2006_NGA.txt";

	//Tolerence to check if the results fall within the range.
	private static double tolerence = 1; //default value for the tolerence

	private DecimalFormat medianformat;
	private DecimalFormat sigmaformat = new DecimalFormat("0.###");
	private ArrayList testDataLines;
	double[] period= {0.05,0.1,0.2,0.3,0.5,1,2,3,4,5};

	public static void main(String[] args) {
		org.junit.runner.JUnitCore.runClasses(BA_2006_test.class);
	}

	public BA_2006_test() {
	}

	@Before
	public void setUp() throws Exception {
		//create the instance of the CY_2006
		ba_2006 = new BA_2006_AttenRel(this);
		ba_2006.setParamDefaults();
	}

	@After
	public void tearDown() throws Exception {
	}

	/*
	 * Test method for 'org.opensha.sha.imr.attenRelImpl.CY_2006_AttenRel.getMean(int, double, double, double, double, double, double)'
	public void testGetMean() {
		int numDataLines = testDataLines.size();
		for(int i=1;i<numDataLines;++i){

			StringTokenizer st = new StringTokenizer((String)testDataLines.get(i));

			double period = Double.parseDouble(st.nextToken().trim());
			if(period == -1)
				ba_2006.setIntensityMeasure(ba_2006.PGV_Param.NAME);
			else{
			  ba_2006.setIntensityMeasure(ba_2006.SA_Param.NAME);
			  ba_2006.getParameter(ba_2006.PeriodParam.NAME).setValue(new Double(period));
			}
			double mag = Double.parseDouble(st.nextToken().trim());
			ba_2006.getParameter(ba_2006.MAG_NAME).setValue(new Double(mag));

			double rjb = Double.parseDouble(st.nextToken().trim());
			ba_2006.getParameter(DistanceJBParameter.NAME).setValue(new Double(rjb));

			double vs30 = Double.parseDouble(st.nextToken().trim());
			ba_2006.getParameter(ba_2006.VS30_NAME).setValue(new Double(vs30));

			int imech = Integer.parseInt(st.nextToken().trim());
			String faultType;
			if(imech == 0)
				faultType = ba_2006.FLT_TYPE_STRIKE_SLIP;
			else if(imech == 2)
				faultType = ba_2006.FLT_TYPE_REVERSE;
			else if(imech == 1)
				faultType = ba_2006.FLT_TYPE_NORMAL;
			else
				faultType = ba_2006.FLT_TYPE_UNKNOWN;

			ba_2006.getParameter(FaultTypeParam.NAME).setValue(faultType);
			double meanVal = ba_2006.getMean();

			double targetMedian = Double.parseDouble(st.nextToken().trim());
			String targetMedianString = ""+targetMedian;
			int numDecimal = targetMedianString.substring(targetMedianString.indexOf(".")+1).length();
			if(numDecimal > 5)
				medianformat = new DecimalFormat(".#####");
			else{
			    String numformat = ".";
			    for(int k=0;k<numDecimal;++k)
				    numformat +="#";
			    medianformat = new DecimalFormat(numformat);
			}
			//targetMedian = Double.parseDouble(medianformat.format(targetMedian));
			double medianFromOpenSHA = Double.parseDouble(medianformat.format(Math.exp(meanVal)));	
			targetMedian = Double.parseDouble(medianformat.format(targetMedian));	
			//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
			boolean results = compareResults(medianFromOpenSHA,targetMedian);
			//if the test was failure the add it to the test cases Vecotr that stores the values for  that failed
        	 	//If any test for the BA-2006 failed


            if(results == false){
            	 String failedResultMetadata = "Results failed for Median calculation for" +
            	 		" BA-2006 attenuation with the following parameter settings:"+
            	          "IMT ="+ba_2006.SA_Param.NAME+" with Period ="+period+"\nMag ="+(float)mag+
            	          "  vs30 = "+vs30+"  rjb = "+(float)rjb+"   FaultType = "+faultType+"\n"+
            	          " Median is "+medianFromOpenSHA+"  where as it should be "+targetMedian;

            	 //System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
            	 //System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
              this.assertNull(failedResultMetadata,failedResultMetadata);
            }
            st.nextToken();
            st.nextToken();
            st.nextToken();
            double stdVal = Math.exp(ba_2006.getStdDev());

            stdVal = Double.parseDouble(sigmaformat.format(stdVal));
            double targetSig = Double.parseDouble(st.nextToken().trim());
            targetSig = Double.parseDouble(sigmaformat.format(targetSig));
//          System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
			results = compareResults(stdVal,targetSig);
			if(results == false){
           	 String failedResultMetadata = "Results failed for Sig calculation for" +
           	 		"BA-2006 attenuation with the following parameter settings:"+
           	          "IMT ="+ba_2006.SA_Param.NAME+" with Period ="+period+"\nMag ="+(float)mag+
           	          "  vs30 = "+vs30+"  rjb = "+(float)rjb+"   FaultType = "+faultType+"\n"+
           	          " Sig is "+stdVal+"  where as it should be "+targetSig;

           	 //System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
           	 //System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
             this.assertNull(failedResultMetadata,failedResultMetadata);
           }
            //if the all the succeeds and their is no fail for any test
            else {
              this.assertTrue("CY-2006 Test succeeded for all the test cases",results);
            }
		}
	}*/

	/*
	 * Test method for 'org.opensha.sha.imr.attenRelImpl.CB_2006_AttenRel.getMean()'
	 * Also Test method for 'org.opensha.sha.imr.attenRelImpl.CB_2006_AttenRel.getStdDev()'
	 */
	@Test
	public void testMeanAndStdDev() {	
		File f = new File(RESULT_SET_PATH);
		File[] fileList = f.listFiles();
		for(int i=0;i<fileList.length;++i){
			String fileName = fileList[i].getName();
			if(fileName.endsWith(".txt")){
				String fltType = fileName.substring(5,7);
				if(fltType.equals("SS"))
					ba_2006.getParameter(FaultTypeParam.NAME).setValue(ba_2006.FLT_TYPE_STRIKE_SLIP);
				else if(fltType.equals("RV"))
					ba_2006.getParameter(FaultTypeParam.NAME).setValue(ba_2006.FLT_TYPE_REVERSE);
				else if(fltType.equals("NR"))
					ba_2006.getParameter(FaultTypeParam.NAME).setValue(ba_2006.FLT_TYPE_NORMAL);
				else if(fltType.equals("UN"))
					ba_2006.getParameter(FaultTypeParam.NAME).setValue(ba_2006.FLT_TYPE_UNKNOWN);
				else 
					continue;

				double vs30 = Double.parseDouble(fileName.substring(11,fileName.indexOf(".")));
				ba_2006.getParameter(Vs30_Param.NAME).setValue(new Double(vs30));
				try {
					testDataLines = FileUtils.loadFile(fileList[i].getAbsolutePath());
					int numLines = testDataLines.size();
					for(int j=1;j<numLines;++j){
						String fileLine = (String)testDataLines.get(j);
						StringTokenizer st = new StringTokenizer(fileLine);
						double mag = Double.parseDouble(st.nextToken().trim());
						((WarningDoubleParameter)ba_2006.getParameter(MagParam.NAME)).setValueIgnoreWarning(new Double(mag));

						double rjb = Double.parseDouble(st.nextToken().trim());
						((WarningDoublePropagationEffectParameter)ba_2006.getParameter(DistanceJBParameter.NAME)).setValueIgnoreWarning(new Double(rjb));
						st.nextToken().trim();//for rRup
						st.nextToken().trim();//for rSeis
						ba_2006.setIntensityMeasure(PGA_Param.NAME);
						double openSHA_mean_ForPGA = Math.exp(ba_2006.getMean());
						double tested_mean = Double.parseDouble(st.nextToken().trim());
						boolean results = this.compareResults(openSHA_mean_ForPGA, tested_mean);
						if(results == false){
							String failedResultMetadata = "Results from file "+fileName+"failed for Mean calculation for " +
							"BA-2006 attenuation with the following parameter settings:"+
							"  PGA "+"\nMag ="+(float)mag+
							"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+
							"Mean from OpenSHA = "+openSHA_mean_ForPGA+"  should be = "+tested_mean;

							//System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
							//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
							assertNull(failedResultMetadata,failedResultMetadata);
						}
						ba_2006.setIntensityMeasure(PGV_Param.NAME);
						double openSHA_mean = Math.exp(ba_2006.getMean());
						tested_mean = Double.parseDouble(st.nextToken().trim());
						results = this.compareResults(openSHA_mean, tested_mean);
						if(results == false){
							String failedResultMetadata = "Results from file "+fileName+"failed for Mean calculation for " +
							"BA-2006 attenuation with the following parameter settings:"+
							"  PGV "+"\nMag ="+(float)mag+
							"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+
							"Mean from OpenSHA = "+openSHA_mean+"  should be = "+tested_mean;

							//System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
							//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
							assertNull(failedResultMetadata,failedResultMetadata);
						}
						st.nextToken();//for PGD

						ba_2006.setIntensityMeasure(SA_Param.NAME);
						int num= period.length;
						for(int k=0;k<num;++k){
							ba_2006.getParameter(PeriodParam.NAME).setValue(new Double(period[k]));
							if(k == 0){
								st.nextToken();
								st.nextToken();
								st.nextToken();
								st.nextToken();
								st.nextToken();
								st.nextToken();

							}
							if(k==1 || k==2 || k==3 || k==4 || k==5 || k==6 ){
								st.nextToken();
							}

							openSHA_mean = Math.exp(ba_2006.getMean());
							if(period[k]< 0.2 && openSHA_mean<openSHA_mean_ForPGA)
								openSHA_mean = openSHA_mean_ForPGA;
							tested_mean = Double.parseDouble(st.nextToken().trim());
							results = this.compareResults(openSHA_mean, tested_mean);
							if(results == false){
								String failedResultMetadata = "Results from file "+fileName+"failed for Mean calculation for " +
								"BA-2006 attenuation with the following parameter settings:"+
								"  SA at period = "+period[k]+"\nMag ="+(float)mag+
								"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+
								"Mean from OpenSHA = "+openSHA_mean+"  should be = "+tested_mean;

								//System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
								//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
								assertNull(failedResultMetadata,failedResultMetadata);
							}
						}

					}
				} catch (FileNotFoundException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			}
		}
	}


	/**
	 * This function compares the values we obtained after running the values for
	 * the IMR and the target Values( our benchmark)
	 * @param valFromSHA = values we got after running the OpenSHA code for the IMR
	 * @param targetVal = values we are comparing with to see if OpenSHA does correct calculation
	 * @return
	 */
	private boolean compareResults(double valFromSHA,
			double targetVal){
		//comparing each value we obtained after doing the IMR calc with the target result
		//and making sure that values lies with the .01% range of the target values.
		//comparing if the values lies within the actual tolerence range of the target result
		double result = 0;
		if(targetVal!=0)
			result =(StrictMath.abs(valFromSHA-targetVal)/targetVal)*100;

		//System.out.println("Result: "+ result);
		if(result < this.tolerence)
			return true;
		return false;
	}


	public void parameterChangeWarning(ParameterChangeWarningEvent e){
		return;
	}
}
