package scratch.vipin;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URLConnection;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.geo.Location;
import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: RuptureFileReaderWriter.java </p>
 * <p>Description: This class writes ruptures to a  text file as well as
 * read from that file</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class RuptureFileReaderWriter {

  // Rupture File Readers
  private BufferedReader brRups;
  private ArrayList nodesList=null; // it will hold the list of alocation/sectionanme/id for each location on a rupture
  private float rupLen=0.0f; // rupture length


  /**
   * This constructor needs to be used only when try to read ruptures from a file
   * @param fileName
   */
  public RuptureFileReaderWriter(String fileName) {
    try {
      File file = new File(fileName);
      if(file.exists()) { // load file without jar file
       // read from rupture file
       FileReader frRups = new FileReader(fileName);
       brRups = new BufferedReader(frRups);
     } else { // load file from jar file
       URLConnection uc = FileUtils.class.getResource("/"+fileName).openConnection();
       brRups =
           new BufferedReader(new InputStreamReader((InputStream) uc.getContent()));
     }


      brRups.readLine(); // skip first line as it just contains number of ruptures
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * Close the files
   */
  public void close() {
    try {
      brRups.close();
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * write the ruptures to the file. For each rupture, it writes:
   * 1. Rupture Id
   * 2. Rupture Length
   * 3. All Locations on this rupture
   * 4. Fault Sections with which each location is associated
   */

  public static void  writeRupsToFile(FileWriter fw, ArrayList rupList) {
    try {
      // get total number of ruptures
      int numRups = 0;
      if (rupList != null) numRups = rupList.size();
        // loop over all ruptures and print them
      for (int i = 0; i < numRups; ++i) {
        MultiSectionRupture multiSectionRup = (MultiSectionRupture)rupList.get(i);
        ArrayList nodesList = multiSectionRup.getNodesList();
        fw.write("#Rupture " + i + " "+multiSectionRup.getLength()+"\n");
        // loop over all locations on this rupture and write them to file
        for (int k = 0; k < nodesList.size(); ++k) {
          Node node = (Node) nodesList.get(k);
          fw.write("\t" + node.getLoc() + ","+node.getFaultSectionName()+","+node.getId()+"\n");
        }
     }
   }catch(Exception e) {
     e.printStackTrace();
   }
 }

 /**
  * Get. next rupture from the file.
  * Returns null if there are no more ruptures in the file
  *
  * @return
  */
 public MultiSectionRupture getNextRupture() {
   try {
     String line = brRups.readLine();
     if(line==null) return null;
     double lat, lon;
     //int k=0;
     MultiSectionRupture multiSectionRup=null;
     while(line!=null) {
       line=line.trim();
       if(!line.equalsIgnoreCase("")) { // if line is not a blank line
         if(line.startsWith("#"))  { // this is new rupture name

           if(nodesList!=null) { // add the rupture to the list of all ruptures
              multiSectionRup = new MultiSectionRupture(
                  nodesList);
             multiSectionRup.setLength(rupLen);
           }
           // initalize for start of next rupture
           StringTokenizer tokenizer = new StringTokenizer(line);
           tokenizer.nextToken(); // rupture string
           tokenizer.nextToken(); // rupture counter
           rupLen = Float.parseFloat(tokenizer.nextToken()); // rupture length
           nodesList = new ArrayList();
           if(multiSectionRup!=null) return multiSectionRup;
         } else {
           // get the lat/lon, sectionName and locationId for each location on this rupture
           StringTokenizer tokenizer = new StringTokenizer(line,",");
           lat = Double.parseDouble(tokenizer.nextToken());// lat
           lon = Double.parseDouble(tokenizer.nextToken()); //lon
           tokenizer.nextToken(); // depth
           String sectionName = tokenizer.nextToken(); //section name
           int id = Integer.parseInt(tokenizer.nextToken());//id
           Node node = new Node(id, sectionName, new Location(lat,lon,0.0));
           nodesList.add(node);
         }
       }
       line=brRups.readLine();
     }
     // return the last rupture
      multiSectionRup = new MultiSectionRupture(
          nodesList);
     multiSectionRup.setLength(rupLen);
     return multiSectionRup;

   }catch(Exception e) {
     e.printStackTrace();
   }
   return null;
 }



 /**
  * It reads a text file and loads all the ruptures into an ArrayList
  *
  * @param fileName Text file containing information about all the ruptures
  * @return
  */
 public ArrayList loadRuptures() {
   ArrayList rupturesList = new ArrayList(); // list of ruptures
   MultiSectionRupture rup = getNextRupture();
   while(rup!=null) {
     rupturesList.add(rup);
     rup = getNextRupture();
   }
   return rupturesList;
 }

}