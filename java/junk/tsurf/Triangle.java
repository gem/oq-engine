package junk.tsurf;

/**
 * <p>Title: Triangle</p>
 * <p>Description: This class represent the Triangle(TRGL) in the T-Surf file.
 * TRGL object creates a triangle from the 3 VRTX object, representing 3 coordinates
 * of the triangle. Each TRGL object is created using the 3 VRTX id's.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @version 1.0
 */

public class Triangle {

  //class variables
  //VRTX ID's creating a triangle
  int id1, id2, id3;


  /**
   * class default constructor
   * Creates a empty TRGL object
   * Note : Must use the setTRGL to set the Triangle values.
   */
  public Triangle(){

  }

  /**
   * Creates a TRGL object similar to the one in the TSurf file
   * @param vrtxId_1
   * @param vrtxId_2
   * @param vrtxId_3
   */
  public Triangle(int vrtxId_1, int vrtxId_2, int vrtxId_3){
    id1 = vrtxId_1;
    id2 = vrtxId_2;
    id3 = vrtxId_3;
  }


  /**
   * Sets the value for the TRGL object.
   * @param vrtxId_1
   * @param vrtxId_2
   * @param vrtxId_3
   */
  public void setTRGL(int vrtxId_1, int vrtxId_2, int vrtxId_3){
    id1 = vrtxId_1;
    id2 = vrtxId_2;
    id3 = vrtxId_3;
  }

  /**
   *
   * @returns the array of VRTX ids constituting the triangle
   */
  public int[] getTRGL(){
    int[] vertex_id = new int[3];
    vertex_id[0] = id1;
    vertex_id[1] = id2;
    vertex_id[2] = id3;
    return vertex_id;
  }
}
