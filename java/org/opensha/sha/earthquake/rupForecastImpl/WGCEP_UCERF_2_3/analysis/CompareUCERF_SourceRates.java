/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.io.FileWriter;
import java.util.HashMap;
import java.util.Iterator;

import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2_TimeIndependentEpistemicList;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2;

/**
 * This class compares the sources rates from logic tree UCERF2 with source rates from 
 *  MeanUCERF2.
 *  
 *  It generates 2 text files: One for Logic Tree and other for MeanUCERF2.
 *  Each file contains the source name and the corresponding annual rate for that source.
 *  The rates for corresponding sources from 2 files can then be compared to
 *  find if there are any discrepancies.
 * 
 * 
 * @author vipingupta
 *
 */
public class CompareUCERF_SourceRates {

	public static void main(String[] args) {
		double duration = 1;
		try {
		// UCERF 2 epistemic list
		UCERF2_TimeIndependentEpistemicList erfList = new UCERF2_TimeIndependentEpistemicList();
		int numERFs = erfList.getNumERFs();
		erfList.getTimeSpan().setDuration(duration);
		HashMap<String,Double> srcRateMapping = new HashMap<String,Double>();
		for(int erfIndex=0; erfIndex<numERFs; ++erfIndex) {
			UCERF2 ucerf2 = (UCERF2) erfList.getERF(erfIndex);
			double wt = erfList.getERF_RelativeWeight(erfIndex);
			int numSources = ucerf2.getNumSources();	
			// Iterate over all sources
			for(int srcIndex=0; srcIndex<numSources; ++srcIndex) {
				ProbEqkSource source = ucerf2.getSource(srcIndex);
				int numRups = source.getNumRuptures();
				double meanAnnualRate = 0;
				// iterate over each rupture in that source
				for(int rupIndex=0; rupIndex<numRups; ++rupIndex) {
					meanAnnualRate+=source.getRupture(rupIndex).getMeanAnnualRate(duration);
				}
				String srcName = source.getName();
				if(!srcRateMapping.containsKey(srcName)) srcRateMapping.put(srcName, 0.0);
				double newRate = srcRateMapping.get(srcName)+wt*meanAnnualRate;
				srcRateMapping.put(srcName, newRate);
			}

		}
		
		FileWriter fw = new FileWriter("LogicTreeUCERF2.txt");
		Iterator<String> it = srcRateMapping.keySet().iterator();
		while(it.hasNext()) {
			String name = it.next();
			fw.write(name+"\t"+srcRateMapping.get(name)+"\n");
		}
		fw.close();
		
		// Mean UCERF 2
		MeanUCERF2 meanUCERF2 = new MeanUCERF2();
		meanUCERF2.setParameter(UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_POISSON);
		meanUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		/*
		 * IMPORTANT NOTE: You need to set the Timespan only after setting the
		 * Probability Model Parameter. If we first set the TimeSpan and then set 
		 * Probability Model, it resets the previously set Timespan.
		 */ 
		meanUCERF2.getTimeSpan().setDuration(duration);
		fw = new FileWriter("MeanUCERF2.txt");
		meanUCERF2.updateForecast();
		int numSources = meanUCERF2.getNumSources();	
		// Iterate over all sources
		for(int srcIndex=0; srcIndex<numSources; ++srcIndex) {
			ProbEqkSource source = meanUCERF2.getSource(srcIndex);
			int numRups = source.getNumRuptures();
			double meanAnnualRate = 0;
			for(int rupIndex=0; rupIndex<numRups; ++rupIndex) {
				meanAnnualRate+=source.getRupture(rupIndex).getMeanAnnualRate(duration);
			}
			fw.write(source.getName()+"\t"+meanAnnualRate+"\n");
		}
		
		fw.close();
		}catch(Exception e) { e.printStackTrace(); }
	}
	
}
