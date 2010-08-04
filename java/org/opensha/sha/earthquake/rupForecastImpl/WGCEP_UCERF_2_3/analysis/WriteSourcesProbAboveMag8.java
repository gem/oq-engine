/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2;

/**
 * Description: It write the source names and probabilities for the sources which have non-zero
 * probability above Magnitude 8
 * @author vipingupta
 *
 */
public class WriteSourcesProbAboveMag8 {
	public static void main(String [] args) {
		double duration = 30;
		double mag = 8.0;
		// UCERF 2
		MeanUCERF2 meanUCERF2 = new MeanUCERF2();
	    // include background sources as point sources
		meanUCERF2.setParameter(UCERF2.RUP_OFFSET_PARAM_NAME, new Double(10.0));
		meanUCERF2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(MeanUCERF2.PROB_MODEL_WGCEP_PREF_BLEND);
		meanUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_INCLUDE);
		meanUCERF2.setParameter(UCERF2.BACK_SEIS_RUP_NAME, UCERF2.BACK_SEIS_RUP_POINT);
		meanUCERF2.getTimeSpan().setDuration(duration);
		meanUCERF2.updateForecast();
		int numSources = meanUCERF2.getNumSources();
		for(int srcIndex=0; srcIndex<numSources; ++srcIndex) {
			ProbEqkSource probEqkSrc = meanUCERF2.getSource(srcIndex);
			double prob = probEqkSrc.computeTotalProbAbove(mag);
			if(prob>0) System.out.println(srcIndex+"\t"+probEqkSrc.getName()+"\t"+(float)prob);
		}
	}
}
