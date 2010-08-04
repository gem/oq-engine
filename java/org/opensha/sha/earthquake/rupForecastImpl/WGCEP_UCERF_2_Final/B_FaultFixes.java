/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final;

import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.util.FileUtils;

/**
 * It reads the text file for B Fault fixes.
 * @author vipingupta
 *
 */
public class B_FaultFixes  implements java.io.Serializable {
	private final static String IN_FILE = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/data/B_FaultFixes.txt";
	private final static String DELIMITER=",";
	private ArrayList sectionNames;
	private ArrayList rates;
	private ArrayList mags;
	
	/**
	 * Read the B fault fixes file
	 *
	 */
	public B_FaultFixes() {
		try {
			sectionNames = new ArrayList();
			rates = new ArrayList();
			mags = new ArrayList();
			ArrayList fileLines = FileUtils.loadFile(IN_FILE);
			for(int i=0; i<fileLines.size(); ++i) {
				String line = (String)fileLines.get(i);
				if(line.startsWith("#")) continue; // skip the comment line
				StringTokenizer tokenizer = new StringTokenizer(line,DELIMITER);
				sectionNames.add(tokenizer.nextToken().trim());
				mags.add(new Double(tokenizer.nextToken().trim()));
				rates.add(new Double(tokenizer.nextToken().trim()));
			}

		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * If B-Fault exists in the Fixes list, retunr Mag else return Nan
	 * 
	 * @param bFaultName Name of B Fault for which Mag is desired
	 * @return
	 */
	public double getMag(String bFaultName) {
		int index = sectionNames.indexOf(bFaultName);
		if(index<0) return Double.NaN;
		return ((Double)mags.get(index)).doubleValue();
	}
	
	/**
	 * If B-Fault exists in the Fixes list, retunr Rate else return Nan
	 * 
	 * @param bFaultName Name of B Fault for which Rate is desired
	 * @return
	 */
	public double getRate(String bFaultName) {
		int index = sectionNames.indexOf(bFaultName);
		if(index<0) return Double.NaN;
		return ((Double)rates.get(index)).doubleValue();
	}
	
	/**
	 * Does B fault exist in list of B Fault names
	 * @param bFaultName
	 * @return
	 */
	public boolean isBFaultInList(String bFaultName) {
		int index = sectionNames.indexOf(bFaultName);
		if(index<0) return false;
		return true;
	}
}
