package junk;


import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;


/**
 * <p>Title: HazardMapCalcServlet </p>
 * <p>Description: this servlet generates the data sets based on the parameters
 * set by the user in applet </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author unascribed
 * @version 1.0
 */

public class HazardMapCalcServlet extends HttpServlet {
  public final static boolean D =false;
  // parent directory where each new calculation will have its own subdirectory
  public static final String PARENT_DIR = "/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/HazardMapDatasets/";
  // filenames for IMR, ERF, Region, metadata
  private static final String IMR_FILE_NAME = "imr.obj";
  private static final String ERF_FILE_NAME = "erf.obj";
  private static final String REGION_FILE_NAME = "region.obj";
  private static final String X_VALUES_FILE_NAME = "xValues.obj";
  public  static final String METADATA_FILE_NAME = "metadata.txt";
  public  static final String SITES_FILE_NAME = "sites.txt";

  //Process the HTTP Get request
  public void doGet(HttpServletRequest request, HttpServletResponse response) throws
  ServletException, IOException {

    try {

      // get an input stream from the applet
      ObjectInputStream inputFromApplet = new ObjectInputStream(request.
          getInputStream());

      //get the sites for which this needs to be calculated
      SitesInGriddedRegion sites = (SitesInGriddedRegion) inputFromApplet.
                                   readObject();
      //get the selected IMR
      ScalarIntensityMeasureRelationshipAPI imr = (ScalarIntensityMeasureRelationshipAPI)
                                       inputFromApplet.readObject();
      //get the selected EqkRupForecast
      Object obj = inputFromApplet.readObject();
      if (D) System.out.println("obj class = "+obj.getClass());
      String  eqkRupForecastLocation = (String) obj;
      // get the X values
      ArrayList xValuesList = (ArrayList) inputFromApplet.readObject();
      // get the MAX_SOURCE distance
      double maxDistance =  ((Double) inputFromApplet.readObject()).doubleValue();

      //get the email address from the applet
      String emailAddr = (String) inputFromApplet.readObject();
      //get the parameter values in String form needed to reproduce this
      String mapParametersInfo = (String) inputFromApplet.readObject();

      //getting the dataset id, in which we want to put all his hazardmap dataset results
      String datasetId = (String)inputFromApplet.readObject();
      //new directory for Hazard map dataset
      String datasetDir = "";
      //checking if datasetId gievn by is null
      if(datasetId!=null && !datasetId.trim().equals(""))
        datasetDir = datasetId.trim();

      else{
        datasetDir = System.currentTimeMillis()+"";
      }
      //creating the dataset directory.
      File hazardMapDataset = new File(PARENT_DIR+datasetDir);
      hazardMapDataset.mkdir();

      // report to the user whether the operation was successful or not
      // get an ouput stream from the applet
      ObjectOutputStream outputToApplet = new ObjectOutputStream(response.
          getOutputStream());
      outputToApplet.writeObject("Generated Dataset with name :"+ datasetDir);
      outputToApplet.close();

      String newDir = PARENT_DIR+datasetDir+"/";
      // write X values to a file
      FileWriter fwX_Values = new FileWriter(newDir+this.X_VALUES_FILE_NAME);
      for (int i=0; i<xValuesList.size(); ++i)
        fwX_Values.write(xValuesList.get(i)+"\n");
      fwX_Values.close();

      // write the metadata to the metadata file
      FileWriter fwMetadata = new FileWriter(newDir+this.METADATA_FILE_NAME);
      fwMetadata.write(mapParametersInfo);
      fwMetadata.close();

      // write site information in sites file
      FileWriter fwSites = new FileWriter(newDir+this.SITES_FILE_NAME);
      fwSites.write(sites.getRegion().getMinLat()+" "+sites.getRegion().getMaxLat()+" "+sites.getRegion().getSpacing()+"\n");
      fwSites.write(sites.getRegion().getMinLon()+" "+sites.getRegion().getMaxLon()+" "+sites.getRegion().getSpacing()+"\n");
      fwSites.close();


      FileUtils.saveObjectInFile(newDir+this.REGION_FILE_NAME, sites);
      FileUtils.saveObjectInFile(newDir+this.IMR_FILE_NAME, imr);

      if(D) System.out.println("ERF URL="+eqkRupForecastLocation);
      //EqkRupForecast eqkRupForecast = (EqkRupForecast)FileUtils.loadObjectFromURL(eqkRupForecastLocation);
      //FileUtils.saveObjectInFile(newDir+this.ERF_FILE_NAME, eqkRupForecast);
      String getERF_FileName = "getERF.sh";
      FileWriter fw = new FileWriter(newDir+getERF_FileName);
      fw.write("#!/bin/csh\n");
      fw.write("cd "+newDir+"\n");
      fw.write("cp  "+eqkRupForecastLocation+" "+newDir+this.ERF_FILE_NAME+"\n");
      fw.close();
      org.opensha.commons.util.RunScript.runScript(new String[]{"sh", "-c", "sh "+newDir+getERF_FileName});
      org.opensha.commons.util.RunScript.runScript(new String[]{"sh", "-c", "rm "+newDir+getERF_FileName});
      if(D) System.out.println("after wget");

      // now run the calculation on grid
      new SubmitJobForGridComputation(IMR_FILE_NAME, ERF_FILE_NAME,
          REGION_FILE_NAME, X_VALUES_FILE_NAME,maxDistance, newDir, datasetDir, sites,
          emailAddr);
    }
    catch (Exception e) {
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
