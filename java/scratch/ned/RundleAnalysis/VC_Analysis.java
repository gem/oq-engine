package scratch.ned.RundleAnalysis;

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.Set;
import java.util.TreeMap;

import org.opensha.commons.calc.FaultMomentCalc;
import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.geo.Location;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * <p>Title: VC_Analysis</p>
 *
 * <p>Description:
 * </p>
 *
 * @author Edward (Ned) Field
 * @version 1.0
 */
public class VC_Analysis {

  final static boolean D = false; // debugging flag

  private String faultNames[];
  private int firstIndex[], lastIndex[];
  private double seg_x_west[],seg_y_west[],seg_x_east[],seg_y_east[],seg_slipRate[], seg_area[];
  private ArrayList segSlipInfoList, randomSegSlipInfoList;
  private TreeMap timeSegMapping, randomTimeSegMapping;
  private ArrayList faultList;
  private ArrayList eventYears, eventSegs;
  private double eventMags[], eventAveSlips[], eventAreas[];
  private double eventYearPred1[], aveLastEvTime1[], eventYearPred2[], aveLastEvTime2[];

  /* these are the lat & lon of the first point on the first segment (Bartlett Strings fault),
     used for converting the x & y values to lat & lon.  These were determined by looking at the
     NSHMP-2002 fault model.
  */
  private double lat0 = 38.9334, lon0 = -122.5041; // lat * lon of first point on first segment


  public VC_Analysis() {

    Read_VC_Faults_2001v6 read_vc_faults_2001v6 = new Read_VC_Faults_2001v6();
    seg_x_west = read_vc_faults_2001v6.getSeg_x_west();
    seg_y_west = read_vc_faults_2001v6.getSeg_y_west();
    seg_x_east = read_vc_faults_2001v6.getSeg_x_east();
    seg_y_east = read_vc_faults_2001v6.getSeg_y_east();
    seg_slipRate = read_vc_faults_2001v6.getSeg_slipRate();

    Read_VC_FaultNamesSegs read_VC_FaultNamesSegs = new Read_VC_FaultNamesSegs();
    faultNames = read_VC_FaultNamesSegs.getFaultNames();
    firstIndex = read_VC_FaultNamesSegs.getFirstIndex();
    lastIndex = read_VC_FaultNamesSegs.getLastIndex();

    Read_VC_FaultActivity read_vc_faultactivity_saf = new
        Read_VC_FaultActivity(
        "scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/VC_Fault_Activity_SAF.txt");
    seg_area = read_vc_faultactivity_saf.getSegmentAreas();
    segSlipInfoList = read_vc_faultactivity_saf.getSegmentsSlipTimeHistories();
    timeSegMapping = read_vc_faultactivity_saf.getTimeSegmentMapping();

  //SegmentSlipTimeInfo firstSegmentSlipTime = (SegmentSlipTimeInfo) segSlipInfoList.get(0);
  //System.out.println("first segment number = "+firstSegmentSlipTime.getSegmentNumber());

    if (D) {
      System.out.println(seg_x_west.length + "  " + seg_y_west.length + "  " +
                         seg_x_east.length + "  " + seg_y_east.length + "  " +
                         seg_slipRate.length + "  " + seg_area.length + "  " +
                         segSlipInfoList.size());
    }

    try {
      writeSegNumYearSlip();
    }
    catch (IOException ex1) {
      ex1.printStackTrace();
      System.exit(0);
    }

    /*
    try {
      writeSegmentStats();
    }
    catch (IOException ex1) {
      ex1.printStackTrace();
      System.exit(0);
    }

    makeSeparateEventsList();

    eventMags = new double[eventYears.size()];
    eventAveSlips = new double[eventYears.size()];
    eventAreas = new double[eventYears.size()];
    eventYearPred1 = new double[eventYears.size()];
    eventYearPred2 = new double[eventYears.size()];
    aveLastEvTime1 = new double[eventYears.size()];
    aveLastEvTime2 = new double[eventYears.size()];


    getEventStats();

    try {
      writeEventData();
    }
    catch (IOException ex1) {
      ex1.printStackTrace();
      System.exit(0);
    }
*/

/*

        // test
        SegmentSlipTimeInfo info = (SegmentSlipTimeInfo) segSlipInfoList.get(0);
        ArrayList times = info.getTimeHistories();
        Iterator it = times.iterator();
        Integer tempInt;
        while(it.hasNext()) {
          tempInt = (Integer) it.next();
          System.out.println(tempInt+"\t"+info.getPreviousSlipTime(tempInt));
        }
        System.out.println(info.getPreviousSlipTime(new Integer(12000000)));

*/
/*
    makeFaultTraces();
    if(D) {
      FaultTrace tempFlt;
      int num=0;
      for(int i = 0; i<faultList.size(); i++) {
        tempFlt = (FaultTrace) faultList.get(i);
        System.out.println(tempFlt.getNumLocations()+"  "+tempFlt.getName());
        num += tempFlt.getNumLocations();
      }
      System.out.println(num-faultList.size());
    }

    try {
      writeFaultTraces();
    }
    catch (IOException ex1) {
      ex1.printStackTrace();
      System.exit(0);
    }
*/
  }


  /**
   * This writes out the date and amount of slip for each section (so the slips can
   * be plotted as segment number versus year)
   */
  private void writeSegNumYearSlip() throws IOException {
    FileWriter fw = new FileWriter("scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/VC_segNumYearSlip.txt");
    SegmentSlipTimeInfo segInfo;
    ArrayList years, slips;
    int segNum;
    int numSegs = segSlipInfoList.size();
    fw.write("segNum\tSegYear\tsegSlip\n");
    for(int j=0;j<numSegs;j++) { // loop over segments
      segInfo = (SegmentSlipTimeInfo) segSlipInfoList.get(j);
      years = segInfo.getTimeHistories();
      slips = segInfo.getSlipHistories();
      segNum = segInfo.getSegmentNumber();
      for (int i = 0; i < years.size(); i++) {
          fw.write(segNum + "\t" + years.get(i) + "\t" + slips.get(i) + "\n");
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
    int numSegs = segSlipInfoList.size();
    fw.write("segNumForInterval\tSegNormInterval\taveSegInterval\n");
    for(int j=0;j<numSegs;j++) { // loop over segments
      segInfo = (SegmentSlipTimeInfo) segSlipInfoList.get(j);
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





  private void getEventStats() {
    Integer year, yearLastInt;
    double totArea, totPot, sum1, sum2, totPotRate, yearLast, slipLast, sumForT_last1, sumForT_last2;
    int seg;
    ArrayList segs;
    for(int i=0;i<eventYears.size();i++) {
      year = (Integer) eventYears.get(i);
      segs = (ArrayList) eventSegs.get(i);
      totArea = 0.0;
      totPot  = 0.0;
      sumForT_last1 = 0.0;
      sumForT_last2 = 0.0;
      sum1 = 0.0;
      sum2 = 0;
      totPotRate = 0.;
      for(int j=0;j<segs.size();j++) { // loop over segments
        seg = ((Integer) segs.get(j)).intValue();
        SegmentSlipTimeInfo info = (SegmentSlipTimeInfo) segSlipInfoList.get(seg);
        if(seg != info.getSegmentNumber())
          throw new RuntimeException("problem");
        totArea += seg_area[seg]*1e6;                    // converted from km to m-squared
        totPot += seg_area[seg]*Math.abs(info.getSlip(year))*1e4;  // converted to meters
        yearLastInt = info.getPreviousSlipTime(year);
        if (yearLastInt != null)
          yearLast = yearLastInt.doubleValue();
        else
          yearLast = Double.NaN;
        slipLast = info.getPreviousSlip(year); // will be NaN is not available
        sum1 += yearLast*Math.abs(seg_slipRate[seg])*seg_area[seg]*1e4;
        sum2 += seg_area[seg]*1e6*(Math.abs(slipLast)/Math.abs(seg_slipRate[seg])+yearLast);
        totPotRate += Math.abs(seg_slipRate[seg])*seg_area[seg]*1e4;
        sumForT_last1 += Math.abs(seg_slipRate[seg])*seg_area[seg]*1e4*yearLast;
        sumForT_last2 += seg_area[seg]*1e6*yearLast;
// if(year.intValue() == 25726)
//          System.out.println(seg+"\t"+seg_area[seg]+"\t"+info.getSlip(year)+"\t"+yearLast+"\t"+slipLast);
      }
      eventAveSlips[i]=(totPot/totArea);   //meters
      eventAreas[i]=totArea;             //meters-sq
      eventMags[i]= MomentMagCalc.getMag(FaultMomentCalc.getMoment(totArea,totPot/totArea));
      eventYearPred1[i] = (totPot+sum1)/totPotRate;
      eventYearPred2[i] = sum2/totArea;
      aveLastEvTime1[i] = sumForT_last1/totPotRate;
      aveLastEvTime2[i] = sumForT_last2/totArea;
// if(year.intValue() == 25726)
//        System.out.println(year+"\t"+eventAveSlips[i]+"\t"+eventAreas[i]+"\t"+eventMags[i]+
//            "\t"+eventYearPred1[i]+"\t"+eventYearPred2[i]+"\t"+aveLastEvTime1[i]+"\t"+aveLastEvTime2[i]);
    }
  }



  private void writeEventData() throws IOException  {
    String filename1 = "scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/VC_EventTimesNumSegs.txt";
    String filename2 = "scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/VC_EventSegs.txt";
    String evName;
    ArrayList tempSegs;
    Integer year;
    int lastYear=-1, counter=-1;

    FileWriter fw1 = new FileWriter(filename1);
    fw1.write("evTimes\tevNumSegs\tevMags\tevAreas\tevSlips\tevYearPred1\taveLastEvTime1\tevYearPred2\taveLastEvTime2\n");
    FileWriter fw2 = new FileWriter(filename2);
    fw2.write("evSegs\n");
    for(int i=0; i < eventYears.size(); i++) {
      year = (Integer) eventYears.get(i);
      if(year.intValue() != lastYear)
        counter = 0;
      else
        counter += 1;
      evName = year.toString()+"_"+Integer.toString(counter);
      lastYear = year.intValue();
      tempSegs = (ArrayList) eventSegs.get(i);
      fw1.write(year+"\t"+tempSegs.size()+"\t"+(float)eventMags[i]+"\t"+(float)eventAreas[i]+"\t"+
                (float)eventAveSlips[i]+"\t"+eventYearPred1[i]+"\t"+aveLastEvTime1[i]+
                "\t"+eventYearPred2[i]+"\t"+aveLastEvTime2[i]+"\n");
      fw2.write(evName+"\n");
      for(int j=0; j < tempSegs.size(); j++)
        fw2.write((Integer) tempSegs.get(j)+"\n");
    }
    fw1.close();
    fw2.close();
  }

  private void makeSeparateEventsList() {
    eventYears = new ArrayList();
    eventSegs = new ArrayList();
    ArrayList tempEventList, tempSegList;
    Set keySet = timeSegMapping.keySet();
    Iterator it = keySet.iterator();
    while (it.hasNext()) {
      Integer timePd = (Integer) it.next();
      tempSegList = (ArrayList) timeSegMapping.get(timePd);
      tempEventList = separateEvents(tempSegList, 8.0);
      eventSegs.addAll(tempEventList);
      for(int i=0; i<tempEventList.size();i++) eventYears.add(timePd);
    }
  }


  private ArrayList separateEvents(ArrayList segments, double distThresh) {

      // this is the list of events (segments list) that will be returned:
    ArrayList eventsList = new ArrayList();
    ArrayList availSegs = (ArrayList) segments.clone();
    ArrayList newEvent;
    ArrayList tempList;
    int int1, int2;
    int cf; // current focus

    while(availSegs.size() > 0) {
      newEvent = new ArrayList();
      newEvent.add(availSegs.get(0));
      availSegs.remove(0);
      cf = 0;
      while(cf < newEvent.size()){
        int1 = ((Integer) newEvent.get(cf)).intValue();
        // find avail segs close to int1
        tempList = (ArrayList) availSegs.clone();
        for(int i=tempList.size()-1; i >= 0 ; i--) {
          int2 = ((Integer) tempList.get(i)).intValue();
          if(getMinDist(int1,int2) < distThresh) {
            newEvent.add(tempList.get(i));
            availSegs.remove(i);
          }
        }
        cf += 1;
      }
      if(creepingNotInvolved(newEvent)) eventsList.add(newEvent);
    }

    if(D) {
      int num = 0;
      for(int i = 0; i < eventsList.size(); i++){
        tempList = (ArrayList) eventsList.get(i);
        num += tempList.size();
        for(int j = 0; j < tempList.size(); j++) System.out.print(tempList.get(j)+"  ");
        System.out.print("\n");
      }
      System.out.println(segments.size()+"  "+ num);
    }

    return eventsList;
  }



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


  /**
   * This gets the minimum distance between either ends of the two input segments
   * @param seg1 int
   * @param seg2 int
   * @return double
   */
  private double getMinDist(int seg1, int seg2) {
    double min = Math.sqrt( Math.pow(seg_x_west[seg1]-seg_x_west[seg2],2.0) + Math.pow(seg_y_west[seg1]-seg_y_west[seg2],2.0) );
    double dist = Math.sqrt( Math.pow(seg_x_west[seg1]-seg_x_east[seg2],2.0) + Math.pow(seg_y_west[seg1]-seg_y_east[seg2],2.0) );
    if (dist < min) min = dist;
    dist = Math.sqrt( Math.pow(seg_x_east[seg1]-seg_x_east[seg2],2.0) + Math.pow(seg_y_east[seg1]-seg_y_east[seg2],2.0) );
    if (dist < min) min = dist;
    dist = Math.sqrt( Math.pow(seg_x_east[seg1]-seg_x_west[seg2],2.0) + Math.pow(seg_y_east[seg1]-seg_y_west[seg2],2.0) );
    if (dist < min) min = dist;
    return min;
  }



  // these methods make and write approx fault traces; they don't look right
  private void makeFaultTraces() {
    faultList = new ArrayList();
    FaultTrace fault;
    Location loc;
    double lat, lon;
    double x0 = seg_x_west[0];
    double y0 = seg_y_west[0];
    double lonCorr = Math.cos(Math.PI*lat0/180);
    for(int i=0; i<faultNames.length; i++) {
      fault = new FaultTrace(faultNames[i]);
      for(int j = firstIndex[i]; j <= lastIndex[i]; j++) {
        lon = (seg_x_west[j]-x0)/(111.111*lonCorr) + lon0;
        lat = (seg_y_west[j]-y0)/111.111 + lat0;
        loc = new Location(lat, lon);
        fault.add(loc);
      }
      // get the last point
      lon = (seg_x_east[lastIndex[i]]-x0)/(111.111*lonCorr) + lon0;
      lat = (seg_y_east[lastIndex[i]]-y0)/111.111 + lat0;
      loc = new Location(lat, lon);
      fault.add(loc);
      faultList.add(fault);
    }
  }


  private void writeFaultTraces() throws IOException {

    FileWriter fw = new FileWriter("scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/VC_faultTraces.txt");
    FaultTrace trace;
    Location tempLoc;
    for(int i=0; i< faultList.size();i++) {
      trace = (FaultTrace) faultList.get(i);
      fw.write(trace.getName()+"\t"+trace.getNumLocations()+"\n");
      for(int j=0; j<trace.getNumLocations();j++) {
        tempLoc = trace.get(j);
        fw.write((float)tempLoc.getLongitude()+"\t"+(float)tempLoc.getLatitude()+"\n");
      }
    }
    fw.close();


    fw = new FileWriter("scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/VC_faultNamesNumPts.txt");
    for(int i=0; i< faultList.size();i++) {
      trace = (FaultTrace) faultList.get(i);
      fw.write(trace.getName()+"\t"+trace.getNumLocations()+"\n");
    }
    fw.close();

  }


  public static void main(String[] args) {
    new VC_Analysis();
  }
}
