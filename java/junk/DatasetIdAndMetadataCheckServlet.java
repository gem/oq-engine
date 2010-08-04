package junk;


import java.io.File;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;
import java.util.ListIterator;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.commons.util.FileUtils;


/**
 * <p>Title: DatasetIdAndMetadataCheckServlet </p>
 * <p>Description: This servlet checks if the dataset name for Hazard Map dataset
 * given by the user already exists, if so then ask him to give a new dataset name.
 * This servlet also checks if computation have already been done using the
 * current parameter settings. If so then just tell the user that these computation
 * have already  been done and give him the dataset name so that he can go and view this
 * result. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class DatasetIdAndMetadataCheckServlet extends HttpServlet {
  public final static boolean D =false;
  // parent directory where each new calculation will have its own subdirectory
  public static final String PARENT_DIR = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/HazardMapDatasets/";
  public  static final String METADATA_FILE_NAME = "metadata.txt";

  //Process the HTTP Get request
  public void doGet(HttpServletRequest request, HttpServletResponse response) throws
  ServletException, IOException {

    try {

      // get an input stream from the applet
      ObjectInputStream inputFromApplet = new ObjectInputStream(request.
          getInputStream());

      //get the parameter values in String form needed to reproduce this
      String mapParametersInfo = (String) inputFromApplet.readObject();

      //getting the dataset id, in which we want to put all his hazardmap dataset results
      String datasetId = (String)inputFromApplet.readObject();

      File mapDatasets = new File(PARENT_DIR);
      File[] datasets = mapDatasets.listFiles();
      String mapInfo = mapParametersInfo.replaceAll("\n","");

      mapInfo = mapInfo.replaceAll(" ","");

      int numDatasets = datasets.length;
      //checks if calculation have already been for these parameters settings, if so then don't do it again.
      boolean calculationAlreadyDone = false;
      //iterating over all tha datasets to check if compuation was done previously for these parameter settings.
      for(int i=0;i<numDatasets;++i){
        //only iterating over the directories
        if(datasets[i].isDirectory()){
          //reading the metadata of existing dataset to see if that metadata matches with metadata
          //for current parameter settings
          File metadataFile = new File(datasets[i].getAbsolutePath()+"/"+this.METADATA_FILE_NAME);
          //System.out.println("Metadata File path:  "+metadataFile.getAbsolutePath());
          if(metadataFile.exists()){
            //reading th existing metadata in the list
            ArrayList existingMetadataLines = FileUtils.loadFile(metadataFile.getAbsolutePath());
            ListIterator it = existingMetadataLines.listIterator();
            String existingMetadata ="";
            while(it.hasNext())
              existingMetadata +=(String)it.next();
            //replacing all \n and spaces and the comparing.
            existingMetadata = existingMetadata.replaceAll("\n","");
            existingMetadata = existingMetadata.replaceAll(" ","");
            //Now even if metadata matches, it does not mean that datafiles also exists
            //so now looking if datafiles also exists or not.
            File[] fileList = datasets[i].listFiles();

            //iterating over all the files in this dataset and looking if datafiles exists
            int numFiles= fileList.length;
            boolean dataFiles = false;
            for(int j=0;j<numFiles;++j){
              File file = fileList[j];
              if(file.isFile()){
                String fileName = file.getName();
                if(fileName.endsWith(".txt")){
                  int firstIndex = fileName.indexOf(".");
                  int lastIndex = fileName.lastIndexOf(".");
                  if(firstIndex != lastIndex){
                    dataFiles = true;
                    break;
                  }
                }
              }
            }
            if(existingMetadata.equals(mapInfo) && dataFiles){
              calculationAlreadyDone = true;
              // report to the user whether the operation was successful or not
              // get an ouput stream from the applet
              ObjectOutputStream outputToApplet = new ObjectOutputStream(response.
                  getOutputStream());
              outputToApplet.writeObject("HazardMap Calculations have already been done"+
                  " for these parameter settings. \nPlease view the results for dataset: "+datasets[i].getName());
              outputToApplet.close();
              break;
            }
          }
        }
      }
      //only does all the processing if calculation have never been done before for
      //these parameter settings.
      if(!calculationAlreadyDone){
        String newDir = "";

        //checks to make if dataset directory was created, only then do the map calculation
        //else report the problem back to the user.
        boolean dirExisted = false;
        //checking if datasetId gievn by is null
        if(datasetId!=null && !datasetId.trim().equals("")){
          newDir = datasetId.trim();

          //checking to see if directory with the same dataset name exists
          //if so then create own directory
          File hazardMapDataset = new File(PARENT_DIR+newDir);
          //creating the directory with the name provided by user
          if(hazardMapDataset.exists()){
            dirExisted = true;
            // report to the user whether the operation was successful or not
            // get an ouput stream from the applet
            ObjectOutputStream outputToApplet = new ObjectOutputStream(response.
                getOutputStream());
            outputToApplet.writeObject(new String("Dataset with "+newDir+" already exists.\n"+
                "Please give some other name"));
            outputToApplet.close();
          }
        }
        //if the dataset name does not already existed then send back to the application
        //that it is safe to create a new directory with this name.
        if(!dirExisted){
          // report to the user whether the operation was successful or not
            // get an ouput stream from the applet
            ObjectOutputStream outputToApplet = new ObjectOutputStream(response.
                getOutputStream());
            outputToApplet.writeObject(new Boolean(true));
            outputToApplet.close();
        }
      }
    }catch (Exception e) {
      // report to the user whether the operation was successful or not
      e.printStackTrace();
    }
  }



  //Process the HTTP Post request
  public void doPost(HttpServletRequest request, HttpServletResponse response) throws
      ServletException, IOException {
    // call the doPost method
    doGet(request, response);
  }

}
