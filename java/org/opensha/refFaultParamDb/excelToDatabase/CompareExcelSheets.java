/**
 * 
 */
package org.opensha.refFaultParamDb.excelToDatabase;

import java.io.FileInputStream;
import java.io.FileWriter;
import java.util.HashMap;
import java.util.Iterator;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.poifs.filesystem.POIFSFileSystem;

/**
 * It compares the excel sheets that are generated for deformation modelers. It can be used
 * to compare different versions of the sheets and find the changes from the previous version.
 * 
 * @author vipingupta
 *
 */
public class CompareExcelSheets {
	private final static String EXCEL_SHEET1 = "org/opensha/refFaultParamDb/excelToDatabase/PaleoSites_2007_02_Bird.xls";
	private final static String EXCEL_SHEET2 = "org/opensha/refFaultParamDb/excelToDatabase/FileForDeformationModelersv4.xls";
	private final static String DIFF_OUT_FILE = "org/opensha/refFaultParamDb/excelToDatabase/Differences.txt";
	private HashMap<Integer, RowIdentifier> sheet1Rows = new HashMap<Integer, RowIdentifier>();
	private HashMap<Integer, RowIdentifier> sheet2Rows = new HashMap<Integer, RowIdentifier>();
	
	public CompareExcelSheets() {
		// load the rowIds and corresponding site Id and entry date into memory
		loadRowsIntoMemory(EXCEL_SHEET1, sheet1Rows);
		loadRowsIntoMemory(EXCEL_SHEET2, sheet2Rows);
		
		//read the  excel files
		try {
			// first excel sheet
			POIFSFileSystem fs1 = new POIFSFileSystem(new FileInputStream(EXCEL_SHEET1));
			HSSFWorkbook wb1 = new HSSFWorkbook(fs1);
			HSSFSheet sheet1 = wb1.getSheetAt(0);
			int lastRowNum1 = sheet1.getLastRowNum();
		
			// second excel sheet
			POIFSFileSystem fs2 = new POIFSFileSystem(new FileInputStream(EXCEL_SHEET2));
			HSSFWorkbook wb2 = new HSSFWorkbook(fs2);
			HSSFSheet sheet2 = wb2.getSheetAt(0);
			int lastRowNum2 = sheet2.getLastRowNum();
			
			FileWriter diffWriter = new FileWriter(DIFF_OUT_FILE);
			
			// compare row by row
			boolean found=false;
			for(int row1=1; row1<=lastRowNum1; ++row1) { // exclude Header row
				RowIdentifier identifier1 = sheet1Rows.get(row1);
				found=false;
				for(int row2=1; row2<=lastRowNum2 && !found; ++row2) {// exclude Header row
					RowIdentifier identifier2 = sheet2Rows.get(row2);
					if(identifier2==null) continue;
					if(identifier1.getSiteId()==identifier2.getSiteId() &&
							identifier1.getEntryDate().equalsIgnoreCase(identifier2.getEntryDate())) {
						HSSFRow r1 = sheet1.getRow(row1);
						HSSFRow r2 = sheet2.getRow(row2);
						compare(r1, r2, row1, row2, diffWriter);
						sheet2Rows.remove(row2);
						found=true;
					}
				}
				
				// if row is present in first sheet but not in second sheet
				if(!found) 
					diffWriter.write("Row "+(row1+1)+" exists in Sheet1 but not in Sheet2\n");
			}
			
			// now write all rows that are present in second sheet but not in first sheet
			Iterator<Integer> it = sheet2Rows.keySet().iterator();
			while(it.hasNext()) {
				int rowId = it.next();
				diffWriter.write("Row "+(rowId+1)+" exists in Sheet2 but not in Sheet1\n");
			}
			
			diffWriter.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
		
	}
	
	/**
	 * Compare each column in rows and write the difference in a file
	 * 
	 * @param r1
	 * @param r2
	 * @param fw
	 */
	private void compare(HSSFRow r1, HSSFRow r2, int rowIndex1, int rowIndex2, FileWriter diffWriter) {
		try {
			int LAST_COL = 50;
			for(int col=0; col<LAST_COL; ++col) { // ignore the last column as it is just a Comment column
				HSSFCell cell1 = r1.getCell((short)col);
				String value1 = getValue(cell1);
				HSSFCell cell2 = r2.getCell((short)col);
				String value2 = getValue(cell2);
				// if values are same, continue else write the difference in a file
				if(value1.equalsIgnoreCase(value2)) continue;
				diffWriter.write(">>>>> Row "+(rowIndex1+1)+" Column "+(col+1)+" in Sheet1 has value "+value1+
						" but Row " +(rowIndex2+1)+" Column "+(col+1)+" in Sheet2 has value "+value2+"\n");
			}
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
		
	private String getValue(HSSFCell cell) {
		if (cell == null || cell.getCellType() == HSSFCell.CELL_TYPE_BLANK) 
			return "";
		if(cell.getCellType() == HSSFCell.CELL_TYPE_STRING)
                return cell.getStringCellValue().trim();
        return ""+cell.getNumericCellValue();
	}
	
	/**
	 * Load the siteId and entryDate correpsonding to each row in the excel sheet
	 * 
	 * @param sheetName
	 * @param rowMapping
	 */
	private void loadRowsIntoMemory(String sheetName, HashMap<Integer, RowIdentifier> rowMapping) {
		try {
		// read the excel file
	      POIFSFileSystem fs = new POIFSFileSystem(new FileInputStream(sheetName));
	      HSSFWorkbook wb = new HSSFWorkbook(fs);
	      HSSFSheet sheet = wb.getSheetAt(0);
	      int lastRowNum = sheet.getLastRowNum();
	      // read data for each row
	      for(int r = 1; r<=lastRowNum; ++r) {
	        HSSFRow row = sheet.getRow(r);
	        String entryDate = row.getCell((short)0).getStringCellValue();
	        int siteId = (int) row.getCell((short)6).getNumericCellValue();
	        RowIdentifier identifier = new RowIdentifier(r, siteId, entryDate);
	        rowMapping.put(r, identifier);
	      }
		}catch(Exception e) {
			e.printStackTrace();
		}
	}
	
	public static void main(String[] args) {
		new CompareExcelSheets();
	}
		      
}

/**
 * It saves the row Index and corresponding site Id and entry Date
 * 
 * @author vipingupta
 *
 */
class RowIdentifier {
	private int rowId;
	private int siteId;
	private String entryDate;
	
	public RowIdentifier() { }
	
	public RowIdentifier(int rowId, int siteId, String entryDate) {
		setRowId(rowId);
		setEntryDate(entryDate);
		setSiteId(siteId);
	}
	
	public String getEntryDate() {
		return entryDate;
	}
	public void setEntryDate(String entryDate) {
		this.entryDate = entryDate;
	}
	public int getRowId() {
		return rowId;
	}
	public void setRowId(int rowId) {
		this.rowId = rowId;
	}
	public int getSiteId() {
		return siteId;
	}
	public void setSiteId(int siteId) {
		this.siteId = siteId;
	}
}