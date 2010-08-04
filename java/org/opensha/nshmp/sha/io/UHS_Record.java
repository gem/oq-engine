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

import java.io.IOException;
import java.io.RandomAccessFile;

import org.apache.commons.io.EndianUtils;
import org.opensha.nshmp.util.GlobalConstants;


/**
 * <p>Title: UHS_Record </p>
 *
 * <p>Description: Creates the record type for the UHS</p>
 * @author Ned Field , Nitin Gupta and E.V.Leyendecker
 * @version 1.0
 */

public class UHS_Record
    extends DataRecord {

  //Hazard Period
  public float uhsFex;

  //Record Length
  public static final int recordLength = 4 + 4 + 4 + 4 + 4 + (7 * 4);

  public void getRecord(String fileName, long recordNum) {
    values = new float[7];
    RandomAccessFile fin = null;
    try {
      fin = new RandomAccessFile(fileName, "r");
      fin.seek( (recordNum - 1) * recordLength);
      //recordNumber = ByteSwapUtil.swap(fin.readInt());
      recordNumber = EndianUtils.swapInteger(fin.readInt());
      //latitude = ByteSwapUtil.swapIntToFloat(fin.readInt());
      latitude = Float.intBitsToFloat(EndianUtils.swapInteger(fin.readInt()));
      //longitude = ByteSwapUtil.swapIntToFloat(fin.readInt());
      longitude = Float.intBitsToFloat(EndianUtils.swapInteger(fin.readInt()));
      //uhsFex = ByteSwapUtil.swapIntToFloat(fin.readInt());
      uhsFex = Float.intBitsToFloat(EndianUtils.swapInteger(fin.readInt()));
      //numValues = ByteSwapUtil.swap(fin.readShort());
      numValues = EndianUtils.swapShort(fin.readShort());
      
      for (int i = 0; i < numValues; ++i) {
        //values[i] = ByteSwapUtil.swapIntToFloat(fin.readInt());
        values[i] = Float.intBitsToFloat(EndianUtils.swapInteger(fin.readInt()));
        values[i] /= GlobalConstants.DIVIDING_FACTOR_HUNDRED;
      }
      fin.close();
    }
    catch (IOException ex) {
      ex.printStackTrace();
    }
  }

}
