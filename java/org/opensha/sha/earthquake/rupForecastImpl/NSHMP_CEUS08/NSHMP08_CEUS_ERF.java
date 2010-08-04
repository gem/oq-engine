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

package org.opensha.sha.earthquake.rupForecastImpl.NSHMP_CEUS08;

import java.util.ArrayList;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;

/**
 * <p>Title: NSHMP08_CEUS_ERF</p>
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author : Edward Field
 * @Date : Aug, 2008
 * @version 1.0
 * 
 */

public class NSHMP08_CEUS_ERF extends EqkRupForecast {

	//for Debug purposes
	private static String C = new String("NSHMP08_CEUS_ERF");
	private boolean D = false;

	// name of this ERF
	public final static String NAME = new String("USGS NSHMP (2008) CEUS ERF (unverified)");

	NSHMP_CEUS_SourceGenerator sourceGen;

	public final static String BACK_SEIS_RUP_NAME = new String ("Treat Background Seismicity As");
	public final static String BACK_SEIS_RUP_POINT = new String ("Point Sources");
	public final static String BACK_SEIS_RUP_RAND_STRIKE = new String ("One Random Strike Fault");
	public final static String BACK_SEIS_RUP_CROSSHAIR = new String ("Two perpendicular faults");
	public final static String BACK_SEIS_RUP_DEFAULT = BACK_SEIS_RUP_CROSSHAIR;
	private StringParameter backSeisRupParam;

	int backSeisSourceType;

	double duration=50;
	
	ArrayList<ProbEqkSource> charlestonSources;


	/**
	 *
	 * No argument constructor
	 */
	public NSHMP08_CEUS_ERF() {

		try {
			sourceGen = new NSHMP_CEUS_SourceGenerator();
		}catch(Exception e) {
			e.printStackTrace();
		}

		// create the timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
		timeSpan.addParameterChangeListener(this);
		timeSpan.setDuration(duration);

		// create and add adj params to list
		initAdjParams();

		// add the change listeners
		backSeisRupParam.addParameterChangeListener(this);
		
		charlestonSources = new ArrayList<ProbEqkSource>();

	}

//	make the adjustable parameters & the list
	private void initAdjParams() {

		ArrayList<String> backSeisRupStrings = new ArrayList<String>();
		backSeisRupStrings.add(BACK_SEIS_RUP_POINT);
		backSeisRupStrings.add(BACK_SEIS_RUP_RAND_STRIKE);
		backSeisRupStrings.add(BACK_SEIS_RUP_CROSSHAIR);
		backSeisRupParam = new StringParameter(BACK_SEIS_RUP_NAME, backSeisRupStrings, UCERF2.BACK_SEIS_RUP_DEFAULT);

		// add adjustable parameters to the list
		adjustableParams.addParameter(backSeisRupParam);

	}

	/**
	 * Get the number of earthquake sources
	 *
	 * @return integer
	 */
	public int getNumSources() {
		return sourceGen.getNumSources() + charlestonSources.size();
	}

	/**
	 * Get the list of all earthquake sources.
	 *
	 * @return ArrayList of Prob Earthquake sources
	 */
	public ArrayList getSourceList() {
		ArrayList sources = new ArrayList();
		for(int i=0; i<this.getNumSources(); i++)
			sources.add(this.getSource(i));
		return sources; 
	}

	/**
	 * Return the name for this class
	 *
	 * @return : return the name for this class
	 */
	public String getName() {
		return NAME;
	}

	/**
	 * update the forecast
	 **/
	public void updateForecast() {

		// make sure something has changed
		if (parameterChangeFlag) {

			String srcType = (String) backSeisRupParam.getValue();
			if(srcType.equals(BACK_SEIS_RUP_POINT))
				backSeisSourceType = 0;
			if(srcType.equals(BACK_SEIS_RUP_CROSSHAIR))
				backSeisSourceType = 1;
			else // Random Strike
				backSeisSourceType = 2;

			duration = timeSpan.getDuration();

			parameterChangeFlag = false;
		}
		
		charlestonSources = this.sourceGen.getCharlestonSourceList(duration, backSeisSourceType);

	}
	
	/**
	 * Returns the  ith earthquake source
	 *
	 * @param iSource : index of the source needed
	 */
	public ProbEqkSource getSource(int iSource) {
		
		if(iSource<sourceGen.getNumSources())  {// everything but Charleston sources
			if(backSeisSourceType == 0)
				return sourceGen.getPointGriddedSource(iSource, duration);
			else if (this.backSeisSourceType == 1)
				return sourceGen.getCrosshairGriddedSource(iSource, duration);
			else
				return sourceGen.getRandomStrikeGriddedSource(iSource, duration);			
		}
		else 
			return this.charlestonSources.get(iSource - sourceGen.getNumSources());				
	}


	// this is temporary for testing purposes
	public static void main(String[] args) {
		
		NSHMP08_CEUS_ERF erf = new NSHMP08_CEUS_ERF();
		erf.updateForecast();
		System.out.println(erf.getNumSources());
		/*
		System.out.println("Starting loop over sources");
		int check = 1000;
		for(int i=0; i<erf.getNumSources();i++) {
			if(i == check) {
				System.out.println(check+" done");
				check += 1000;
			}
			erf.getSource(i);
		}
		System.out.println("Done with loop over sources");
		*/
		

	}

}
