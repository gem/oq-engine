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
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.A_Faults.A_FaultSegmentedSourceGenerator;

/**
 * This class writes Ruptures probabilities and gains into an excel sheet. 
 * It loops over logic tree branches and writes prob and gains for each branch.
 * This class only writes for Segmented A-Faults case. The unsegmented branch in not computed in this case.
 * The loop over unsegmented is done in WriteTimeDepUnsegmentedProbAndGain class.
 * Currenly it loops over deformation model, Mag Area Rel, Relative A-Priori Wt, Prob Model and Aperiodicity Params
 * It makes 12 excel sheets for different Parameter combinations.
 * 
 * @author vipingupta
 *
 */
public class WriteTimeDepSegmentedProbAndGain {
	private final static String PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/analysis/files/";

	
	private final static String README_TEXT = "This Excel spreadsheet tabulates Rupture Probability, Rupture Prob for Mag�6.7, "+
		"Rupture Gain, Segment Probability, Segment Prob for M�6.7, Segment Gain, Segment Rate, and Segment Recurrence"+
		" Interval (each on a different sheet) for all Type-A fault segmented models,"+
		" and for various logic-tree branches."+
		" The exact parameter settings for each logic-tree branch are listed in the \"Parameter Settings\""+
		" sheet, where those that vary between branches are in bold typeface.  The total aggregated"+
		" rupture probability for each fault is given at the bottom of the list for each fault."+
		" The third-to-last column gives the weighted average value (over all logic tree branches, where the weights"+
		" are given on row 147 on the rupture-related sheets and row 52 on the segment-related sheets.  The last"+
		" two columns give the Min and Max, respectively, among all the logic-tree"+
		" branches. \"Gain\" is defined as the ratio of the probability to the Poisson probability.  Note" +
		" that the weighted averages for the gains are"+
		" the individual ratios averaged, which is not the same as the weight-averaged probability divided by"+
		" the weight-averaged Poisson probability (the latter is more correct). The \"Segment Rate\" and"+
		" \"Segment Recurrence Interval\" sheets give data on the long-term annual"+
		" rate of events and recurrence interval, respectively, on each segment (i.e., the Empricial model does not influence these values).";
	private ArrayList<String> paramNames;
	private ArrayList<ParamOptions> paramValues;
	private int lastParamIndex;
	private UCERF2 ucerf2;
	private HSSFSheet rupProbSheet, rupGainSheet, segProbSheet, segProbSheet67, segGainSheet, rupProbSheet67 ;
	private HSSFSheet adjustableParamsSheet, readmeSheet, segRateSheet, segRecurIntvSheet;
	private int loginTreeBranchIndex;
	
	private ArrayList<String> adjustableParamNames;
	private ArrayList<Double> segProbWtAve, segProbMin, segProbMax;
	private ArrayList<Double> segProbWtAve67, segProbMin67, segProbMax67;
	private ArrayList<Double> rupProbWtAve, rupProbMin, rupProbMax;
	private ArrayList<Double> rupProbWtAve67, rupProbMin67, rupProbMax67;
	private ArrayList<Double> segGainWtAve, segGainMin, segGainMax;
	private ArrayList<Double> rupGainWtAve, rupGainMin, rupGainMax;
	private ArrayList<Double> segRateWtAve, segRateMin, segRateMax;
	private ArrayList<Integer>  segRecurIntvMin, segRecurIntvMax;
	private ArrayList<Double> segRecurIntvWtAve;
	private HSSFCellStyle boldStyle;
	
	private static double DURATION ;
	private  static Boolean SEG_DEP_APERIODICITY ;
	private  static String PROB_MODEL_VAL;
	private String FILENAME;
	private double MAG_67=6.7;
	
	
	public WriteTimeDepSegmentedProbAndGain() {
		this(new UCERF2());
	}
	

	public WriteTimeDepSegmentedProbAndGain(UCERF2 ucerf2) {
		this.ucerf2 = ucerf2;
		fillAdjustableParams();
		// Poisson 30 yrs
		DURATION = 30;
		 FILENAME = "RupProbs_Pois_30yr.xls";
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_POISSON;
		makeExcelSheet(ucerf2);
		// Poisson 5 yrs
		DURATION = 5;
		FILENAME = "RupProbs_Pois_5yr.xls";
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_POISSON;
		makeExcelSheet(ucerf2);
		// Empirical 30 yrs
		DURATION = 30;
		FILENAME = "RupProbs_Empirical_30yr.xls";
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_EMPIRICAL;
		makeExcelSheet(ucerf2);
		// Empirical 5 yrs
		DURATION = 5;
		FILENAME = "RupProbs_Empirical_5yr.xls";
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_EMPIRICAL;
		makeExcelSheet(ucerf2);
		
		
		// BPT 30 yrs seg Depenedent Aper
		DURATION = 30;
		FILENAME = "RupProbs_BPT_30yr_SegDepAper.xls";
		SEG_DEP_APERIODICITY = new Boolean(true);
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_BPT;
		makeExcelSheet(ucerf2);
		//	BPT 5 yrs seg Depenedent Aper
		DURATION = 5;
		FILENAME = "RupProbs_BPT_5yr_SegDepAper.xls";
		SEG_DEP_APERIODICITY = new Boolean(true);
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_BPT;
		makeExcelSheet(ucerf2);
		
		// BPT 30 yrs seg Const Aper
		DURATION = 30;
		FILENAME = "RupProbs_BPT_30yr_ConstAper.xls";
		SEG_DEP_APERIODICITY = new Boolean(false);
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_BPT;
		makeExcelSheet(ucerf2);
		
		//	BPT 5 yrs seg const Aper
		DURATION = 5;
		FILENAME = "RupProbs_BPT_5yr_ConstAper.xls";
		SEG_DEP_APERIODICITY = new Boolean(false);
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_BPT;
		makeExcelSheet(ucerf2);
		
		// Prob Model
		paramNames.add(UCERF2.PROB_MODEL_PARAM_NAME);
		ParamOptions options = new ParamOptions();
		options.addValueWeight(UCERF2.PROB_MODEL_EMPIRICAL, 0.3);
		options.addValueWeight(UCERF2.PROB_MODEL_BPT, 0.7);
		paramValues.add(options);
		
		//	BPT parameter setting
		paramNames.add(UCERF2.APERIODICITY_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(0.3), 0.2);
		options.addValueWeight(new Double(0.5), 0.5);
		options.addValueWeight(new Double(0.7), 0.3);
		paramValues.add(options);
		
		DURATION = 5;
		FILENAME = "RupProbs_Emp_BPT_5yr.xls";
		SEG_DEP_APERIODICITY = new Boolean(false);
		makeExcelSheet(ucerf2);
		
		DURATION = 30;
		FILENAME = "RupProbs_Emp_BPT_30yr.xls";
		SEG_DEP_APERIODICITY = new Boolean(false);
		makeExcelSheet(ucerf2);
		
		
		paramNames.remove(UCERF2.PROB_MODEL_PARAM_NAME);
		paramValues.remove(paramValues.size()-2);
		//		BPT 30 yrs seg const Aper
		DURATION = 30;
		FILENAME = "RupProbs_BPT_30yr_ConstAperBranches.xls";
		SEG_DEP_APERIODICITY = new Boolean(false);
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_BPT;
		makeExcelSheet(ucerf2);
		
		//	BPT 5 yrs seg const Aper
		DURATION = 5;
		FILENAME = "RupProbs_BPT_5yr_ConstAperBranches.xls";
		SEG_DEP_APERIODICITY = new Boolean(false);
		PROB_MODEL_VAL = UCERF2.PROB_MODEL_BPT;
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
		segProbSheet = wb.createSheet("Segment Probability");
		segProbSheet67 = wb.createSheet("Segment Prob for Mag>6.7");
		segGainSheet = wb.createSheet("Segment Gain");
		segRateSheet = wb.createSheet("Segment Rate");
		segRecurIntvSheet = wb.createSheet("Segment Recurrence Interval");
		ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).setValue(PROB_MODEL_VAL);
		ucerf2.getTimeSpan().setDuration(DURATION); // Set duration 
		if(ucerf2.getAdjustableParameterList().containsParameter(UCERF2.SEG_DEP_APERIODICITY_PARAM_NAME))
			ucerf2.getParameter(UCERF2.SEG_DEP_APERIODICITY_PARAM_NAME).setValue(SEG_DEP_APERIODICITY);
		
		
		
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
		int rupRowIndex = 0, segRowIndex=0;
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
		segProbSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Weighted Average");
		segProbSheet.createRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue("Min");
		segProbSheet.createRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue("Max");
		segProbSheet67.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Weighted Average");
		segProbSheet67.createRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue("Min");
		segProbSheet67.createRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue("Max");
		segGainSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Weighted Average");
		segGainSheet.createRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue("Min");
		segGainSheet.createRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue("Max");
		segRateSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Weighted Average");
		segRateSheet.createRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue("Min");
		segRateSheet.createRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue("Max");
		segRecurIntvSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Weighted Average");
		segRecurIntvSheet.createRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue("Min");
		segRecurIntvSheet.createRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue("Max");
		++rupRowIndex;
		++segRowIndex;
		++rupRowIndex;
		++segRowIndex;
		
		// loop over all faults
		int totRupsIndex=0, totSegsIndex=0;
		ArrayList<A_FaultSegmentedSourceGenerator> aFaultGenerators = ucerf2.get_A_FaultSourceGenerators();
		for(int fltGenIndex=0; fltGenIndex<aFaultGenerators.size(); ++fltGenIndex, ++rupRowIndex, ++segRowIndex) {
			A_FaultSegmentedSourceGenerator sourceGen = aFaultGenerators.get(fltGenIndex);
			
			int numRups = sourceGen.getNumRupSources();
			++rupRowIndex;
			// loop over all ruptures
			for(int rupIndex=0; rupIndex<numRups; ++rupIndex, ++totRupsIndex) {
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
			++totRupsIndex;
			++rupRowIndex;
			
			
			FaultSegmentData faultSegData = sourceGen.getFaultSegmentData();
			int numSegs = faultSegData.getNumSegments();
			++segRowIndex;
			
			// loop over all segments
			for(int segIndex=0; segIndex<numSegs; ++segIndex, ++totSegsIndex) {
				segProbSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segProbWtAve.get(totSegsIndex));
				segProbSheet.getRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue(segProbMin.get(totSegsIndex));
				segProbSheet.getRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue(segProbMax.get(totSegsIndex));
				segProbSheet67.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segProbWtAve67.get(totSegsIndex));
				segProbSheet67.getRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue(segProbMin67.get(totSegsIndex));
				segProbSheet67.getRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue(segProbMax67.get(totSegsIndex));
				segGainSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segGainWtAve.get(totSegsIndex));
				segGainSheet.getRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue(segGainMin.get(totSegsIndex));
				segGainSheet.getRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue(segGainMax.get(totSegsIndex));
				segRateSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segRateWtAve.get(totSegsIndex));
				segRateSheet.getRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue(segRateMin.get(totSegsIndex));
				segRateSheet.getRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue(segRateMax.get(totSegsIndex));
				segRecurIntvSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(Math.round(segRecurIntvWtAve.get(totSegsIndex)));
				segRecurIntvSheet.getRow(segRowIndex).createCell((short)(colIndex+1)).setCellValue(segRecurIntvMin.get(totSegsIndex));
				segRecurIntvSheet.getRow(segRowIndex).createCell((short)(colIndex+2)).setCellValue(segRecurIntvMax.get(totSegsIndex));
				++segRowIndex;
			}
		}
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
		
		// Aprioti wt param
		paramNames.add(UCERF2.REL_A_PRIORI_WT_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(1e-4), 0.5);
		options.addValueWeight(new Double(1e10), 0.5);
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
			} else {
				if(i==0) newWt=weight;
				else return;
			}
			if(paramIndex==lastParamIndex) { // if it is last paramter in list, write the Rupture Rates to excel sheet
				
				
				System.out.println("Doing run:"+(this.loginTreeBranchIndex+1));
				ucerf2.getTimeSpan().setDuration(DURATION);
				ucerf2.updateForecast();
				ArrayList<A_FaultSegmentedSourceGenerator> aFaultGenerators = ucerf2.get_A_FaultSourceGenerators();
				if(this.loginTreeBranchIndex==0) {
					
					segProbWtAve = new ArrayList<Double>();
					segProbMin = new ArrayList<Double>(); 
					segProbMax = new ArrayList<Double>();
					
					segProbWtAve67 = new ArrayList<Double>();
					segProbMin67 = new ArrayList<Double>(); 
					segProbMax67 = new ArrayList<Double>();
					
					segGainWtAve = new ArrayList<Double>();
					segGainMin = new ArrayList<Double>(); 
					segGainMax = new ArrayList<Double>();
					
					segRateWtAve = new ArrayList<Double>();
					segRateMin = new ArrayList<Double>(); 
					segRateMax = new ArrayList<Double>();
					
					segRecurIntvWtAve = new ArrayList<Double>();
					segRecurIntvMin = new ArrayList<Integer>(); 
					segRecurIntvMax = new ArrayList<Integer>();
					
					rupProbWtAve = new ArrayList<Double>();
					rupProbMin = new ArrayList<Double>();
					rupProbMax = new ArrayList<Double>();
					
					rupProbWtAve67 = new ArrayList<Double>();
					rupProbMin67 = new ArrayList<Double>();
					rupProbMax67 = new ArrayList<Double>();
					
					rupGainWtAve = new ArrayList<Double>();
					rupGainMin = new ArrayList<Double>();
					rupGainMax = new ArrayList<Double>();
					
					
					int rupRowIndex = 0, segRowIndex=0;
					int colIndex = loginTreeBranchIndex;
					rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Rupture Name");
					rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Rupture Name");
					rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Rupture Name");
					segProbSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Segment Name");
					segProbSheet67.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Segment Name");
					segGainSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Segment Name");
					segRateSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Segment Name");
					segRecurIntvSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Segment Name");
					++rupRowIndex;
					++segRowIndex;
					++rupRowIndex;
					++segRowIndex;
					
					// loop over all faults
					for(int fltGenIndex=0; fltGenIndex<aFaultGenerators.size(); ++fltGenIndex, ++rupRowIndex, ++segRowIndex) {
						A_FaultSegmentedSourceGenerator sourceGen = aFaultGenerators.get(fltGenIndex);
						
						rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
						rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
						rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
						int numRups = sourceGen.getNumRupSources();
						++rupRowIndex;
						// loop over all ruptures
						for(int rupIndex=0; rupIndex<numRups; ++rupIndex) {
							rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getLongRupName(rupIndex));
							rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getLongRupName(rupIndex));
							rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getLongRupName(rupIndex));
							++rupRowIndex;
							rupProbWtAve.add(0.0);
							rupProbWtAve.add(0.0);
							rupProbMin.add(Double.MAX_VALUE);
							rupProbMax.add(0.0);
							
							rupProbWtAve67.add(0.0);
							rupProbWtAve67.add(0.0);
							rupProbMin67.add(Double.MAX_VALUE);
							rupProbMax67.add(0.0);
							
							rupGainWtAve.add(0.0);
							rupGainWtAve.add(0.0);
							rupGainMin.add(Double.MAX_VALUE);
							rupGainMax.add(0.0);
						}
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
						
						segProbSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
						segProbSheet67.createRow(segRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
						segGainSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
						segRateSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
						segRecurIntvSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(sourceGen.getFaultSegmentData().getFaultName());
						FaultSegmentData faultSegData = sourceGen.getFaultSegmentData();
						int numSegs = faultSegData.getNumSegments();
						++segRowIndex;
						// loop over all segments
						for(int segIndex=0; segIndex<numSegs; ++segIndex) {
							segProbSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(faultSegData.getSegmentName(segIndex));
							segProbSheet67.createRow(segRowIndex).createCell((short)colIndex).setCellValue(faultSegData.getSegmentName(segIndex));
							segGainSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(faultSegData.getSegmentName(segIndex));
							segRateSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(faultSegData.getSegmentName(segIndex));
							segRecurIntvSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(faultSegData.getSegmentName(segIndex));
							++segRowIndex;
							
							segProbWtAve.add(0.0);
							segProbMin.add(Double.MAX_VALUE);
							segProbMax.add(0.0);
							
							segProbWtAve67.add(0.0);
							segProbMin67.add(Double.MAX_VALUE);
							segProbMax67.add(0.0);
							
							segGainWtAve.add(0.0);
							segGainMin.add(Double.MAX_VALUE);
							segGainMax.add(0.0);
							
							segRateWtAve.add(0.0);
							segRateMin.add(Double.MAX_VALUE);
							segRateMax.add(0.0);
							
							segRecurIntvWtAve.add(0.0);
							segRecurIntvMin.add(Integer.MAX_VALUE);
							segRecurIntvMax.add(0);
						}
						
					}
					rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					segProbSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					segProbSheet67.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					segGainSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					segRateSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					segRecurIntvSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch Weight");
					
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
				int rupRowIndex = 0, segRowIndex=0;
				int colIndex = loginTreeBranchIndex;
				rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				segProbSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				segProbSheet67.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				segGainSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				segRateSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				segRecurIntvSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				adjustableParamsSheet.createRow(0).createCell((short)colIndex).setCellValue("Branch "+loginTreeBranchIndex);
				
				++rupRowIndex;
				++segRowIndex;
				++rupRowIndex;
				++segRowIndex;
				
				// loop over all faults
				int totRupsIndex=0, totSegsIndex=0;
				for(int fltGenIndex=0; fltGenIndex<aFaultGenerators.size(); ++fltGenIndex, ++rupRowIndex, ++segRowIndex) {
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
//						 wt and min/max columns
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
					
					
					FaultSegmentData faultSegData = sourceGen.getFaultSegmentData();
					int numSegs = faultSegData.getNumSegments();
					++segRowIndex;
					double segProb, segProb67, segGain, segRate;
					int segRecurIntv;
					// loop over all segments
					for(int segIndex=0; segIndex<numSegs; ++segIndex, ++totSegsIndex) {
						segProb = sourceGen.getSegProb(segIndex);
	// use this if aggregate probs are desired enstead:
	//					segProb = sourceGen.computeSegProbAboveMag(5.0, segIndex);
						//	wt and min/max columns
						segProbWtAve.set(totSegsIndex, segProbWtAve.get(totSegsIndex)+newWt*segProb);
						if(segProbMin.get(totSegsIndex) > segProb) segProbMin.set(totSegsIndex, segProb);
						if(segProbMax.get(totSegsIndex) < segProb) segProbMax.set(totSegsIndex, segProb);
						segProbSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segProb);
						
						segProb67 = sourceGen.computeSegProbAboveMag(this.MAG_67, segIndex);
						//	wt and min/max columns
						segProbWtAve67.set(totSegsIndex, segProbWtAve67.get(totSegsIndex)+newWt*segProb67);
						if(segProbMin67.get(totSegsIndex) > segProb67) segProbMin67.set(totSegsIndex, segProb67);
						if(segProbMax67.get(totSegsIndex) < segProb67) segProbMax67.set(totSegsIndex, segProb67);
						segProbSheet67.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segProb67);

						segGain = sourceGen.getSegProbGain(segIndex);
						//	wt and min/max columns
						segGainWtAve.set(totSegsIndex, segGainWtAve.get(totSegsIndex)+newWt*segGain);
						if(segGainMin.get(totSegsIndex) > segGain) segGainMin.set(totSegsIndex, segGain);
						if(segGainMax.get(totSegsIndex) < segGain) segGainMax.set(totSegsIndex, segGain);
						segGainSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segGain);
						segGainSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segGain);
						
						segRate = sourceGen.getFinalSegmentRate(segIndex);
						//	wt and min/max columns
						segRateWtAve.set(totSegsIndex, segRateWtAve.get(totSegsIndex)+newWt*segRate);
						if(segRateMin.get(totSegsIndex) > segRate) segRateMin.set(totSegsIndex, segRate);
						if(segRateMax.get(totSegsIndex) < segRate) segRateMax.set(totSegsIndex, segRate);
						segRateSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segRate);
						segRateSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segRate);
						
						
						segRecurIntv = Math.round((float) (1/sourceGen.getFinalSegmentRate(segIndex)));
						//	wt and min/max columns
						segRecurIntvWtAve.set(totSegsIndex, segRecurIntvWtAve.get(totSegsIndex)+newWt*segRecurIntv);
						if(segRecurIntvMin.get(totSegsIndex) > segRecurIntv) segRecurIntvMin.set(totSegsIndex, segRecurIntv);
						if(segRecurIntvMax.get(totSegsIndex) < segRecurIntv) segRecurIntvMax.set(totSegsIndex, segRecurIntv);
						segRecurIntvSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segRecurIntv);
						segRecurIntvSheet.getRow(segRowIndex).createCell((short)colIndex).setCellValue(segRecurIntv);
						
						
						++segRowIndex;
					}
				}
				
				rupProbSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(newWt);
				rupProbSheet67.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(newWt);
				rupGainSheet.createRow(rupRowIndex).createCell((short)colIndex).setCellValue(newWt);
				segProbSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(newWt);
				segProbSheet67.createRow(segRowIndex).createCell((short)colIndex).setCellValue(newWt);
				segGainSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(newWt);
				segRateSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(newWt);
				segRecurIntvSheet.createRow(segRowIndex).createCell((short)colIndex).setCellValue(newWt);
				
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
	
	public static void main(String []args) {
		WriteTimeDepSegmentedProbAndGain rupProbWriter = new WriteTimeDepSegmentedProbAndGain();
	}
}
