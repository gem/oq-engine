package scratch.vipin;

import java.io.FileWriter;
import java.util.HashMap;
import java.util.Iterator;

/**
 * <p>Title: CreateScriptsForMultiProcessor.java </p>
 * <p>Description: Create scripts to submit to multiple processors </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class CreateScriptsForMultiProcessor {
  private String rupFilePrefix, sectionFile, pbsScriptsPrefix;
  private String masterScriptFilename;
  private String faultSectionFilename1, faultSectionFilename2, faultSectionFilename3;

  public CreateScriptsForMultiProcessor() {}

  /**
   * Create pbs scripts and master script to submit the pbs scripts
   */
  public void createScripts() {

    try {
      FileWriter fwMasterScript = new FileWriter(masterScriptFilename);
      int numSections = getNumberOfSections();
      for (int i = 1; i <= numSections; ++i) {
        String pbsFileName = pbsScriptsPrefix + "_" + i +".pbs";
        writeToPbsFile(pbsFileName, i);
        fwMasterScript.write("chmod +x "+pbsFileName+"\n");
        fwMasterScript.write("qsub "+pbsFileName+"\n");
      }
      fwMasterScript.close();
    }catch(Exception e){
      e.printStackTrace();
    }
  }

  /**
   * Write Pbs script for each section
   * @param filename
   * @param sectionIndex
   */
  private void writeToPbsFile(String filename, int sectionIndex) {
    String rupFileName = rupFilePrefix+"_"+sectionIndex+".txt";
    boolean writeSectionFile = false;
    // write section file only once
    if(sectionIndex==1) writeSectionFile = true;
    try {
      FileWriter fw = new FileWriter(filename);
      fw.write("#!/bin/csh\n");
      fw.write("#PBS -l walltime=1:00:00,nodes=1:ppn=2\n");
      fw.write("cd $PBS_O_WORKDIR\n");
      fw.write(
          "java -classpath RupCalc.jar scratchJavaDevelopers.vipin.PrepareTreeStructure " +
          rupFileName + " " + this.sectionFile + " " + writeSectionFile + " " +
          sectionIndex + " " + faultSectionFilename1 + " " +
          faultSectionFilename2 + " " + faultSectionFilename3 + "\n");
      fw.close();
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * Get the number of fault sections that need to be processed
   * @return
   */
  private int getNumberOfSections() {
    FaultSections faultSections = new FaultSections(faultSectionFilename1, faultSectionFilename2, faultSectionFilename3);
    HashMap faultTraceMapping = faultSections.getAllFaultSections(); // get all the fault sections
    int numSections=0;
    Iterator it = faultTraceMapping.keySet().iterator();
    while(it.hasNext()) {
      ++numSections;
      it.next();
    }
    return numSections;
  }

  /**
   * Filenames to read fault sections
   *
   * @param faultSectionFilename1
   * @param faultSectionFilename2
   * @param faultSectionFilename3
   */
  public void setFaultSectionFilename1(String faultSectionFilename1,
                                       String faultSectionFilename2,
                                       String faultSectionFilename3) {
    this.faultSectionFilename1 = faultSectionFilename1;
    this.faultSectionFilename2 = faultSectionFilename2;
    this.faultSectionFilename3 = faultSectionFilename3;
  }

  /**
   *  Filename for master shell script
   * @param masterScriptFilename
   */
   public void setMasterScriptFilename(String masterScriptFilename) {
     this.masterScriptFilename = masterScriptFilename;
   }

   /**
    * Rupture files prefix
    * @param rupFilePrefix
    */
   public void setRupFilePrefix(String rupFilePrefix) {
     this.rupFilePrefix = rupFilePrefix;
   }

   /**
    * Fault Sections
    * @param sectionFilePrefix
    */
   public void setSectionFileName(String sectionFile) {
     this.sectionFile = sectionFile;
   }

   /**
    * Prefix for pbs scripts for each section
    *
    * @param shellScriptsPrefix
    */
   public void setPbsScriptsPrefix(String shellScriptsPrefix) {
     this.pbsScriptsPrefix = shellScriptsPrefix;
   }



  /**
   * It either accepts 7 arguments or no arguments at all.
   * If 7 arguments are provided :
   * 1. Prefix for Rupture output file
   * 2. Sections output file
   * 3. Prefix for pbs scripts file names
   * 4. Name for master shell script
   * 5. Filename1 for fault section
   * 6. Filename2 for fault section
   * 7. Filename3 for fault section
   * @param args
   */

  public static void main(String[] args) {
    CreateScriptsForMultiProcessor createScriptsForMultiProcessor =
        new CreateScriptsForMultiProcessor();
    createScriptsForMultiProcessor.setRupFilePrefix(args[0]);
    createScriptsForMultiProcessor.setSectionFileName(args[1]);
    createScriptsForMultiProcessor.setPbsScriptsPrefix(args[2]);
    createScriptsForMultiProcessor.setMasterScriptFilename(args[3]);
    createScriptsForMultiProcessor.setFaultSectionFilename1(args[4], args[5], args[6]);
    createScriptsForMultiProcessor.createScripts();
  }

}