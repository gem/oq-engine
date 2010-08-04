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

package junk;

import java.io.DataInputStream;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.IOException;

/**
 * <p>Title: Bin2Ascii4Floats</p>
 * <p>Description: Converts the Binary to Ascii for the floats because
 * each element in the binary is of 4 bytes and it is equivalent to float or
 * int in java.</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class Bin2Ascii4Floats {

  public Bin2Ascii4Floats() {
  }
  public static void main(String[] args) {
//    Bin2Ascii4Floats binary2Ascii1 = new Bin2Ascii4Floats();

    if(args.length <1)
      System.out.println("Usage : Binary2Ascii <filename>");
    else{
      int i=0;
      FileWriter fw = null;
      FileInputStream fp =null;
      DataInputStream dis = null;
      try{
        fw = new FileWriter(args[0]+".asc");
        fp = new FileInputStream(args[0]);
        dis = new DataInputStream(fp);
        while(dis!=null){
          fw.write(dis.readFloat()+"\n");
          ++i;
        }
      }catch(IOException e){
        //e.printStackTrace();
        //System.out.println(args[0]);
      }
      finally{
        System.out.println("Rows: "+i);
        try{
        dis.close();
        fp.close();
        fw.close();
        }catch(Exception e){
          e.printStackTrace();
        }
      }

    }

  }
}
