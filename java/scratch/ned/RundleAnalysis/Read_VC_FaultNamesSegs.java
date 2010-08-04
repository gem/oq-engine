package scratch.ned.RundleAnalysis;


import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: Read_VC_FaultNamesSegs</p>
 *
 * <p>Description: This class reads the faultNames-Segments.txt and gives arrays
 * of fault names and the index of the first and last segments on the fault
 * </p>
 *
 * @author Edward (Ned) Field
 * @version 1.0
 */
public class Read_VC_FaultNamesSegs {

  private String faultNames[];
  private int firstIndex[], lastIndex[];
  private String inputFileName = "scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/faultNames-Segments.txt";


  public Read_VC_FaultNamesSegs() {
    try {
      //reading the file
      readFromFile();
    }
    catch (FileNotFoundException ex) {
      ex.printStackTrace();
      System.exit(0);
    }
    catch (IOException ex) {
      ex.printStackTrace();
      System.exit(0);
    }
  }


  private void readFromFile() throws FileNotFoundException, IOException {

    //reading the all lines in the file seperately as strings
    ArrayList fileLines = FileUtils.loadFile(inputFileName);
    StringTokenizer st;
    int numElements = fileLines.size();
//    System.out.println(fileLines.size());
    //initializing the array size with number of elements
    firstIndex = new int[numElements];
    lastIndex = new int[numElements];
    faultNames = new String[numElements];

    //starting the index from 1 as first line in file has to be skipped
    for(int i=0; i<numElements; ++i){
      st = new StringTokenizer((String)fileLines.get(i));
      faultNames[i] = st.nextToken().trim();
      firstIndex[i] = Integer.parseInt(st.nextToken().trim());
      lastIndex[i]  = Integer.parseInt(st.nextToken().trim());
    }
//    int num = firstIndex.length;
//    for (int j = 0; j < num; ++j)
//        System.out.println(j+"   "+firstIndex[j]);

  }



  public String[] getFaultNames() { return faultNames; }

  public int[] getFirstIndex() { return firstIndex; }

  public int[] getLastIndex() { return lastIndex; }



  public static void main(String[] args) {

    Read_VC_FaultNamesSegs read_VC_FaultNamesSegs = new Read_VC_FaultNamesSegs();

    String names[] = read_VC_FaultNamesSegs.getFaultNames();
    int first[] = read_VC_FaultNamesSegs.getFirstIndex();
    int last[] = read_VC_FaultNamesSegs.getLastIndex();

    int num = first.length;
    for (int j = 0; j < num; ++j) {
        System.out.println(j+"   "+names[j]+"   "+first[j]+"  "+last[j]);
    }
  }
}
