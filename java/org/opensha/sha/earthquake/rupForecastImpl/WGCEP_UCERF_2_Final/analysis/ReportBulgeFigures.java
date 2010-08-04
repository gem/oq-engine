/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.analysis;

import java.io.FileOutputStream;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.Iterator;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFCellStyle;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.ParameterListParameter;
import org.opensha.commons.param.StringConstraint;
import org.opensha.commons.param.StringParameter;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.gui.EqkRateModel2_MFDsPlotter;
import org.opensha.sha.gui.infoTools.GraphWindow;

/**
 * This class tries various parameter settings in UCERF2 and finds the effect of each parameter on Bulge
 * @author vipingupta
 *
 */
public class ReportBulgeFigures {
	private String dirName;
	private UCERF2 ucerf2;


	public ReportBulgeFigures() {
		ucerf2 = new UCERF2();
	}

	public ReportBulgeFigures(UCERF2 ucerf2) {
		this.ucerf2 = ucerf2;
	}

	/**
	 * Generate figures for analysis
	 * @param dirName
	 */
	public  void generateAnalysisFigures(String dirName) {
		ArrayList<String> paramNames = new ArrayList<String>();
		// remove parameter listeners
		ParameterList paramList = ucerf2.getAdjustableParameterList();
		Iterator it = paramList.getParametersIterator();
		while(it.hasNext()) {
			ParameterAPI param = (ParameterAPI)it.next();
			paramNames.add(param.getName());
		}

		HSSFWorkbook wb  = new HSSFWorkbook();
		HSSFSheet sheet = wb.createSheet();
		HSSFRow row;
		// add row for each parameter name. Also add a initial blank row for writing figure names
		for(int i=0; i<=paramNames.size(); ++i) {
			row = sheet.createRow(i); 
			if(i>0) row.createCell((short)0).setCellValue(paramNames.get(i-1));
		}
		// add a row for predicted and observed ratio
		sheet.createRow(paramNames.size()+1).createCell((short)0).setCellValue("M 6.5 pred/obs");


		this.dirName=dirName;
		ucerf2.setParamDefaults();

		// figure 1 with defaults
		int fig=1;
		ucerf2.updateForecast();
		makeMFDsPlot("plot"+fig, ucerf2);
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		for(int i=0; i<paramNames.size(); ++i) {
			if(paramNames.get(i).equalsIgnoreCase(UCERF2.SEGMENTED_RUP_MODEL_TYPE_NAME))
				sheet.getRow(i+1).createCell((short)fig).setCellValue("Geological Insight");
			else	 sheet.getRow(i+1).createCell((short)fig).setCellValue(paramList.getValue(paramNames.get(i)).toString());			 
		}
		double obsVal = ucerf2.getObsCumMFD(ucerf2.areAfterShocksIncluded()).get(0).getInterpolatedY(6.5);
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));

		// figure 2 (Deformation Model set to 2.2)
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue("D2.2");
		ucerf2.updateForecast();
		makeMFDsPlot("plot"+fig, ucerf2);
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.DEFORMATION_MODEL_PARAM_NAME)).createCell((short)fig).setCellValue("D2.2");
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		
		// figure 3 (Deformation Model set to 2.3)
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue("D2.3");
		ucerf2.updateForecast();
		makeMFDsPlot("plot"+fig, ucerf2);
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.DEFORMATION_MODEL_PARAM_NAME)).createCell((short)fig).setCellValue("D2.3");
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		
		// figure 4 (Deformation Model set to 2.4)
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue("D2.4");
		ucerf2.updateForecast();
		makeMFDsPlot("plot"+fig, ucerf2);
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.DEFORMATION_MODEL_PARAM_NAME)).createCell((short)fig).setCellValue("D2.4");
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		
		// figure 5 (Deformation Model set to 2.5)
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue("D2.5");
		ucerf2.updateForecast();
		makeMFDsPlot("plot"+fig, ucerf2);
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.DEFORMATION_MODEL_PARAM_NAME)).createCell((short)fig).setCellValue("D2.5");
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		
		
		// figure 6 (Deformation Model set to 2.6)
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).setValue("D2.6");
		ucerf2.updateForecast();
		makeMFDsPlot("plot"+fig, ucerf2);
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.DEFORMATION_MODEL_PARAM_NAME)).createCell((short)fig).setCellValue("D2.6");
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		

		// figure 7 (Unsegmented A-Faults)
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.RUP_MODEL_TYPE_NAME).setValue(UCERF2.UNSEGMENTED_A_FAULT_MODEL);
		ucerf2.updateForecast();
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.RUP_MODEL_TYPE_NAME)).createCell((short)fig).setCellValue(UCERF2.UNSEGMENTED_A_FAULT_MODEL);
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		makeMFDsPlot("plot"+fig, ucerf2);

		//		 figure 8
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME).setValue(new Double(1e7));
		ucerf2.updateForecast();
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.REL_A_PRIORI_WT_PARAM_NAME)).createCell((short)fig).setCellValue("1e7");
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		makeMFDsPlot("plot"+fig, ucerf2);

		//		 figure 9 (Hans and Bakun Mag Area Relationship)
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(HanksBakun2002_MagAreaRel.NAME);
		ucerf2.updateForecast();
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.MAG_AREA_RELS_PARAM_NAME)).createCell((short)fig).setCellValue(HanksBakun2002_MagAreaRel.NAME);
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		makeMFDsPlot("plot"+fig, ucerf2);

		//		 figure 6
		/*++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.MEAN_MAG_CORRECTION).setValue(new Double(-0.1));
		ucerf2.updateForecast();
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.MEAN_MAG_CORRECTION)).createCell((short)fig).setCellValue(-0.1);
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		makeMFDsPlot("plot"+fig, ucerf2);

		//		 figure 7
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.MEAN_MAG_CORRECTION).setValue(new Double(0.1));
		ucerf2.updateForecast();
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.MEAN_MAG_CORRECTION)).createCell((short)fig).setCellValue(0.1);
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		makeMFDsPlot("plot"+fig, ucerf2);*/

		//		 figure 10 (More B-Faults not connected)
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.CONNECT_B_FAULTS_PARAM_NAME).setValue(new Boolean(false));
		ucerf2.updateForecast();
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.CONNECT_B_FAULTS_PARAM_NAME)).createCell((short)fig).setCellValue("False");
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		makeMFDsPlot("plot"+fig, ucerf2);

		//		 figure 9
		/*++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.C_ZONE_WT_PARAM_NAME).setValue(new Double(0.0));
		ucerf2.updateForecast();
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.C_ZONE_WT_PARAM_NAME)).createCell((short)fig).setCellValue(0.0);
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		makeMFDsPlot("plot"+fig, ucerf2);

		//		 figure 10
		++fig;
		ucerf2.setParamDefaults();
		ucerf2.getParameter(UCERF2.C_ZONE_WT_PARAM_NAME).setValue(new Double(1.0));
		ucerf2.updateForecast();
		sheet.getRow(0).createCell((short)fig).setCellValue("Figure "+fig);
		sheet.getRow(1+paramNames.indexOf(UCERF2.C_ZONE_WT_PARAM_NAME)).createCell((short)fig).setCellValue(1.0);
		sheet.getRow(paramNames.size()+1).createCell((short)fig).setCellValue((ucerf2.getTotalMFD().getCumRate(6.5)/obsVal));
		makeMFDsPlot("plot"+fig, ucerf2);*/


		// wrap cell style
		HSSFCellStyle wrapCellStyle = wb.createCellStyle();
		wrapCellStyle.setWrapText(true);
		for(int rowCount=0; rowCount<=sheet.getLastRowNum(); ++rowCount) {
			for(int colCount=0; colCount<=fig; ++colCount) {
				HSSFCell cell = sheet.getRow(rowCount).getCell((short)colCount);
				if(cell==null) continue;
				cell.setCellStyle(wrapCellStyle);
			}
		}

		//ucerf2.setParamDefaults();

		try {
			FileOutputStream fileOut = new FileOutputStream(dirName+"/Table_For_Figures.xls");
			wb.write(fileOut);
			fileOut.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Plot MFDs
	 * @param fileName
	 */
	private void makeMFDsPlot(String fileName, UCERF2 ucerf2) {
		EqkRateModel2_MFDsPlotter mfdsPlotter = new EqkRateModel2_MFDsPlotter(ucerf2, true);
		GraphWindow graphWindow= new GraphWindow(mfdsPlotter);
		graphWindow.setPlotLabel("Cum Mag Freq Dist");
		graphWindow.plotGraphUsingPlotPreferences();
		graphWindow.setVisible(true);
		try {
			graphWindow.saveAsPNG(dirName+"/"+fileName+".png");
		}catch(Exception e) {
			e.printStackTrace();
		}

	}



	//private void printMag6_5_discrepancies() {
	//throw new RuntimeException ("Method unsupported exception");
	/*ArrayList magAreaOptions = ((StringConstraint)magAreaRelParam.getConstraint()).getAllowedStrings();
		ArrayList rupModelOptions = ((StringConstraint)rupModelParam.getConstraint()).getAllowedStrings();
		ArrayList slipModelOptions = ((StringConstraint)slipModelParam.getConstraint()).getAllowedStrings();
		double obVal = this.getObsBestFitCumMFD(true).getY(6.5);
		for(int imag=0; imag<magAreaOptions.size();imag++)
			for(int irup=0; irup<rupModelOptions.size();irup++)
					for(int islip=0; islip<slipModelOptions.size();islip++) {
						magAreaRelParam.setValue(magAreaOptions.get(imag));
						rupModelParam.setValue(rupModelOptions.get(irup));
						slipModelParam.setValue(slipModelOptions.get(islip));
						try {
							updateForecast();
						}catch(Exception e) {
							System.out.println(e.getMessage()+" , "+magAreaOptions.get(imag)+
									" , " + rupModelOptions.get(irup) +
									" , " + slipModelOptions.get(islip));
							continue;
						}
						// print out pred rate of M�6.5 and ratio with respect to obsBestFitCumMFD at same mag
						double predCumRate = getTotalMFD().getCumRate(6.5);

						System.out.println((float)(predCumRate/obVal)+" , "+(float)predCumRate+" , "+magAreaOptions.get(imag)+
								" , " + rupModelOptions.get(irup) +
								" , " + slipModelOptions.get(islip));
						//System.out.println("display CASE_"+imag+"_"+irup+"_"+islip);

					}*/
	//}

	/**
	 * It tries various parameter settings (Various combination of values for Mag Area Relationship,
	 * Rup Models, Slip Models, %Char vs GR, % moment rate reduction) and tries to find minimum bulge
	 *
	 */
	public void findMinBulge() {
		// use this
//		this.relativeSegRateWeightParam.setValue(1.0);
//		String filename = "Bulge_1.txt";
		// or this
		ucerf2.getParameter(UCERF2.REL_SEG_RATE_WT_PARAM_NAME).setValue(0.0);
		String filename = "Bulge_0.txt";
		StringParameter magAreaRelParam = (StringParameter)ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME);
		StringParameter slipModelParam = (StringParameter)ucerf2.getParameter(UCERF2.SLIP_MODEL_TYPE_NAME);
		ParameterListParameter segmentedRupModelParam = (ParameterListParameter)ucerf2.getParameter(UCERF2.SEGMENTED_RUP_MODEL_TYPE_NAME);
		ArrayList magAreaOptions = ((StringConstraint)magAreaRelParam.getConstraint()).getAllowedStrings();
		ArrayList slipModelOptions = ((StringConstraint)slipModelParam.getConstraint()).getAllowedStrings();
		// set the following two and use moRateFracToBackgroundParam as proxy for all
		ucerf2.getParameter(UCERF2.AFTERSHOCK_FRACTION_PARAM_NAME).setValue(0.0);
		ucerf2.getParameter(UCERF2.COUPLING_COEFF_PARAM_NAME).setValue(1);
		double obVal = ucerf2.getObsCumMFD(false).get(0).getY(6.5);
		double minRatio = 10, ratio;
		String str="", minStr="";
		try {
			FileWriter fw = new FileWriter(filename);
			//int imag=1;
			String bVal1 = "default";
			String bVal2 = "default";
			for(int imag=0; imag<magAreaOptions.size();imag++) {
				String[] models = {"Geological Insight", "Min Rate", "Max Rate"};
				for(int irup=0; irup<3;irup++) {
					Iterator it = segmentedRupModelParam.getParametersIterator();
					while(it.hasNext()) { // set the specfiied rup model in each A fault
						StringParameter param = (StringParameter)it.next();
						ArrayList<String> allowedVals = param.getAllowedStrings();
						param.setValue(allowedVals.get(irup));
					}
					for(int islip=0; islip<slipModelOptions.size();islip++) {
						for(double per=0.0; per<=100; per+=33.3) { // % char vs GR
//							for(double bVal1=0.8; bVal1<=1.2; bVal1+=0.1)  // b faults B val
//							for(double bVal2=0.8; bVal2<=1.2; bVal2+=0.1) // bacgrd B val
							for(double frac=0.0; frac<=0.5; frac+=0.15){ // moment rate reduction
								ucerf2.getParameter(UCERF2.MAG_AREA_RELS_PARAM_NAME).setValue(magAreaOptions.get(imag));
								ucerf2.getParameter(UCERF2.SLIP_MODEL_TYPE_NAME).setValue(slipModelOptions.get(islip));
								ucerf2.getParameter(UCERF2.ABC_MO_RATE_REDUCTION_PARAM_NAME).setValue(frac);
								ucerf2.getParameter(UCERF2.CHAR_VS_GR_PARAM_NAME).setValue(per);
								try {
									ucerf2.updateForecast();
								}catch(Exception e) {
									System.out.println(e.getMessage()+" , "+magAreaOptions.get(imag)+
											" , " + models[irup] +
											" , " + slipModelOptions.get(islip));
									continue;
								}
								// print out pred rate of M�6.5 and ratio with respect to obsBestFitCumMFD at same mag
								double predCumRate = ucerf2.getTotalMFD().getCumRate(6.5);
								ratio = (predCumRate/obVal);
								str = (float)(predCumRate/obVal)+" , "+(float)predCumRate+" , "+magAreaOptions.get(imag)+
								" , " + models[irup] +
								" , " + slipModelOptions.get(islip)+","+per+","+bVal1+","+
								bVal2+","+frac;
								//System.out.println(str);
								fw.write(str+"\n");
								if(ratio<minRatio) {
									minRatio = ratio;
									minStr = str;
								}

							}
						}
						System.out.println(str);
					}
				}
			}
			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
		System.out.println(minRatio+"------"+minStr);
	}


	public static void main(String []args) {
		new ReportBulgeFigures();
		//bulgeFigures.generateAnalysisFigures("BulgeFigures");
		//bulgeFigures.findMinBulge();
	}

}
