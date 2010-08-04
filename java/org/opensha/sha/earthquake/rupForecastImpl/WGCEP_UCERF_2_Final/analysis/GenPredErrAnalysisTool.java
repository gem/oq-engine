/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.analysis;

import java.io.FileWriter;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.ParameterListParameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.A_Faults.A_FaultSegmentedSourceGenerator;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.A_FaultsFetcher;

/**
 * Generate the test excel sheets
 * @author vipingupta
 *
 */
public class GenPredErrAnalysisTool {
	private UCERF2 ucerf2;
	private ParameterAPI magAreaRelParam, slipModelParam;
	private ParameterListParameter segmentedRupModelParam;
	private ParameterList adjustableParams;
	private ArrayList aFaultSourceGenerators ;
	private A_FaultsFetcher aFaultsFetcher;
	private ArrayList magAreaOptions, slipModelOptions;
	
	
	public GenPredErrAnalysisTool(UCERF2 ucerf2) {
		this.ucerf2 = ucerf2;
		adjustableParams = ucerf2.getAdjustableParameterList();
		magAreaRelParam = ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME);
		segmentedRupModelParam = (ParameterListParameter)ucerf2.getParameter(UCERF2.SEGMENTED_RUP_MODEL_TYPE_NAME);
		slipModelParam = ucerf2.getParameter(UCERF2.SLIP_MODEL_TYPE_NAME);
		aFaultsFetcher = ucerf2.getA_FaultsFetcher();
		magAreaOptions = ((StringConstraint)magAreaRelParam.getConstraint()).getAllowedStrings();
		slipModelOptions = ((StringConstraint)slipModelParam.getConstraint()).getAllowedStrings();
		
	}
	
	
	/**
	 * This writes the total prediction error for each fault looping over several parameters
	 */
	public void writeResults(String outFileName) {	
		try { 
			FileWriter fw = new FileWriter(outFileName);

			DecimalFormat formatter = new DecimalFormat("0.000E0");
			String[] models = {"Geological Insight", "Min Rate", "Max Rate"};
			for(int irup=0; irup<3;irup++) {
//			for(int irup=0; irup<1;irup++) {

				Iterator it = this.segmentedRupModelParam.getParametersIterator();
				while(it.hasNext()) { // set the specfiied rup model in each A fault
					StringParameter param = (StringParameter)it.next();
					ArrayList<String> allowedVals = param.getAllowedStrings();
					param.setValue(allowedVals.get(irup));
				}

//				for(int imag=3; imag<magAreaOptions.size();imag++) {
				for(int imag=0; imag<magAreaOptions.size();imag++) {
					//int numSlipModels = slipModelOptions.size();
					//double magRate[][] = new double[numSlipModels][2];
					for(int islip=0; islip<slipModelOptions.size();islip++) {
//					for(int islip=2; islip<3;islip++) {

						magAreaRelParam.setValue(magAreaOptions.get(imag));
						slipModelParam.setValue(slipModelOptions.get(islip));
						fw.write(magAreaRelParam.getValue()+"\t"+slipModelParam.getValue()+"\t"+models[irup]+"\n");
						System.out.println(magAreaRelParam.getValue()+"\t"+slipModelParam.getValue()+"\t"+models[irup]+"\n");
						double aPrioriWt = 0;
						this.ucerf2.setParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME,new Double(aPrioriWt));
						ucerf2.updateForecast();
						// do the 0.0 case
						aFaultSourceGenerators = ucerf2.get_A_FaultSourceGenerators();
						fw.write("\t");
						for(int i=0; i<aFaultSourceGenerators.size(); ++i) {
							A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator)aFaultSourceGenerators.get(i);
							fw.write(source.getFaultSegmentData().getFaultName()+"\t");
						}

						// do for each fault
						fw.write("\n"+aPrioriWt+"\t");
						for(int i=0; i<aFaultSourceGenerators.size(); ++i) {
							A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator)aFaultSourceGenerators.get(i);
							fw.write(formatter.format(source.getNonNormA_PrioriModelError())+"\t\t");
						}	 
						fw.write("\n");

						for(int pow=-20; pow<16;pow++) {
							aPrioriWt = Math.pow(10,pow);
							fw.write("1E"+pow+"\t");
							ucerf2.setParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME,new Double(aPrioriWt));
							ucerf2.updateForecast();
							aFaultSourceGenerators = ucerf2.get_A_FaultSourceGenerators();
							// do for each fault
							for(int i=0; i<aFaultSourceGenerators.size(); ++i) {
								A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator)aFaultSourceGenerators.get(i);
								fw.write(formatter.format(source.getNonNormA_PrioriModelError())+"\t\t");
							}	 
							fw.write("\n");
							/*System.out.println("1E"+pow+"\t"+
								formatter.format(getGeneralPredErr())+"\t"+
								formatter.format(getModSlipRateError())+"\t"+
								formatter.format(getDataER_Err())+"\t"+
								formatter.format(getNormalizedA_PrioriRateErr())+"  ("+
								formatter.format(getNonNormalizedA_PrioriRateErr())+
								")");*/
						}
					}

				}
			}
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}

	}

	
	
	
	/**
	 * This writes the stable regions looping over several parameters
	 */
	public void writeAllStableRanges(String outFileName) {	
		try { 
			FileWriter fw = new FileWriter(outFileName);
			String outPutString;

			String[] models = {"Geological Insight", "Min Rate", "Max Rate"};
			for(int irup=0; irup<3;irup++) {
//			for(int irup=0; irup<1;irup++) {
				// set a-priori model
				Iterator it = this.segmentedRupModelParam.getParametersIterator();
				while(it.hasNext()) { // set the specfiied rup model in each A fault
					StringParameter param = (StringParameter)it.next();
					ArrayList<String> allowedVals = param.getAllowedStrings();
					param.setValue(allowedVals.get(irup));
				}

				for(int imag=0; imag<magAreaOptions.size();imag++) {
					for(int islip=0; islip<slipModelOptions.size();islip++) {
						magAreaRelParam.setValue(magAreaOptions.get(imag));
						slipModelParam.setValue(slipModelOptions.get(islip));
						outPutString = magAreaRelParam.getValue()+";"+slipModelParam.getValue()+";"+models[irup]+"\t";
//						fw.write(magAreaRelParam.getValue()+";"+slipModelParam.getValue()+";"+models[irup]);
						outPutString += this.findStableRange();
						System.out.println(outPutString);
						fw.write(outPutString+"\n");
					}
				}
			}
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	
	
	
	
	/*
	 * This explores the influence of REL_A_PRIORI_WT_PARAM_NAME
	 * It identifies three integers: 1) the power at the end of the first stable region
	 * (where the a-priori model is fit exactly at powers greater than and equal to this
	 * value); 2) The powers at the beginning and ending of the second stable region
	 * (interpreted as where the "nearest to aPriori that best-fits data" region).
	 * The numbers are returned in the string in that order.
	 */
	public String findStableRange() {
		double tol = 0.00001;
		boolean deBug = false;
		boolean noChange = true;
		int pow = 10;
		int minPow = -20;
		int pow1,pow2,pow3;
		double aPrioriWt = Math.pow(10,pow);
		ucerf2.setParameter(ucerf2.REL_A_PRIORI_WT_PARAM_NAME,new Double(aPrioriWt));
		ucerf2.updateForecast();
		double lastError = ucerf2.getNonNormalizedA_PrioriRateErr();
		double newError, fractChange;
		if(deBug) System.out.println(pow+"\t"+lastError);
		while (noChange  && pow >= minPow) {
			pow -= 1;
			aPrioriWt = Math.pow(10,pow);
			ucerf2.setParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME,new Double(aPrioriWt));
			ucerf2.updateForecast();
			newError = ucerf2.getNonNormalizedA_PrioriRateErr();
			fractChange = Math.abs((lastError-newError)/lastError);
			noChange = (fractChange < tol);
			lastError = newError;
			if(deBug) System.out.println(pow+"\t"+lastError+"\t"+fractChange);
		}
		pow1 = pow+1;
		if(deBug) System.out.println("Power at end of 1st stable region = "+pow1);
		while (!noChange  && pow >= minPow) {
			pow -= 1;
			aPrioriWt = Math.pow(10,pow);
			ucerf2.setParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME,new Double(aPrioriWt));
			ucerf2.updateForecast();
			newError = ucerf2.getNonNormalizedA_PrioriRateErr();
			fractChange = Math.abs((lastError-newError)/lastError);
			noChange = (fractChange < tol);
			lastError = newError;
			if(deBug) System.out.println(pow+"\t"+lastError+"\t"+fractChange);
		}
		pow2 = pow+1;
		if(deBug) System.out.println("Power at beginning of 2nd stable region ="+pow2);
		while (noChange && pow >= minPow) {
			pow -=1;
			aPrioriWt = Math.pow(10,pow);
			ucerf2.setParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME,new Double(aPrioriWt));
			ucerf2.updateForecast();
			newError = ucerf2.getNonNormalizedA_PrioriRateErr();
			fractChange = Math.abs((lastError-newError)/lastError);
			noChange = (fractChange < tol);
			lastError = newError;
			if(deBug) System.out.println(pow+"\t"+lastError+"\t"+fractChange);
		}
		pow3=pow+1;
		if(deBug) System.out.println("Power at end of 2nd stable region ="+pow3);
		
		return new String(pow1+"\t"+pow2+"\t"+pow3);
	}
	
	
	
	
	public static void main(String args[]) {
		
		// NOTE: for speed, it's wise to comment out the non type-A faults in the updateForecast() method

		UCERF2 ucerf2 = new UCERF2();
		GenPredErrAnalysisTool analysisTool = new GenPredErrAnalysisTool(ucerf2);
		
//		System.out.println(analysisTool.findStableRange());
		analysisTool.writeResults("PredErrAnalysisResults1.txt");
		analysisTool.writeAllStableRanges("PredErrStableRangeAnalysis1.txt");
/**/
		ucerf2.setParameter(UCERF2.REL_SEG_RATE_WT_PARAM_NAME,new Double(1.0));
		analysisTool.writeAllStableRanges("PredErrStableRangeAnalysis2.txt");
		analysisTool.writeResults("PredErrAnalysisResults2.txt");

	}
	
}


