/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.StringTokenizer;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.util.FileUtils;

/**
 * This reads the UCERF 1 MFD from the text file.
 * 
 * @author vipingupta
 *
 */
public class UCERF1MfdReader {
	private final static String UCERF1_RATE_FILE = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/data/UCERF1_MFDs.txt";
	private static HashMap<String, ArbitrarilyDiscretizedFunc> incrMFD_Map = new HashMap<String, ArbitrarilyDiscretizedFunc>();
	private static HashMap<String, ArbitrarilyDiscretizedFunc> cumMFD_Map = new HashMap<String, ArbitrarilyDiscretizedFunc>();

	/**
	 * Get the Incremental MFD for UCERF 1 for the selected fault
	 * @param faultName
	 * @return
	 */
	public  static ArbitrarilyDiscretizedFunc getUCERF1IncrementalMFD(String faultName) {
		if(incrMFD_Map.containsKey(faultName)) return incrMFD_Map.get(faultName);
		try {
			ArbitrarilyDiscretizedFunc magRateFunc = new ArbitrarilyDiscretizedFunc();
			ArrayList fileLines = FileUtils.loadJarFile(UCERF1_RATE_FILE);
			int numLines = fileLines.size();
			for(int i=0; i<numLines; ++i) {
				String fileLine = (String)fileLines.get(i);
				if(fileLine.trim().equals("") || fileLine.startsWith("#")) continue;
				if(fileLine.startsWith("-") && 
						fileLine.substring(1).trim().equalsIgnoreCase(faultName)) {
					for(int j=i+1; j<numLines; ++j) {
						fileLine = (String)fileLines.get(j);
						if(fileLine.startsWith("-")) break;
						StringTokenizer tokenizer = new StringTokenizer(fileLine);
						magRateFunc.set(Double.parseDouble(tokenizer.nextToken()),
								Double.parseDouble(tokenizer.nextToken()));
					}
					incrMFD_Map.put(faultName, magRateFunc);
					break;
				} 
			}
			magRateFunc.setName(faultName +" MFD for UCERF 1.0");
			return magRateFunc;
		}catch(Exception e) {
			e.printStackTrace();
		}
		return null;
	}
	
	/**
	 * Get the Cumulative MFD for UCERF 1 for the selected fault
	 * @param faultName
	 * @return
	 */
	public  static ArbitrarilyDiscretizedFunc getUCERF1CumMFD(String faultName) {
		if(cumMFD_Map.containsKey(faultName)) return cumMFD_Map.get(faultName);
		ArbitrarilyDiscretizedFunc ucerf1Rate = getUCERF1IncrementalMFD(faultName);
		ArbitrarilyDiscretizedFunc ucerf1CumRate = new ArbitrarilyDiscretizedFunc();
		double rate=0;
		for(int i=ucerf1Rate.getNum()-1; i>=0; --i) {
			rate+=ucerf1Rate.getY(i);
			ucerf1CumRate.set(ucerf1Rate.getX(i), rate);
		}
		ucerf1CumRate.setName(faultName+ " Cumulative Rate from UCERF 1.0");
		cumMFD_Map.put(faultName, ucerf1CumRate);
		return ucerf1CumRate;
	}
}
