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

import java.util.GregorianCalendar;

import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.PointSurface;

/**
 * <p>Title: ObsEqkRupture </p>
 *
 * <p>Description: </p>
 *
 * <p>Copyright: Copyright (c) 2002</p>
 *
 * <p>Company: </p>
 *
 * @author not attributable
 * @version 1.0
 */
public class ObsEqkRupture
    extends EqkRupture implements java.io.Serializable{


  private String eventId;
  private String dataSource;
  private char eventVersion;
  private GregorianCalendar originTime;
  private double hypoLocHorzErr;
  private double hypoLocVertErr;
  private double magError ;
  private String magType;


  public ObsEqkRupture(){}

  public ObsEqkRupture(String eventId, String dataSource, char eventVersion,
                       GregorianCalendar originTime, double hypoLocHorzErr,
                       double hypoLocVertErr,double magError,
                      String magType, Location hypoLoc, double mag) {

   super(mag,0,null,hypoLoc);
   //making the Obs Rupture Surface to just be the hypocenter location.
   PointSurface surface = new PointSurface(hypoLoc);
   this.setRuptureSurface(surface);
   this.setObsEqkRup(eventId,dataSource,eventVersion,originTime,hypoLocHorzErr,
                     hypoLocVertErr, magError, magType);
  }

  public String getDataSource() {
    return dataSource;
  }

  public String getEventId() {
    return eventId;
  }

  public char getEventVersion() {
    return eventVersion;
  }

  public double getHypoLocHorzErr() {
    return hypoLocHorzErr;
  }

  public double getHypoLocVertErr() {
    return hypoLocVertErr;
  }

  public GregorianCalendar getOriginTime() {
    return originTime;
  }

  public double getMagError() {
    return magError;
  }

  public String getMagType() {
    return magType;
  }

  public void setObsEqkRup(String eventId, String dataSource, char eventVersion,
                       GregorianCalendar originTime, double hypoLocHorzErr,
                       double hypoLocVertErr, double magError,
  String magType){
    this.eventId = eventId;
    this.dataSource = dataSource;
    this.eventVersion = eventVersion;
    this.originTime = originTime;
    this.hypoLocHorzErr = hypoLocHorzErr;
    this.hypoLocVertErr = hypoLocVertErr;
    this.magError = magError;
    this.magType = magType;

  }
  public void setDataSource(String dataSource) {
    this.dataSource = dataSource;
  }

  public void setEventId(String eventId) {
    this.eventId = eventId;
  }

  public void setEventVersion(char eventVersion) {
    this.eventVersion = eventVersion;
  }

  public void setHypoLocHorzErr(double hypoLocHorzErr) {
    this.hypoLocHorzErr = hypoLocHorzErr;
  }

  public void setHypoLocVertErr(double hypoLocVertErr) {
    this.hypoLocVertErr = hypoLocVertErr;
  }

  public void setOriginTime(GregorianCalendar originTime) {
    this.originTime = originTime;
  }

  public void setMagError(double magError) {
    this.magError = magError;
  }

  public void setMagType(String magType) {
    this.magType = magType;
  }


  /**
   * Checks if the given ObsEqkRupture objects are same
   * @param obsRupEvent ObsEqkRupture
   * Note : Currently we are not checking if 2 Observed Eqk Rupture events
   * have same Gridded Surface, I don't think that is necessary, so havn't
   * added.
   * @return boolean
   */
  public boolean equalsObsEqkRupEvent(ObsEqkRupture obsRupEvent){

    boolean eventsEqual = true;

    //if any of the condition is not true else return false
    if(!eventId.equals(obsRupEvent.getEventId()) ||
       eventVersion != obsRupEvent.getEventVersion() ||
       !magType.equals(obsRupEvent.getMagType()) ||
       magError != obsRupEvent.getMagError() ||
       hypoLocHorzErr != obsRupEvent.getHypoLocHorzErr() ||
       hypoLocVertErr != obsRupEvent.getHypoLocVertErr() ||
       getMag() != obsRupEvent.getMag())
      return false;

    return eventsEqual;
  }



  /**
   * Checks if the passed object (obj) is similar to the object equalsObsEqkRup Object
   * on which this function was called.
   * Indicates whether some other object is "equal to" this one.
   * The equals method implements an equivalence relation  on non-null object references:
   * It is reflexive: for any non-null reference value  x, x.equals(x) should return  true.
   * It is symmetric: for any non-null reference values  x and y, x.equals(y)  should return true if and only if  y.equals(x) returns true.
   * It is transitive: for any non-null reference values  x, y, and z, if  x.equals(y) returns true and  y.equals(z) returns true, then  x.equals(z) should return true.
   * It is consistent: for any non-null reference values  x and y, multiple invocations of  x.equals(y) consistently return true  or consistently return false, provided no  information used in equals comparisons on the  objects is modified.
   * For any non-null reference value x,  x.equals(null) should return false.
   * The equals method for class Object implements the most discriminating possible equivalence relation on objects; that is, for any non-null reference values x and  y, this method returns true if and only  if x and y refer to the same object  (x == y has the value true).
   * Note that it is generally necessary to override the hashCode  method whenever this method is overridden, so as to maintain the  general contract for the hashCode method, which states  that equal objects must have equal hash codes
   * @param obj Object the reference object with which to compare
   * @return boolean true if this object is the same as the obj  argument; false otherwise.
   */
  public boolean equals(Object obj) {
    if (obj instanceof ObsEqkRupture)return equalsObsEqkRupEvent( (
        ObsEqkRupture) obj);
    return false;
  }


  /**
   * Gets the Info for the Observed EqkRupture
   * @return String
   */
  public String getInfo(){
    String obsEqkInfo = super.getInfo();
    obsEqkInfo += "EventId ="+eventId+"\n";
    obsEqkInfo += "DataSource ="+dataSource+"\n";
    obsEqkInfo += "EventVersion ="+eventVersion+"\n";
    obsEqkInfo += "OriginTime ="+originTime.toString()+"\n";
    obsEqkInfo += "HypoLocHorzErr ="+hypoLocHorzErr+"\n";
    obsEqkInfo += "HypoLocVertErr ="+hypoLocVertErr+"\n";
    obsEqkInfo += "MagError ="+magError+"\n";
    obsEqkInfo += "MagType ="+magType+"\n";
    return obsEqkInfo;
  }


  /**
   * Clones the eqk rupture and returns the new cloned object
   * @return
   */
 public Object clone() {
   ObsEqkRupture eqkEventClone=new ObsEqkRupture();
   eqkEventClone.setEventId(eventId);
   eqkEventClone.setMag(mag);
   eqkEventClone.setRuptureSurface(getRuptureSurface());
   eqkEventClone.setHypocenterLocation(hypocenterLocation);
   eqkEventClone.setDataSource(dataSource);
   eqkEventClone.setEventVersion(eventVersion);
   eqkEventClone.setOriginTime(originTime);
   eqkEventClone.setHypoLocHorzErr(hypoLocHorzErr);
   eqkEventClone.setHypoLocVertErr(hypoLocVertErr);
   eqkEventClone.setMagError(magError);
   eqkEventClone.setMagType(magType);
   eqkEventClone.setAveRake(aveRake);
   return eqkEventClone;
  }


}
