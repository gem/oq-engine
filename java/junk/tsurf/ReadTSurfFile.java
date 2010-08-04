package junk.tsurf;

import java.io.BufferedReader;
import java.io.FileReader;
import java.util.ArrayList;
import java.util.StringTokenizer;

//import org.opensha.sha.fault.tsurf.*;

/**
 * <p>Title: ReadTSurfFile</p>
 * <p>Description: This class reads a T-Surf file and creates TSurface object from the
 * given file. </p>
 * @author : Ned Field, Nitin Gupta and Vipin Gupta
 * @created : Feb 20, 2004
 * @version 1.0
 */

public class ReadTSurfFile {


  private final static String HEADER = "HEADER";
  private final static String VRTX = "VRTX";
  private final static String PVRTX = "PVRTX";
  private final static String TRGL = "TRGL";
  private final static String HDR_NAME_1 = "name";
  private final static String HDR_NAME_2 = "HDR name";
  private final static String HEADER_ENDING_BRACKETS = "}";

  private String faultName;
  //VRTX added to this arraylist on the bases of the vrtx id's
  private ArrayList vrtx = new ArrayList();

  //TRGL added to this arraylist
  private ArrayList trgl = new ArrayList();

  /**
   * Constructor to read the T-Surf file.
   * @param fileName : Name of the TSurf file
   */
  public ReadTSurfFile(String fileName) {
    readFile(fileName);
    int vrtx_size = vrtx.size();
    int trgl_size = trgl.size();
    //System.out.println("vrtx size: "+vrtx_size);
    Vertex vertex[] = new Vertex[vrtx_size+1];
    for(int i=0;i<vrtx_size;++i){
      Vertex vrtxObject = (Vertex)vrtx.get(i);
      //System.out.println("id: "+vrtxObject.getVrtxId());
      vertex[vrtxObject.getVrtxId()] = vrtxObject;
    }

    Object[] trglObject = trgl.toArray();
    Triangle[] triangle = new Triangle[trgl_size +1];
    for(int i=0;i<trgl_size;++i)
      triangle[i] = (Triangle)trglObject[i];

    TSurface surface  = new TSurface(faultName,vertex,triangle);

    System.out.println("Fault Name: "+faultName);
    for(int i=0; i<vertex.length;++i)
      if(vertex[i] !=null)
        System.out.println("id: " +vertex[i].getVrtxId());
    //for(int i=0; i<trgl.size();++i)
      //System.out.println("id: " +((Vertex)vrtx.get(i)).getVrtxId()+" Location: "+((Triangle)vrtx.get(i)).getLocation().toString());

  }

  /**
   * Function  to read the T-Surf file
   * @param fileName : name of the T-Surf file
   */
  private void readFile(String fileName){
    try{
      FileReader fr = new FileReader(fileName);
      BufferedReader br = new BufferedReader(fr);
      String fileLine = br.readLine();
      while(fileLine !=null){
        //reading the name of the fault
        if(fileLine.startsWith(HEADER)){
          fileLine = br.readLine().trim();
          //after we find the header starting brackets, find the name of the fault
          while(!fileLine.trim().endsWith(HEADER_ENDING_BRACKETS)){
            //if the line correspond to name of the fault, get that name.
            if(fileLine.startsWith(this.HDR_NAME_1) || fileLine.startsWith(this.HDR_NAME_2)){
              StringTokenizer st = new StringTokenizer(fileLine,":");
              st.nextToken();
              faultName = st.nextToken();
            }
            fileLine = br.readLine();
          }
        }
        //if line corresponds to the VRTX in the T-Surf
        else if(fileLine.startsWith(VRTX) || fileLine.startsWith(PVRTX)){
          StringTokenizer st = new StringTokenizer(fileLine);
          st.nextToken();
          int id = Integer.parseInt(st.nextToken());
          double lat = Double.parseDouble(st.nextToken());
          double lon = Double.parseDouble(st.nextToken());
          double depth = Double.parseDouble(st.nextToken());
          vrtx.add(new Vertex(id,lat,lon,depth));
        }
        //if line corresponds to the TRGL in the T-Surf
        else if(fileLine.startsWith(TRGL)){
          StringTokenizer st = new StringTokenizer(fileLine);
          st.nextToken();
          //getting the ids of the VRTX constituting the triangle object
          int id1 = Integer.parseInt(st.nextToken());
          int id2 = Integer.parseInt(st.nextToken());
          int id3 = Integer.parseInt(st.nextToken());
          trgl.add(new Triangle(id1,id2,id3));
        }
        fileLine = br.readLine();
      }
    }catch(Exception e){
      e.printStackTrace();
    }

  }


  public static void main(String[] args) {
    ReadTSurfFile readTSurfFile1 = new ReadTSurfFile("/Users/nitingupta/projects/la3d/data/cfm_faults-1.01b/cmfa_sisar_complete.ts");
  }
}
