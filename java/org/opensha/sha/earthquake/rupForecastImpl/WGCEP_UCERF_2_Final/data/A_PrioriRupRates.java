/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data;

import java.util.ArrayList;
import java.util.HashMap;

/**
 * This class is used to hold the segment rates and ruptures rates after reading
 * from the excel File
 * 
 * @author vipingupta
 *
 */
public class A_PrioriRupRates  implements java.io.Serializable {
	private String faultName;
	private HashMap<String, ArrayList> aPrioriRatesMap = new HashMap<String, ArrayList>();
	private ArrayList<String> modelNames = new ArrayList<String>();
	/**
	 * constructor : Accepts the segment name
	 * @param segmentName
	 */
	public A_PrioriRupRates(String faultName) {
		this.faultName = faultName;
	}
	
	/**
	 * Get the segment name
	 * 
	 * @return
	 */
	public String getFaultName() {
		return faultName;
	}
	
	/**
	 * Add the rup rate for specified model
	 */
	public void putRupRate(String modelName, double rate) { 
		ArrayList<Double> ratesList = aPrioriRatesMap.get(modelName);
		if(ratesList==null) {
			ratesList = new ArrayList<Double>();
			aPrioriRatesMap.put(modelName, ratesList);
			modelNames.add(modelName);
		}
		ratesList.add(rate);
	}
	
	/**
	 * Get a list of all supported model names (Eg. Geologic, Min, max)
	 * @return
	 */
	public ArrayList<String> getSupportedModelNames() {
		return modelNames;
	}
	
	/**
	 * Get the A priori rates for the solution type
	 * @param modelName
	 * @return
	 */
	public ArrayList<Double> getA_PrioriRates(String modelName) {
		return this.aPrioriRatesMap.get(modelName);
	}
}
