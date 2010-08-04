package junk;

import java.util.ArrayList;

import org.opensha.commons.exceptions.RegionConstraintException;
import org.opensha.sha.gui.infoTools.ConnectToCVM;

/**
 * <p>Title: TestSiteTypeServlets</p>
 * <p>Description: This class checks if we are getting the correct values from the
 * sitetypes from the servlets.
 * Note: This tester class just checks for the values if we are getting the correct
 * values from the servlets and in no way checks if the algorithm we are using is correct.
 * Because that algorithm would be same to get the site type values from the file
 * hosted on the local computer or if we are getting the values from the servlet
 * hosted on a web server.</p>
 * @author : Edward (Ned) Field, Nitin Gupta and Vipin Gupta
 * @created June 1, 2004
 * @version 1.0
 */

public final class TestSiteTypeServlets {

  private double MIN_LAT = 32.5;
  private double MAX_LAT = 34.7;
  private double MIN_LON = -119.5;
  private double MAX_LON = -116.0;
  private double GRIDSPACING = .07;

  //gets the Wills site class and basin depth from the servlet(gravity.usc.edu)
  private ArrayList willsSiteClassFromServlet;
  private ArrayList basinDepthFromServlet;

  //gets the Wills site class and basin depth from the standalone file on local system.
  private ArrayList willsSiteClassFromFile;
  private ArrayList basinDepthFromFile;


  /**
   * Files get the site information from.
   */
  private static final String WILLS_SITE_CLASS_FILE = "cvmfiles/usgs_cgs_geology_60s_mod.txt";
  private static final String BASIN_DEPTH_FILE = "cvmfiles/basindepth_OpenSHA.txt";

  /**
   * Test class default constructor
   */
  public TestSiteTypeServlets() throws RegionConstraintException {
    //gets the site type values from the servlet
    getValuesForSiteTypeFromServlets();
    //gets the site type values from file
    getValuesForSiteType();
    //compare the wills site class values
    compareWillsSiteClassValues();
    //compare the basin depth values
    compareBasinDepthValues();
  }

  /**
   * main method to run the test application
   * @param args
   */
  public static void main(String[] args) {
    //TestSiteTypeServlets testSiteTypeServlets1 = new TestSiteTypeServlets();
    java.util.GregorianCalendar data = new java.util.GregorianCalendar();
    data.set(1969,11,30);
    System.out.println("Date: "+data.getTime().getTime());
  }


  /**
   * gets the Wills site and basin depth information from the site type files
   * on the local system.
   */
  public void getValuesForSiteType() throws RegionConstraintException {

    willsSiteClassFromFile = ConnectToCVM.getWillsSiteType(MIN_LON,MAX_LON,MIN_LAT,MAX_LAT,
        GRIDSPACING,WILLS_SITE_CLASS_FILE);
    basinDepthFromFile = ConnectToCVM.getBasinDepth(MIN_LON,MAX_LON,MIN_LAT,MAX_LAT,
        GRIDSPACING,BASIN_DEPTH_FILE);

  }


  /**
   * method to get the Wills site information and basin depth information from the
   * servlets hosted on gravity.usc.edu
   */
  public void getValuesForSiteTypeFromServlets(){
    try{
      willsSiteClassFromServlet = ConnectToCVM.getWillsSiteTypeFromCVM(MIN_LON,MAX_LON,MIN_LAT,MAX_LAT,
          GRIDSPACING);
      basinDepthFromServlet = ConnectToCVM.getBasinDepthFromCVM(MIN_LON,MAX_LON,MIN_LAT,MAX_LAT,
          GRIDSPACING);
    }catch(Exception e){
      System.out.println("Error connecting with servlet "+e.getMessage());
    }
  }

  /**
   * compares the values we got from the Wills site class file using the
   * servlet and other from the local system
   */
  private void compareWillsSiteClassValues(){
    int size = willsSiteClassFromServlet.size();
    int size1 = willsSiteClassFromFile.size();
    if(size !=size1){
      System.out.println("We are getting incorrect number of values for Wills Site Class from servlet");
      return;
    }
    boolean willsSiteClassCheckFlag = true;
    for(int i=0;i<size && willsSiteClassCheckFlag;++i){
      if(!((String)willsSiteClassFromServlet.get(i)).equals(((String)willsSiteClassFromFile.get(i))))
        willsSiteClassCheckFlag = false;
    }

    if(willsSiteClassCheckFlag)
      System.out.println("We are getting the correct values for the Wills site Class from servlet");
    else
      System.out.println("We are getting incorrect values for the Wills site Class from servlet");

  }

  /**
   * compares the values we got from the Basin Depth file using the
   * servlet and other from the local system.
   */
  private void compareBasinDepthValues(){
    int size = basinDepthFromServlet.size();
    int size1 = basinDepthFromFile.size();
    if(size !=size1){
      System.out.println("We are getting incorrect number of values for Basin Depth from servlet");
      return;
    }
    boolean basinDepthCheckFlag = true;
    for(int i=0;i<size && basinDepthCheckFlag;++i){
      if(!((Double)basinDepthFromServlet.get(i)).equals(((Double)basinDepthFromFile.get(i))))
        basinDepthCheckFlag = false;
    }

    if(basinDepthCheckFlag)
      System.out.println("We are getting the correct values for the Basin Depth from servlet");
    else
      System.out.println("We are getting incorrect values for the Basin Depth from servlet");
  }


}
