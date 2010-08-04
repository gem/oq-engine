/**
 * 
 */
package org.opensha.refFaultParamDb.gui.view;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.util.ArrayList;

import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.refFaultParamDb.dao.db.DB_AccessAPI;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.DeformationModelPrefDataDB_DAO;
import org.opensha.refFaultParamDb.gui.infotools.GUI_Utils;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.gui.infoTools.CalcProgressBar;

/**
 * @author vipingupta
 *
 */
public class DeformationModelFileWriter implements Runnable {
	private DeformationModelPrefDataDB_DAO deformationModelPrefDAO;
	private CalcProgressBar progressBar;
	private int totSections;
	private int currSection;
	private HSSFWorkbook wb;
	private HSSFSheet excelSheet;
	private int rowNum;
	private boolean createExcelSheet;
	
	public DeformationModelFileWriter(DB_AccessAPI dbConnection) {
		deformationModelPrefDAO = new DeformationModelPrefDataDB_DAO(dbConnection);
	}
	
	/**
	 * Write FaultSectionPrefData to file.
	 * @param faultSectionIds  array of faultsection Ids
	 * 
	 * It creates an excel sheet as well if createExcelSheet is set as true. Excel sheet format is 
	 * as requested by Ray Weldon in his email on June 26, 2007 at 1:39 PM
	 * @param file
	 */
	public void writeForDeformationModel(int deformationModelId, File file, boolean createExcelSheet) {
		try {
			this.createExcelSheet = createExcelSheet;
			if(createExcelSheet) {
				wb  = new HSSFWorkbook();
				excelSheet  = wb.createSheet();
			}
			currSection=0;
			ArrayList faultSectionIds = deformationModelPrefDAO.getFaultSectionIdsForDeformationModel(deformationModelId);
			totSections = faultSectionIds.size();
			// make JProgressBar
			progressBar = new CalcProgressBar("Writing to file", "Writing Fault sections");
			progressBar.displayProgressBar();
			Thread t = new Thread(this);
			t.start();
			// write to file
			FileWriter fw = new FileWriter(file);
			fw.write(getFormatStringForDeformationModel());
			for(currSection=0; currSection<totSections; ++currSection) {
				//System.out.println(currSection);
				writeForDeformationModel(deformationModelId, 
						((Integer)faultSectionIds.get(currSection)).intValue(), 
						fw);
			}
			fw.close();
			
			// write to Excel sheet
			if(createExcelSheet) {
				FileOutputStream fileOut = new FileOutputStream(file.getAbsolutePath().replaceFirst(".txt", ".xls"));
				wb.write(fileOut);
				fileOut.close();
			}
			
			
			// dispose the progressbar
			progressBar.showProgress(false);
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	public void run() {
		try {
			while(currSection<totSections) {
				//System.out.println("Updating "+currSection+ " of "+totSections);
				progressBar.updateProgress(this.currSection, this.totSections);
				Thread.currentThread().sleep(500);
			}
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * Write FaultSectionPrefData to the file. It does not contain slip rate and aseismic slip factor
	 * @param faultSectionId Fault section Id for which data needs to be written to file
	 * @param fw
	 */
	public  void writeForDeformationModel(int deformationModelId, int faultSectionId, FileWriter fw) {
		try{
			FaultSectionPrefData faultSectionPrefData = deformationModelPrefDAO.getFaultSectionPrefData(deformationModelId, faultSectionId);
			writeForDeformationModel(faultSectionPrefData, fw);
			if(this.createExcelSheet) writeToExcelSheet(faultSectionPrefData);
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	
	/**
	 * Write to excel sheet
	 * 
	 * @param faultSectionPrefData
	 */
	private void writeToExcelSheet(FaultSectionPrefData faultSectionPrefData) {
		HSSFRow row = this.excelSheet.createRow(rowNum);
		int colIndex=0;
		if(this.rowNum==0) {
			row.createCell((short)colIndex).setCellValue("Section Name");
			++colIndex;
			
			row.createCell((short)colIndex).setCellValue("Ave Strike -  LocationVector from the first to the last point on fault trace");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Dip (degrees)");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Slip Rate (mm/yr)");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Aseismic Slip Factor");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Rake");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Upper Seis Depth (km)");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Lower Seis Depth (km)");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Length (km)");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Down Dip Width (km)");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Area (sq. km)");
			++colIndex;
			row.createCell((short)colIndex).setCellValue("Num Fault Trace Locations");
			++colIndex;
			++rowNum;
			row = this.excelSheet.createRow(rowNum);
		}
		FaultTrace faultTrace  = faultSectionPrefData.getFaultTrace();
		int numLocations = faultTrace.getNumLocations();
		colIndex= 0;
		row.createCell((short)colIndex).setCellValue(faultSectionPrefData.getSectionName());
		++colIndex;
		double strike = LocationUtils.vector(faultTrace.get(0), faultTrace.get(numLocations-1)).getAzimuth();
		row.createCell((short)colIndex).setCellValue(strike);
		++colIndex;
		row.createCell((short)colIndex).setCellValue(getValue(faultSectionPrefData.getAveDip()));
		++colIndex;
		row.createCell((short)colIndex).setCellValue(getValue(faultSectionPrefData.getAveLongTermSlipRate()));
		++colIndex;
		row.createCell((short)colIndex).setCellValue(getValue(faultSectionPrefData.getAseismicSlipFactor()));
		++colIndex;
		row.createCell((short)colIndex).setCellValue(getValue(faultSectionPrefData.getAveRake()));
		++colIndex;
		row.createCell((short)colIndex).setCellValue(getValue(faultSectionPrefData.getAveUpperDepth()));
		++colIndex;
		row.createCell((short)colIndex).setCellValue(getValue(faultSectionPrefData.getAveLowerDepth()));
		++colIndex;
		row.createCell((short)colIndex).setCellValue(faultSectionPrefData.getLength());
		++colIndex;
		row.createCell((short)colIndex).setCellValue(faultSectionPrefData.getDownDipWidth());
		++colIndex;
		row.createCell((short)colIndex).setCellValue(faultSectionPrefData.getLength()*faultSectionPrefData.getDownDipWidth());
		++colIndex;
		
		row.createCell((short)colIndex).setCellValue(numLocations);
		for(int i=0; i<numLocations; ++i) {
			Location loc = faultTrace.get(i);
			++colIndex;
			row.createCell((short)colIndex).setCellValue(loc.getLatitude());
			++colIndex;
			row.createCell((short)colIndex).setCellValue(loc.getLongitude());
		}
		++colIndex;
		++rowNum;
	}
	
	/**
	 * Write FaultSectionPrefData to the file. It also contains slip rate and aseismic slip factor
	 * @param faultSectionPrefData
	 * @param fw
	 */
	public  void writeForDeformationModel(FaultSectionPrefData faultSectionPrefData, FileWriter fw) {
		try{
			fw.write(getStringForDeformationModel(faultSectionPrefData));
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	/**
	 * Get String for faultSectionPrefData ( including slip rate and aseismic slip factor)
	 * @param faultSectionPrefData
	 * @return
	 */
	public  String getStringForDeformationModel(FaultSectionPrefData faultSectionPrefData) {
		FaultTrace faultTrace = faultSectionPrefData.getFaultTrace(); 
		String str =  "#"+faultSectionPrefData.getSectionName()+"\n"+
		    getValue(faultSectionPrefData.getShortName())+"\n"+
			getValue(faultSectionPrefData.getAveUpperDepth())+"\n"+
			getValue(faultSectionPrefData.getAveLowerDepth())+"\n"+
			getValue(faultSectionPrefData.getAveDip()) +"\n"+
			getValue(faultSectionPrefData.getDipDirection())+"\n"+
			getValue(faultSectionPrefData.getAveLongTermSlipRate())+"\n"+
			getValue(faultSectionPrefData.getAseismicSlipFactor())+"\n"+
			getValue(faultSectionPrefData.getAveRake())+"\n"+
			getValue(faultTrace.getTraceLength())+"\n"+
			faultTrace.getNumLocations()+"\n";
		// write all the point on the fault section trace
		for(int i=0; i<faultTrace.getNumLocations(); ++i)
			str+=(float)faultTrace.get(i).getLatitude()+"\t"+(float)faultTrace.get(i).getLongitude()+"\n";
		return str;
	}
	
	private  String getValue(double val) {
		if(Double.isNaN(val)) return "Not Available";
		else return GUI_Utils.decimalFormat.format(val);
	}
	
	private String getValue(String val) {
		if(val==null || val.equalsIgnoreCase("")) return "Not Available";
		else return val;
	}
	
	/**
	 * File format for writing fault sections in a deformation model file.
	 * Fault sections within a deformation model have slip rate and aseismic slip factor as well
	 *  
	 * @return
	 */
	public  String getFormatStringForDeformationModel() {
		return "********************************\n"+ 
			"#Section Name\n"+
			"#Short Name\n"+
			"#Ave Upper Seis Depth (km)\n"+
			"#Ave Lower Seis Depth (km)\n"+
			"#Ave Dip (degrees)\n"+
			"#Ave Dip LocationVector\n"+
			"#Ave Long Term Slip Rate\n"+
			"#Ave Aseismic Slip Factor\n"+
			"#Ave Rake\n"+
			"#Trace Length (derivative value) (km)\n"+
			"#Num Trace Points\n"+
			"#lat1 lon1\n"+
			"#lat2 lon2\n"+
			"********************************\n";
	}
}
