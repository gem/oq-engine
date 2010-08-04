package scratch.ned.RundleAnalysis;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.Set;
import java.util.StringTokenizer;
import java.util.TreeMap;


/**
 * <p>Title: Read_VC_FaultActivity_SAF</p>
 *
 * <p>Description: This class reads the VC_Fault_Activity_SAF.txt . Then
 * extract the slip info at time period on each segment.</p>
 * @author Edward (Ned) Field
 * @version 1.0
 */
public class Read_VC_FaultActivity {


  //gets the Segment area
  private double[] segmentAreas;


  //Name of the input file to read
  private  String inputFile;

  //Name of the output file that saves all Segments Numbers that have Slip histories at same time period
  private final static String outSegmentSlipFile = "scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/ned_out.txt";

  //list consisting of SegmentSlipTimeInfo Object
  private ArrayList segmentSlipInfoList;

  //Treemap to store which segments have same Time Pds.
  //Key for this mapping is TimePd and Value is the Arraylist of all the segments
  //that have same Time Pd
  private TreeMap timeSegmentMapping;

  private ArrayList randomSegmentSlipInfoList;
  private TreeMap randomTimeSegmentMapping;

  public Read_VC_FaultActivity(String fileName) {
    inputFile = fileName;

    try {
      getSegmentSlipTimeInfoFromFile();
    }
    catch (FileNotFoundException ex) {
      ex.printStackTrace();
      System.exit(0);
    }
    catch (IOException ex) {
      ex.printStackTrace();
      System.exit(0);
    }

    sortSegmentListForTimePd();

  }

  private void getSegmentSlipTimeInfoFromFile() throws FileNotFoundException,
      IOException {

    //reading the file to extract Slip time infor for each segment
    FileReader fr = new FileReader(inputFile);
    BufferedReader br = new BufferedReader(fr);
    //skipping the first line
    br.readLine();
    //reading the next line in the file that tells how many segments are there in the file
    String numSegmentsLine = br.readLine();
    StringTokenizer st = new StringTokenizer(numSegmentsLine);
    int numSegments = (int)Double.parseDouble(st.nextToken().trim());
    segmentAreas = new double[numSegments];
    //skipping the next line as it just provide with String " SEGMENT Area" String
    br.readLine();
    //counter for number of segment Areas.
    int i=0;
    //counter to see how many lines taken by Segment Area block
    int numSegmentLines = 0;

    //looping over whole of "Segment Area" block to get all the segment areas
    while(i < numSegments){
      ++numSegmentLines;
      String segmentLine = br.readLine();
      st = new StringTokenizer(segmentLine);
      while(st.hasMoreTokens()){
        segmentAreas[i] = Double.parseDouble(st.nextToken());
        ++i;
      }
    }


    //Skipping the lines for Segment Velocity
    for(i=0;i<=numSegmentLines;++i)
      br.readLine();

    //initialising the List to store the Segment Slip time histories info
    segmentSlipInfoList = new ArrayList();
    //initialing the treemap to get all the Segments that have slip info for same time pd.
    timeSegmentMapping = new TreeMap();

    //looping over all the segments to get all the slip time histories .
    for(int j=0;j<numSegments;++j){
      //reading a null line
       br.readLine();
      //reading a line that is to be skipped
      br.readLine();
      String numEventsInSegment = br.readLine();
      st = new StringTokenizer(numEventsInSegment);
      int segmentNum = Integer.parseInt(st.nextToken()) - 1;  // minus 1!
      String token = st.nextToken();
      //System.out.println("Token :"+token);
      int numEvents = Integer.parseInt(token);
      //reading a line that needs to be skipped
      br.readLine();

      //List for storing the Slip time histories for each segment
      ArrayList timeHistories = new ArrayList();
      ArrayList slipHistories = new ArrayList();

      //reading the slip time histories for each segment
      for(int k=0;k<numEvents;++k){
        String segmentSlipTimeLine = br.readLine();
        StringTokenizer st1 = new StringTokenizer(segmentSlipTimeLine);
        //skipping the event number
        st1.nextToken();
        //Reading the time Pd for the segment
        Integer timePd = new Integer((int)Double.parseDouble(st1.nextToken().trim()));

        //Looking in the Treemap if the Time Pd already exists, if it does,
        //then extract the corresponding ArrayList of the Segments have
        //same Time Pd and add the new segment to this list.
        //If the mapping does not contain the time pd. then add this time pd to the
        //Treemap.
        Object timeSegList = timeSegmentMapping.get(timePd);
        if(timeSegList !=null)
          ((ArrayList)timeSegList).add(new Integer(segmentNum));
        else{
          ArrayList segList = new ArrayList();
          segList.add(new Integer(segmentNum));
          timeSegmentMapping.put(timePd,segList);
        }
        //getting the time histories and storing it in the Array List
        timeHistories.add(timePd);
        //getting the slip histories and storing it in the Array List
        slipHistories.add(new Double(st1.nextToken().trim()));
      }
      //creating the SegmentSlipTimeInfo object
      SegmentSlipTimeInfo  segmentSlipTime = new SegmentSlipTimeInfo(segmentNum,timeHistories,slipHistories);
      //adding this object to the list
      segmentSlipInfoList.add(segmentSlipTime);
    }
  }


  /**
   * This function sorts the Segment list that have slip at the same Time Pd.
   */
  private void sortSegmentListForTimePd(){
    Set keySet = timeSegmentMapping.keySet();
    Iterator it = keySet.iterator();
    while(it.hasNext())
      Collections.sort((ArrayList)timeSegmentMapping.get(it.next()));
  }


  /**
   * Returns the ArrayList for the SegmentSlipTimeInfo Object.
   * This object contains all slip time Histories info for each segment
   * @return ArrayList
   */
  public ArrayList getSegmentsSlipTimeHistories(){
    return segmentSlipInfoList;
  }


  /**
   * This returns the segment areas
   * @return double[]
   */
  public double[] getSegmentAreas() {
    return segmentAreas;
  }


  /**
   * This returns timeSegmentMapping
   * @return double[]
   */
  public TreeMap getTimeSegmentMapping() {
    return timeSegmentMapping;
  }

  /**
   * Returns the ArrayList for a randomized SegmentSlipTimeInfo Object.
   * This object contains all slip time Histories info for each segment
   * @return ArrayList
   */
  public ArrayList getRandomizedSegmentsSlipTimeHistories(){
    if(randomSegmentSlipInfoList == null)
      randomizeYears();
    return randomSegmentSlipInfoList;
  }


  /**
   * This returns a randomized timeSegmentMapping
   * @return double[]
   */
  public TreeMap getRandomizedTimeSegmentMapping() {
    if(randomTimeSegmentMapping == null)
      randomizeYears();
    return randomTimeSegmentMapping;
  }

  /**
   * Writes the output file for all segments having the same TimePd for slip histories.
   * Writes the output file in the following format:
   * Time-Pd-1 segmentNum-1,segmentNum-2,.....
   * Time-Pd-2 segmentNum-2,segmentNum-3
   * .
   * .
   * .
   * @param fileName String Output filename
   * Output file is a sorted file.
   */
  public void writeTimeSegmentFile(String fileName) throws IOException {
    FileWriter fw = new FileWriter(fileName);
    Set keySet = timeSegmentMapping.keySet();
    Iterator it = keySet.iterator();
    fw.write("Year  Segment-Numbers\n");
    while(it.hasNext()){
     Integer timePd = (Integer)it.next();
     ArrayList segmentList = (ArrayList)timeSegmentMapping.get(timePd);
     int size = segmentList.size();
     fw.write(timePd.intValue()+" ");
     for(int i=0;i<size-1;++i)
       fw.write(((Integer)segmentList.get(i)).intValue()+" ");
     fw.write(""+((Integer)segmentList.get(size-1)).intValue());
     fw.write("\n");
    }
    fw.close();
  }


  /**
   * this randomizes the rupture times, by swapping each year in timeSegentMapping with
   * a randmly chosen year, and then replacing occurrences of that year in each appropriate
   * setSlipTimeInfo object.  Everything is put in new objects.
   */
  private void randomizeYears() {
    randomTimeSegmentMapping = new TreeMap();
    TreeMap oldToNewYearMap = new TreeMap();
    SegmentSlipTimeInfo tempOldSegmentSlipTimeInfo, tempNewSegmentSlipTimeInfo;
    Integer lastYear = (Integer) timeSegmentMapping.lastKey();
    Integer oldYear;
    int seg;
    Double newYear;
    ArrayList tempSegList, tempOldYearList, tempNewYearList, tempSlipList;
//    System.out.println("Last year = "+lastYear);
    int numYears = timeSegmentMapping.size();
    Set keySet = timeSegmentMapping.keySet();
    Iterator it = keySet.iterator();
    while(it.hasNext()){
      oldYear = (Integer) it.next();
      tempSegList = (ArrayList) timeSegmentMapping.get(oldYear);
      // get a unique, random year
      newYear = new Double(lastYear.doubleValue() * Math.random());
      while (randomTimeSegmentMapping.get(newYear) != null) { // check that it's unique
        newYear = new Double(lastYear.doubleValue() * Math.random());
      }
      randomTimeSegmentMapping.put(newYear, tempSegList);
      oldToNewYearMap.put(oldYear, newYear);
    }

    // now creat the randomSegmentSlipInfoList
    randomSegmentSlipInfoList = new ArrayList();
    for(int i=0; i<segmentSlipInfoList.size();i++) {
      tempOldSegmentSlipTimeInfo = (SegmentSlipTimeInfo) segmentSlipInfoList.get(i);
      tempOldYearList = tempOldSegmentSlipTimeInfo.getTimeHistories();
      tempNewYearList = new ArrayList();
      tempSlipList = tempOldSegmentSlipTimeInfo.getSlipHistories();
      for(int j=0;j<tempOldYearList.size();j++)
        tempNewYearList.add(oldToNewYearMap.get(tempOldYearList.get(j)));
      tempNewSegmentSlipTimeInfo = new SegmentSlipTimeInfo(i,tempNewYearList,tempSlipList);
      randomSegmentSlipInfoList.add(tempNewSegmentSlipTimeInfo);
    }
}


  public static void main(String[] args) {
    Read_VC_FaultActivity read_vc_faultactivity_saf = new
        Read_VC_FaultActivity("scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/VC_Fault_Activity_SAF.txt");
    System.out.println("starting");
    read_vc_faultactivity_saf.randomizeYears();
    System.out.println("finished");
/*
    try {
      read_vc_faultactivity_saf.writeTimeSegmentFile(outSegmentSlipFile);
    }
    catch (IOException ex1) {
      ex1.printStackTrace();
      System.exit(0);
    }
*/
  }

}
