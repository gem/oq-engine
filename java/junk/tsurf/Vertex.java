package junk.tsurf;

import org.opensha.commons.geo.Location;

/**
 * <p>Title: Vertex</p>
 * <p>Description: This class represent the VRTX/PVTRX in the tsurf file.
 * Each VRTX object takes a id and location object (lat,lon and depth) to be
 * created. Each VRTX has a unique id.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created : Feb 20,2004
 * @version 1.0
 */

public class Vertex {

  //class variable to store information about each vertex in the tsurf file.
  private int vrtxId;
  private double lat,lon,depth;


  /**
   * class default constructor
   * creates an empty VRTX object
   * Note : Must use the setVRTX() to set the values to this empty VRTX object.
   */
  public Vertex(){

  }

  /**
   * Creates a VRTX object similar to the VRTX in the T-Surf file.
   * @param id : Vertex Id
   * @param lat
   * @param lon
   * @param depth
   */
  public Vertex(int id, double lat, double lon,double depth){
    vrtxId = id;
    this.lat = lat;
    this.lon = lon;
    this.depth = depth;
  }

  /**
   * Creates a VRTX object similar to the VRTX in the T-Surf file.
   * @param id : Vertex Id
   * @param loc
   */
  public Vertex(int id, Location loc){
    vrtxId = id;
    lat  = loc.getLatitude();
    lon = loc.getLongitude();
    depth = loc.getDepth();
  }


  /**
   * Sets the value of the VRTX object
   * @param id : VRTX id
   * @param lat
   * @param lon
   * @param depth
   */
  public void setVRTX(int id, double lat, double lon, double depth){
    vrtxId = id;
    this.lat = lat;
    this.lon = lon;
    this.depth = depth;
  }

  /**
   *
   * @returns the Id of the VRTX
   */
  public int getVrtxId(){
   return vrtxId;
  }

  /**
   *
   * @returns the location of the VRTX
   */
  public Location getLocation(){
    return new Location(lat,lon,depth);
  }

}
