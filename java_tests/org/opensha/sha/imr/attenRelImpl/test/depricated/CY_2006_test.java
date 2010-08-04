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
import org.opensha.sha.imr.attenRelImpl.depricated.CY_2006_AttenRel;
import org.opensha.sha.imr.param.EqkRuptureParams.DipParam;
import org.opensha.sha.imr.param.EqkRuptureParams.FaultTypeParam;
import org.opensha.sha.imr.param.EqkRuptureParams.MagParam;
import org.opensha.sha.imr.param.EqkRuptureParams.RupTopDepthParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.PropagationEffectParams.DistRupMinusJB_OverRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.DistanceRupParameter;
import org.opensha.sha.imr.param.PropagationEffectParams.WarningDoublePropagationEffectParameter;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;

public class CY_2006_test implements ParameterChangeWarningListener{


	private CY_2006_AttenRel cy_2006 = null;

	private static final String RESULT_SET_PATH = "test/org/opensha/sha/imr/attenRelImpl/test/AttenRelResultSetFiles/NGA_ModelsTestFiles/depricated/CY06/";
	//private static final String CY_2006_RESULTS = RESULT_SET_PATH +"CY2006_NGA.txt";
	private double[] period = {
			0.01,0.02,0.025,0.03,0.04,0.05,0.075,0.1,0.15,
			0.2,0.25,0.3,0.4,0.5,0.75,1,1.5,2.0,3.0,4,5,7.5,10
	};


	//Tolerence to check if the results fall within the range.
	private static double tolerence = 1; //default value for the tolerence

	private ArrayList testDataLines;
	public static void main(String[] args) {
		org.junit.runner.JUnitCore.runClasses(CY_2006_test.class);
	}

	public CY_2006_test() {
	}

	@Before
	public void setUp() throws Exception {
		//create the instance of the CY_2006
		cy_2006 = new CY_2006_AttenRel(this);
		cy_2006.setParamDefaults();
	}

	@After
	protected void tearDown() throws Exception {
	}

	/*
	 * Test method for 'org.opensha.sha.imr.attenRelImpl.CY_2006_AttenRel.getMean(int, double, double, double, double, double, double)'
	public void testGetMean() {
		int numDataLines = testDataLines.size();
		for(int i=1;i<numDataLines;++i){
			cy_2006.setIntensityMeasure(cy_2006.SA_Param.NAME);
			StringTokenizer st = new StringTokenizer((String)testDataLines.get(i));
			double period = Double.parseDouble(st.nextToken().trim());
			cy_2006.getParameter(cy_2006.PeriodParam.NAME).setValue(new Double(period));
			double mag = Double.parseDouble(st.nextToken().trim());
			cy_2006.getParameter(cy_2006.MAG_NAME).setValue(new Double(mag));
			double rrup = Double.parseDouble(st.nextToken().trim());
			cy_2006.getParameter(DistanceRupParameter.NAME).setValue(new Double(rrup));
			double vs30 = Double.parseDouble(st.nextToken().trim());
			cy_2006.getParameter(cy_2006.VS30_NAME).setValue(new Double(vs30));
			double rjb = Double.parseDouble(st.nextToken().trim());
			double distRupMinusJB_OverRup = (rrup-rjb)/rrup;
			cy_2006.getParameter(DistRupMinusJB_OverRupParameter.NAME).setValue(new Double(distRupMinusJB_OverRup));
			double rupWidth =  Double.parseDouble(st.nextToken().trim());
			cy_2006.getParameter(cy_2006.RUP_WIDTH_NAME).setValue(new Double(rupWidth));
			int frv =  Integer.parseInt(st.nextToken().trim());
			int fnm = Integer.parseInt(st.nextToken().trim());
			cy_2006.getParameter(cy_2006.FLT_TYPE_NAME).setValue(cy_2006.FLT_TYPE_STRIKE_SLIP);
			if(frv ==1 && fnm==0)
			   cy_2006.getParameter(cy_2006.FLT_TYPE_NAME).setValue(cy_2006.FLT_TYPE_REVERSE);
			else if(frv ==0 && fnm ==1)
			   cy_2006.getParameter(cy_2006.FLT_TYPE_NAME).setValue(cy_2006.FLT_TYPE_NORMAL);

			double depthTop =  Double.parseDouble(st.nextToken().trim());
			cy_2006.getParameter(cy_2006.RUP_TOP_NAME).setValue(new Double(depthTop));
			double dip =  Double.parseDouble(st.nextToken().trim());
			cy_2006.getParameter(cy_2006.DIP_NAME).setValue(new Double(dip));
			double meanVal = cy_2006.getMean();
			st.nextToken();
			double targetMedian = Double.parseDouble(st.nextToken().trim());
			double medianFromOpenSHA = Double.parseDouble(format.format(Math.exp(meanVal)));	
			//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
			boolean results = compareResults(medianFromOpenSHA,targetMedian);
			//if the test was failure the add it to the test cases Vecotr that stores the values for  that failed

               //If any test for the CY-2006 failed


            if(results == false){
            	 String failedResultMetadata = "Results failed for CY-2006 attenuation with the following parameter settings:"+
            	          "IMT ="+cy_2006.SA_Param.NAME+" with Period ="+period+"\nMag ="+(float)mag+" rRup = "+rrup+
            	          "  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n   rupWidth = "+rupWidth+"   Frv = "+frv+
            	          "   Fnm = "+fnm+
            	          "   depthTop = "+depthTop+"\n   dip = "+dip;
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
	@Test
	public void testGetMean() {
		File f = new File(RESULT_SET_PATH);
		File[] fileList = f.listFiles();
		for(int i=0;i<fileList.length;++i){
			String fileName = fileList[i].getName();
			if(fileName.endsWith(".txt")){
				String fltType = fileName.substring(5,7);
				if(fltType.equals("SS"))
					cy_2006.getParameter(FaultTypeParam.NAME).setValue(cy_2006.FLT_TYPE_STRIKE_SLIP);
				else if(fltType.equals("RV"))
					cy_2006.getParameter(FaultTypeParam.NAME).setValue(cy_2006.FLT_TYPE_REVERSE);
				else if(fltType.equals("NR"))
					cy_2006.getParameter(FaultTypeParam.NAME).setValue(cy_2006.FLT_TYPE_NORMAL);
				else
					continue;
				double dip = Double.parseDouble(fileName.substring(8,10));
				cy_2006.getParameter(DipParam.NAME).setValue(new Double(dip));

				double vs30 = Double.parseDouble(fileName.substring(11,fileName.indexOf("_Z")));
				cy_2006.getParameter(Vs30_Param.NAME).setValue(new Double(vs30));
				double depthTop = Double.parseDouble(fileName.substring((fileName.indexOf("Zt")+2),fileName.indexOf(".")));
				cy_2006.getParameter(RupTopDepthParam.NAME).setValue(new Double(depthTop));
				try {
					testDataLines = FileUtils.loadFile(fileList[i].getAbsolutePath());
					int numLines = testDataLines.size();
					for(int j=1;j<numLines;++j){
						String fileLine = (String)testDataLines.get(j);
						StringTokenizer st = new StringTokenizer(fileLine);
						double mag = Double.parseDouble(st.nextToken().trim());
						((WarningDoubleParameter)cy_2006.getParameter(MagParam.NAME)).setValueIgnoreWarning(new Double(mag));

						double rjb = Double.parseDouble(st.nextToken().trim());
						double rrup = Double.parseDouble(st.nextToken().trim());
						((WarningDoublePropagationEffectParameter)cy_2006.getParameter(DistanceRupParameter.NAME)).
						setValueIgnoreWarning(new Double(rrup));
						double distRupMinusJB_OverRup = (rrup-rjb)/rrup;
						((WarningDoublePropagationEffectParameter)cy_2006.getParameter(DistRupMinusJB_OverRupParameter.NAME)).
						setValueIgnoreWarning(new Double(distRupMinusJB_OverRup));
						st.nextToken().trim();//for rSeis
						cy_2006.setIntensityMeasure(PGA_Param.NAME);
						double openSHA_mean = Math.exp(cy_2006.getMean());
						double tested_mean = Double.parseDouble(st.nextToken().trim());
						boolean results = this.compareResults(openSHA_mean, tested_mean);
						if(results == false){
							String failedResultMetadata = "Results from file "+fileName+"failed for Mean calculation for " +
							"CY-2006 attenuation with the following parameter settings:"+
							"  PGA "+"\nMag ="+(float)mag+" rRup = "+(float)rrup+
							"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+" FaultType = "+fltType+
							"   depthTop = "+depthTop+"\n   dip = "+dip+"\n"+
							"Mean from OpenSHA = "+openSHA_mean+"  should be = "+tested_mean;

							//System.out.println("Test number= "+i+" failed for +"+failedResultMetadata);
							//System.out.println("OpenSHA Median = "+medianFromOpenSHA+"   Target Median = "+targetMedian);
							assertNull(failedResultMetadata,failedResultMetadata);
						}
						st.nextToken();//for PGV
						st.nextToken();//for PGD

						cy_2006.setIntensityMeasure(SA_Param.NAME);
						int num= period.length;
						for(int k=0;k<num;++k){
							cy_2006.getParameter(PeriodParam.NAME).setValue(new Double(period[k]));
							if(k == 1)
								st.nextToken();


							openSHA_mean = Math.exp(cy_2006.getMean());
							tested_mean = Double.parseDouble(st.nextToken().trim());
							results = this.compareResults(openSHA_mean, tested_mean);
							if(results == false){
								String failedResultMetadata = "Results from file "+fileName+"failed for Mean calculation for " +
								"CY-2006 attenuation with the following parameter settings:"+
								"  SA at period = "+period[k]+ "\nMag ="+(float)mag+" rRup = "+(float)rrup+
								"  vs30 = "+vs30+"  rjb = "+(float)rjb+"\n"+" FaultType = "+fltType+
								"   depthTop = "+depthTop+"\n   dip = "+dip+"\n"+
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
