/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.gui;

import java.awt.Color;
import java.io.File;
import java.io.FileInputStream;
import java.util.ArrayList;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.poifs.filesystem.POIFSFileSystem;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.GraphWindowAPI;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;

/**
 * @author vipingupta
 *
 */
public class CreatePlotFromMagRateFile implements GraphWindowAPI {
	
	private final static String X_AXIS_LABEL = "Index";
	private final static String Y_AXIS_LABEL = "Rate";
	private final static String PLOT_LABEL = "Rates";
	private ArrayList funcs;
	private final static String[] names = {"A-Priori Rates", "Char Rate", 
		"Ellsworth-A_Uniform/Boxcar", "Ellsworth-A_WGCEP-2002", "Ellsworth-A_Tapered",
		"Ellsworth-B_Uniform/Boxcar", "Ellsworth-B_WGCEP-2002", "Ellsworth-B_Tapered",
		"Hanks & Bakun (2002)_Uniform/Boxcar", "Hanks & Bakun (2002)_WGCEP-2002", "Hanks & Bakun (2002)_Tapered",
		"Somerville (2006)_Uniform/Boxcar", "Somerville (2006)_WGCEP-2002", "Somerville (2006)_Tapered"};
	
	private final PlotCurveCharacterstics PLOT_CHAR1 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
		      new Color(0,0,0), 4); // black
	private final PlotCurveCharacterstics PLOT_CHAR4 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(192,192,192), 2); // silver grey
	private final PlotCurveCharacterstics PLOT_CHAR3 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(128,0,0), 2); // maroon
	private final PlotCurveCharacterstics PLOT_CHAR2 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(255,0,0), 2); //red
	private final PlotCurveCharacterstics PLOT_CHAR5 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(128,0,128), 2); // purple
	private final PlotCurveCharacterstics PLOT_CHAR6 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(255,0,255), 2); // fuchisia
	private final PlotCurveCharacterstics PLOT_CHAR7 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(0,255,0), 4); //geen
	private final PlotCurveCharacterstics PLOT_CHAR8 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(0,255,0), 2); //lime
	private final PlotCurveCharacterstics PLOT_CHAR9 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(128,128,0), 2); //olive
	private final PlotCurveCharacterstics PLOT_CHAR10 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(255,255,0), 2); //yellow
	private final PlotCurveCharacterstics PLOT_CHAR11 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(0,0,128), 2); //navy
	private final PlotCurveCharacterstics PLOT_CHAR12 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(0,0,255), 2); // blue
	private final PlotCurveCharacterstics PLOT_CHAR13 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(0,128,128), 2); //teal
 	private final PlotCurveCharacterstics PLOT_CHAR14 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,
			new Color(0,255,255), 2); //aqua
	//private final PlotCurveCharacterstics PLOT_CHAR9 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.DASHED_LINE,
		//      Color.RED, 5);
	//private final PlotCurveCharacterstics PLOT_CHAR10 = new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.CROSS_SYMBOLS,
		//      Color.RED, 5);
 	private boolean yLog = false;
	
	public CreatePlotFromMagRateFile(ArrayList funcList) {
		funcs = funcList;
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

	public void setYLog(boolean yLog) {
		this.yLog = yLog;
	}
	
	/* (non-Javadoc)
	 * @see org.opensha.sha.gui.infoTools.GraphWindowAPI#getYLog()
	 */
	public boolean getYLog() {
		return yLog;
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
	public ArrayList getPlottingFeatures() {
		 ArrayList list = new ArrayList();
		 int numFuncs = funcs.size();
		 if(numFuncs>0) list.add(this.PLOT_CHAR7);
		 if(numFuncs>1) list.add(this.PLOT_CHAR1);
		 if(numFuncs>2) list.add(this.PLOT_CHAR3);
		 if(numFuncs>3) list.add(this.PLOT_CHAR4);
		 if(numFuncs>4) list.add(this.PLOT_CHAR5);
		 if(numFuncs>5) list.add(this.PLOT_CHAR6);
		 if(numFuncs>6) list.add(this.PLOT_CHAR2);
		 if(numFuncs>7) list.add(this.PLOT_CHAR8);
		 if(numFuncs>8) list.add(this.PLOT_CHAR9);
		 if(numFuncs>9) list.add(this.PLOT_CHAR10);
		 if(numFuncs>10) list.add(this.PLOT_CHAR11);
		 if(numFuncs>11) list.add(this.PLOT_CHAR12);
		 if(numFuncs>12) list.add(this.PLOT_CHAR13);
		 if(numFuncs>13) list.add(this.PLOT_CHAR14);
		 return list;
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
	
	
	/**
	 * It creates plots and saves PDFs in A_FaultRupRatesPlots_2_1 subdirectory in masterDirectory
	 * @param masterDirName MasterDirectoty where A_FaultRupRatesPlots_2_1 will be created
	 * @param excelSheetName Absolute pathname to excel file
	 */
	public static void createPlots(String masterDirName, String excelSheetName) {
		try {
			// directory to save the PDF files. Directory will be created if it does not exist already
			String dirName = masterDirName+"/A_FaultRupRatesPlots_2_1/";
			File file = new File(dirName);
			if(!file.isDirectory()) { // create directory if it does not exist already
				file.mkdir();
			}
			// read the mag rates file
			POIFSFileSystem fs = new POIFSFileSystem(new FileInputStream(excelSheetName));
			HSSFWorkbook wb = new HSSFWorkbook(fs);
			String[] models = {"Geological Insight", "Min Rate", "Max Rate"};
			for(int i=1; i<(wb.getNumberOfSheets()-2); ++i) { // do not plot the general prediction error, metadata, total rates
				HSSFSheet sheet = wb.getSheetAt(i);
				String sheetName = wb.getSheetName(i);
				int lastIndex = sheet.getLastRowNum();
				int r = 3;
				int count=0;
				// read data for each row
				for(; r<=lastIndex && count<3; ++r) {
					int j=-1;
					String modelType = models[count++];
					ArrayList funcList = new ArrayList();
					for(int k=0; k<14; ++k) {
						ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
						func.setName(names[k]);
						funcList.add(func);
					}
					while(true) {
						++j;
						HSSFRow row = sheet.getRow(r);
						HSSFCell cell = row.getCell( (short) 0);
						// rup name
						String rupName = cell.getStringCellValue().trim();
						if(rupName.equalsIgnoreCase("Totals")) {
							r= r+5;
							GraphWindow graphWindow= new GraphWindow(new CreatePlotFromMagRateFile(funcList));
							graphWindow.setPlotLabel(PLOT_LABEL);
							graphWindow.plotGraphUsingPlotPreferences();
							graphWindow.setTitle(sheetName+" "+modelType);
							graphWindow.pack();
							graphWindow.setVisible(true);
							graphWindow.saveAsPDF(dirName+sheetName+" "+modelType+".pdf");
							break;
						}
						//System.out.println(r);
						((ArbitrarilyDiscretizedFunc)funcList.get(0)).set((double)j, row.getCell( (short) 1).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(1)).set((double)j, row.getCell( (short) 3).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(2)).set((double)j, row.getCell( (short) 5).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(3)).set((double)j, row.getCell( (short) 6).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(4)).set((double)j, row.getCell( (short) 7).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(5)).set((double)j, row.getCell( (short) 9).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(6)).set((double)j, row.getCell( (short) 10).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(7)).set((double)j, row.getCell( (short) 11).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(8)).set((double)j, row.getCell( (short) 13).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(9)).set((double)j, row.getCell( (short) 14).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(10)).set((double)j, row.getCell( (short) 15).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(11)).set((double)j, row.getCell( (short) 17).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(12)).set((double)j, row.getCell( (short) 18).getNumericCellValue());
						((ArbitrarilyDiscretizedFunc)funcList.get(13)).set((double)j, row.getCell( (short) 19).getNumericCellValue());
						++r;
					}
					
					
				}
			}
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
}
