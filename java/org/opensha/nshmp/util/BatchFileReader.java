package org.opensha.nshmp.util;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.ArrayList;

import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.filechooser.FileFilter;

import org.apache.poi.hssf.usermodel.HSSFCell;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.poifs.filesystem.POIFSFileSystem;
import org.opensha.nshmp.sha.gui.beans.ExceptionBean;


public class BatchFileReader {
	private HSSFWorkbook workbook = null;
	private int activeSheet = 0;

	private BatchFileReader() {}
	
	/**
	 * Creates an <code>HSSFWorkbook</code> object for reading in data.
	 * @param filename The name of the workbook to read.
	 */
	public BatchFileReader(String filename) {
		try {
			POIFSFileSystem fs = 
				new POIFSFileSystem(new FileInputStream(filename));
			workbook = new HSSFWorkbook(fs);
		} catch (IOException iox) {
			ExceptionBean.showSplashException("Could not find: " + filename, "File Not Found", iox);
		}
		activeSheet = 0;
	}

	public ArrayList<Double> getColumnVals(short columnNumber) {
		return getColumnVals(columnNumber, activeSheet);
	}
	
	/**
	 * Gets all the values for the given column on the given sheet number.
	 * This will only get the values from the second row onwards to allow for
	 * a header row.  (You only get one header row, tough).
	 * 
	 * @param columnNumber The number of the column you wish to get.  Column A = 0.
	 * @param sheetNumber The number of the sheet you wish to get.  Sheet1 = 0.
	 * @return An <code>ArrayList</code> containing all the doubles it found in the column.
	 */
	public ArrayList<Double> getColumnVals(short columnNumber, int sheetNumber) {
		short maxRows = 32767;
		ArrayList<Double> vals = new ArrayList<Double>();
		HSSFSheet sheet = null;
		if(inReadyState()) {
			try {
				sheet = workbook.getSheetAt(sheetNumber);
			} catch (Exception ex) {
				ex.printStackTrace();
			}
			
			for(short i = 1; i < maxRows; ++i) {
				// Make sure we have a valid row
				HSSFRow row = sheet.getRow(i);
				if(row == null)
					break;
				
				// Make sure we have a valid cell
				HSSFCell cell = row.getCell(columnNumber);
				if(cell == null) {
					// The row was defined, so this "should" be defined.
					// Since it is not, we give it a value of 0.
					vals.add(0.0);
					continue;
				}
				
				// Get the current value
				String s = getCellValue(cell);
				
				if(s!=null && !"".equals(s)) {
					try {
						// This could be a problem if there is text in the cell
						vals.add(new Double(s));
					} catch (Exception ex) {
						ExceptionBean.showSplashException(
							"A value was not valid in the sheet!", "Invalid value", ex);
					} // try
				} else {
					break;
				} // if
			} // for
		}
		return vals;
	}

	public ArrayList<String> getColumnStringVals(short columnNumber) {
		return getColumnStringVals(columnNumber, activeSheet);
	}
	
	public ArrayList<String> getColumnStringVals(short columnNumber, int sheetNumber) {
		short maxRows = 32767;
		ArrayList<String> vals = new ArrayList<String>();
		HSSFSheet sheet = null;
		if(inReadyState()) {
			try {
				sheet = workbook.getSheetAt(sheetNumber);
			} catch (Exception ex) {
				ex.printStackTrace();
			}
			
			for(short i = 1; i < maxRows; ++i) {
				// Make sure we have a valid row
				HSSFRow row = sheet.getRow(i);
				if(row == null)
					break;
				
				// Make sure we have a valid cell
				HSSFCell cell = row.getCell(columnNumber);
				if(cell == null) {
					// The row was non-empty, so this cell "should" be defined.
					// Since there is no value, it is defined as empty.
					vals.add("");
					continue;
				}
				
				// Get the current value
				String s = getCellValue(cell);
				
				if(s!=null) {
					try {
						vals.add(s);
					} catch (Exception ex) {
						ExceptionBean.showSplashException(
							"A value was not valid in the sheet!", "Invalid value", ex);
					} // try
				} else {
					break;
				} // if
			} // for
		}
		return vals;
	}
	
	private String getCellValue(HSSFCell cell) {
		String s = null;
		try {
			s = cell.getStringCellValue();
		} catch (Exception ex) {
			try {
				Double d = new Double(cell.getNumericCellValue());
				s = d.toString();
			} catch (Exception ex1) {
				// Ho hum...we can't try anything else, so I guess we die...
			} // try
		} // try
		return s;
	}
	
	private boolean inReadyState() {
		if(workbook == null) {
			ExceptionBean.showSplashException("Workbook was null!", 
					"Null Pointer Exception", new NullPointerException("Workbook was null"));
			return false;
		} else {
			return true;
		}
	}
	
	public boolean ready() { return workbook != null; }
	
	public static BatchFileReader createReaderFromGui() {
		JFrame frame = new JFrame("Select the file to batch");
		JFileChooser chooser = new JFileChooser();
		chooser.setFileFilter(new FileFilter() {
			public boolean accept(File arg0) {
				return (arg0.getAbsolutePath().endsWith("xls") ||
					arg0.isDirectory());
			}
			public String getDescription() {
				return "Microsoft Excel Files (*.xls)";
			}
		});
		
		int returnVal = chooser.showOpenDialog(frame);
		if(returnVal == JFileChooser.APPROVE_OPTION) {
			return new BatchFileReader(chooser.getSelectedFile().getAbsolutePath());
		} else {
			return new BatchFileReader();
		}
	}
}
