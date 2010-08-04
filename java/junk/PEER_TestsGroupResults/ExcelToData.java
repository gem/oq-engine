package junk.PEER_TestsGroupResults;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.StringTokenizer;
/**
 * <p>Title: ExcelToData</p>
 * <p>Description: This class aceepts the name of a text file and converts it
 * into the data format used by us</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Nitin Gupta & Vipin Gupta
 * @version 1.0
 */

public class ExcelToData {

  private static boolean D = true;
  private static String TEST_CASE10 = "Set1-Case10";
  private static String TEST_CASE11 = "Set1-Case11";

  /**
   * this will accept the directory conatining the input file names as command line argument
   * Also it will accept the path to create the output files
   * @param args : It will conatain the name of input file name
   * It will also acceot the path where to create the output files.
   * Any existing files with same name will be overwritten.
   */
  public static void main(String args[]) {

  try {
    // first comman line argument contains the inputfile name
    // second contains the output file name
    String inputFilesDir =  args[0];
    File fileDir  = new File(inputFilesDir);
    String fileList[] = fileDir.list();
    int numFilesinDir = fileList.length;

    FileWriter logFileWriter = new FileWriter("GroupTestDataFiles/files.log");
    for(int i=0;i < numFilesinDir; ++i) {

      String inputFileName = inputFilesDir+fileList[i];
      String outputPath =  args[1];
      if(D) System.out.println("Input file Name:"+ inputFileName);

      // get the test case number and the file identifier
      int index=inputFileName.indexOf("_");
      String testCase = inputFileName.substring(inputFileName.lastIndexOf('/')+1,index);
      String identifier = inputFileName.substring(index+1,inputFileName.lastIndexOf('.'));
      // set the nuumber of sites
      // sites are 7 except for test case 10 and 11
      int numSites = 7;
      if(testCase.equalsIgnoreCase(TEST_CASE10) || testCase.equalsIgnoreCase(TEST_CASE11))
        numSites = 4;
      if(inputFileName.indexOf("Set2")>-1) numSites = 3; // there are 3 sites in set2

      // now open the files and write to them.
      int numFiles= numSites*2;
      FileWriter [] files = new FileWriter[numFiles];

      char site = 'a'; // site identifier

      // create files
      for(int k=0;k<numFiles;)  {
        files[k]=new FileWriter(outputPath+testCase+"-"+site+"-PGA"+"_"+identifier+".dat");
        logFileWriter.write(testCase+"-"+site+"-PGA"+"_"+identifier+".dat"+"\n");
        ++k;
        files[k]=new FileWriter(outputPath+testCase+"-"+site+"-1secSA"+"_"+identifier+".dat");
        logFileWriter.write(testCase+"-"+site+"-1secSA"+"_"+identifier+".dat"+"\n");
        ++k;
        site = (char)(site+1);
      }

      // open the input file
      FileReader reader = new FileReader(inputFileName);
      BufferedReader bufReader = new BufferedReader(reader);
      // read the file
      String str = bufReader.readLine();
      while(str!=null && !str.trim().equalsIgnoreCase("")) {
        int k=0;
        StringTokenizer tokenizer = new StringTokenizer(str,"\t \n");
        // write to the files
        //if(D) System.out.println("string:"+str);
        while(tokenizer.hasMoreTokens()) {
          files[k].write(tokenizer.nextToken()+ "  ");
          files[k].write(tokenizer.nextToken());
          files[k].write("\n");
          ++k;
        }
        str = bufReader.readLine();
    }

    // close the input and output files
    for(int k=0; k<numFiles;++k)
      files[k].close();
    bufReader.close();
    reader.close();
    }
   logFileWriter.close();
  }catch(Exception e) {
    e.printStackTrace();
  }


  }

}


