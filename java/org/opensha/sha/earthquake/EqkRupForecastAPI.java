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

package org.opensha.sha.earthquake;


import java.util.ArrayList;


/**
 * <b>Title:</b> EqkRupForecast<br>
 * <b>Description: This is the API for an Earthquake Rupture Forecast</b> <br>
 *
 * @author Nitin Gupta & Vipin Gupta
 * @date Aug 27, 2002
 * @version 1.0
 */

public interface EqkRupForecastAPI extends EqkRupForecastBaseAPI{

     /**
      *
      * @returns the total number os sources
      */
     public int getNumSources();

     /**
      *
      * @returns the sourceList
      */
     public ArrayList getSourceList();

     /**
      * Return the earhthquake source at index i.   Note that this returns a
      * pointer to the source held internally, so that if any parameters
      * are changed, and this method is called again, the source obtained
      * by any previous call to this method will no longer be valid.  
      * This is done for memory conservation.
      *
      * @param iSource : index of the desired source (only "0" allowed here).
      *
      * @return Returns the ProbEqkSource at index i
      *
      */
     public ProbEqkSource getSource(int iSource);


     /**
      *
      * @param iSource
      * @returns the number of ruptures for the ithSource
      */
     public int getNumRuptures(int iSource);


     /**
      *
      * @param iSource
      * @param nRupture
      * @returns the ProbEqkRupture object for the ithSource and nth rupture
      */
     public ProbEqkRupture getRupture(int iSource,int nRupture);
     
     /**
      * This draws a random event set.
      * @return
      */
     public ArrayList<EqkRupture> drawRandomEventSet();


}






