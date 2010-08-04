package scratch.vipin;

import java.util.ArrayList;

/**
 * <p>Title: MultiSectionRupture.java  </p>
 * <p>Description: Data structure to represent the multi fault section rupture</p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class MultiSectionRupture {
  private ArrayList nodeList;
  private float length;


  public MultiSectionRupture(ArrayList nodesList) {
    this.nodeList = nodesList;
  }

  /**
   * Get the nodes which make up this rupture
   * @return
   */
  public ArrayList getNodesList() {
    return this.nodeList;
  }

  /**
   * Set the length of the rupture
   * @param len
   */
  public void setLength(float len) {
    this.length = len;
  }

  /**
   * Get the length of this rupture
   * @return
   */
  public float getLength() {
    return this.length;
  }

  /**
   * Finds whether a section is contained within this rupture
   *
   * @param sectionName
   * @return
   */
  public boolean isSectionContained(String sectionName) {
    if(this.nodeList==null) return false;
    for(int i=0; i<nodeList.size(); ++i) {
      Node node = (Node)nodeList.get(i);
      if(node.getFaultSectionName().equalsIgnoreCase(sectionName)) return true;
    }
    return false;
  }

  /**
   * Finds whether this rupture spans more than 1 section
   *
   * @return
   */
  public boolean isMultiSection() {
    if(this.nodeList==null) return false;
    String sectionName = ((Node)nodeList.get(0)).getFaultSectionName();
    for(int i=1; i<nodeList.size(); ++i) {
      if(!sectionName.equalsIgnoreCase(((Node)nodeList.get(i)).getFaultSectionName())) return true;
    }
    return false;
  }

  /**
   * Finds whether 2 ruptures are same or not. It checks:
   *  1. number of points on both ruptures are same.
   *  2. It checks that length of the ruptures are same
   *  3. It checks that end points are same on the rupture
   *  4. the locations on 1 rupture also exist for the second rupture
   * @param rup
   * @return
   */
  public boolean equals(Object obj) {
    if(! (obj instanceof MultiSectionRupture)) return false;
    MultiSectionRupture rup = (MultiSectionRupture) obj;
    ArrayList rupNodesList = rup.getNodesList();
    int rupNodesListSize = rupNodesList.size();
    int nodesListSize = nodeList.size();
    // check that number of points in both ruptures are same
    if(nodesListSize!=rupNodesListSize) return false;
    //check the length of ruptures are withn tolerance
    if(Math.abs(length-rup.getLength())>1e-6) return false;

    // check the end points are same
    Node node = (Node)nodeList.get(0);
    if(node.getId()!=((Node)rupNodesList.get(0)).getId() &&
       node.getId()!=((Node)rupNodesList.get(rupNodesListSize-1)).getId()) {
      return false;
    }
    node = (Node)nodeList.get(nodesListSize-1);
    if(node.getId()!=((Node)rupNodesList.get(0)).getId() &&
       node.getId()!=((Node)rupNodesList.get(rupNodesListSize-1)).getId()) {
      return false;
    }

    // check that locations on one ruptures also exist on other rupture
    for(int i=1; i<nodesListSize; ++i) {
       node = (Node)nodeList.get(i);
      boolean found = false;
      for(int j=0; j<rupNodesListSize && !found; ++j) {
        if(node.getId()==((Node)rupNodesList.get(j)).getId()) found = true;
      }
      if(!found) return false;
    }
    return true;
  }

}