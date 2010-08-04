/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.awt.Color;
import java.io.BufferedReader;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.StringTokenizer;

import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_B_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.sha.earthquake.rupForecastImpl.Frankel02.Frankel02_AdjustableEqkRupForecast;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2_TimeIndependentEpistemicList;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.magdist.ArbIncrementalMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;


/**
 * This is used for plotting various logic tree MFDs. 
 * It generates MFDs for each source type for each branch in UCERF2. The MFDs are saved in a text
 * file. Actually, this class can generate the MFD files and also plot (using JFreeChart) after reading those files.
 * 
 * To Generate the files, use the generateMFDsData() method call.
 * To plot the MFDs from files, use the method plotMFDs().
 * 
 * The main() function of this class provides valuable insight into this.
 * 
 * @author vipingupta
 *
 */
public class LogicTreeMFDsPlotter implements GraphWindowAPI {
	
	private final static String X_AXIS_LABEL = "Magnitude";
	private final static String CUM_Y_AXIS_LABEL = "Cumulative Rate (per year)";
	private final static String INCR_Y_AXIS_LABEL = "Incremental Rate (per year)";
	
	
	protected ArrayList<IncrementalMagFreqDist> aFaultMFDsList, bFaultCharMFDsList, bFaultGRMFDsList, totMFDsList, nonCA_B_FaultsMFDsList;
	private IncrementalMagFreqDist cZoneMFD, bckMFD, nshmp02TotMFD;
	
	private final static String DEFAULT_PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/logicTreeMFDs/";
	private final static String BCK_FRAC_PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/logicTreeMFDs/BackGrdFrac0_1/";
	private final static String BFAULT_BVAL_PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/logicTreeMFDs/BFault_BVal0/";
	
	protected final static String A_FAULTS_MFD_FILENAME = "A_Faults_MFDs.txt";
	protected final static String B_FAULTS_CHAR_MFD_FILENAME = "B_FaultsCharMFDs.txt";
	protected final static String B_FAULTS_GR_MFD_FILENAME = "B_FaultsGR_MFDs.txt";
	protected final static String NON_CA_B_FAULTS_MFD_FILENAME = "Non_CA_B_Faults_MFDs.txt";
	protected final static String TOT_MFD_FILENAME = "TotMFDs.txt";
	private final static String NSHMP_02_MFD_FILENAME = "NSHMP02_MFDs.txt";
	private final static String METADATA_EXCEL_SHEET = "Metadata.xls";
	private final static String COMBINED_AVG_FILENAME = "CombinedAvgMFDs.txt";
	
	
	protected final PlotCurveCharacterstics PLOT_CHAR1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.BLUE, 2); // A-Faults
	private final PlotCurveCharacterstics PLOT_CHAR1_1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DOT_DASH_LINE,
		      Color.BLUE, 2); // A-Faults
	private final PlotCurveCharacterstics PLOT_CHAR1_2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DASHED_LINE,
		      Color.BLUE, 2); // A-Faults
	private final PlotCurveCharacterstics PLOT_CHAR1_3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.LINE_AND_CIRCLES,
		      Color.BLUE, 1); // A-Faults
	
	
	protected final PlotCurveCharacterstics PLOT_CHAR2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.LIGHT_GRAY, 2); // B-Faults Char
	private final PlotCurveCharacterstics PLOT_CHAR2_1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DOT_DASH_LINE,
		      Color.LIGHT_GRAY, 2); // B-Faults Char
	private final PlotCurveCharacterstics PLOT_CHAR2_2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DASHED_LINE,
		      Color.LIGHT_GRAY, 2); // B-Faults Char
	private final PlotCurveCharacterstics PLOT_CHAR2_3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.LINE_AND_CIRCLES,
		      Color.LIGHT_GRAY, 1); // B-Faults Char
	
	
	protected final PlotCurveCharacterstics PLOT_CHAR3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.GREEN, 2); // B-Faults GR
	private final PlotCurveCharacterstics PLOT_CHAR3_1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DOT_DASH_LINE,
		      Color.GREEN, 2); // B-Faults GR
	private final PlotCurveCharacterstics PLOT_CHAR3_2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DASHED_LINE,
		      Color.GREEN, 2); // B-Faults GR
	private final PlotCurveCharacterstics PLOT_CHAR3_3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.LINE_AND_CIRCLES,
		      Color.GREEN, 1); // B-Faults GR
	
	protected final PlotCurveCharacterstics PLOT_CHAR10 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.ORANGE, 2); // Non-CA B-Faults
	
	
	
	protected final PlotCurveCharacterstics PLOT_CHAR4 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.BLACK, 2); // Tot MFD
	private final PlotCurveCharacterstics PLOT_CHAR4_1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DOT_DASH_LINE,
		      Color.BLACK, 2); // Tot MFD
	private final PlotCurveCharacterstics PLOT_CHAR4_2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DASHED_LINE,
		      Color.BLACK, 2); // Tot MFD
	private final PlotCurveCharacterstics PLOT_CHAR4_3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.LINE_AND_CIRCLES,
		      Color.BLACK, 1); // Tot MFD
	
	
	protected final PlotCurveCharacterstics PLOT_CHAR5 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.MAGENTA, 2); //background
	private final PlotCurveCharacterstics PLOT_CHAR5_1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DOT_DASH_LINE,
		      Color.MAGENTA, 2); //background
	private final PlotCurveCharacterstics PLOT_CHAR5_2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DASHED_LINE,
		      Color.MAGENTA, 2); //background
	
	protected final PlotCurveCharacterstics PLOT_CHAR6 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.PINK, 2); // C-zone
	
	protected final PlotCurveCharacterstics PLOT_CHAR7 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      Color.RED, 2); // best fit MFD
	protected final PlotCurveCharacterstics PLOT_CHAR8 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.CROSS_SYMBOLS,
		      Color.RED, 5); // observed MFD
	
	protected final PlotCurveCharacterstics PLOT_CHAR9 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      new Color(188, 143, 143), 2); // NSHMP 2002
	
	protected ArrayList funcs;
	protected ArrayList<PlotCurveCharacterstics> plottingFeaturesList = new ArrayList<PlotCurveCharacterstics>();
	private boolean isCumulative;
	private HSSFSheet excelSheet;
	private ArrayList<String> adjustableParamNames;
	private UCERF2_TimeIndependentEpistemicList ucerf2List = new UCERF2_TimeIndependentEpistemicList();
	//	 Eqk Rate Model 2 ERF
	protected UCERF2 ucerf2 = (UCERF2)ucerf2List.getERF(0);
	

	public LogicTreeMFDsPlotter () {
		aFaultMFDsList = new ArrayList<IncrementalMagFreqDist>();
		bFaultCharMFDsList = new ArrayList<IncrementalMagFreqDist>();
		bFaultGRMFDsList = new ArrayList<IncrementalMagFreqDist>();
		nonCA_B_FaultsMFDsList = new ArrayList<IncrementalMagFreqDist>();
		totMFDsList = new ArrayList<IncrementalMagFreqDist>();
		
	}

	
	/**
	 * This method caclulates MFDs for all logic tree branches and saves them to files.
	 * It also generates a metadata excel sheet that contains information about parameter settings
	 * for each logic tree branch.
	 * 
	 * If path is null, default path is used
	 * @param path
	 */
	public void generateMFDsData(String path) {
		if(path==null) path = DEFAULT_PATH;
		HSSFWorkbook wb  = new HSSFWorkbook();
		excelSheet = wb.createSheet();
		HSSFRow row;
		ParameterList adjustableParams = ucerf2.getAdjustableParameterList();
		Iterator it = adjustableParams.getParametersIterator();
		adjustableParamNames = new ArrayList<String>();
		while(it.hasNext()) {
			 ParameterAPI param = (ParameterAPI)it.next();
			 adjustableParamNames.add(param.getName());
		 }
		// add column for each parameter name. Also add a initial blank row for writing figure names
		 row = excelSheet.createRow(0); 
		 for(int i=1; i<=adjustableParamNames.size(); ++i) {
			if(i>0) row.createCell((short)i).setCellValue(adjustableParamNames.get(i-1));
		}
		int colNum = adjustableParams.size()+1;
		// add a row for predicted and observed ratio
		row.createCell((short)(colNum)).setCellValue("M 6.5 pred/obs");
		++colNum;
		row.createCell((short)(colNum)).setCellValue("Weight");
		++colNum;
		row.createCell((short)(colNum)).setCellValue("A-Fault MoRate");
		++colNum;
		row.createCell((short)(colNum)).setCellValue("B-Faults Char MoRate");
		++colNum;
		row.createCell((short)(colNum)).setCellValue("B-Faults GR Mo Rate");
		++colNum;
		row.createCell((short)(colNum)).setCellValue("Non-CA B-Faults Mo Rate");
		++colNum;
		row.createCell((short)(colNum)).setCellValue("C-Zone MoRate");
		++colNum;
		row.createCell((short)(colNum)).setCellValue("Background MoRate");
		++colNum;
		row.createCell((short)(colNum)).setCellValue("Total MoRate");
		calcMFDs();
		saveMFDsToFile(path+A_FAULTS_MFD_FILENAME, this.aFaultMFDsList);
		saveMFDsToFile(path+B_FAULTS_CHAR_MFD_FILENAME, this.bFaultCharMFDsList);
		saveMFDsToFile(path+B_FAULTS_GR_MFD_FILENAME, this.bFaultGRMFDsList);
		saveMFDsToFile(path+NON_CA_B_FAULTS_MFD_FILENAME, this.nonCA_B_FaultsMFDsList);
		saveMFDsToFile(path+TOT_MFD_FILENAME, this.totMFDsList);
		saveMFDToFile(path+NSHMP_02_MFD_FILENAME, Frankel02_AdjustableEqkRupForecast.getTotalMFD_InsideRELM_region());
		// write metadata excel sheet
		try {
			FileOutputStream fileOut = new FileOutputStream(path+METADATA_EXCEL_SHEET);
			wb.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	
	/**
	 * Save MFDs to file
	 *
	 */
	private void saveMFDsToFile(String fileName, ArrayList<IncrementalMagFreqDist> mfdList) {
		try {
			FileWriter fw = new FileWriter(fileName);
			for(int i=0; i<mfdList.size(); ++i) {
				IncrementalMagFreqDist mfd = mfdList.get(i);
				fw.write("#Run "+(i+1)+"\n");
				for(int magIndex=0; magIndex<mfd.getNum(); ++magIndex)
					fw.write(mfd.getX(magIndex)+"\t"+mfd.getY(magIndex)+"\n");
			}
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	

	/**
	 * Save single MFD to file
	 *
	 */
	private void saveMFDToFile(String fileName, IncrementalMagFreqDist mfd) {
		ArrayList<IncrementalMagFreqDist> mfdList = new ArrayList<IncrementalMagFreqDist>();
		mfdList.add(mfd);
		saveMFDsToFile(fileName, mfdList);
	}
	
	/**
	 * Read MFDs from file
	 * 
	 * @param fileName
	 * @param mfdList
	 */
	protected void readMFDsFromFile(String fileName, ArrayList<IncrementalMagFreqDist> mfdList, boolean isNSHMP02) {
		try {
			FileReader fr = new FileReader(fileName);
			BufferedReader br = new BufferedReader(fr);
			String line = br.readLine();
			IncrementalMagFreqDist mfd = null;
			double mag, rate;
			while(line!=null) {
				if(line.startsWith("#")) {
					if(isNSHMP02) mfd = new IncrementalMagFreqDist(4.0, 9.0, 101);
					else mfd = new IncrementalMagFreqDist(getMinMag(), getMaxMag(), getNumMags());
					mfdList.add(mfd);
				} else {
					StringTokenizer tokenizer = new StringTokenizer(line);
					mag = Double.parseDouble(tokenizer.nextToken());
					rate = Double.parseDouble(tokenizer.nextToken());
					//if(!Double.isInfinite(rate))
					mfd.set(mag, rate);
				}
				line = br.readLine();
			}
			br.close();
			fr.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * Min Mag
	 * @return
	 */
	protected double getMinMag() {
		return UCERF2.MIN_MAG;
	}
	
	/**
	 * Max Mag
	 * @return
	 */
	protected double getMaxMag() {
		return UCERF2.MAX_MAG;
	}
	
	/**
	 * Get num Mag
	 * @return
	 */
	protected int getNumMags() {
		return UCERF2.NUM_MAG;
	}
	
	/**
	 * Read single MFD from file
	 * 
	 * @param fileName
	 * @param mfd
	 */
	private IncrementalMagFreqDist readMFDFromFile(String fileName, boolean isNSHMP02) {
		ArrayList<IncrementalMagFreqDist> mfdList = new ArrayList<IncrementalMagFreqDist>();
		readMFDsFromFile(fileName, mfdList, isNSHMP02);
		return mfdList.get(0);
	}
	
	
	
	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getPlottingFeatures()
	 */
	public ArrayList getPlottingFeatures() {
		 return this.plottingFeaturesList;
	}
	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getCurveFunctionList()
	 */
	public ArrayList getCurveFunctionList() {
		return this.funcs;
	}
	
	
	/**
	 * Calculate MFDs
	 * 
	 * @param paramIndex
	 * @param weight
	 */
	private void calcMFDs() {
		double obs6_5CumRate = getObsCumMFD(ucerf2).get(0).getY(6.5);
		int numBranches = ucerf2List.getNumERFs();
		for(int i=0; i<numBranches; ++i) {
			UCERF2 ucerf2 = (UCERF2)ucerf2List.getERF(i);
			 // if it is last paramter in list, save the MFDs
			System.out.println("Doing run "+(aFaultMFDsList.size()+1)+" of "+numBranches);
			//ucerf2.updateForecast();
			aFaultMFDsList.add(getTotal_A_FaultsMFD(ucerf2));
			bFaultCharMFDsList.add(getTotal_B_FaultsCharMFD(ucerf2));
			bFaultGRMFDsList.add(getTotal_B_FaultsGR_MFD(ucerf2));
			this.nonCA_B_FaultsMFDsList.add(getTotal_NonCA_B_FaultsMFD(ucerf2));
			totMFDsList.add(getTotalMFD(ucerf2));
			short colIndex = (short)totMFDsList.size();
			HSSFRow row = this.excelSheet.createRow(colIndex);
			// write to excel sheet
			row.createCell((short)0).setCellValue("Plot "+colIndex);
			ParameterList paramList = ucerf2.getAdjustableParameterList();
			for(int p=0; p<this.adjustableParamNames.size(); ++p) {
				String pName = adjustableParamNames.get(p);
				if(paramList.containsParameter(pName))
					row.createCell((short)(p+1)).setCellValue(paramList.getValue(pName).toString());
			}
			
			int colNum = adjustableParamNames.size()+1;
			// add a row for predicted and observed ratio
			row.createCell((short)(colNum)).setCellValue(getCumRateAt6_5(totMFDsList.get(colIndex-1))/obs6_5CumRate);
			++colNum;
			row.createCell((short)(colNum)).setCellValue(ucerf2List.getERF_RelativeWeight(i));
			++colNum;
			row.createCell((short)(colNum)).setCellValue(aFaultMFDsList.get(colIndex-1).getTotalMomentRate());
			++colNum;
			row.createCell((short)(colNum)).setCellValue(bFaultCharMFDsList.get(colIndex-1).getTotalMomentRate());
			++colNum;
			row.createCell((short)(colNum)).setCellValue(bFaultGRMFDsList.get(colIndex-1).getTotalMomentRate());
			++colNum;
			row.createCell((short)(colNum)).setCellValue(this.nonCA_B_FaultsMFDsList.get(colIndex-1).getTotalMomentRate());
			++colNum;
			row.createCell((short)(colNum)).setCellValue(ucerf2.getTotal_C_ZoneMFD().getTotalMomentRate());
			++colNum;
			row.createCell((short)(colNum)).setCellValue(ucerf2.getTotal_BackgroundMFD().getTotalMomentRate());
			++colNum;
			row.createCell((short)(colNum)).setCellValue(totMFDsList.get(colIndex-1).getTotalMomentRate());
		
		}
	}
	
	/**
	 * Cum rate at 6.5
	 * @param mfd
	 * @return
	 */
	protected double getCumRateAt6_5(IncrementalMagFreqDist mfd) {
		return mfd.getCumRate(6.5+UCERF2.DELTA_MAG/2);
	}
	
	/**
	 * Get Observed Cum MFD
	 * 
	 * @param ucerf2
	 * @return
	 */
	protected  ArrayList<EvenlyDiscretizedFunc> getObsCumMFD(UCERF2 ucerf2) {
		boolean includeAfterShocks = ucerf2.areAfterShocksIncluded();
		return ucerf2.getObsCumMFD(includeAfterShocks);
	}
	

	/**
	 * Get Observed Incr MFD
	 * 
	 * @param ucerf2
	 * @return
	 */
	protected  ArrayList<ArbitrarilyDiscretizedFunc> getObsIncrMFD(UCERF2 ucerf2) {
		boolean includeAfterShocks = ucerf2.areAfterShocksIncluded();
		return ucerf2.getObsIncrMFD(includeAfterShocks);
	}
	
	/**
	 * Get A_Faults MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_A_FaultsMFD(UCERF2 ucerf2) {
		return ucerf2.getTotal_A_FaultsMFD();
	}
	
	/**
	 * Get C-Zones MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_C_ZoneMFD(UCERF2 ucerf2) {
		return ucerf2.getTotal_C_ZoneMFD();
	}
	
	/**
	 * Get Background MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_BackgroundMFD(UCERF2 ucerf2) {
		return ucerf2.getTotal_BackgroundMFD();
	}
	
	
	/**
	 * Get B_Faults Char MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_B_FaultsCharMFD(UCERF2 ucerf2) {
		return ucerf2.getTotal_B_FaultsCharMFD();
	}
	
	/**
	 * Get B_Faults GR MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_B_FaultsGR_MFD(UCERF2 ucerf2) {
		return ucerf2.getTotal_B_FaultsGR_MFD();
	}

	/**
	 * Get Non CA B_Faults MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_NonCA_B_FaultsMFD(UCERF2 ucerf2) {
		return ucerf2.getTotal_NonCA_B_FaultsMFD();
	}
	
	/**
	 * Get Total MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotalMFD(UCERF2 ucerf2) {
		return ucerf2.getTotalMFD();
	}
	
	
	/**
	 * Plot MFDs using Jfreechart.  The boolean "isCumulative" decides whether to plot the
	 * incremental MFDs or the cumulative MFDs.
	 * 
	 * If path is null, default path is used
	 *
	 */
	public void plotMFDs(String path, boolean isCumulative) {
		this.isCumulative = isCumulative;
		if(path==null) path = DEFAULT_PATH;
		readMFDsFromFile(path+A_FAULTS_MFD_FILENAME, this.aFaultMFDsList, false);
		//for(int i=0; i<aFaultMFDsList.size(); ++i)
			//System.out.println(aFaultMFDsList.get(i).getCumRate(6.5));
		readMFDsFromFile(path+B_FAULTS_CHAR_MFD_FILENAME, this.bFaultCharMFDsList, false);
		readMFDsFromFile(path+B_FAULTS_GR_MFD_FILENAME, this.bFaultGRMFDsList, false);
		readMFDsFromFile(path+NON_CA_B_FAULTS_MFD_FILENAME, this.nonCA_B_FaultsMFDsList, false);
		readMFDsFromFile(path+TOT_MFD_FILENAME, this.totMFDsList, false);
		nshmp02TotMFD = readMFDFromFile(path+NSHMP_02_MFD_FILENAME, true);
		ucerf2.updateForecast();
		cZoneMFD = getTotal_C_ZoneMFD(ucerf2);
		bckMFD = getTotal_BackgroundMFD(ucerf2);
		
		// combined Logic Tree MFD
		plotMFDs(null, null, true, true, true, true, true, false);
		
//		 combined Logic Tree MFD comparison with NSHMP2002
		plotMFDs(null, null, false, false, false, false, false, true);
		
		//	Different Fault Models
		String paramName = UCERF2.DEFORMATION_MODEL_PARAM_NAME;
		ArrayList values = new ArrayList();
		values.add("D2.1");
		values.add("D2.4");
		plotMFDs(paramName, values, false, true, false, false, false, false); // plot B-faults only
		
		//	Differemt Def Models
		paramName = UCERF2.DEFORMATION_MODEL_PARAM_NAME;
		values = new ArrayList();
		values.add("D2.1");
		values.add("D2.2");
		values.add("D2.3");
		plotMFDs(paramName, values, true, false, false, false, false, false); // plot A-faults only
		
		// Mag Area Rel
		paramName = UCERF2.MAG_AREA_RELS_PARAM_NAME;
		values = new ArrayList();
		values.add(Ellsworth_B_WG02_MagAreaRel.NAME);
		values.add(HanksBakun2002_MagAreaRel.NAME);
		plotMFDs(paramName, values, true, true, false, false, false, false); // plot both A and B-faults
		
		
		// A-Fault solution type
		paramName = UCERF2.RUP_MODEL_TYPE_NAME;
		values = new ArrayList();
		values.add(UCERF2.SEGMENTED_A_FAULT_MODEL);
		values.add(UCERF2.UNSEGMENTED_A_FAULT_MODEL);
		plotMFDs(paramName, values, true, false, false, false, false, false); // plot A-faults  only
		
		// Aprioti wt param
		paramName = UCERF2.REL_A_PRIORI_WT_PARAM_NAME;
		values = new ArrayList();
		values.add(new Double(1e-4));
		values.add(new Double(1e10));
		plotMFDs(paramName, values, true, false, false, false, false, false); // plot A-faults  only
		

		//	Connect More B-Faults?
		 paramName = UCERF2.CONNECT_B_FAULTS_PARAM_NAME;
		 values = new ArrayList();
		values.add(new Boolean(true));
		values.add(new Boolean(false));
		plotMFDs(paramName, values, false, true, false, false, false, false); // plot B-faults
		
		
		//plotBackgroundEffectsMFDs();
		
//		B-faults b-values
		paramName = UCERF2.B_FAULTS_B_VAL_PARAM_NAME;
		values = new ArrayList();
		values.add(new Double(0.0));
		//plotMFDs(paramName, values, false, true, false, false, false, false); // plot B-faults

//		fraction MoRate to Background
		paramName = UCERF2.ABC_MO_RATE_REDUCTION_PARAM_NAME;
		values = new ArrayList();
		values.add(new Double(0.1));
		//plotMFDs(paramName, values, true, true, false, false, false, false); // plot A & B-faults
	
	}
	
	
	
	/**
	 * @param paramName Param Name whose value needs to remain constant. Can be null 
	 * @param value Param Value for constant paramter. can be null
	 * 
	 * @return
	 */
	private void plotMFDs(String paramName, ArrayList values, boolean showAFaults, boolean showBFaults, boolean showNonCA_B_Faults, 
			boolean showCZones, boolean showBackground, boolean showNSHMP_TotMFD) {
		String metadata;
		SummedMagFreqDist avgTotMFD = doAverageMFDs(showAFaults, showBFaults, showNonCA_B_Faults, showCZones, showBackground, showNSHMP_TotMFD);
		
		PlotCurveCharacterstics plot1, plot2, plot3, plot4;
		for(int i =0; values!=null && i<values.size(); ++i) {
			IncrementalMagFreqDist aFaultMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
			IncrementalMagFreqDist bFaultCharMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
			IncrementalMagFreqDist bFaultGRMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
			IncrementalMagFreqDist nonCA__B_FaultsMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
			IncrementalMagFreqDist totMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
			
			
			if(paramName.equalsIgnoreCase(UCERF2.ABC_MO_RATE_REDUCTION_PARAM_NAME)) {
				ArrayList<IncrementalMagFreqDist> mfds = this.getMFDsWhenBckFrac0_1();
				aFaultMFD = mfds.get(0);
				aFaultMFD.setInfo("A-Faults MFD");
				bFaultCharMFD = mfds.get(1);
				bFaultCharMFD.setInfo("B-Faults Char MFD");
				bFaultGRMFD = mfds.get(2);
				bFaultGRMFD.setInfo("B-Faults GR MFD");
				totMFD = mfds.get(3);
				totMFD.setInfo("Total MFD");
			} else if(paramName.equalsIgnoreCase(UCERF2.B_FAULTS_B_VAL_PARAM_NAME)) {
				ArrayList<IncrementalMagFreqDist> mfds = getMFDsWhenBVal0();
				aFaultMFD = mfds.get(0);
				aFaultMFD.setInfo("A-Faults MFD");
				bFaultCharMFD = mfds.get(1);
				bFaultCharMFD.setInfo("B-Faults Char MFD");
				bFaultGRMFD = mfds.get(2);
				bFaultGRMFD.setInfo("B-Faults GR MFD");
				totMFD = mfds.get(3);
				totMFD.setInfo("Total MFD");
			} else doWeightedSum(paramName, values.get(i), (SummedMagFreqDist)aFaultMFD, (SummedMagFreqDist)bFaultCharMFD, (SummedMagFreqDist)bFaultGRMFD,(SummedMagFreqDist)nonCA__B_FaultsMFD, (SummedMagFreqDist)totMFD);
			
			
			if(i==0) {
				plot1 = PLOT_CHAR1_1;
				plot2 = PLOT_CHAR2_1;
				plot3 = PLOT_CHAR3_1;
				plot4 = PLOT_CHAR4_1;
				metadata="Dotted Dashed Line - ";
			} else if(i==1) {
				plot1 = PLOT_CHAR1_2;
				plot2 = PLOT_CHAR2_2;
				plot3 = PLOT_CHAR3_2;
				plot4 = PLOT_CHAR4_2;
				metadata="Dashed Line - ";
			} else {
				plot1 = PLOT_CHAR1_3;
				plot2 = PLOT_CHAR2_3;
				plot3 = PLOT_CHAR3_3;
				plot4 = PLOT_CHAR4_3;
				metadata="Lines and Circles - ";
			}
			metadata += "("+paramName+"="+values.get(i)+")  ";
			
			if(showAFaults) addToFuncList(aFaultMFD, metadata+"A-Fault MFD", plot1);
			if(showBFaults) addToFuncList(bFaultCharMFD, metadata+"Char B-Fault MFD", plot2);
			if(showBFaults) addToFuncList(bFaultGRMFD, metadata+"GR B-Fault MFD", plot3);
			addToFuncList(totMFD, metadata+"Total MFD, M6.5 Cum Ratio = "+totMFD.getCumRate(6.5+UCERF2.DELTA_MAG/2)/avgTotMFD.getCumRate(6.5+UCERF2.DELTA_MAG/2), plot4);	
		}
		
		GraphWindow graphWindow= new GraphWindow(this);
	    graphWindow.setPlotLabel("Mag Freq Dist");
	    graphWindow.plotGraphUsingPlotPreferences();
	    graphWindow.setVisible(true);
	 }

	/**
	 *  Loop over all logic tree branches and calculated the Average MFD for each source type
	 *  after applying the branch weight.
	 * 
	 * @param showAFaults - Whether to plot Type A Faults
	 * @param showBFaults - Whether to plot Type B faults
	 * @param showNonCA_B_Faults - Whether to plot Non-CA B-Faults
	 * @param showCZones - Whether to plot C Zones
	 * @param showBackground - Whether to plot the background
	 * @param showNSHMP_TotMFD - Whether to show the MFD from NSHMP-2002
	 * @return
	 */
	private SummedMagFreqDist doAverageMFDs(boolean showAFaults, boolean showBFaults, boolean showNonCA_B_Faults, boolean showCZones, boolean showBackground, boolean showNSHMP_TotMFD) {
		funcs  = new ArrayList();
		plottingFeaturesList = new ArrayList<PlotCurveCharacterstics>();
		
		// Avg MFDs
		SummedMagFreqDist avgAFaultMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
		SummedMagFreqDist avgBFaultCharMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
		SummedMagFreqDist avgBFaultGRMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
		SummedMagFreqDist avgNonCA_B_FaultsMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
		SummedMagFreqDist avgTotMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG,UCERF2. NUM_MAG);
		
		doWeightedSum(null, null, avgAFaultMFD, avgBFaultCharMFD, avgBFaultGRMFD, avgNonCA_B_FaultsMFD, avgTotMFD);
		String metadata = "Solid Line-";
		// Add to function list
		if(showAFaults) addToFuncList(avgAFaultMFD, metadata+"Average A-Fault MFD", PLOT_CHAR1);
		if(showBFaults) addToFuncList(avgBFaultCharMFD, metadata+"Average Char B-Fault MFD", PLOT_CHAR2);
		if(showBFaults) addToFuncList(avgBFaultGRMFD,metadata+ "Average GR B-Fault MFD", PLOT_CHAR3);
		if(showNonCA_B_Faults) addToFuncList(avgNonCA_B_FaultsMFD,metadata+ "Average Non-CA B-Fault MFD", PLOT_CHAR10);
		if(showBackground) addToFuncList(this.bckMFD, metadata+"Average Background MFD", PLOT_CHAR5);
		if(showCZones) addToFuncList(this.cZoneMFD, metadata+"Average C-Zones MFD", PLOT_CHAR6);
		if(showNSHMP_TotMFD) { // add NSHMP MFD after resampling for smoothing purposes
			EvenlyDiscretizedFunc nshmpCumMFD = nshmp02TotMFD.getCumRateDistWithOffset();
			
			ArbitrarilyDiscretizedFunc resampledNSHMP_MFD = new ArbitrarilyDiscretizedFunc();
			for(int i=0; i<nshmpCumMFD.getNum(); i=i+2)
				resampledNSHMP_MFD.set(nshmpCumMFD.getX(i), nshmpCumMFD.getY(i));
			
			resampledNSHMP_MFD.setName("NSHMP-2002 Total MFD");
			if(this.isCumulative) {
				funcs.add(resampledNSHMP_MFD);
			} else {
				ArbIncrementalMagFreqDist nshmpIncrMFD = new ArbIncrementalMagFreqDist(UCERF2.MIN_MAG+UCERF2.DELTA_MAG/2, UCERF2.MAX_MAG-UCERF2.DELTA_MAG/2,UCERF2. NUM_MAG-1);
				nshmpIncrMFD.setCumRateDist(resampledNSHMP_MFD);
				funcs.add(nshmpIncrMFD);
			}
			this.plottingFeaturesList.add(PLOT_CHAR9);
		}
		
		//Karen's observed data
		
		ArrayList obsMFD;
		if(this.isCumulative)  {
			obsMFD = getObsCumMFD(ucerf2);
			metadata+="Average Total MFD, M6.5 Cum Ratio = "+avgTotMFD.getCumRate(6.5+UCERF2.DELTA_MAG/2)/((EvenlyDiscretizedFunc)obsMFD.get(0)).getY(6.5);
		}
		else  {
			obsMFD = getObsIncrMFD(ucerf2);
			metadata+="Average Total MFD";
		}
		addToFuncList(avgTotMFD, metadata, PLOT_CHAR4);
		
		
		// historical best fit cum dist
		//funcs.add(eqkRateModel2ERF.getObsBestFitCumMFD(includeAfterShocks));
		funcs.add(obsMFD.get(0));
		this.plottingFeaturesList.add(PLOT_CHAR7);
		// historical cum dist
		funcs.addAll(obsMFD);
		this.plottingFeaturesList.add(PLOT_CHAR8);
		if(obsMFD.size()>1) { // incremental does not have upper and lower bounds
			this.plottingFeaturesList.add(PLOT_CHAR8);
			this.plottingFeaturesList.add(PLOT_CHAR8);
		}
		
		return avgTotMFD;
	}
	
	/**
	 * 
	 * @param mfd
	 */
	private void addToFuncList(IncrementalMagFreqDist mfd, String metadata, 
			PlotCurveCharacterstics curveCharateristic) {
		EvenlyDiscretizedFunc func;
		if(this.isCumulative) func = mfd.getCumRateDistWithOffset();
		else func = mfd;
		func.setName(metadata);
		funcs.add(func);
		this.plottingFeaturesList.add(curveCharateristic);
	}
	 
	
	/**
	 * Do Weighted Sum
	 * 
	 * @param paramIndex
	 * @param paramName
	 * @param value
	 * @param weight
	 * @param aFaultMFD
	 * @param bFaultMFD
	 * @param totMFD
	 */
	protected void doWeightedSum(String constantParamName, Object value,
			SummedMagFreqDist aFaultTotMFD, SummedMagFreqDist bFaultTotCharMFD, SummedMagFreqDist bFaultTotGRMFD, 
			SummedMagFreqDist nonCA_B_FaultsTotMFD, SummedMagFreqDist totMFD) {
		
		int numBranches = ucerf2List.getNumERFs();
		double paramWt = 1;
		if(constantParamName!=null)
			paramWt = ucerf2List.getWtForParamVal(constantParamName,  value);
		for(int i=0; i<numBranches; ++i) {
			ParameterList paramList = ucerf2List.getParameterList(i);
			double wt = ucerf2List.getERF_RelativeWeight(i);
			if(constantParamName!=null && (!paramList.containsParameter(constantParamName)))
				continue;
			if(constantParamName!=null) {
				ParameterAPI param = paramList.getParameter(constantParamName);
				if(!param.getValue().equals(value)) continue;
				wt = wt/paramWt;
			}
			//System.out.println(constantParamName+":"+value+" branch used:"+i+":weight=\t"+wt);
			addMFDs(aFaultTotMFD, aFaultMFDsList.get(i), wt);
			addMFDs(bFaultTotCharMFD, bFaultCharMFDsList.get(i), wt);
			addMFDs(bFaultTotGRMFD, bFaultGRMFDsList.get(i), wt);
			addMFDs(nonCA_B_FaultsTotMFD, this.nonCA_B_FaultsMFDsList.get(i), wt);
			addMFDs(totMFD, totMFDsList.get(i), wt);
			
		}
		
	}
	
	
	/**
	 * Return the MFDs for A-Faults, B-Char, B-GR and Total when B-Fault b-value=0
	 * @return
	 */
	private ArrayList<IncrementalMagFreqDist> getMFDsWhenBVal0() {
		ArrayList<IncrementalMagFreqDist> mfdList = new ArrayList<IncrementalMagFreqDist>();
		readMFDsFromFile(BFAULT_BVAL_PATH+ COMBINED_AVG_FILENAME, mfdList, false);
		return mfdList;
	}
	
	/**
	 * Return the MFDs for A-Faults, B-Char, B-GR and Total when 
	 * Fraction MoRate to Bck = 0.1
	 * @return
	 */
	private ArrayList<IncrementalMagFreqDist> getMFDsWhenBckFrac0_1() {
		ArrayList<IncrementalMagFreqDist> mfdList = new ArrayList<IncrementalMagFreqDist>();
		readMFDsFromFile(BCK_FRAC_PATH+ COMBINED_AVG_FILENAME, mfdList, false);
		return mfdList;
	}
	
	
	
	/**
	 * Add source MFD to Target MFD after applying the  weight
	 * @param targetMFD
	 * @param sourceMFD
	 * @param wt
	 */
	private void addMFDs(SummedMagFreqDist targetMFD, IncrementalMagFreqDist sourceMFD, double wt) {
		for(int i=0; i<sourceMFD.getNum(); ++i) {
			targetMFD.add(sourceMFD.getX(i), wt*sourceMFD.getY(i));
		}
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
		return true;
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
		if(this.isCumulative)	return CUM_Y_AXIS_LABEL;
		else return INCR_Y_AXIS_LABEL;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#isCustomAxis()
	 */
	public boolean isCustomAxis() {
		return true;
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinX()
	 */
	public double getMinX() {
		return 5.0;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxX()
	 */
	public double getMaxX() {
		return 9.255;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMinY()
	 */
	public double getMinY() {
		return 1e-4;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}

	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getMaxY()
	 */
	public double getMaxY() {
		return 10;
		//throw new UnsupportedOperationException("Method not implemented yet");
	}
	
	
	public static void main(String []args) {
		 LogicTreeMFDsPlotter  logicTreeMFDsPlotter = new LogicTreeMFDsPlotter();
		 //logicTreeMFDsPlotter.generateMFDsData(null);
		 logicTreeMFDsPlotter.plotMFDs(null, true);
		 //logicTreeMFDsPlotter.plotMFDs(null, false);
		
		//LogicTreeMFDsPlotter mfdPlotter = new LogicTreeMFDsPlotter(true);
		//mfdPlotter.plotMFDs();
		//System.out.println(mfdPlotter.getMFDs(null, null).get(3).toString());
	}
}


