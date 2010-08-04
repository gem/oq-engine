/**
 * 
 */
package org.opensha.sha.cybershake;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.apache.commons.lang.SystemUtils;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.gui.infoTools.ConnectToCVM;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.util.SiteTranslator;

/**
 * @author nitingupta
 *
 */
public class IML_Calc_Cybershake extends MedianCalc_Cybershake {

	
	private int sourceIndex,rupIndex;
	
	/**
	 * 
	 */
	public IML_Calc_Cybershake(String inputFileName, String dirName) {
		// TODO Auto-generated constructor stub
		super(inputFileName,dirName);
	}

	  protected void parseFile() throws FileNotFoundException,IOException{

	      ArrayList fileLines = null;

	      fileLines = FileUtils.loadFile(inputFileName);

	      int j = 0;
	      int numIMRdone=0;
	      int numIMRs=0;
	      int numIMTdone=0;
	      int numIMTs=0;
	      int numSitesDone=0;
	      int numSites =0;
	      for(int i=0; i<fileLines.size(); ++i) {
	        String line = ((String)fileLines.get(i)).trim();
	        // if it is comment skip to next line
	        if(line.startsWith("#") || line.equals("")) continue;
	        if(j==0)getERF(line);
	        if(j==1){
	          boolean toApplyBackGround = Boolean.parseBoolean(line.trim());
	          toApplyBackGroud(toApplyBackGround);
	        }
	        if(j==2){
	          double rupOffset = Double.parseDouble(line.trim());
	          setRupOffset(rupOffset);
	        }
	        if(j==3){
		      int sourceIndex = Integer.parseInt(line.trim());
		      this.setSourceIndex(sourceIndex);
		    }
	        if(j==4){
	           int ruptureIndex = Integer.parseInt(line.trim());
			   this.setRuptureIndex(ruptureIndex);
			}
	        if(j==5)
	          numIMRs = Integer.parseInt(line.trim());
	        if(j==6){
	            setIMR(line.trim());
	            ++numIMRdone;
	            if(numIMRdone == numIMRs)
	              ++j;
	            continue;
	        }
	        if(j==7)
	          numIMTs = Integer.parseInt(line.trim());
	        if(j==8){
	          setIMT(line.trim());
	          ++numIMTdone;
	          if (numIMTdone == numIMTs)
	            ++j;
	          continue;
	        }
	        if(j==9)
	          numSites = Integer.parseInt(line.trim());
	        if(j==10){
	          setSite(line.trim());
	          ++numSitesDone;
	          if (numSitesDone == numSites)
	            ++j;
	          continue;
	        }
	        ++j;
	      }
	      getWillsSiteAndBasinDepth();
	  }	

	  
	  /**
	   * Gets the list of locations with their Wills Site Class values
	   * @param line String
	   */
	  protected void setSite(String line){
	    if(locList == null)
	      locList = new LocationList();
	    StringTokenizer st = new StringTokenizer(line);
	    int tokens = st.countTokens();
	    if(tokens > 3 || tokens < 2){
	      throw new RuntimeException("Must Enter valid Lat Lon in each line in the file");
	    }
	    double lat = Double.parseDouble(st.nextToken().trim());
	    double lon = Double.parseDouble(st.nextToken().trim());
	    Location loc = new Location(lat,lon);
	    locList.add(loc);
	  }	

	  
	  /**
	   * Gets the list of locations with their Wills Site Class values
	   * @param line String
	   */
	  /*private void getWillsSiteAndBasinDepth(){


		  if(willsSiteClassVals == null)
		     willsSiteClassVals = new ArrayList();
		  if(basinDepthVals == null)
		     basinDepthVals = new ArrayList();
		  String willsClass="";
		  Double basinDepth =  null;
		    
		      
	      int numLocations = locList.size();
	      for(int i=0;i<numLocations;++i){
	    	  LocationList siteLocListForWillsSiteClass = new LocationList();
		      siteLocListForWillsSiteClass.addLocation(locList.getLocationAt(i));
		      try{
		        willsClass = (String) ConnectToCVM.getWillsSiteTypeFromCVM(
		            siteLocListForWillsSiteClass).get(0);
		        if(willsClass.equals("NA"))
		        	willsClass = SiteTranslator.WILLS_DE;
		        basinDepth = (Double)ConnectToCVM.getBasinDepthFromCVM(siteLocListForWillsSiteClass).get(0);
		        
		      }catch(Exception e){
		        e.printStackTrace();
		      }
		       //System.out.println("WillsSiteClass :"+willsClass +" BasinDepth = "+basinDepth);
		      if(basinDepth == null)	
		        basinDepthVals.add(new Double(Double.NaN));
		      else
		         basinDepthVals.add(basinDepth);
		       willsSiteClassVals.add(willsClass);
	     }
	  }*/
	  
	  
	  /**
	   * Gets the Wills Site Class Vals and Basin Depth values for the Locations in file
	   *
	   */
	  private void getWillsSiteAndBasinDepth(){
		  
		  try{
			  ArrayList willsSiteVals =ConnectToCVM.getWillsSiteTypeFromCVM(-121, -113.943965, 31.082920, 36.621696, .016667);
			  ArrayList basinVals = ConnectToCVM.getBasinDepthFromCVM(-121, -113.943965, 31.082920, 36.621696, .016667);
			  GriddedRegion region = 
				  new GriddedRegion(
						  new Location(31.082920, -121),
						  new Location(36.621696, -113.943965),
						  .016667, new Location(0,0));
			  int numLocs = locList.size();
			  basinDepthVals = new ArrayList();
			  willsSiteClassVals = new ArrayList();
			  for(int i=0;i<numLocs;++i){
				  int index = region.indexForLocation(locList.get(i));
				  basinDepthVals.add(basinVals.get(index));
				  String willsVal = (String)willsSiteVals.get(index);
				  if(willsVal.equals("NA"))
					  willsVal = SiteTranslator.WILLS_DE;
				  willsSiteClassVals.add(willsVal);
			  }
			  
		  }catch(Exception e){
		    throw new RuntimeException(e);
		  }
	  }
	  
	/**
	 * Sets the source Index for calculation needs to be done
	 * @param sourceIndex
	 */  
	private void setSourceIndex(int sourceIndex){
		this.sourceIndex = sourceIndex;
	}
	
	/**
	 * Sets the rupture Index for the calculations that needs to be done
	 * @param ruptureIndex
	 */
	private void setRuptureIndex (int ruptureIndex){
		this.rupIndex = ruptureIndex;
	}
	
	 /**
	   * Generates the Mean and Sigma files for selected Attenuation Relationship application
	   * @param imr AttenuationRelationshipAPI
	   * @param dirName String
	   */
	  protected void generateMedian(ScalarIntensityMeasureRelationshipAPI imr,
	                                          String imtLine,
	                                          String dirName) {

	    // get total number of sources
	    int numSources = forecast.getNumSources();


	    // init the current rupture number
	    int currRuptures = 0;

	    // set the Site in IMR
	    try {
	      FileWriter imlFile;

	      String fileNamePrefixCommon = dirName +
	      SystemUtils.FILE_SEPARATOR + imr.getShortName();

	      // opens the files for writing
	      StringTokenizer st = new StringTokenizer(imtLine);
	      int numTokens = st.countTokens();
	      String imt = st.nextToken().trim();
	      imr.setIntensityMeasure(imt);
	 
	      String pd = "";
	      if (numTokens == 2) {
	        pd = st.nextToken().trim();
	        if (pd != null && !pd.equals(""))	
	        	  imr.getParameter(PeriodParam.NAME).setValue(new Double(Double.parseDouble(pd)));
	        imlFile = new FileWriter(fileNamePrefixCommon + "_" +
	                                       imt + "_" + pd + ".txt");
	      }
	      else
	    	  imlFile = new FileWriter(fileNamePrefixCommon + "_" +
	                                       imt + ".txt");
	          imlFile.write("#Lat \t Lon \t SA@3sec \n");
	     
       	      ProbEqkSource source = forecast.getSource(sourceIndex);
       	      ProbEqkRupture rupture = source.getRupture(rupIndex);
       	      rupture.setProbability(1.0);
	          imr.setEqkRupture(rupture);
	          imr.setExceedProb(0.5);
	          
	          int numSites = locList.size();
	
	          //looping over all the sites for the selected Attenuation Relationship
	          for (int j = 0; j < numSites; ++j) {
	            setSiteParamsInIMR(imr, (String) willsSiteClassVals.get(j),(Double)basinDepthVals.get(j));
	            //this method added to the Attenuation Relationship allows to set the
	            //Location in the site of the attenuation relationship
	            Location loc = (Location)locList.get(j);
	            imr.setSiteLocation(loc);
	            double iml = Math.exp(imr.getIML_AtExceedProb());
	            imlFile.write(format.format(loc.getLatitude())+"\t"+format.format(loc.getLongitude())+"\t"+format.format(iml)+"\n");
	            //setting different intensity measures for each site and writing those to the file.
	          }
	          imlFile.close();
	    }
	    catch (Exception e) {
	      e.printStackTrace();
	    }
	  }	
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		   if(args.length != 2){
			      System.out.println("Usage :\n\t"+"java -jar [jarfileName] [inputFileName] [output directory name]\n\n");
			      System.out.println("jarfileName : Name of the executable jar file, by default it is MeanSigmaCalc.jar");
			      System.out.println("inputFileName :Name of the input file, this input file should contain only 3 columns"+
			                         " \"Lon Lat Vs30\", For eg: see \"MeanSigmaCalc_InputFile.txt\". ");
			      System.out.println("output directory name : Name of the output directory where all the output files will be generated");
			      System.exit(0);
			    }

			    IML_Calc_Cybershake calc = new IML_Calc_Cybershake(args[0],args[1]);
			    try {
			      calc.parseFile();
			    }
			    catch (FileNotFoundException ex) {
			      ex.printStackTrace();
			    }
			    catch (IOException ex) {
			      ex.printStackTrace();
			    }
			    catch (Exception ex) {
			      ex.printStackTrace();
			    }

			    calc.createSiteList();
			    calc.getMedian();
	}

}
