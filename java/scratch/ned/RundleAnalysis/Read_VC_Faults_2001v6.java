package scratch.ned.RundleAnalysis;


import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.util.FileUtils;

/**
 * <p>Title: Read_VC_Faults_2001v6</p>
 *
 * <p>Description: This class reads the VC_Faults_2001v6.d file and extract the
 * segment info. It extracts info from Col 3,4,5,6 and 7. These columns give the
 * following info :</p>
 * <p>
 * <ul>
 * <li> seg_x_west - col3
 * <li> seg_y_west - col4
 * <li> seg_x_east - col 5
 * <li> seg_y_east - col 6
 * <li> seg_slipRate - col 7
 * </ul>
 * </p>
 *
 * @author Edward (Ned) Field
 * @version 1.0
 */
public class Read_VC_Faults_2001v6 {

  private double seg_x_west[];
  private double seg_y_west[];
  private double seg_x_east[];
  private double seg_y_east[];
  private double seg_slipRate[];
  private int numElements;
  private String inputFileName = "scratchJavaDevelopers/ned/RundleAnalysis/RundleVC_data/VC_FAULTS_2001v6.d";



  public Read_VC_Faults_2001v6() {
    try {
      //reading the file
      getSegmentInfoFromFile();
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



  private void getSegmentInfoFromFile() throws FileNotFoundException,
      IOException {
    //reading the all lines in the file seperately as strings
    ArrayList fileLines = FileUtils.loadFile(inputFileName);
    String firstLine = (String)fileLines.get(0);
    //reading the first line to extract number of elements (currently 650)
    StringTokenizer st = new StringTokenizer(firstLine);
    numElements = Integer.parseInt(st.nextToken().trim());
    //initializing the array size with number of elements
    seg_x_west = new double[numElements];
    seg_y_west = new double[numElements];
    seg_x_east = new double[numElements];
    seg_y_east = new double[numElements];
    seg_slipRate = new double[numElements];

    //starting the index from 1 as first line in file has to be skipped
    for(int i=1;i<=numElements;++i){
      String fileLine = (String)fileLines.get(i);
      st = new StringTokenizer(fileLine);

      //going over each line and extracting the segment info.
      //skipping the first 2 tokens in files as don't need those.
      String token = st.nextToken();
      token = st.nextToken();
      seg_x_west[i - 1] = Double.parseDouble(st.nextToken().trim());
      seg_y_west[i - 1] = Double.parseDouble(st.nextToken().trim());
      seg_x_east[i - 1] = Double.parseDouble(st.nextToken().trim());
      seg_y_east[i - 1] = Double.parseDouble(st.nextToken().trim());
      seg_slipRate[i - 1] = Double.parseDouble(st.nextToken().trim());

    }
  }


  /**
   * Returns ArrayList that contains the 5 double[] .
   * Following is the list of contents returned by it ( in order):
   * 1) double [] for seg _x_west
   * 2) double [] for seg_y_west
   * 3) double [] for seg_x_east
   * 4) double [] for seg_y_east
   * 5) double [] for seg_slipRate
   * @return ArrayList
   */
  public ArrayList getAllSegmentInfo(){

    ArrayList segmentList = new ArrayList();
    segmentList.add(seg_x_west);
    segmentList.add(seg_y_west);
    segmentList.add(seg_x_east);
    segmentList.add(seg_y_west);
    segmentList.add(seg_slipRate);

    return segmentList;
  }

  public double[] getSeg_x_west() { return seg_x_west;}
  public double[] getSeg_y_west() { return seg_y_west;}
  public double[] getSeg_x_east() { return seg_x_east;}
  public double[] getSeg_y_east() { return seg_y_east;}
  public double[] getSeg_slipRate() { return seg_slipRate;}



  // this tests the file
  public static void main(String[] args) {
    Read_VC_Faults_2001v6 read_vc_faults_2001v6 = new Read_VC_Faults_2001v6();

    //getting the segments info
    //returns ArrayList that contain the double arrays ( please refer the function
    //documentation to follow the correct order of elements in ArrayList)
    ArrayList segList = read_vc_faults_2001v6.getAllSegmentInfo();
    int size = segList.size();

    for (int j = 0; j < size; ++j) {
      double[] seg_dir = (double[])segList.get(j);
      for (int i = 0; i < seg_dir.length; ++i)
        System.out.println(seg_dir[i]);
      System.out.println("\n\n\n "+(j+1)+" done ");
    }
  }
}
