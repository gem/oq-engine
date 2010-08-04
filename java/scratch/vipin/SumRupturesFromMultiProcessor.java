package scratch.vipin;

import java.io.BufferedReader;
import java.io.FileReader;

/**
 * <p>Title: SumRupturesFromMultiProcessor.java </p>
 * <p>Description: When each section is processed on a different processor,
 * we get multiple rupture files. Each rupture file has number of ruptures
 * as the first line of file. This program reads all files and sums the number
 * of ruptures to find the grand total.
 * </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class SumRupturesFromMultiProcessor {
  private String ruptureFilePrefix;
  private int startIndex, endIndex;

  public SumRupturesFromMultiProcessor() {
  }


  public void calculateTotalRuptures() {
    try {
      int total = 0;
      //loop over all files
      for(int i=startIndex; i<=endIndex; ++i) {
        String rupFileName = ruptureFilePrefix+"_"+i+".txt";
        FileReader fr = new FileReader(rupFileName);
        BufferedReader br = new BufferedReader(fr);
        String line = br.readLine();
        int index = line.indexOf("=");
        total+=Integer.parseInt(line.substring(index+1).trim());
        br.close();
        fr.close();
      }
      System.out.println("Toal Ruptures="+total);
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
   * It accepts following command line arguments
   * 1. Rupture files prefix
   * 2. starting index of file
   * 3. End index of file
   *
   * @param args
   */
  public static void main(String[] args) {
    SumRupturesFromMultiProcessor sumRupturesFromMultiProcessor =
        new SumRupturesFromMultiProcessor();
    sumRupturesFromMultiProcessor.setRupFilePrefix(args[0]);
    sumRupturesFromMultiProcessor.setSectionRange(Integer.parseInt(args[1]),
        Integer.parseInt(args[2]));
    sumRupturesFromMultiProcessor.calculateTotalRuptures();
  }

}
