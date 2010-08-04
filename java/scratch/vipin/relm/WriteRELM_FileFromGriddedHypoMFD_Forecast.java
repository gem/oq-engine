package scratch.vipin.relm;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.StringTokenizer;

import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.griddedForecast.GriddedHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * <p>Title: WriteRELM_FileFromGriddedHypoMFD_Forecast.java </p>
 * <p>Description: This class accepts a Gridded Hypo Mag Freq Dist forecast
 * and writes out a file in RELM format . </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class WriteRELM_FileFromGriddedHypoMFD_Forecast {

  private GriddedHypoMagFreqDistForecast griddedHypoMFD;
  private final static int MASK = 1;
  public final static String BEGIN_FORECAST = "begin_forecast";
  public final static String END_FORECAST = "end_forecast";
  

  public final static String MODEL_NAME = "modelname=";
  public final static String VERSION_NAME = "version=";
  public final static String AUTHOR_NAME = "author=";
  public final static String ISSUE_DATE_NAME = "issue_date=";
  public final static String FORECAST_START_DATE_NAME = "forecast_start_date=";
  public final static String FORECAST_DURATION_NAME = "forecast_duration=";

  private String modelName, version, author;
  private int issueYear, issueMonth, issueDay, issueHour, issueMinute, issueSecond, issueMilliSecond;
  private int startYear, startMonth, startDay, startHour, startMinute, startSecond, startMilliSecond;
  private double duration;
  private String durationUnits;
  private final static String TEMPLATE_FILENAME = "scratchJavaDevelopers/vipin/relm/forecast.qs.dat";

  /**
   *
   * @param griddedHypoMagFreqDistForecast
   */
  public WriteRELM_FileFromGriddedHypoMFD_Forecast(GriddedHypoMagFreqDistForecast
      griddedHypoMagFreqDistForecast) {
    setGriddedHypoMagFreqDistForecast(griddedHypoMagFreqDistForecast);
  }

  /**
  * Set the GriddedHypoMagFreqDistForecast
  * @param griddedHypoMagFreqDistForecast
  */
 public void setGriddedHypoMagFreqDistForecast(
     GriddedHypoMagFreqDistForecast griddedHypoMagFreqDistForecast) {
   this.griddedHypoMFD = griddedHypoMagFreqDistForecast;
 }

 /**
  * set the model name, version and author
  * @param modelName
  */
 public void setModelVersionAuthor(String modelName, String version, String author) {
   this.modelName = modelName;
   this.version = version;
   this.author = author;
 }

 /**
  * Set the issue date
  *
  * @param issueYear
  * @param issueMonth
  * @param issueDay
  * @param issueHour
  * @param issueMinute
  * @param issueSecond
  * @param issueMilliSecond
  */
 public void setIssueDate(int issueYear, int issueMonth, int issueDay,
                          int issueHour, int issueMinute, int issueSecond,
                          int issueMilliSecond) {
   this.issueYear = issueYear;
   this.issueMonth = issueMonth;
   this.issueDay = issueDay;
   this.issueHour = issueHour;
   this.issueMinute = issueMinute;
   this.issueSecond = issueSecond;
   this.issueMilliSecond = issueMilliSecond;
 }

 /**
  * Set forecast start date
  *
  * @param startYear
  * @param startMonth
  * @param startDay
  * @param startHour
  * @param startMinute
  * @param startSecond
  * @param startMilliSecond
  */
 public void setForecastStartDate(int startYear, int startMonth, int startDay,
                          int startHour, int startMinute, int startSecond,
                          int startMilliSecond) {
    this.startYear = startYear;
    this.startMonth = startMonth;
    this.startDay = startDay;
    this.startHour = startHour;
    this.startMinute = startMinute;
    this.startSecond = startSecond;
    this.startMilliSecond = startMilliSecond;
  }


  /**
   * Se the forecast duration
   *
   * @param duration
   * @param durationUnits
   */
  public void setDuration(double duration, String durationUnits) {
    this.duration = duration;
    this.durationUnits = durationUnits;
  }




  /**
  * Writes the GriddedHypoMagFreqDistForecast into an output file. The format
  * of the output file is in RELM format
  */
 public void makeFileInRELM_Format(String outputFileName) {
   try {
     FileWriter fw = new FileWriter(outputFileName);

     // Write the header lines. following lines represent header lines in the output file
     /*modelname=John's model
     version=1.0
     author=John Doe
     issue_date=2005,8,1,0,0,0,0
     forecast_start_date=2005,9,1,0,0,0,0
     forecast_duration=5,years*/

     fw.write(MODEL_NAME+modelName+"\n");
     fw.write(VERSION_NAME+version+"\n");
     fw.write(AUTHOR_NAME+author+"\n");
     fw.write(ISSUE_DATE_NAME+issueYear+","+issueMonth+","+issueDay+","+
              issueHour+","+issueMinute+","+issueSecond+","+issueMilliSecond+"\n");
     fw.write(FORECAST_START_DATE_NAME+startYear+","+startMonth+","+startDay+","+
              startHour+","+startMinute+","+startSecond+","+startMilliSecond+"\n");
     fw.write(FORECAST_DURATION_NAME+duration+","+durationUnits+"\n");
     // write the data lines
     fw.write(BEGIN_FORECAST+"\n");
     GriddedRegion region  = griddedHypoMFD.getRegion();
     int numLocs  = region.getNodeCount();
     double mag1, mag2; 
     double rate;
     double gridSpacing = region.getSpacing();
     
     // READ THE TEMPLATE FILE
     FileReader fr = new FileReader(TEMPLATE_FILENAME);
     BufferedReader br = new BufferedReader(fr);
     String line = br.readLine();
    // SummedMagFreqDist summedMFD = new SummedMagFreqDist(5.0, 9.0, 41);
     //summedMFD.setTolerance(summedMFD.getDelta()/2);
     // go upto the line which says "begin_forecast"
     while(line!=null && !line.equalsIgnoreCase(WriteRELM_FileFromGriddedHypoMFD_Forecast.BEGIN_FORECAST)) {
       line = br.readLine();
     }
     line= br.readLine();
     double lon1, lon2, lat1, lat2;
     double prevLon1=0, prevLon2=0, prevLat1=0, prevLat2=0;
     int depth1, depth2;
     // Iterrate over all locations and write Magnitude frequency distribution for each location
     while(line!=null) {
    	 if(line.equalsIgnoreCase(END_FORECAST)) break;
    	 StringTokenizer tokenizer = new StringTokenizer(line);
         lon1= Double.parseDouble(tokenizer.nextToken());
         lon2 =  Double.parseDouble(tokenizer.nextToken());
         lat1 = Double.parseDouble(tokenizer.nextToken());
         lat2 = Double.parseDouble(tokenizer.nextToken());
         if(prevLon1==lon1 && prevLon2==lon2 && prevLat1==lat1 && prevLat2==lat2) {
        	 line=br.readLine();
        	 continue;
         }
         prevLon1 = lon1;
         prevLon2 = lon2;
         prevLat1 = lat1;
         prevLat2 = lat2;
         
         depth1 = Integer.parseInt(tokenizer.nextToken());
         depth2 = Integer.parseInt(tokenizer.nextToken());
         
         Location loc1 = new Location(lat1, lon1);
         Location loc2 = new Location(lat1, lon2);
         Location loc3 = new Location(lat2, lon1);
         Location loc4 = new Location(lat2, lon2);
         
         HypoMagFreqDistAtLoc hypoMFD_AtLoc1 = griddedHypoMFD.getHypoMagFreqDistAtLoc(region.indexForLocation(loc1));
         IncrementalMagFreqDist incrementalMFD1 = hypoMFD_AtLoc1.getMagFreqDistList()[0];
         HypoMagFreqDistAtLoc hypoMFD_AtLoc2 = griddedHypoMFD.getHypoMagFreqDistAtLoc(region.indexForLocation(loc2));
         IncrementalMagFreqDist incrementalMFD2 = hypoMFD_AtLoc2.getMagFreqDistList()[0];
         HypoMagFreqDistAtLoc hypoMFD_AtLoc3 = griddedHypoMFD.getHypoMagFreqDistAtLoc(region.indexForLocation(loc3));
         IncrementalMagFreqDist incrementalMFD3 = hypoMFD_AtLoc3.getMagFreqDistList()[0];
         HypoMagFreqDistAtLoc hypoMFD_AtLoc4 = griddedHypoMFD.getHypoMagFreqDistAtLoc(region.indexForLocation(loc4));
         IncrementalMagFreqDist incrementalMFD4 = hypoMFD_AtLoc4.getMagFreqDistList()[0];
         
         for(int j=0; j<incrementalMFD1.getNum(); ++j) {
             mag1  = incrementalMFD1.getX(j)-incrementalMFD1.getDelta()/2;
             mag2  = incrementalMFD1.getX(j)+incrementalMFD1.getDelta()/2;
             rate  = (incrementalMFD1.getIncrRate(j)+incrementalMFD2.getIncrRate(j)+
             		incrementalMFD3.getIncrRate(j)+incrementalMFD4.getIncrRate(j))/4;
             if(j==incrementalMFD1.getNum()-1) mag2=10.0;
             fw.write((float)lon1+"\t"+(float)(lon2)+"\t"+
            		 (float)lat1+"\t"+(float)(lat2)+"\t"+depth1+"\t"+
                      depth2+"\t"+(float)mag1+"\t"+(float)mag2+"\t"+rate+"\t"+MASK+"\n");
           }
         line = br.readLine();
     }
     fw.write(END_FORECAST+"\n");
     fw.close();
   }catch(Exception e) {
     e.printStackTrace();
   }
 }
 /**
  *  
   * This test will make Frankel02 ERF, convert it into GriddedHypoMagFreqDistForecast and
   * then view it.
   * This function was tested for Frankel02 ERF.
   * Following testing procedure was applied(Region used was RELM Gridded region and
   *  min mag=5, max Mag=9, Num mags=41):
   * 1. Choose an arbitrary location say 31.5, -117.2
   * 2. Make Frankel02 ERF with Background only sources
   * 3. Modify Frankel02 ERF for testing purposes to use ONLY CAmapC_OpenSHA input file
   * 4. Now print the Magnitude Frequency distribution in Frankel02 ERF for that location
   * 5. Using the same ERF settings, get the Magnitude Frequency distribution using
   * this function and it should be same as we printed out in ERF.
   * 6. In another test, we printed out cum dist above Mag 5.0 for All locations.
   * The cum dist from Frankel02 ERF and from MFD retured from this function should
   * be same.
   * 7. Another test done was to make 3 files: One with only background, another with
   * only foregound and another with both. The rates in the "both file" was sum of
   * background and foreground
   *
   * @param args
   */
  public static void main(String[] args) {
	  // region to view the rates
	  CaliforniaRegions.RELM_TESTING_GRIDDED evenlyGriddedRegion  = new CaliforniaRegions.RELM_TESTING_GRIDDED();
	   /* EqkRupForecast eqkRupForecast = new Frankel02_AdjustableEqkRupForecast();
	    // include background sources as point sources
	    eqkRupForecast.setParameter(Frankel02_AdjustableEqkRupForecast.RUP_OFFSET_PARAM_NAME,
	                                new Double(10.0));
	    eqkRupForecast.setParameter(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_NAME,
	                                Frankel02_AdjustableEqkRupForecast.BACK_SEIS_INCLUDE);
	    eqkRupForecast.setParameter(Frankel02_AdjustableEqkRupForecast.BACK_SEIS_RUP_NAME,
	                               Frankel02_AdjustableEqkRupForecast.BACK_SEIS_RUP_POINT);
	    eqkRupForecast.getTimeSpan().setDuration(5.0);*/
	    
	   /*EqkRupForecast eqkRupForecast = new WGCEP_UCERF1_EqkRupForecast();
	   // include background sources as point sources
	   eqkRupForecast.setParameter(WGCEP_UCERF1_EqkRupForecast.RUP_OFFSET_PARAM_NAME,
	                               new Double(10.0));
	   eqkRupForecast.setParameter(WGCEP_UCERF1_EqkRupForecast.BACK_SEIS_NAME,
	                               Frankel02_AdjustableEqkRupForecast.BACK_SEIS_INCLUDE);
	   eqkRupForecast.setParameter(WGCEP_UCERF1_EqkRupForecast.BACK_SEIS_RUP_NAME,
	                               Frankel02_AdjustableEqkRupForecast.BACK_SEIS_RUP_POINT);
	   eqkRupForecast.setParameter(WGCEP_UCERF1_EqkRupForecast.FAULT_MODEL_NAME,
	                               Frankel02_AdjustableEqkRupForecast.FAULT_MODEL_STIRLING);
	   eqkRupForecast.setParameter(WGCEP_UCERF1_EqkRupForecast.TIME_DEPENDENT_PARAM_NAME,
	                               new Boolean(true));
	   eqkRupForeast.getTimeSpan().setDuration(5.0);*/
	   
	   
	   // write into RELM formatted file
	   /* WriteRELM_FileFromGriddedHypoMFD_Forecast writeRELM_File = new WriteRELM_FileFromGriddedHypoMFD_Forecast(griddedHypoMagFeqDistForecast);
	     String version="1.0 (";
	     // write the adjustable params
	     ParameterList paramList = eqkRupForecast.getAdjustableParameterList();
	     Iterator it= paramList.getParameterNamesIterator();
	     while(it.hasNext()) {
	       String paramName=(String)it.next();
	        version=version+paramName+"="+paramList.getValue(paramName).toString()+",";
	      }
	      // write the timespan adjustable params
	      paramList  = eqkRupForecast.getTimeSpan().getAdjustableParams();
	       it= paramList.getParameterNamesIterator();
	      while(it.hasNext()) {
	        String paramName=(String)it.next();
	        version=version+paramName+"="+paramList.getValue(paramName).toString()+",";
	      }
	      version=version+")";
	      //for(int i=0; i<paramList
	      writeRELM_File.setModelVersionAuthor("NSHMP-2002", version, "Originally from USGS, Golden. Rewritten by Ned Field in Java");
	      writeRELM_File.setIssueDate(2006, 0,0,0,0,0,0);
	      writeRELM_File.setForecastStartDate(2006, 0,0,0,0,0,0);
	      writeRELM_File.setDuration(5, "years");
	      writeRELM_File.makeFileInRELM_Format("NSHMP2002Rates.txt");*/
  }
}