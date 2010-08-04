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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.Iterator;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFCellStyle;
import org.apache.poi.hssf.usermodel.HSSFFont;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_B_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UnsegmentedSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.A_Faults.A_FaultSegmentedSourceGenerator;

/**
 * This class writes Ruptures probabilities and gains into an excel sheet.
 * Its differs from WriteTimeDepSegmentedProbAndGain because this class includes a loop on Rup Model type. 
 * It loops over logic tree branches and writes prob and gains for each branch.
 * Currenly it loops over deformation model, Mag Area Rel, Rup Model, Relative A-Priori Wt, Prob Model and Aperiodicity Params
 * It makes 6 excel sheets for different Parameter combinations.
 * 
 * @author vipingupta
 *
 */
public class WriteTimeDepUnsegmentedProbAndGain {
	private final static String PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/analysis/files/";
	
	private final static String README_TEXT = "This Excel spreadsheet tabulates Rupture Probability, Rupture Prob for Mag�6.7, "+
		" andRupture Gain (each on a different sheet) for all Type-A fault (including unsegmented models, which is why segment "+
		" rates are not listed) and for various logic-tree branches."+
		" The exact parameter settings for each logic-tree branch are listed in the \"Parameter Settings\""+
		" sheet, where those that vary between branches are in bold typeface.  The total aggregated"+
		" rupture probability for each fault is given at the bottom of the list for each fault."+
		" The third-to-last column gives the weighted average value (over all logic tree branches), where the weights"+
		" are given on row 154 on the rupture-related sheets (or row 31 if only unsegmented branches are used).  The last"+
		" two columns give the Min and Max, respectively, among all the logic-tree"+
		" branches. \"Gain\" is defined as the ratio of the probability to the Poisson probability.  Note" +
		" that the weighted averages for the gains are"+
		" the individual ratios averaged, which is not the same as the weight-averaged probability divided by"+
		" the weight-averaged Poisson probability (the latter is more correct).";
	private ArrayList<String> paramNames;
	private ArrayList<ParamOptions> paramValues;
	private int lastParamIndex;
	private UCERF2 ucerf2;
	private HSSFSheet rupProbSheet, rupGainSheet, rupProbSheet67 ;
	private HSSFSheet adjustableParamsSheet, readmeSheet;
	private int loginTreeBranchIndex;
	
	private ArrayList<String> adjustableParamNames;
	private ArrayList<Double> rupProbWtAve, rupProbMin, rupProbMax;
	private ArrayList<Double> rupProbWtAve67, rupProbMin67, rupProbMax67;
	private ArrayList<Double> rupGainWtAve, rupGainMin, rupGainMax;
	private ArrayList<Integer> unsegRowIndex, unsegWtAvgListIndex;
	private HSSFCellStyle boldStyle;
	
	private static double DURATION ;
	private  static String PROB_MODEL_VAL;
	private String FILENAME;
	private double MAG_67=6.7;
	private String fltNames[];
	
	
	public WriteTimeDepUnsegmentedProbAndGain() {
		this(new UCERF2());
	}
	

	public WriteTimeDepUnsegmentedProbAndGain(UCERF2 ucerf2) {
		this.ucerf2 = ucerf2;
		fillAdjustableParams();
		PROB_MODEL_VAL =  UCERF2.PROB_MODEL_POISSON;
		ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).setValue(UCERF2.UNSEGMENTED_A_FAULT_MODEL);
		// Poisson 30 yrs
		DURATION = 30;
		FILENAME = "UnsegmentedRupProbs_Pois_30yr.xls";
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_POISSON;
		makeExcelSheet(ucerf2);
		
		// Poisson 5 yrs
		DURATION = 5;
		FILENAME = "UnsegmentedRupProbs_Pois_5yr.xls";
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_POISSON;
		makeExcelSheet(ucerf2);
		
		// Empirical 30 yrs
		DURATION = 30;
		FILENAME = "UnsegmentedRupProbs_Empirical_30yr.xls";
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_EMPIRICAL;
		makeExcelSheet(ucerf2);
		
		// Empirical 5 yrs
		DURATION = 5;
		FILENAME = "UnsegmentedRupProbs_Empirical_5yr.xls";
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_EMPIRICAL;
		makeExcelSheet(ucerf2);
		
		
//		A-Fault solution type
		paramNames.add(UCERF2.RUP_MODEL_TYPE_NAME);
		ParamOptions options = new ParamOptions();
		options.addValueWeight(UCERF2.SEGMENTED_A_FAULT_MODEL, 0.9);
		options.addValueWeight(UCERF2.UNSEGMENTED_A_FAULT_MODEL, 0.1);
		paramValues.add(options);
		
		// Aprioti wt param
		paramNames.add(UCERF2.REL_A_PRIORI_WT_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(1e-4), 0.5);
		options.addValueWeight(new Double(1e10), 0.5);
		paramValues.add(options);
		
		// Prob Model
		paramNames.add(UCERF2.PROB_MODEL_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(UCERF2.PROB_MODEL_EMPIRICAL, 0.3);
		options.addValueWeight(UCERF2.PROB_MODEL_BPT, 0.7);
		paramValues.add(options);
		
		// Aperiodicity
		paramNames.add(UCERF2.APERIODICITY_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(0.3), 0.2);
		options.addValueWeight(new Double(0.5), 0.5);
		options.addValueWeight(new Double(0.7), 0.3);
		paramValues.add(options);
		
		PROB_MODEL_VAL= UCERF2.PROB_MODEL_BPT;
		DURATION = 5;
		FILENAME = "RupProbs_AllFinalModels_5yr.xls";
		makeExcelSheet(ucerf2);
		
		PROB_MODEL_VAL= UCERF2.PROB_MODEL_BPT;
		DURATION = 30;
		FILENAME = "RupProbs_AllFinalModels_30yr.xls";
		makeExcelSheet(ucerf2);
	}


	private void makeExcelSheet(UCERF2 ucerf2) {
		System.out.println(this.FILENAME);
		loginTreeBranchIndex = 0;
		lastParamIndex = paramNames.size()-1;
		HSSFWorkbook wb  = new HSSFWorkbook();
		readmeSheet = wb.createSheet("README");
		adjustableParamsSheet = wb.createSheet("Parameter Settings");
		rupProbSheet = wb.createSheet("Rupture Probability");
		rupProbSheet67 = wb.createSheet("Rup Prob for Mag>6.7");
		rupGainSheet = wb.createSheet("Rupture Gain");
		ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(PROB_MODEL_VAL);
		ucerf2.getTimeSpan().setDuration(DURATION); // Set duration 		
		
		// Save names of all adjustable parameters
		ParameterList adjustableParams = ucerf2.getAdjustableParameterList();
		Iterator it = adjustableParams.getParametersIterator();
		adjustableParamNames = new ArrayList<String>();
		while(it.hasNext()) {
			 ParameterAPI param = (ParameterAPI)it.next();
			 adjustableParamNames.add(param.getName());
		 }
		
		
		// add timespan parameters
		it = ucerf2.getTimeSpan().getAdjustableParams().getParametersIterator();
		while(it.hasNext()) {
			 ParameterAPI param = (ParameterAPI)it.next();
			 adjustableParamNames.add(param.getName());
		 }
		
		// create bold font style
		HSSFFont boldFont = wb.createFont();
		boldFont.setBoldweight(HSSFFont.BOLDWEIGHT_BOLD);
		boldStyle = wb.createCellStyle();
		boldStyle.setFont(boldFont);
		
		calcLogicTreeBranch(0, 1);
		
		// write weight averaged/min/max columns
		writeWeightAvMinMaxCols();
		
		// write README
		readmeSheet.setColumnWidth((short)0,(short) (51200)); // 256 * number of desired characters
		HSSFCellStyle wrapCellStyle = wb.createCellStyle();
		wrapCellStyle.setWrapText(true);
		readmeSheet.createRow(0).createCell((short)0).setCellStyle(wrapCellStyle);
		readmeSheet.getRow(0).getCell((short)0).setCellValue(README_TEXT);
		
		
		// write  excel sheet
		try {
			FileOutputStream fileOut = new FileOutputStream(PATH+FILENAME);
			wb.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	
	
	/**
	 * Write Weight averaged and min/max columns
	 *
	 */
	private void writeWeightAvMinMaxCols() {
		int rupRowIndex = 0;
		int colIndex = loginTreeBranchIndex+1;
		
		rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Weighted Average");
		rupProbSheet.createRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue("Min");
		rupProbSheet.createRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue("Max");
		rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Weighted Average");
		rupProbSheet67.createRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue("Min");
		rupProbSheet67.createRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue("Max");
		rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Weighted Average");
		rupGainSheet.createRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue("Min");
		rupGainSheet.createRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue("Max");
		
		++rupRowIndex;
		++rupRowIndex;
		
		// loop over all faults
		int totRupsIndex=0;
		boolean onlyUnsegmented = true;
		
		if(this.paramNames.contains(UCERF2.RUP_MODEL_TYPE_NAME)) {
			onlyUnsegmented = false;
		}
		
		
		ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).setValue(UCERF2.SEGMENTED_A_FAULT_MODEL);
		ucerf2.updateForecast();
		ArrayList<A_FaultSegmentedSourceGenerator> aFaultGenerators = ucerf2.get_A_FaultSourceGenerators();
		for(int fltGenIndex=0; fltGenIndex<aFaultGenerators.size(); ++fltGenIndex, ++rupRowIndex) {
			A_FaultSegmentedSourceGenerator sourceGen = aFaultGenerators.get(fltGenIndex);
			
			int numRups = sourceGen.getNumRupSources();
			if(onlyUnsegmented) numRups= 0;
			++rupRowIndex;
			// loop over all ruptures
			for(int rupIndex=0; rupIndex<numRups; ++rupIndex, ++totRupsIndex) {
				//System.out.println("33333:"+sourceGen.getFaultSegmentData().getFaultName()+"="+rupRowIndex);
				rupProbSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProbWtAve.get(totRupsIndex));
				rupProbSheet.getRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue(rupProbMin.get(totRupsIndex));
				rupProbSheet.getRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue(rupProbMax.get(totRupsIndex));
				rupProbSheet67.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProbWtAve67.get(totRupsIndex));
				rupProbSheet67.getRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue(rupProbMin67.get(totRupsIndex));
				rupProbSheet67.getRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue(rupProbMax67.get(totRupsIndex));
				rupGainSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupGainWtAve.get(totRupsIndex));
				rupGainSheet.getRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue(rupGainMin.get(totRupsIndex));
				rupGainSheet.getRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue(rupGainMax.get(totRupsIndex));
				++rupRowIndex;
			}
			rupProbSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProbWtAve.get(totRupsIndex));
			rupProbSheet.getRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue(rupProbMin.get(totRupsIndex));
			rupProbSheet.getRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue(rupProbMax.get(totRupsIndex));
			rupProbSheet67.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProbWtAve67.get(totRupsIndex));
			rupProbSheet67.getRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue(rupProbMin67.get(totRupsIndex));
			rupProbSheet67.getRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue(rupProbMax67.get(totRupsIndex));
			rupGainSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupGainWtAve.get(totRupsIndex));
			rupGainSheet.getRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue(rupGainMin.get(totRupsIndex));
			rupGainSheet.getRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue(rupGainMax.get(totRupsIndex));
			++rupRowIndex;
			++totRupsIndex;
			rupProbSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProbWtAve.get(totRupsIndex));
			rupProbSheet.getRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue(rupProbMin.get(totRupsIndex));
			rupProbSheet.getRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue(rupProbMax.get(totRupsIndex));
			rupProbSheet67.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProbWtAve67.get(totRupsIndex));
			rupProbSheet67.getRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue(rupProbMin67.get(totRupsIndex));
			rupProbSheet67.getRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue(rupProbMax67.get(totRupsIndex));
			rupGainSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupGainWtAve.get(totRupsIndex));
			rupGainSheet.getRow(rupRowIndex).createCell((short)(colIndex+1)).setCellValue(rupGainMin.get(totRupsIndex));
			rupGainSheet.getRow(rupRowIndex).createCell((short)(colIndex+2)).setCellValue(rupGainMax.get(totRupsIndex));
			++totRupsIndex;
			++rupRowIndex;
		}
		if(onlyUnsegmented) ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).setValue(UCERF2.UNSEGMENTED_A_FAULT_MODEL);
	}
	
		
	/**
	 * Paramters that are adjusted in the runs
	 *
	 */
	private void fillAdjustableParams() {
		this.paramNames = new ArrayList<String>();
		this.paramValues = new ArrayList<ParamOptions>();
		
		// Deformation model
		paramNames.add(UCERF2.DEFORMATION_MODEL_PARAM_NAME);
		ParamOptions options = new ParamOptions();
		options.addValueWeight("D2.1", 0.5);
		options.addValueWeight("D2.2", 0.2);
		options.addValueWeight("D2.3", 0.3);
		paramValues.add(options);
		
		// Mag Area Rel
		paramNames.add(UCERF2.MAG_AREA_RELS_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(Ellsworth_B_WG02_MagAreaRel.NAME, 0.5);
		options.addValueWeight(HanksBakun2002_MagAreaRel.NAME, 0.5);
		paramValues.add(options);
	}
	
	
	/**
	 * Calculate MFDs
	 * 
	 * @param paramIndex
	 * @param weight
	 */
	private void calcLogicTreeBranch(int paramIndex, double weight) {
		
		ParamOptions options = paramValues.get(paramIndex);
		String paramName = paramNames.get(paramIndex);
		int numValues = options.getNumValues();
		for(int i=0; i<numValues; ++i) {
			double newWt;
			if(ucerf2.getAdjustableParameterList().containsParameter(paramName)) {
				ucerf2.getParameter(paramName).setValue(options.getValue(i));	
				newWt = weight * options.getWeight(i);
				if(paramName.equalsIgnoreCase(UCERF2.REL_A_PRIORI_WT_PARAM_NAME)) {
					ParameterAPI param = ucerf2.getParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME);
					if(((Double)param.getValue()).doubleValue()==1e10) {
						ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_1_PARAM_NAME).setValue(new Double(0.0));
						ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_2_PARAM_NAME).setValue(new Double(0.0));	
					} else {
						ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_1_PARAM_NAME).setValue(UCERF2.MIN_A_FAULT_RATE_1_DEFAULT);
						ucerf2.getParameter(UCERF2.MIN_A_FAULT_RATE_2_PARAM_NAME).setValue(UCERF2.MIN_A_FAULT_RATE_2_DEFAULT);	
					}
				}
				
				//	change BPT to Poisson for Unsegmented case
				if(paramName.equalsIgnoreCase(UCERF2.PROB_MODEL_PARAM_NAME) &&
						ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).getValue().equals(UCERF2.UNSEGMENTED_A_FAULT_MODEL) &&
						options.getValue(i).equals(UCERF2.PROB_MODEL_BPT)	) {
					ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(UCERF2.PROB_MODEL_POISSON);
				}
				
			} else {
				if(i==0) newWt=weight;
				else return;
			}
			if(paramIndex==lastParamIndex) { // if it is last paramter in list, write the Rupture Rates to excel sheet
				
				
				System.out.println("Doing run:"+(this.loginTreeBranchIndex+1));
				ucerf2.getTimeSpan().setDuration(DURATION);
				ucerf2.updateForecast();
				ArrayList aFaultsList = ucerf2.get_A_FaultSourceGenerators();
				if(this.loginTreeBranchIndex==0) {
					
					rupProbWtAve = new ArrayList<Double>();
					rupProbMin = new ArrayList<Double>();
					rupProbMax = new ArrayList<Double>();
					
					rupProbWtAve67 = new ArrayList<Double>();
					rupProbMin67 = new ArrayList<Double>();
					rupProbMax67 = new ArrayList<Double>();
					
					rupGainWtAve = new ArrayList<Double>();
					rupGainMin = new ArrayList<Double>();
					rupGainMax = new ArrayList<Double>();
					
					unsegRowIndex = new ArrayList<Integer>();
					unsegWtAvgListIndex = new ArrayList<Integer>();
					
					
					int rupRowIndex = 0;
					int colIndex = loginTreeBranchIndex;
					rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Rupture Name");
					rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Rupture Name");
					rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Rupture Name");
					++rupRowIndex;
					++rupRowIndex;
					if(ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).getValue().equals(UCERF2.SEGMENTED_A_FAULT_MODEL))
						rupRowIndex = doFirstBranchWhenSegmented(aFaultsList, rupRowIndex, colIndex);
					else rupRowIndex = doFirstBranchWhenUnsegmented(rupRowIndex, colIndex);
						
					rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
										
					// write adjustable parameters
					// add a row for each parameter name. Also add a initial blank row for writing Branch names
					HSSFRow row = this.adjustableParamsSheet.createRow(0);
					row.createCell((short)0).setCellValue("Parameters"); 
					for(int p=1; p<=adjustableParamNames.size(); ++p) {
						String adjParamName = adjustableParamNames.get(p-1);
						HSSFCell cell = adjustableParamsSheet.createRow(p).createCell((short)0);
						if(this.paramNames.contains(adjParamName) ||
								adjParamName.equalsIgnoreCase(UCERF2.MIN_A_FAULT_RATE_1_PARAM_NAME) ||
								adjParamName.equalsIgnoreCase(UCERF2.MIN_A_FAULT_RATE_2_PARAM_NAME)) 
							cell.setCellStyle(this.boldStyle);
						cell.setCellValue(adjParamName);
					}
					
					
				}
				
				loginTreeBranchIndex++;
				int rupRowIndex = 0;
				int colIndex = loginTreeBranchIndex;
				rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				adjustableParamsSheet.createRow(0).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				
				++rupRowIndex;
		
				++rupRowIndex;
				
				if(ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).getValue().equals(UCERF2.SEGMENTED_A_FAULT_MODEL))
					rupRowIndex = doForSegmented(
						(ArrayList<A_FaultSegmentedSourceGenerator>)aFaultsList, newWt, rupRowIndex, colIndex);
				else 
					rupRowIndex = doForUnsegmented((ArrayList<UnsegmentedSource>)aFaultsList, newWt, colIndex);
				rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(newWt);
				rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(newWt);
				rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(newWt);
			
				// Write adjustable parameters
				// add a row for each parameter name. Also add a initial blank row for writing Branch names 
				ParameterList paramList = ucerf2.getAdjustableParameterList();
				ParameterList timeSpanParamList = ucerf2.getTimeSpan().getAdjustableParams();
				for(int p=1; p<=adjustableParamNames.size(); ++p) {
					String parameterName = adjustableParamNames.get(p-1);
					if(paramList.containsParameter(parameterName)) {
						HSSFCell cell = adjustableParamsSheet.getRow(p).createCell((short)loginTreeBranchIndex);
						if(this.paramNames.contains(parameterName) ||
								parameterName.equalsIgnoreCase(UCERF2.MIN_A_FAULT_RATE_1_PARAM_NAME) ||
								parameterName.equalsIgnoreCase(UCERF2.MIN_A_FAULT_RATE_2_PARAM_NAME)) 
							cell.setCellStyle(this.boldStyle);
						cell.setCellValue(paramList.getValue(parameterName).toString());
					}
					else if(timeSpanParamList.containsParameter(parameterName))
						adjustableParamsSheet.getRow(p).createCell((short)loginTreeBranchIndex).setCellValue(timeSpanParamList.getValue(parameterName).toString());
				}

			} else { // recursion 
				calcLogicTreeBranch(paramIndex+1, newWt);
			}
		}
	}


	private int doFirstBranchWhenSegmented(ArrayList aFaultsList, int rupRowIndex, int colIndex) {
		ArrayList<A_FaultSegmentedSourceGenerator> aFaultGenerators=
			(ArrayList<A_FaultSegmentedSourceGenerator>)aFaultsList;
		fltNames = new String[aFaultGenerators.size()];
		// loop over all faults
		for(int fltGenIndex=0; fltGenIndex<aFaultGenerators.size(); ++fltGenIndex, ++rupRowIndex) {
			A_FaultSegmentedSourceGenerator sourceGen = aFaultGenerators.get(fltGenIndex);
			fltNames[fltGenIndex] = sourceGen.getFaultSegmentData().getFaultName();
			rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
			rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
			rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
			int numRups = sourceGen.getNumRupSources();
			++rupRowIndex;
			// loop over all ruptures
			for(int rupIndex=0; rupIndex<numRups; ++rupIndex) {
				//System.out.println("111111: rupRowIndex="+rupRowIndex+","+sourceGen.getLongRupName(rupIndex));
				rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getLongRupName(rupIndex));
				rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getLongRupName(rupIndex));
				rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getLongRupName(rupIndex));
				
				
				rupProbWtAve.add(0.0);
				rupProbMin.add(Double.MAX_VALUE);
				rupProbMax.add(0.0);
				
				
				rupProbWtAve67.add(0.0);
				rupProbMin67.add(Double.MAX_VALUE);
				rupProbMax67.add(0.0);
				
				
				rupGainWtAve.add(0.0);
				rupGainMin.add(Double.MAX_VALUE);
				rupGainMax.add(0.0);
				
				++rupRowIndex;
			}
			unsegRowIndex.add(rupRowIndex); // row index for unsegmented
			unsegWtAvgListIndex.add(rupProbWtAve.size());
			//System.out.println("111111: rupRowIndex="+rupRowIndex+",Unsegmented");
			rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Unsegmented");
			rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Unsegmented");
			rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Unsegmented");
			
			rupProbWtAve.add(0.0);
			rupProbMin.add(Double.MAX_VALUE);
			rupProbMax.add(0.0);
			
			rupProbWtAve67.add(0.0);
			rupProbMin67.add(Double.MAX_VALUE);
			rupProbMax67.add(0.0);
			
			rupGainWtAve.add(0.0);
			rupGainMin.add(Double.MAX_VALUE);
			rupGainMax.add(0.0);
			++rupRowIndex;
			//System.out.println("111111: rupRowIndex="+rupRowIndex+",WtAve");
			rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Total Probability");
			rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Total Probability");
			rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Total Gain");
			
			rupProbWtAve.add(0.0);
			rupProbMin.add(Double.MAX_VALUE);
			rupProbMax.add(0.0);
			
			rupProbWtAve67.add(0.0);
			rupProbMin67.add(Double.MAX_VALUE);
			rupProbMax67.add(0.0);
			
			rupGainWtAve.add(0.0);
			rupGainMin.add(Double.MAX_VALUE);
			rupGainMax.add(0.0);
			
			++rupRowIndex;
			
		}
		return rupRowIndex;
	}
	
	
	private int doFirstBranchWhenUnsegmented(int rupRowIndex, int colIndex) {
	
				
		 String []aFaultNames = { "Elsinore", "Garlock", "San Jacinto", "N. San Andreas", "S. San Andreas",
				"Hayward-Rodgers Creek", "Calaveras"};
		 
		fltNames = aFaultNames;
		// loop over all faults
		for(int fltGenIndex=0; fltGenIndex<fltNames.length; ++fltGenIndex, ++rupRowIndex) {
		
			rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(fltNames[fltGenIndex]);
			rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(fltNames[fltGenIndex]);
			rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(fltNames[fltGenIndex]);
			
			++rupRowIndex;
			
			unsegRowIndex.add(rupRowIndex); // row index for unsegmented
			unsegWtAvgListIndex.add(rupProbWtAve.size());
			//System.out.println("111111: rupRowIndex="+rupRowIndex+",Unsegmented");
			rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Unsegmented");
			rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Unsegmented");
			rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Unsegmented");
			
			rupProbWtAve.add(0.0);
			rupProbMin.add(Double.MAX_VALUE);
			rupProbMax.add(0.0);
			
			rupProbWtAve67.add(0.0);
			rupProbMin67.add(Double.MAX_VALUE);
			rupProbMax67.add(0.0);
			
			rupGainWtAve.add(0.0);
			rupGainMin.add(Double.MAX_VALUE);
			rupGainMax.add(0.0);
			++rupRowIndex;
			//System.out.println("111111: rupRowIndex="+rupRowIndex+",WtAve");
			rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Total Probability");
			rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Total Probability");
			rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Total Gain");
			
			rupProbWtAve.add(0.0);
			rupProbMin.add(Double.MAX_VALUE);
			rupProbMax.add(0.0);
			
			rupProbWtAve67.add(0.0);
			rupProbMin67.add(Double.MAX_VALUE);
			rupProbMax67.add(0.0);
			
			rupGainWtAve.add(0.0);
			rupGainMin.add(Double.MAX_VALUE);
			rupGainMax.add(0.0);
			
			++rupRowIndex;
			
		}
		return rupRowIndex;
	}



	private int doForSegmented(ArrayList<A_FaultSegmentedSourceGenerator> aFaultGenerators, double newWt, int rupRowIndex, int colIndex) {
		// loop over all faults
		int totRupsIndex=0;
		for(int fltGenIndex=0; fltGenIndex<aFaultGenerators.size(); ++fltGenIndex, ++rupRowIndex) {
			A_FaultSegmentedSourceGenerator sourceGen = aFaultGenerators.get(fltGenIndex);

			int numRups = sourceGen.getNumRupSources();
			++rupRowIndex;
			// loop over all ruptures
			double rupProb, rupGain, rupProb67;
			for(int rupIndex=0; rupIndex<numRups; ++rupIndex, ++totRupsIndex) {
				rupProb = sourceGen.getRupSourceProb(rupIndex);

				// wt and min/max columns
				rupProbWtAve.set(totRupsIndex, rupProbWtAve.get(totRupsIndex)+newWt*rupProb);
				if(rupProbMin.get(totRupsIndex) > rupProb) rupProbMin.set(totRupsIndex, rupProb);
				if(rupProbMax.get(totRupsIndex) < rupProb) rupProbMax.set(totRupsIndex, rupProb);
				rupProbSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProb);

				rupProb67 = sourceGen.getRupSourceProbAboveMag(rupIndex, MAG_67);
//				wt and min/max columns
				rupProbWtAve67.set(totRupsIndex, rupProbWtAve67.get(totRupsIndex)+newWt*rupProb67);
				if(rupProbMin67.get(totRupsIndex) > rupProb67) rupProbMin67.set(totRupsIndex, rupProb67);
				if(rupProbMax67.get(totRupsIndex) < rupProb67) rupProbMax67.set(totRupsIndex, rupProb67);
				rupProbSheet67.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProb67);

				rupGain = sourceGen.getRupSourcProbGain(rupIndex);
				rupGainWtAve.set(totRupsIndex, rupGainWtAve.get(totRupsIndex)+newWt*rupGain);
				if(rupGainMin.get(totRupsIndex) > rupGain) rupGainMin.set(totRupsIndex, rupGain);
				if(rupGainMax.get(totRupsIndex) < rupGain) rupGainMax.set(totRupsIndex, rupGain);
				rupGainSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupGain);

				++rupRowIndex;
			}

			++totRupsIndex; // skip the unsegmented 
			++rupRowIndex;
			rupProb = sourceGen.getTotFaultProb();
			// wt and min/max columns
			rupProbWtAve.set(totRupsIndex, rupProbWtAve.get(totRupsIndex)+newWt*rupProb);
			if(rupProbMin.get(totRupsIndex) > rupProb) rupProbMin.set(totRupsIndex, rupProb);
			if(rupProbMax.get(totRupsIndex) < rupProb) rupProbMax.set(totRupsIndex, rupProb);
			rupProbSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProb);

			rupProb67 = sourceGen.getTotFaultProb(MAG_67);
			// wt and min/max columns
			rupProbWtAve67.set(totRupsIndex, rupProbWtAve67.get(totRupsIndex)+newWt*rupProb67);
			if(rupProbMin67.get(totRupsIndex) > rupProb67) rupProbMin67.set(totRupsIndex, rupProb67);
			if(rupProbMax67.get(totRupsIndex) < rupProb67) rupProbMax67.set(totRupsIndex, rupProb67);
			rupProbSheet67.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProb67);

			rupGain = sourceGen.getTotFaultProbGain();
			rupGainWtAve.set(totRupsIndex, rupGainWtAve.get(totRupsIndex)+newWt*rupGain);
			if(rupGainMin.get(totRupsIndex) > rupGain) rupGainMin.set(totRupsIndex, rupGain);
			if(rupGainMax.get(totRupsIndex) < rupGain) rupGainMax.set(totRupsIndex, rupGain);
			rupGainSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupGain);

			++totRupsIndex;
			++rupRowIndex;


		}
		return rupRowIndex;
	}
	
	private int doForUnsegmented(ArrayList<UnsegmentedSource> unsegmentedSourceList, double newWt, int colIndex) {
		// loop over all faults
		int rupRowIndex=0;
		for(int fltGenIndex=0; fltGenIndex<fltNames.length; ++fltGenIndex) {
			
			rupRowIndex= this.unsegRowIndex.get(fltGenIndex);
			int wtAveIndex = unsegWtAvgListIndex.get(fltGenIndex);
			// loop over all ruptures
			double rupProb, rupGain, rupProb67;
			
			// wt and min/max columns
			if(fltNames[fltGenIndex].equals("San Jacinto")) {
				UnsegmentedSource unsegmentedSource1 = getUnsegmentedSource("San Jacinto (SB to C)", unsegmentedSourceList);
				UnsegmentedSource unsegmentedSource2 = getUnsegmentedSource("San Jacinto (CC to SM)", unsegmentedSourceList);
				
				double rupProb1 = unsegmentedSource1.computeTotalProb();
				double rupProb2 = unsegmentedSource2.computeTotalProb();
				rupProb = 1-(1-rupProb1)*(1-rupProb2);
				
				double rupProb67_1 = unsegmentedSource1.computeTotalProbAbove(MAG_67);
				double rupProb67_2 = unsegmentedSource2.computeTotalProbAbove(MAG_67);
				rupProb67 = 1-(1-rupProb67_1)*(1-rupProb67_2);
				
				double rupGain1 = unsegmentedSource1.getSourceGain();
				double rupGain2 = unsegmentedSource2.getSourceGain();
				rupGain = rupProb/(1-(1-rupProb1/rupGain1)*(1-rupProb2/rupGain2));
			} else {
				UnsegmentedSource unsegmentedSource = getUnsegmentedSource(fltNames[fltGenIndex], unsegmentedSourceList);
				rupProb = unsegmentedSource.computeTotalProb();
				rupProb67 = unsegmentedSource.computeTotalProbAbove(this.MAG_67);
				rupGain = unsegmentedSource.getSourceGain();
			}
			rupProbWtAve.set(wtAveIndex, rupProbWtAve.get(wtAveIndex)+newWt*rupProb);
			if(rupProbMin.get(wtAveIndex) > rupProb) rupProbMin.set(wtAveIndex, rupProb);
			if(rupProbMax.get(wtAveIndex) < rupProb) rupProbMax.set(wtAveIndex, rupProb);
			rupProbSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProb);

			
			//wt and min/max columns
			
			rupProbWtAve67.set(wtAveIndex, rupProbWtAve67.get(wtAveIndex)+newWt*rupProb67);
			if(rupProbMin67.get(wtAveIndex) > rupProb67) rupProbMin67.set(wtAveIndex, rupProb67);
			if(rupProbMax67.get(wtAveIndex) < rupProb67) rupProbMax67.set(wtAveIndex, rupProb67);
			rupProbSheet67.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProb67);

			// gain
			
			rupGainWtAve.set(wtAveIndex, rupGainWtAve.get(wtAveIndex)+newWt*rupGain);
			if(rupGainMin.get(wtAveIndex) > rupGain) rupGainMin.set(wtAveIndex, rupGain);
			if(rupGainMax.get(wtAveIndex) < rupGain) rupGainMax.set(wtAveIndex, rupGain);
			rupGainSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupGain);

			++rupRowIndex;
			++wtAveIndex;
			// wt and min/max columns
			rupProbWtAve.set(wtAveIndex, rupProbWtAve.get(wtAveIndex)+newWt*rupProb);
			if(rupProbMin.get(wtAveIndex) > rupProb) rupProbMin.set(wtAveIndex, rupProb);
			if(rupProbMax.get(wtAveIndex) < rupProb) rupProbMax.set(wtAveIndex, rupProb);
			rupProbSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProb);

			
			// wt and min/max columns
			rupProbWtAve67.set(wtAveIndex, rupProbWtAve67.get(wtAveIndex)+newWt*rupProb67);
			if(rupProbMin67.get(wtAveIndex) > rupProb67) rupProbMin67.set(wtAveIndex, rupProb67);
			if(rupProbMax67.get(wtAveIndex) < rupProb67) rupProbMax67.set(wtAveIndex, rupProb67);
			rupProbSheet67.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupProb67);

			rupGainWtAve.set(wtAveIndex, rupGainWtAve.get(wtAveIndex)+newWt*rupGain);
			if(rupGainMin.get(wtAveIndex) > rupGain) rupGainMin.set(wtAveIndex, rupGain);
			if(rupGainMax.get(wtAveIndex) < rupGain) rupGainMax.set(wtAveIndex, rupGain);
			rupGainSheet.getRow(rupRowIndex).createCell((short)colIndex).setCellValue(rupGain);

		}
		return (rupRowIndex+2);
	}
	
	
	private UnsegmentedSource getUnsegmentedSource(String srcName, 
			ArrayList<UnsegmentedSource> srcList) {
		for(int i=0; i<srcList.size(); ++i) {
			if(srcList.get(i).getFaultSegmentData().getFaultName().equals(srcName))
				return srcList.get(i);
		}
		return null;
	}
	
	public static void main(String []args) {
		WriteTimeDepUnsegmentedProbAndGain rupProbWriter = new WriteTimeDepUnsegmentedProbAndGain();
	}
}
