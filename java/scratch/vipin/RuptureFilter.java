package scratch.vipin;

import java.util.ArrayList;

/**
 * <p>Title: RuptureFilter.java </p>
 * <p>Description: This accepts a list of ruptures and returns a sublist based
 * on the filter parameters </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class RuptureFilter {

  /**
   * Return the rupture list which contains ruptures involving a specific section name
   * @param masterRupList
   * @param sectionName
   * @return
   */
  public static ArrayList getRupturesListForSection(ArrayList masterRupList, String sectionName) {
    if(sectionName==null) return masterRupList;
    ArrayList rupSubList = new ArrayList();
    // loop over all ruptures
    for(int i=0; i<masterRupList.size(); ++i) {
      MultiSectionRupture multiSectionRup = (MultiSectionRupture)masterRupList.get(i);
      // if this rupture contains the section, add it to sub list
      if(multiSectionRup.isSectionContained(sectionName)) rupSubList.add(multiSectionRup);
    }
    return rupSubList;
  }

  /**
   * Get the ruptures for a specific range of length
   *
   * @param masterRupList
   * @param minLength
   * @param maxLength
   * @return
   */
  public static ArrayList getRupturesForLength(ArrayList masterRupList, double minLength, double maxLength) {
    // no filtering
    if(Double.isNaN(minLength) && Double.isNaN(maxLength)) return masterRupList;
    // only filter for max length
    if(Double.isNaN(minLength)) minLength=0;
    // only filter for min length
    if(Double.isNaN(maxLength)) maxLength=Double.MAX_VALUE;

    ArrayList rupSubList = new ArrayList();
    float length;
   // loop over all ruptures
   for(int i=0; i<masterRupList.size(); ++i) {
     MultiSectionRupture multiSectionRup = (MultiSectionRupture)masterRupList.get(i);
     length = multiSectionRup.getLength();
     // if this rupture contains the section, add it to sub list
     if(minLength<=length && maxLength>=length) rupSubList.add(multiSectionRup);
   }
   return rupSubList;
  }

  /**
   * Return the rupture list which contains ruptures involving more than 1 section
   *
   * @param masterRupList
   * @param sectionName
   * @return
   */
  public static ArrayList getRupturesSpanningMultipleSections(ArrayList masterRupList) {
    ArrayList rupSubList = new ArrayList();
    // loop over all ruptures
    for(int i=0; i<masterRupList.size(); ++i) {
      MultiSectionRupture multiSectionRup = (MultiSectionRupture)masterRupList.get(i);
      // if this rupture contains the section, add it to sub list
      if(multiSectionRup.isMultiSection()) rupSubList.add(multiSectionRup);
    }
    return rupSubList;
  }



  /**
   * Returns the ruptures for specific length range on a particular section
   *
   * @param masterRupList
   * @param sectionName
   * @param minLength
   * @param maxLength
   * @return
   */
  public static ArrayList getRupturesForLengthAndSection(ArrayList masterRupList,
      String sectionName, double minLength, double maxLength, boolean isMultiSection) {
    ArrayList rupSubList = new ArrayList();
    // filter based on whether rupture spans across multiple sections
    if(isMultiSection) masterRupList = getRupturesSpanningMultipleSections(masterRupList);
    // no filtering
    if(sectionName==null && Double.isNaN(minLength) && Double.isNaN(maxLength))
      return masterRupList;
    // only filter based on rup length
    if(sectionName==null) return getRupturesForLength(masterRupList, minLength, maxLength);
    // only filter based on section name
    if(Double.isNaN(minLength) && Double.isNaN(maxLength)) return getRupturesListForSection(masterRupList, sectionName);

    float length;
   // loop over all ruptures
   for(int i=0; i<masterRupList.size(); ++i) {
     MultiSectionRupture multiSectionRup = (MultiSectionRupture)masterRupList.get(i);
     length = multiSectionRup.getLength();
     // if this rupture contains the section, add it to sub list
     if(minLength<=length && maxLength>=length && multiSectionRup.isSectionContained(sectionName)) rupSubList.add(multiSectionRup);
   }
   return rupSubList;

  }

}