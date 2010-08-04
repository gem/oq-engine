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

package org.opensha.nshmp.util;

import java.util.ArrayList;

import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.Region;
import org.opensha.nshmp.exceptions.AnalysisOptionNotSupportedException;



/**
 * <p>Title: RegionUtil</p>
 *
 * <p>Description: </p>

 * @author not attributable
 * @version 1.0
 */
public final class RegionUtil {

  /**
   *
   * @param selectedAnalysisOption String
   * @return ArrayList
   */
  public static ArrayList getSupportedGeographicalRegions(String
      selectedAnalysisOption) throws AnalysisOptionNotSupportedException {
    ArrayList<String> supportedRegionList = new ArrayList<String>();
    if (selectedAnalysisOption.equals(GlobalConstants.NEHRP) ||
        selectedAnalysisOption.equals(GlobalConstants.ASCE_7) ||
        selectedAnalysisOption.equals(GlobalConstants.NFPA) ||
        selectedAnalysisOption.equals(GlobalConstants.INTL_BUILDING_CODE)) {
      supportedRegionList.add(GlobalConstants.CONTER_48_STATES);
      supportedRegionList.add(GlobalConstants.ALASKA);
      supportedRegionList.add(GlobalConstants.HAWAII);
      supportedRegionList.add(GlobalConstants.PUERTO_RICO);
      supportedRegionList.add(GlobalConstants.CULEBRA);
      supportedRegionList.add(GlobalConstants.ST_CROIX);
      supportedRegionList.add(GlobalConstants.ST_JOHN);
      supportedRegionList.add(GlobalConstants.ST_THOMAS);
      supportedRegionList.add(GlobalConstants.VIEQUES);
      supportedRegionList.add(GlobalConstants.TUTUILA);
      supportedRegionList.add(GlobalConstants.GUAM);
    }
    else if (selectedAnalysisOption.equals(GlobalConstants.PROB_HAZ_CURVES) ||
             selectedAnalysisOption.equals(GlobalConstants.PROB_UNIFORM_HAZ_RES) ||
				 selectedAnalysisOption.equals(GlobalConstants.INTL_RESIDENTIAL_CODE)) {
      supportedRegionList.add(GlobalConstants.CONTER_48_STATES);
      supportedRegionList.add(GlobalConstants.ALASKA);
      supportedRegionList.add(GlobalConstants.HAWAII);
      // Add this only for Hazard Curves
      /*if(selectedAnalysisOption.equals(GlobalConstants.PROB_HAZ_CURVES)) {
  		supportedRegionList.add(GlobalConstants.INDONESIA);
  	  }*/
      supportedRegionList.add(GlobalConstants.PUERTO_RICO);
      supportedRegionList.add(GlobalConstants.CULEBRA);
      supportedRegionList.add(GlobalConstants.ST_CROIX);
      supportedRegionList.add(GlobalConstants.ST_JOHN);
      supportedRegionList.add(GlobalConstants.ST_THOMAS);
      supportedRegionList.add(GlobalConstants.VIEQUES);
    } 	
    /*else if (selectedAnalysisOption.equals(GlobalConstants.FEMA_IEBC_2003)) {
      supportedRegionList.add(GlobalConstants.CONTER_48_STATES);
      supportedRegionList.add(GlobalConstants.ALASKA);
      supportedRegionList.add(GlobalConstants.HAWAII);
    }*/
    else {
      throw new AnalysisOptionNotSupportedException(
          "This " + selectedAnalysisOption +
          " analysis option not supported!!\nPlease provide correct option.");
    }

    return supportedRegionList;
  }

  /**
   *
   * @return RectangularGeographicRegion
   */
  public static Region getRegionConstraint(String
      selectedGeographicRegion) throws RegionConstraintException {

    if (selectedGeographicRegion.equals(GlobalConstants.CONTER_48_STATES)) {
      //return new Region(24.7, 50, -125, -65);
      return new Region(
    		  new Location(24.7,-125),
    		  new Location(50, -65));
    }
    else if (selectedGeographicRegion.equals(GlobalConstants.ALASKA)) {
    	// TODO this must have problems, both in past and present
    	// implementations; spans dateline
      //return new Region(48, 72, -200, -125);
      return new Region(
    		  new Location(48, -200),
    		  new Location(72, -125));
    }
    else if (selectedGeographicRegion.equals(GlobalConstants.HAWAII)) {
        //return new Region(18, 23, -161, -154);
        return new Region(
      		  new Location(18, -161),
      		  new Location(23, -154));
    }
    else if (selectedGeographicRegion.equals(GlobalConstants.PUERTO_RICO)) {
        //return new Region(17.89, 18.55, -67.36, -65.47);
        return new Region(
        		  new Location(17.89, -67.36),
          		  new Location(18.55, -65.47));
    }
    else if (selectedGeographicRegion.equals(GlobalConstants.CULEBRA)) {
      //return new Region(18.27, 18.36, -65.39, -65.21);
      return new Region(
      		  new Location(18.27, -65.39),
      		  new Location(18.36, -65.21));
    }
    else if (selectedGeographicRegion.equals(GlobalConstants.ST_CROIX)) {
      //return new Region(17.67, 17.8, -64.93, -64.54);
      return new Region(
      		  new Location(17.67, -64.93),
      		  new Location(17.8, -64.54));
    }
    else if (selectedGeographicRegion.equals(GlobalConstants.ST_JOHN)) {
      //return new Region(18.29, 18.38, -64.85, -64.65);
      return new Region(
      		  new Location(18.29, -64.85),
      		  new Location(18.38, -64.65));
    }
    else if (selectedGeographicRegion.equals(GlobalConstants.ST_THOMAS)) {
      //return new Region(18.26, 18.43, -65.10, -64.80);
      return new Region(
      		  new Location(18.26, -65.10),
      		  new Location(18.43, -64.80));
    }
    else if (selectedGeographicRegion.equals(GlobalConstants.VIEQUES)) {
      //return new Region(18.07, 18.17, -65.6, -65.25);
      return new Region(
      		  new Location(18.07, -65.6),
      		  new Location(18.17, -65.25));
    }
    /*else if (selectedGeographicRegion.equals(GlobalConstants.INDONESIA)) {
    	return new RectangularGeographicRegion(-10.0, 8.00, 92, 118);
    }*/

    return null;
  }

  /**
   * Returns the IMT periods for the selected Region.
   * Used in the Prob Hazard Curves
   * @param selectedRegion String
   * @return ArrayList
   */
  public static ArrayList getSupportedIMT_PERIODS(String selectedRegion) {
    ArrayList<String> supportedImtPeriods = new ArrayList<String>();
    if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES)) {
      supportedImtPeriods.add(GlobalConstants.PGA);
      supportedImtPeriods.add(GlobalConstants.IMT_POINT_ONE_SEC);
      supportedImtPeriods.add(GlobalConstants.IMT_POINT_TWO_SEC);
      supportedImtPeriods.add(GlobalConstants.IMT_POINT_THREE_SEC);
      //supportedImtPeriods.add(GlobalConstants.IMT_POINT_FOUR_SEC);
      supportedImtPeriods.add(GlobalConstants.IMT_POINT_FIVE_SEC);
      supportedImtPeriods.add(GlobalConstants.IMT_ONE_SEC);
      supportedImtPeriods.add(GlobalConstants.IMT_TWO_SEC);
    }
    else if (selectedRegion.equals(GlobalConstants.HAWAII) ||
             selectedRegion.equals(GlobalConstants.ALASKA)) {
      supportedImtPeriods.add(GlobalConstants.PGA);
      supportedImtPeriods.add(GlobalConstants.IMT_POINT_TWO_SEC);
      supportedImtPeriods.add(GlobalConstants.IMT_POINT_THREE_SEC);
      supportedImtPeriods.add(GlobalConstants.IMT_ONE_SEC);
    }
    else {
      supportedImtPeriods.add(GlobalConstants.PGA);
      supportedImtPeriods.add(GlobalConstants.IMT_POINT_TWO_SEC);
      supportedImtPeriods.add(GlobalConstants.IMT_ONE_SEC);
    }
    return supportedImtPeriods;
  }

}
