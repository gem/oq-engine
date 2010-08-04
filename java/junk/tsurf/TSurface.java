package junk.tsurf;

/**
 * <p>Title: TSurface</p>
 * <p>Description: This class represent the T-Surf object.It creates the T-Surf
 * object in the similar as the one produced by the GOCAD.
 * Indexing of the VRTX (Vertex) array  is done on the basis of VRTX ids from the
 * T-Surf file.So whatever ids for VRTX are present in the TSurf file only those
 * indexes of the VRTX array contain  the Vertex object.</p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created : Feb 20, 2004
 * @version 1.0
 */

public class TSurface {

  //class variables
  //name of the fault for which TSurf is created
  private String TSurfFaultName;

  //array of VRTX points
  private Vertex[] TSurf_VRTX;

  //array of triangles
  private Triangle[] TSurf_TRGL;

  public TSurface(String faultName, Vertex vrtx[],Triangle trgl[]) {
    TSurfFaultName = faultName;
    TSurf_VRTX = vrtx;
    TSurf_TRGL = trgl;
  }


  /**
   *
   * @returns the name of the fault which is represented as the TSurf object.
   */
  public String getFaultName(){
    return TSurfFaultName;
  }

  /**
   *
   * @returns the array of the VRTX objects creating the TSurface
   */
  public Vertex[] getAllTSurfVRTX(){
    return TSurf_VRTX;
  }

  /**
   *
   * @returns the array of the TRGL objects creating the TSurface
   */
  public Triangle[] getAllTSurfTRGL(){
    return TSurf_TRGL;

  }

  /**
   *
   * @param vrtxID : VRTX id as given in the TSurf file
   * @returns the Vertex object for the given vrtxID.
   */
  public Vertex getVRTX(int vrtxID){
    return TSurf_VRTX[vrtxID];
  }


  /**
   *
   * @param ith : index of the requested triangle
   * @returns the Vertex array constituting the actual vertex objects
   * for the ith Triangle.
   * ***Note: No Cloning of the VRTX object is done, they are passed by reference
   */
  public Vertex[] getTRGL_Vertexes(int ith){
    //size is 4 becuase 3 VRTX points constitute a triangle
    Vertex[] vertex = new Vertex[3];
    //gets the i-th triangle from the Triangle object array
    Triangle triangle = TSurf_TRGL[ith];
    //gets the ids of the VRTX's making that triangle
    int[] ids = triangle.getTRGL();
    //size of ids array would always be 3 becuase # VRTX constituting the triangle are 3
    int size = ids.length;

    //creating the VRTX array with all the VRTX points location that make the ith triangle
    for(int i=0;i<size;++i)
      vertex[i] = getVRTX(ids[i]);

    return vertex;
  }
}
