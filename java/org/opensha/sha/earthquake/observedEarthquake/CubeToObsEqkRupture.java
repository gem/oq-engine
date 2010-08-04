/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.earthquake.observedEarthquake;

import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.GregorianCalendar;

import org.opensha.commons.geo.Location;
import org.opensha.commons.util.FileUtils;

import scratch.matt.calc.RegionDefaults;


/**
 * <p>Title: CubeToObsEqkRupture</p>
 *
 * <p>Description: This class will create the ObsEqkRupture object from the
 * data string that it receives from the network catalog. </p>
 *
 * Note : Mag read from the QDM cube format file is not always assumed to be
 * moment mag.
 *
 * @author Nitin Gupta , Vipin Gupta and Ned Field
 * @version 1.0
 */
public class CubeToObsEqkRupture {


  //Gets  the ObsEqkRupEvents from QDM Cube File
  private ObsEqkRupList eqkRupList;

  //define the region for which we have to collect the events
  private  double MIN_LAT = RegionDefaults.searchLatMin;//32.0;
  private  double MAX_LAT = RegionDefaults.searchLatMax;//42.2;
  private  double MIN_LON = RegionDefaults.searchLongMin;//-124.6;
  private  double MAX_LON = RegionDefaults.searchLongMax;//-112.0;


  public CubeToObsEqkRupture(String eventFile) throws FileNotFoundException,
      IOException {
    //reading the lines into an arrayList from a the Cube format file to read all the
    //ObsEqk Events.
    ArrayList fileLines = FileUtils.loadFile(eventFile);
    int numEvents = fileLines.size();
    eqkRupList = new ObsEqkRupList();
    for (int i = 0; i < numEvents; ++i) {

      String obsEqkRupString = (String)fileLines.get(i);
      ObsEqkRupture obsEqkEvent = readFile(obsEqkRupString);
      if(obsEqkEvent !=null)
        eqkRupList.addObsEqkEvent(obsEqkEvent);
    }
    fileLines = null;
  }


  private ObsEqkRupture readFile(String obsEqkEvent) {
    // sRecord represents one full line of the CUBE file
    // Gather all the attributes for this earthquake message; we use trim to get rid of leading and trailing whitespace
    String sMsgType = obsEqkEvent.substring(0,2).trim();
    ObsEqkRupture rupture = null;
    if (sMsgType.equals("E")) {
      String sEventId = obsEqkEvent.substring(2, 10).trim();
      String sDataSource = obsEqkEvent.substring(10, 12).trim();
      char sEventVersion = obsEqkEvent.substring(12, 13).trim().charAt(0);
      String sYear = obsEqkEvent.substring(13, 17).trim();
      String sMonth = obsEqkEvent.substring(17, 19).trim();
      String sDay = obsEqkEvent.substring(19, 21).trim();
      String sHour = obsEqkEvent.substring(21, 23).trim();
      String sMinute = obsEqkEvent.substring(23, 25).trim();
      String sSecond = divideAndGetString(obsEqkEvent.substring(25, 28), 10);
      //sSecond = sSecond.substring(0, sSecond.indexOf('.')); //This is to get rid of the decimal point in seconds
      String sLatitude = divideAndGetString(obsEqkEvent.substring(28, 35),
                                            10000);
      String sLongitude = divideAndGetString(obsEqkEvent.substring(35, 43),
                                             10000);
      String sDepth = divideAndGetString(obsEqkEvent.substring(43, 47), 10);
      double lat = Double.parseDouble(sLatitude);
      double lon = Double.parseDouble(sLongitude);
      double depth = Double.parseDouble(sDepth);

      //if lat or lon of the events are outside the region bounds then neglect them.
      if(lat < MIN_LAT || lat >MAX_LAT)
        return null;
      if(lon < MIN_LON || lon > MAX_LON)
        return null;

      String sMagnitude = divideAndGetString(obsEqkEvent.substring(47, 49), 10);
      //if(sMagnitude ==null || sMagnitude.equals(""))
        //return null;
      //String sNst = sRecord.substring(49, 52).trim();
      //String sNph = sRecord.substring(52, 55).trim();
      //String sDmin = divideAndGetString(sRecord.substring(55, 59), 10);
      //String sRmss = divideAndGetString(sRecord.substring(59, 63), 100);
      String sErho = divideAndGetString(obsEqkEvent.substring(63, 67), 10);
      String sErzz = divideAndGetString(obsEqkEvent.substring(67, 71), 10);
      //String sGap = multiplyAndGetString(sRecord.substring(71, 73), 3.6);
      String sMagnitudeType = obsEqkEvent.substring(73, 74).trim();
      //String sNumberOfStations = obsEqkEvent.substring(74, 76).trim();
      String sMagnitudeError = divideAndGetString(obsEqkEvent.substring(76, 78),
                                                  10);
      //String sLocationMethod = obsEqkEvent.substring(78, 79).trim();

      //getting the Origin time for the ObsEvent in terms of Gregorian Calender
      int year = Integer.parseInt(sYear);
      int month = Integer.parseInt(sMonth);
      int day = Integer.parseInt(sDay);
      int hour = Integer.parseInt(sHour);
      int min = Integer.parseInt(sMinute);
      int sec = (int) Double.parseDouble(sSecond);
      GregorianCalendar originTime = new GregorianCalendar(year, month-1, day, hour,
          min, sec);

      //Hypocenter Location at which EqkRupture occured

      Location hypoLoc = new Location(lat, lon, depth);

      //magnitude of the rupture
      double mag = Double.parseDouble(sMagnitude);
      double horzErr =0, vertErr=0, magErr=0;
      if(sErho !=null && !sErho.equals(""))
        horzErr = Double.parseDouble(sErho);
      if(sErzz !=null && !sErzz.equals(""))
        vertErr = Double.parseDouble(sErzz);
      if(sMagnitudeError !=null && !sMagnitudeError.equals(""))
        magErr = Double.parseDouble(sMagnitudeError);
      rupture = new ObsEqkRupture(sEventId,sDataSource,sEventVersion,
                                                originTime,horzErr,vertErr,magErr,
                                                sMagnitudeType,hypoLoc,mag);
    }
    return rupture;
  }

   /**
    * Input: an input string to be converted and divided and the divisor by which we'll divide
    * Output: a string that contains the manipulated value
    * Notes: CUBE format files do not contain decimal points, so some of the raw
    * data must be divided in order to get the actual value.
    * This function does the division if data is present in the field and returns
    * the string representation of the actual data value.
    * @param sIn String
    * @param dDivisor double
    * @return String
    */
   private String divideAndGetString(String sIn, double dDivisor) {

     double dTemp;
     // we only want to perform the division if we have data for this parameter
     if (sIn.trim().length() > 0) {
       dTemp = Double.parseDouble(sIn); // convert the string to a double
       dTemp /= dDivisor; // perform the division
       return (Double.toString(dTemp)); // convert the double back to a string
     }
     // return an empty string w/o performing division
     else {
       return "";
     }
   }


   /**
    * Returns the list of ObsEqkRuptures as read from the QDM CUBE format file.
    * @return ObsEqkRupList
    */
   public ObsEqkRupList getAllObsEqkRupEvents(){
     return eqkRupList;
   }

   /**
    * Returns the ObsEqkRupture from the list of observed EqkRup list at a given index.
    * @param index int index in the ObsEqkRupList at which ObsEqkEvent is to be retrieved.
    * @return ObsEqkRupture
    */
   public ObsEqkRupture getObsEqkRupture(int index){
     return (ObsEqkRupture)eqkRupList.getObsEqkRuptureAt(index);
   }

   /**
    * Method to test and see if we are reading the network catalog file correctly.
    * @param args String[]
    */
   public static void main(String args[]){
    CubeToObsEqkRupture cubeToRup = null;
    try {
      cubeToRup = new CubeToObsEqkRupture("/Users/nitingupta/merge.nts");
    }
    catch (FileNotFoundException ex) {
      ex.printStackTrace();
    }
    catch (IOException ex) {
      ex.printStackTrace();
    }
     ObsEqkRupList rupList = cubeToRup.getAllObsEqkRupEvents();
     rupList.sortObsEqkRupListByOriginTime();
     int size = rupList.size();
     try{
       FileWriter fw = new FileWriter("ObsEqkRup.txt");
       for (int i = 0; i < size; ++i) {
         ObsEqkRupture eqkRup = (ObsEqkRupture) rupList.getObsEqkRuptureAt(i);
         fw.write("Obs EqkRupture: "+i+"\n");
         fw.write(eqkRup.getInfo()+"\n\n");
       }
       fw.close();
     }catch(Exception e){
       e.printStackTrace();
     }
   }
}
