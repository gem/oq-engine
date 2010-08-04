/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.awt.Color;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.Iterator;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.poifs.filesystem.POIFSFileSystem;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_B_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.geo.Region;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2_TimeDependentEpistemicList;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2_TimeIndependentEpistemicList;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;

/**
 * This class generates excel sheets for probability contribution of each A-Fault source and
 * some B-Faults (San Gregorio Connected, Greenville Connected, Green Valley Connected, 
 * Mount Diablo Thrust) in different regions (WG02, NoCal, SoCal, RELM) and for different durations. 
 * The method generateProbContributionsExcelSheet() is used to make excel sheets.
 * 
 * The generated excel sheets can then be used to make histogram plots and other plots for UCERF2 report.
 * A detailed explanation for generating the excel sheets and figures for UCERF2 report was emailed to Ned.
 * Since various excel sheets were generated, I ran this program multiple times on Mac Server. Every time I ran
 * this program, I called generateProbContributionsExcelSheet() with different parameters. Please see
 * the main() for different parameters which were passed to  generateProbContributionsExcelSheet().
 * 
 * 
 * @author vipingupta
 *
 */
public class ProbabilityDistHistogramPlotter implements GraphWindowAPI {
	private final static String PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/analysis/probContr/";
	private final static double MIN_PROB= 0.025;
	private final static double MAX_PROB= 0.975;
	private final static double DELTA_PROB= 0.05;
	private final static int NUM_PROB= Math.round((float)((MAX_PROB-MIN_PROB)/DELTA_PROB))+1;
	private final static String X_AXIS_LABEL = "Probability";
	private final static String Y_AXIS_LABEL = "Contribution";
	private final static String PLOT_LABEL = "Probability Contribution";
	private final PlotCurveCharacterstics HISTOGRAM1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.HISTOGRAM,
			new Color(0,0,0), 2); // black

	private final PlotCurveCharacterstics STACKED_BAR1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.STACKED_BAR,
			new Color(0,0,0), 2); // black
	private final PlotCurveCharacterstics STACKED_BAR2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.STACKED_BAR,
			Color.GREEN, 2); // Green
	private final PlotCurveCharacterstics STACKED_BAR3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.STACKED_BAR,
			Color.BLUE, 2); // Green

	private ArrayList funcs;
	private ArrayList<PlotCurveCharacterstics> plottingCurveChars;
	private HSSFWorkbook workbook;

	// Magnitudes for which calculations need to be done. 
	private double mags[] = { 5.0, 5.25, 5.5, 5.75, 6.0, 6.25, 6.5, 6.7, 7.0, 7.25, 7.5, 7.75, 8.0, 8.25};
	/*private double mags[] = { 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 
			6.0, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 
			7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 
			8.0, 8.1, 8.2, 8.3
	};*/
	public final static String A_FAULTS = "A-Faults";
	public final static String B_FAULTS = "B-Faults";
	public final static String NON_CA_B_FAULTS = "Non-CA B-Faults";
	public final static String C_ZONES = "C-Zones";
	public final static String BACKGROUND = "Background";
	public final static String TOTAL = "Total";
	private String[] sources = { A_FAULTS, B_FAULTS, NON_CA_B_FAULTS, C_ZONES, BACKGROUND, TOTAL };
	private UCERF2_TimeIndependentEpistemicList ucerf2EpistemicList;
	private String []bFaultNames = { "San Gregorio Connected", "Greenville Connected", 
			"Green Valley Connected", "Mount Diablo Thrust"};
	private String []aFaultNames = { "Elsinore", "Garlock", "San Jacinto", "N. San Andreas", "S. San Andreas",
			"Hayward-Rodgers Creek", "Calaveras"};



	/**
	 * Make probability contribution excel sheet from various branches for a given
	 * region and duration.
	 * 
	 * @param minMag
	 */
	public void generateProbContributionsExcelSheet(boolean isTimeDependent, 
			double duration, String fileName, Region region) {

		if(ucerf2EpistemicList==null) { // UCERF epistemic list
			if(isTimeDependent) ucerf2EpistemicList = new UCERF2_TimeDependentEpistemicList();
			else ucerf2EpistemicList = new UCERF2_TimeIndependentEpistemicList();
		}

		//	create a sheet that contains param settings for each logic tree branch
		workbook  = new HSSFWorkbook();
		createParamSettingsSheet();


		int numSources = sources.length; // A-Faults, B-Faults, Non-CA B-Faults, Background, C-Zones, Total

		// create sheet for each source
		for(int i=0; i<sources.length; ++i) {
			workbook.createSheet(sources[i]);
		}

		HSSFRow row1=null;


		// create sheet for each A-Fault
		for(int i=0; i<aFaultNames.length; ++i) {
			workbook.createSheet(aFaultNames[i]);
		}

		//create sheet for each B-Fault
		for(int i=0; i<bFaultNames.length; ++i) {
			workbook.createSheet(bFaultNames[i]);
		}

		// create sheet for each Source-type
		for(int i=0; i<sources.length; ++i) {
			row1 = workbook.getSheet(sources[i]).createRow(0);
			for(int magIndex=0; magIndex<mags.length; ++magIndex)
				row1.createCell((short)(magIndex+1)).setCellValue(" Mag "+mags[magIndex]);
		}


		// create sheet for each A-Fault
		for(int i=0; i<aFaultNames.length; ++i) {
			row1 = workbook.getSheet(aFaultNames[i]).createRow(0);
			for(int magIndex=0; magIndex<mags.length; ++magIndex)
				row1.createCell((short)(magIndex+1)).setCellValue(" Mag "+mags[magIndex]);
		}

		//create sheet for each B-Fault
		for(int i=0; i<bFaultNames.length; ++i) {
			row1 = workbook.getSheet(bFaultNames[i]).createRow(0);
			for(int magIndex=0; magIndex<mags.length; ++magIndex)
				row1.createCell((short)(magIndex+1)).setCellValue(" Mag "+mags[magIndex]);

		}


		int numERFs = ucerf2EpistemicList.getNumERFs(); // number of logic tree branches
		//	now write the probability contribtuions of each source in each branch of logic tree
		int startRowIndex = 2;
		DiscretizedFuncAPI bckgroundProbs = null;
		DiscretizedFuncAPI cZoneProbs =null;
		ucerf2EpistemicList.getTimeSpan().setDuration(duration);
		for(int erfIndex=0; erfIndex<numERFs; ++erfIndex) {
			System.out.println("Doing run "+(erfIndex+1)+" of "+numERFs);
			UCERF2 ucerf2 = (UCERF2)ucerf2EpistemicList.getERF(erfIndex);

			if(bckgroundProbs==null) {
				bckgroundProbs = getDiscretizedFunc();
				cZoneProbs = getDiscretizedFunc();
				ucerf2.getTotal_C_ZoneProb(cZoneProbs, region);
				ucerf2.getTotal_BackgroundProb(bckgroundProbs, region);
			}
			DiscretizedFuncAPI aFaultsProbs = getDiscretizedFunc();
			DiscretizedFuncAPI bFaultsProbs = getDiscretizedFunc();
			DiscretizedFuncAPI nonCA_B_FaultsProbs = getDiscretizedFunc();
			DiscretizedFuncAPI totalProbs = getDiscretizedFunc();

			ucerf2.getTotal_A_FaultsProb(aFaultsProbs, region);
			ucerf2.getTotal_B_FaultsProb(bFaultsProbs, region);
			ucerf2.getTotal_NonCA_B_FaultsProb(nonCA_B_FaultsProbs, region);
			getTotalProb(totalProbs, aFaultsProbs, bFaultsProbs, nonCA_B_FaultsProbs, cZoneProbs, bckgroundProbs);


			// each Source Type
			for(int i=0; i<sources.length; ++i) {
				row1 = workbook.getSheet(sources[i]).createRow(startRowIndex+erfIndex);
				row1.createCell((short)0).setCellValue("Branch "+(erfIndex+1));
				DiscretizedFuncAPI func=null;
				if(sources[i].equals(this.A_FAULTS)) func = aFaultsProbs;
				else if(sources[i].equals(this.B_FAULTS)) func = bFaultsProbs;
				else if(sources[i].equals(this.NON_CA_B_FAULTS)) func = nonCA_B_FaultsProbs;
				else if(sources[i].equals(this.BACKGROUND)) func = bckgroundProbs;
				else if(sources[i].equals(this.C_ZONES)) func = cZoneProbs;
				else if(sources[i].equals(this.TOTAL)) func = totalProbs;

				for(int magIndex=0; magIndex<mags.length; ++magIndex)
					row1.createCell((short)(magIndex+1)).setCellValue(func.getY(magIndex));
			}


			// each A-Fault
			for(int i=0; i<aFaultNames.length; ++i) {
				DiscretizedFuncAPI aFaultProbDist = getDiscretizedFunc();
				row1 = workbook.getSheet(aFaultNames[i]).createRow(startRowIndex+erfIndex);
				row1.createCell((short)0).setCellValue("Branch "+(erfIndex+1));
				ucerf2.getProbForA_Fault(aFaultNames[i], aFaultProbDist, region);
				for(int magIndex=0; magIndex<mags.length; ++magIndex)
					row1.createCell((short)(magIndex+1)).setCellValue(aFaultProbDist.getY(magIndex));
			}

			//each B-Fault
			for(int i=0; i<bFaultNames.length; ++i) {
				DiscretizedFuncAPI bFaultProbDist = getDiscretizedFunc();
				row1 = workbook.getSheet(bFaultNames[i]).createRow(startRowIndex+erfIndex);
				row1.createCell((short)0).setCellValue("Branch "+(erfIndex+1));
				ucerf2.getProbsForB_Fault(bFaultNames[i], bFaultProbDist, region);
				for(int magIndex=0; magIndex<mags.length; ++magIndex)
					row1.createCell((short)(magIndex+1)).setCellValue(bFaultProbDist.getY(magIndex));
			}

		}

		//		 write  excel sheet
		try {
			FileOutputStream fileOut = new FileOutputStream(fileName);
			workbook.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Calculate Total prob
	 * @param totalProbs
	 * @param aFaultsProbs
	 * @param bFaultsProbs
	 * @param nonCA_B_FaultsProbs
	 * @param cZoneProbs
	 * @param bckgroundProbs
	 */
	private void getTotalProb(DiscretizedFuncAPI totalProbs, 
			DiscretizedFuncAPI aFaultsProbs, 
			DiscretizedFuncAPI bFaultsProbs, DiscretizedFuncAPI nonCA_B_FaultsProbs, 
			DiscretizedFuncAPI cZoneProbs, DiscretizedFuncAPI bckgroundProbs) {
		int numMags = totalProbs.getNum();
		for(int i=0; i<numMags; ++i) {
			double prob = 1;
			prob *= 1-bFaultsProbs.getY(i);
			prob *= 1-nonCA_B_FaultsProbs.getY(i);
			prob *= 1-aFaultsProbs.getY(i);
			prob *= 1-bckgroundProbs.getY(i);
			prob *= 1-cZoneProbs.getY(i);
			totalProbs.set(i, 1.0-prob);
		}
	}


	/**
	 * Get discretized func
	 * 
	 * @return
	 */
	private DiscretizedFuncAPI getDiscretizedFunc() {
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
		for(int i=0; i<mags.length; ++i) func.set(mags[i], 1.0);
		return func;
	}


	/**
	 * Plot stacked histograms for Ellsworth B and Hans-Bakun 2002 Magnitude Area Relationship
	 * @param fileName
	 */
	public void plotMagAreaComparisonProbPlot(double mag, String fileName, String sourceType) {


		ArrayList<Integer> ellB_BranchIndices;
		ArrayList<Integer> hansBakunBranchIndices;

//		Open the excel file
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(fileName));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet paramSettingsSheet = wb.getSheetAt(0); // 
			// Ellsworth B
			ellB_BranchIndices = getBranchIndices(paramSettingsSheet, UCERF2.MAG_AREA_RELS_PARAM_NAME, Ellsworth_B_WG02_MagAreaRel.NAME);
			// Hans & Bakun 2002
			hansBakunBranchIndices = getBranchIndices(paramSettingsSheet, UCERF2.MAG_AREA_RELS_PARAM_NAME, HanksBakun2002_MagAreaRel.NAME);

			int totProbColIndex=getColIndexForMag(mag);
			HSSFSheet probSheet = wb.getSheet(sourceType); // whole Region

			EvenlyDiscretizedFunc ellB_Func = getFunc("Histogram Plot for Ellsworth B  for "+sourceType + " for fileName "+fileName+" at Mag="+mag, ellB_BranchIndices, paramSettingsSheet, totProbColIndex, probSheet);
			EvenlyDiscretizedFunc hansBakunFunc = getFunc("Histogram Plot for Hans & Bakun for "+sourceType + " for fileName "+fileName+" at Mag="+mag, hansBakunBranchIndices, paramSettingsSheet, totProbColIndex, probSheet);
			this.addFuncs(hansBakunFunc, ellB_Func);
			// plot histograms 
			funcs = new ArrayList();
			funcs.add(ellB_Func);
			funcs.add(hansBakunFunc);
			plottingCurveChars = new ArrayList<PlotCurveCharacterstics>();
			plottingCurveChars.add(STACKED_BAR1);
			plottingCurveChars.add(STACKED_BAR2);
			GraphWindow graphWindow= new GraphWindow(this);
			graphWindow.setPlotLabel(PLOT_LABEL);
			graphWindow.plotGraphUsingPlotPreferences();
			graphWindow.setVisible(true);

		}catch (Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Plot Aperiodicity histograms for aperiodicity values: 0.3, 0.5, 0.7
	 * 
	 * @param fileName
	 */
	public void plotAperiodicity_ComparisonProbPlot(double mag, String fileName, String sourceType) {


		ArrayList<Integer> aperiodicity0_3;
		ArrayList<Integer> aperiodicity0_5;
		ArrayList<Integer> aperiodicity0_7;

//		Open the excel file
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(fileName));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet paramSettingsSheet = wb.getSheetAt(0); // 
			// BPT and Poisson
			aperiodicity0_3 = getBranchIndices(paramSettingsSheet, UCERF2.APERIODICITY_PARAM_NAME, "0.3");
			aperiodicity0_5 = getBranchIndices(paramSettingsSheet, UCERF2.APERIODICITY_PARAM_NAME, "0.5");
			aperiodicity0_7 = getBranchIndices(paramSettingsSheet, UCERF2.APERIODICITY_PARAM_NAME, "0.7");

			int totProbColIndex=getColIndexForMag(mag);
			HSSFSheet probSheet = wb.getSheet(sourceType); // whole Region

			EvenlyDiscretizedFunc func0_3 = getFunc("Histogram Plot for Aperiodicity = 0.3 for "+sourceType + " for fileName "+fileName+" at Mag="+mag, aperiodicity0_3, paramSettingsSheet, totProbColIndex, probSheet);
			EvenlyDiscretizedFunc func0_5 = getFunc("Histogram Plot for Aperiodicity = 0.5 for "+sourceType + " for fileName "+fileName+" at Mag="+mag, aperiodicity0_5, paramSettingsSheet, totProbColIndex, probSheet);
			addFuncs(func0_5, func0_3);
			EvenlyDiscretizedFunc func0_7 = getFunc("Histogram Plot for Aperiodicity = 0.7 for "+sourceType + " for fileName "+fileName+" at Mag="+mag, aperiodicity0_7, paramSettingsSheet, totProbColIndex, probSheet);
			addFuncs(func0_7, func0_5);
			// plot histograms 
			funcs = new ArrayList();
			funcs.add(func0_3);
			funcs.add(func0_5);
			funcs.add(func0_7);
			plottingCurveChars = new ArrayList<PlotCurveCharacterstics>();
			plottingCurveChars.add(STACKED_BAR1);
			plottingCurveChars.add(STACKED_BAR2);
			plottingCurveChars.add(STACKED_BAR3);
			GraphWindow graphWindow= new GraphWindow(this);
			graphWindow.setPlotLabel(PLOT_LABEL);
			graphWindow.plotGraphUsingPlotPreferences();
			graphWindow.setVisible(true);

		}catch (Exception e) {
			e.printStackTrace();
		}
	}


	/**
	 * Plot Apriori and MoBal comparison histograms.
	 * 
	 * @param fileName
	 */
	public void plotAprioiMoBal_ComparisonPlot(double mag, String fileName, String sourceType) {


		ArrayList<Integer> apriori;
		ArrayList<Integer> moBal;


//		Open the excel file
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(fileName));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet paramSettingsSheet = wb.getSheetAt(0); // 
			// BPT and Poisson
			moBal = getBranchIndices(paramSettingsSheet, UCERF2.REL_A_PRIORI_WT_PARAM_NAME, "1.0E-4");
			apriori = getBranchIndices(paramSettingsSheet, UCERF2.REL_A_PRIORI_WT_PARAM_NAME, "1.0E10");

			int totProbColIndex=getColIndexForMag(mag);
			HSSFSheet probSheet = wb.getSheet(sourceType); // whole Region

			EvenlyDiscretizedFunc aprioriFunc = getFunc("Histogram Plot for Apriori for "+sourceType + " for fileName "+fileName+" at Mag="+mag, apriori, paramSettingsSheet, totProbColIndex, probSheet);
			EvenlyDiscretizedFunc moBalFunc = getFunc("Histogram Plot for Mo Bal  for "+sourceType + " for fileName "+fileName+" at Mag="+mag, moBal, paramSettingsSheet, totProbColIndex, probSheet);
			addFuncs(moBalFunc, aprioriFunc);
			// plot histograms 
			funcs = new ArrayList();
			funcs.add(aprioriFunc);
			funcs.add(moBalFunc);
			plottingCurveChars = new ArrayList<PlotCurveCharacterstics>();
			plottingCurveChars.add(STACKED_BAR1);
			plottingCurveChars.add(STACKED_BAR2);
			GraphWindow graphWindow= new GraphWindow(this);
			graphWindow.setPlotLabel(PLOT_LABEL);
			graphWindow.plotGraphUsingPlotPreferences();
			graphWindow.setVisible(true);

		}catch (Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * It updates func1 values. It adds values from func2 to func1
	 * @param func1
	 * @param func2
	 */
	private void addFuncs(EvenlyDiscretizedFunc func1, EvenlyDiscretizedFunc func2) {
		for(int i=0; i<func1.getNum(); ++i)
			func1.add(i, func2.getY(i));
	}

	/**
	 * Plot stacked histograms for BPT vs Empirical plots
	 * @param fileName
	 */
	public void plotEmpiricalBPT_ComparisonProbPlot(double mag, String fileName, String sourceType) {


		ArrayList<Integer> bptBranchIndices;
		ArrayList<Integer> empiricalBranchIndices;

//		Open the excel file
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(fileName));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet paramSettingsSheet = wb.getSheetAt(0); // 
			// BPT and Poisson
			bptBranchIndices = getBranchIndices(paramSettingsSheet, UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_BPT);
			bptBranchIndices.addAll(getBranchIndices(paramSettingsSheet, UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_POISSON));
			// Empirical
			empiricalBranchIndices = getBranchIndices(paramSettingsSheet, UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_EMPIRICAL);

			int totProbColIndex=getColIndexForMag(mag);
			HSSFSheet probSheet = wb.getSheet(sourceType); // whole Region

			EvenlyDiscretizedFunc bptFunc = getFunc("Histogram Plot for BPT/Poisson for "+sourceType + " for fileName "+fileName+" at Mag="+mag, bptBranchIndices, paramSettingsSheet, totProbColIndex, probSheet);
			EvenlyDiscretizedFunc empFunc = getFunc("Histogram Plot for Empirical for "+sourceType + " for fileName "+fileName+" at Mag="+mag, empiricalBranchIndices, paramSettingsSheet, totProbColIndex, probSheet);
			this.addFuncs(empFunc, bptFunc);
			// plot histograms 
			funcs = new ArrayList();
			funcs.add(bptFunc);
			funcs.add(empFunc);
			plottingCurveChars = new ArrayList<PlotCurveCharacterstics>();
			plottingCurveChars.add(STACKED_BAR1);
			plottingCurveChars.add(STACKED_BAR2);
			GraphWindow graphWindow= new GraphWindow(this);
			graphWindow.setPlotLabel(PLOT_LABEL);
			graphWindow.plotGraphUsingPlotPreferences();
			graphWindow.setVisible(true);

		}catch (Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * It reads the input file as created by generateProbContributionsExcelSheet() method
	 * and adds an additional sheet with min, max, mean for each column.
	 * 
	 * @param inputFileName
	 */
	public void addMinMaxAvgSheet(String inputFileName) {

		// Open the excel file
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(inputFileName));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet paramSettingSheet = wb.getSheetAt(0);
			int numSheets = wb.getNumberOfSheets();

			// list of all branch indices
			ArrayList<Integer>  bIndices= getBranchIndices(wb.getSheetAt(0),  UCERF2.PROB_MODEL_PARAM_NAME,  null);


			HSSFSheet newSheet = wb.createSheet("MinMaxAvg");

			newSheet.createRow(0); // Row to write Sheet name
			newSheet.createRow(1); // row to write min/max/avg
			final int startRowIndex = 2;

			// write all magnitudes
			for(int magIndex=0; magIndex<this.mags.length; ++magIndex)
				newSheet.createRow(magIndex+startRowIndex).createCell((short)0).setCellValue(mags[magIndex]);

			int lastColIndex = mags.length;
			//	do for each sheet except parameter Settings sheet
			for(int sheetIndex=1; sheetIndex<numSheets; ++sheetIndex) { 
				String sheetName = wb.getSheetName(sheetIndex); 
				HSSFSheet origSheet = wb.getSheetAt(sheetIndex);
				int startColIndex = 3*(sheetIndex-1)+1;
				newSheet.getRow(0).createCell((short)(startColIndex)).setCellValue(sheetName);
				newSheet.getRow(1).createCell((short)(startColIndex)).setCellValue("Min");
				newSheet.getRow(1).createCell((short)(startColIndex+1)).setCellValue("Max");
				newSheet.getRow(1).createCell((short)(startColIndex+2)).setCellValue("Avg");

				// write min, max, avg and Y values in all subsequent columns
				for(int colIndex=1; colIndex<=lastColIndex; ++colIndex) {
					double[] minMaxAvg = getMinMaxAvg(paramSettingSheet, bIndices, colIndex, origSheet);
					HSSFRow row  = newSheet.getRow(startRowIndex+colIndex-1);
					// create min/max/avg rows
					row.createCell((short)startColIndex).setCellValue(minMaxAvg[0]);
					row.createCell((short)(startColIndex+1)).setCellValue(minMaxAvg[1]);
					row.createCell((short)(startColIndex+2)).setCellValue(minMaxAvg[2]);				
				}
			}

			// write to output file
			FileOutputStream fileOut = new FileOutputStream(inputFileName);
			wb.write(fileOut);
			fileOut.close();

		}catch (Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * It reads the input file as created by generateProbContributionsExcelSheet() method
	 * and generates min, max, mean and a histogram function for each column in the sheet.
	 * These values are then saved in a separate excel sheet
	 * 
	 * @param inputFileName
	 * @param outputFileName
	 */
	public void mkHistogramSheet(String inputFileName, String outputFileName) {

		int lastColIndex;

		// Open the excel file
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(inputFileName));
			HSSFWorkbook wb = new HSSFWorkbook(fs);

			int numSheets = wb.getNumberOfSheets();

			// list of all branch indices
			ArrayList<Integer>  bIndices= getBranchIndices(wb.getSheetAt(0),  UCERF2.PROB_MODEL_PARAM_NAME,  null);

			//	create a sheet that contains param settings for each logic tree branch
			HSSFWorkbook newWorkbook  = new HSSFWorkbook();

			//	do for each sheet except parameter Settings sheet
			for(int sheetIndex=1; sheetIndex<numSheets; ++sheetIndex) { 
				HSSFSheet origSheet = wb.getSheetAt(sheetIndex); 
				lastColIndex = mags.length;
				HSSFSheet newSheet = newWorkbook.createSheet(wb.getSheetName(sheetIndex));

				int rowIndex=0;

				EvenlyDiscretizedFunc xValuesFunc = new EvenlyDiscretizedFunc(MIN_PROB, MAX_PROB, NUM_PROB);
				// copy first 2 rows from original sheet to final sheet
				for(; rowIndex<2; ++rowIndex) {
					HSSFRow newRow = newSheet.createRow(rowIndex);
					HSSFRow origRow = origSheet.getRow(rowIndex);
					if(origRow == null) continue;
					for(int colIndex=0; colIndex<=lastColIndex; ++colIndex) {
						HSSFCell origCell = origRow.getCell((short)colIndex);
						if(origCell==null) continue;
						newRow.createCell((short)colIndex).setCellValue(origCell.getStringCellValue());
					}
				}

				rowIndex = 2;
				// create min/max/avg rows
				newSheet.createRow(rowIndex++).createCell((short)0).setCellValue("Min");
				newSheet.createRow(rowIndex++).createCell((short)0).setCellValue("Max");
				newSheet.createRow(rowIndex++).createCell((short)0).setCellValue("Avg");

				rowIndex = 6;
				// now write all x values in first column
				for(int i=0; i<xValuesFunc.getNum(); ++i)
					newSheet.createRow(rowIndex++).createCell((short)0).setCellValue(xValuesFunc.getX(i));

				// write min, max, avg and Y values in all subsequent columns
				for(int colIndex=1; colIndex<=lastColIndex; ++colIndex) {
					double[] minMaxAvg = getMinMaxAvg(wb.getSheetAt(0), bIndices, colIndex, origSheet);
					EvenlyDiscretizedFunc func = getFunc("", bIndices, wb.getSheetAt(0), colIndex, origSheet);
					rowIndex = 2;
					// create min/max/avg rows
					newSheet.getRow(rowIndex++).createCell((short)colIndex).setCellValue(minMaxAvg[0]);
					newSheet.createRow(rowIndex++).createCell((short)colIndex).setCellValue(minMaxAvg[1]);
					newSheet.createRow(rowIndex++).createCell((short)colIndex).setCellValue(minMaxAvg[2]);

					rowIndex = 6;
					// now write all x values in first column
					for(int i=0; i<func.getNum(); ++i)
						newSheet.createRow(rowIndex++).createCell((short)colIndex).setCellValue(func.getY(i));

				}
			}

			// write to output file
			FileOutputStream fileOut = new FileOutputStream(outputFileName);
			newWorkbook.write(fileOut);
			fileOut.close();

		}catch (Exception e) {
			e.printStackTrace();
		}
	}


	/**
	 *  Get min/max/avg for a column
	 *  
	 * @param bptBranchIndices
	 * @param totProbColIndex
	 * @param probSheet
	 * @return
	 */
	private double[] getMinMaxAvg(HSSFSheet paramSettingsSheet, ArrayList<Integer> branchIndices, 
			int probColIndex, HSSFSheet probSheet) {

		double totProb = 0.0, totWt=0.0;
		double minProb = Double.MAX_VALUE;
		double maxProb = Double.NEGATIVE_INFINITY;
		int weightColIndex =  getColIndexForParam(paramSettingsSheet, "Branch Weight"); // logic tree branch weight  index column

		for (int i=0; i<branchIndices.size(); ++i) { 
			int branchNum=branchIndices.get(i);
			double wt= paramSettingsSheet.getRow(branchNum).getCell((short)weightColIndex).getNumericCellValue();
			double prob = probSheet.getRow(branchNum+1).getCell((short)probColIndex).getNumericCellValue();
			totProb+=wt*prob;
			totWt+=wt;
			if(prob>maxProb) maxProb = prob;
			if(prob<minProb) minProb = prob;
		}
		double []minMaxAvg = new double[3];
		minMaxAvg[0] = minProb;
		minMaxAvg[1] = maxProb;
		minMaxAvg[2] = totProb/totWt;
		return minMaxAvg;
	}

	/**
	 * 
	 * @param metadata
	 * @param branchIndices
	 * @param paramSettingsSheet
	 * @param probColIndex
	 * @param probSheet
	 * @return
	 */
	private EvenlyDiscretizedFunc getFunc(String metadata, ArrayList<Integer> branchIndices, 
			HSSFSheet paramSettingsSheet, int probColIndex, HSSFSheet probSheet) {

		int weightColIndex =  getColIndexForParam(paramSettingsSheet, "Branch Weight"); // logic tree branch weight  index column

		// 
		EvenlyDiscretizedFunc bptFunc = new EvenlyDiscretizedFunc(MIN_PROB, MAX_PROB, NUM_PROB);
		bptFunc.setInfo(metadata);
		bptFunc.setTolerance(DELTA_PROB);

		double totProbWt=0, totWt=0;
		for (int i=0; i<branchIndices.size(); ++i) { // populate  func
			int branchNum=branchIndices.get(i);
			double wt= paramSettingsSheet.getRow(branchNum).getCell((short)weightColIndex).getNumericCellValue();
			totWt+=wt;
			double prob = probSheet.getRow(branchNum+1).getCell((short)probColIndex).getNumericCellValue();
			totProbWt+=wt*prob;
			if(prob>this.MAX_PROB) prob=MAX_PROB;
			//System.out.println(prob);
			bptFunc.add(prob, wt);
		}
		bptFunc.setName("Mean="+totProbWt/totWt);
		return bptFunc;
	}

	/**
	 * Plot Histogram for a particular source or total prob 
	 * 
	 * @param minMag
	 * @param fileName
	 * @param sourceType It can be A_Faults, B_Faults, Non_CA_B_Faults, C-Zones, Background, Total.
	 * These are constant values as defined in this class
	 */
	public void plotHistogramsForMagAndSource(double minMag, String fileName, String sourceType) {


		int colIndex=getColIndexForMag(minMag);

		// Open the excel file
		try {
			POIFSFileSystem fs = new POIFSFileSystem(getClass().getClassLoader().getResourceAsStream(fileName));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			HSSFSheet sheet = wb.getSheet(sourceType); // whole Region

			ArrayList<Integer>  bIndices= getBranchIndices(wb.getSheetAt(0),  UCERF2.PROB_MODEL_PARAM_NAME,  null);
			EvenlyDiscretizedFunc func = this.getFunc("Histogram plot for "+fileName+" for Mag>="+minMag, bIndices, wb.getSheetAt(0), colIndex, sheet);

			funcs = new ArrayList();
			funcs.add(func);
			plottingCurveChars = new ArrayList<PlotCurveCharacterstics>();
			plottingCurveChars.add(this.HISTOGRAM1);
			GraphWindow graphWindow= new GraphWindow(this);
			graphWindow.setPlotLabel(PLOT_LABEL);
			graphWindow.plotGraphUsingPlotPreferences();
			graphWindow.setVisible(true);
		}catch (Exception e) {
			e.printStackTrace();
		}
	}


	/**
	 * Get column index for a magnitiude
	 * 
	 * @param minMag
	 * @return
	 */
	private int getColIndexForMag(double minMag) {
		boolean found = false;
		int colIndex=-1;
		// find the column based on the specfied magnitude
		for(int magIndex=0; magIndex<this.mags.length && !found; ++magIndex) {
			if(mags[magIndex]==minMag) {
				colIndex = magIndex+1;
				found=true;
			}
		}
		if(!found) throw new RuntimeException("Invalid minimum magnitude");
		return colIndex;
	}

	/**
	 * Get a list of branch numbers which has the specified value of parameter specified by
	 * paramName.
	 * Indices start from 1.
	 * @param paramName 
	 * @param value null if all rows are required
	 * @return
	 */
	private ArrayList<Integer> getBranchIndices(HSSFSheet sheet, String paramName, String value) {
		int colIndex = getColIndexForParam(sheet, paramName); // column index where Prob Model value is specified in file
		int lastRowIndex = sheet.getLastRowNum();
		ArrayList<Integer> branchIndices = new ArrayList<Integer>();
		// fill the branch numbers for BPT (or Poisson) and Empirical
		for(int i=1; i<=lastRowIndex; ++i) {
			HSSFCell cell = sheet.getRow(i).getCell((short)colIndex);
			if(cell==null) continue;
			String cellVal = cell.getStringCellValue();
			if(value==null || cellVal.equals(value)) branchIndices.add(i);
		}
		return branchIndices;
	}


	/**
	 * Get column index for specified parameter name from metadata sheet
	 * 
	 * @param paramName
	 * @return
	 */
	private int getColIndexForParam(HSSFSheet sheet, String paramName) {
		HSSFRow row = sheet.getRow(0);
		int firsColIndex = row.getFirstCellNum();
		int lastColIndex = row.getLastCellNum();
		for(int i=firsColIndex; i<=lastColIndex; ++i)
			if(row.getCell((short)i).getStringCellValue().equals(paramName)) return i;
		throw new RuntimeException("Parameter "+paramName+" does not exist in the sheet");
	}


	/**
	 * create a sheet that lists parameter settings for each logic tree branch
	 *
	 */
	private void createParamSettingsSheet() {

		HSSFSheet paramSettingsSheet = workbook.createSheet("Parameter Settings");
		HSSFRow row;
		ParameterList adjustableParams = ucerf2EpistemicList.getParameterList(0);
		Iterator it = adjustableParams.getParametersIterator();
		ArrayList<String> adjustableParamNames = new ArrayList<String>();
		while(it.hasNext()) {
			ParameterAPI param = (ParameterAPI)it.next();
			adjustableParamNames.add(param.getName());
		}

		// add column for each parameter name. 
		row = paramSettingsSheet.createRow(0); 
		for(int i=1; i<=adjustableParamNames.size(); ++i) {
			row.createCell((short)i).setCellValue(adjustableParamNames.get(i-1));
		}

		int weightCol = adjustableParamNames.size()+1;
		row.createCell((short)(weightCol)).setCellValue("Branch Weight");

		int numERFs = ucerf2EpistemicList.getNumERFs(); // number of logic tree branches
		//		now write all the parameter settings for each branch in the excel sheet
		for(int i=0; i<numERFs; ++i) {
			row = paramSettingsSheet.createRow(i+1); 
			row.createCell((short)0).setCellValue("Branch "+(i+1));
			adjustableParams = ucerf2EpistemicList.getParameterList(i);
			for( int paramIndex=0; paramIndex<adjustableParamNames.size(); ++paramIndex) {
				String pName = adjustableParamNames.get(paramIndex);
				if(adjustableParams.containsParameter(pName))
					row.createCell((short)(paramIndex+1)).setCellValue(adjustableParams.getValue(pName).toString());
			}
			row.createCell((short)(weightCol)).setCellValue(ucerf2EpistemicList.getERF_RelativeWeight(i));

		}
	}


	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getCurveFunctionList()
	 */
	public ArrayList getCurveFunctionList() {
		return funcs;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXLog()
	 */
	public boolean getXLog() {
		return false;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYLog()
	 */
	public boolean getYLog() {
		return false;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getXAxisLabel()
	 */
	public String getXAxisLabel() {
		return X_AXIS_LABEL;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYAxisLabel()
	 */
	public String getYAxisLabel() {
		return Y_AXIS_LABEL;
	}


	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getPlottingFeatures()
	 */
	public ArrayList<PlotCurveCharacterstics> getPlottingFeatures() {
		return plottingCurveChars;
	}


	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#isCustomAxis()
	 */
	public boolean isCustomAxis() {
		return false;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinX()
	 */
	public double getMinX() {
		//return 5.0;
		throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxX()
	 */
	public double getMaxX() {
		//return 9.255;
		throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinY()
	 */
	public double getMinY() {
		//return 1e-4;
		throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxY()
	 */
	public double getMaxY() {
		//return 10;
		throw new UnsupportedOperationException("Method not implemented yet");
	}

	public static void main(String[] args) {
		ProbabilityDistHistogramPlotter plotter = new ProbabilityDistHistogramPlotter();
		//plotter.generateProbContributionsExcelSheet(true, 30, PATH+"ProbabilityContributions_30yrs_All.xls", null);
		//plotter.generateProbContributionsExcelSheet(true, 30, PATH+"ProbabilityContributions_30yrs_WG02.xls", new EvenlyGriddedWG02_Region());
		//plotter.generateProbContributionsExcelSheet(true, 30, PATH+"ProbabilityContributions_30yrs_NoCal.xls", new EvenlyGriddedNoCalRegion());
		//plotter.generateProbContributionsExcelSheet(true, 30, PATH+"ProbabilityContributions_30yrs_SoCal.xls", new EvenlyGriddedSoCalRegion());
		//plotter.generateProbContributionsExcelSheet(true, 5, PATH+"ProbabilityContributions_5yrs_All.xls", null);
		//plotter.generateProbContributionsExcelSheet(true, 5, PATH+"ProbabilityContributions_5yrs_WG02.xls", new EvenlyGriddedWG02_Region());
		//plotter.generateProbContributionsExcelSheet(true, 5, PATH+"ProbabilityContributions_5yrs_NoCal.xls", new EvenlyGriddedNoCalRegion());
		//plotter.generateProbContributionsExcelSheet(true, 5, PATH+"ProbabilityContributions_5yrs_SoCal.xls", new EvenlyGriddedSoCalRegion());
		//plotter.generateProbContributionsExcelSheet(true, 1, PATH+"ProbabilityContributions_1yr_All.xls", null);
		//plotter.generateProbContributionsExcelSheet(true, 15, PATH+"ProbabilityContributions_15yrs_All.xls", null);
		//plotter.generateProbContributionsExcelSheet(false, 30, PATH+"ProbabilityContributions_Pois_30yrs_All.xls", null);
		 //plotter.generateProbContributionsExcelSheet(true, 30, PATH+"ProbabilityContributions_30yrs_LA_Box.xls", new EvenlyGriddedWG07_LA_Box_Region());

		/**/
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_30yrs_All.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_5yrs_All.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_30yrs_WG02.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_5yrs_WG02.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_30yrs_NoCal.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_5yrs_NoCal.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_30yrs_SoCal.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_5yrs_SoCal.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_1yr_All.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_15yrs_All.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_Pois_30yrs_All.xls");
		plotter.addMinMaxAvgSheet(PATH+"ProbabilityContributions_30yrs_LA_Box.xls");
		 
		

		//plotter.plotEmpiricalBPT_ComparisonProbPlot(7.5, PATH+"ProbabilityContributions_30yrs_All.xls", ProbabilityDistHistogramPlotter.TOTAL);
		//plotter.plotMagAreaComparisonProbPlot(7.5, PATH+"ProbabilityContributions_30yrs_All.xls", ProbabilityDistHistogramPlotter.TOTAL);
		//plotter.plotEmpiricalBPT_ComparisonProbPlot(6.7, PATH+"ProbabilityContributions_30yrs_WG02.xls", ProbabilityDistHistogramPlotter.TOTAL);
		//plotter.plotMagAreaComparisonProbPlot(6.7, PATH+"ProbabilityContributions_30yrs_WG02.xls", ProbabilityDistHistogramPlotter.TOTAL);

		//plotter.plotEmpiricalBPT_ComparisonProbPlot(7.5, PATH+"ProbabilityContributions_30yrs_All.xls", ProbabilityDistHistogramPlotter.A_FAULTS);
		//plotter.plotMagAreaComparisonProbPlot(7.5, PATH+"ProbabilityContributions_30yrs_All.xls", ProbabilityDistHistogramPlotter.A_FAULTS);
		//plotter.plotEmpiricalBPT_ComparisonProbPlot(6.7, PATH+"ProbabilityContributions_30yrs_WG02.xls", ProbabilityDistHistogramPlotter.A_FAULTS);
		//plotter.plotMagAreaComparisonProbPlot(6.7, PATH+"ProbabilityContributions_30yrs_WG02.xls", ProbabilityDistHistogramPlotter.A_FAULTS);

		//plotter.plotAperiodicity_ComparisonProbPlot(6.7, PATH+"ProbabilityContributions_30yrs_All.xls", ProbabilityDistHistogramPlotter.A_FAULTS);
		//plotter.plotAprioiMoBal_ComparisonPlot(6.7, PATH+"ProbabilityContributions_30yrs_All.xls", ProbabilityDistHistogramPlotter.A_FAULTS);
		//plotter.plotAprioiMoBal_ComparisonPlot(6.7, PATH+"ProbabilityContributions_30yrs_All.xls", ProbabilityDistHistogramPlotter.A_FAULTS);


		//plotter.plotAperiodicity_ComparisonProbPlot(7.0, PATH+"ProbabilityContributions_30yrs_All.xls", ProbabilityDistHistogramPlotter.A_FAULTS);
		//plotter.plotAperiodicity_ComparisonProbPlot(7.5, PATH+"ProbabilityContributions_30yrs_All.xls", ProbabilityDistHistogramPlotter.A_FAULTS);

	}

}
