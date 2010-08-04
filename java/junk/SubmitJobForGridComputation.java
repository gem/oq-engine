package junk;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.Iterator;
import java.util.LinkedList;

import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.util.RunScript;

/**
 * <p>Title: SubmitJobForGridComputation</p>
 * <p>Description: This class will accept the filenames of the IMR, ERF,
 * GRIDDEDREGION  and it will create condor submit files and DAG needed for
 * grid computation </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta and Vipin Gupta
 * @date Mar 15, 2004
 * @version 1.0
 */

public class SubmitJobForGridComputation {

  protected final static boolean D = false;
  // parent directory on almaak.usc.edu where computations will take place
  protected final static String REMOTE_DIR = "/home/rcf-71/vgupta/pool/OpenSHA/";

  // tar file which will conatin all the hazard curves
  protected final static String OUTPUT_TAR_FILE_NAME = "outputfiles.tar";

  //tar file which contain all the submit files and Dag.
  private final static String SUBMIT_TAR_FILES = "submitfiles.tar";
  private final DecimalFormat decimalFormat = new DecimalFormat("0.00##");
  private final static int SUGGESTED_NUM_SITES_IN_WORK_UNIT = 100;

  protected final static String REMOTE_EXECUTABLE_NAME = "org.opensha.sha.calc.GridHazardMapCalculator";
  // name of the perl executable which will accept a submit file to submit to condor
  private final static String PERL_EXECUTABLE = "OpenSHA_HazardMapCalculator.pl";

  //Hazard Map Jar file using which executable will be executed
  private final static String HAZARD_MAP_JAR_FILE_NAME =
      "opensha_hazardmapcondor.jar";

  // this executable will create a new directory at the machine
  protected final static String PRE_PROCESSOR_EXECUTABLE = "HazardMapPreProcessor.sh";
  // name of condor submit file which will submit the pre processor job
  protected final static String PRE_PROCESSOR_CONDOR_SUBMIT = "preparation";
  // name of Job that will be used in DAG
  protected final static String PRE_PROCESSOR_JOB_NAME = "PREPARATION";

  // this script will be executed after all the hazard map dataset is created
  protected final static String POST_PROCESSOR_EXECUTABLE = "HazardMapPostProcessor.sh";
  // name of condor submit file which will submit the post processor job
  protected final static String POST_PROCESSOR_CONDOR_SUBMIT = "finish";
  // name of Job that will be used in DAG
  protected final static String FINISH_JOB_NAME = "FINISH";

  // files for untarring the submit files on the remote machine
  private final static String UNTAR_CONDOR_SUBMIT = "untarSubmitFiles";
  private final static String UNTAR_CONDOR_SUBMIT_EXECUTABLE= "UntarSubmit.sh";
  private final static String UNTAR_CONDOR_SUBMIT_JOB_NAME="UNTARSUBMIT";



  protected final static String DAG_FILE_NAME = "pathway1.dag";
  protected final static String LOG_FILE_NAME = "pathway1.log";
  protected final static String GET_CURVES_FROM_REMOTE_MACHINE = "getCurves.sh";
  private final static String PUT_SUBMIT_FILES_TO_REMOTE_MACHINE =
      "putSubmitFiles.sh";
  protected final static String SUBMIT_DAG_SHELL_SCRIPT_NAME = "submitDag.sh";
  private final static String PERL_JOB_NAME = "CurveX";
  private final static String PERL_CONDOR_SUBMIT = "Job";
  protected final static String HAZARD_CURVES_SUBMIT ="HazardCurves";

  //Directory names in which we store the different file types
  protected final static String SUBMIT_FILES_DIR = "submitfiles/";
  //stores all the image and map related info in this directory
  protected final static String MAP_INFO_DIR = "mapinfo/";
  protected final static String LOG_FILES_DIR = "logfiles/";
  protected final static String SCRIPT_FILES_DIR = "scriptfiles/";
  protected final static String OBJECTS_DIR = "objectfiles/";
  protected final static String DATA_DIR = "datafiles/";

  //name of the shell script that will create the move the files to their respective directories
  protected final static String FILE_MOVE_SCRIPT = "movefiles.sh";

  protected final static String DIRECTORY_PATH_FOR_SRB ="/home/sceclib.scec/development/Pathway_1/HazardMaps/";


  /**
   * class default constructor
   */
  public SubmitJobForGridComputation(){};


  /**
   *
   * @param imrFileName FileName in which IMR is saved as a serialized object
   * @param erfFileName Filename in which ERF is saved as a serialized object
   * @param regionFileName FileName in which Region is saved as a serialized object
   * @param outputDir directory where condor submit files will be created
   * @param remoteMachineSubdir subdirectory on remote machine where computations will take
   * place. So, compuatations will take place in directory /home/rcf-71/vgupta/pool/remoteMachineSubdirName
   */
  public SubmitJobForGridComputation(String imrFileName, String erfFileName,
                                     String regionFileName,
                                     String xValuesFileName,
                                     double maxDistance,
                                     String outputDir,
                                     String remoteMachineSubdirName,
                                     SitesInGriddedRegion sites,
                                     String emailAddr) {
    if (!outputDir.endsWith("/"))
      outputDir = outputDir + "/";


    //creating the directory for arranging the hazard map data files in a
    //organized manner.
    createDirectoriesForHazardMapData(outputDir);

    // some standard lines that will be written to all the condor submit files
    String remoteDir = REMOTE_DIR + remoteMachineSubdirName + "/";

    String fileDataPrefix = "universe = globus\n" +
        "globusscheduler=almaak.usc.edu/jobmanager-fork\n" +
        "initialdir=" + outputDir+SUBMIT_FILES_DIR+ "\n";
    String remoteInitDir = "remote_initialdir=" + remoteDir + "\n";
    String fileDataSuffix = "notification=error\n" +
        "transfer_executable=false\n" +
        "queue\n";

    try {
      // file in which DAG will be written
      FileWriter frmap = new FileWriter(outputDir+SUBMIT_FILES_DIR+ this.DAG_FILE_NAME);

      // this will create  a new directory for each run on the remote machine
      String condorSubmit = createCondorScript(fileDataPrefix, fileDataSuffix,
                                               remoteMachineSubdirName,
                                               outputDir,outputDir+SUBMIT_FILES_DIR,
                                               PRE_PROCESSOR_CONDOR_SUBMIT,
                                               REMOTE_DIR,
                                               PRE_PROCESSOR_EXECUTABLE);
      frmap.write("Job "+this.PRE_PROCESSOR_JOB_NAME+" " +condorSubmit+"\n");

      //creates the shell script to gridftp the condor submit files(in tar format)
      //to almaak.usc.edu
      ftpSubmitFilesToRemoteMachine(outputDir, remoteDir, imrFileName, erfFileName,
                                    regionFileName, xValuesFileName);
      frmap.write("Script Post "+PRE_PROCESSOR_JOB_NAME+" "+
                  outputDir+SCRIPT_FILES_DIR+PUT_SUBMIT_FILES_TO_REMOTE_MACHINE+"\n");

      // now make a condor script which will untar the condor submit files on remote machine
      condorSubmit = createCondorScript(fileDataPrefix, fileDataSuffix, "",
                                        outputDir,outputDir+SUBMIT_FILES_DIR, UNTAR_CONDOR_SUBMIT,
                                        remoteDir, UNTAR_CONDOR_SUBMIT_EXECUTABLE);
      frmap.write("Job " + this.UNTAR_CONDOR_SUBMIT_JOB_NAME + " " + condorSubmit + "\n");
      frmap.write("PARENT "+PRE_PROCESSOR_JOB_NAME+" CHILD "+UNTAR_CONDOR_SUBMIT_JOB_NAME+"\n");


      // a post processor which will tar all the files on remote machine after
      // all hazard map calculations are done
      condorSubmit = createCondorScript(fileDataPrefix, fileDataSuffix, remoteDir+" "+
                                        new String(DIRECTORY_PATH_FOR_SRB+remoteMachineSubdirName),
                                        outputDir,outputDir+SUBMIT_FILES_DIR, POST_PROCESSOR_CONDOR_SUBMIT,
                                        remoteDir, POST_PROCESSOR_EXECUTABLE);
      frmap.write("Job " + this.FINISH_JOB_NAME + " " + condorSubmit + "\n");


      //create shell script to ftp hazard curve tar file from remote machine
      // to local machine and then untar them on the local machine
      ftpCurvesFromRemoteMachine(outputDir, remoteDir,
                                 sites.getRegion().getNodeCount(),
                                 emailAddr,
                                 remoteMachineSubdirName);

      frmap.write("Script POST " + FINISH_JOB_NAME + " " +
                  outputDir+SCRIPT_FILES_DIR+GET_CURVES_FROM_REMOTE_MACHINE + "\n");


      // make the submit files to submit the jobs
      LinkedList list  = getSubmitFileNames(imrFileName, erfFileName,
                                     regionFileName, xValuesFileName,
                                     maxDistance,
                                     outputDir+SUBMIT_FILES_DIR, remoteDir,
                                     sites);
      Iterator it = list.iterator();
      int i=0;
      while(it.hasNext()) {
        condorSubmit = createCondorScript(fileDataPrefix, fileDataSuffix,
                                          (String) it.next(),
                                          outputDir,outputDir+SUBMIT_FILES_DIR,
                                          PERL_CONDOR_SUBMIT + "_" + i,
                                          remoteDir, PERL_EXECUTABLE);
        String jobName = PERL_JOB_NAME + i;
        frmap.write("Job " + jobName + " " + condorSubmit + "\n");
        frmap.write("PARENT " + jobName + " CHILD " + this.FINISH_JOB_NAME +
                    "\n");
        frmap.write("PARENT " + UNTAR_CONDOR_SUBMIT_JOB_NAME + " CHILD " +
                    jobName + "\n");
        ++i;
      }

      // close the DAG files
      frmap.close();

      /*FileWriter fw = new FileWriter(outputDir+FILE_MOVE_SCRIPT);
      fw.write("#!/bin/csh\n");
      fw.write("cd "+outputDir);
      fw.write("cp *.sub "+ SUBMIT_FILES_DIR);
      fw.write("cp *.dag "+ SUBMIT_FILES_DIR);
      fw.write("cp *.err "+ LOG_FILES_DIR );
      fw.write("cp *.out "+ LOG_FILES_DIR);
      fw.write("cp *.obj "+ OBJECTS_DIR);
      fw.write("cp *.sh "+ SCRIPT_FILES_DIR);
      fw.write("cp *.txt "+ METADATA_DIR);
      fw.close();
      RunScript.runScript(new String[]{"sh", "-c", "sh "+outputDir+FILE_MOVE_SCRIPT});*/

      // submit the DAG for execution
      submitDag(outputDir, remoteDir);

      //putting the information related to this hazard map in the SRB.
      //SRBDrop srb = new SRBDrop(true);
      //putting the whole eventID containing all the files to the SRB
      //srb.directoryPut(outputDir,new String(DIRECTORY_PATH_FOR_SRB+remoteMachineSubdirName),true);
      String localPathtoMetadataFile = outputDir+DATA_DIR+HazardMapCalcServlet.METADATA_FILE_NAME;
      String remotePathToMetadataFile = DIRECTORY_PATH_FOR_SRB+remoteMachineSubdirName+
                                        DATA_DIR+HazardMapCalcServlet.METADATA_FILE_NAME;
      //srb.addMDToCollection(localPathtoMetadataFile,remotePathToMetadataFile,"=");
    }
    catch (Exception ex) {
      ex.printStackTrace();
    }
  }

  /**
   *
   * This function create the directories to organise the HazardMap data files.
   * This also helps in putting these files to the SRB with a organised directory
   * structure.
   * @param outputDir : Absolute path to the directory where we new hazardMap
   * resultset directory is created.
   */
  protected void createDirectoriesForHazardMapData(String outputDir){
    //creating a directory for the submit files
    String submitFilesDir = outputDir+SUBMIT_FILES_DIR;
    new File(submitFilesDir).mkdir();

    //creating a directory to store all the mapInfo
    String mapInfoDir = outputDir+MAP_INFO_DIR;
    new File(mapInfoDir).mkdir();

    //creating a directory to store all the log files
    String logFiles = outputDir+LOG_FILES_DIR;
    new File(logFiles).mkdir();

    //creating a directory to store all the script files
    String scriptFiles = outputDir+SCRIPT_FILES_DIR;
    new File(scriptFiles).mkdir();

    //creating a directory to store all the objects files
    String objectFiles = outputDir+OBJECTS_DIR;
    new File(objectFiles).mkdir();

    //creating a directory to store all the data files
    String dataFiles = outputDir+DATA_DIR;
    new File(dataFiles).mkdir();

    /**
     * moving the obj files( that contains the serialized object)
     * to the Object files directory.Creating the script to do this.
     * This script will be deleted when the work is completed.
     */
    try{
      FileWriter fw = new FileWriter(outputDir+FILE_MOVE_SCRIPT);
      fw.write("#!/bin/csh\n");
      fw.write("cd "+outputDir+"\n");
      fw.write("mv  "+"*.obj "+" "+objectFiles+"\n");
      fw.write("cp "+"sites.txt "+dataFiles+"\n");
      fw.write("cp "+HazardMapCalcServlet.METADATA_FILE_NAME+" "+dataFiles+"\n");
      fw.close();
      RunScript.runScript(new String[]{"sh", "-c", "sh "+outputDir+FILE_MOVE_SCRIPT});
      RunScript.runScript(new String[]{"sh", "-c", "rm "+outputDir+FILE_MOVE_SCRIPT});
    }catch(IOException e){
      e.printStackTrace();
}

  }

  /**
   * Generate the submit files which will be ftped to almmak and submitted from there
   * @param imrFileName
   * @param erfFileName
   * @param regionFileName
   * @param outputDir
   * @param remoteDir
   * @param griddedSites
   * @return
   */
  protected LinkedList getSubmitFileNames(String imrFileName, String erfFileName,
                                     String regionFileName,
                                     String xValuesFileName,
                                     double maxDistance,
                                     String outputDir, String remoteDir,
                                     SitesInGriddedRegion sites) {

    int numSites = sites.getRegion().getNodeCount(); // num grid locs
    int endSite = 0;
    int startSite = 0;

    // some lines needed in the condor submit file
    String fileDataPrefix = "universe = java\n" +
       "globusscheduler=almaak.usc.edu/jobmanager-fork\n" +
       "initialdir=" + remoteDir + "\n";
    String fileDataSuffix = "jar_files = " + this.HAZARD_MAP_JAR_FILE_NAME + "\n" +
        "transfer_executable=false" + "\n" +
        "should_transfer_files=YES" + "\n" +
        "WhenToTransferOutput = ON_EXIT" + "\n" +
        "transfer_input_files=" + HAZARD_MAP_JAR_FILE_NAME+","+
        regionFileName + "," + erfFileName + "," +
        imrFileName + "," + xValuesFileName+"\n" +
        "notification=error\n"+
        "queue" + "\n";
    LinkedList list = new LinkedList();

    // snd start index and end index to each computer
    String arg2 = regionFileName+ " " + erfFileName + " " + imrFileName
        +" "+xValuesFileName+" "+maxDistance+" -Xmx400M";
    for (int site = 0; site < numSites; site += this.SUGGESTED_NUM_SITES_IN_WORK_UNIT) {
      startSite = site;
      endSite = site + SUGGESTED_NUM_SITES_IN_WORK_UNIT;

      String arguments = REMOTE_EXECUTABLE_NAME + " " + startSite+" "+endSite + " " + arg2;
      String fileNamePrefix = HAZARD_CURVES_SUBMIT + site;
      String condorSubmitScript = createCondorScript(fileDataPrefix, fileDataSuffix, arguments,
                             remoteDir,outputDir, fileNamePrefix + "_" + startSite,
                             remoteDir, "");
      list.add(condorSubmitScript);
    }

    return list;
  }

  /**
   * This method will create a condor submit script
   */
  protected String createCondorScript(String fileDataPrefix,
                                    String fileDataSuffix,
                                    String arguments, String outputDir,String submitFilesDir,
                                    String condorFileNamePrefix,
                                    String remoteDir, String executableName) {
    try {
      String fileName = condorFileNamePrefix + ".sub";
      // make the preprocessor submit script to make new directory for each run
      FileWriter fileWriter = new FileWriter(submitFilesDir + fileName);
      fileWriter.write("executable = " + executableName + "\n");
      fileWriter.write(fileDataPrefix);
      fileWriter.write("remote_initialdir=" + remoteDir + "\n");
      fileWriter.write("arguments = " + arguments + "\n");
      fileWriter.write("Output = " + outputDir+LOG_FILES_DIR+condorFileNamePrefix + "." + "out\n");
      fileWriter.write("Error = " + outputDir+LOG_FILES_DIR+condorFileNamePrefix + ".err\n");
      fileWriter.write("Log = " + outputDir+LOG_FILES_DIR+LOG_FILE_NAME + "\n");
      fileWriter.write(fileDataSuffix);
      fileWriter.close();
      return fileName;
    }
    catch (Exception e) {
      e.printStackTrace();
    }
    return null;
  }

  /**
   * creates the shell to Grid FTP the submit files to remote machine.
   *
   * @param remoteDir
   * @param outputDir
   */
  private void ftpSubmitFilesToRemoteMachine(String outputDir,
                                             String remoteDir, String imrFileName,
                                             String erfFileName,
                                             String regionFileName,
                                             String xValuesFileName) {
    try {

      //When all jobs are finished, grid ftp files from almaak to gravity
      FileWriter frFTP = new FileWriter(outputDir +SCRIPT_FILES_DIR+
                                        PUT_SUBMIT_FILES_TO_REMOTE_MACHINE);

      frFTP.write("#!/bin/csh\n");
      frFTP.write("cd " +outputDir+SUBMIT_FILES_DIR+ "\n");
      frFTP.write("tar -cf " + SUBMIT_TAR_FILES + " "+HAZARD_CURVES_SUBMIT+"*.sub \n");
      frFTP.write("mv "+SUBMIT_TAR_FILES+" "+outputDir+OBJECTS_DIR+"\n");
      frFTP.write("cd " +outputDir+OBJECTS_DIR+ "\n");
      frFTP.write("tar -uf " + SUBMIT_TAR_FILES+" "+imrFileName+" "+erfFileName+" "+
                  regionFileName+ " "+xValuesFileName+"\n");
      frFTP.write("globus-url-copy file:" + outputDir+OBJECTS_DIR +
                  SUBMIT_TAR_FILES +
                  " gsiftp://almaak.usc.edu" + remoteDir + SUBMIT_TAR_FILES +
                  "\n");
      frFTP.close();
    }
    catch (Exception e) {
      e.printStackTrace();
    }
  }

  //create shell script to ftp hazard curve tar file from remote machine
  protected void ftpCurvesFromRemoteMachine(String outputDir, String remoteDir,
                                          int expectedNumOfFiles,
                                          String emailAddr, String datasetId) {
    try {
      // write the post script.
      //When all jobs are finished, grid ftp files from almaak to gravity
      FileWriter frFTP = new FileWriter(outputDir +SCRIPT_FILES_DIR+
                                        this.GET_CURVES_FROM_REMOTE_MACHINE);
      frFTP.write("#!/bin/csh\n");
      frFTP.write("cd " + outputDir + "\n");
      frFTP.write("globus-url-copy gsiftp://almaak.usc.edu" + remoteDir +DATA_DIR+
                  OUTPUT_TAR_FILE_NAME +
                  " file:" + outputDir + OUTPUT_TAR_FILE_NAME + "\n");
      frFTP.write("tar xf " + OUTPUT_TAR_FILE_NAME + "\n");
      String fileName = outputDir + "ActualFilesLog.log";

      frFTP.write("find . -name . -o -type d -prune -o -type f -name '*_*.txt' -print0 | xargs -0 ls -l | wc -l > " + fileName + "\n");
      frFTP.write("java -classpath /opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/WEB-INF/lib/ERF.jar:/opt/install/apache-tomcat-5.5.20/webapps/OpenSHA/WEB-INF/lib/mail.jar:$CLASSPATH org.opensha.sha.gui.infoTools.HazardMapCalcPostProcessing " +
                  fileName + " " + expectedNumOfFiles + " " + emailAddr + " "+
                  datasetId+" "+
                  java.util.Calendar.getInstance().getTime().toString().replaceAll(" ","_")+"\n");
      frFTP.close();
    }
    catch (Exception e) {
      e.printStackTrace();
    }
  }

  // creates a shell script that will submit the DAG
  protected void submitDag(String outputDir, String remoteDir) {
    try {
       FileWriter fw = new FileWriter(outputDir+SUBMIT_FILES_DIR+this.SUBMIT_DAG_SHELL_SCRIPT_NAME);
       fw.write("#!/bin/csh\n");
       fw.write("cd "+outputDir+SUBMIT_FILES_DIR+"\n");
       fw.write("chmod +x "+outputDir+SCRIPT_FILES_DIR+GET_CURVES_FROM_REMOTE_MACHINE+"\n");
       fw.write("chmod +x "+outputDir+SCRIPT_FILES_DIR+PUT_SUBMIT_FILES_TO_REMOTE_MACHINE+"\n");
       fw.write("condor_submit_dag "+DAG_FILE_NAME+"\n");
       fw.close();
       RunScript.runScript(new String[]{"sh", "-c", "sh "+outputDir+SUBMIT_FILES_DIR+SUBMIT_DAG_SHELL_SCRIPT_NAME});
    }
    catch (Exception e) {
      e.printStackTrace();
    }
  }

}
