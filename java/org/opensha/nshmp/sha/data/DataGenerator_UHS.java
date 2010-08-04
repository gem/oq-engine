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
import java.text.NumberFormat;
import java.text.ParseException;
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
import org.opensha.nshmp.sha.data.api.DataGeneratorAPI_UHS;
import org.opensha.nshmp.util.BatchProgress;
import org.opensha.nshmp.util.GlobalConstants;

/**
 * <p>Title: DataGenerator_UHS</p>
 *
 * <p>Description: This class acts as the data model for the Uniform Hazard Spectra Option. </p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public class DataGenerator_UHS
    implements DataGeneratorAPI_UHS {

  //gets the selected region
  protected String geographicRegion;
  //gets the selected edition
  protected String dataEdition;

  protected ArbitrarilyDiscretizedFunc saFunction;
  protected ArbitrarilyDiscretizedFunc saSdFunction;
  protected ArbitrarilyDiscretizedFunc sdTFunction;

  protected float faVal = 1.0f;
  protected float fvVal = 1.0f;
  protected String siteClass = GlobalConstants.SITE_CLASS_B;
  protected ArbitrarilyDiscretizedFunc sdSpectrumSaSdFunction;
  protected ArbitrarilyDiscretizedFunc smSpectrumSaSdFunction;

  protected ArbitrarilyDiscretizedFunc sdSpectrumSaTFunction;
  protected ArbitrarilyDiscretizedFunc smSpectrumSaTFunction;

  protected ArbitrarilyDiscretizedFunc approxUHSpectrumSaTFunction;
  protected ArbitrarilyDiscretizedFunc approxUHSpectrumSaSdFunction;

  private ArbitrarilyDiscretizedFunc pgaFunction;

  //holds all the data and its info in a String format.
  protected String dataInfo = "";

  //metadata to be shown when plotting the curves
  protected String metadataForPlots;

  //sets the selected spectra type
  protected String selectedSpectraType;

  private double sa, ss;

  private DecimalFormat saFormat = new DecimalFormat("0.000");

  private void getSASsVals() {
    int numPoints = saFunction.getNum();
    for (int i = 0; i < numPoints; ++i) {
      String periodVal = saFormat.format(saFunction.getX(i));
      // double period = Double.parseDouble(periodVal);
      double period;
      try {
    	  period = NumberFormat.getInstance().parse(periodVal).doubleValue();
      } catch (ParseException pex) {
    	  period = Double.parseDouble(periodVal);
      }
      if (period == 0.2) {
        ss = saFunction.getY(i);
      }
      else if (period == 1.0) {
        sa = saFunction.getY(i);
      }
    }
  }

  /**
   * Returns the SA at .2sec
   * @return double
   */
  public double getSs() {
    return ss;
  }

  /**
   * Returns the SA at 1 sec
   * @return double
   */
  public double getSa() {
    return sa;
  }

  /**
   *
   * @default class constructor
   */
  public void calculateApproxUHS() throws RemoteException {
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    DiscretizedFuncList functions = miner.getApprox_UHSpectrum(pgaFunction);
    addDataInfo(functions.getInfo());
    getFunctionsForApprox_UHSpectrum(functions);
  }

  /**
   *
   * @param mapSpectrumFunctions DiscretizedFuncList
   */
  protected void getFunctionsForApprox_UHSpectrum(DiscretizedFuncList
                                                  mapSpectrumFunctions) {

    int numFunctions = mapSpectrumFunctions.size();

    int i = 0;
    for (; i < numFunctions; ++i) {
      ArbitrarilyDiscretizedFunc tempFunction = (ArbitrarilyDiscretizedFunc)
          mapSpectrumFunctions.get(i);
      if (tempFunction.getName().equals(GlobalConstants.
                                        APPROX_UNIFORM_HAZARD_SPECTRUM_NAME +
                                        " of " +
                                        GlobalConstants.SA_Vs_T_GRAPH_NAME)) {
        approxUHSpectrumSaTFunction = tempFunction;
        break;
      }
    }

    ArbitrarilyDiscretizedFunc tempSDFunction = (ArbitrarilyDiscretizedFunc)
        mapSpectrumFunctions.get(1 - i);

    approxUHSpectrumSaSdFunction = tempSDFunction.getYY_Function(
        approxUHSpectrumSaTFunction);
    approxUHSpectrumSaSdFunction.setName(GlobalConstants.
                                         APPROX_UNIFORM_HAZARD_SPECTRUM_NAME +
                                         " of " +
                                         GlobalConstants.SA_Vs_SD_GRAPH_NAME);
    String info = metadataForPlots;
    info += "Site Class -" + siteClass + "\n";
    info += "Fa = " + faVal + " Fv = " + fvVal + "\n";

    approxUHSpectrumSaSdFunction.setInfo(info);
    approxUHSpectrumSaTFunction.setInfo(info);
    approxUHSpectrumSaSdFunction.setYAxisName(GlobalConstants.SA);
    approxUHSpectrumSaSdFunction.setXAxisName(GlobalConstants.SD);
    approxUHSpectrumSaTFunction.setYAxisName(GlobalConstants.SA);
    approxUHSpectrumSaTFunction.setXAxisName(GlobalConstants.PERIOD_NAME);
  }

  /**
   *
   * @param smSpectrumFunctions DiscretizedFuncList
   */
  protected void getFunctionsForSMSpectrum(DiscretizedFuncList
                                           smSpectrumFunctions) {

    int numFunctions = smSpectrumFunctions.size();
    int i = 0;
    for (; i < numFunctions; ++i) {
      ArbitrarilyDiscretizedFunc tempFunction = (ArbitrarilyDiscretizedFunc)
          smSpectrumFunctions.get(i);
      if (tempFunction.getName().equals(GlobalConstants.
                                        SITE_MODIFIED_SA_Vs_T_GRAPH)) {
        smSpectrumSaTFunction = tempFunction;
        break;
      }
    }

    ArbitrarilyDiscretizedFunc tempSDFunction = (ArbitrarilyDiscretizedFunc)
        smSpectrumFunctions.get(1 - i);
    smSpectrumSaSdFunction = tempSDFunction.getYY_Function(
        smSpectrumSaTFunction);
    smSpectrumSaSdFunction.setName(GlobalConstants.SITE_MODIFIED_SA_Vs_SD_GRAPH);
    String info = metadataForPlots;
    info += "Site Class -" + siteClass + "\n";
    info += "Fa = " + faVal + " Fv = " + fvVal + "\n";

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
    info += "Site Class -" + siteClass + "\n";
    info += "Fa = " + faVal + " Fv = " + fvVal + "\n";
    sdSpectrumSaSdFunction.setInfo(info);
    sdSpectrumSaTFunction.setInfo(info);
    sdSpectrumSaSdFunction.setYAxisName(GlobalConstants.SA);
    sdSpectrumSaSdFunction.setXAxisName(GlobalConstants.SD);
    sdSpectrumSaTFunction.setYAxisName(GlobalConstants.SA);
    sdSpectrumSaTFunction.setXAxisName(GlobalConstants.PERIOD_NAME);
  }

  /**
   *
   *
   */
  public void calculateSMSpectrum() throws RemoteException {
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    DiscretizedFuncList functions = miner.getSM_UHSpectrum(pgaFunction, faVal,
        fvVal, siteClass);
    addDataInfo(functions.getInfo());
    getFunctionsForSMSpectrum(functions);
  }

  /**
   *
   */
  public void calculateSDSpectrum() throws RemoteException {
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    DiscretizedFuncList functions = miner.getSD_UHSpectrum(pgaFunction, faVal,
        fvVal, siteClass);
    addDataInfo(functions.getInfo());
    getFunctionsForSDSpectrum(functions);
  }

  /**
   *
   * @param sdSpectrumFunctions DiscretizedFuncList
   */
  private void getFunctionsForSDT(DiscretizedFuncList functions) {

    int numFunctions = functions.size();
    int i = 0;
    for (; i < numFunctions; ++i) {
      ArbitrarilyDiscretizedFunc tempFunction = (ArbitrarilyDiscretizedFunc)
          functions.get(i);
      if (tempFunction.getName().equals(GlobalConstants.
                                        UNIFORM_HAZARD_SPECTRUM_NAME + " of " +
                                        GlobalConstants.SA_Vs_T_GRAPH_NAME)) {
        saFunction = tempFunction;
      }

      else if (tempFunction.getName().equals(GlobalConstants.UHS_PGA_FUNC_NAME)) {
        pgaFunction = tempFunction;
      }
      else {
        sdTFunction = tempFunction;
      }
    }

    saSdFunction = sdTFunction.getYY_Function(
        saFunction);
    saSdFunction.setName(GlobalConstants.UNIFORM_HAZARD_SPECTRUM_NAME + " of " +
                         GlobalConstants.SA_Vs_SD_GRAPH_NAME);
    saSdFunction.setInfo(metadataForPlots);
    saFunction.setInfo(metadataForPlots);
    saSdFunction.setYAxisName(GlobalConstants.SA);
    saSdFunction.setXAxisName(GlobalConstants.SD);
    saFunction.setYAxisName(GlobalConstants.SA);
    saFunction.setXAxisName(GlobalConstants.PERIOD_NAME);
  }

  /**
   * Gets the data for SsS1 in case region specified is not a Territory and
   * user specifies zip code for the location.
   *
   * @param zipCode String
   * @throws ZipCodeErrorException
   * @todo Implement this org.opensha.nshmp.sha.data.api.DataGeneratorAPI_UHS method
   */
  public void calculateUHS(String zipCode) throws ZipCodeErrorException,
      RemoteException {
    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    DiscretizedFuncList funcList = miner.getSA(geographicRegion, dataEdition,
                                               zipCode, selectedSpectraType);
    String location = "ZipCode - " + zipCode;
    createMetadataForPlots(location);
    addDataInfo(funcList.getInfo());
    getFunctionsForSDT(funcList);
    getSASsVals();
  }

  /**
   * Gets the data for SsS1 in case region specified is not a Territory and
   * user specifies Lat-Lon for the location.
   *
   * @param lat double
   * @param lon double
   * @todo Implement this org.opensha.nshmp.sha.data.api.DataGeneratorAPI_UHS method
   */
  public void calculateUHS(double lat, double lon) throws RemoteException {

    HazardDataMinerAPI miner = new HazardDataMinerServletMode();
    DiscretizedFuncList funcList = miner.getSA(geographicRegion, dataEdition,
                                               lat, lon, selectedSpectraType);
    String location = "Lat - " + lat + "  Lon - " + lon;
    createMetadataForPlots(location);
    addDataInfo(funcList.getInfo());
    getFunctionsForSDT(funcList);
    getSASsVals();
  }

  public void calculateUHS(ArrayList<Location> locations, String outFile) {
	 HSSFWorkbook xlOut = getOutputFile(outFile);
	 // Create the output sheet
	 HSSFSheet xlSheet = xlOut.getSheet("Uniform Hazard Spectra");
	 if(xlSheet==null)
		 xlSheet = xlOut.createSheet("Uniform Hazard Spectra");
	 
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
	 
	 // Return Period
	 xlRow = xlSheet.createRow(startRow++);
	 xlRow.createCell((short) 0).setCellValue("Spectra Type:");
	 xlRow.getCell((short) 0).setCellStyle(headerStyle);
	 xlRow.createCell((short) 1).setCellValue(selectedSpectraType);
	 ++startRow; // We would like a blank line.
	 // Column Headers
	 xlRow = xlSheet.createRow(startRow++);
	 String[] headers = {"Latitude (Degrees)", "Longitude (Degrees)", "Site Class", "Grid Spacing Basis", "Period (sec)", "Sa (g)", "Sd (inches)"};
	 short[] colWidths = {4500, 4500, 3000, 5000, 3000, 3000, 3000};
	 for(short i = 0; i < headers.length; ++i) {
		 xlRow.createCell(i).setCellValue(headers[i]);
		 xlRow.getCell(i).setCellStyle(headerStyle);
		 xlSheet.setColumnWidth(i, colWidths[i]);
	 }
	 
	 // Write the data information
	 int answer = 1;
	 BatchProgress bp = new BatchProgress("Computing Uniform Hazard Response Spectra", locations.size());
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
			 HazardDataMinerAPI miner = new HazardDataMinerServletMode();
			 DiscretizedFuncList funcList = miner.getSA(geographicRegion, dataEdition,
					 curLat, curLon, selectedSpectraType);
			saFunc = funcList.get(1);
			sdFunc = funcList.get(0);
			
			String reg1 = "^.*Data are based on a ";
			String reg2 = " deg grid spacing.*$";
			curGridSpacing = Pattern.compile(reg1, Pattern.DOTALL).matcher(funcList.getInfo()).replaceAll("");
			curGridSpacing = Pattern.compile(reg2, Pattern.DOTALL).matcher(curGridSpacing).replaceAll("");
			curGridSpacing += " Degrees";
		} catch (Exception e) {
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
			saFunc = new ArbitrarilyDiscretizedFunc();
			sdFunc = new ArbitrarilyDiscretizedFunc();
			
			curGridSpacing = "Location out of Region";
			++startRow;
		} finally {
		 xlRow.createCell((short) 0).setCellValue(curLat);
		 xlRow.createCell((short) 1).setCellValue(curLon);
		 xlRow.createCell((short) 2).setCellValue("B/C Boundary");
		 xlRow.createCell((short) 3).setCellValue(curGridSpacing);
		 for(int j = 0; j < saFunc.getNum(); ++j) {
			 xlRow.createCell((short) 4).setCellValue(
					 Double.parseDouble(saFormat.format(saFunc.getX(j))));
			 xlRow.createCell((short) 5).setCellValue(
			 		 Double.parseDouble(saFormat.format(saFunc.getY(j))));
			 xlRow.createCell((short) 6).setCellValue(
					 Double.parseDouble(saFormat.format(sdFunc.getY(j))));
			 ++startRow;
			 xlRow = xlSheet.createRow(i+startRow);
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
  
  protected void createMetadataForPlots(String location) {
    metadataForPlots = GlobalConstants.SA_DAMPING + "\n";
    metadataForPlots += geographicRegion + "\n";
    metadataForPlots += dataEdition + "\n";
    metadataForPlots += location + "\n";
  }

  /**
   * Removes all the calculated data.
   */
  public void clearData() {
    dataInfo = "";
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
    dataInfo += data + "\n\n";
  }

  /**
   * Returns the list of functions for plotting.
   * @param isUHSFunctionNeeded boolean
   * @param isApproxUHSFunctionNeeded boolean
   * @param isSDSpectrumFunctionNeeded boolean
   * @param isSMSpectrumFunctionNeeded boolean
   * @return ArrayList
   */
  public ArrayList getFunctionsToPlotForSA(boolean isUHSFunctionNeeded,
                                           boolean isApproxUHSFunctionNeeded,
                                           boolean isSDSpectrumFunctionNeeded,
                                           boolean isSMSpectrumFunctionNeeded) {
    ArrayList<DiscretizedFuncAPI> functions = new ArrayList<DiscretizedFuncAPI>();
    if (isUHSFunctionNeeded) {
      functions.add(saFunction);
      functions.add(saSdFunction);
    }
    if (isApproxUHSFunctionNeeded) {
      functions.add(approxUHSpectrumSaTFunction);
      functions.add(approxUHSpectrumSaSdFunction);
    }
    if (isSMSpectrumFunctionNeeded) {
      functions.add(smSpectrumSaTFunction);
      functions.add(smSpectrumSaSdFunction);
    }
    if (isSDSpectrumFunctionNeeded) {
      functions.add(sdSpectrumSaTFunction);
      functions.add(sdSpectrumSaSdFunction);
    }
    return functions;
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
