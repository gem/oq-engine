/**
 * 
 */
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
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.ParameterListParameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.A_Faults.A_FaultSegmentedSourceGenerator;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.data.A_FaultsFetcher;

/**
 * Generate the test excel sheets
 * @author vipingupta
 *
 */
public class GenerateTestExcelSheets {
	private UCERF2 ucerf2;
	private ParameterAPI magAreaRelParam, slipModelParam;
	private ParameterListParameter segmentedRupModelParam;
	private ParameterList adjustableParams;
	private ArrayList aFaultSourceGenerators ;
	private A_FaultsFetcher aFaultsFetcher;
	private ArrayList magAreaOptions, slipModelOptions;
	
	
	public GenerateTestExcelSheets() {
		this(new UCERF2());
	}
	
	public GenerateTestExcelSheets(UCERF2 ucerf2) {
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
	 * This generates some excel spreadsheet test results, where each file has results for all mag-area
	 * relationships, slip models, and solution types.
	 *
	 */
	public void mkExcelSheetTests() {

		// TEST 1 - defaults
		ucerf2.setParamDefaults();
		generateExcelSheetsForRupMagRates("Test1_A_FaultRupRates.xls");
		generateExcelSheetsForNormResSR_And_ER("Test1_A_FaultNormResids.xls");

		// TEST 2 zero moment rate taken out
		ucerf2.getParameter(UCERF2.AFTERSHOCK_FRACTION_PARAM_NAME).setValue(0.0);
		generateExcelSheetsForRupMagRates("Test2_A_FaultRupRates.xls");
		generateExcelSheetsForNormResSR_And_ER("Test2_A_FaultNormResids.xls");

		// TEST 3 (MEAN-MAG CORRECTION = +0.1)
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.MEAN_MAG_CORRECTION).setValue(0.1);
		generateExcelSheetsForRupMagRates("Test3_A_FaultRupRates.xls");
		generateExcelSheetsForNormResSR_And_ER("Test3_A_FaultNormResids.xls");

		// TEST 4 (MEAN-MAG CORRECTION = -0.1)
		ucerf2.getParameter(UCERF2.MEAN_MAG_CORRECTION).setValue(-0.1);
		generateExcelSheetsForRupMagRates("Test4_A_FaultRupRates.xls");
		generateExcelSheetsForNormResSR_And_ER("Test4_A_FaultNormResids.xls");

		// TEST 5 Deformation Model D2.2
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue("D2.2");
		generateExcelSheetsForRupMagRates("Test5_A_FaultRupRates.xls");
		generateExcelSheetsForNormResSR_And_ER("Test5_A_FaultNormResids.xls");

		// TEST 6 Deformation Model D2.3
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue("D2.3");
		generateExcelSheetsForRupMagRates("Test6_A_FaultRupRates.xls");
		generateExcelSheetsForNormResSR_And_ER("Test6_A_FaultNormResids.xls");	

		/*
		// TEST - FULL WEIGHT ON A-PRIORI
		setParamDefaults();
		relativeA_PrioriWeightParam.setValue(1e10);
		excelSheetsGen.generateExcelSheetsForRupMagRates("FullWt_A_FaultRupRates_2_3.xls");
		excelSheetsGen.generateExcelSheetsForNormResSR_And_ER("FullWt_A_FaultNormResids_2_3.xls");

  		// TEST - INTERMEDIATE WEIGHT ON A-PRIORI
		setParamDefaults();
		relativeA_PrioriWeightParam.setValue(1.0);
		excelSheetsGen.generateExcelSheetsForRupMagRates("IntWt_A_FaultRupRates_2_3.xls");
		excelSheetsGen.generateExcelSheetsForNormResSR_And_ER("IntWt_A_FaultNormResids_2_3.xls");

		// TEST - DEFAULT VALUES
		setParamDefaults();
		excelSheetsGen.generateExcelSheetsForRupMagRates("Default_A_FaultRupRates_2_3.xls");
		excelSheetsGen.generateExcelSheetsForNormResSR_And_ER("Default_A_FaultNormResids_2_3.xls");

		// TEST - Deformation Model D2.2
		setParamDefaults();
		deformationModelsParam.setValue(((DeformationModelSummary)deformationModelSummariesList.get(1)).getDeformationModelName());
		excelSheetsGen.generateExcelSheetsForRupMagRates("D2_3_A_FaultRupRates_2_3.xls");
		excelSheetsGen.generateExcelSheetsForNormResSR_And_ER("D2_3_A_FaultNormResids_2_3.xls");

		// TEST - Deformation Model D2.3
		setParamDefaults();
		deformationModelsParam.setValue(((DeformationModelSummary)deformationModelSummariesList.get(2)).getDeformationModelName());
		excelSheetsGen.generateExcelSheetsForRupMagRates("D2_3_A_FaultRupRates_2_3.xls");
		excelSheetsGen.generateExcelSheetsForNormResSR_And_ER("D2_3_A_FaultNormResids_2_3.xls");	
		 */

	}

	
	
	/**
	 * Generate Excel sheet for each fault.
	 * Each sheet will have all Rup solution Types
	 * 
	 */
	private void generateExcelSheetsForRupMagRates(String outputFileName) {		
		System.out.println(outputFileName);
		int numA_Faults = this.aFaultsFetcher.getAllFaultNames().size();	
//		 Create Excel Workbook and sheets if they do not exist already
		String[] columnHeaders = { "Rup_Name", "A-Priori Rate", "Char Mag", "Char Rate"};
		HSSFWorkbook wb  = new HSSFWorkbook();
		HSSFCellStyle cellStyle = wb.createCellStyle();
		HSSFFont font = wb.createFont();
		font.setColor(HSSFFont.COLOR_RED);
		cellStyle.setFont(font);
		//currRow = new int[aFaultSources.size()];
		{
		// METADATA SHEET
		HSSFSheet metadataSheet = wb.createSheet(); // Sheet for displaying the Total Rates
		wb.setSheetName(0, "README");
		String metadataStr = "This file contains final (post-inversion) rupture rates for the four " +
				"different magnitude-area relationships, the four slip models, " +
				"and the three solution types (min rate, max rate, and geologic insight).  " +
				"All other parameters were set as listed below.  The sheet for each fault lists" +
				" the following for each solution type: rupture name; the a-prior rate; " +
				"the characteristic magnitude and characteristic rate resulting from the " +
				"characteristic-slip model (which does not use a magnitude-area relationship); " +
				"and the rates for the other three slip models for each magnitude-area relationship" +
				" (twelve columns).  Listed at the bottom of the sheet for each fault are the " +
				"following total-rate ratios: min/geol, max/geol, and max/min " +
				"(useful for seeing the extent to which the different a-priori models " +
				"converge to the same final rates).  The \"Total Rates\" sheet lists the " +
				"total rates (summed over all faults) for each case.  The \"Gen. Pred. Err\" sheet" +
				" lists the generalized prediction errors for each case (smaller values mean " +
				"a better overall fit to the slip-rate and total segment event-rate data)." ;
		
		/*String metadataStr = "This file contains final (post-inversion) rupture rates for the four " +
		"different magnitude-area relationships, the four slip models, " +
		"and the geologic insight solution type.  " +
		"All other parameters were set as listed below.  The sheet for each fault lists" +
		" the following for each solution type: rupture name; the a-prior rate; " +
		"the characteristic magnitude and characteristic rate resulting from the " +
		"characteristic-slip model (which does not use a magnitude-area relationship); " +
		"and the rates for the other three slip models for each magnitude-area relationship" +
		" (twelve columns).  The \"Total Rates\" sheet lists the " +
		"total rates (summed over all faults) for each case.  The \"Gen. Pred. Err\" sheet" +
		" lists the generalized prediction errors for each case (smaller values mean " +
		"a better overall fit to the slip-rate and total segment event-rate data)." ;
*/
		writeMetadata(wb, cellStyle, metadataSheet, metadataStr);
		}
		
		// SHEETS FOR EACH A-FAULT
		for(int i=0; i<numA_Faults; ++i) {
			wb.createSheet();
			//currRow[i]=0;
		}
		HSSFSheet genPredErrSheet = wb.createSheet(); // Sheet for displaying the General Prediction error
		wb.setSheetName(wb.getNumberOfSheets()-1, "Gen. Pred. Err");
		HSSFSheet totalRatesSheet = wb.createSheet(); // Sheet for displaying the Total Rates
		wb.setSheetName(wb.getNumberOfSheets()-1, "Total Rates");
		int currRow[] = new int[numA_Faults];
		//for(int irup=0; irup<1;irup++) { // just do for geologic insight
		 for(int irup=0; irup<3;irup++) { // Do for min/max/geologic insight
			int rupStartRow[] = new int[numA_Faults];	
			Iterator it = this.segmentedRupModelParam.getParametersIterator();
			while(it.hasNext()) { // set the specfiied rup model in each A fault
				StringParameter param = (StringParameter)it.next();
				ArrayList<String> allowedVals = param.getAllowedStrings();
				param.setValue(allowedVals.get(irup));
			}
			
			for(int imag=0; imag<magAreaOptions.size();imag++) {
				//int numSlipModels = slipModelOptions.size();
				//double magRate[][] = new double[numSlipModels][2];
				for(int islip=0; islip<slipModelOptions.size();islip++) {
			
						magAreaRelParam.setValue(magAreaOptions.get(imag));
						
						slipModelParam.setValue(slipModelOptions.get(islip));
						this.ucerf2.updateForecast();
						aFaultSourceGenerators = ucerf2.get_A_FaultSourceGenerators();
						this.genPredErrAndTotRateSheet( genPredErrSheet, totalRatesSheet, imag, islip,irup, cellStyle);
						// Write header for each Rup Solution Types
						if(imag==0 && islip==0) {
							// do for each fault
							for(int i=0; i<aFaultSourceGenerators.size(); ++i) {
								HSSFSheet sheet = wb.getSheetAt(i+1); // first sheet is metadata sheet
								String sheetName = ((A_FaultSegmentedSourceGenerator)aFaultSourceGenerators.get(i)).getFaultSegmentData().getFaultName();
								wb.setSheetName(i+1, sheetName);
								HSSFRow row;
								generateExcelSheetHeader(cellStyle, currRow[i], irup, sheet, columnHeaders);		
								currRow[i]+=3;
								 // write Rup Names and Apriori Rates
								 A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator) aFaultSourceGenerators.get(i);
								 rupStartRow[i] = currRow[i];
								 for(int rup=0; rup<source.getNumRupSources(); ++rup) {
									 row = sheet.createRow((short)currRow[i]++);
									 row.createCell((short)0).setCellValue(source.getLongRupName(rup));
									 row.createCell((short)1).setCellValue(source.getAPrioriRupRate(rup));
								 }
								 // write totals
								 row = sheet.createRow((short)currRow[i]++);
								 int totRow1=currRow[i];
								 int totRow2 = 2*totRow1+2;
								 int totRow3 = 3*totRow1+4;
								 int ratioRowIndex1 = totRow3+2;
								 createTotalRow( row, rupStartRow[i], rupStartRow[i]+source.getNumRupSources());
								 if(irup==0){
									 this.createRatioRows(sheet, ratioRowIndex1, totRow1, totRow2, totRow3);
								 }	 
							}
						}
					
						// write the rup Mag and rates
						for(int i=0; i<this.aFaultSourceGenerators.size(); ++i) {
							 HSSFSheet sheet = wb.getSheetAt(i+1);// first sheet is metadata
							 A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator) aFaultSourceGenerators.get(i);
							 int magCol = this.getMagCol(islip, imag);
							 int rateCol = this.getRateCol(islip, imag);
							 for(int rup=0; rup<source.getNumRupSources(); ++rup) {
								 sheet.getRow(rup+rupStartRow[i]).createCell((short)magCol).setCellValue(source.getRupMeanMag(rup));
								 sheet.getRow(rup+rupStartRow[i]).createCell((short)rateCol).setCellValue(source.getRupRate(rup));
							 }
						}
					}
			}
			// 
			for(int i=1; i<(wb.getNumberOfSheets()-2); ++i) { // do not do for Gen Pred Error and Tot rates
				HSSFSheet sheet = wb.getSheetAt(i);
				sheet.createRow((short)currRow[i-1]++);
				sheet.createRow((short)currRow[i-1]++);
			}
			
		}
		try {
			FileOutputStream fileOut = new FileOutputStream(outputFileName);
			wb.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	
	/**
	 * Generate Excel sheet for each fault.
	 * Each sheet will have all Rup solution Types
	 * 
	 */
	private void generateExcelSheetsForNormResSR_And_ER(String outputFileName) {		
		System.out.println(outputFileName);
		int numA_Faults = this.aFaultsFetcher.getAllFaultNames().size();	
//		 Create Excel Workbook and sheets if they do not exist already
		String[] columnHeaders = { "Segment Name", "A-Priori Rate", "Char Mag", "Char Rate"};
		HSSFWorkbook wb  = new HSSFWorkbook();
		HSSFCellStyle cellStyle = wb.createCellStyle();
		HSSFFont font = wb.createFont();
		font.setColor(HSSFFont.COLOR_RED);
		cellStyle.setFont(font);
		//currRow = new int[aFaultSources.size()];
		{
		// METADATA SHEET
		HSSFSheet metadataSheet = wb.createSheet(); // Sheet for displaying the Total Rates
		wb.setSheetName(0, "README");
		String metadataStr = "This file contains normalized residuals for each segment and for each " +
				"combination of parameters." ;
		writeMetadata(wb, cellStyle, metadataSheet, metadataStr);
		}
		
		// SHEETS FOR EACH A-FAULT
		for(int i=0; i<numA_Faults; ++i) {
			wb.createSheet();
		}
	
		int currRow[] = new int[numA_Faults];
		//for(int irup=0; irup<1;irup++) { // do for geologic insight only
		 for(int irup=0; irup<3;irup++) { // Do for Min/Max/Geologic insight
			int segSRStartRow[] = new int[numA_Faults];	
			int segERStartRow[] = new int[numA_Faults];	
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
						this.ucerf2.updateForecast();
						aFaultSourceGenerators = ucerf2.get_A_FaultSourceGenerators();
						// Write header for each Rup Solution Types
						if(imag==0 && islip==0) {
							// do for each fault
							for(int i=0; i<aFaultSourceGenerators.size(); ++i) {
								HSSFSheet sheet = wb.getSheetAt(i+1); // first sheet is metadata sheet
								String sheetName = ((A_FaultSegmentedSourceGenerator)aFaultSourceGenerators.get(i)).getFaultSegmentData().getFaultName();
								wb.setSheetName(i+1, sheetName);
								HSSFRow row;
								 // write Segment  Names and Original rates
								 A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator) aFaultSourceGenerators.get(i);
								 FaultSegmentData faultSegmentData = source.getFaultSegmentData();

								 // for  Slip Rates
								 sheet.createRow((short)currRow[i]++).createCell((short)0).setCellValue("Normalized Residual Slip Rate");
								 generateExcelSheetHeader(cellStyle, currRow[i], irup, sheet, columnHeaders);		
								 currRow[i]+=3;
								 segSRStartRow[i] = currRow[i];
								 for(int seg=0; seg<faultSegmentData.getNumSegments(); ++seg) {
									 row = sheet.createRow((short)currRow[i]++);
									 row.createCell((short)0).setCellValue(faultSegmentData.getSegmentName(seg));
								 }
								 
								 // for  Event Rates
								 currRow[i]+=3;
								 sheet.createRow((short)currRow[i]++).createCell((short)0).setCellValue("Normalized Residual Event Rates");
								 generateExcelSheetHeader(cellStyle, currRow[i], irup, sheet, columnHeaders);		
								 currRow[i]+=3;
								 segERStartRow[i] = currRow[i];
								 for(int seg=0; seg<faultSegmentData.getNumSegments(); ++seg) {
									 row = sheet.createRow((short)currRow[i]++);
									 row.createCell((short)0).setCellValue(faultSegmentData.getSegmentName(seg));
								 }
							}
						}
					
						// write the rup Mag and rates
						for(int i=0; i<this.aFaultSourceGenerators.size(); ++i) {
							 HSSFSheet sheet = wb.getSheetAt(i+1);// first sheet is metadata
							 A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator) aFaultSourceGenerators.get(i);	
							 // normalized slip rates
							 double normModSR[] = source.getNormModSlipRateResids();
							 //	normalized event rates
							 double normModER[] = source.getNormDataER_Resids();
							 int rateCol = this.getRateCol(islip, imag);
							 for(int seg=0; seg<normModSR.length; ++seg) {
								 sheet.getRow(seg+segSRStartRow[i]).createCell((short)rateCol).setCellValue((normModSR[seg]));
								 sheet.getRow(seg+segERStartRow[i]).createCell((short)rateCol).setCellValue((normModER[seg]));
							 }
						}
					}
			}
			// 
			for(int i=1; i<(wb.getNumberOfSheets()); ++i) { // do not do for Gen Pred Error and Tot rates
				HSSFSheet sheet = wb.getSheetAt(i);
				sheet.createRow((short)currRow[i-1]++);
				sheet.createRow((short)currRow[i-1]++);
			}
			
		}
		try {
			FileOutputStream fileOut = new FileOutputStream(outputFileName);
			wb.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}


	private void writeMetadata(HSSFWorkbook wb, HSSFCellStyle cellStyle, HSSFSheet metadataSheet, String metadataStr) {
		metadataSheet.setColumnWidth((short)0,(short) (32000)); // 256 * number of desired characters
		metadataSheet.createRow(0).createCell((short)0).setCellValue(metadataStr);
		HSSFCellStyle wrapCellStyle = wb.createCellStyle();
		wrapCellStyle.setWrapText(true);
		metadataSheet.getRow(0).getCell((short)0).setCellStyle(wrapCellStyle);
		metadataSheet.createRow(2).createCell((short)0).setCellValue("Parameter Settings");
		metadataSheet.getRow(2).getCell((short)0).setCellStyle(cellStyle);
		int row = 3;
		Iterator it = this.adjustableParams.getParametersIterator();
		while(it.hasNext()) {
			ParameterAPI param = (ParameterAPI)it.next();
			if(param.getName().equals(UCERF2.MAG_AREA_RELS_PARAM_NAME) || param.getName().equals(UCERF2.SLIP_MODEL_TYPE_NAME) ||
					param.getName().equals(UCERF2.SEGMENTED_RUP_MODEL_TYPE_NAME)) continue;
			metadataSheet.createRow(row++).createCell((short)0).setCellValue(param.getMetadataString());
		}
	}


	/**
	 * Get column for Rate
	 * 
	 * @param islip
	 * @param imag
	 * @return
	 */
	private int getRateCol(int islip, int imag) {
		 if(slipModelOptions.get(islip).equals(A_FaultSegmentedSourceGenerator.CHAR_SLIP_MODEL)) 
			 return 3;
		 else 
			 return getMagCol(islip,imag)+islip;
			
	}
	
	/**
	 * Get column for Mag
	 * @param islip
	 * @param imag
	 * @return
	 */
	private int getMagCol(int islip, int imag) {
		 if(slipModelOptions.get(islip).equals(A_FaultSegmentedSourceGenerator.CHAR_SLIP_MODEL))
			 return  2; 
		 else 
			 return 4 + imag*slipModelOptions.size();
	}
	
	
	private void createRatioRows(HSSFSheet sheet, int ratioRowIndex1, int totRow1, int totRow2, int totRow3) {
		HSSFRow ratioRow1=null, ratioRow2=null, ratioRow3=null;
		ratioRow1 = sheet.createRow((short)ratioRowIndex1);
		 ratioRow2 = sheet.createRow((short)(ratioRowIndex1+1));
		 ratioRow3 = sheet.createRow((short)(ratioRowIndex1+2));				 
		 ratioRow1.createCell((short)0).setCellValue("min/geol");	
		 ratioRow2.createCell((short)0).setCellValue("max/geol");	
		 ratioRow3.createCell((short)0).setCellValue("max/min");	
		 // a priori rate ratio
		 String colStr="B";
		 HSSFCell cell = ratioRow1.createCell((short)1);
		 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
		 cell.setCellFormula(colStr+totRow2+"/"+colStr+totRow1);
		 cell = ratioRow2.createCell((short)1);
		 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
		 cell.setCellFormula(colStr+totRow3+"/"+colStr+totRow1);
		 cell = ratioRow3.createCell((short)1);
		 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
		 cell.setCellFormula(colStr+totRow3+"/"+colStr+totRow2);
		 // Char rate ratio
		 colStr="D";
		 cell = ratioRow1.createCell((short)3);
		 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
		 cell.setCellFormula(colStr+totRow2+"/"+colStr+totRow1);
		 cell = ratioRow2.createCell((short)3);
		 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
		 cell.setCellFormula(colStr+totRow3+"/"+colStr+totRow1);
		 cell = ratioRow3.createCell((short)3);
		 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
		 cell.setCellFormula(colStr+totRow3+"/"+colStr+totRow2);
		 // totals for other rates
		 for(int k=0; k<slipModelOptions.size(); ++k) {
			 if(slipModelOptions.get(k).equals(A_FaultSegmentedSourceGenerator.CHAR_SLIP_MODEL)) continue;
			 for(int j=0; j<magAreaOptions.size(); ++j) {
				 int totCol = 4 + j*slipModelOptions.size()+k;
				 colStr=""+(char)('A'+totCol);
				 cell = ratioRow1.createCell((short)totCol);
				 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
				 cell.setCellFormula(colStr+totRow2+"/"+colStr+totRow1);
				 cell = ratioRow2.createCell((short)totCol);
				 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
				 cell.setCellFormula(colStr+totRow3+"/"+colStr+totRow1);
				 cell = ratioRow3.createCell((short)totCol);
				 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
				 cell.setCellFormula(colStr+totRow3+"/"+colStr+totRow2);
			 }
		 }
	}
	
	private void createTotalRow(HSSFRow row, int sumStartIndex, int sumEndIndex) {
	

		 row.createCell((short)0).setCellValue("Totals");							 
		 // a priori rate total
		 HSSFCell cell = row.createCell((short)1);
		 String colStr="B";
		 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
		 cell.setCellFormula("SUM("+colStr+sumStartIndex+":"+colStr+(sumEndIndex+")"));
		 // Char rate total
		 cell = row.createCell((short)3);
		 colStr="D";
		 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
		 cell.setCellFormula("SUM("+colStr+sumStartIndex+":"+colStr+(sumEndIndex+")"));
		 // totals for other rates
		 for(int k=0; k<slipModelOptions.size(); ++k) {
			 if(slipModelOptions.get(k).equals(A_FaultSegmentedSourceGenerator.CHAR_SLIP_MODEL)) continue;
			 for(int j=0; j<magAreaOptions.size(); ++j) {
				 int totCol = 4 + j*slipModelOptions.size()+k;
				 cell = row.createCell((short)totCol);
				 colStr=""+(char)('A'+totCol);
				 //System.out.println(colStr);
				 cell.setCellType(HSSFCell.CELL_TYPE_FORMULA);
				 cell.setCellFormula("SUM("+colStr+sumStartIndex+":"+colStr+(sumEndIndex+")"));
			 }
		 }
		 

	}
	

	/**
	 * Create header lines - mag area names, etc
	 * @param cellStyle
	 * @param rowIndex
	 * @param irup
	 * @param sheet
	 */
	private void generateExcelSheetHeader(HSSFCellStyle cellStyle, 
			int rowIndex, int irup,  HSSFSheet sheet, String columLabels[]) {
		
		String[] models = {"Geological Insight", "Min Rate", "Max Rate"};
		
		//System.out.println(currRow[i]);
		 HSSFRow row = sheet.createRow((short)rowIndex++);
		 // Write Rup solution Type
		 HSSFCell cell = row.createCell((short)0);
		 cell.setCellValue(models[irup]);
		 cell.setCellStyle(cellStyle);
		 row = sheet.createRow((short)rowIndex++);
		 int col=4;
		 
		 // Write All Mag Areas in appropriate columns
		 for(int j=0; j<magAreaOptions.size(); ++j, col+=slipModelOptions.size()) {
			 cell = row.createCell((short)col);
			 cell.setCellValue((String)magAreaOptions.get(j));
			 cell.setCellStyle(cellStyle);
		 }
		 // write the headers
		 row = sheet.createRow((short)rowIndex++);
		 col=0;
		 cell = row.createCell((short)col++);
		 cell.setCellValue("Rup_Name");
		 cell.setCellStyle(cellStyle);
		 cell = row.createCell((short)col++);
		 cell.setCellValue("A-Priori Rate");
		 cell.setCellStyle(cellStyle);
		 cell = row.createCell((short)col++);
		 cell.setCellValue("Char Mag");
		 cell.setCellStyle(cellStyle);
		 cell = row.createCell((short)col++);
		 cell.setCellValue("Char Rate");
		 cell.setCellStyle(cellStyle);
		 for(int j=0; j<magAreaOptions.size(); ++j) {
			 cell = row.createCell((short)col++);
			 cell.setCellValue("Mag");
			 cell.setCellStyle(cellStyle);
			 for(int k=0; k<slipModelOptions.size(); ++k) {
				 String slipModel = (String)slipModelOptions.get(k);
				 if(!slipModel.equals(A_FaultSegmentedSourceGenerator.CHAR_SLIP_MODEL)) {
					 cell = row.createCell((short)col++);
					 cell.setCellValue((String)slipModelOptions.get(k));
					 cell.setCellStyle(cellStyle);
				 }
			 }
		 }
	}
	
	/**
	 * Generate the excel sheet to save the general prediction error
	 * @param sheet
	 */
	private void genPredErrAndTotRateSheet(HSSFSheet predErrSheet, HSSFSheet totRateSheet, int imag, int islip, int irup, HSSFCellStyle cellStyle) {
		String[] columnHeaders1 = { "Fault Name", "A-Priori Rate", "Char Mag", "Char Rate"};
		String[] columnHeaders2 = { "Total", "A-Priori Rate", "Char Mag", "Char Rate"};
		int numA_Faults = this.aFaultsFetcher.getAllFaultNames().size();	
		//Create Excel Workbook and sheets if they do not exist already
		double totRate=0;
		
		// Write header for each Rup Solution Types
		int currRow  = irup*(numA_Faults+6);
		int faultNamesStartRow = currRow+3;
		
		if(irup==0) { // ratios in total rate sheet	 
			int ratioRowIndex1 = 2*(numA_Faults+6)+3+3;
			int totRow1 = faultNamesStartRow+1; 
			int totRow2  = (numA_Faults+6)+3+1;
			int totRow3  = 2*(numA_Faults+6)+3+1;
			//this.createRatioRows(totRateSheet, ratioRowIndex1, totRow1, totRow2, totRow3);
		}
		
		if(imag==0 && islip==0) { // Write the headers and fault names for the first time	
			generateExcelSheetHeader(cellStyle, currRow, irup, predErrSheet, columnHeaders1);	
			generateExcelSheetHeader(cellStyle, currRow, irup, totRateSheet, columnHeaders2);	
			currRow+=3;	
			// write Source Names
			totRate=0;
			HSSFRow row1;
			for(int iSource=0; iSource<aFaultSourceGenerators.size(); ++iSource) {
				row1 = predErrSheet.createRow((short)(faultNamesStartRow+iSource));
				A_FaultSegmentedSourceGenerator src = (A_FaultSegmentedSourceGenerator)aFaultSourceGenerators.get(iSource);
				for(int rupIndex=0; rupIndex<src.getNumRupSources(); ++rupIndex) totRate+=src.getAPrioriRupRate(rupIndex);
				row1.createCell((short)0).setCellValue(src.getFaultSegmentData().getFaultName());
			}
			
			totRateSheet.createRow(faultNamesStartRow).createCell((short)0).setCellValue("Total Rate");
			// write the sum of apriori rates
			totRateSheet.getRow(faultNamesStartRow).createCell((short)1).setCellValue(totRate);
			
			currRow+=aFaultSourceGenerators.size();
			// write totals
			row1 = predErrSheet.createRow((short)currRow++);
			this.createTotalRow(row1, faultNamesStartRow, faultNamesStartRow+numA_Faults);
		}
		
		
		int col = this.getRateCol(islip, imag);				
		// write the Gen. Pred. Error
		totRate=0;
		for(int i=0; i<this.aFaultSourceGenerators.size(); ++i) {
			A_FaultSegmentedSourceGenerator source = (A_FaultSegmentedSourceGenerator) aFaultSourceGenerators.get(i);
			for(int rupIndex=0; rupIndex<source.getNumRupSources(); ++rupIndex) totRate+=source.getRupRate(rupIndex);
			predErrSheet.getRow(i+faultNamesStartRow).createCell((short)col).setCellValue(source.getGeneralizedPredictionError());
		}			
		totRateSheet.getRow(faultNamesStartRow).createCell((short)(col)).setCellValue(totRate);
	}
	
	/**
	 * Generate Excel sheet for each fault.
	 * Each sheet will have all Rup solution Types
	 * 
	 */
	/*public void generateExcelSheetForSegRecurIntv(String outputFileName) {
		ArrayList magAreaOptions = ((StringConstraint)magAreaRelParam.getConstraint()).getAllowedStrings();
		ArrayList slipModelOptions = ((StringConstraint)slipModelParam.getConstraint()).getAllowedStrings();
		int numA_Faults = this.aFaultsFetcher.getAllFaultNames().size();	
//		 Create Excel Workbook and sheets if they do not exist already
		
		HSSFWorkbook wb  = new HSSFWorkbook();
		HSSFCellStyle cellStyle = wb.createCellStyle();
		HSSFFont font = wb.createFont();
		font.setColor(HSSFFont.COLOR_RED);
		cellStyle.setFont(font);
		
		// create sheets
		for(int i=0; i<numA_Faults; ++i) {
			wb.createSheet();
		}
		int currRow[] = new int[numA_Faults];
		String[] models = {"Geological Insight", "Min Rate", "Max Rate"};
		for(int irup=0; irup<3;irup++) { // various rupture model types
			int rupStartRow[] = new int[numA_Faults];
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
						
						
						this.updateForecast();
						
						// Write header for each Rup Solution Types
						if(imag==0 && islip==0) {
							// do for each fault
							for(int i=0; i<this.aFaultSources.size(); ++i) {
								 HSSFSheet sheet = wb.getSheetAt(i);
								 String sheetName = ((A_FaultSegmentedSource)aFaultSources.get(i)).getFaultSegmentData().getFaultName();
								 wb.setSheetName(i, sheetName);
								 //System.out.println(currRow[i]);
								 HSSFRow row = sheet.createRow((short)currRow[i]++);
								 // Write Rup solution Type
								 HSSFCell cell = row.createCell((short)0);
								 cell.setCellValue(models[irup]);
								 cell.setCellStyle(cellStyle);
								 row = sheet.createRow((short)currRow[i]++);
								 int col=5;
								 
								 // Write All Mag Areas in appropriate columns
								 for(int j=0; j<magAreaOptions.size(); ++j, col+=(slipModelOptions.size()-1)) {
									 cell = row.createCell((short)col);
									 cell.setCellValue((String)magAreaOptions.get(j));
									 cell.setCellStyle(cellStyle);
								 }
								 // write the headers
								 row = sheet.createRow((short)currRow[i]++);
								 col=0;
								 cell = row.createCell((short)col++);
								 cell.setCellValue("Segment_Name");
								 cell.setCellStyle(cellStyle);
								 cell = row.createCell((short)col++);
								 cell.setCellValue("Mean Recur Intv");
								 cell.setCellStyle(cellStyle);
								 cell = row.createCell((short)col++);
								 cell.setCellValue("Min Recur Intv");
								 cell.setCellStyle(cellStyle);
								 cell = row.createCell((short)col++);
								 cell.setCellValue("Max Recur Intv");
								 cell.setCellStyle(cellStyle);
								 cell = row.createCell((short)col++);
								 cell.setCellValue("Characteristic Model Recur Intv");
								 cell.setCellStyle(cellStyle);
								 for(int j=0; j<magAreaOptions.size(); ++j) {
									 for(int k=0; k<slipModelOptions.size(); ++k) {
										 String slipModel = (String)slipModelOptions.get(k);
										 if(!slipModel.equals(A_FaultSegmentedSource.CHAR_SLIP_MODEL)) {
											 cell = row.createCell((short)col++);
											 cell.setCellValue(slipModel);
											 cell.setCellStyle(cellStyle);
										 }
									 }
								 }								 
								 // write Seg Names and mean Recur Intv
								 A_FaultSegmentedSource source = (A_FaultSegmentedSource) aFaultSources.get(i);
								 rupStartRow[i] = currRow[i];
								 								 
								 for(int seg=0; seg<source.getFaultSegmentData().getNumSegments(); ++seg) {
									 row = sheet.createRow((short)currRow[i]++);
									 row.createCell((short)0).setCellValue(source.getFaultSegmentData().getSegmentName(seg));
									 double recurIntv = source.getFaultSegmentData().getRecurInterval(seg);
									 if(Double.isNaN(recurIntv)) continue;
									 double recurIntvStdDev = source.getFaultSegmentData().getRecurIntervalSigma(seg);
									 //System.out.println(seg+","+source.getFaultSegmentData().getSegmentName(seg));
									 row.createCell((short)1).setCellValue((int)Math.round(recurIntv));
									 row.createCell((short)2).setCellValue((int)Math.round(recurIntv-2*recurIntvStdDev));
									 row.createCell((short)3).setCellValue((int)Math.round(recurIntv+2*recurIntvStdDev));

									 //row.createCell((short)1).setCellValue(source.getS(rup));
								 }
							}
						}
						   
						   
						
						// 
						for(int i=0; i<this.aFaultSources.size(); ++i) {
							 HSSFSheet sheet = wb.getSheetAt(i);
							 A_FaultSegmentedSource source = (A_FaultSegmentedSource) aFaultSources.get(i);
							 int rateCol;
							 if(slipModelOptions.get(islip).equals(A_FaultSegmentedSource.CHAR_SLIP_MODEL)) {
								 rateCol = 4;
							 } else rateCol = 4 + imag*(slipModelOptions.size()-1) + islip;
							 //rateCol = magCol + islip;
							 for(int seg=0; seg<source.getFaultSegmentData().getNumSegments(); ++seg) {
								 sheet.getRow(seg+rupStartRow[i]).createCell((short)rateCol).setCellValue((int)Math.round(source.getFinalSegRecurInt(seg)));
							 }
						}
					}
			}
			// 
			for(int i=0; i<wb.getNumberOfSheets(); ++i) {
				HSSFSheet sheet = wb.getSheetAt(i);
				sheet.createRow((short)currRow[i]++);
				sheet.createRow((short)currRow[i]++);
			}
			
		}
		try {
			FileOutputStream fileOut = new FileOutputStream(outputFileName);
			wb.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}*/
	
	
	/**
	 * Generate Excel sheet for each fault.
	 * Each sheet will have all Rup solution Types
	 * 
	 */
	/*public void generateExcelSheetForSegSlipRate(String outputFileName) {
		ArrayList magAreaOptions = ((StringConstraint)magAreaRelParam.getConstraint()).getAllowedStrings();
		ArrayList slipModelOptions = ((StringConstraint)slipModelParam.getConstraint()).getAllowedStrings();
		int numA_Faults = this.aFaultsFetcher.getAllFaultNames().size();	
//		 Create Excel Workbook and sheets if they do not exist already
		
		HSSFWorkbook wb  = new HSSFWorkbook();
		HSSFCellStyle cellStyle = wb.createCellStyle();
		HSSFFont font = wb.createFont();
		font.setColor(HSSFFont.COLOR_RED);
		cellStyle.setFont(font);
		
		// create sheets
		for(int i=0; i<numA_Faults; ++i) {
			wb.createSheet();
		}
		String[] models = {"Geological Insight", "Min Rate", "Max Rate"};
		int currRow[] = new int[numA_Faults];
		for(int irup=0; irup<3;irup++) {
			int rupStartRow[] = new int[numA_Faults];
			
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
						this.updateForecast();
						
						// Write header for each Rup Solution Types
						if(imag==0 && islip==0) {
							// do for each fault
							for(int i=0; i<this.aFaultSources.size(); ++i) {
								 HSSFSheet sheet = wb.getSheetAt(i);
								 String sheetName = ((A_FaultSegmentedSource)aFaultSources.get(i)).getFaultSegmentData().getFaultName();
								 wb.setSheetName(i, sheetName);
								 //System.out.println(currRow[i]);
								 HSSFRow row = sheet.createRow((short)currRow[i]++);
								 // Write Rup solution Type
								 HSSFCell cell = row.createCell((short)0);
								 cell.setCellValue(models[irup]);
								 cell.setCellStyle(cellStyle);
								 row = sheet.createRow((short)currRow[i]++);
								 int col=5;
								 
								 // Write All Mag Areas in appropriate columns
								 for(int j=0; j<magAreaOptions.size(); ++j, col+=(slipModelOptions.size()-1)) {
									 cell = row.createCell((short)col);
									 cell.setCellValue((String)magAreaOptions.get(j));
									 cell.setCellStyle(cellStyle);
								 }
								 // write the headers
								 row = sheet.createRow((short)currRow[i]++);
								 col=0;
								 cell = row.createCell((short)col++);
								 cell.setCellValue("Segment_Name");
								 cell.setCellStyle(cellStyle);
								 cell = row.createCell((short)col++);
								 cell.setCellValue("Original Slip Rate");
								 cell.setCellStyle(cellStyle);
								 cell = row.createCell((short)col++);
								 cell.setCellValue("Min Slip Rate");
								 cell.setCellStyle(cellStyle);
								 cell = row.createCell((short)col++);
								 cell.setCellValue("Max Slip Rate");
								 cell.setCellStyle(cellStyle);

								 cell = row.createCell((short)col++);
								 cell.setCellValue("Characteristic Model Slip Rate");
								 cell.setCellStyle(cellStyle);
								 for(int j=0; j<magAreaOptions.size(); ++j) {
									 for(int k=0; k<slipModelOptions.size(); ++k) {
										 String slipModel = (String)slipModelOptions.get(k);
										 if(!slipModel.equals(A_FaultSegmentedSource.CHAR_SLIP_MODEL)) {
											 cell = row.createCell((short)col++);
											 cell.setCellValue(slipModel);
											 cell.setCellStyle(cellStyle);
										 }
									 }
								 }								 
								 // write Seg Names and original Slip Rate
								 A_FaultSegmentedSource source = (A_FaultSegmentedSource) aFaultSources.get(i);
								 rupStartRow[i] = currRow[i];
								 
								 for(int seg=0; seg<source.getFaultSegmentData().getNumSegments(); ++seg) {
									 row = sheet.createRow((short)currRow[i]++);
									 row.createCell((short)0).setCellValue(source.getFaultSegmentData().getSegmentName(seg));
									 double slipRate = source.getFaultSegmentData().getSegmentSlipRate(seg);
									 double stdDev = source.getFaultSegmentData().getSegSlipRateStdDev(seg);
									 //System.out.println(seg+","+source.getFaultSegmentData().getSegmentName(seg));
									 row.createCell((short)1).setCellValue(slipRate*1e3);
									 row.createCell((short)2).setCellValue((slipRate-2*stdDev)*1e3);
									 row.createCell((short)3).setCellValue((slipRate+2*stdDev)*1e3);
								 }
							}
						}
						   
						   
						
						// write the rup Mag and rates
						for(int i=0; i<this.aFaultSources.size(); ++i) {
							 HSSFSheet sheet = wb.getSheetAt(i);
							 A_FaultSegmentedSource source = (A_FaultSegmentedSource) aFaultSources.get(i);
							 int rateCol;
							 if(slipModelOptions.get(islip).equals(A_FaultSegmentedSource.CHAR_SLIP_MODEL)) {
								 rateCol = 4;
							 } else rateCol = 4 + imag*(slipModelOptions.size()-1) + islip;
							 //rateCol = magCol + islip;
							 for(int seg=0; seg<source.getFaultSegmentData().getNumSegments(); ++seg) {
								 sheet.getRow(seg+rupStartRow[i]).createCell((short)rateCol).setCellValue(source.getFinalSegSlipRate(seg)*1e3);
							 }
						}
					}
			}
			// 
			for(int i=0; i<wb.getNumberOfSheets(); ++i) {
				HSSFSheet sheet = wb.getSheetAt(i);
				sheet.createRow((short)currRow[i]++);
				sheet.createRow((short)currRow[i]++);
			}
			
		}
		try {
			FileOutputStream fileOut = new FileOutputStream(outputFileName);
			wb.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}*/
	
	public static void main(String args[]) {
		GenerateTestExcelSheets genExcelSheets = new GenerateTestExcelSheets();
		genExcelSheets.mkExcelSheetTests();
	}
	
}
