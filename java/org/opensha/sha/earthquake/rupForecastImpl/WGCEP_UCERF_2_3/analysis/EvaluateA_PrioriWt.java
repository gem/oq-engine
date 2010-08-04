/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.text.DecimalFormat;

import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;

/**
 * This loops over various a-priori wts to see the impact in terms of prediction errors.  This was used
 * to generate the numbers cited in Appendix G of ERM 2.2.
 *
 */
public class EvaluateA_PrioriWt {
	private UCERF2 ucerf2;
	
	public EvaluateA_PrioriWt(UCERF2 ucerf2) {
		this.ucerf2 = ucerf2;
	}
	
	public EvaluateA_PrioriWt() {
		this(new UCERF2());
	}
	
	/**
	 * This loops over various a-priori wts to see the impact in terms of prediction errors.  This was used
	 * to generate the numbers cited in Appendix G of ERM 2.2.
	 *
	 */
	public void evaluateA_prioriWT() {
//		do some tests
		//erRateModel2_ERF.setParameter(REL_SEG_RATE_WT_PARAM_NAME,new Double(1.0));
		//erRateModel2_ERF.setParameter(PRESERVE_MIN_A_FAULT_RATE_PARAM_NAME,false);
		DecimalFormat formatter = new DecimalFormat("0.000E0");
		System.out.println("A_prior Wt\tTotal Gen Pred Error\tSeg Slip Rate Error\tSeg Event Rate Error\tA-Priori Rup Rate Error (non-normalized)");
		double aPrioriWt = 0;
		ucerf2.getParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME).setValue(new Double(aPrioriWt));
		ucerf2.updateForecast();
		// do the 0.0 case
		System.out.println((float)aPrioriWt+"\t"+
				formatter.format(ucerf2.getGeneralPredErr())+"\t"+
				formatter.format(ucerf2.getModSlipRateError())+"\t"+
				formatter.format(ucerf2.getDataER_Err())+"\t"+
				formatter.format(ucerf2.getNormalizedA_PrioriRateErr())+"  ("+
				formatter.format(ucerf2.getNonNormalizedA_PrioriRateErr())+
		")");
		for(int pow=-20; pow<16;pow++) {
			aPrioriWt = Math.pow(10,pow);
			ucerf2.getParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME).setValue(new Double(aPrioriWt));
			ucerf2.updateForecast();
			System.out.println("1E"+pow+"\t"+
					formatter.format(ucerf2.getGeneralPredErr())+"\t"+
					formatter.format(ucerf2.getModSlipRateError())+"\t"+
					formatter.format(ucerf2.getDataER_Err())+"\t"+
					formatter.format(ucerf2.getNormalizedA_PrioriRateErr())+"  ("+
					formatter.format(ucerf2.getNonNormalizedA_PrioriRateErr())+
			")");
		}
	}
	
	public static void main(String[] args) {
		EvaluateA_PrioriWt evalA_PrioriWt= new EvaluateA_PrioriWt();
		evalA_PrioriWt.evaluateA_prioriWT();
	}
}
