package scratch.vipin;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.StringTokenizer;

import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: FaultSections.java </p>
 * <p>Description: It loads the fault sections from text files.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class FaultSections {
  private final static String INPUT_FILE_NAME1 = "scratchJavaDevelopers/ned/NSHMP02_CA_Traces_N.txt";
  private final static String INPUT_FILE_NAME2 = "scratchJavaDevelopers/ned/NSHMP02_CA_Traces_RV.txt";
  private final static String INPUT_FILE_NAME3 = "scratchJavaDevelopers/ned/NSHMP02_CA_Traces_SS.txt";
  private HashMap faultTraceMapping; // fault section and their correpsonding traces
  private final static double LAT_CUTOFF = 34.0; // any fault section have a location above this CUTOFF is neglected
  private FileWriter fw;

  // load the fault sections from files
  public FaultSections() {
    this(INPUT_FILE_NAME1, INPUT_FILE_NAME2, INPUT_FILE_NAME3);

  }

  public FaultSections(String fileName1, String fileName2, String fileName3) {
    try {
      fw = new FileWriter("FaultSectionEndPoints.txt");
      faultTraceMapping = new HashMap();
      loadFaultSections(fileName1, faultTraceMapping);
      loadFaultSections(fileName2, faultTraceMapping);
      loadFaultSections(fileName3, faultTraceMapping);
      fw.close();
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * Load the fault sections into the hashmap
   * @param fileName
   * @param faultMap
   */
  private void loadFaultSections(String fileName, HashMap faultMap) {
    ArrayList fileLines=null;
    try{
      fileLines = FileUtils.loadFile(fileName);
    }catch(Exception e) {
      e.printStackTrace();
    }
    try {

      // parse the fault section file to load the fault trace locations in LocationList
      String faultName = null;
      double lon, lat, depth;
      LocationList locList = null;
      boolean lowerThanCutoff = true;
      for (int i = 0; i < fileLines.size(); ++i) {
        String line = ( (String) fileLines.get(i)).trim();
        if (line.equalsIgnoreCase(""))
          continue;
        if (line.startsWith("#")) { // if it is new fault name
          if (faultName != null && lowerThanCutoff) {
            saveSection(faultMap,  faultName, locList);
          }
          faultName = line.substring(1);
          locList = new LocationList();
          lowerThanCutoff = true;
        }
        else { // fault trace location on current fault
          StringTokenizer tokenizer = new StringTokenizer(line);
          lon = Double.parseDouble(tokenizer.nextToken());
          lat = Double.parseDouble(tokenizer.nextToken());
          if (lat > LAT_CUTOFF)
            lowerThanCutoff = false;
          depth = Double.parseDouble(tokenizer.nextToken());
          locList.add(new Location(lat, lon, depth));
        }
      }

      if (lowerThanCutoff) {
        saveSection(faultMap,  faultName, locList);
      }
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  private void saveSection(HashMap faultMap,  String faultName,
                           LocationList locList) throws InvalidRangeException,
      IOException {
    faultMap.put(faultName, locList);
    fw.write("#" + faultName + "\n");
    fw.write(getLocationAsString(locList.get(0)) + "\n");
    fw.write(getLocationAsString(locList.get(locList.size() - 1)) + "\n");
  }

  private String getLocationAsString(Location loc) {
    return loc.getLongitude()+"\t"+loc.getLatitude()+"\t"+loc.getDepth();
  }


  /**
   * Get all the fault sections
   * @return
   */
  public HashMap getAllFaultSections() {
    return faultTraceMapping;
  }

}