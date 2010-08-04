package scratch.ned.RundleAnalysis;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.Set;
import java.util.TreeMap;

/**
 * <p>Title: SegmentSlipTimeInfo</p>
 *
 * <p>Description: This class stores the Segment Slip time histories, sorting the list of
 * times/slips in order of time.</p>
 *
 * @author Edward (NEd) Field
 * @version 1.0
 */
public class SegmentSlipTimeInfo {


  //Segment number
  private int segmentNumber;
  //Mapping between the Time Pd and Slip during that time pd. at that segment number
  private TreeMap slipTimeHistoriesMap;


  /**
   * Class constructor
   * @param segmentNum int
   * @param timeHist ArrayList
   * @param slipHist ArrayList
   */
  public SegmentSlipTimeInfo(int segmentNum,ArrayList timeHist, ArrayList slipHist){
    segmentNumber = segmentNum;
    createSlipTimeSortedFunction(timeHist,slipHist);
  }


  /**
   * Set all the segment slip time info
   * @param segmentNum int
   * @param timeHist ArrayList
   * @param slipHist ArrayList
   */
  public void setAllForSegment(int segmentNum, ArrayList timeHist, ArrayList slipHist){
    segmentNumber = segmentNum;
    createSlipTimeSortedFunction(timeHist,slipHist);
  }


  /**
   * This function creates a sorted Slip time history function for a given segment number
   */
  private void createSlipTimeSortedFunction(ArrayList timeHist, ArrayList slipHist){
    slipTimeHistoriesMap = new TreeMap();
    int size = timeHist.size();
    for(int i=0;i<size;++i)
      slipTimeHistoriesMap.put(timeHist.get(i),slipHist.get(i));

  }

  /**
   * Return the Segment number
   * @return int
   */
  public int getSegmentNumber(){
    return segmentNumber;
  }

  /**
   * Return the Time histories for this segment
   * @return ArrayList
   */
  public ArrayList getTimeHistories(){
    Set timeHistSet = slipTimeHistoriesMap.keySet();
    Iterator it = timeHistSet.iterator();
    ArrayList timeHistList = new ArrayList();
    while(it.hasNext())
      timeHistList.add(it.next());
    return timeHistList;
  }


  /**
   * Return a list of recurrence intervals
   * @return ArrayList
   */
  public ArrayList getRecurrenceIntervals(){
    Set timeHistSet = slipTimeHistoriesMap.keySet();
    Iterator it = timeHistSet.iterator();
    ArrayList intervalList = new ArrayList();
    Integer nextYear, interval;
    Integer lastYear= (Integer)it.next();
    while(it.hasNext()) {
      nextYear = (Integer)it.next();
      interval = new Integer(nextYear.intValue()-lastYear.intValue());
      intervalList.add(interval);
      lastYear = nextYear;
    }
    return intervalList;
  }


  /**
   * Return the average recurrence interval
   * @return ArrayList
   */
  public double getAveRecurrenceInterval(){
    Set timeHistSet = slipTimeHistoriesMap.keySet();
    Iterator it = timeHistSet.iterator();
    double ave=0, num=0;
    Integer nextYear;
    Integer lastYear= (Integer)it.next();
    while(it.hasNext()) {
      nextYear = (Integer)it.next();
      ave += nextYear.doubleValue()-lastYear.doubleValue();
      lastYear = nextYear;
      num+=1.0;
    }
    return ave/num;
  }



  /**
   * Return a list of recurrence intervals (this only differs from
   * getRecurrenceIntervals in that is knows the years are Doubles)
   * @return ArrayList
   */
  public ArrayList getRecurrenceIntervalsRand(){
    Set timeHistSet = slipTimeHistoriesMap.keySet();
    Iterator it = timeHistSet.iterator();
    ArrayList intervalList = new ArrayList();
    Double nextYear, interval;
    Double lastYear= (Double)it.next();
    while(it.hasNext()) {
      nextYear = (Double)it.next();
      interval = new Double(nextYear.intValue()-lastYear.intValue());
      intervalList.add(interval);
      lastYear = nextYear;
    }
    return intervalList;
  }


  /**
   * Return the average recurrence interval (this only differs from
   * getAveRecurrenceInterval in that is knows the years are Doubles)
   * @return average
   */
  public double getAveRecurrenceIntervalRand(){
    Set timeHistSet = slipTimeHistoriesMap.keySet();
    Iterator it = timeHistSet.iterator();
    double ave=0, num=0;
    Double nextYear;
    Double lastYear= (Double)it.next();
    while(it.hasNext()) {
      nextYear = (Double)it.next();
      ave += nextYear.doubleValue()-lastYear.doubleValue();
      lastYear = nextYear;
      num+=1.0;
    }
    return ave/num;
  }


  /**
   * Return Slip histories occured during the given time pds on the segment.
   * @return ArrayList
   */
  public ArrayList getSlipHistories(){
    Set timeHistSet = slipTimeHistoriesMap.keySet();
    Iterator it = timeHistSet.iterator();
    ArrayList slipHistList = new ArrayList();
    while(it.hasNext())
      slipHistList.add(slipTimeHistoriesMap.get(it.next()));

    return slipHistList;

  }

  /**
   * This returns the slip corresponding the given year
   */
  public double getSlip(Integer year){
    return ((Double) slipTimeHistoriesMap.get(year)).doubleValue();
  }


  /**
   * This returns the slip corresponding the given year
   */
  public double getSlip(Double year){
    return ((Double) slipTimeHistoriesMap.get(year)).doubleValue();
  }


  /**
    * This returns the year of the last rupture before the given year.
    * null is return if the year is the first year or the year is not found
    * @param year Integer
    * @return Integer
    */
   public Integer getPreviousSlipTime(Integer year) {
     Integer lastYear = null, newYear;
     Set keySet = slipTimeHistoriesMap.keySet();
     Iterator it = keySet.iterator();
     while(it.hasNext()) {
       newYear = (Integer) it.next();
       if(newYear.intValue() == year.intValue())
         return lastYear;
       else
         lastYear = newYear;
     }
     // if we get to here return null (year not found)
     return null;
   }


   /**
     * This returns the year of the last rupture before the given year.
     * null is return if the year is the first year or the year is not found
     * @param year Integer
     * @return Integer
     */
    public Double getPreviousSlipTime(Double year) {
      Double lastYear = null, newYear;
      Set keySet = slipTimeHistoriesMap.keySet();
      Iterator it = keySet.iterator();
      while(it.hasNext()) {
        newYear = (Double) it.next();
        if(newYear.doubleValue() == year.doubleValue())
          return lastYear;
        else
          lastYear = newYear;
      }
      // if we get to here return null (year not found)
      return null;
    }

   /**
     * This returns the the amount of slip (cm) in the event that occurred before the given year.
     * NaN is return if the year is the first year or the year is not found
     * @param year Integer
     * @return slip (cm)
     */
    public double getPreviousSlip(Integer year) {
      Integer lastYear = null, newYear;
      Set keySet = slipTimeHistoriesMap.keySet();
      Iterator it = keySet.iterator();
      while(it.hasNext()) {
        newYear = (Integer) it.next();
        if(newYear.intValue() == year.intValue() && lastYear != null)
          return getSlip(lastYear);
        else
          lastYear = newYear;
      }
      // if we get to here return NaN (year not found or is the first year)
      return Double.NaN;
    }



    /**
  * This returns the the amount of slip (cm) in the event that occurred before the given year.
  * NaN is return if the year is the first year or the year is not found
  * @param year Integer
  * @return slip (cm)
  */
 public double getPreviousSlip(Double year) {
   Double lastYear = null, newYear;
   Set keySet = slipTimeHistoriesMap.keySet();
   Iterator it = keySet.iterator();
   while(it.hasNext()) {
     newYear = (Double) it.next();
     if(newYear.doubleValue() == year.doubleValue() && lastYear != null)
       return getSlip(lastYear);
     else
       lastYear = newYear;
   }
   // if we get to here return NaN (year not found or is the first year)
   return Double.NaN;
 }


    public Object clone() {
      return new SegmentSlipTimeInfo(getSegmentNumber(), getTimeHistories(),  getSlipHistories());
    }



}
