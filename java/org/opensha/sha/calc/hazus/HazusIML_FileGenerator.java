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

package org.opensha.sha.calc.hazus;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.StringTokenizer;
/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class HazusIML_FileGenerator {

  private final String Hazus ="HazusMapDataSets/";
  DecimalFormat format = new DecimalFormat("0.000000##");
  public HazusIML_FileGenerator() {

    format.setMaximumFractionDigits(6);
    // for each data set, read the meta data and sites info

    try{

      FileReader fr = new FileReader(Hazus+"metadata.dat");
      BufferedReader br = new BufferedReader(fr);
      String metadata = "#";
      String temp =br.readLine()+"\n";
      while(temp !=null){
        metadata +=temp+"\n"+"#";
        temp=br.readLine();
      }

      //doing for the return Pd:100
      double rate = 1.0/100;
      createReturnPdFile(Hazus+"final_100.dat",rate,metadata);

      //doing for the return Pd:250
      rate = 1.0/250;
      createReturnPdFile(Hazus+"final_250.dat",rate,metadata);

      //doing for the return Pd:500
      rate = 1.0/500;
      createReturnPdFile(Hazus+"final_500.dat",rate,metadata);

      //doing for the return Pd:750
      rate = 1.0/750;
      createReturnPdFile(Hazus+"final_750.dat",rate,metadata);

      //doing for the return Pd:1000
      rate = 1.0/1000;
      createReturnPdFile(Hazus+"final_1000.dat",rate,metadata);

      //doing for the return Pd:1500
      rate = 1.0/1500;
      createReturnPdFile(Hazus+"final_1500.dat",rate,metadata);

      //doing for the return Pd:2000
      rate = 1.0/2000;
      createReturnPdFile(Hazus+"final_2000.dat",rate,metadata);

      //doing for the return Pd:2500
      rate = 1.0/2500;
      createReturnPdFile(Hazus+"final_2500.dat",rate,metadata);

    }catch(Exception e){
      e.printStackTrace();
    }
  }


  /*public static void main(String[] args) {
    HazusIML_FileGenerator hazusIML_FileGenerator1 = new HazusIML_FileGenerator();
  }*/

  private void createReturnPdFile(String fileName,double rate,String metaData){
    ArrayList imlVector = new ArrayList();
    File dirsPGA =new File(Hazus+"pga/");
    String[] dirListPGA=dirsPGA.list();
    File dirsPGV =new File(Hazus+"pgv/");
    String[] dirListPGV=dirsPGV.list();
    File dirsSA =new File(Hazus+"sa_.3/");
    String[] dirListSA=dirsSA.list();
    File dirsSA_1 =new File(Hazus+"sa_1/");
    String[] dirListSA_1=dirsSA_1.list();

    //doing for the return Pd =100
    try{
    FileWriter fw = new FileWriter(fileName);
    fw.write(metaData);
    fw.write("#Column Info: Lat,Lon,PGA,PGV,SA-0.3,SA-1"+"\n\n");
    for(int i=0;i<dirListPGA.length;++i){
      imlVector.clear();
      if(dirListPGA[i].endsWith(".txt")){
        imlVector.add(new Double(getIML(Hazus+"pga/"+dirListPGA[i],rate)));
        imlVector.add(new Double(getIML(Hazus+"pgv/"+dirListPGV[i],rate)/2.5));
        imlVector.add(new Double(getIML(Hazus+"sa_.3/"+dirListSA[i],rate)));
        imlVector.add(new Double(getIML(Hazus+"sa_1/"+dirListSA_1[i],rate)));
      }

      String lat = dirListPGA[i].substring(0,dirListPGA[i].indexOf("_"));
      String lon = dirListPGA[i].substring(dirListPGA[i].indexOf("_")+1,dirListPGA[i].indexOf(".txt"));
      fw.write(lat+","+lon+",");
      for(int j=0;j<imlVector.size()-1;++j)
        fw.write(""+format.format(((Double)imlVector.get(j)).doubleValue())+",");
      fw.write(""+format.format(((Double)imlVector.get(imlVector.size()-1)).doubleValue())+"\n");
    }
    fw.close();
    }catch(Exception e){
      System.out.println("Error Occured");
      e.printStackTrace();
    }
  }

  private double getIML(String filename , double rate){
    try{
      FileReader fr = new FileReader(filename);
      BufferedReader br = new BufferedReader(fr);
      String prevLine = br.readLine();
      String currLine= br.readLine();
      StringTokenizer st =null;
      while(currLine!=null){
        st = new StringTokenizer(prevLine);
        double prevIML = new Double(st.nextToken()).doubleValue();
        double prevRate = new Double(st.nextToken()).doubleValue();
        st = new StringTokenizer(currLine);
        double currIML = new Double(st.nextToken()).doubleValue();
        double currRate = new Double(st.nextToken()).doubleValue();
        //System.out.println("CurrProb: "+currProb+" PrevProb: "+prevProb+" prob: "+prob);
        if(rate >=currRate && rate <=prevRate){
          double logCurrRate = Math.log(currRate);
          double logPrevRate = Math.log(prevRate);
          double logCurrIML = Math.log(currIML);
          double logPrevIML = Math.log(prevIML);
          rate = Math.log(rate);
          double iml = (((rate-logCurrRate)/(logPrevRate- logCurrRate)) *
                        (logPrevIML - logCurrIML)) + logCurrIML;
          return Math.exp(iml);
        }
        prevLine = currLine;
        currLine = br.readLine();
      }
    }catch(Exception e){
      System.out.println(filename+" file not found");
      e.printStackTrace();
    }
    return 0;
  }
}
