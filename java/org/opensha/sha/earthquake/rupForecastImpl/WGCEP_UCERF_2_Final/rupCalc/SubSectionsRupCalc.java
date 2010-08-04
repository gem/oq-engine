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

import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.refFaultParamDb.dao.db.DB_ConnectionPool;
import org.opensha.refFaultParamDb.dao.db.PrefFaultSectionDataDB_DAO;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.faultSurface.FaultTrace;

/**
 * This class finds all the ruptures that includes 1 or more subsections. The subsections should
 * be within a cut-off distance from each other at the end points.
 * 
 * @author vipingupta
 *
 */
public class SubSectionsRupCalc {
	private double subSectionsCutoffDist = 10; 
	private  double maxSubSectionLength = 10;
	private ArrayList<MultipleSectionRup> rupList;
	private final PrefFaultSectionDataDB_DAO faultSectionPrefDataDAO = new PrefFaultSectionDataDB_DAO(DB_ConnectionPool.getDB2ReadOnlyConn());
	private ArrayList subSectionList;
	private ArrayList doneList;
	private ArrayList<Tree> clusterList;

	  public SubSectionsRupCalc() {
		  doProcessing();
	  }
	  
	  public SubSectionsRupCalc(double maxSubSectionLength, double cutOffDistance) {
		  this.maxSubSectionLength = maxSubSectionLength;
		  this.subSectionsCutoffDist = cutOffDistance;
		  this.doProcessing();
	  }
	 

	  /**
	   * Find the various subsections, clusters and ruptures
	   *
	   */
	  public void doProcessing()  {
	    try {      
	      subSectionList = getAllSubSections(); // get all the fault sections
	      createTreesForFaultSections(); // discretize the section in 5km
	      
	    }catch(Exception e) {
	      e.printStackTrace();
	    }
	  }

	  
	  /**
	   * Get all subsections 
	   * 
	   * @return
	   */
	  private ArrayList getAllSubSections() {
			ArrayList faultSectionPrefList = faultSectionPrefDataDAO.getAllFaultSectionPrefData();
			ArrayList<FaultSectionPrefData> subSecList = new ArrayList<FaultSectionPrefData>();
			for(int i=0; i<faultSectionPrefList.size(); ++i) {
				FaultSectionPrefData faultSectionPrefData = (FaultSectionPrefData)faultSectionPrefList.get(i);
				//if(!faultSectionPrefData.getSectionName().equalsIgnoreCase("Battle Creek")) continue;
				subSecList.addAll(faultSectionPrefData.getSubSectionsList(maxSubSectionLength));
			}
			return subSecList;
	  }

	  /**
	   * Divide each section to subsections after sub sampling.
	   * Also create a tree for each section
	   *
	   * @param faultTraceMapping
	   * @throws InvalidRangeException
	   */
	  private void createTreesForFaultSections() throws
	      InvalidRangeException {
		  
		 clusterList = new ArrayList<Tree>();
		 rupList = new ArrayList<MultipleSectionRup>();
		 // create trees 
		 doneList = new ArrayList();
		 for(int i=0; i<subSectionList.size(); ++i) {
	    	FaultSectionPrefData faultSectionPrefData = (FaultSectionPrefData)subSectionList.get(i);
	    	if(doneList.contains(faultSectionPrefData.getSectionName())) continue;
	    	Tree tree = new Tree();
	    	getAdjacentFaultSectionNodes(tree, i);
	    	clusterList.add(tree);
	    	//System.out.println("***********TREE "+clusterList.size()+" ***********\n");
	    	//tree.writeInfo();
	    	ArrayList treeRupList = tree.getRuptures();
	    	rupList.addAll(treeRupList);
	    }
	    System.out.println("Total Subsections ="+subSectionList.size());
	    System.out.println("Total Clusters ="+clusterList.size());
	    System.out.println("Total ruptures="+rupList.size());
	  }
	  
	  
	  /**
	   * Retunr the number of clusters
	   * @return
	   */
	  public int getNumClusters() {
		  return this.clusterList.size();
	  }
	  
	  
	  /**
	   * Get the cluster at specified index
	   * @param index
	   * @return
	   */
	  public Tree getCluster(int index) {
		  return this.clusterList.get(index);
	  }
	  
	  /**
	   * Get the number of ruptures
	   * 
	   * @return
	   */
	  public int getNumRuptures() {
		  return this.rupList.size();
	  }

	  /**
	   * Get the rupture at the specified index
	   * 
	   * @param rupIndex
	   * @return
	   */
	  public MultipleSectionRup getRupture(int rupIndex) {
		  return rupList.get(rupIndex);
	  }
	  
	  /**
	   * Return a list of all ruptures
	   * @return
	   */
	  public ArrayList<MultipleSectionRup> getRupList() {
		  return this.rupList;
	  }

	  /**
	   * Get all the faults within interFaultCutOffDistance kms of the location loc
	   * This allows to find adjacent fault for fault to fault jumps
	   * @param loc
	   * @param interFaultCutOffDistance
	   * @param adjacentFaultNames
	   */
	  private void getAdjacentFaultSectionNodes(Tree tree, int subSectionIndex) {
		  FaultSectionPrefData faultSectionPrefData = (FaultSectionPrefData)subSectionList.get(subSectionIndex);
		  doneList.add(faultSectionPrefData.getSectionName());
		  tree.connectInTree(faultSectionPrefData.getSectionId(), faultSectionPrefData.getSectionId());
		  for(int i=0; i<subSectionList.size(); ++i) {
			  if(i==subSectionIndex) continue;
			  FaultSectionPrefData faultSectionPrefData1 = (FaultSectionPrefData)subSectionList.get(i);
			  if(!isWithinCutOffDist(faultSectionPrefData, faultSectionPrefData1)) continue;
			  tree.connectInTree(faultSectionPrefData.getSectionId(), faultSectionPrefData1.getSectionId());
			  if(doneList.contains(faultSectionPrefData1.getSectionName())) continue;
			  //System.out.println("Connected "+faultSectionPrefData.getSectionName()+ " AND "+ faultSectionPrefData1.getSectionName());
			  /*if(i>subSectionIndex)*/ getAdjacentFaultSectionNodes(tree, i);
		  }
	  }
	  
	  /**
	   * It finds whether 2 subsections are within cutoff distance of each other
	   * @param faultSectionPrefData1
	   * @param faultSectionPrefData2
	   * @return
	   */
	  private boolean isWithinCutOffDist(FaultSectionPrefData faultSectionPrefData1, 
			  FaultSectionPrefData faultSectionPrefData2) {
		  FaultTrace trace1= faultSectionPrefData1.getFaultTrace();
		  int endIndex1 = trace1.getNumLocations()-1;
		  FaultTrace trace2 = faultSectionPrefData2.getFaultTrace();
		  int endIndex2 = trace2.getNumLocations()-1;
		  if(LocationUtils.horzDistanceFast(trace1.get(0), trace2.get(0))<=subSectionsCutoffDist) 
			  return true;
		  if(LocationUtils.horzDistanceFast(trace1.get(0), trace2.get(endIndex2))<=subSectionsCutoffDist) 
			  return true;
		  if(LocationUtils.horzDistanceFast(trace1.get(endIndex1), trace2.get(0))<=subSectionsCutoffDist) 
			  return true;
		  if(LocationUtils.horzDistanceFast(trace1.get(endIndex1), trace2.get(endIndex2))<=subSectionsCutoffDist) 
			  return true;
		  return false;
	  }

	  public static void main(String args[]) {
		  SubSectionsRupCalc rupCalc = new SubSectionsRupCalc(10, 10);
	  }
}
