package scratch.vipin.relm;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.StringTokenizer;


/**
 * <p>Title: CreateRELM_GriddedRegion.java </p>
 * <p>Description: This class reads  the RELM ouput file format and creates a ouput file
 * which can be read to make RELM_EvenlyGriddedRegion object </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class CreateRELM_GriddedRegion {
  public final static String GRIDDED_REGION_OUT_FILENAME = "RelmRegion.txt";

  /**
   * Read the RELM output file and create a file so that we can create a
   * file which can be used to create a RELM_EvenlyGriddedRegion object
   */
  public CreateRELM_GriddedRegion(String relmOuputFileName) {
    try {
      // read the RELM output file and get min and max lon for each lat in the region
      FileReader fr = new FileReader(relmOuputFileName);
      BufferedReader br = new BufferedReader(fr);
      String line = br.readLine();
     // go upto the line which says "begin_forecast"
     while(line!=null && !line.equalsIgnoreCase(WriteRELM_FileFromGriddedHypoMFD_Forecast.BEGIN_FORECAST)) {
       line = br.readLine();
     }
     // if it end of file, return
     if(line==null) return;
     // start reading forecast
     line = br.readLine();
     // read forecast until end of file or until "end_forecast" is encountered
     double lat1, lat2;
     double lon1, lon2;
     int locIndex;
     // calculate min and max lon for each lat in the region
     HashMap minLonsForLats = new HashMap(), maxLonsForLats = new HashMap();
     while(line!=null && !line.equalsIgnoreCase(WriteRELM_FileFromGriddedHypoMFD_Forecast.END_FORECAST)) {
       StringTokenizer tokenizer = new StringTokenizer(line);
       lon1= Double.parseDouble(tokenizer.nextToken());
       lon2 =  Double.parseDouble(tokenizer.nextToken());
       lat1 = Double.parseDouble(tokenizer.nextToken());
       lat2 = Double.parseDouble(tokenizer.nextToken());
       // update the min/max lons for a specific lat
       updateLonsForLat(lat1, lon1, lon2, minLonsForLats, maxLonsForLats);
       updateLonsForLat(lat2, lon1, lon2, minLonsForLats, maxLonsForLats);
       line = br.readLine();
     }
     br.close();
     fr.close();
     // sort the lats
     ArrayList latList = new ArrayList(minLonsForLats.keySet());
     Collections.sort(latList);
     // write the min lon for each lat first.
     FileWriter fw = new FileWriter(GRIDDED_REGION_OUT_FILENAME);
     for(int i=0; i<latList.size(); ++i) {
       fw.write("locList.addLocation(new Location("+((Double)latList.get(i)).doubleValue()+","+
                ((Double)minLonsForLats.get(latList.get(i))).doubleValue()+"));\n");
     }
     // now write the max lon for each lat
     for(int i=latList.size()-1; i>=0; --i) {
       fw.write("locList.addLocation(new Location("+((Double)latList.get(i)).doubleValue()+","+
                ((Double)maxLonsForLats.get(latList.get(i))).doubleValue()+"));\n");
     }
     fw.close();
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * Update the Hashmaps representing the min and max lons for each lat in the region
   *
   * @param lat1  Latitude for which longitudes may need to be updated
   * @param lon1
   * @param lon2
   * @param minLonsForLats
   * @param maxLonsForLats
   */
  private void updateLonsForLat(double lat, double lon1, double lon2,
                                HashMap minLonsForLats, HashMap maxLonsForLats) {
    Double latObj = new Double(lat);
    // Update the min lon hashmap
    double currLonMin=Double.POSITIVE_INFINITY;
    if(minLonsForLats.containsKey(latObj)) {
      currLonMin = ((Double)minLonsForLats.get(latObj)).doubleValue();
    }
    if(lon1<currLonMin) minLonsForLats.put(latObj, new Double(lon1));
    if(lon2<lon1) minLonsForLats.put(latObj, new Double(lon2));

    // update the max lon hashmap
  double currLonMax=Double.NEGATIVE_INFINITY;
  if(maxLonsForLats.containsKey(latObj)) {
    currLonMax = ((Double)maxLonsForLats.get(latObj)).doubleValue();
  }
  if(lon1>currLonMax) maxLonsForLats.put(latObj, new Double(lon1));
  if(lon2>lon1) maxLonsForLats.put(latObj, new Double(lon2));

  }

  public static void main(String[] args) {
    new CreateRELM_GriddedRegion("alm.forecast");
  }

}