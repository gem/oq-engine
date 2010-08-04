package junk.nga;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.geo.LocationVector;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.FrankelGriddedSurface;
import org.opensha.sha.faultSurface.SimpleFaultData;

/**
 * <p>Title: ReadNGA_DataFile</p>
 * <p>Description: This class reads the NGA earthquake file and creates the
 * EqkRupture object from the data given in the file.
 * This class also allows the users to select from the list of the earthquakes.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created August 17, 2004
 * @version 1.0
 */

public class ReadNGA_DataFile {

  //It is a file provide by the NGA for the point source
  public static final String NGA_SOURCE_DATA_FILE_NAME = "/Users/nitingupta/PEER_NGA_Data/peer_nga_source_data.txt";


  public static final double DEFAULT_RAKE = 90;

 //list to get all the ruptures from the NGA
  private ArrayList nga_ruptureList = new ArrayList();

  public void ReadData(){
    FileReader fr = null;
    BufferedReader br = null;
    try{
      fr = new FileReader(NGA_SOURCE_DATA_FILE_NAME);
      br = new BufferedReader(fr);
      String fileLine = br.readLine();
      String  prevEqkId ="";
      String prevEqkName =null;
      while(fileLine!=null){
        //System.out.println("FileLine: "+fileLine);
        fileLine = fileLine.trim();
        if(fileLine.startsWith("#") || fileLine.equals("\n") || fileLine.equals("")){
          fileLine = br.readLine().trim();
          continue;
        }

        StringTokenizer st = new StringTokenizer(fileLine,",");
        String eqkIdString = st.nextToken().trim();
        String eqkId = "";
        String eqkName = null;
        if(eqkIdString.equals("") || eqkIdString==null){
          eqkId = prevEqkId;
          eqkName = prevEqkName;
        }
        else{
          //getting the earthquake id
          eqkId = eqkIdString;
          //reading the name of the earthquake
          eqkName = st.nextToken();
          prevEqkId = eqkId;
          prevEqkName = eqkName;
        }


        //getting the mag of the earthquake
        double mag = Double.parseDouble(st.nextToken().trim());
        //getting the Hypocenter info.
        double lat = Double.parseDouble(st.nextToken().trim());
        double lon = Double.parseDouble(st.nextToken().trim());
        double depth = Double.parseDouble(st.nextToken().trim());
        //creating the Hypocenter location object
        Location hypoLoc = new Location(lat,lon,depth);

        //reading the notes column in the  file
        st.nextToken();
        //reading the info about the fault trace and creating the gridded surface object
        //reading the origin location.
        lat = Double.parseDouble(st.nextToken().trim());
        lon = Double.parseDouble(st.nextToken().trim());
        double upperSeismogenicDepth = Double.parseDouble(st.nextToken().trim());
        //reading the notes column in the  file
        st.nextToken();

        Location originLoc = new Location(lat,lon,upperSeismogenicDepth);

        //reading the Azimuth or strike
        double strike = Double.parseDouble(st.nextToken().trim());
        //getting the dip info
        double dip =   Double.parseDouble(st.nextToken().trim());

        //getting the horizontal distance from the first location
        double length = Double.parseDouble(st.nextToken().trim());


        //getting the down dip width
        double downDipWidth = Double.parseDouble(st.nextToken().trim());

//        Location otherLoc = LocationUtils.getLocation(originLoc,new LocationVector(0.0,length,strike,0.0));
        Location otherLoc = LocationUtils.location(originLoc,
        		new LocationVector(strike, length, 0.0));

        FaultTrace fltTrace = new FaultTrace(null);
        fltTrace.add(originLoc);
        fltTrace.add(otherLoc);

        //converting the Dip(in deg.) to radians and then taking the Sin of it
        double sinOfAvDipRadians = Math.sin(Math.toRadians(dip));
        //calculating the lowerSiesmogenicDepth from the downDipWidth
        double lowerSiesmogenicDepth = (downDipWidth*sinOfAvDipRadians)+upperSeismogenicDepth;

        //creating the instance of the SimpleFaultData
        SimpleFaultData fltData = new SimpleFaultData(dip,lowerSiesmogenicDepth,
          upperSeismogenicDepth, fltTrace);

        FrankelGriddedSurface frankelFaultSurface = new FrankelGriddedSurface(fltData,1.0);

        EqkRuptureFromNGA rupture = new EqkRuptureFromNGA(eqkId,eqkName,mag,this.DEFAULT_RAKE,
            frankelFaultSurface,hypoLoc);
        //adding the rupture to the list
        nga_ruptureList.add(rupture);
        fileLine = br.readLine();
      }
      br.close();
      fr.close();
    }catch(Exception e){
      e.printStackTrace();
    }

  }


  /**
   * This function returns the observed rupture list created from the info.
   * provided from the nga peer files.
   * @return
   */
  public ArrayList getNGA_ObservedRuptureList(){
    return this.nga_ruptureList;
  }




  public static void main(String[] args){
    ReadNGA_DataFile ngaFiles = new ReadNGA_DataFile();
    ngaFiles.ReadData();
    ArrayList ruptureList = ngaFiles.getNGA_ObservedRuptureList();

    int size = ruptureList.size();
    for(int i=0;i<size;++i){
      System.out.println("Name of the Earthquake: "+((EqkRuptureFromNGA)ruptureList.get(i)).getEqkName());
    }


  }
}
