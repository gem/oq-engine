package scratch.ned.WardAnalysis;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;
import java.util.TreeMap;

import org.opensha.commons.util.FileUtils;

import scratch.ned.RundleAnalysis.SegmentSlipTimeInfo;

/**
 * <p>Title: WardAnalysis</p>
 *
 * <p>Description:
 *
 * NOTE that an element ("elem") here corresponds to a "segment" in the Rundle analysis,
 * as ruptures are composed of elements here.
 * </p>
 *
 * @author Edward (Ned) Field
 * @version 1.0
 */
public class WardAnalysis {

  final static boolean D = false; // debugging flag

  // segment info (segment number is the index in the following):
  private double seg_slipRate[], seg_ddw[];
  private String seg_code[], seg_name[];

  // element info(element number is the index in the following):
  private int elem_fltNum[], elem_segNum[];
  private double elem_length[], elem_azim[], elem_lat[], elem_lon[];

  // simulation data (qk number is the index in the following):
  private int eventStartElem[], eventEndElem[];
  private double eventMo[], eventMag[], eventYear[];

  //computed info:
  private double elem_area[];
  private ArrayList elemSlipInfoList, randomElemSlipInfoList;
  private TreeMap timeElemMapping, randomTimeElemMapping;
  private double eventAveSlip[], eventArea[];
  private double eventYearPred1[], aveLastEvTime1[], eventYearPred2[], aveLastEvTime2[];

  // this will hold an ArrayList of elements for each event
  private ArrayList eventElems;


  public WardAnalysis() {

    // read segment info: seg_slipRate[], seg_ddw, seg_code[], & seg_name[]
    // and element info:  elem_fltNum[], elem_segNum[],elem_length[], elem_azim[],
    //                    elem_lat, elem_lon
    read_fort_11();

    // read event info: eventStartElem[], eventEndElem[], eventMo[], eventMag[], & eventYear[]
    read_FOR088_DAT();

    // make other data
    make_computed_data();


    // get computed info:
    // elemSlipInfoList ;
    // timeElemMapping ;

    eventYearPred1 = new double[eventYear.length];
    eventYearPred2 = new double[eventYear.length];
    aveLastEvTime1 = new double[eventYear.length];
    aveLastEvTime2 = new double[eventYear.length];


    getEventStats();

    try {
      writeElemNumYearSlip();
    }
    catch (IOException ex1) {
      ex1.printStackTrace();
      System.exit(0);
    }

    try {
      writeEventData();
    }
    catch (IOException ex1) {
      ex1.printStackTrace();
      System.exit(0);
    }

    /*



        // test
        SegmentSlipTimeInfo info = (SegmentSlipTimeInfo) elemSlipInfoList.get(0);
        ArrayList times = info.getTimeHistories();
        Iterator it = times.iterator();
        Integer tempInt;
        while(it.hasNext()) {
          tempInt = (Integer) it.next();
          System.out.println(tempInt+"\t"+info.getPreviousSlipTime(tempInt));
        }
        System.out.println(info.getPreviousSlipTime(new Integer(12000000)));
 */
  }


  private void getEventStats() {
    Integer year, yearLastInt;
    double totArea, totPot, sum1, sum2, totPotRate, yearLast, slipLast, sumForT_last1, sumForT_last2;
    int elem;
    ArrayList elems;
    for(int i=0;i<eventYear.length;i++) {
      year = new Integer(Math.round((float)eventYear[i]));
      elems = (ArrayList) eventElems.get(i); // this gets the elements for the event
      totArea = 0.0;
      totPot  = 0.0;
      sumForT_last1 = 0.0;
      sumForT_last2 = 0.0;
      sum1 = 0.0;
      sum2 = 0;
      totPotRate = 0.;
      for(int j=0;j<elems.size();j++) { // loop over segments
        elem = ((Integer) elems.get(j)).intValue();
        SegmentSlipTimeInfo info = (SegmentSlipTimeInfo) elemSlipInfoList.get(elem);
        if(elem != info.getSegmentNumber())
          throw new RuntimeException("problem");
        totArea += elem_area[elem];                              // m-squared
        totPot += elem_area[elem]*Math.abs(info.getSlip(year));  // SI units
        yearLastInt = info.getPreviousSlipTime(year);
        if (yearLastInt != null)
          yearLast = yearLastInt.doubleValue();
        else
          yearLast = Double.NaN;
        slipLast = info.getPreviousSlip(year); // will be NaN is not available
        sum1 += yearLast*Math.abs(seg_slipRate[elem_segNum[elem]])*1e-3*elem_area[elem];
        sum2 += Math.abs( elem_area[elem] * slipLast / (seg_slipRate[elem_segNum[elem]]*1e-3));
        totPotRate += Math.abs(seg_slipRate[elem_segNum[elem]])*1e-3*elem_area[elem];
        sumForT_last2 += elem_area[elem]*yearLast;
      }
      aveLastEvTime1[i] = sum1/totPotRate;
      eventYearPred1[i] = totPot/totPotRate + aveLastEvTime1[i];
      aveLastEvTime2[i] = sumForT_last2/totArea;
      eventYearPred2[i] = sum2/totArea + aveLastEvTime2[i];
    }
  }

  private void make_computed_data() {
    // elem_area[], eventAveSlip[], eventArea[],
    // ArrayList elemSlipInfoList
    // TreeMap timeElemMapping

    // make elem_area
    int num_elem = elem_length.length;
    elem_area = new double[num_elem];
    int i,j;
    for(i=0;i<num_elem;i++) {
      elem_area[i] = elem_length[i] * seg_ddw[elem_segNum[i]] *1e6;  // this is sq-meters
    }

    // make the event aveSlip and area
    int num_events = eventMag.length;
    eventAveSlip = new double[num_events];
    eventArea = new double[num_events];
    double totArea;
    for(i=0;i<num_events;i++) {
      totArea = 0;
      for(j=eventStartElem[i]; j<=eventEndElem[i];j++)
        totArea += elem_area[j];
      eventArea[i] = totArea;
      eventAveSlip[i] = eventMo[i]/(eventArea[i]*3e10);
//      if(i < 100)
//        System.out.println(i+"\t"+eventArea[i]+"\t"+eventAveSlip[i]+"\t"+eventMo[i]+"\t"+
//                       eventMag[i]+"\t"+eventYear[i]);
    }

    // make eventElems (elements associated with each event)
    eventElems = new ArrayList();
    ArrayList tempElemList;
    for(i=0; i <num_events; i++) {
      tempElemList = new ArrayList();
      for(j=eventStartElem[i]; j<=eventEndElem[i];j++)
        tempElemList.add(new Integer(j));
      eventElems.add(tempElemList);
    }

    // make elemSlipInfoList (a SegmentSlipTimeInfo object for each element)
    elemSlipInfoList = new ArrayList();
    SegmentSlipTimeInfo tempInfo;
    ArrayList tempTimes, tempSlips;
    Integer time;
    Double slip;
    for(int e=0; e < elem_area.length; e++) {
      tempTimes = new ArrayList();
      tempSlips = new ArrayList();
      for(i=0;i<num_events;i++) {
        if(e >= eventStartElem[i] && e <= eventEndElem[i]) {
          time = new Integer(Math.round((float)eventYear[i]));
          slip = new Double(eventAveSlip[i]);
          tempTimes.add(time);
          tempSlips.add(slip);
        }
      }
      tempInfo = new SegmentSlipTimeInfo(e,tempTimes, tempSlips);
      elemSlipInfoList.add(tempInfo);
    }

  }

  private void read_fort_11() {
    String inputFileName = "scratchJavaDevelopers/ned/WardAnalysis/Warddata/fort.11";
    int numSegs = 101;
    int numElems = 1500;

    seg_slipRate = new double[numSegs];
    seg_ddw = new double[numSegs];
    seg_code = new String[numSegs];
    seg_name = new String[numSegs];

    // element info(element number is the index in the following):
    elem_fltNum = new int[numElems];
    elem_segNum = new int[numElems];
    elem_length = new double[numElems];
    elem_azim = new double[numElems];
    elem_lat = new double[numElems];
    elem_lon = new double[numElems];


    try {
      ArrayList fileLines = FileUtils.loadFile(inputFileName);
      char charStr[];

      // read the segment stuff
      for(int i=0; i<numSegs; ++i){
        String line = (String) fileLines.get(i+1); // added 1 to skip first line
        charStr = new char[4];
        line.getChars(19,23,charStr,0);
        seg_slipRate[i] = Double.parseDouble(new String(charStr));
        charStr = new char[4];
        line.getChars(24,28,charStr,0);
        seg_ddw[i] = Double.parseDouble(new String(charStr));
        line.getChars(35,39,charStr,0);
        seg_code[i] = new String(charStr);
        int numChars = line.toCharArray().length;
        charStr = new char[numChars-41];
        line.getChars(41,numChars,charStr,0);
        seg_name[i] = (new String(charStr)).trim();
//        System.out.println(i+"\t"+seg_slipRate[i]+"\t"+seg_ddw[i]+"\t"+seg_code[i]+"\t"+seg_name[i]);

      }

      // now read the element stuff
      for(int i=0; i<numElems; ++i){
        String line = (String)fileLines.get(i+1+numSegs); // added 1 to skip first line
        charStr = new char[3];
        line.getChars(8,11,charStr,0);
        elem_fltNum[i] = Integer.parseInt((new String(charStr)).trim());
        line.getChars(12,15,charStr,0);
        elem_segNum[i] = Integer.parseInt((new String(charStr)).trim()) - 1; // subtract 1 for indexing from 0
        charStr = new char[8];
        line.getChars(40,48,charStr,0);
        elem_length[i] = Double.parseDouble((new String(charStr)).trim());
        charStr = new char[10];
        line.getChars(49,59,charStr,0);
        elem_azim[i] = Double.parseDouble((new String(charStr)).trim());
        charStr = new char[6];
        line.getChars(84,90,charStr,0);
        elem_lat[i] = Double.parseDouble((new String(charStr)).trim());
        charStr = new char[8];
        line.getChars(91,99,charStr,0);
        elem_lon[i] = Double.parseDouble((new String(charStr)).trim());

//        if(i>1400)
//          System.out.println(i+"\t"+elem_fltNum[i]+"\t"+elem_segNum[i]+"\t"+elem_length[i]+"\t"+
//                           elem_azim[i]+"\t"+elem_lat[i]+"\t"+elem_lon[i]);

      }

      //find min and max elem length
      double maxLen =0, minLen=100;
      for(int i=0;i<elem_length.length;i++){
        if(maxLen < elem_length[i]) maxLen = elem_length[i];
        if(minLen > elem_length[i]) minLen = elem_length[i];
      }
      System.out.println("maxElemLength = "+maxLen+"; minElemLength = "+minLen);


    }
    catch (FileNotFoundException ex) {
      ex.printStackTrace();
      System.exit(0);
    }
    catch (IOException ex) {
      ex.printStackTrace();
      System.exit(0);
}
  }



  private void read_FOR088_DAT() {
    String inputFileName = "scratchJavaDevelopers/ned/WardAnalysis/Warddata/FOR088.DAT";
    ArrayList fileLines = new ArrayList();
    try {
        //reading the file
        fileLines = FileUtils.loadFile(inputFileName);
    }
    catch (FileNotFoundException ex) {
        ex.printStackTrace();
        System.exit(0);
    }
    catch (IOException ex) {
        ex.printStackTrace();
        System.exit(0);
    }

    StringTokenizer st;

    int numEvents = fileLines.size();
    int numGoodEvents=0;
    int startElem, endElem, numElem=0;
    double mo, mag, year;

    // find the number of good events
    for(int i=0; i<numEvents; ++i){
      st = new StringTokenizer( (String) fileLines.get(i));
      st.nextToken();
      st.nextToken();
      startElem = Integer.parseInt(st.nextToken().trim()) - 1; // subtract 1 for indexing from 0
      endElem = Integer.parseInt(st.nextToken().trim()) - 1; // subtract 1 for indexing from 0
      numElem = endElem-startElem+1;
      st.nextToken();
      mag = Double.parseDouble(st.nextToken().trim());
      if(mag >= 5.5) numGoodEvents++;
    }
    System.out.println("num good events = "+numGoodEvents);
    //
    eventStartElem = new int[numGoodEvents];
    eventEndElem = new int[numGoodEvents];
    eventMo = new double[numGoodEvents];
    eventMag = new double[numGoodEvents];
    eventYear = new double[numGoodEvents];

    int index=0;
    for(int i=0; i<numEvents; ++i){
      st = new StringTokenizer( (String) fileLines.get(i));
      st.nextToken();
      st.nextToken();
      startElem = Integer.parseInt(st.nextToken().trim()) - 1; // subtract 1 for indexing from 0
      endElem = Integer.parseInt(st.nextToken().trim()) - 1;   // subtract 1 for indexing from 0
      mo = Double.parseDouble(st.nextToken().trim());
      mag = Double.parseDouble(st.nextToken().trim());
      year = Double.parseDouble(st.nextToken().trim());
      if(mag >= 5.5) {
        eventStartElem[index] = startElem;
        eventEndElem[index] = endElem;
        eventMo[index] = mo;
        eventMag[index] = mag;
        eventYear[index] = year;
        index ++;
      }
//      if(i > numEvents-100)
//        System.out.println(i+"\t"+eventStartElem[i]+"\t"+eventEndElem[i]+"\t"+eventMo[i]+"\t"+
//                       eventMag[i]+"\t"+eventYear[i]);

    }
  }


  /**
   * This writes out the date and amount of slip for each element (so the slips can
   * be plotted as element number versus year)
   */
  private void writeElemNumYearSlip() throws IOException {
    FileWriter fw = new FileWriter("scratchJavaDevelopers/ned/WardAnalysis/WardData/Ward_elemNumYearSlip.txt");
    SegmentSlipTimeInfo elemInfo;
    ArrayList years, slips;
    int elemNum;
    int numElems = elemSlipInfoList.size();
    fw.write("elemNum\telemYear\telemSlip\n");
    for(int j=0;j<numElems;j++) { // loop over segments
      elemInfo = (SegmentSlipTimeInfo) elemSlipInfoList.get(j);
      years = elemInfo.getTimeHistories();
      slips = elemInfo.getSlipHistories();
      elemNum = elemInfo.getSegmentNumber();
      for (int i = 0; i < years.size(); i++) {
          fw.write(elemNum + "\t" + years.get(i) + "\t" + slips.get(i) + "\n");
      }
    }
    fw.close();
  }



  /**
   * This writes out the normalized recurrence intervals and the average recurrence interval
   * for each segment (excluding creeping section)
   */
  private void writeSegmentStats() throws IOException {
    FileWriter fw = new FileWriter("scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/VC_segRecurIntervals.txt");
    SegmentSlipTimeInfo segInfo;
    ArrayList intervals;
    double aveRecur, normInt;
    int segNum;
//    for(int j=0;j<1;j++) { // loop over segments
    int numSegs = elemSlipInfoList.size();
    fw.write("segNumForInterval\tSegNormInterval\taveSegInterval\n");
    for(int j=0;j<numSegs;j++) { // loop over segments
      segInfo = (SegmentSlipTimeInfo) elemSlipInfoList.get(j);
      aveRecur = segInfo.getAveRecurrenceInterval();
      segNum = segInfo.getSegmentNumber();
      intervals = segInfo.getRecurrenceIntervals();
      if (!(segNum >= 264 && segNum <= 273)) // exclude creaping sections
        for (int i = 0; i < intervals.size(); i++) {
          normInt = ( (Integer) intervals.get(i)).doubleValue() / aveRecur;
          fw.write(segNum + "\t" + normInt + "\t" + aveRecur + "\n");
        }
    }
    fw.close();
  }


  private void writeEventData() throws IOException  {
    String filename1 = "scratchJavaDevelopers/ned/WardAnalysis/WardData/Ward_EventTimesNumSegs.txt";
    String filename2 = "scratchJavaDevelopers/ned/WardAnalysis/WardData/Ward_EventSegs.txt";
    String evName;
    ArrayList tempElems;
    Integer year;
    int lastYear=-1, counter=-1;

    FileWriter fw1 = new FileWriter(filename1);
    fw1.write("evTimes\tevNumElems\tevMags\tevAreas\tevSlips\tevYearPred1\taveLastEvTime1\tevYearPred2\taveLastEvTime2\n");
    FileWriter fw2 = new FileWriter(filename2);
    fw2.write("evSegs\n");
    for(int i=0; i < eventYear.length; i++) {
      year = new Integer(Math.round((float)eventYear[i]));
      if(year.intValue() != lastYear)
        counter = 0;
      else
        counter += 1;
      evName = year.toString()+"_"+Integer.toString(counter);
      lastYear = year.intValue();
      tempElems = (ArrayList) eventElems.get(i);
      fw1.write(year+"\t"+tempElems.size()+"\t"+(float)eventMag[i]+"\t"+(float)eventArea[i]+"\t"+
                (float)eventAveSlip[i]+"\t"+(float)eventYearPred1[i]+"\t"+(float)aveLastEvTime1[i]+
                "\t"+(float)eventYearPred2[i]+"\t"+(float)aveLastEvTime2[i]+"\n");
      fw2.write(evName+"\n");
      for(int j=0; j < tempElems.size(); j++)
        fw2.write((Integer) tempElems.get(j)+"\n");
    }
    fw1.close();
    fw2.close();
  }


  /*

  private boolean creepingNotInvolved(ArrayList newEvent) {
    boolean crNotInv = true;
    Iterator it = newEvent.iterator();
    int seg;
    while(it.hasNext()) {
      seg = ((Integer) it.next()).intValue();
      if (seg >= 264 && seg <= 273) crNotInv = false;
    }
    return crNotInv;
  }

*/


  public static void main(String[] args) {
    new WardAnalysis();
  }
}
