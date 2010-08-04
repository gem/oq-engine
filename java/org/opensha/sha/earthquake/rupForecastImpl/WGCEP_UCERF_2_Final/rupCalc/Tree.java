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
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;

/**
 * <p>Title: Tree.java </p>
 * <p>Description: This refers to a tree which can consist of various branches. </p>
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author not attributable
 * @version 1.0
 */
public class Tree {
	// mapping of subsections name and their corresponding treemap
	public HashMap<Integer,TreeBranch> treeBranchMap = new HashMap<Integer,TreeBranch>();
	// mapping to mantain which branches have been traversed already
	public HashMap<String, Boolean> traversedBranchMap;
	public ArrayList<MultipleSectionRup> rupList;
	public void connectInTree(int subSectionId1, int subSectionId2) {		
		// This statement is needed to avoid cycles
		if(subSectionId1 > subSectionId2) {
			updateTreeBranch(subSectionId1, subSectionId2);
		}
		else {
			updateTreeBranch(subSectionId2, subSectionId1);
		}
		//else return;
	}

	/**
	 * Update tree branch
	 * @param subSection1
	 * @param subSection2
	 */
	private void updateTreeBranch(int subSection1, int subSection2) {
		TreeBranch treeBranch;
		treeBranch = treeBranchMap.get(subSection1);
		if(treeBranch==null) {
			 treeBranch = new TreeBranch(subSection1);
			 treeBranchMap.put(subSection1, treeBranch);
		}
		treeBranch.addAdjacentSubSection(subSection2);
	}
	
	/**
	 * Write the tree on System.out
	 *
	 */
	public void writeInfo() {
		Iterator<Integer> it  = treeBranchMap.keySet().iterator();
		while(it.hasNext()) {
			TreeBranch treeBranch = treeBranchMap.get(it.next());
			System.out.println("Adjacent nodes for "+treeBranch.getSubSectionId());
			for(int i=0; i<treeBranch.getNumAdjacentSubsections(); ++i)
				System.out.println(treeBranch.getAdjacentSubSection(i));
		}
	}
	
	/**
	 * Get all possible ruptures in this Tree
	 * @return
	 */
	public ArrayList getRuptures() {
		  //traversedBranchMap = new HashMap<String, Boolean>();
		  
		  rupList = new ArrayList<MultipleSectionRup>() ;
		  Iterator<Integer> it = this.treeBranchMap.keySet().iterator();
		  while(it.hasNext()) {
			  int subSecId = it.next();
			  //System.out.println("subsection Id="+subSecId);
			  ArrayList rupture= new ArrayList();
			  // if(isTraversed(subSecName)) continue;
			  traverse(subSecId, rupture);
		  }
		  return this.rupList;
	}
	
	/**
	 * Traverse all the adjacent subsections of the specified subsection
	 * @param subSecName
	 * @param subSecList
	 */
	private void traverse(int subSecId, ArrayList subSecList) {
		if(subSecList.contains(subSecId)) return;
		subSecList.add(subSecId);
		MultipleSectionRup rup = new MultipleSectionRup(subSecList);
		if(!this.rupList.contains(rup)) {
			rupList.add(rup);
			//writeRup(rup);
		}
		//traversedBranchMap.put(subSecName, new Boolean(true));
		//if(isTraversed(subSecName)) return;
		TreeBranch branch = treeBranchMap.get(subSecId);
		for(int i=0; branch!=null && i<branch.getNumAdjacentSubsections(); ++i) {
			traverse(branch.getAdjacentSubSection(i), subSecList);
		}
		
	}
	
	private void writeRup(MultipleSectionRup rup) {
		for(int i=0; i<rup.getNumSubSections(); ++i)
			System.out.print(rup.getSubSection(i)+",");
		System.out.println("");
	}
	
	/**
	 * Returns true if the subsection has already been traversed
	 * 
	 * @param subSecName
	 * @return
	 */
	private boolean isTraversed(String subSecName) {
		Boolean isTraversed = traversedBranchMap.get(subSecName);
		if(isTraversed !=null && isTraversed.booleanValue()) return true;
		return false;
	}
	
	/**
	 * Get the number of subsections in this cluster
	 * @return
	 */
	public int getNumSubSections() {
		return getAllSubSectionsIdList().size();
		/*Iterator<Integer> it = treeBranchMap.keySet().iterator();
		int numSubSections=0;
		while(it.hasNext()) {
			int subSectionId = it.next();
			++numSubSections;
			numSubSections+=treeBranchMap.get(subSectionId).getAdjacentSubSectionsList().size();
		}
		return numSubSections;*/
	}
	
	
	/**
	 * List of all subsections within this cluster
	 */
	public ArrayList<Integer> getAllSubSectionsIdList() {
		HashSet<Integer> subSectionIdSet = new HashSet<Integer>();
		Iterator<Integer> it = treeBranchMap.keySet().iterator();
		while(it.hasNext()) {
			int subSectionId = it.next();
			
			subSectionIdSet.add(subSectionId);
			subSectionIdSet.addAll(treeBranchMap.get(subSectionId).getAdjacentSubSectionsList());
		}
		ArrayList<Integer> subSectionIdList = new ArrayList<Integer>();
		subSectionIdList.addAll(subSectionIdSet);
		return subSectionIdList;
	}

	
}
