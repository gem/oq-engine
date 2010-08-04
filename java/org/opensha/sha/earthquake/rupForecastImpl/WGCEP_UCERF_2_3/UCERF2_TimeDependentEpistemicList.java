/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3;

import java.util.ArrayList;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_B_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis.ParamOptions;

/**
 * It creates UCERF2 Epistemic List for Time Dependent model
 * 
 * @author vipingupta
 *
 */
public class UCERF2_TimeDependentEpistemicList extends UCERF2_TimeIndependentEpistemicList{
	/**
	 * Paramters that are adjusted in the runs
	 *
	 */
	protected void fillLogicTreeParams() {
		
		ucerf2.getParameter(UCERF2.SEG_DEP_APERIODICITY_PARAM_NAME).setValue(new Boolean(false));
		this.logicTreeParamNames = new ArrayList<String>();
		this.logicTreeParamValues = new ArrayList<ParamOptions>();
		
		// Deformation model
		logicTreeParamNames.add(UCERF2.DEFORMATION_MODEL_PARAM_NAME);
		ParamOptions options = new ParamOptions();
		options.addValueWeight("D2.1", 0.25);
		options.addValueWeight("D2.2", 0.1);
		options.addValueWeight("D2.3", 0.15);
		options.addValueWeight("D2.4", 0.25);
		options.addValueWeight("D2.5", 0.1);
		options.addValueWeight("D2.6", 0.15);
		logicTreeParamValues.add(options);
		
		// Mag Area Rel
		logicTreeParamNames.add(UCERF2.MAG_AREA_RELS_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(Ellsworth_B_WG02_MagAreaRel.NAME, 0.5);
		options.addValueWeight(HanksBakun2002_MagAreaRel.NAME, 0.5);
		logicTreeParamValues.add(options);
		
		// A-Fault solution type
		logicTreeParamNames.add(UCERF2.RUP_MODEL_TYPE_NAME);
		options = new ParamOptions();
		options.addValueWeight(UCERF2.SEGMENTED_A_FAULT_MODEL, 0.9);
		options.addValueWeight(UCERF2.UNSEGMENTED_A_FAULT_MODEL, 0.1);
		logicTreeParamValues.add(options);
		
		// Aprioti wt param
		logicTreeParamNames.add(UCERF2.REL_A_PRIORI_WT_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(1e-4), 0.5);
		options.addValueWeight(new Double(1e10), 0.5);
		logicTreeParamValues.add(options);
		
		//	Connect More B-Faults?
		logicTreeParamNames.add(UCERF2.CONNECT_B_FAULTS_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Boolean(true), 0.5);
		options.addValueWeight(new Boolean(false), 0.5);
		logicTreeParamValues.add(options);
		
		// B-Fault bValue=0
		logicTreeParamNames.add(UCERF2.B_FAULTS_B_VAL_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(0.8), 0.5);
		options.addValueWeight(new Double(0.0), 0.5);
		logicTreeParamValues.add(options);
		
		// Prob Model
		logicTreeParamNames.add(UCERF2.PROB_MODEL_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(UCERF2.PROB_MODEL_BPT, 0.7);
		options.addValueWeight(UCERF2.PROB_MODEL_EMPIRICAL, 0.3);
		
		logicTreeParamValues.add(options);
		
		//	BPT parameter setting
		logicTreeParamNames.add(UCERF2.APERIODICITY_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(0.3), 0.2);
		options.addValueWeight(new Double(0.5), 0.5);
		options.addValueWeight(new Double(0.7), 0.3);
		logicTreeParamValues.add(options);
	}
	
	public static void main(String[] args) {
		UCERF2_TimeDependentEpistemicList ucerf2EpistemicList = new UCERF2_TimeDependentEpistemicList();
		int numERFs = ucerf2EpistemicList.getNumERFs();
		System.out.println("Num Branches="+numERFs);
		for(int i=0; i<numERFs; ++i) {
			System.out.println("Weight of Branch "+i+"=\t"+ucerf2EpistemicList.getERF_RelativeWeight(i));
			//System.out.println("Parameters of Branch "+i+":");
			//System.out.println(ucerf2EpistemicList.getERF(i).getAdjustableParameterList().getParameterListMetadataString("\n"));
			
		}
		
	}
}
