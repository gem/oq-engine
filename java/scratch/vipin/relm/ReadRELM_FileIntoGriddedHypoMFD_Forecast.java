package scratch.vipin.relm;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.StringTokenizer;

import org.opensha.commons.exceptions.DataPoint2DException;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.griddedForecast.GriddedHypoMagFreqDistForecast;
import org.opensha.sha.earthquake.griddedForecast.HypoMagFreqDistAtLoc;
import org.opensha.sha.magdist.IncrementalMagFreqDist;


/**
 * <p>Title: ReadRELM_FileIntoGriddedHypoMFD_Forecast.java </p>
 * <p>Description: It reads the file given in RELM format and makes a GriddedHypoMagFreqDistForecast
 * from that file. Once we have this object, we can use it as any other forecast
 * or view it in a map.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class ReadRELM_FileIntoGriddedHypoMFD_Forecast extends GriddedHypoMagFreqDistForecast{
  private HypoMagFreqDistAtLoc magFreqDistForLocations[];
  private String inputFileName;

  /**
  * This function reads the input file and converts it into GriddedHypoMagFreqDistForecast.
  * @param inputFileName
  * @param griddedRegion
  * @param minMag
  * @param maxMag
  * @param numMagBins
  * @return
  */
 public ReadRELM_FileIntoGriddedHypoMFD_Forecast(String inputFileName,
                                                 GriddedRegion griddedRegion,
                                                 double minMag,
                                                 double maxMag,
                                                 int numMagBins,
                                                 boolean useMask,
                                                 boolean adjustLatLon) {
    setRegion(griddedRegion);
    this.inputFileName = inputFileName;
   // make HypoMagFreqDist for each location in the region
   magFreqDistForLocations = new HypoMagFreqDistAtLoc[this.getNumHypoLocs()];
   for(int i=0; i<magFreqDistForLocations.length; ++i ) {
     IncrementalMagFreqDist magFreqDist = new IncrementalMagFreqDist(minMag, maxMag, numMagBins);
     magFreqDist.setTolerance(magFreqDist.getDelta()/2);
     IncrementalMagFreqDist []magFreqDistArray = new IncrementalMagFreqDist[1];
     magFreqDistArray[0] = magFreqDist;
     magFreqDistForLocations[i] = new HypoMagFreqDistAtLoc(magFreqDistArray,griddedRegion.locationForIndex(i));
   }
   // read the file and calculate HypoMagFreqDist at each location
   calculateHypoMagFreqDistForEachLocation(useMask, adjustLatLon);
 }

 /*
  * computes the Mag-Rate distribution for each location within the provided region.
  */
  private void calculateHypoMagFreqDistForEachLocation(boolean useMask, boolean adjustLatLon) {
    try {
      FileReader fr = new FileReader(this.inputFileName);
      BufferedReader br = new BufferedReader(fr);
      String line = br.readLine();
     // SummedMagFreqDist summedMFD = new SummedMagFreqDist(5.0, 9.0, 41);
      //summedMFD.setTolerance(summedMFD.getDelta()/2);
      // go upto the line which says "begin_forecast"
      while(line!=null && !line.equalsIgnoreCase(WriteRELM_FileFromGriddedHypoMFD_Forecast.BEGIN_FORECAST)) {
        line = br.readLine();
      }
      // if it end of file, return
      if(line==null) return;
      // start reading forecast
      line = br.readLine();
      // read forecast until end of file or until "end_forecast" is encountered
      double lat1, lat2, lat;
      double lon1, lon2, lon;
      double mag1, mag2, mag;
      double rate;
      int mask;
      int locIndex;
      double totRate5=0, totRate6_5=0, totRate8=0, totRate8_05=0, filteredRate=0, tempRate=0;
      while(line!=null && !line.equalsIgnoreCase(WriteRELM_FileFromGriddedHypoMFD_Forecast.END_FORECAST)) {
        StringTokenizer tokenizer = new StringTokenizer(line);
        lon1= Double.parseDouble(tokenizer.nextToken());
        lon2 =  Double.parseDouble(tokenizer.nextToken());
        lat1 = Double.parseDouble(tokenizer.nextToken());
        lat2 = Double.parseDouble(tokenizer.nextToken());
        tokenizer.nextToken(); // min depth
        tokenizer.nextToken(); // max depth
        mag1= Double.parseDouble(tokenizer.nextToken());
        mag2 =  Double.parseDouble(tokenizer.nextToken());
        rate = Double.parseDouble(tokenizer.nextToken()); // rate
        mask = (int)Double.parseDouble(tokenizer.nextToken());
        if(useMask && mask!=1) {
        	line = br.readLine();
        	continue; // do not consider the masked locations
        }
        // calculate the midpoint of lon bin
        lon = (lon1+lon2)/2; 
        // midpoint of the lat bin
        lat = (lat1+lat2)/2; 
        if(adjustLatLon) {// this is added so that location can match the location in EvenlyGriddedRELM_TestingRegion
        	lon+=0.05;
        	lat+=0.05;
        }
        // calculate midpoint of mag bin
        mag = (mag1+mag2)/2;
        if(mag1>=8 || mag2>=8) {
        	//if(rate==0) System.out.println(lat1+","+lat2+","+lon1+","+lon2);
        	tempRate+=rate;
        }
        if(mag>9) mag=9.0;
        //System.out.println(mag);
        //summedMFD.add(mag,rate);
       
        if(mag>5 || (5-mag<0.005)) totRate5+=rate;
        if(mag>6.5 || (6.5-mag<0.005)) totRate6_5+=rate;
        if(mag>8 || (8-mag<0.005)) totRate8+=rate;
        if(mag>8.05 || (8.05-mag<0.005)) totRate8_05+=rate;
        locIndex = getRegion().indexForLocation(new Location(lat,lon));
        //continue if location not in the region
        if (locIndex >= 0)  {
          IncrementalMagFreqDist incrMagFreqDist = magFreqDistForLocations[locIndex].getMagFreqDistList()[0];
          try {
            int index = incrMagFreqDist.getXIndex(mag);
            incrMagFreqDist.set(mag, incrMagFreqDist.getY(index) + rate);
          }
          catch (DataPoint2DException dataPointException) {
            // do not do anything if this mag is not allowed
          }
        } else {
        	//System.out.println(lat+","+lon);
        	filteredRate+=rate;
        }
        line = br.readLine();
      }
      br.close();
      fr.close();
      System.out.println("Total Rates="+totRate5+","+totRate6_5+","+totRate8 +","+totRate8_05+",filteredRate="+filteredRate);
      System.out.println(tempRate);
      //System.out.println(summedMFD.getCumRateDist());
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

 /**
  * gets the Hypocenter Mag.
  *
  * @param ithLocation int : Index of the location in the region
  * @return HypoMagFreqDistAtLoc Object using which user can retrieve the
  *   Magnitude Frequency Distribution.
  * @todo Implement this
  *   org.opensha.sha.earthquake.GriddedHypoMagFreqDistAtLocAPI method
  */
 public HypoMagFreqDistAtLoc getHypoMagFreqDistAtLoc(int ithLocation) {
   return magFreqDistForLocations[ithLocation];
 }

}