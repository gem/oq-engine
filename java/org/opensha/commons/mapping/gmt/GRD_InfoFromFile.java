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

package org.opensha.commons.mapping.gmt;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.StringTokenizer;

import org.opensha.commons.util.RunScript;

/**
 * <p>Title: GRD_InfoFromFile </p>
 * <p>Description: This class generates gets the info from a grd file (using GMT's
 * grdinfo command</p>
 * @author: Ned Field, Nitin Gupta, & Vipin Gupta
 * @created:Dec 21,2002
 * @version 1.0
 */

public class GRD_InfoFromFile {

  private boolean D = true;

  private String filename;

  // to be set from line 6 of the file output from grdinfo
  private double x_min = Double.NaN;
  private double x_max = Double.NaN;
  private double x_inc = Double.NaN;  // the discretization interval (increment)
  private String x_units = null;
  private int nx = 0;

  // to be set from line 7 of the file output from grdinfo
  private double y_min = Double.NaN;
  private double y_max = Double.NaN;
  private double y_inc = Double.NaN;  // the discretization interval (increment)
  private String y_units = null;
  private int ny = 0;

  // to be set from line 8 of the file output from grdinfo
  private double z_min = Double.NaN;
  private double z_max = Double.NaN;
  private String z_units = null;

  // here are the getter methods:
  public double get_x_min() { return x_min; }
  public double get_x_max() { return x_max; }
  public double get_x_inc() { return x_inc; }
  public String get_x_units() { return x_units; }
  public int get_nx() { return nx; }

  public double get_y_min() { return y_min; }
  public double get_y_max() { return y_max; }
  public double get_y_inc() { return y_inc; }
  public String get_y_units() { return y_units; }
  public int get_ny() { return ny; }

  public double get_z_min() { return z_min; }
  public double get_z_max() { return z_max; }
  public String get_z_units() { return z_units; }


  /**
   * empty constructor
   */
  public GRD_InfoFromFile() {}

  /**
   * non-empty constructor
   */
  public GRD_InfoFromFile(String filename,String gmtPath) { setFilename(filename,gmtPath); }


  public void setFilename(String filename, String gmtPath) {

    this.filename = filename;
    //line 6,7 and 8 strings declaration
    String line6=null,line7=null,line8=null;

    String tempFileName = "temp_" + filename + "_info";
    String[] command ={"sh","-c",gmtPath + "grdinfo " + filename + " > " + tempFileName};
    RunScript.runScript(command);

    /* What if multiple instances of this object are working doing this simultaneously with
    the same file; will there be any potential conflicts */

    // Now we have to read that file, put it into a string, and parse each line to set the
    // following info parameters
    try{
      //reading the output file
      BufferedReader reader = new BufferedReader(new FileReader(tempFileName));
      int count=0;

     //reads the first 5 lines of the output file and discards them
      while(count<5){
        String temp=reader.readLine();
        ++count;
      }
       //reads the line 6,7 and 8 from the output file
       line6 = reader.readLine();
       line7 = reader.readLine();
       line8 = reader.readLine();
    }catch(Exception ee){
      ee.printStackTrace();
    }

    if(D){
      System.out.println("Line-6:"+line6);
      System.out.println("Line-7:"+line7);
      System.out.println("Line-8:"+line8);
    }

    // set from line 6 of output file
    StringTokenizer st= new StringTokenizer(line6);
    int count=0;
    while(st.hasMoreTokens()){
      st.nextToken(); // reading the non-required elements from the line
      ++count; // to get the required elements from the file
      if(count==2) x_min = (new Double(st.nextToken())).doubleValue();
      else if(count==3) x_max = (new Double(st.nextToken())).doubleValue();
      else if(count==4) x_inc = (new Double(st.nextToken())).doubleValue();  // the discretization interval (increment)
      else if(count==5) x_units = new String(st.nextToken());
      else if(count==6) nx = Integer.parseInt(st.nextToken().toString());
    }

    if (D) System.out.println(x_min + "  " + x_max + "  " + x_inc + "  " + x_units + "  " + nx);

    // set from line 7 of the output file
    st= new StringTokenizer(line7);
    count=0;
    while(st.hasMoreTokens()){
      st.nextToken(); // reading the non-required elements from the line
      ++count; // to get the required elements from the file
      if(count==2) y_min = (new Double(st.nextToken())).doubleValue();
      else if(count==3) y_max = (new Double(st.nextToken())).doubleValue();
      else if(count==4) y_inc = (new Double(st.nextToken())).doubleValue();  // the discretization interval (increment)
      else if(count==5) y_units = new String(st.nextToken());
      else if(count==6) ny = Integer.parseInt(st.nextToken().toString());
    }

    if (D) System.out.println(y_min + "  " + y_max + "  " + y_inc + "  " + y_units + "  " + ny);

    // set from line 8 of the output file
    st= new StringTokenizer(line8);
    count=0;
    while(st.hasMoreTokens()){
      st.nextToken(); // reading the non-required elements from the line
      ++count; // to get the required elements from the file
      if(count==2) z_min = (new Double(st.nextToken())).doubleValue();
      else if(count==3) z_max = (new Double(st.nextToken())).doubleValue();
      else if(count==4) z_units = new String(st.nextToken());
    }

    if (D) System.out.println(z_min + "  " + z_max + "  " +  z_units);

  }


  /**
   * main function to test this class
   *
   * @param args
   */
  public static void main(String[] args) {
    // to test this class, it should create a temp.jpg
    GRD_InfoFromFile grdInfo = new GRD_InfoFromFile();
   // grdInfo.setFilename("testData.grd");
  }


}
