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

/**
 * <p>Title: DataRecord</p>
 *
 * <p>Description: Creates the record type.</p>
 * @author Ned Field , Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */
public abstract class DataRecord {
  //record number
  protected int recordNumber;

  //Location latitude
  protected float latitude;

  //Location longitude
  protected float longitude;

  //number of values
  protected short numValues;

  //SA values
  protected float[] values;

  /**
   * Reads the Record
   * @param fileName String
   * @param recordNum long
   */
  public abstract void getRecord(String fileName, long recordNum);

  /**
   * Returns the Latitude of the record
   * @return float
   */
  public float getLatitude() {
    return latitude;
  }

  /**
   * Returns the Longitude of the record
   * @return float
   */
  public float getLongitude() {
    return longitude;
  }

  /**
   * Returns the number of periods
   * @return short
   */
  public short getNumPeriods() {
    return numValues;
  }

  /**
   * Returns the Periods
   * @return float[]
   */
  public float[] getPeriods() {
    return values;
  }
}
