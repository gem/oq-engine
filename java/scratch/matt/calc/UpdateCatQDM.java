package scratch.matt.calc;

import java.io.BufferedWriter;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.Date;
import java.util.GregorianCalendar;
import java.util.ListIterator;
import java.util.StringTokenizer;
import java.util.TimeZone;

import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class UpdateCatQDM {
  public static int iLR_Year, iLR_Month, iLR_Day, iLR_Hour, iLR_Min, iLR_Sec;
  public UpdateCatQDM() {
  }

  public static int readTimeStamp(String stampFileName){
    ArrayList lastCatReadTime = null;
    try {
      lastCatReadTime = FileUtils.loadFile(stampFileName);
    }
    catch (FileNotFoundException e) {
      e.printStackTrace();
    }
    catch (IOException e) {
      e.printStackTrace();
    }

    // get an iterator for the input file lines
    ListIterator it = lastCatReadTime.listIterator();
    // use the tokenizer to step thru the string
    StringTokenizer st = new StringTokenizer(it.next().toString());
    // advance to skip the text
    st.nextToken();st.nextToken();st.nextToken();st.nextToken();
    iLR_Year = Integer.parseInt(st.nextToken());
    iLR_Month = Integer.parseInt(st.nextToken())-1;
    iLR_Day = Integer.parseInt(st.nextToken());
    iLR_Hour = Integer.parseInt(st.nextToken());
    iLR_Min = Integer.parseInt(st.nextToken());
    iLR_Sec = Integer.parseInt(st.nextToken());
    return iLR_Year; // this is useless at the mo - need to figure out how to return the entire date
  }

  public static int findQDM_Updates(String qdmCatFile, String updatedFile,
                                    String tsFile){
    long dayDiff = 0;
    int updateCt = 0;
    ArrayList qdmCatLine = null;
    ArrayList updatedEvents = new ArrayList();
    PrintWriter updatePW = null;
    PrintWriter stampOut = null;

    try {
      qdmCatLine = FileUtils.loadFile(qdmCatFile);
    }
    catch (FileNotFoundException e) {
      System.out.println(e.toString());
    }
    catch (IOException e) {
      System.out.println(e.toString());
    }

    GregorianCalendar calendar = new GregorianCalendar(TimeZone.getTimeZone(
        "UTC"));;
    calendar.set(iLR_Year, iLR_Month, iLR_Day, iLR_Hour, iLR_Min, iLR_Sec); // set last cat read time
    Date lastReadDate = calendar.getTime();


    // get an iterator for the input file lines
    ListIterator it = qdmCatLine.listIterator();
    while (it.hasNext()) {

      String cubeLine = new String(it.next().toString());
      int iYear = Integer.parseInt(cubeLine.substring(0, 4));
      int iMonth = Integer.parseInt(cubeLine.substring(5, 7))-1;
      int iDay = Integer.parseInt(cubeLine.substring(8, 10));
      int iHour = Integer.parseInt(cubeLine.substring(11, 13));
      int iMin = Integer.parseInt(cubeLine.substring(14, 16));
      int iSec = Integer.parseInt(cubeLine.substring(17, 19));

      calendar.set(iYear, iMonth, iDay, iHour, iMin, iSec); //time of loaded event
      Date eventDate = calendar.getTime();
      dayDiff = (eventDate.getTime() - lastReadDate.getTime());
          /// (1000 * 60 * 60 * 24);
      //System.out.println(dayDiff);
      //System.out.println(lastReadDate.getTime());
      if (dayDiff < 0)continue; // if this event was updated b4 the last read, ignore
      System.out.println(eventDate.getTime());
      (updatedEvents).add(cubeLine);
      updateCt++;
    }

    // write out the new time stamp file after reading in all of the new data
    GregorianCalendar curCalendar = new
        GregorianCalendar(TimeZone.getTimeZone("GMT"));
    String curDate = new String();
    curDate = "Last QDM Catalogue Read: ";
    int year = curCalendar.get(curCalendar.YEAR);
    curDate = curDate.concat(String.valueOf(year)+" ");
    curDate = curDate.concat(String.valueOf(curCalendar.get(curCalendar.MONTH)+1)+" ");
    curDate = curDate.concat(String.valueOf(curCalendar.get(curCalendar.DATE))+" ");
    curDate = curDate.concat(String.valueOf(curCalendar.get(curCalendar.HOUR_OF_DAY))+" ");
    curDate = curDate.concat(String.valueOf(curCalendar.get(curCalendar.MINUTE))+" ");
    curDate = curDate.concat(String.valueOf(curCalendar.get(curCalendar.SECOND)));
      System.out.println(curDate);
    try{
      BufferedWriter bw = new BufferedWriter(new FileWriter(tsFile));
      stampOut = new PrintWriter(bw);
      stampOut.println(curDate);
      stampOut.close();

    }
    catch( Exception e){
        e.printStackTrace();
    }

    // write out the new event file containing all events/updates occurring after the timestamp
    try{
      BufferedWriter bwout = new BufferedWriter(new FileWriter(updatedFile));
      updatePW = new PrintWriter(bwout);
    }
    catch( Exception e){
        e.printStackTrace();
    }
    System.setProperty("line.separator", "\n");
    ListIterator itUpdate = updatedEvents.listIterator();
    while (itUpdate.hasNext()) {
      String updateLine = new String(itUpdate.next().toString());
      String cutString = updateLine.substring(20,99);
      updatePW.println(cutString);
    }
    updatePW.close();
    return updateCt;
  }

  public static void main(String[] args) {
    UpdateCatQDM updateCatQDM1 = new UpdateCatQDM();
    String tsFile = "/home/matt/ForecastMap/QDDS/QDMcat/TimeStamp.txt";
    String catFile = "/home/matt/ForecastMap/QDDS/QDMcat/merge.sum";
    String updatedFile = "/home/matt/ForecastMap/UpdatedCat/UpdatedEvents.cat";

    //int ts = readTimeStamp(tsFile);
    //long td = findQDM_Updates(catFile);

    readTimeStamp(tsFile);
    findQDM_Updates(catFile,updatedFile,tsFile);

  }

}
