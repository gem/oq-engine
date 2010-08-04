package scratch.vipin;

import java.util.ArrayList;

import org.opensha.commons.geo.Location;

/**
 * <p>Title: Node.java </p>
 * <p>Description: </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class Node {
  private int id;
  private Location loc;
  private String faultSectionName;
  private Node primaryLink;
  private ArrayList secondaryLinks; // locations connecting with this node.

  public Node() {
  }



  public Node(int id, String faultSecName, Location loc) {
    this.setFaultSectionName(faultSecName);
    this.setLoc(loc);
    setId(id);
  }

  public int getId() {
    return this.id;
  }

  public void setId(int id) {
    this.id = id;
  }

  public String getFaultSectionName() {
    return faultSectionName;
  }

  public Location getLoc() {
    return loc;
  }

  public Node getPrimaryLink() {
    return this.primaryLink;
  }

  public ArrayList getSecondaryLinks() {
    return this.secondaryLinks;
  }

  public void setFaultSectionName(String faultSectionName) {
    this.faultSectionName = faultSectionName;
  }

  public void setLoc(Location loc) {
    this.loc = loc;
  }

  public void setPrimaryLink(Node primaryLink) {
    this.primaryLink = primaryLink;
  }

  public void addSecondayLink(Node secondayLink) {
    if(this.secondaryLinks==null) this.secondaryLinks = new ArrayList();
    secondaryLinks.add(secondayLink);
  }

  /**
   * Remove all the children except the first one
   */
  public void removeSecondayLinks() {
    if(secondaryLinks!=null)  secondaryLinks.clear();
  }

}