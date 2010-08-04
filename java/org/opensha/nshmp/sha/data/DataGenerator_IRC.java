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

package org.opensha.nshmp.sha.data;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.rmi.RemoteException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.regex.Pattern;

import javax.swing.JOptionPane;

import org.apache.poi.hssf.usermodel.HSSFCellStyle;
import org.apache.poi.hssf.usermodel.HSSFFont;
import org.apache.poi.hssf.usermodel.HSSFRow;
import org.apache.poi.hssf.usermodel.HSSFSheet;
import org.apache.poi.hssf.usermodel.HSSFWorkbook;
import org.apache.poi.poifs.filesystem.POIFSFileSystem;
import org.opensha.commons.geo.Location;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;
import org.opensha.nshmp.sha.data.calc.FaFvCalc;
import org.opensha.nshmp.sha.data.calc.ResidentialSiteCalc;
import org.opensha.nshmp.util.BatchProgress;
import org.opensha.nshmp.util.GlobalConstants;



/**
 * <p>Title: DataGenerator_IRC</p>
 *
 * <p>Description: This class acts as the modal for the application. It computes
 * data needed by the application.</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public class DataGenerator_IRC
    extends DataGenerator_NEHRP {

  private double residentialSiteVal;
  private String residentilaSeismicDesignVal;

  private static DecimalFormat siteValFormat = new DecimalFormat("0.00");
  private static final String RESIDENTIAL_SITE_DESIGN =
      "Residential Seismic Design Category";
  private static final String Ss_S1 =
      "Ss and S1 = Mapped Spectral Acceleration Values";
  private static final String Site_D = "Site Class D - ";
  private static final String MCE_MAP_VALUES = "MCE MAP VALUES";
  private static final String Ss_Val_String = "Short Period Map Value - Ss = ";
  private static final String S1_Val_String =
      "1.0 sec Period Map Value - S1 = ";
  private static final String RESIDENTIAL_DESIGN_STRING =
      "RESIDENTIAL DESIGN INFORMATION";
  private static final String SOIL_FACTOR_STRING = "Soil factor for " + Site_D;
  private static final String RESIDENTIAL_SITE_VAL =
      "Residential Site Value = 2/3 x Fa x Ss = ";
  private static final String RESIDENTIAL_SEIS_DESIGN_VAL =
      "Residential Seismic Design Category = ";

  private String createInfoString() {
    String info = RESIDENTIAL_SITE_DESIGN + "\n";
    info += Ss_S1 + "\n";
    info += Site_D + "Fa = " + siteValFormat.format(faVal) + ", Fv = " +
        siteValFormat.format(fvVal) + "\n";
    info += MCE_MAP_VALUES + "\n";
    info += Ss_Val_String + siteValFormat.format(getSs()) +
        GlobalConstants.SA_UNITS + "\n";
    info += S1_Val_String + siteValFormat.format(getSa()) +
        GlobalConstants.SA_UNITS + "\n\n";

    info += RESIDENTIAL_DESIGN_STRING + "\n";
    info += Ss_Val_String + siteValFormat.format(getSs()) +
        GlobalConstants.SA_UNITS + "\n";
    info += SOIL_FACTOR_STRING + " Fa = " + siteValFormat.format(faVal) + "\n";
    info += RESIDENTIAL_SITE_VAL + siteValFormat.format(residentialSiteVal) +
        GlobalConstants.SA_UNITS + "\n";
    info += RESIDENTIAL_SEIS_DESIGN_VAL + residentilaSeismicDesignVal;
    return info;
  }

  /*
   * Sets the Fa and Fv
   */
  private void setFaFv() {
    FaFvCalc calc = new FaFvCalc();
    String fa = "" + calc.getFa(GlobalConstants.SITE_CLASS_D, getSs());
    faVal = Float.parseFloat(fa);
    String fv = "" + calc.getFv(GlobalConstants.SITE_CLASS_D, getSa());
    fvVal = Float.parseFloat(fv);
  }

  /**
   * Sets the Residential Site values
   */
  private void setResidentialSiteValues() {
    ResidentialSiteCalc calc = new ResidentialSiteCalc();
    residentialSiteVal = calc.calcResidentialSiteValue(faVal, getSs());
    residentilaSeismicDesignVal = calc.getResidentialSeismicDesignCategory(
        residentialSiteVal, dataEdition);
  }

  /**
   * Gets the data for SsS1 in case Territory.
   * Territory is when user is not allowed to enter any zip code or Lat-Lon
   * for the location or if it is GAUM and TAUTILLA.
   */
  public void calculateSsS1() throws RemoteException {
    super.getCalculateSsS1Function();
    //clearData();
    setFaFv();
    setResidentialSiteValues();
    addDataInfo(createInfoString());
  }

  /**
   * Gets the data for SsS1 in case region specified is not a Territory and user
   * specifies Lat-Lon for the location.
   */
  public void calculateSsS1(double lat, double lon) throws RemoteException {
    super.getCalculateSsS1Function(lat, lon);
    //clearData();
    setFaFv();
    setResidentialSiteValues();
    addDataInfo(createInfoString());
  }

  public void calculateSsS1(ArrayList<Location> locations, String outFile) {
	 HSSFWorkbook xlOut = getOutputFile(outFile);
	 // Create the output sheet
	 HSSFSheet xlSheet = xlOut.getSheet("Seismic Design Categories");
	 if(xlSheet==null)
		 xlSheet = xlOut.createSheet("Seismic Design Categories");
	 
	 /* Write the header information */
	 int startRow = xlSheet.getLastRowNum();
	 startRow = (startRow==0)?0:startRow+2;  // Put an empty row in case there is already data
	 
	 // Create a header style
	 HSSFFont headerFont = xlOut.createFont();
	 headerFont.setBoldweight(HSSFFont.BOLDWEIGHT_BOLD);
	 HSSFCellStyle headerStyle = xlOut.createCellStyle();
	 headerStyle.setFont(headerFont);
	 
	 // Geographic Region
	 HSSFRow xlRow = xlSheet.createRow(startRow++);
	 xlRow.createCell((short) 0).setCellValue("Geographic Region:");
	 xlRow.getCell((short) 0).setCellStyle(headerStyle);
	 xlRow.createCell((short) 1).setCellValue(geographicRegion);
	 
	 // Data Edition
	 xlRow = xlSheet.createRow(startRow++);
	 xlRow.createCell((short) 0).setCellValue("Data Edition:");
	 xlRow.getCell((short) 0).setCellStyle(headerStyle);
	 xlRow.createCell((short) 1).setCellValue(dataEdition);
	 
	 ++startRow; // We would like a blank line.
	 // Column Headers
	 xlRow = xlSheet.createRow(startRow++);
	 String[] headers = {"Latitude (Degrees)", "Longitude (Degrees)", "Site Class",
			 "Grid Spacing Basis", "Fa", "Fv", "Ss (g)", "S1 (g)", "2/3*Fa*Ss", "Design Category"};
	 short[] colWidths = {4500, 4500, 3000, 5000, 3000, 3000, 3000, 3000, 3000, 3000};
	 for(short i = 0; i < headers.length; ++i) {
		 xlRow.createCell(i).setCellValue(headers[i]);
		 xlRow.getCell(i).setCellStyle(headerStyle);
		 xlSheet.setColumnWidth(i, colWidths[i]);
	 }
	 
	 // Write the data information
	 int answer = 1;
	 BatchProgress bp = new BatchProgress("Computing Residential Design Values", locations.size());
	 bp.start();
	 for(int i = 0; i < locations.size(); ++i) {
		 bp.update(i+1);
		 xlRow = xlSheet.createRow(i+startRow);
		 double curLat = locations.get(i).getLatitude();
		 double curLon = locations.get(i).getLongitude();
		 double ssVal = Double.MAX_VALUE;
		 double s1Val = Double.MAX_VALUE;
		 double coef = (double) 2/3;
		 String curGridSpacing = "";
		 try {
			super.getCalculateSsS1Function(curLat, curLon);
		    //clearData();
		    ssVal = getSs();
		    s1Val = getSa();
		    
			setFaFv();
		    setResidentialSiteValues();
		    
			String reg1 = "^.*Data are based on a ";
			String reg2 = " deg grid spacing.*$";
			curGridSpacing = Pattern.compile(reg1, Pattern.DOTALL).matcher(saFunction.getInfo()).replaceAll("");
			curGridSpacing = Pattern.compile(reg2, Pattern.DOTALL).matcher(curGridSpacing).replaceAll("");
			curGridSpacing += " Degrees";
		} catch (RemoteException e) {
			if(answer != 0) {
				Object[] options = {"Suppress Future Warnings", "Continue Calculations", "Cancel Calculations"};
				answer = JOptionPane.showOptionDialog(null, "Failed to retrieve information for:\nLatitude: " +
							curLat + "\nLongitude: " + curLon, "Data Mining Error", 0, 
							JOptionPane.ERROR_MESSAGE, null, options, options[0]);
			}
			if(answer == 2) {
				bp.update(locations.size());
				break;
			}
			
			curGridSpacing = "Location out of Region";
		} finally {
			try {
			 xlRow.createCell((short) 0).setCellValue(curLat);
			 xlRow.createCell((short) 1).setCellValue(curLon);
			 xlRow.createCell((short) 2).setCellValue("D");
			 xlRow.createCell((short) 3).setCellValue(curGridSpacing);
			 xlRow.createCell((short) 4).setCellValue(
					 Double.parseDouble(siteValFormat.format(faVal)));
			 xlRow.createCell((short) 5).setCellValue(
					 Double.parseDouble(siteValFormat.format(fvVal)));
			 xlRow.createCell((short) 6).setCellValue(
					 Double.parseDouble(siteValFormat.format(ssVal)));
			 xlRow.createCell((short) 7).setCellValue(
					 Double.parseDouble(siteValFormat.format(s1Val)));
			 xlRow.createCell((short) 8).setCellValue( 
					 Double.parseDouble(siteValFormat.format(coef * faVal * ssVal )));
			 xlRow.createCell((short) 9).setCellValue(residentilaSeismicDesignVal);
			} catch(Exception ex) {
				// Ignore these since they are just formatting issues
			}
		} 
	 }
	 
	 try {
		FileOutputStream fos = new FileOutputStream(outFile);
		xlOut.write(fos);
		fos.close();
		// Let the user know that we are done
		dataInfo += "Batch Completed!\nOutput sent to: " + outFile + "\n\n";
	} catch (FileNotFoundException e) {
		// Just ignore for now...
	} catch (IOException e) {
		// Just ignore for now...
	}
  }
  
  /**
   * Gets the data for SsS1 in case region specified is not a Territory and user
   * specifies zip code for the location.
   */
  public void calculateSsS1(String zipCode) throws ZipCodeErrorException,
      RemoteException {
    super.getCalculateSsS1Function(zipCode);
    //clearData();
    setFaFv();
    setResidentialSiteValues();
    addDataInfo(createInfoString());
  }
  
  private HSSFWorkbook getOutputFile(String outFile) {
	  // Create the Excel output file, or open it if it already exists
	  File outBook = new File(outFile);
	  HSSFWorkbook xlsOut = null;
	  if(outBook.exists()) {
		  try {
			  POIFSFileSystem fs = new
			  	POIFSFileSystem(new FileInputStream(outBook));
			  xlsOut = new HSSFWorkbook(fs);
		  } catch (FileNotFoundException e) {
			  // This won't happen since we just checked that it exists
			  // But we'll alert you anyway.
			  JOptionPane.showMessageDialog(null, "The file "+outFile+" was not found.",
					  "File Not Found", JOptionPane.ERROR_MESSAGE);
			  return new HSSFWorkbook();
		  } catch (IOException e) {
			  JOptionPane.showMessageDialog(null, "Failed to open file: " + outFile,
					  "I/O Failure", JOptionPane.ERROR_MESSAGE);
			  return new HSSFWorkbook();
		}
	  } else {
		  xlsOut = new HSSFWorkbook();
	  }
	  return xlsOut;
  }

}
