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

package org.opensha.nshmp.sha.data.region;

import java.text.DecimalFormat;

import org.opensha.nshmp.sha.io.DataRecord;

/**
 * <p>Title: RegionBounds</p>
 *
 * <p>Description: This class returns the region bounds for given datafile.
 * </p>
 * @author Ned Field, Nitin Gupta and E.V. Leyendecker
 * @version 1.0
 */
public class RegionBounds {

  private int gridPointsPerLatitude;
  private float[] saPeriods;
  private int numPeriods;
  private float minLat;
  private float maxLat;
  private float minLon;
  private float maxLon;
  private float gridSpacing;

  private DecimalFormat gridSpacingFormat = new DecimalFormat("0.0#");

  /**
   * Class constructor takes the binary file to read the region bounds.
   * @param dataFileName String takes in the binary filename which has a fix file format
   * and conforms to the NEHRP Record.
   */
  public RegionBounds(DataRecord record, String dataFileName) {
    getRegionEndPoints(record, dataFileName);
  }

  /**
   * Gets the end points for the region for the selected region and edition
   * @param fileName String takes in the binary filename which has a fix file format
   * and conforms to the NEHRP Record.
   *
   */
  private void getRegionEndPoints(DataRecord record, String fileName) {

    record.getRecord(fileName, 1);
    maxLat = record.getLatitude();
    minLon = record.getLongitude();
    record.getRecord(fileName, 2);
    minLat = record.getLatitude();
    maxLon = record.getLongitude();

    record.getRecord(fileName, 4);
    float longitude1 = record.getLongitude();
    record.getRecord(fileName, 5);
    float longitude2 = record.getLongitude();
    gridSpacing = Math.abs(longitude1 - longitude2);

    gridSpacing = Float.parseFloat(gridSpacingFormat.format(gridSpacing));
    gridPointsPerLatitude = (int) ( (maxLon - minLon) / gridSpacing) + 1;

    record.getRecord(fileName, 3);
    numPeriods = record.getNumPeriods();
    saPeriods = record.getPeriods();
  }

  public float getMinLat() {
    return minLat;
  }

  public float getMinLon() {
    return minLon;
  }

  public float getMaxLat() {
    return maxLat;
  }

  public float getMaxLon() {
    return maxLon;
  }

  public float getGridSpacing() {
    return gridSpacing;
  }

  public int getNumPeriods() {
    return numPeriods;
  }

  public int getNumPointsPerLatitude() {
    return gridPointsPerLatitude;
  }

  public float[] getSA_Periods() {
    return saPeriods;
  }

}
