package junk.PEER_TestsGroupResults;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.LineNumberReader;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.ArrayList;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


/**
 * <p>Title: PEER_InputFilesServlet </p>
 * <p>Description: This servlet is needed whenever the files are input from the
 * web using the Applet for inputting the data for PEER test cases</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta, Vipin Gupta
 * @date Dec 17 2002
 * @version 1.0
 */


public class PEER_InputFilesServlet extends HttpServlet {

  private static String JAR_PATH = "/export/home/scec-00/scecweb/jsdk2.1/webpages/";

  //Process the HTTP Get request
  public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {

    try {
       boolean  success = true;
       System.out.println("initialized to upload/delete file");
      // get an input stream from the applet
      ObjectInputStream inputFromApplet = new ObjectInputStream(request.getInputStream());

      // get whether the user has requested the addition/deletion of the file
      String functionDesired  = (String) inputFromApplet.readObject();
      // read the filename from applet
      String fileName =  (String) inputFromApplet.readObject();

      // if file is to be added
      if(functionDesired.equalsIgnoreCase("Add"))
        addFile(inputFromApplet, fileName);
      // if file is to be deleted
      else if(functionDesired.equalsIgnoreCase("Delete"))
        deleteFile(fileName);
      // if password checking functinality is desired
      else if(functionDesired.equalsIgnoreCase("Password"))
        success = checkPassword(fileName);
      // if file overwrite is ddesired
      else if(functionDesired.equalsIgnoreCase("Overwrite"))
        overwriteFile(inputFromApplet, fileName);

      // report to the user whether the operation was successful or not
      // get an ouput stream from the applet
      ObjectOutputStream outputToApplet = new ObjectOutputStream(response.getOutputStream());
      if(success) outputToApplet.writeObject(new String("Success"));
      else outputToApplet.writeObject(new String("Failure"));
      outputToApplet.close();
    } catch (Exception e) {
      // report to the user whether the operation was successful or not
      e.printStackTrace();
    }
  }


  //Process the HTTP Post request
  public void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
    // call the doPost method
    doGet(request,response);
  }

  /**
   * checks the password entered by the user
   * @param password : password to be verified
   * @return
   */
  private boolean checkPassword(String password) {
    System.out.println("Password check desired");
    if(password.equals("PEER"))
      return true;
    return false;
  }

  /**
   * to add the specified file to the jar file
   *
   * @param inputFromApplet  : Input stream from the applet
   * @param fileName : Name of the file to be added
   */
  private void addFile(ObjectInputStream inputFromApplet, String fileName) {
    try {
      System.out.println("Addition of a file desired");
      // read the data
      ArrayList data  = (ArrayList) inputFromApplet.readObject();
      inputFromApplet.close();

      // create the file
      createFile(fileName, data);

      // now update the files.log file to reflect the newly added file
      addToLogFile(fileName);

      // now update the data.version file to reflect the new data version
      updateDataVersion();

      // add this file to the JAR also
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar GroupTestDataFiles/"+fileName);
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar GroupTestDataFiles/files.log");
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar GroupTestDataFiles/data.version");
      System.out.println("::PEER_TestResultsPlotterApp.jar updated");

      // add this file to the JAR also
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsSubmApp.jar GroupTestDataFiles/"+fileName);
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsSubmApp.jar GroupTestDataFiles/files.log");
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsSubmApp.jar GroupTestDataFiles/data.version");
      System.out.println("::PEER_TestResultsSubmApp.jar updated");

      //Runtime.getRuntime().exec("rm GroupTestDataFiles/"+fileName);
    } catch(Exception e) {
      e.printStackTrace();
      return;
    }
  }

  /**
   * This function overwrites a file.
   * This is same as Add function except that it does not add to the log file
   * @param inputFromApplet
   * @param fileName
   */
  private void overwriteFile(ObjectInputStream inputFromApplet, String fileName) {
    try {
      System.out.println("Overwrite of file desired");
      // read the data
      ArrayList data  = (ArrayList) inputFromApplet.readObject();
      inputFromApplet.close();


      // create the file
      createFile(fileName, data);

      // now update the data.version file to reflect the new data version
      updateDataVersion();

      // add this file to the JAR also
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar GroupTestDataFiles/"+fileName);
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar GroupTestDataFiles/files.log");
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar GroupTestDataFiles/data.version");

      System.out.println("::PEER_TestResultsPlotterApp.jar updated");

      // add this file to the JAR also
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsSubmApp.jar GroupTestDataFiles/"+fileName);
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsSubmApp.jar GroupTestDataFiles/files.log");
      RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsSubmApp.jar GroupTestDataFiles/data.version");

      System.out.println("::PEER_TestResultsSubmApp.jar updated");

      //Runtime.getRuntime().exec("rm GroupTestDataFiles/"+fileName);
    } catch(Exception e) {
      e.printStackTrace();
      return;
    }
  }



  /**
   * create the file with name filename and values specified in ArrayList values
   * @param fileName : filename to create
   * @param data  : vector of values
   */
  private void createFile(String fileName, ArrayList data) {
    try {
      System.out.println("filename to upload:"+fileName);
      FileWriter file = new FileWriter("GroupTestDataFiles/"+fileName);
      BufferedWriter oBuf= new BufferedWriter(file);
      // now read all the points from function and put into file
      int num = data.size();
      System.out.println("num of points:"+num);
      for(int i=0;i<num;++i)
        oBuf.write(data.get(i)+"\n");
      oBuf.close();
      file.close();
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * Add the specified filename to log file
   * @param fileName : file to add to log file
   */
  private void addToLogFile(String fileName) {
   try {
     FileWriter logFile = new FileWriter("GroupTestDataFiles/files.log",true);
     logFile.write(fileName+"\n");
     logFile.close();
   }catch(Exception e) {
     e.printStackTrace();
   }
  }
  /**
   * This function updates the data version
   * this is called whenever any file is added or removed
   */
  private void updateDataVersion() {
    try{

      // first read the current version number from the file
      FileReader versionFile = new FileReader("GroupTestDataFiles/data.version");
      LineNumberReader lin = new LineNumberReader(versionFile);
      // get the current version number
      int version = Integer.parseInt(lin.readLine());
      lin.close();
      versionFile.close();

      // now update the version number in the file
      FileWriter newVersionFile = new FileWriter("GroupTestDataFiles/data.version");
      newVersionFile.write(""+(version+1)+"\n"); // write the new version
      newVersionFile.write(""+new java.util.Date().toString()); // write the current updated time
      newVersionFile.close();

    }catch (Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * to delete the specified filename
   * @param fileName
   */
  private void deleteFile(String fileName) {
   try {
     System.out.println("Deletion of a file desired");
     // now update the files.log file to reflect the removed file
     FileReader logFile = new FileReader("GroupTestDataFiles/files.log");
     LineNumberReader lin = new LineNumberReader(logFile);
     ArrayList fileNamesVector = new ArrayList();
     String str = lin.readLine();
     while(str!=null) {
       if(!str.equals(fileName)) fileNamesVector.add(str);
       str = lin.readLine();
     }
     lin.close();
     logFile.close();


     // remove this file from the GUI Plotter JAR also
     RunScript.runScript("jar xf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar org/");
      RunScript.runScript("jar xf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar com/");
       RunScript.runScript("jar xf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar META-INF/");
        RunScript.runScript("jar xf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar img/");
     // rewrite the log file after removing the name of the removed file
     FileWriter newLogFile = new FileWriter("GroupTestDataFiles/files.log");
     int size = fileNamesVector.size();
     for(int i =0; i< size; ++i)
       newLogFile.write((String)fileNamesVector.get(i)+"\n");
     newLogFile.close();
     // update the version in the version file
     this.updateDataVersion();

     RunScript.runScript("rm  GroupTestDataFiles/"+fileName);
     RunScript.runScript("rm "+JAR_PATH+"PEER_TestResultsPlotterApp.jar");
     RunScript.runScript("jar cfm "+JAR_PATH+"PEER_TestResultsPlotterApp.jar "+
                                    "META-INF/MANIFEST.MF org/");
     RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar "+
                                   "com/");
     RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar "+
                                   "GroupTestDataFiles/");
     RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsPlotterApp.jar "+
                                   "img/");
     // remove the files created by the above
     RunScript.runScript("rm -rf com/");
     RunScript.runScript("rm -rf org/");
     RunScript.runScript("rm -rf META-INF/");
     //RunScript.runScript("rm -rf img/");
     /*for(int i =0; i< size; ++i)
       RunScript.runScript("rm GroupTestDataFiles/"+(String)fileNamesVector.get(i));
     */

     // remove this file from the Data Submission JAR also
     RunScript.runScript("jar xf "+JAR_PATH+"PEER_TestResultsSubmApp.jar org/");

     // rewrite the log file after removing the name of the removed file
     /*newLogFile = new FileWriter("GroupTestDataFiles/files.log");
     for(int i =0; i< size; ++i)
       newLogFile.write((String)fileNamesVector.get(i)+"\n");
     newLogFile.close();
     // update the version in the version file
     this.updateDataVersion();

     RunScript.runScript("rm GroupTestDataFiles/"+fileName);*/
     RunScript.runScript("rm "+JAR_PATH+"PEER_TestResultsSubmApp.jar");
     RunScript.runScript("jar cf "+JAR_PATH+"PEER_TestResultsSubmApp.jar "+
                                    "org/");
     RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsSubmApp.jar "+
                                    "GroupTestDataFiles/");
     RunScript.runScript("jar uf "+JAR_PATH+"PEER_TestResultsSubmApp.jar "+
                                    "img/");
     // remove the files created by above
     RunScript.runScript("rm -rf org/");
     RunScript.runScript("rm -rf img/");

    //for(int i =0; i< size; ++i)
     //RunScript.runScript("rm GroupTestDataFiles/"+(String)fileNamesVector.get(i));

    //RunScript.runScript("rm -rf GroupTestDataFiles/*.dat");
    System.out.println("::PEER_TestResultsPlotterApp.jar updated after file deletion");
    System.out.println("::PEER_TestResultsSubmApp.jar updated after file deletion");
   } catch(Exception e) {
     e.printStackTrace();
   }
  }
}




/**
 * <p>Title: RunScript</p>
 * <p>Description : Accepts the command and runs the shell script
 * @author: Nitin Gupta and Vipin Gupta
 * @created:Dec 27, 2002
 * @version 1.0
 */

class RunScript {

  private static Runtime runtime = null;
  /**
   * accepts the command and executes on java runtime environment
   *
   * @param command : command to execute
   */
  public static void runScript(String command) {

    if(runtime==null) runtime = Runtime.getRuntime();

    try {
      // wait for the shell script to end
      System.out.println("Command to execute: " +command);
      Process p=runtime.exec(command);
      p.waitFor();
      int i=p.exitValue();

      // check the process status after the process ends
      if ( i == 0 ) {
        // Display the normal o/p if script completed successfully.
        System.out.println("script exited with i =" + i);
       displayOutput(p.getInputStream());
      }
      else {
        // Display the normal and error o/p if script failed.
       System.out.println("script exited with i =" + i);
       displayOutput(p.getErrorStream());
       displayOutput(p.getInputStream());
      }
    } catch(Exception e) {
      // if there is some other exception, print the detailed explanation
      System.out.println("Exception in Executing Shell Script:"+e);
      e.printStackTrace();
    }
  }


  /**
   * display the input stream
   * @param is inputstream
   * @throws Exception
   */
  public static void displayOutput(InputStream is) throws Exception {
    String s;
    try {
      BufferedReader br = new BufferedReader(new InputStreamReader(is));
      while ((s = br.readLine()) != null)
        System.out.println(s);
    } catch (Exception e) {
      System.out.println("Exception in RunCoreCode:displayOutput:"+e);
      e.printStackTrace();
    }
  }

}
