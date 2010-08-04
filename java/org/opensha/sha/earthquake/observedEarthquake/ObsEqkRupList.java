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

import java.util.ArrayList;
import java.util.Collections;
import java.util.GregorianCalendar;
import java.util.ListIterator;

import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.EqkRuptureMagComparator;

/**
 * <p>Title: ObsEqkRupList</p>
 *
 * <p>Description: This class provide capabilty of storing observed events as
 * a list. Also defines the function using which user can extract a subset of the
 * list based on Magnitude  range, origin time or geographic Region.
 * It also defines functions that allows user to Sort the list based on Mag,
 * Origin Time.</p>
 *
 * @author Nitin Gupta, Vipin Gupta and Edward (Ned) Field
 * @version 1.0
 */


public class ObsEqkRupList implements java.io.Serializable{

  /** Class name used for debugging purposes */
  protected final static String C = "ObsEqkRupList";

  /** if true print out debugging statements */
  protected final static boolean D = false;

  private ArrayList obsEqkList = new ArrayList();

  /**
   * Returns the list of the Observed events above/at the given magnitude.
   * @param mag double Magnitude
   * @returns the subset of total observed events as ObsEqkRupList list
   * above a given magnitude
   */
  public ObsEqkRupList getObsEqkRupsAboveMag(double mag) {
    ObsEqkRupList obsEventList = new ObsEqkRupList();
    int size = size();
    for (int i = 0; i < size; ++i) {
      ObsEqkRupture eqkRup = (ObsEqkRupture) obsEqkList.get(i);
      if (eqkRup.getMag() >= mag)
        obsEventList.addObsEqkEvent(eqkRup);
    }
    return obsEventList;
  }

  /**
   * Returns the list of the Observed events below the given magnitude.
   * @param mag double Magnitude
   * @returns the subset of total observed events as ObsEqkRupList list
   * below a given magnitude
   */
  public ObsEqkRupList getObsEqkRupsBelowMag(double mag) {
    ObsEqkRupList obsEventList = new ObsEqkRupList();
    int size = size();
    for (int i = 0; i < size; ++i) {
      ObsEqkRupture eqkRup = (ObsEqkRupture) obsEqkList.get(i);
      if (eqkRup.getMag() < mag)
        obsEventList.addObsEqkEvent(eqkRup);

    }
    return obsEventList;
  }

  /**
   * Returns the list of the Observed events between 2 given magnitudes.
   * It includes lower magnitude in the range but excludes the upper magnitude.
   * @param mag1 double lower magnitude
   * @param mag2 double upper magnitude
   * @returns the subset of total observed events as ObsEqkRupList list
   * between 2 given magnitudes.
   */
  public ObsEqkRupList getObsEqkRupsBetweenMag(double mag1, double mag2) {
    ObsEqkRupList obsEventList = new ObsEqkRupList();
    int size = size();
    for (int i = 0; i < size; ++i) {
      ObsEqkRupture eqkRup = (ObsEqkRupture) obsEqkList.get(i);
      double eventMag = eqkRup.getMag();
      if (eventMag >= mag1 && eventMag < mag2)
        obsEventList.addObsEqkEvent(eqkRup);
    }
    return obsEventList;

  }

  /**
   * Returns the list of Observed events before a given time period
   * @param cal GregorianCalendar Time Period
   * @returns the subset of total observed events as ObsEqkRupList list
   * before a given time period
   */
  public ObsEqkRupList getObsEqkRupsBefore(GregorianCalendar cal) {

    ObsEqkRupList obsEventList = new ObsEqkRupList();
    int size = size();
    for (int i = 0; i < size; ++i) {
      ObsEqkRupture eqkRup = (ObsEqkRupture) obsEqkList.get(i);
      GregorianCalendar eventTime = eqkRup.getOriginTime();
      if (eventTime.before(cal))
        obsEventList.addObsEqkEvent(eqkRup);
    }
    return obsEventList;
  }



  /**
   * Returns the list of Observed events after a given time period
   * @param cal GregorianCalendar Time Period
   * @returns the subset of total observed events as ObsEqkRupList list
   * after a given time period
   */
  public ObsEqkRupList getObsEqkRupsAfter(GregorianCalendar cal) {
    ObsEqkRupList obsEventList = new ObsEqkRupList();
    int size = size();
    for (int i = 0; i < size; ++i) {
      ObsEqkRupture eqkRup = (ObsEqkRupture) obsEqkList.get(i);
      GregorianCalendar eventTime = eqkRup.getOriginTime();
      if (eventTime.after(cal))
        obsEventList.addObsEqkEvent(eqkRup);
    }
    return obsEventList;

  }

  /**
   * Returns the list of the Observed events between 2 given time periods.
   * @param cal1 GregorianCalendar Time Period
   * @param cal2 GregorianCalendar Time Period
   * @returns the subset of total observed events as ObsEqkRupList list
   * between 2 given time periods.
   */
  public ObsEqkRupList getObsEqkRupsBetween(GregorianCalendar cal1,
                                        GregorianCalendar cal2) {
    ObsEqkRupList obsEventList = new ObsEqkRupList();
    int size = size();
    for (int i = 0; i < size; ++i) {
      ObsEqkRupture eqkRup = (ObsEqkRupture) obsEqkList.get(i);
      GregorianCalendar eventTime = eqkRup.getOriginTime();
      if (eventTime.after(cal1) && eventTime.before(cal2))
        obsEventList.addObsEqkEvent(eqkRup);
    }
    return obsEventList;

  }

  /**
   * Returns the list of the Observed events inside a given geographic region
   * @param region Region
   * @returns the subset of total observed events as ObsEqkRupList list
   * inside a given region.
   */
  public ObsEqkRupList getObsEqkRupsInside(Region region) {
    ObsEqkRupList obsEventList = new ObsEqkRupList();
    int size = size();
    for (int i = 0; i < size; ++i) {
      ObsEqkRupture eqkRup = (ObsEqkRupture) obsEqkList.get(i);
      Location loc = eqkRup.getHypocenterLocation();
      if(region.contains(loc))
        obsEventList.addObsEqkEvent(eqkRup);
    }
    return obsEventList;

  }

  /**
   * Returns the list of the Observed events outside a given geographic region
   * @param region Region
   * @returns the subset of total observed events as ObsEqkRupList list
   * outside a given region.
   */
  public ObsEqkRupList getObsEqkRupsOutside(Region region) {
    ObsEqkRupList obsEventList = new ObsEqkRupList();
    int size = size();
    for (int i = 0; i < size; ++i) {
      ObsEqkRupture eqkRup = (ObsEqkRupture) obsEqkList.get(i);
      Location loc = eqkRup.getHypocenterLocation();
      if (!region.contains(loc))
        obsEventList.addObsEqkEvent(eqkRup);
    }
    return obsEventList;
  }

  /**
   * Returns the list of ObsEqkRuptures as ArrayList.
   * @return ArrayList of ObsEqkRuptures.
   */
  public ArrayList getObsEqkRupEventList() {
    return obsEqkList;
  }


  /**
   *  Returns parameter at the specified index if exist, else throws
   *  exception. Recall that these Observed Eqk Rupture events are stored
   *  in a ArrayList, which is like an array. Therefore you can access items by
   *  index.
   *
   * @param  index  Description of the Parameter
   * @return        ObsEqkRupture event in the list at the given index.
   */
  public ObsEqkRupture getObsEqkRuptureAt(int index) throws
      InvalidRangeException {
    checkIndex(index);
    return (ObsEqkRupture) obsEqkList.get(index);
  }

  /** Validates that an index falls within the internal data structure range */
  private void checkIndex(int index) throws InvalidRangeException {

    if (size() < index + 1)throw new InvalidRangeException(
        C + ": getLocationAt(): " +
        "Specified index larger than array size."
        );

  }

  /**
   *  Replaces the ObsEqkRup event in the list at the specified index if it is a valid index.
   *  An exception is thrown if the specified index is invalid.
   *
   * @param  obsEqkEvent  Observed Rupture Event that is to be added
   * @param  index     location in the list at which this event needs to be added.
   */
  public void replaceObsEqkRupEventAt(ObsEqkRupture obsEqkEvent, int index) throws
      InvalidRangeException {
    checkIndex(index);
    obsEqkList.set(index, obsEqkEvent);
  }

  /**
   * Inserts the ObsEqkRup event at the given index location.
   *
   * @param  location  The feature to be added to the ObsEqkRupture attribute
   * @param index int Index at which location is to be added
   *
   * Inserts the specified element at the specified position in this list.
   * Shifts the element currently at that position (if any) and any subsequent
   * elements to the right (adds one to their indices).
   */
  public void addObsEqkEventAt(ObsEqkRupture obsEqkEvent, int index) {
    obsEqkList.add(index, obsEqkEvent);
  }


  /**
   * This adds a list of events to the existing list of events. List of events is
   * added to the ObsEqkRupList object on which this function is called.
   * @param obsRupEventList ObsEqkRupList
   *
   * Appends all of the elements in the specified Collection to the end of this
   * list, in the order that they are returned by the specified Collection's Iterator.
   * The behavior of this operation is undefined if the specified Collection is
   * modified while the operation is in progress. (This implies that the behavior
   * of this call is undefined if the specified Collection is this list, and
   * this list is nonempty.)
   *
   * @return true if this list changed as a result of the call.
   */
  public boolean addAllObsEqkRupEvents(ObsEqkRupList obsRupEventList){
    return obsEqkList.addAll(obsRupEventList.getObsEqkRupEventList());
  }




  /**
   * Returns the number of ObsEqkRupEvents in the list
   * @return int
   */
  public int size() {
    return obsEqkList.size();
  }

  /**
   *  Adds the Observed Eqk Events to the end of the list.
   *
   * @param  obsEqkEvent allowsd user to just add the ObsEqkRupture event
   */
  public void addObsEqkEvent(ObsEqkRupture obsEqkEvent) {
    obsEqkList.add(obsEqkEvent);
  }

  /**
   *  Returns a list iterator of all Observed Eqk events in this list, in the order they
   *  were added to the list
   *
   */
  public ListIterator listIterator() {
    return obsEqkList.listIterator();
  }

  /**  Removes all Observed Eqk Events from the list */
  public void clear() {
    obsEqkList.clear();
  }


  /**
   * Sorts the Observed Eqk Rupture Event list based on the magitude.
   *
   */
  public void sortObsEqkRupListByMag(){
    Collections.sort(obsEqkList, new EqkRuptureMagComparator());
  }

  /**
   * Sorts the Observed Eqk Rupture Event list based on the Origin time.
   *
   */
  public void sortObsEqkRupListByOriginTime() {
    Collections.sort(obsEqkList,new ObsEqkRupEventOriginTimeComparator());
  }

  /**
   * Compares  2 ObsEqkRupList.
   * It checks if both ObsEqkRupList object contains the same ObsEqkRupture objects.
   * @param obj ObsEqkRupList Obj
   * @return 0 if both object are same else return -1
   */
  public int compareTo(Object obj) {

    boolean compareFlag = true;
    if (! (obj instanceof ObsEqkRupList)) {
      throw new ClassCastException(C +
                                   "Object not a ObsEqkRupList, unable to compare");
    }

    ObsEqkRupList obsEventList = (ObsEqkRupList) obj;

    ListIterator it = obsEventList.listIterator();
    ListIterator it1 = listIterator();

    if (size() != obsEventList.size())
      return -1;

    while (it.hasNext()) {
      ObsEqkRupture event1 = (ObsEqkRupture) it.next();
      ObsEqkRupture event2 = (ObsEqkRupture) it1.next();
      compareFlag = event1.equals(event2);

      if (compareFlag == false)
        break;
    }

    if (!compareFlag)
      return -1;

    return 0;
  }

  /**
   * Returns the index of ObsEqkRupture event with the given observed eqk rupture
   * list.
   * @param obsEqkEvent ObsEqkRupture finds index of this location
   * @return int index in the List.
   */
  public int getIndex(ObsEqkRupture obsEqkEvent) {
    return obsEqkList.indexOf(obsEqkEvent);
  }

}
