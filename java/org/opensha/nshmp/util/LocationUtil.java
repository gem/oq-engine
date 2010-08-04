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

import org.opensha.commons.geo.Location;
import org.opensha.nshmp.exceptions.ZipCodeErrorException;

/**
 * <p>Title: LocationUtil</p>
 *
 * <p>Description: Provides the utillities for the location</p>
 * @author Ned Field, Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public final class LocationUtil {

  /**
   *
   * Checks if the zip code entered is a valid for the region the user has selected
   * @param loc Location
   * @param selectedRegion String
   * @throws ZipCodeErrorException thrown if locations Lat and Lon are not within
   * the selected Geographic Region.
   */
  public static void checkZipCodeValidity(Location loc, String selectedRegion) throws
      ZipCodeErrorException {
    double lat = loc.getLatitude();
    double lon = loc.getLongitude();
    //if selected Region is Counterminous 48 states
    if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES)) {
      if (lat >= 24.6 && lat <= 50 && lon >= -125 && lon <= -65) {
        return;
      }
      else if (lat >= 48 && lat <= 72 && lon >= -200 && lon <= -125) {
        throw new ZipCodeErrorException(
            "The Zip Code is outside the geographic region of counterminous 48 states.\n" +
            "It is in Alaska");
      }
      else if (lat >= 18 && lat <= 23 && lon >= -161 && lon <= -154) {
        throw new ZipCodeErrorException(
            "The Zip Code is outside the geographic region of counterminous 48 states.\n" +
            "It is in Hawaii");

      }
    }
    //if selected region is Alaska
    else if (selectedRegion.equals(GlobalConstants.ALASKA)) {
      if (lat >= 24.6 && lat <= 50 && lon >= -125 && lon <= -65) {
        throw new ZipCodeErrorException(
            "The Zip Code is outside the geographic region of Alaska." +
            "It is in counterminous 48 states");
      }
      else if (lat >= 48 && lat <= 72 && lon >= -200 && lon <= -125) {
        return;
      }
      else if (lat >= 18 && lat <= 23 && lon >= -161 && lon <= -154) {
        throw new ZipCodeErrorException(
            "The Zip Code is outside the geographic region of Alaska." +
            "It is in Hawaii.");

      }
    }
    //if selected region is Hawaii
    else if (selectedRegion.equals(GlobalConstants.HAWAII)) {
      if (lat >= 24.6 && lat <= 50 && lon >= -125 && lon <= -65) {
        throw new ZipCodeErrorException(
            "The Zip Code is outside the geographic region of Hawaii." +
            "It is in counterminous 48 states");
      }
      else if (lat >= 48 && lat <= 72 && lon >= -200 && lon <= -125) {
        throw new ZipCodeErrorException(
            "The Zip Code is outside the geographic region of Hawaii." +
            "It is in Alaska.");
      }
      else if (lat >= 18 && lat <= 23 && lon >= -161 && lon <= -154) {
        return;
      }
    }

  }

  /**
   *
   * @return boolean
   */
  public static boolean isZipCodeSupportedBySelectedEdition(String
      selectedRegion) {

    if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES)) {
      return true;
    }
    else if (selectedRegion.equals(GlobalConstants.ALASKA)) {
      return true;
    }
    else if (selectedRegion.equals(GlobalConstants.HAWAII)) {
      return true;
    }

    return false;
  }

}
