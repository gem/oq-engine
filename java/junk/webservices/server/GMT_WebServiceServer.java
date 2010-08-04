package junk.webservices.server;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;

import javax.activation.DataHandler;

import junk.webservices.GMT_WebServiceAPI;

import org.opensha.commons.util.RunScript;

/**
 * <p>Title: </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class GMT_WebServiceServer implements GMT_WebServiceAPI{

  private final static String FILE_PATH="/opt/install/apache-tomcat-5.5.20/webapps/gmtWS/";
  private final static String GMT_DATA_DIR ="gmtData/" ;
  //private final static String DATA_PATH ="/usr/scec/data/gmt/";
  private final static String GMT_SCRIPT_FILE = "temp_gmtScript.txt";
  public GMT_WebServiceServer() {
  }

  public String runGMT_Script(String[] fileName , DataHandler[] dh) throws java.rmi.RemoteException{
    //string that decides the name of the output gmt files
    String outFile = null;
    //gets the current time in milliseconds to be the new director for each user
    String currentMilliSec ="";
    currentMilliSec += System.currentTimeMillis();

    //Assuming that first file that we add is the GMT Script file and rest are the data file if any.
    try{
      //Name of the directory in which we are storing all the gmt data for the user
      String newDir= null;
      //all the user gmt stuff will be stored in this directory
      File mainDir = new File(FILE_PATH+GMT_DATA_DIR);
      //create the main directory if it does not exist already
      if(!mainDir.isDirectory()){
        boolean success = (new File(FILE_PATH+GMT_DATA_DIR)).mkdir();
      }
      newDir = FILE_PATH+GMT_DATA_DIR+currentMilliSec;
      //create a gmt directory for each user in which all his gmt files will be stored
      boolean success =(new File(newDir)).mkdir();

      //writing the GMT file to the server
      FileOutputStream fout = new FileOutputStream(newDir+"/"+fileName[0]);
      dh[0].writeTo(fout);
      fout.close();

      //reading the gmtScript file that user sent as the attachment and create
      //a new gmt script inside the directory created for the user.
      //The new gmt script file created also has one minor modification
      //at the top of the gmt script file I am adding the "cd ... " command so
      //that it should pick all the gmt related files from the directory cretade for the user.
      //reading the gmt script file sent by user as te attchment

      String gmtScriptFile = newDir+"/"+this.GMT_SCRIPT_FILE;
      //creating a new gmt script for the user and writing it ot the directory created for the user
      FileWriter fw = new FileWriter(gmtScriptFile);
      BufferedWriter bw = new BufferedWriter(fw);
      bw.write("cd "+newDir+"/"+"\n");
      bw.write("chmod 777 "+fileName[0]+"\n");
      bw.write(fileName[0]+"\n");
      bw.close();
      fw.close();
      //writing the XYZ dataSet file to the disk
      //dh[1].writeTo(new FileOutputStream(newDir+"/"+fileName[1]));


      //writing the rest of the data files including the xyz file (if any) to the disk
      for(int i=1;i<fileName.length;++i){
        FileOutputStream fout_dataFile = new FileOutputStream(newDir+"/"+fileName[i]);
        dh[i].writeTo(fout_dataFile);
        fout_dataFile.close();
      }

      //running the gmtScript file
      String[] command ={"sh","-c","sh "+gmtScriptFile};
      RunScript.runScript(command);
      //name of the outputfiles
      //outFile = fileName[1].substring(0,fileName[1].indexOf("."));
      // remove the temporary files created
      command[2]="rm "+gmtScriptFile;
      RunScript.runScript(command);
      /*command[2]="rm temp"+outFile+".grd";
      RunScript.runScript(command);
      command[2]="rm temp_temp"+outFile+".grd_info";
      RunScript.runScript(command);
      command[2]="rm "+outFile+".cpt";
      RunScript.runScript(command);*/
    }catch(Exception e){
      e.printStackTrace();
    }
    //return the full path of the output JPEG file
    return "http://gravity.usc.edu/gmtWS/"+this.GMT_DATA_DIR+currentMilliSec+"/";
  }
}
