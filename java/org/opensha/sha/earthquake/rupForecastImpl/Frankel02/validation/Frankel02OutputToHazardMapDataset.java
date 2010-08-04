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

package org.opensha.sha.earthquake.rupForecastImpl.Frankel02.validation;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.text.DecimalFormat;
import java.util.StringTokenizer;

/**
 * <p>Title: Frankel02OutputToHazardMapDataset.java </p>
 * <p>Description: This will convert the Frankel 02 ASCII file test21_ca-all-pga.asc
 * into a hazard map dataset format. This file has hazard curve data for each site.
 * This file has 3 columns namely lat, lon and rate. To generate the Hazard Map Dataset,
 * we have to convert rate into probability using formula:
 *   prob = 1 - exp(rate*timeSpanDuration)
 *
 * Here timeSpanDuration will be assumed to be 50 years.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class Frankel02OutputToHazardMapDataset {
  double pga[] = {.005, .007, .0098, .0137, .0192, .0269, .0376, .0527, .0738,
      .103, .145, .203, .284, .397, .556, .778, 1.09, 1.52, 2.13};


  /**
   * This will read the fileName and then generate hazardmapdatset in newDir
   *
   * @param fileName Filename of ASCII output generated from Frankel 02 code
   * @param newDir New directory in which hazardMap datset will be generated
   */
  public Frankel02OutputToHazardMapDataset(String fileName, String newDir) {
    int timeDuration = 50;
    try {
      new File(newDir).mkdir();
      if(!newDir.endsWith("/")) newDir = newDir +"/";
      FileReader fr = new FileReader(fileName);
      BufferedReader br = new BufferedReader(fr);
      String str;
      StringTokenizer tokenizer;
      br.readLine();
      double lat,lon,val, prevLat=-1,prevLon=-1;
      //formatting of the text double Decimal numbers for 2 places of decimal.
      DecimalFormat d= new DecimalFormat("0.00##");
      FileWriter fw = null;
      int counter =0;
      while((str=br.readLine())!=null) {
        tokenizer = new StringTokenizer(str);
        lon = Double.parseDouble(tokenizer.nextToken());
        lat = Double.parseDouble(tokenizer.nextToken());
        val = Double.parseDouble(tokenizer.nextToken());
        if((prevLat==-1) || (prevLat!=lat) || (prevLon!=lon)) {
          if(prevLat!=-1) fw.close();
          fw = new FileWriter(newDir+d.format(lat) + "_" + d.format(lon) + ".txt");
          counter = 0;
          prevLat = lat;
          prevLon = lon;
        }
        fw.write(pga[counter]+" "+(1-Math.exp(-val*timeDuration))+"\n");
        ++counter;
      }
      fw.close();
      br.close();
      fr.close();
    }catch(Exception e) { e.printStackTrace(); }
  }

  /**
   * It will accept 2 command line arguments:
   * 1. Name of Frankel02 output file
   * 2. New directory where hazard map datset will be created.
   * @param args
   */
  public static void main(String[] args) {
    Frankel02OutputToHazardMapDataset frankel02OutputToHazardMapDataset1 =
        new Frankel02OutputToHazardMapDataset(args[0], args[1]);
  }

}
