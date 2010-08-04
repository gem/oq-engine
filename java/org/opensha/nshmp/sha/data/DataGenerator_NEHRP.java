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
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;
import org.opensha.commons.data.function.DiscretizedFuncList;
import org.opensha.commons.geo.Location;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;
import org.opensha.nshmp.sha.data.api.DataGeneratorAPI_NEHRP;
import org.opensha.nshmp.sha.data.calc.FaFvCalc;
import org.opensha.nshmp.util.BatchProgress;
import org.opensha.nshmp.util.GlobalConstants;

/**
 * <p>Title: DataGenerator_NEHRP</p>
 *
 * <p>Description: </p>
 * @author Ned Field, Nitin Gupta , E.V.Leyendecker
 * @version 1.0
 */
public class DataGenerator_NEHRP
    implements DataGeneratorAPI_NEHRP {

  //gets the selected region
  protected String geographicRegion;
  //gets the selected edition
  protected String dataEdition;
	protected String zipCode, lat, lon = "";

  private static final DecimalFormat saValFormat = new DecimalFormat("0.000");
  private static final DecimalFormat faFvFormat = new DecimalFormat("0.00#");
  
  protected ArbitrarilyDiscretizedFunc saFunction;

  protected float faVal = 1.0f;
  protected float fvVal = 1.0f;
  protected String siteClass = GlobalConstants.SITE_CLASS_B;
  protected ArbitrarilyDiscretizedFunc sdSpectrumSaSdFunction;
  protected ArbitrarilyDiscretizedFunc smSpectrumSaSdFunction;
  protected ArbitrarilyDiscretizedFunc mapSpectrumSaSdFunction;
  protected ArbitrarilyDiscretizedFunc sdSpectrumSaTFunction;
  protected ArbitrarilyDiscretizedFunc smSpectrumSaTFunction;
  protected ArbitrarilyDiscretizedFunc mapSpectrumSaTFunction;

  //holds all the data and its info in a String format.
  protected String dataInfo = "";

  //metadata to be shown when plotting the curves
  protected String metadataForPlots;

  //sets the selected spectra type
  protected String selectedSpectraType;

  /**
   * Default class constructor
   */
  public DataGenerator_NEHRP() {}

  /**
   * Removes all the calculated data.
   */
  public void clearData() {
    dataInfo = "";
		zipCode = "";
		lat = "";
		lon = "";
  }

  /**
   * Returns the Data and all the metadata associated with it in a String.
   * @return String
   */
  public String getDataInfo() {
    return dataInfo;
  }

  protected void addDataInfo(String data) {
    dataInfo += geographicRegion + "\n";
    dataInfo += dataEdition + "\n";

	if ( zipCode != null && lat != null && lon != null ) {	
		if (!zipCode.equals(""))
			dataInfo += "Zip Code = " + zipCode + "\n";
		if (!lat.equals("") && !lon.equals(""))
			dataInfo += "Latitude = " + lat +
									"\nLongitude = " + lon + "\n";
	} else {
		dataInfo += geographicRegion + " - " + dataEdition + "\n";
	}
    dataInfo += data + "\n\n";
  }

  /**
   * Returns the SA at .2sec
   * @return double
   */
  public double getSs() {
    return saFunction.getY(0);
  }

  /**
   * Returns the SA at 1 sec
   * @return double
   */
  public double getSa() {
    return saFunction.getY(1);
  }

	public ArbitrarilyDiscretizedFunc getSaFunction() {
		return saFunction;
	}
	
  /**
   * Gets the data for SsS1 in case Territory.
   * Territory is when user is not allowed to enter any zip code or Lat-Lon
   * for the location or if it is GAUM and TAUTILLA.
   */
  public void calculateSsS1() throws RemoteException {
	getCalculateSsS1Function();
	addDataInfo(saFunction.getInfo());


    /*
	HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSsS1(geographicRegion);
    String location = "Spectral values are constant for the region";
    createMetadataForPlots(location);
    addDataInfo(function.getInfo());
    saFunction = function;
	*/

  }
  
  public void getCalculateSsS1Function() throws RemoteException {
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSsS1(geographicRegion);
    String location = "Spectral values are constant for the region";
    createMetadataForPlots(location);
	saFunction = function;
  }
  
  
  /**
   * Gets the data for SsS1 in case region specified is not a Territory and user
   * specifies Lat-Lon for the location.
   */
  public void calculateSsS1(double lat, double lon) throws RemoteException {
	getCalculateSsS1Function(lat, lon);
	addDataInfo(saFunction.getInfo());

	/*
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSsS1(geographicRegion,
        dataEdition,
        lat, lon);
    String location = "Lat - " + lat + "  Lon - " + lon;
    createMetadataForPlots(location);
    addDataInfo(function.getInfo());
    saFunction = function;
	*/

  }
  
  public void getCalculateSsS1Function(double lat, double lon) throws RemoteException {

    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSsS1(geographicRegion,
        dataEdition,
        lat, lon);
	if ( function == null ) {
		System.err.println("Server returned Null function");
		throw new RemoteException("Given lat/lon pair ("+lat +"/"+lon+") failed to return data.");
	}
		this.lat = "" + lat; //newline
		this.lon = "" + lon; //newline
		this.zipCode = "";
    String location = "Lat : " + lat + "\nLon : " + lon;
    createMetadataForPlots(location);
    saFunction = function;

  }
  

  /**
   * Gets the data for SsS1 in case region specified is not a Territory and user
   * specifies zip code for the location.
   */
  public void calculateSsS1(String zipCode) throws ZipCodeErrorException,
      RemoteException {
	getCalculateSsS1Function(zipCode);
	addDataInfo(saFunction.getInfo());

	/*
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSsS1(geographicRegion,
        dataEdition,
        zipCode);
    String location = "Zipcode - " + zipCode;
    createMetadataForPlots(location);
    addDataInfo(function.getInfo());
    saFunction = function;
	*/
  }

	public void setNoLocation() {
		zipCode = "";
		lat = "";
		lon = "";
 	}

 public void getCalculateSsS1Function(String zipCode) throws ZipCodeErrorException,
      RemoteException {
		this.zipCode = zipCode; //newline
		this.lat = "";
		this.lon = "";
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSsS1(geographicRegion,
        dataEdition,
        zipCode);
    String location = "Zipcode - " + zipCode;
    createMetadataForPlots(location);
    saFunction = function;
  }

 public void calculateSsS1(ArrayList<Location> locations, String outFile) {
	 HSSFWorkbook xlOut = getOutputFile(outFile);
	 // Create the output sheet
	 HSSFSheet xlSheet = xlOut.getSheet("Ss & S1 Values");
	 if(xlSheet==null)
		 xlSheet = xlOut.createSheet("Ss & S1 Values");
	 
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
	 String[] headers = {"Latitude (Degrees)", "Longitude (Degrees)", "Site Class", "Ss (g)", "S1 (g)", "Grid Spacing Basis"};
	 short[] colWidths = {4500, 4500, 3000, 3000, 3000, 5000};
	 for(short i = 0; i < headers.length; ++i) {
		 xlRow.createCell(i).setCellValue(headers[i]);
		 xlRow.getCell(i).setCellStyle(headerStyle);
		 xlSheet.setColumnWidth(i, colWidths[i]);
	 }
	 
	 // Write the data information
	 int answer = 1;
	 BatchProgress bp = new BatchProgress("Computing Ss and S1", locations.size());
	 bp.start();
	 for(int i = 0; i < locations.size(); ++i) {
		 bp.update(i+1);
		 xlRow = xlSheet.createRow(i+startRow);
		 double curLat = locations.get(i).getLatitude();
		 double curLon = locations.get(i).getLongitude();
		 Double curSa = null;
		 Double curSs = null;
		 String curGridSpacing = "";
		 try {
			getCalculateSsS1Function(curLat, curLon);
			curSs = Double.parseDouble(saValFormat.format(getSs()));
			curSa = Double.parseDouble(saValFormat.format(getSa()));
			String reg1 = "^.*Data are based on a ";
			String reg2 = " deg grid spacing.*$";
			curGridSpacing = Pattern.compile(reg1, Pattern.DOTALL).matcher(saFunction.getInfo()).replaceAll("");
			curGridSpacing = Pattern.compile(reg2, Pattern.DOTALL).matcher(curGridSpacing).replaceAll("");
			curGridSpacing += " Degrees";
		} catch (RemoteException e) {
			if(answer != 0) {
				Object[] options = {"Suppress Future Warnings", "Continue Calculations", "Abort Run"};
				answer = JOptionPane.showOptionDialog(null, "Failed to retrieve information for:\nLatitude: " +
							curLat + "\nLongitude: " + curLon, "Data Mining Error", 0, 
							JOptionPane.ERROR_MESSAGE, null, options, options[0]);
			}
			if(answer == 2) {
				bp.update(locations.size());
				break;
			}
			
			curSs = Double.MAX_VALUE;
			curSa = Double.MAX_VALUE;
			curGridSpacing = "Location out of Region";
		} finally {
		 xlRow.createCell((short) 0).setCellValue(curLat);
		 xlRow.createCell((short) 1).setCellValue(curLon);
		 xlRow.createCell((short) 2).setCellValue("B");
		 xlRow.createCell((short) 3).setCellValue(curSs);
		 xlRow.createCell((short) 4).setCellValue(curSa);
		 xlRow.createCell((short) 5).setCellValue(curGridSpacing);
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

  protected void createMetadataForPlots(String location) {
    metadataForPlots = GlobalConstants.SA_DAMPING + "\n";
    metadataForPlots += geographicRegion + "\n";
    metadataForPlots += dataEdition + "\n";
    metadataForPlots += location + "\n";
  }

  /**
   *
   */
  public void calculateSMSsS1() throws RemoteException {
	
	addDataInfo(getCalculateSMSsS1Function().getInfo());

	/*
	HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSMSsS1(saFunction, faVal,
        fvVal, siteClass);
    addDataInfo(function.getInfo());
	*/
  }
  
  public ArbitrarilyDiscretizedFunc getCalculateSMSsS1Function() throws RemoteException {
	
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSMSsS1(saFunction, faVal,
        fvVal, siteClass);
    if (dataEdition.equals(GlobalConstants.NEHRP_2009)) {
    	function.setInfo(
    		function.getInfo()
    			.replaceAll("SMs", "SRs")
    			.replaceAll("SM1", "SR1")
    			.replaceAll("Spectral Response Accelerations SRs",
    					"MCE_R Spectral Response Accelerations SRS")
    		);
    }
		
	return(function);
  }
  
  public void calculateSMSsS1(String edition,
		  String region, String zipCode, String siteClass) 
  		throws RemoteException {
	 addDataInfo(getCalculateSMSsS1Function(edition, region, zipCode,
			 siteClass).getInfo());
  }
  
  public ArbitrarilyDiscretizedFunc getCalculateSMSsS1Function(String edition,
		  String region, String zipCode, String siteClass) 
  		throws RemoteException {
	  HazardDataMinerAPI miner = new HazardDataMinerServletMode();
	  ArbitrarilyDiscretizedFunc function = miner.getSMSsS1(edition, region,
			  zipCode, siteClass);
	  return function;
  }
  
  /**
   *
   *
   */
  public void calculatedSDSsS1() throws RemoteException {
	addDataInfo(getCalculatedSDSsS1Function().getInfo());

	/*
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSDSsS1(saFunction, faVal,
        fvVal, siteClass);
    addDataInfo(function.getInfo());
	*/
  }

  public ArbitrarilyDiscretizedFunc getCalculatedSDSsS1Function() throws RemoteException {

    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    ArbitrarilyDiscretizedFunc function = miner.getSDSsS1(saFunction, faVal,
        fvVal, siteClass);
    if (dataEdition.equals(GlobalConstants.NEHRP_2009)) {
    	function.setInfo(
    		function.getInfo()
    			.replaceAll("SMs", "SRs")
    			.replaceAll("SM1", "SR1")
    		);
    }
	return(function);
  }
  
  public void calculateSDSsS1(String edition,
		  String region, String zipCode, String siteClass) 
  		throws RemoteException {
	 addDataInfo(getCalculateSDSsS1Function(edition, region, zipCode,
			 siteClass).getInfo());
  }
  
  public ArbitrarilyDiscretizedFunc getCalculateSDSsS1Function(String edition,
		  String region, String zipCode, String siteClass) 
  		throws RemoteException {
	  HazardDataMinerAPI miner = new HazardDataMinerServletMode();
	  ArbitrarilyDiscretizedFunc function = miner.getSDSsS1(edition, region,
			  zipCode, siteClass);
	  return function;
  }
  
  public void calculateSMsSm1SDsSD1(ArrayList<Location> locations, 
		  ArrayList<String> siteConditions, String outFile) {
	  HSSFWorkbook xlOut = getOutputFile(outFile);
	 // Create the output sheet
	  String shtStr = "SM";
	  if(dataEdition.equals(GlobalConstants.NEHRP_2009)) {
		  shtStr = "SR";
	  }
	 HSSFSheet xlSheet = xlOut.getSheet(shtStr + " & SD Values");
	 if(xlSheet==null)
		 xlSheet = xlOut.createSheet(shtStr + " & SD Values");
	 
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
	 
	 // Data Generation Explanation
	 xlRow = xlSheet.createRow(startRow++);
	 xlRow.createCell((short) 1).setCellValue(shtStr + "s = Fa*Ss");
	 xlRow.createCell((short) 2).setCellValue(shtStr + "1 = Fv*S1");
	 xlRow = xlSheet.createRow(startRow++);
	 xlRow.createCell((short) 1).setCellValue("SDs = 2/3 * " + shtStr + "s");
	 xlRow.createCell((short) 2).setCellValue("SD1 = 2/3 * " + shtStr + "1");
	 
	 // Header row
	 String[] headers = {"Latitude (Degrees)", "Longitude (Degrees)", "Site Class", "Fa", "Fv", shtStr + "s (g)", shtStr + "1 (g)", "SDs (g)", "SD1 (g)", "Grid Spacing Basis"};
	 short[] colWidths = {4500, 4500, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 5000};
	 ++startRow; // We want a blank row
	 xlRow = xlSheet.createRow(startRow++);
	 for(short i = 0; i < headers.length; ++i) {
		 xlRow.createCell(i).setCellValue(headers[i]);
		 xlRow.getCell(i).setCellStyle(headerStyle);
		 xlSheet.setColumnWidth(i, colWidths[i]);
	 }
	 
	 // A calculator
	 FaFvCalc calc = new FaFvCalc();
	 
	 // Start plugging in the data
	 int answer = 1;
	 BatchProgress bp = new BatchProgress("Computing " + shtStr + "s, " + shtStr + "1, SDs and SD1", locations.size());
	 bp.start();
	 for(int i = 0; i < locations.size(); ++i) {
		 bp.update(i+1);
		 xlRow = xlSheet.createRow(i+startRow);
		 double curLat = locations.get(i).getLatitude();
		 double curLon = locations.get(i).getLongitude();
		 
		 Float curSMs = null; Float curSM1 = null; Float curSDs = null; Float curSD1 = null;
		 
		 Float curFa = Float.MAX_VALUE;
		 Float curFv = Float.MAX_VALUE;
		 
		 String curCond = siteConditions.get(i);
		 
		 Float curSa = null;
		 Float curSs = null;
		 String curGridSpacing = "";
		 try {
			getCalculateSsS1Function(curLat, curLon);
			
			curSs = (float) getSs();
			curSa = (float) getSa();
			
			String reg1 = "^.*Data are based on a ";
			String reg2 = " deg grid spacing.*$";
			curGridSpacing = Pattern.compile(reg1, Pattern.DOTALL).matcher(saFunction.getInfo()).replaceAll("");
			curGridSpacing = Pattern.compile(reg2, Pattern.DOTALL).matcher(curGridSpacing).replaceAll("");
			curGridSpacing += " Degrees";
			
			curFa = Float.parseFloat(faFvFormat.format(calc.getFa(curCond, curSs)));
			curFv = Float.parseFloat(faFvFormat.format(calc.getFv(curCond, curSa)));
			float coef = (float) 2 / 3;
			curSMs = curFa * curSs; curSM1 = curFv * curSa;
			curSDs = coef*curSMs; curSD1 = coef*curSM1;
			
			
		} catch (RemoteException e) {
			if(answer != 0) {
				Object[] options = {"Suppress Future Warnings", "Continue Calculations", "Abort Run"};
				answer = JOptionPane.showOptionDialog(null, "Failed to retrieve information for:\nLatitude: " +
							curLat + "\nLongitude: " + curLon, "Data Mining Error", 0, 
							JOptionPane.ERROR_MESSAGE, null, options, options[0]);
			}
			if(answer == 2) {
				bp.update(locations.size());
				break;
			}
			
			curSMs = Float.MAX_VALUE; curSM1 = Float.MAX_VALUE;
			curSDs = Float.MAX_VALUE; curSD1 = Float.MAX_VALUE;
			curGridSpacing = "Location out of Region";
		} finally {
		 xlRow.createCell((short) 0).setCellValue(curLat);
		 xlRow.createCell((short) 1).setCellValue(curLon);
		 xlRow.createCell((short) 2).setCellValue(curCond.substring(curCond.length()-1));
		 xlRow.createCell((short) 3).setCellValue(Double.parseDouble(saValFormat.format(curFa)));
		 xlRow.createCell((short) 4).setCellValue(Double.parseDouble(saValFormat.format(curFv)));
		 xlRow.createCell((short) 5).setCellValue(Double.parseDouble(saValFormat.format(curSMs)));
		 xlRow.createCell((short) 6).setCellValue(Double.parseDouble(saValFormat.format(curSM1)));
		 xlRow.createCell((short) 7).setCellValue(Double.parseDouble(saValFormat.format(curSDs)));
		 xlRow.createCell((short) 8).setCellValue(Double.parseDouble(saValFormat.format(curSD1)));
		 xlRow.createCell((short) 9).setCellValue(curGridSpacing);
		} 
	 } // for
	 
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
   *
   *
   */
  public void calculateMapSpectrum() throws RemoteException {
	// For 2009 we don't care about Map Spectrum. Just skip.
	// if (GlobalConstants.NEHRP_2009.equals(dataEdition)) {return;}
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    DiscretizedFuncList functions = miner.getMapSpectrum(saFunction);
    addDataInfo(functions.getInfo());
    getFunctionsForMapSpectrum(functions);
  }

  public void calculateMapSpectrum(ArrayList<Location> locations, String outFile) {
	  HSSFWorkbook xlOut = getOutputFile(outFile);
		 // Create the output sheet
		 HSSFSheet xlSheet = xlOut.getSheet("Map Spectra");
		 if(xlSheet==null)
			 xlSheet = xlOut.createSheet("Map Spectra");
		 
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
		 
		 // MCE Header
		 xlRow = xlSheet.createRow(startRow++);
		 xlRow.createCell((short) 1).setCellValue("MCE Response Spectra for Site Class B");
		 
		 // Header row
		 String[] headers = {"Latitude (Degrees)", "Longitude (Degrees)", "Site Class", "Grid Spacing Basis", "Period (sec)", "Sa (g)", "Sd (Inches)"};
		 short[] colWidths = {4500, 4500, 3000, 5000, 3000, 3000, 3000};
		 ++startRow; // We want a blank row
		 xlRow = xlSheet.createRow(startRow++);
		 for(short i = 0; i < headers.length; ++i) {
			 xlRow.createCell(i).setCellValue(headers[i]);
			 xlRow.getCell(i).setCellStyle(headerStyle);
			 xlSheet.setColumnWidth(i, colWidths[i]);
		 }
		 
		 // Start plugging in the data
		 int answer = 1;
		 BatchProgress bp = new BatchProgress("Computing Map Spectra", locations.size());
		 bp.start();
		 for(int i = 0; i < locations.size(); ++i) {
			 bp.update(i+1);
			 xlRow = xlSheet.createRow(i+startRow);
			 double curLat = locations.get(i).getLatitude();
			 double curLon = locations.get(i).getLongitude();
			 DiscretizedFuncAPI saFunc = null;
			 DiscretizedFuncAPI sdFunc = null;
			 String curGridSpacing = "";
			 try {
				// Set the saFunction (ss,s1)
				getCalculateSsS1Function(curLat, curLon);
				// Now get the Map Spectrum (sa,sd funcs)
			    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
				DiscretizedFuncList functions = miner.getMapSpectrum(saFunction);
				saFunc = functions.get(1);
				sdFunc = functions.get(0);
				
				String reg1 = "^.*Data are based on a ";
				String reg2 = " deg grid spacing.*$";
				curGridSpacing = Pattern.compile(reg1, Pattern.DOTALL).matcher(saFunction.getInfo()).replaceAll("");
				curGridSpacing = Pattern.compile(reg2, Pattern.DOTALL).matcher(curGridSpacing).replaceAll("");
				curGridSpacing += " Degrees";
				
			} catch (RemoteException e) {
				if(answer != 0) {
					Object[] options = {"Suppress Future Warnings", "Continue Calculations", "Abort Run"};
					answer = JOptionPane.showOptionDialog(null, "Failed to retrieve information for:\nLatitude: " +
								curLat + "\nLongitude: " + curLon, "Data Mining Error", 0, 
								JOptionPane.ERROR_MESSAGE, null, options, options[0]);
				}
				if(answer == 2) {
					bp.update(locations.size());
					break;
				}
				saFunc = new ArbitrarilyDiscretizedFunc();
				sdFunc = new ArbitrarilyDiscretizedFunc();
				curGridSpacing = "Location out of Region";
				++startRow;
			} finally {
			 xlRow.createCell((short) 0).setCellValue(curLat);
			 xlRow.createCell((short) 1).setCellValue(curLon);
			 xlRow.createCell((short) 2).setCellValue("B");
			 xlRow.createCell((short) 3).setCellValue(curGridSpacing);
			 for(int j = 0; j < saFunc.getNum(); ++j) {
				 xlRow.createCell((short) 4).setCellValue(
						 Double.parseDouble(saValFormat.format(saFunc.getX(j))));
				 xlRow.createCell((short) 5).setCellValue(
						 Double.parseDouble(saValFormat.format(saFunc.getY(j))));
				 xlRow.createCell((short) 6).setCellValue(
						 Double.parseDouble(saValFormat.format(sdFunc.getY(j))));
				 ++startRow;
				 xlRow  = xlSheet.createRow(i+startRow);
			 } // for
			} 
		 } // for
		 
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
   *
   * @param mapSpectrumFunctions DiscretizedFuncList
   */
  protected void getFunctionsForMapSpectrum(DiscretizedFuncList
                                            mapSpectrumFunctions) {

	int numFunctions = mapSpectrumFunctions.size();
    System.err.printf("There are %d Map Spectra.\n", numFunctions);

    int i = 0;
    for (; i < numFunctions; ++i) {
      ArbitrarilyDiscretizedFunc tempFunction = (ArbitrarilyDiscretizedFunc)
          mapSpectrumFunctions.get(i);
      if (tempFunction.getName().equals(GlobalConstants.
                                        MCE_SPECTRUM_SA_Vs_T_GRAPH)) {
        mapSpectrumSaTFunction = tempFunction;
        break;
      } else {
    	  System.err.printf("Function %d name: %s\n", i, tempFunction.getName());
      }
    }

    System.err.printf("i = %d\n", i);
    ArbitrarilyDiscretizedFunc tempSDFunction = (ArbitrarilyDiscretizedFunc)
        mapSpectrumFunctions.get(1 - i);

    mapSpectrumSaSdFunction = tempSDFunction.getYY_Function(
        mapSpectrumSaTFunction);
    mapSpectrumSaSdFunction.setName(GlobalConstants.MCE_SPECTRUM_SA_Vs_SD_GRAPH);
    String info = metadataForPlots;
    info += siteClass + "\n";
    if (!dataEdition.equals(GlobalConstants.NEHRP_2009)) {
    	info += "Fa = " + faVal + " Fv = " + fvVal + "\n";
    }

    mapSpectrumSaSdFunction.setInfo(info);
    mapSpectrumSaTFunction.setInfo(info);
    mapSpectrumSaSdFunction.setYAxisName(GlobalConstants.SA);
    mapSpectrumSaSdFunction.setXAxisName(GlobalConstants.SD);
    mapSpectrumSaTFunction.setYAxisName(GlobalConstants.SA);
    mapSpectrumSaTFunction.setXAxisName(GlobalConstants.PERIOD_NAME);
  }

  /**
   *
   * @param smSpectrumFunctions DiscretizedFuncList
   */
  protected void getFunctionsForSMSpectrum(DiscretizedFuncList
                                           smSpectrumFunctions) {

    int numFunctions = smSpectrumFunctions.size();
    System.err.printf("There are %d SM Spectra.\n", numFunctions);
    int i = 0;
    for (; i < numFunctions; ++i) {
      ArbitrarilyDiscretizedFunc tempFunction = (ArbitrarilyDiscretizedFunc)
          smSpectrumFunctions.get(i);
      if (tempFunction.getName().equals(
    		  GlobalConstants.SITE_MODIFIED_SA_Vs_T_GRAPH) ||
    	  tempFunction.getName().equals("MCE_R Spectrum Sa Vs T")) {
        smSpectrumSaTFunction = tempFunction;
        break;
      } else {
    	  System.err.printf("Function %d name: %s\n", i, tempFunction.getName());
      }
    }

    System.err.printf("i = %d\n", i);
    ArbitrarilyDiscretizedFunc tempSDFunction = (ArbitrarilyDiscretizedFunc)
        smSpectrumFunctions.get(1 - i);
    smSpectrumSaSdFunction = tempSDFunction.getYY_Function(
        smSpectrumSaTFunction);
    smSpectrumSaSdFunction.setName(GlobalConstants.SITE_MODIFIED_SA_Vs_SD_GRAPH);
    String info = metadataForPlots;
    info += siteClass + "\n";
    if (!dataEdition.equals(GlobalConstants.NEHRP_2009)) {
    	info += "Fa = " + faVal + " Fv = " + fvVal + "\n";
    }

    smSpectrumSaSdFunction.setInfo(info);
    smSpectrumSaTFunction.setInfo(info);
    smSpectrumSaSdFunction.setYAxisName(GlobalConstants.SA);
    smSpectrumSaSdFunction.setXAxisName(GlobalConstants.SD);
    smSpectrumSaTFunction.setYAxisName(GlobalConstants.SA);
    smSpectrumSaTFunction.setXAxisName(GlobalConstants.PERIOD_NAME);

  }

  /**
   *
   * @param sdSpectrumFunctions DiscretizedFuncList
   */
  protected void getFunctionsForSDSpectrum(DiscretizedFuncList
                                           sdSpectrumFunctions) {

    int numFunctions = sdSpectrumFunctions.size();
    int i = 0;
    for (; i < numFunctions; ++i) {
      ArbitrarilyDiscretizedFunc tempFunction = (ArbitrarilyDiscretizedFunc)
          sdSpectrumFunctions.get(i);
      if (tempFunction.getName().equals(GlobalConstants.
                                        DESIGN_SPECTRUM_SA_Vs_T_GRAPH)) {
        sdSpectrumSaTFunction = tempFunction;
        break;
      }
    }

    ArbitrarilyDiscretizedFunc tempSMFunction = (ArbitrarilyDiscretizedFunc)
        sdSpectrumFunctions.get(1 - i);
    sdSpectrumSaSdFunction = tempSMFunction.getYY_Function(
        sdSpectrumSaTFunction);
    sdSpectrumSaSdFunction.setName(GlobalConstants.
                                   DESIGN_SPECTRUM_SA_Vs_SD_GRAPH);
    String info = metadataForPlots;
    info += siteClass + "\n";
    if (!dataEdition.equals(GlobalConstants.NEHRP_2009)) {
    	info += "Fa = " + faVal + " Fv = " + fvVal + "\n";
    }
    sdSpectrumSaSdFunction.setInfo(info);
    sdSpectrumSaTFunction.setInfo(info);
    sdSpectrumSaSdFunction.setYAxisName(GlobalConstants.SA);
    sdSpectrumSaSdFunction.setXAxisName(GlobalConstants.SD);
    sdSpectrumSaTFunction.setYAxisName(GlobalConstants.SA);
    sdSpectrumSaTFunction.setXAxisName(GlobalConstants.PERIOD_NAME);
  }

  /**
   * Returns the list of functions for plotting.
   * @param isMapSpectrumFunctionNeeded boolean true if user has clicked the map spectrum button
   * @param isSDSpectrumFunctionNeeded boolean true if user has clicked the SD spectrum button
   * @param isSMSpectrumFunctionNeeded boolean true if user has clicked the SM spectrum button
   * @return ArrayList
   */
  public ArrayList getFunctionsToPlotForSA(boolean
                                           isMapSpectrumFunctionNeeded,
                                           boolean isSDSpectrumFunctionNeeded,
                                           boolean isSMSpectrumFunctionNeeded) {

    ArrayList<DiscretizedFuncAPI> functions = new ArrayList<DiscretizedFuncAPI>();

    boolean is2009 = GlobalConstants.NEHRP_2009.equals(dataEdition);
    
    if (isMapSpectrumFunctionNeeded && !is2009) {
      functions.add(mapSpectrumSaTFunction);
      functions.add(mapSpectrumSaSdFunction);
    }
    if (isSDSpectrumFunctionNeeded) {
      functions.add(sdSpectrumSaTFunction);
      if (!is2009) {functions.add(sdSpectrumSaSdFunction);}
    }
    if (isSMSpectrumFunctionNeeded) {
      functions.add(smSpectrumSaTFunction);
      if (!is2009) {functions.add(smSpectrumSaSdFunction);}
    }
    return functions;
  }

  /**
   *
   *
   */
  public void calculateSMSpectrum() throws RemoteException {
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    DiscretizedFuncList functions = miner.getSMSpectrum(saFunction, faVal,
        fvVal, siteClass, dataEdition);
    addDataInfo(functions.getInfo());
    getFunctionsForSMSpectrum(functions);
  }

  public void calculateSMSpectrum(ArrayList<Location> locations, 
		  ArrayList<String> siteConditions, String outFile) {
	  HSSFWorkbook xlOut = getOutputFile(outFile);
	 // Create the output sheet
	  String shtStr = "SM";
	  if (dataEdition.equals(GlobalConstants.NEHRP_2009)) {
		  shtStr = "SR";
	  }
	 HSSFSheet xlSheet = xlOut.getSheet(shtStr + " Spectra");
	 if(xlSheet==null)
		 xlSheet = xlOut.createSheet(shtStr + " Spectra");
	 
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
	 
	 // Data Generation Explanation
	 //xlRow = xlSheet.createRow(startRow++);
	 //xlRow.createCell((short) 1).setCellValue("SMs = Fa*Ss");
	 //xlRow.createCell((short) 2).setCellValue("SM1 = Fv*S1");
	 
	 // Header row
	 String[] headers = {"Latitude (Degrees)", "Longitude (Degrees)", "Site Class", "Grid Spacing Basis", "Fa", "Fv", "Period (sec)", "Sa (g)", "Sd (inches)"};
	 short[] colWidths = {4500, 4500, 3000, 5000, 3000, 3000, 3000, 3000, 3000};
	 ++startRow; // We want a blank row
	 xlRow = xlSheet.createRow(startRow++);
	 for(short i = 0; i < headers.length; ++i) {
		 xlRow.createCell(i).setCellValue(headers[i]);
		 xlRow.getCell(i).setCellStyle(headerStyle);
		 xlSheet.setColumnWidth(i, colWidths[i]);
	 }
	 
	 // A calculator
	 FaFvCalc calc = new FaFvCalc();
	 
	 // Start plugging in the data
	 int answer = 1;
	 BatchProgress bp = new BatchProgress("Computing " + shtStr + " Spectra", locations.size());
	 bp.start();
	 for(int i = 0; i < locations.size(); ++i) {
		 bp.update(i+1);
		 xlRow = xlSheet.createRow(i+startRow);
		 double curLat = locations.get(i).getLatitude();
		 double curLon = locations.get(i).getLongitude();
		 DiscretizedFuncAPI saFunc = null;
		 DiscretizedFuncAPI sdFunc = null;
		 String curGridSpacing = "";
		 Float curFa = Float.MAX_VALUE;
		 Float curFv = Float.MAX_VALUE;
		 
		 String curCond = siteConditions.get(i);
		 // double coef = (double) 2 / 3;
		 
		 try {
			getCalculateSsS1Function(curLat, curLon);
			
			double curSs = getSs();
			double curSa = getSa();
			
			curFa = (float) calc.getFa(curCond, curSs);
			curFv = (float) calc.getFv(curCond, curSa);

		    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
		    DiscretizedFuncList functions = miner.getSMSpectrum(saFunction, curFa,
		        curFv, curCond, dataEdition);
			
		    saFunc = functions.get(1);
		    sdFunc = functions.get(0);
		    
		    String reg1 = "^.*Data are based on a ";
			String reg2 = " deg grid spacing.*$";
			curGridSpacing = Pattern.compile(reg1, Pattern.DOTALL).matcher(saFunction.getInfo()).replaceAll("");
			curGridSpacing = Pattern.compile(reg2, Pattern.DOTALL).matcher(curGridSpacing).replaceAll("");
			curGridSpacing += " Degrees";
		    
		} catch (RemoteException e) {
			if(answer != 0) {
				Object[] options = {"Suppress Future Warnings", "Continue Calculations", "Abort Run"};
				answer = JOptionPane.showOptionDialog(null, "Failed to retrieve information for:\nLatitude: " +
							curLat + "\nLongitude: " + curLon, "Data Mining Error", 0, 
							JOptionPane.ERROR_MESSAGE, null, options, options[0]);
			}
			if(answer == 2) {
				bp.update(locations.size());
				break;
			}
			saFunc = new ArbitrarilyDiscretizedFunc();
			sdFunc = new ArbitrarilyDiscretizedFunc();
			curGridSpacing = "Location out of Region";
			++startRow;
		} finally {
		 xlRow.createCell((short) 0).setCellValue(curLat);
		 xlRow.createCell((short) 1).setCellValue(curLon);
		 xlRow.createCell((short) 2).setCellValue(curCond.substring(curCond.length()-1));
		 xlRow.createCell((short) 3).setCellValue(curGridSpacing);
		 xlRow.createCell((short) 4).setCellValue(Double.parseDouble(saValFormat.format(curFa)));
		 xlRow.createCell((short) 5).setCellValue(Double.parseDouble(saValFormat.format(curFv)));
		 for(int j = 0; j < saFunc.getNum(); ++j) {
			 xlRow.createCell((short) 6).setCellValue(
					 Double.parseDouble(saValFormat.format(saFunc.getX(j))));
			 xlRow.createCell((short) 7).setCellValue(
					 Double.parseDouble(saValFormat.format(saFunc.getY(j))));
			 xlRow.createCell((short) 8).setCellValue(
					 Double.parseDouble(saValFormat.format(sdFunc.getY(j))));
			 ++startRow;
			 xlRow = xlSheet.createRow(i+startRow);
		 }
		} 
	 } // for
	 
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
   *
   */
  public void calculateSDSpectrum() throws RemoteException {
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    DiscretizedFuncList functions = miner.getSDSpectrum(saFunction, faVal,
        fvVal, siteClass, dataEdition);
    addDataInfo(functions.getInfo());
    getFunctionsForSDSpectrum(functions);
  }

  public void calculateSDSpectrum(ArrayList<Location> locations,
		  ArrayList<String> siteConditions, String outFile) {
	  HSSFWorkbook xlOut = getOutputFile(outFile);
	 // Create the output sheet
	 HSSFSheet xlSheet = xlOut.getSheet("SD Spectra");
	 if(xlSheet==null)
		 xlSheet = xlOut.createSheet("SD Spectra");
	 
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
	 
	 // Data Generation Explanation
	 //xlRow = xlSheet.createRow(startRow++);
	 //xlRow.createCell((short) 1).setCellValue("SMs = Fa*Ss");
	 //xlRow.createCell((short) 2).setCellValue("SM1 = Fv*S1");
	 
	 // Header row
	 String[] headers = {"Latitude (Degrees)", "Longitude (Degrees)", "Site Class", "Grid Spacing Basis", "Fa", "Fv", "Period (sec)", "Sa (g)", "Sd (inches)"};
	 short[] colWidths = {4500, 4500, 3000, 5000, 3000, 3000, 3000, 3000, 3000};
	 ++startRow; // We want a blank row
	 xlRow = xlSheet.createRow(startRow++);
	 for(short i = 0; i < headers.length; ++i) {
		 xlRow.createCell(i).setCellValue(headers[i]);
		 xlRow.getCell(i).setCellStyle(headerStyle);
		 xlSheet.setColumnWidth(i, colWidths[i]);
	 }
	 
	 // A calculator
	 FaFvCalc calc = new FaFvCalc();
	 
	 // Start plugging in the data
	 int answer = 1;
	 BatchProgress bp = new BatchProgress("Computing SD Spectra", locations.size());
	 bp.start();
	 for(int i = 0; i < locations.size(); ++i) {
		 bp.update(i+1);
		 xlRow = xlSheet.createRow(i+startRow);
		 double curLat = locations.get(i).getLatitude();
		 double curLon = locations.get(i).getLongitude();
		 DiscretizedFuncAPI saFunc = null;
		 DiscretizedFuncAPI sdFunc = null;
		 String curGridSpacing = "";
		 Float curFa = Float.MAX_VALUE;
		 Float curFv = Float.MAX_VALUE;
		 
		 String curCond = siteConditions.get(i);
		 // double coef = (double) 2 / 3;
		 
		 try {
			getCalculateSsS1Function(curLat, curLon);
			
			double curSs = getSs();
			double curSa = getSa();
			
			String reg1 = "^.*Data are based on a ";
			String reg2 = " deg grid spacing.*$";
			curGridSpacing = Pattern.compile(reg1, Pattern.DOTALL).matcher(saFunction.getInfo()).replaceAll("");
			curGridSpacing = Pattern.compile(reg2, Pattern.DOTALL).matcher(curGridSpacing).replaceAll("");
			curGridSpacing += " Degrees";
			
			curFa = (float) calc.getFa(curCond, curSs);
			curFv = (float) calc.getFv(curCond, curSa);

		    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
		    DiscretizedFuncList functions = miner.getSDSpectrum(saFunction, curFa,
		        curFv, curCond, dataEdition);
			
		    saFunc = functions.get(1);
		    sdFunc = functions.get(0);
		    
		} catch (RemoteException e) {
			if(answer != 0) {
				Object[] options = {"Suppress Future Warnings", "Continue Calculations", "Abort Run"};
				answer = JOptionPane.showOptionDialog(null, "Failed to retrieve information for:\nLatitude: " +
							curLat + "\nLongitude: " + curLon, "Data Mining Error", 0, 
							JOptionPane.ERROR_MESSAGE, null, options, options[0]);
			}
			if(answer == 2) {
				bp.update(locations.size());
				break;
			}
			saFunc = new ArbitrarilyDiscretizedFunc();
			sdFunc = new ArbitrarilyDiscretizedFunc();
			curGridSpacing = "Location out of Region";
			++startRow;
		} finally {
		 xlRow.createCell((short) 0).setCellValue(curLat);
		 xlRow.createCell((short) 1).setCellValue(curLon);
		 xlRow.createCell((short) 2).setCellValue(curCond.substring(curCond.length()-1));
		 xlRow.createCell((short) 3).setCellValue(curGridSpacing);
		 xlRow.createCell((short) 4).setCellValue(Double.parseDouble(saValFormat.format(curFa)));
		 xlRow.createCell((short) 5).setCellValue(Double.parseDouble(saValFormat.format(curFv)));
		 for(int j = 0; j < saFunc.getNum(); ++j) {
			 xlRow.createCell((short) 6).setCellValue(
					 Double.parseDouble(saValFormat.format(saFunc.getX(j))));
			 xlRow.createCell((short) 7).setCellValue(
					 Double.parseDouble(saValFormat.format(saFunc.getY(j))));
			 xlRow.createCell((short) 8).setCellValue(
					 Double.parseDouble(saValFormat.format(sdFunc.getY(j))));
			 ++startRow;
			 xlRow = xlSheet.createRow(i+startRow);
		 }
		} 
	 } // for
	 
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
   * Sets the selected geographic region.
   * @param region String
   */
  public void setRegion(String region) {
    geographicRegion = region;
  }

  /**
   * Sets the selected data edition.
   * @param edition String
   */
  public void setEdition(String edition) {
    dataEdition = edition;
  }

  /**
   * Sets the Fa value.
   * @param fa double
   */
  public void setFa(float fa) {
    faVal = fa;
  }

  /**
   * Sets the Fv value.
   * @param fv double
   */
  public void setFv(float fv) {
    fvVal = fv;
  }

  /**
   * Sets the selected site class
   * @param siteClass String
   */
  public void setSiteClass(String siteClass) {
    this.siteClass = siteClass;
  }

  /**
   * Returns the site class
   * @return String
   */
  public String getSelectedSiteClass() {
    return siteClass;
  }

  /**
   * Sets the Spectra type
   * @param spectraType String
   */
  public void setSpectraType(String spectraType) {
    selectedSpectraType = spectraType;
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
