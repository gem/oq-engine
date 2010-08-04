package junk;

import java.io.FileWriter;

import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.util.FileUtils;
import org.opensha.commons.util.RunScript;

/**
 * <p>Title: SubmitJobForMultiprocessorComputation</p>
 * <p>Description: This creates the script to submit the job on the multiprocessor
 * machine. It submits the job on the multi-processor shared memory using the PBS
 * script.</p>
 * @author : Nitin Gupta , Vipin Gupta
 * @created : May 03, 2004
 * @version 1.0
 */

public class SubmitJobForMultiprocessorComputation extends SubmitJobForGridComputation {

  private final static boolean D = false;

  //number of processors requested to run this job
  public final static int NUM_OF_PROCESSORS_AVAILABLE = 8;

  //maximum wall time that we are requesting the processors for (in minutes)
  public final static double MAX_WALL_TIME =180;

  // parent directory on almaak.usc.edu where computations will take place
  protected final static String REMOTE_DIR = "/home/rcf-71/vgupta/pool/OpenSHA/threadCalc/";

  private final static String REMOTE_EXECUTABLE_NAME = "MapCalcUsingMultiprocessor.sh";

  // this executable will create a new directory at the machine
  private final static String PRE_PROCESSOR_EXECUTABLE = "HazardMapThreadPreProcessor.sh";


  //tar file which contain all the object files and Dag.
  private final static String OBJECT_TAR_FILES = "objectfiles.tar";

  private final static String HAZARD_MAP_JOB_NAME = "HAZARD_MAP_MULTIPROCESSOR_JOB";

  private final static String PUT_OBJECT_FILES_TO_REMOTE_MACHINE = "putObjects.sh";


  // files for untarring the object files on the remote machine
  private final static String UNTAR_OBJECT_FILES = "untarObjectFiles";
  private final static String UNTAR_OBJECT_EXECUTABLE= "UntarObjectFiles.sh";
  private final static String UNTAR_OBJECT_JOB_NAME="UNTAROBJECT";



  /**
   *
   * @param imrFileName FileName in which IMR is saved as a serialized object
   * @param erfFileName Filename in which ERF is saved as a serialized object
   * @param regionFileName FileName in which Region is saved as a serialized object
   * @param outputDir directory where condor submit files will be created
   * @param remoteMachineSubdir subdirectory on remote machine where computations will take
   * place. So, compuatations will take place in directory /home/rcf-71/vgupta/pool/remoteMachineSubdirName
   */
  public SubmitJobForMultiprocessorComputation(String imrFileName, String erfFileName,
                                     String regionFileName,
                                     String xValuesFileName,
                                     double maxDistance,
                                     String outputDir,
                                     String remoteMachineSubdirName,
                                     String emailAddr) {
    if (!outputDir.endsWith("/"))
      outputDir = outputDir + "/";

    SitesInGriddedRegion sites = (SitesInGriddedRegion)FileUtils.loadObject(outputDir+regionFileName);

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

      //creates the shell script to gridftp the object files(in tar format)
      //to almaak.usc.edu
      ftpObjectFilesToRemoteMachine(outputDir, remoteDir, imrFileName, erfFileName,
                                    regionFileName, xValuesFileName);
      frmap.write("Script Post "+PRE_PROCESSOR_JOB_NAME+" "+
                  outputDir+SCRIPT_FILES_DIR+PUT_OBJECT_FILES_TO_REMOTE_MACHINE+"\n");

      // now make a condor script which will untar the object files on remote machine
      condorSubmit = createCondorScript(fileDataPrefix, fileDataSuffix, "",
                                        outputDir,outputDir+SUBMIT_FILES_DIR, UNTAR_OBJECT_FILES,
                                        remoteDir, UNTAR_OBJECT_EXECUTABLE);
      frmap.write("Job " + UNTAR_OBJECT_JOB_NAME + " " + condorSubmit + "\n");
      frmap.write("PARENT "+PRE_PROCESSOR_JOB_NAME+" CHILD "+UNTAR_OBJECT_JOB_NAME+"\n");

      // make the submit files to submit the jobs
      condorSubmit = getSubmitFileName(imrFileName, erfFileName,
                                       regionFileName, xValuesFileName,
                                       maxDistance,outputDir+SUBMIT_FILES_DIR,
                                       remoteDir, outputDir);

      frmap.write("Job " + HAZARD_MAP_JOB_NAME + " " + condorSubmit + "\n");

      frmap.write("PARENT "+UNTAR_OBJECT_JOB_NAME+" CHILD "+HAZARD_MAP_JOB_NAME+"\n");


      // a post processor which will tar all the files on remote machine after
      // all hazard map calculations are done
      condorSubmit = createCondorScript(fileDataPrefix, fileDataSuffix, remoteDir+" "+
                                        new String(DIRECTORY_PATH_FOR_SRB+remoteMachineSubdirName),
                                        outputDir,outputDir+SUBMIT_FILES_DIR, POST_PROCESSOR_CONDOR_SUBMIT,
                                        remoteDir, POST_PROCESSOR_EXECUTABLE);
      frmap.write("Job " + this.FINISH_JOB_NAME + " " + condorSubmit + "\n");
      frmap.write("PARENT " + HAZARD_MAP_JOB_NAME + " CHILD " + this.FINISH_JOB_NAME +
                  "\n");

      //create shell script to ftp hazard curve tar file from remote machine
      // to local machine and then untar them on the local machine
      ftpCurvesFromRemoteMachine(outputDir, remoteDir,
                                 sites.getRegion().getNodeCount(),
                                 emailAddr,
                                 remoteMachineSubdirName);

      frmap.write("Script POST " + FINISH_JOB_NAME + " " +
                  outputDir+SCRIPT_FILES_DIR+GET_CURVES_FROM_REMOTE_MACHINE + "\n");


      // close the DAG files
      frmap.close();

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
   * Generate the submit files which will be ftped to almmak and submitted from there
   * @param imrFileName
   * @param erfFileName
   * @param regionFileName
   * @param outputDir
   * @param remoteDir
   * @param griddedSites
   * @return
   */
  protected String getSubmitFileName(String imrFileName, String erfFileName,
                                     String regionFileName,
                                     String xValuesFileName,
                                     double maxDistance,
                                     String submitFilesDir, String remoteDir,
                                     String outputDir) {


    // some lines needed in the condor submit file
    String fileDataPrefix = "universe = globus\n" +
                            "globusscheduler=almaak.usc.edu/jobmanager-pbs\n" +
                            "initialdir=" + outputDir + "\n"+
                            "globusrsl = (count="+NUM_OF_PROCESSORS_AVAILABLE+") (hostcount=1) "+
                            " (max_wall_time="+MAX_WALL_TIME+")"+"\n";

    String fileDataSuffix ="WhenToTransferOutput = ON_EXIT" + "\n" +
                           "notification=error\n"+
                           "queue" + "\n";

    String arguments = imrFileName+" "+regionFileName + " " + erfFileName+" "+
                       xValuesFileName+" "+maxDistance+" "+NUM_OF_PROCESSORS_AVAILABLE;
    return createCondorScript(fileDataPrefix, fileDataSuffix,
                              arguments,
                              outputDir, submitFilesDir, HAZARD_CURVES_SUBMIT,
                              remoteDir, REMOTE_EXECUTABLE_NAME);
  }



  /**
   * creates the shell to Grid FTP the objects files to remote machine.
   *
   * @param remoteDir
   * @param outputDir
   */
  private void ftpObjectFilesToRemoteMachine(String outputDir,
                                             String remoteDir, String imrFileName,
                                             String erfFileName,
                                             String regionFileName,
                                             String xValuesFileName) {
    try {

      //grid ftp object files from gravity to almaak
      FileWriter frFTP = new FileWriter(outputDir +SCRIPT_FILES_DIR+
                                        PUT_OBJECT_FILES_TO_REMOTE_MACHINE);
      frFTP.write("#!/bin/csh\n");
      frFTP.write("cd " +outputDir+OBJECTS_DIR+ "\n");
      frFTP.write("tar -cf " + OBJECT_TAR_FILES+" "+imrFileName+" "+erfFileName+" "+
                  regionFileName+ " "+xValuesFileName+"\n");
      frFTP.write("globus-url-copy file:" + outputDir+OBJECTS_DIR +
                  OBJECT_TAR_FILES +
                  " gsiftp://almaak.usc.edu" + remoteDir + OBJECT_TAR_FILES +
                  "\n");
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
      fw.write("chmod +x "+outputDir+SCRIPT_FILES_DIR+PUT_OBJECT_FILES_TO_REMOTE_MACHINE+"\n");
      fw.write("condor_submit_dag "+DAG_FILE_NAME+"\n");
      fw.close();
      RunScript.runScript(new String[]{"sh", "-c", "sh "+outputDir+SUBMIT_FILES_DIR+SUBMIT_DAG_SHELL_SCRIPT_NAME});
    }
    catch (Exception e) {
      e.printStackTrace();
    }
  }


  /**
   * It takes the following argument
   * args[0] = imrFileName
   * args[1] = erfFileName
   * args[2] = regionFileName
   * args[3] = xValuesFileName
   * args[4] = maxDistance
   * args[5] = outputDir with absolute path where the directory is to be created
   * args[6] = remoteMachineSubdirName (outoutDir without absolute path)
   * args[7] = emailAddr
   * @param args
   */
  public final static void main(String args[]){
    SubmitJobForMultiprocessorComputation submitJob =
        new SubmitJobForMultiprocessorComputation(args[0],args[1],args[2],args[3],
        Double.parseDouble(args[4]),args[5],args[6],args[7]);
  }
}
