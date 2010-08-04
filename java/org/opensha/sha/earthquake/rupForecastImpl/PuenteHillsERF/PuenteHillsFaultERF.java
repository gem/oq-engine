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

package org.opensha.sha.earthquake.rupForecastImpl.PuenteHillsERF;

import java.util.ArrayList;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;


/**
 * <p>Title: PuenteHillsFaultERF</p>
 * <p>Description: This is   </p>
 *
 * @author Ned Field
 * Date : Oct 24 , 2002
 * @version 1.0
 */

public class PuenteHillsFaultERF extends EqkRupForecast{

  //for Debug purposes
  private static String  C = new String("PuenteHillsFaultERF");
  private boolean D = false;

  //name for this classs
  public final static String  NAME = "Puente Hills Fault ERF";

  private ArrayList sourceList;

  /**
   * Constructor for this source (no arguments)
   */
  public PuenteHillsFaultERF() {

    // create the timespan object with start time and duration in years
    timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
    timeSpan.addParameterChangeListener(this);

    FaultRuptureSource source;

    // MAKE THE FAULT SURFACE
    // the original fault trace points as given by Andreas Plesch (reversed to be in correct order)
    // Coyote Hills segment:
    //         B 117.868192971 33.899509717 -2500.00000
    //         A 118.044407949 33.894579252 -3441.00000
    // Santa Fe Springs segment:
    //         B 118.014078570 33.929699246 -2850.00000
    //         A 118.144918182 33.905266010 -2850.00000
    // Los Angeles segment:
    //         B 118.122170045 33.971013662 -3000.00000
    //         A 118.308353340 34.019965922 -3000.00000

    // Fault Trace (my merging of the four segments given by John Shaw and Andreas) at 3 km depth:

    //  33.8995	-117.868	3 km
    //  33.9122	-118.029	3 km
    //  33.9381	-118.133	3 km
    //  34.0200	-118.308	3 km


    FaultTrace faultTrace = new FaultTrace("Puente Hills Fault Trace");
    // this is to move the lats north to where depth is 5 km (assumes all orig depths are 3 km)
    double latIncr= (5.0-3.0)/(Math.tan(27*Math.PI/180)*111.0);
    if(D) System.out.println(this.NAME+": latIncr = "+latIncr);
    if(D) System.out.println(this.NAME+": fault trace name = "+faultTrace.getName());

    // for the jagged version:
    /*
    faultTrace.addLocation(new Location(33.899509717+latIncr,-117.868192971,5.0));
    faultTrace.addLocation(new Location(33.894579252+latIncr,-118.044407949,5.0));
    faultTrace.addLocation(new Location(33.929699246+latIncr,-118.014078570,5.0));
    faultTrace.addLocation(new Location(33.905266010+latIncr,-118.144918182,5.0));
    faultTrace.addLocation(new Location(33.971013662+latIncr,-118.122170045,5.0));
    faultTrace.addLocation(new Location(34.019965922+latIncr,-118.308353340,5.0));
    */

    // for the simpler, merged version
    faultTrace.add(new Location(33.8995+latIncr,-117.868,5.0));
    faultTrace.add(new Location(33.9122+latIncr,-118.029,5.0));
    faultTrace.add(new Location(33.9381+latIncr,-118.133,5.0));
    faultTrace.add(new Location(34.0200+latIncr,-118.308,5.0));

    if(D) System.out.println(this.NAME+" num fault trace points = "+ faultTrace.size());
    // make it dip exactly north
     double aveDipDir = 0.0;

    StirlingGriddedSurface surface = new StirlingGriddedSurface(faultTrace,27.0,5.0,17.0,1.0,aveDipDir);

     double rake = 90;

    if(D) System.out.println(this.NAME+" aveDipDir = "+ aveDipDir);
    if(D) System.out.println(this.NAME+" rake = "+ rake);

    sourceList = new ArrayList();
    for(int mag=71; mag<=75;mag += 1) {
      source = new FaultRuptureSource((double)mag/10.0, surface, rake, 0.2);
      source.setName("mag = "+(double)mag/10.0+" PH fault source");
      sourceList.add(source);
    }

    if (D) System.out.println(NAME+": number of sources = "+sourceList.size());

  }



   /**
    * update the source based on the paramters (only if a parameter value has changed)
    */
   public void updateForecast(){
     String S = C + "updateForecast::";

     if(parameterChangeFlag) {
       parameterChangeFlag = false;
     }

   }


   /**
    * Return the earhthquake source at index i.   Note that this returns a
    * pointer to the source held internally, so that if any parameters
    * are changed, and this method is called again, the source obtained
    * by any previous call to this method will no longer be valid.
    *
    * @param iSource : index of the desired source (only "0" allowed here).
    *
    * @return Returns the ProbEqkSource at index i
    *
    */
   public ProbEqkSource getSource(int iSource) {
    return (FaultRuptureSource) sourceList.get(iSource);
   }


   /**
    * Returns the number of earthquake sources
    *
    * @return integer value specifying the number of earthquake sources
    */
   public int getNumSources(){
     return sourceList.size();
   }


    /**
     *  This returns a list of sources
     *
     * @return ArrayList of Prob Earthquake sources
     */
    public ArrayList  getSourceList(){
      return this.sourceList;
    }


  /**
   * Return the name for this class
   *
   * @return : return the name for this class
   */
   public String getName(){
     return NAME;
   }
}
