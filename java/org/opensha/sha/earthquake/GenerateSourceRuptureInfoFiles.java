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

package org.opensha.sha.earthquake;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF1.WGCEP_UCERF1_EqkRupForecast;



/**
 * <p>Title: GenerateSourceRuptureInfoFiles</p>
 *
 * <p>Description: This allows the user to create various lists for an earthquake rupture forecast,
 * rupture and ERF.</p>
 *
 * @author Nitin Gupta
 * @since March 1, 2006
 * @version 1.0
 */
public class GenerateSourceRuptureInfoFiles {



  public GenerateSourceRuptureInfoFiles() {
    super();
  }


  /**
   * Create the Directory where all source and rupture information will be dumped.
   * @param dirName String
   * @return String
   */
  private String createDirectory(String dirName){
    File f = new File(dirName);
    boolean success = f.mkdir();
    if(success)
      return f.getAbsolutePath();
    return null;
  }


  /**
   * Creates the EqkRupForecast Metadata file
   * @param directoryPath String path to the directory where files are to be created
   * @param forecast EqkRupForecast : Eqk Rup Forecast
   */
  public void createERF_MetadataFile(String directoryPath,EqkRupForecast forecast){

    String forecastMetadata = "EqkRupForecast Name= "+forecast.getName()+"\n";
    forecastMetadata += forecast.adjustableParams.getParameterListMetadataString();
    String timeSpanMetadata = forecast.getTimeSpan().getAdjustableParams().getParameterListMetadataString();
    FileWriter fw = null;
    try {
      fw = new FileWriter(directoryPath+"/ERF_Metadata.txt");
      fw.write(forecastMetadata+"\n");
      fw.write(timeSpanMetadata);
      fw.close();
    }
    catch (IOException ex) {
      ex.printStackTrace();
    }
  }

  /**
   * Creates the source list file, writes out the metadata for each source in a file
   * in each line of file
   * @param directoryPath String path to the directory where files are to be created
   * @param forecast EqkRupForecast : Earthquake Rupture Forecast
   * @returns the path to the source directory, where al the information about the
   * ruptures will be stored
   */
  public void createSourceListFile(String directoryPath,EqkRupForecast forecast) {
    //String sourceDirName = "source";
    FileWriter fw = null;
    FileWriter fw_rupture = null;
    try {
      fw = new FileWriter(directoryPath+"/sourceList.txt");
      fw_rupture = new FileWriter(directoryPath+"/ruptureList.txt");
      int numSources = forecast.getNumSources();
      //System.out.println("NumSources ="+numSources);
      //fw.write("#Source-Index   NumRuptures    IsPoission    Total-Prob.   Src-Name\n");
      //fw_rupture.write(
        //  "#Src-Index  Rup-Index  Mag  Prob.  Ave.Rake   Ave. dip   \"Source-Name\"\n");
      for(int i=0;i<numSources;++i){
        ProbEqkSource source = forecast.getSource(i);
        fw.write(source.getSourceMetadata()+"\n");
        //File f = new File(directoryPath+"/"+sourceDirName + i);
        //f.mkdir();
        //create the rupture list in one big file
        createRuptureListFile(fw_rupture,source,i);
      }
      fw_rupture.close();
      fw.close();
    }
    catch (IOException ex) {
      ex.printStackTrace();
    }
    return ;
  }


  /**
   * Creates the Rupture list file which gives the metadata for a rupture in each line of
   * file. It only displays the list of ruptures in a given source.
   * @param sourceDir String
   * @param source ProbEqkSource
   */
  public void createRuptureListFile(FileWriter rupfile, ProbEqkSource source,int sourceIndex){

    int numRuptures = source.getNumRuptures();
    try{

      for (int i = 0; i < numRuptures; ++i) {
        ProbEqkRupture rupture = source.getRupture(i);
        rupture.setRuptureIndexAndSourceInfo(sourceIndex,
                                             source.getName(), i);
        rupfile.write(rupture.getRuptureMetadata()+"\n");
        /*GriddedSurfaceAPI surface = rupture.getRuptureSurface();
        if(!(surface instanceof PointSurface))
          createRuptureSurfaceFile(sourceDir,rupture);*/
      }
    }catch(IOException e){
      e.printStackTrace();
    }
  }


  /**
   * Creates the individual metadata file for each rupture surface.
   * @param sourceDir String
   * @param rupture ProbEqkRupture
   */
  public void createRuptureSurfaceFile(String sourceDir,
                                       ProbEqkRupture rupture){
    FileWriter fw = null;
    try{
      fw = new FileWriter(sourceDir+"/"+rupture.getRuptureIndex()+".txt");
     // fw.write(
       //   "#Ave-Dip  RupSurface-Length  Rup-DownDipWidth  GridSpacing "+
        // "NumRows   NumCols   NumPoints \n");
      fw.write(rupture.getRuptureSurface().getSurfaceMetadata());
      fw.close();

    }catch(IOException e){
      e.printStackTrace();
    }

  }


  /**
   * Creates the Readme file for user to understand how the Source-Rupture info.
   * has been structured and which information can be located in files. It also
   * explains how directories are presented and what metadata was used to create
   * these files.
   */
  public void createReadMeFile(String directoryPath){
    FileWriter fw = null;
    try{
      fw = new FileWriter(directoryPath+"/"+"Readme.txt");
      /*fw.write(
          "This file explains how source and rupture files have been structured.\n");
      fw.write(
          "It also tells user what information is contained in each file.\n");
      fw.write(
          "The program used to create these source rupture files takes the " +
          "directory name as the command line input where all the source and ruptures " +
          "file will be created, also referred to as root level directory.\n");
      fw.write(
          "At the same level as this Readme file, it has 3 other files:\n");
      fw.write(
          "1) ERF_Metadata.txt - This file contains the information about the " +
          " Earthquake Rupture Forecast (ERF), what were parameters value for which " +
          "this ERF was instantiated.\n");
      fw.write(
          "2)SourceList.txt - This file contains information about each source in the " +
          "Earthquake Rupture Forecast model. Each source information is contained in single line " +
          " in the file.Each line tab delimited with first line being the comment line " +
          "contains following information:\n");
      fw.write("Source-Index   NumRuptures    IsPoission    Total-Prob.   Src-Name.\n");
      fw.write(
          "For each source in the ERF a file is created that contains " +
          "the ruptures information for that source.\nThis file that list all the ruptures for a given source "+
          "is named as source number appened with \"ruptureList.txt\" in the ERF. For eg: file for "+
          "source 0 is labeled as \"0_ruptureList.txt\".\n");
      fw.write(" This rupture list file for each source contains the following information about each " +
               "rupture defined on the given source :\n");
      fw.write(
          "#Src-Index  Rup-Index  Mag  Prob.  Ave.Rake  Ave. Dip  \"Source-Name\"\n");
      fw.write(
          "Each line the above file gives the information on each rupture defined " +
          "on the source.\nEach element is tab delimited. Elements mentioned as " +
          "\"conditional\" are only present if rupture surface is a point surface location, "+
          "they are discarded.\n");
      /*fw.write(
          "Each source directory also contains the Rupture Surface that gives the following info. "+
          "about the surface in a single line(tab demilited):\n");
      fw.write(
          "#Ave-Dip  RupSurface-Length  Rup-DownDipWidth  GridSpacing "+
          "NumRows   NumCols   NumPoints .\n");
      fw.write(
          "This file also gives the each point location on the surface with " +
          "each line defining the lat lon depth of a point location on the surface. " +
          "It is also a tab delimited file with location defined as:\n\t\t " +
          "Lat   Lon   Depth\n");
      fw.write(
          "Any file that contains \"#\" refers to comment line in the file " +
          "that describes the contents of the file below that line.\n");
      fw.write(
          "Rupture Surface files are created for a rupture if it is not a point surface, "+
          "otherwise it just write out the point surface locations of the rupture "+
          "in the \"ruptureList.txt\" file.");*/

      fw.write("This file explains the information contained in each of the other files here.\n"+
               "1) ERF_Metadata.txt - The gives the name of the Earthquake Rupture Forecast (ERF) and "+
               "how any adjustable parameters were set.\n"+
               "2) sourceList.txt - This contains information about each source in the Earthquake Rupture Forecast.  "+
               "After a header line, the info for each source is on a separate line as follows (tab delimited):\n\n"+
               "\t\tSource-Index   NumRuptures    IsPoission    Total-Prob.   Src-Name. \n\n"+
               "3) ruptureList.txt - This contains the following information for each rupture (tab delimited):\n"+
               "\t\tSrc-Index  Rup-Index  Mag  Prob.  Ave.Rake  Ave. Dip  \"Source-Name\" \n\n"+
              "We don't yet include the rupture surfaces because it is not yet clear how users want "+
              "this represented (there are several options, most of which consume a great deal of disk space).\n");
     fw.close();

    }catch(IOException e){
      e.printStackTrace();
    }
  }


  /*
   * Main method to start the application
   * @param args String[]
   */
  public static void main(String[] args) {
    GenerateSourceRuptureInfoFiles generatesourceruptureinfofiles = new
        GenerateSourceRuptureInfoFiles();
    String directoryPath = generatesourceruptureinfofiles.createDirectory("WGCEP_UCERF_5yrs");
    if(directoryPath !=null || !directoryPath.trim().equals("")){
      WGCEP_UCERF1_EqkRupForecast ucerf = null;

      ucerf = new
          WGCEP_UCERF1_EqkRupForecast();

      ucerf.getAdjustableParameterList().getParameter(
          WGCEP_UCERF1_EqkRupForecast.
          BACK_SEIS_NAME).setValue(WGCEP_UCERF1_EqkRupForecast.
                                   BACK_SEIS_EXCLUDE);

      ucerf.getAdjustableParameterList().getParameter(
          WGCEP_UCERF1_EqkRupForecast.BACK_SEIS_RUP_NAME).
          setValue(WGCEP_UCERF1_EqkRupForecast.BACK_SEIS_RUP_POINT);

      ucerf.getAdjustableParameterList().getParameter(
          WGCEP_UCERF1_EqkRupForecast.FAULT_MODEL_NAME).setValue(
              WGCEP_UCERF1_EqkRupForecast.FAULT_MODEL_STIRLING);
      ucerf.getAdjustableParameterList().getParameter(
          WGCEP_UCERF1_EqkRupForecast.RUP_OFFSET_PARAM_NAME).setValue(
              new Double(5.0));

      ucerf.getTimeSpan().setDuration(5.0);
      ucerf.updateForecast();

      generatesourceruptureinfofiles.createERF_MetadataFile(directoryPath,
          ucerf);
      generatesourceruptureinfofiles.createSourceListFile(directoryPath, ucerf);
      generatesourceruptureinfofiles.createReadMeFile(directoryPath);
    }
  }
}
