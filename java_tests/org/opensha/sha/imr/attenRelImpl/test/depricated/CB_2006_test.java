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
import org.opensha.sha.imr.attenRelImpl.depricated.CB_2006_AttenRel;
import org.opensha.sha.imr.param.EqkRuptureParams.DipParam;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupTopDepthParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGD_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGV_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusJB_OverRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.WarningDoublePropagationEffectParameter;
import org.opensha.sha.imr.param.SiteParams.DepthTo2pt5kmPerSecParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

public class CB_2006_test implements ParameterChangeWarningListener{


	private CB_2006_AttenRel cb_2006 = null;

	private static final String RESULT_SET_PATH = "test/org/opensha/sha/imr/attenRelImpl/test/AttenRelResultSetFiles/NGA_ModelsTestFiles/depricated/CB06/";
	//private static final String CB_2006_RESULTS = RESULT_SET_PATH +"CB2006_NGA.txt";

	private double[] period={0.010,0.020,0.030,0.050,0.075,0.10,0.15,0.20,0.25,0.30,0.40,0.50,0.75,1.0,1.5,2.0,3.0,4.0,5.0,7.5,10.0};


	//Tolerence to check if the results fall within the range.
	private static double tolerence = 1; //default value for the tolerence

	private DecimalFormat format = new DecimalFormat("0.####");
	private ArrayList testDataLines;
	public static void main(String[] args) {
		org.junit.runner.JUnitCore.runClasses(CB_2006_test.class);
	}

	public CB_2006_test() {
	}

	@Before
	public void setUp() {
		//create the instance of the CB_2006
		cb_2006 = new CB_2006_AttenRel(this);
		cb_2006.setParamDefaults();
		//testDataLines = FileUtils.loadFile(CB_2006_RESULTS);
	}

	@After
	public void tearDown() {
	}

	/*
	 * Test method for 'org.opensha.sha.imr.attenRelImpl.CB_2006_AttenRel.getMean()'
	 * Also Test method for 'org.opensha.sha.imr.attenRelImpl.CB_2006_AttenRel.getStdDev()'

	public void testMeanAndStdDev() {
		int numDataLines = testDataLines.size();
		for(int i=1;i<numDataLines;++i){

			StringTokenizer st = new StringTokenizer((String)testDataLines.get(i));
			double period = Double.parseDouble(st.nextToken().trim());
			if(period == -1)
				cb_2006.setIntensityMeasure(cb_2006.PGV_Param.NAME);
			else{
				cb_2006.setIntensityMeasure(cb_2006.SA_Param.NAME);
				cb_2006.getParameter(cb_2006.PeriodParam.NAME).setValue(new Double(period));
			}
			double mag = Double.parseDouble(st.nextToken().trim());
			cb_2006.getParameter(cb_2006.MAG_NAME).setValue(new Double(mag));
			String fltType = st.nextToken().trim();
			if(fltType.equals("SS"))
			  cb_2006.getParameter(cb_2006.FLT_TYPE_NAME).setValue(cb_2006.FLT_TYPE_STRIKE_SLIP);
			else if(fltType.equals("RV"))
				  cb_2006.getParameter(cb_2006.FLT_TYPE_NAME).setValue(cb_2006.FLT_TYPE_REVERSE);
			else
				cb_2006.getParameter(cb_2006.FLT_TYPE_NAME).setValue(cb_2006.FLT_TYPE_NORMAL);

			double frv= Double.parseDouble(st.nextToken().trim());
			double fnm= Double.parseDouble(st.nextToken().trim());
			double depthTop = Double.parseDouble(st.nextToken().trim());
			cb_2006.getParameter(cb_2006.RUP_TOP_NAME).setValue(new Double(depthTop));
			double dip = Double.parseDouble(st.nextToken().trim());
			cb_2006.getParameter(cb_2006.DIP_NAME).setValue(new Double(dip));
			double vs30 = Double.parseDouble(st.nextToken().trim());
			cb_2006.getParameter(cb_2006.VS30_NAME).setValue(new Double(vs30));
			double depth25 = Double.parseDouble(st.nextToken().trim());
			cb_2006.getParameter(cb_2006.DEPTH_2pt5_NAME).setValue(new Double(depth25));


			double rrup = Double.parseDouble(st.nextToken().trim());
			cb_2006.getParameter(DistanceRupParameter.NAME).setValue(new Double(rrup));

			double rjb = Double.parseDouble(st.nextToken().trim());
			double distRupMinusJB_OverRup = (rrup-rjb)/rrup;
			cb_2006.getParameter(DistRupMinusJB_OverRupParameter.NAME).setValue(new Double(distRupMinusJB_OverRup));
			double meanVal = cb_2006.getMean();
			double targetMedian = Double.parseDouble(st.nextToken().trim());
			double medianFromOpenSHA = Double.parseDouble(format.format(Math.exp(meanVal)));	
			targetMedian = Double.parseDouble(format.format(targetMedian));
			//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
			boolean results = compareResults(medianFromOpenSHA,targetMedian);
			//if the test was failure the add it to the test cases Vecotr that stores the values for  that failed

              //If any test for the CB-2006 failed


            if(results == false){
            	 String failedResultMetadata = "Results failed for Median calculation for" +
            	 		  "CB-2006 attenuation with the following parameter settings:"+
            	          "  Period ="+period+"\nMag ="+(float)mag+" rRup = "+(float)rrup+
            	          "  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+ " depth2pt5 ="+depth25+" FaultType = "+fltType+
            	          "   Frv = "+frv+
            	          "   Fnm = "+fnm+
            	          "   depthTop = "+depthTop+"   dip = "+dip+"\n"+
            	          "Median from OpenSHA = "+medianFromOpenSHA+"  should be = "+targetMedian;
            	 //System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
            	 //System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
              this.assertNull(failedResultMetadata,failedResultMetadata);
            }
            st.nextToken();
            st.nextToken();
            st.nextToken();
            cb_2006.getParameter(cb_2006.STD_DEV_TYPE_NAME).setValue(cb_2006.STD_DEV_TYPE_TOTAL);
            cb_2006.getParameter(cb_2006.COMPONENT_NAME).setValue(cb_2006.COMPONENT_RANDOM_HORZ);
            double stdVal = cb_2006.getStdDev();
			double targetStdDev = Double.parseDouble(st.nextToken().trim());
			double stdFromOpenSHA = Double.parseDouble(format.format(stdVal));	
			targetStdDev = Double.parseDouble(format.format(targetStdDev));
			//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
			results = compareResults(stdFromOpenSHA,targetStdDev);
			//if the test was failure the add it to the test cases Vecotr that stores the values for  that failed
        	 	//
               //If any test for the CY-2006 failed


            if(results == false){
            	String failedResultMetadata = "Results failed for Std Dev calculation for " +
            			                        "CB-2006 attenuation with the following parameter settings:"+
            									"  Period ="+period+"\nMag ="+(float)mag+" rRup = "+(float)rrup+
            									"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+ " depth2pt5 ="+depth25+" FaultType = "+fltType+
            									"   Frv = "+frv+
            									"   Fnm = "+fnm+
            									"   depthTop = "+depthTop+"\n   dip = "+dip+"\n"+
            									"Std Dev from OpenSHA = "+stdFromOpenSHA+"  should be = "+targetStdDev;;

            	 //System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
            	 //System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
              this.assertNull(failedResultMetadata,failedResultMetadata);
            }

            //if the all the succeeds and their is no fail for any test
            else {
              this.assertTrue("CY-2006 Test succeeded for all the test cases",results);
            }
		}
	}
	 */

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
					cb_2006.getParameter(FaultTypeParam.NAME).setValue(cb_2006.FLT_TYPE_STRIKE_SLIP);
				else if(fltType.equals("RV"))
					cb_2006.getParameter(FaultTypeParam.NAME).setValue(cb_2006.FLT_TYPE_REVERSE);
				else if(fltType.equals("NR"))
					cb_2006.getParameter(FaultTypeParam.NAME).setValue(cb_2006.FLT_TYPE_NORMAL);
				else
					continue;
				double dip = Double.parseDouble(fileName.substring(8,10));
				cb_2006.getParameter(DipParam.NAME).setValue(new Double(dip));
				double vs30 = Double.parseDouble(fileName.substring(11,fileName.indexOf("_Z")));
				((WarningDoubleParameter)cb_2006.getParameter(Vs30_Param.NAME)).setValueIgnoreWarning(new Double(vs30));
				double depthTop = Double.parseDouble(fileName.substring((fileName.indexOf("Zt")+2),fileName.lastIndexOf("_")));
				cb_2006.getParameter(RupTopDepthParam.NAME).setValue(new Double(depthTop));
				double depth25 = Double.parseDouble(fileName.substring(fileName.lastIndexOf("_")+3,fileName.indexOf(".")));
				((WarningDoubleParameter)cb_2006.getParameter(DepthTo2pt5kmPerSecParam.NAME)).setValueIgnoreWarning(new Double(depth25));
				try {
					testDataLines = FileUtils.loadFile(fileList[i].getAbsolutePath());
					int numLines = testDataLines.size();
					for(int j=1;j<numLines;++j){
						String fileLine = (String)testDataLines.get(j);
						StringTokenizer st = new StringTokenizer(fileLine);
						double mag = Double.parseDouble(st.nextToken().trim());
						cb_2006.getParameter(MagParam.NAME).setValue(new Double(mag));

						double rjb = Double.parseDouble(st.nextToken().trim());

						double rrup = Double.parseDouble(st.nextToken().trim());
						((WarningDoublePropagationEffectParameter)cb_2006.getParameter(DistanceRupParameter.NAME)).setValueIgnoreWarning(new Double(rrup));


						double distRupMinusJB_OverRup = (rrup-rjb)/rrup;
						((WarningDoublePropagationEffectParameter)cb_2006.getParameter(DistRupMinusJB_OverRupParameter.NAME)).setValueIgnoreWarning(new Double(distRupMinusJB_OverRup));
						st.nextToken().trim();
						cb_2006.setIntensityMeasure(PGA_Param.NAME);
						double openSHA_meanForPGA = Math.exp(cb_2006.getMean());
						double tested_mean = Double.parseDouble(st.nextToken().trim());
						boolean results = this.compareResults(openSHA_meanForPGA, tested_mean);
						if(results == false){
							String failedResultMetadata = "Results from file "+fileName+"failed for Mean calculation for " +
							"CB-2006 attenuation with the following parameter settings:"+
							"  PGA "+"\nMag ="+(float)mag+" rRup = "+(float)rrup+
							"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+ " depth2pt5 ="+depth25+" FaultType = "+fltType+
							"   depthTop = "+depthTop+"\n   dip = "+dip+"\n"+
							"Std Dev from OpenSHA = "+openSHA_meanForPGA+"  should be = "+tested_mean;

							//System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
							//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
							assertNull(failedResultMetadata,failedResultMetadata);
						}
						cb_2006.setIntensityMeasure(PGV_Param.NAME);
						double openSHA_mean = Math.exp(cb_2006.getMean());
						tested_mean = Double.parseDouble(st.nextToken().trim());
						results = this.compareResults(openSHA_mean, tested_mean);
						if(results == false){
							String failedResultMetadata = "Results from file "+fileName+"failed for Mean calculation for " +
							"CB-2006 attenuation with the following parameter settings:"+
							"  PGV "+"\nMag ="+(float)mag+" rRup = "+(float)rrup+
							"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+ " depth2pt5 ="+depth25+" FaultType = "+fltType+
							"   depthTop = "+depthTop+"\n   dip = "+dip+"\n"+
							"Std Dev from OpenSHA = "+openSHA_mean+"  should be = "+tested_mean;

							//System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
							//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
							assertNull(failedResultMetadata,failedResultMetadata);
						}
						cb_2006.setIntensityMeasure(PGD_Param.NAME);
						openSHA_mean = Math.exp(cb_2006.getMean());
						tested_mean = Double.parseDouble(st.nextToken().trim());
						results = this.compareResults(openSHA_mean, tested_mean);
						if(results == false){
							String failedResultMetadata = "Results from file "+fileName+"failed for Mean calculation for " +
							"CB-2006 attenuation with the following parameter settings:"+
							"  PGD "+"\nMag ="+(float)mag+" rRup = "+(float)rrup+
							"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+ " depth2pt5 ="+depth25+" FaultType = "+fltType+
							"   depthTop = "+depthTop+"\n   dip = "+dip+"\n"+
							"Std Dev from OpenSHA = "+openSHA_mean+"  should be = "+tested_mean;

							//System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
							//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
							assertNull(failedResultMetadata,failedResultMetadata);
						}
						cb_2006.setIntensityMeasure(SA_Param.NAME);
						int num= period.length;
						for(int k=0;k<num;++k){
							cb_2006.getParameter(PeriodParam.NAME).setValue(new Double(period[k]));
							if(k == 1 || k==2 || k==3){
								st.nextToken();
							}
							openSHA_mean = Math.exp(cb_2006.getMean());
							if(period[k] < 0.2  && openSHA_mean < openSHA_meanForPGA)
								openSHA_mean = openSHA_meanForPGA;
							tested_mean = Double.parseDouble(st.nextToken().trim());
							results = this.compareResults(openSHA_mean, tested_mean);
							if(results == false){
								String failedResultMetadata = "Results from file "+fileName+"failed for Mean calculation for " +
								"CB-2006 attenuation with the following parameter settings:"+
								"  SA at period = "+period[k]+"\nMag ="+(float)mag+" rRup = "+(float)rrup+
								"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+ " depth2pt5 ="+depth25+" FaultType = "+fltType+
								"   depthTop = "+depthTop+"\n   dip = "+dip+"\n"+
								"Std Dev from OpenSHA = "+openSHA_mean+"  should be = "+tested_mean;

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
