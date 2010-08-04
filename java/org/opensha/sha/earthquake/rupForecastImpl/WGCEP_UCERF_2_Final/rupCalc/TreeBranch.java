/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.rupCalc;

import java.util.ArrayList;

/**
 * <p>Title: TreeBranch.java </p>
 * <p>Description: This refers to a branch of a tree </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */

public class TreeBranch {
  private int subSectionId;
  private ArrayList<Integer> adjacentSubSections = new ArrayList<Integer>();

  public TreeBranch(int subSectionId) {
	  this.subSectionId = subSectionId;
  }

  /**
   * Get sub-section id
   * @return
   */
  public int getSubSectionId() {
    return subSectionId;
  }

  /**
   * Get number of adjacent subsections to this section
   * @return
   */
  public int getNumAdjacentSubsections() {
	  return this.adjacentSubSections.size();
  }
  
  
  /**
   * Get the adjancet subsection at the specified index
   * @param index
   * @return
   */
  public int getAdjacentSubSection(int index) {
	  return adjacentSubSections.get(index);
  }
  
  /**
   * Get a list of all adjacent subsections
   * @return
   */
  public ArrayList<Integer> getAdjacentSubSectionsList() {
	  return this.adjacentSubSections;
  }
  
  /**
   * Add adjacent sub section (if it does not exist already)
   * @param subSectionName
   */
  public void addAdjacentSubSection(int subSectionId) {
	  if(!adjacentSubSections.contains(subSectionId))
		  adjacentSubSections.add(subSectionId);
  }
  
  /**
   * Is the specified sub section  adjacent to this sub section?
   * 
   * @param subSectionName
   * @return
   */
  public boolean isAdjacentSubSection(int subSectionId) {
	  return adjacentSubSections.contains(subSectionId);
  }

}
