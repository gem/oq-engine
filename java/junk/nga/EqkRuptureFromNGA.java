package junk.nga;


import java.util.ArrayList;

import org.opensha.commons.data.Site;
import org.opensha.commons.geo.Location;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.faultSurface.EvenlyGriddedSurfaceAPI;


/**
 * <p>Title: EqkRuptureFromNGA</p>
 * <p>Description: This class extends the EqkRuture and creates the observed
 * earthquake rupture from the data provided by the NGA-PEER file</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created August 18, 2004
 * @version 1.0
 */

public class EqkRuptureFromNGA extends EqkRupture {

  private String eqkId ;
  private String eqkName;

  //List containing the different locations this rupture was recorded
  private ArrayList observeredRuptureLocations ;

  //List containing the rakes as observed at different locations for rupture
  private ArrayList observeredRuptureRakeList ;


  //List of the Vs30 as provided by different locations that observed the rupture
  private ArrayList observedRuptureVs30List ;

  //list of the SA values as provided by different locations that observed the rupture
  private ArrayList observedRuptureIM_ValuesList ;



  /**
   * Class default constructor
   */
  public EqkRuptureFromNGA() {}

  /**
   * Class constructor to accept the Earthquake Id and Name
   * @param eqkId : EarthQuake Id given by the PEER-NGA group
   * @param eqkName : Name of the earthquake provided by PEER-NGA group
   */
  public EqkRuptureFromNGA(String eqkId, String eqkName){
    this.eqkId = eqkId;
    this.eqkName = eqkName;
  }

  /**
   * Class constructor accepts the following parameters to create the
   * EqkRupture object.
   * @param mag
   * @param aveRake
   * @param ruptureSurface
   * @param hypocenterLocation
   */
  public EqkRuptureFromNGA(double mag,double aveRake,
        EvenlyGriddedSurfaceAPI ruptureSurface,
	Location hypocenterLocation){
    super(mag,aveRake,ruptureSurface,hypocenterLocation);
  }


  /**
   * Class constructor accepts the parameters to create the EqkRupture object
   * @param eqkId : EarthQuake Id given by the PEER-NGA group
   * @param eqkName : Name of the earthquake provided by PEER-NGA group
   * @param mag
   * @param aveRake
   * @param ruptureSurface
   * @param hypocenterLocation
   */
  public EqkRuptureFromNGA(String eqkId, String eqkName,double mag,double aveRake,
        EvenlyGriddedSurfaceAPI ruptureSurface,
	Location hypocenterLocation){
    super(mag,aveRake,ruptureSurface,hypocenterLocation);
    this.eqkId = eqkId;
    this.eqkName = eqkName;
  }

  /**
   * Set the Earthquake Id
   * @param id
   */
  public void setEqkId(String id){
    eqkId = id;
  }

  /**
   * set the earthquake name
   * @param name
   */
  public void setEqkName(String name){
    eqkName = name;
  }


  /**
   * Add the Eqk qk sites in the list of observed earthquake sites
   * @param loc
   */
  public void addSite(ArrayList locationList){
    observeredRuptureLocations = new ArrayList();
    int size  = locationList.size();
    for(int i=0;i<size;++i){
      Location loc  = (Location)locationList.get(i);
      Site site = new Site(loc);
      observeredRuptureLocations.add(site);
    }

  }


  /**
   * Add the observed Eqk qk Rake at the location in the list
   * @param loc
   */
  public void addSiteRake(ArrayList rakeList){
    observeredRuptureRakeList = rakeList;
  }

  /**
   * Add the observed Eqk qk IM values for all the locations of the earthquake
   * @param loc
   */
  public void addIM_Values(ArrayList imValues){
    observedRuptureIM_ValuesList = imValues;
  }



  /**
   * Add the observed Vs30 for the site in the list
   * @param Vs30
   */
  public void addSiteVs30(ArrayList vs30List){
    observedRuptureVs30List = vs30List;
  }


  /**
   * get the list of vs30 for the locations that reported the rupture info.
   * @return
   */
  public ArrayList getSiteVs30(){
    return observedRuptureVs30List;
  }


  /**
   * get the list of sites for the observed rupture
   * @return
   */
  public ArrayList getSiteList(){
    return observeredRuptureLocations;
  }



  /**
   *
   * @returns the list of rake for each observed location
   */
  public ArrayList getObservedRuptureSiteRakeList(){
    return observeredRuptureRakeList;
  }

  /**
   *
   * @returns the list of IM values for each observed location of the rupture
   */
  public ArrayList getObservedRuptureSiteIMList(){
    return observedRuptureIM_ValuesList;
  }



  /**
   *
   * @returns the information for the rupture
   */
  public String getInfo() {
    String info1, info2;
    info1 = new String("\tEqk Name = "+eqkName+"\n"+
                       "\tEqk Id = "+eqkId+"\n"+
                       "\tMag. = "+(float)mag+"\n"+
                       "\tAve. Dip = "+(float)ruptureSurface.getAveDip()+"\n");

    // write our rupture surface information
    if(ruptureSurface.getNumCols() == 1 && ruptureSurface.getNumRows() == 1) {
      Location loc = ruptureSurface.getLocation(0,0);
      info2 = new String("\tPoint-Surface Location (lat, lon, depth (km):"+"\n\n"+
                         "\t\t"+ (float)loc.getLatitude()+", "+(float)loc.getLongitude()+
                         ", "+(float)loc.getDepth());
    }
    else {
      Location loc1 = ruptureSurface.getLocation(0,0);
      Location loc2 = ruptureSurface.getLocation(0,ruptureSurface.getNumCols()-1);
      Location loc3 = ruptureSurface.getLocation(ruptureSurface.getNumRows()-1,0);
      Location loc4 = ruptureSurface.getLocation(ruptureSurface.getNumRows()-1,ruptureSurface.getNumCols()-1);
      info2 = new String("\tRup. Surf. Corner Locations (lat, lon, depth (km):"+"\n\n"+
                         "\t\t"+ (float)loc1.getLatitude()+", "+(float)loc1.getLongitude()+", "+(float)loc1.getDepth()+"\n"+
                         "\t\t"+ (float)loc2.getLatitude()+", "+(float)loc2.getLongitude()+", "+(float)loc2.getDepth()+"\n"+
                         "\t\t"+ (float)loc3.getLatitude()+", "+(float)loc3.getLongitude()+", "+(float)loc3.getDepth()+"\n"+
                         "\t\t"+ (float)loc4.getLatitude()+", "+(float)loc4.getLongitude()+", "+(float)loc4.getDepth()+"\n");
    }
    return info1 + info2;
   }

  /**
   * get the earthquake id
   * @return
   */
  public String getEqkId(){
    return eqkId;
  }

  /**
   * get the Eqk Name
   * @return
   */
  public String getEqkName(){
    return eqkName;
  }
}
