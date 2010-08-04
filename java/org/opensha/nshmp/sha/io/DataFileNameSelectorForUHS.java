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

package org.opensha.nshmp.sha.io;

import org.opensha.nshmp.util.GlobalConstants;

/**
 * <p>Title: DataFileNameSelectorForUHS</p>
 *
 * <p>Description: This class gives  name of the datafile to read based on the
 * analysis option, edition, location and spectra type filled in by the user.
 * </p>
 * @author Ned Field, Nitin Gupta and E.V. Leyendecker
 * @version 1.0
 */
public class DataFileNameSelectorForUHS {
	private final static String filePath = GlobalConstants.DATA_FILE_PATH;

  /**
   *
   * @param selectedRegion String
   * @param selectedEdition String
   * @param lat double
   * @param lon double
   * @return String
   */
  public String getFileName(String selectedRegion, String selectedEdition,
                            double lat, double lon, String spectraType) {
    if (selectedRegion.equals(GlobalConstants.CONTER_48_STATES)) {
      return getFileNameFor48States(selectedEdition, lat, lon, spectraType);
    }
    else if (selectedRegion.equals(GlobalConstants.ALASKA)) {
      return getFileNameForAlaska(selectedEdition, spectraType);
    }
    else if (selectedRegion.equals(GlobalConstants.HAWAII)) {
      return getFileNameForHawaii(selectedEdition, spectraType);
    }
    else {
      return getFileNameForPRVI(selectedEdition, spectraType);
    }
  }

  /**
   * Gets the filename for the region of Alaska
   * @param selectedEdition String
   * @return String
   */
  private String getFileNameForAlaska(String selectedEdition,
                                      String spectraType) {

    if (spectraType.equals(GlobalConstants.PE_2)) {
      String fileName = "1998-AK-UHS-02-050-R2a.rnd";
      return filePath + fileName;
    }
    else if (spectraType.equals(GlobalConstants.PE_10)) {
      String fileName = "1998-AK-UHS-10-050-R2a.rnd";
      return filePath + fileName;
    }
    return null;
  }

  private String getFileNameForPRVI(String selectedEdition, String spectraType) {
    if (spectraType.equals(GlobalConstants.PE_2)) {
      String fileName = "2003-PRVI-UHS-02-050-R1a.rnd";
      return filePath + fileName;
    }
    else if (spectraType.equals(GlobalConstants.PE_10)) {
      String fileName = "2003-PRVI-UHS-10-050-R1a.rnd";
      return filePath + fileName;
    }
    return null;
  }

  /**
   * Getting the filenames for the region of Hawaii
   * @param selectedEdition String
   * @param selectedHazardCurveType String
   * @return String
   */
  private String getFileNameForHawaii(String selectedEdition,
                                      String spectraType) {
    if (spectraType.equals(GlobalConstants.PE_2)) {
      String fileName = "1998-HI-UHS-02-050-R2a.rnd";
      return filePath + fileName;
    }
    else if (spectraType.equals(GlobalConstants.PE_10)) {
      String fileName = "1998-HI-UHS-10-050-R2a.rnd";
      return filePath + fileName;
    }
    return null;

  }

  /**
   * Gets the filename for the Counter 48 states with selected analysis option being
   * Hazard curves.
   * @param selectedEdition String
   * @param lat double
   * @param lon double
   * @param spectraType String
   * @return String
   */
  private String getFileNameFor48States(String selectedEdition, double lat,
                                        double lon, String spectraType) {
    if (selectedEdition.equals(GlobalConstants.data_1996)) {
      if (lon >= -125 && lon <= -111 && lat >= 32 && lat <= 43) { //getting the file for CA and NV
        if (spectraType.equals(GlobalConstants.PE_2)) {
          String fileName = "1996-CANV-UHS-02-050-R2a.rnd";
          return filePath + fileName;
        }
        else if (spectraType.equals(GlobalConstants.PE_5)) {
          String fileName = "1996-CANV-UHS-05-050-R2a.rnd";
          return filePath + fileName;
        }
        else if (spectraType.equals(GlobalConstants.PE_10)) {
          String fileName = "1996-CANV-UHS-10-050-R2a.rnd";
          return filePath + fileName;
        }
      } //end of Data file for California and NV
      else { //getting the filename for whole of US other then CA and NV
        if (spectraType.equals(GlobalConstants.PE_2)) {
          String fileName = "1996-US-UHS-02-050-R2a.rnd";
          return filePath + fileName;
        }
        else if (spectraType.equals(GlobalConstants.PE_5)) {
          String fileName = "1996-US-UHS-05-050-R2a.rnd";
          return filePath + fileName;
        }
        else if (spectraType.equals(GlobalConstants.PE_10)) {
          String fileName = "1996-US-UHS-10-050-R2a.rnd";
          return filePath + fileName;
        }
      }
    } //End for the 48 states and data edition to be 1996
    else if (selectedEdition.equals(GlobalConstants.data_2002)) { //reading the data for 2002
      if (spectraType.equals(GlobalConstants.PE_2)) {
        String fileName = "2002-US-UHS-02-050-R1a.rnd";
        return filePath + fileName;
      }
      else if (spectraType.equals(GlobalConstants.PE_10)) {
        String fileName = "2002-US-UHS-10-050-R1a.rnd";
        return filePath + fileName;
      }
    }
    return null;
  }
}
