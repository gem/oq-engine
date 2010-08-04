package scratch.vipin;

import java.io.FileWriter;
import java.util.ArrayList;

/**
 * <p>Title: MergeRupturesFromMultiProcessor.java </p>
 * <p>Description: When each section is processed on a different processor,
 * we get multiple rupture files. These rupture files may have duplicate ruptures.
 * This program reads each file and then creates one common rupture file
 * which does not have any duplicates. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class MergeRupturesFromMultiProcessor {
  private String ruptureFilePrefix, outputFilename;
  private int startIndex, endIndex;
  private final static String STATUS_FILE_NAME = "MergeStatus.txt";

  public MergeRupturesFromMultiProcessor() {
  }


  public void doMerge() {
    ArrayList masterRuptureList = new ArrayList();
    try {
      //loop over all files
      for(int i=startIndex; i<=endIndex; ++i) {
        String rupFileName = ruptureFilePrefix+"_"+i+".txt";
        writeToStatusFile("Pocessing "+rupFileName+".......\n");
        System.out.println(rupFileName);
        RuptureFileReaderWriter rupFileReader = new RuptureFileReaderWriter(rupFileName);
        MultiSectionRupture rup = rupFileReader.getNextRupture();
        // loop over each rupture in that file
        int k=0;
        while(rup!=null) {
          //writeToStatusFile("Processing Rupture "+(++k)+"\n");
          // if it is not a duplicate rupture, add it to list
          if(!masterRuptureList.contains(rup)) masterRuptureList.add(rup);
          rup = rupFileReader.getNextRupture();
        }
        // load all the ruptures from the file
        /*ArrayList rupList = rupFileReader.loadRuptures();
        rupFileReader.close();
        for(int j=0; j<rupList.size(); ++j) {
          MultiSectionRupture rup = (MultiSectionRupture)rupList.get(j);
          if(!masterRuptureList.contains(rup)) masterRuptureList.add(rup);
        }*/

        writeToStatusFile("Num Ruptures in master list="+masterRuptureList.size()+"\n");
      }

      FileWriter fw = new FileWriter(outputFilename);
      RuptureFileReaderWriter.writeRupsToFile(fw, masterRuptureList);
      fw.close();
    }catch(Exception e) {
      e.printStackTrace();
    }
  }

  /**
   * Write to status file
   * @param s
   */
  private void writeToStatusFile(String s) {
    try {
      FileWriter statusFile = new FileWriter(STATUS_FILE_NAME, true);
      statusFile.write(s);
      statusFile.close();
    }catch(Exception e) {
      e.printStackTrace();
    }

  }
  /**
   * File prefix for the files to be read
   *
   * @param rupFilePrefix
   */
  public void setRupFilePrefix(String rupFilePrefix) {
    this.ruptureFilePrefix = rupFilePrefix;
  }

  /**
   * File numbers range for which merge needs to be done
   *
   * @param startIndex
   * @param endIndex
   */
  public void setSectionRange(int startIndex, int endIndex) {
    this.startIndex = startIndex;
    this.endIndex = endIndex;
  }

  /**
   * Name of the output file to be generated
   *
   * @param outFilename
   */
  public void setOutFilename(String outFilename) {
    this.outputFilename=outFilename;
  }

  /**
   * It accepts following command line arguments
   * 1. Rupture files prefix
   * 2. starting index of file
   * 3. End index of file
   * 4. Name of resultant output file
   *
   * @param args
   */
  public static void main(String[] args) {
    MergeRupturesFromMultiProcessor mergeRupturesFromMultiProcessor =
        new MergeRupturesFromMultiProcessor();
    mergeRupturesFromMultiProcessor.setRupFilePrefix(args[0]);
    mergeRupturesFromMultiProcessor.setSectionRange(Integer.parseInt(args[1]),
        Integer.parseInt(args[2]));
    mergeRupturesFromMultiProcessor.setOutFilename(args[3]);
    mergeRupturesFromMultiProcessor.doMerge();
  }

}