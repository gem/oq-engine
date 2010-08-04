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
 * <p>Title: DataFileNameSelectorForFEMA</p>
 *
 * <p>Description: This class gives  name of the datafile to read based on the
 * analysis option, edition and location filled in by the user.
 * </p>
 * @author Ned Field, Nitin Gupta and E.V. Leyendecker
 * @version 1.0
 */
public class DataFileNameSelectorForFEMA {

  public DataFileNameSelectorForFEMA() {}
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

    return null;
  }

  /**
   *
   * @param selectedEdition String
   * @return String
   */
  private String getFileNameForAlaska(String selectedEdition,
                                      String spectraType) {

    if (selectedEdition.equals(GlobalConstants.FEMA_273_DATA) ||
        selectedEdition.equals(GlobalConstants.FEMA_356_DATA) ||
        selectedEdition.equals(GlobalConstants.IEBC_2003) ||
        selectedEdition.equals(GlobalConstants.FEMA_310_DATA) ||
        selectedEdition.equals(GlobalConstants.SCI_ASCE)) {
      if (spectraType.equals(GlobalConstants.MCE_GROUND_MOTION)) {
        String fileName = "1997-AK-MCE-R1a.rnd";
        return filePath + fileName;
      }
      else if (spectraType.equals(GlobalConstants.PE_10)) {
        String fileName = "1998-AK-Retrofit-10-050-a.rnd";
        return filePath + fileName;
      }

    }
    return null;
  }

  private String getFileNameForHawaii(String selectedEdition,
                                      String spectraType) {
    if (selectedEdition.equals(GlobalConstants.FEMA_273_DATA) ||
        selectedEdition.equals(GlobalConstants.FEMA_356_DATA) ||
        selectedEdition.equals(GlobalConstants.IEBC_2003)||
        selectedEdition.equals(GlobalConstants.FEMA_310_DATA) ||
        selectedEdition.equals(GlobalConstants.SCI_ASCE)) {
      if (spectraType.equals(GlobalConstants.MCE_GROUND_MOTION)) {
        String fileName = "1997-HI-MCE-R1a.rnd";
        return filePath + fileName;
      }
      else if (spectraType.equals(GlobalConstants.PE_10)) {
        String fileName = "1998-HI-Retrofit-10-050-a.rnd";
        return filePath + fileName;
      }

    }
    return null;
  }

  private String getFileNameFor48States(String selectedEdition, double lat,
                                        double lon, String spectraType) {
    if (selectedEdition.equals(GlobalConstants.FEMA_273_DATA) ||
        selectedEdition.equals(GlobalConstants.FEMA_356_DATA) ||
        selectedEdition.equals(GlobalConstants.IEBC_2003)||
        selectedEdition.equals(GlobalConstants.FEMA_310_DATA) ||
        selectedEdition.equals(GlobalConstants.SCI_ASCE)) {
      if (lon >= -125 && lon <= -111 && lat >= 32 && lat <= 43) {
        if (spectraType.equals(GlobalConstants.MCE_GROUND_MOTION)) {
          String fileName = "1997-CANV-MCE-R2.rnd";
          return filePath + fileName;
        }
        else if (spectraType.equals(GlobalConstants.PE_10)) {
          String fileName = "1996-CANV-Retrofit-10-050-a.rnd";
          return filePath + fileName;
        }
      }
      else {
        if (spectraType.equals(GlobalConstants.MCE_GROUND_MOTION)) {
          String fileName = "1997-US-MCE-R1a.rnd";
          return filePath + fileName;
        }
        else if (spectraType.equals(GlobalConstants.PE_10)) {
          String fileName = "1996-US-Retrofit-10-050-a.rnd";
          return filePath + fileName;
        }

      }
    }
    return null;
  }

}
