package scratch.ned.rupsInFaultSystem.OLD_STUFF;

import java.io.FileWriter;
import java.util.ArrayList;
import java.util.Collections;

import org.opensha.commons.data.NamedObjectComparator;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelPrefDataFinal;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.gui.infoTools.GraphiWindowAPI_Impl;

public class OldCreateRupturesFromSections {
	
	/*
	SubSectionsRupCalc

DONE	getNumClusters()
DONE	getCluster(i).getNumSubSections()
DONE	getCluster(i).getRuptures().size()				mid method is ArrayList
DONE	getCluster(clusterIndex).getAllSubSectionsIdList()	ArrayList<Integer>
DONE	getCluster(clusterIndex).getRuptures()			ArrayList
DONE	getRupList()								ArrayList<MultipleSectionRup>

	 */
	
	ArrayList<FaultSectionPrefData> allFaultSectionPrefData;
	double sectionDistances[][], sectionAngleDiffs[][];
	String endPointNames[];
	Location endPointLocs[];
	int numSections, numSectEndPts, counter, numSubSections, minNumSubSectInRup;
	ArrayList<ArrayList<Integer>> sectionConnectionsList, endToEndSectLinksList;
	ArrayList<OldSectionCluster> sectionClusterList;
	double maxJumpDist, maxAngle, maxTotStrikeChange, maxSubSectionLength;
	ArrayList<ArrayList<FaultSectionPrefData>> subSectionPrefDataList;

	
	/**
	 * 
	 * @param maxJumpDist
	 * @param maxAngle
	 * @param maxStrikeChange
	 * @param maxSubSectionLength
	 * @param minNumSubSectInRup
	 */
	public OldCreateRupturesFromSections(double maxJumpDist, double maxAngle, double maxStrikeChange, 
			double maxSubSectionLength, int minNumSubSectInRup) {
		
		this.maxJumpDist=maxJumpDist;
		this.maxAngle=maxAngle;
		this.maxTotStrikeChange=maxStrikeChange;
		this.maxSubSectionLength=maxSubSectionLength;
		this.minNumSubSectInRup=minNumSubSectInRup;
		
		Boolean includeSectionsWithNaN_slipRates = false;
		getAllSections(includeSectionsWithNaN_slipRates);
		
//		writeSectionDistances(10.0);
		
		computeConnectedSectionEndpointPairs();
		computeEndToEndSectLinksList();
		computeSectionClusters();

		System.out.println("maxDist="+maxJumpDist+"\tmaxAngle="+maxAngle+"\tmaxStrikeChange="+
				maxStrikeChange+"\tmaxSubSectionLength="+maxSubSectionLength+"\tminNumSubSectInRup="+minNumSubSectInRup);
		System.out.println("numSubSections="+numSubSections+"\tgetRupList().size()="+getRupList().size());
		
		
		
//		for(int i=0; i<sectionClusterList.size();i++)
//		System.out.println("sectionClusterList.get(0).getRuptures().size()="+sectionClusterList.get(0).getRuptures().size());
///			System.out.println("Cluster "+i+" has "+sectionClusterList.get(i).getNumSubSections()+" subsections");
//		testClusters();
	}
	
	public int getNumClusters() {
		return sectionClusterList.size();
	}
	
	public OldSectionCluster getCluster(int clusterIndex) {
		return sectionClusterList.get(clusterIndex);
	}
	
	
	
	  public ArrayList<ArrayList<Integer>> getRupList() {
		  ArrayList<ArrayList<Integer>> rupList = new ArrayList<ArrayList<Integer>>();
		  for(int i=0; i<sectionClusterList.size();i++)
			  rupList.addAll(sectionClusterList.get(i).getRuptures());
		  return rupList;
	  }

	
	
	/**
	 * This gets the section data, creates subsections, and fills in arrays giving the 
	 * name of section endpoints, angles between section endpoints, and distances between
	 * section endpoints (these latter arrays are for sections, not subsections)
	 * @param includeSectionsWithNaN_slipRates
	 */
	private void getAllSections(boolean includeSectionsWithNaN_slipRates) {
		/** Set the deformation model
		 * D2.1 = 82
		 * D2.2 = 83
		 * D2.3 = 84
		 * D2.4 = 85
		 * D2.5 = 86
		 * D2.6 = 87
		 */
		int deformationModelId = 82;
		
		DeformationModelPrefDataFinal deformationModelPrefDB = new DeformationModelPrefDataFinal();
		allFaultSectionPrefData = deformationModelPrefDB.getAllFaultSectionPrefData(deformationModelId);
		//Alphabetize:
		Collections.sort(allFaultSectionPrefData, new NamedObjectComparator());

		// find and print max Down-dip width
		double maxDDW=0;
		int index=-1;
		for(int i=0; i<allFaultSectionPrefData.size(); i++) {
			double ddw = allFaultSectionPrefData.get(i).getDownDipWidth();
			if(ddw>maxDDW) {
				maxDDW = ddw;
				index=i;
			}
		}
		System.out.println("Max Down-Dip Width = "+maxDDW+" for "+allFaultSectionPrefData.get(index).getSectionName());

		
		// remove those with no slip rate
		 if(!includeSectionsWithNaN_slipRates) {
				System.out.println("Removing the following due to NaN slip rate:");
				for(int i=allFaultSectionPrefData.size()-1; i>=0;i--)
					if(Double.isNaN(allFaultSectionPrefData.get(i).getAveLongTermSlipRate())) {
						System.out.println("\t"+allFaultSectionPrefData.get(i).getSectionName());
						allFaultSectionPrefData.remove(i);
					}	 
		 }
		 

		 // make subsection data
		 subSectionPrefDataList = new ArrayList<ArrayList<FaultSectionPrefData>>();
		 numSubSections=0;
		 numSections = allFaultSectionPrefData.size();
		 for(int i=0; i<numSections; ++i) {
			 FaultSectionPrefData faultSectionPrefData = (FaultSectionPrefData)allFaultSectionPrefData.get(i);
			 ArrayList<FaultSectionPrefData> subSectData = faultSectionPrefData.getSubSectionsList(maxSubSectionLength);
			 numSubSections += subSectData.size();
			 subSectionPrefDataList.add(subSectData);
		 }
		 
		 // write the number of sections and subsections
//		 System.out.println("numSections="+numSections+";  numSubSections="+numSubSections);
		 // write index/names
//		 for(int i=0;i<allFaultSectionPrefData.size();i++) System.out.println(i+"\t"+allFaultSectionPrefData.get(i).getSectionName());
		 // write out strike directions
//		 for(int s=0;s<num_sections;s++) System.out.println(allFaultSectionPrefData.get(s).getFaultTrace().getStrikeDirection());

		
		numSectEndPts = 2*numSections;
		sectionDistances = new double[numSectEndPts][numSectEndPts];
		sectionAngleDiffs = new double[numSectEndPts][numSectEndPts];
		endPointNames = new String[numSectEndPts];
		endPointLocs = new Location[numSectEndPts];
		
		// loop over first fault section (A)
		for(int a=0;a<numSections;a++) {
			FaultSectionPrefData dataA = allFaultSectionPrefData.get(a);
			int indexA_firstPoint = 2*a;
			int indexA_lastPoint = indexA_firstPoint+1;
			endPointNames[indexA_firstPoint] = dataA.getSectionName() +" -- first";
			endPointNames[indexA_lastPoint] = dataA.getSectionName() +" -- last";
			Location locA_1st = dataA.getFaultTrace().get(0);
			Location locA_2nd = dataA.getFaultTrace().get(dataA.getFaultTrace().size()-1);
			endPointLocs[indexA_firstPoint] = locA_1st;
			endPointLocs[indexA_lastPoint] = locA_2nd;
//			System.out.println(endPointNames[indexA_firstPoint]+"\t"+endPointNames[indexA_lastPoint]);
			// loop over second fault section (B)
			for(int b=0;b<allFaultSectionPrefData.size();b++) {
				FaultSectionPrefData dataB = allFaultSectionPrefData.get(b);
				int indexB_firstPoint = 2*b;
				int indexB_lastPoint = indexB_firstPoint+1;
				Location locB_1st = dataB.getFaultTrace().get(0);
				Location locB_2nd = dataB.getFaultTrace().get(dataB.getFaultTrace().size()-1);
				sectionDistances[indexA_firstPoint][indexB_firstPoint] = LocationUtils.horzDistanceFast(locA_1st, locB_1st);
				sectionDistances[indexA_firstPoint][indexB_lastPoint] = LocationUtils.horzDistanceFast(locA_1st, locB_2nd);
				sectionDistances[indexA_lastPoint][indexB_firstPoint] = LocationUtils.horzDistanceFast(locA_2nd, locB_1st);
				sectionDistances[indexA_lastPoint][indexB_lastPoint] = LocationUtils.horzDistanceFast(locA_2nd, locB_2nd);
				
				double dirA = dataA.getFaultTrace().getStrikeDirection();  // values are between -180 and 180
				double dirB = dataB.getFaultTrace().getStrikeDirection();
				
				sectionAngleDiffs[indexA_firstPoint][indexB_firstPoint] = getStrikeDirectionDifference(reverseAzimuth(dirA), dirB);
				sectionAngleDiffs[indexA_firstPoint][indexB_lastPoint] = getStrikeDirectionDifference(reverseAzimuth(dirA), reverseAzimuth(dirB));
				sectionAngleDiffs[indexA_lastPoint][indexB_firstPoint] = getStrikeDirectionDifference(dirA, dirB);
				sectionAngleDiffs[indexA_lastPoint][indexB_lastPoint] = getStrikeDirectionDifference(dirA, reverseAzimuth(dirB));
			}
		}
	}
	
	
	/**
	 * For each section endpoint, this creates a list of endpoints on other sections that are both within 
	 * the given distance and where the angle differences between sections is not larger than given.  This
	 * generates an ArrayList of ArrayLists (named sectionConnectionsList).  Reciprocal duplicates are not filtered out.
	 * @param maxJumpDist
	 * @param maxAngle
	 */
	private void computeConnectedSectionEndpointPairs() {
		sectionConnectionsList = new ArrayList<ArrayList<Integer>>();
		for(int i=0;i<numSectEndPts;i++) {
			ArrayList<Integer> sectionConnections = new ArrayList<Integer>();
			for(int j=0;j<numSectEndPts;j++)
				 
				if(sectionAngleDiffs[i][j] <= maxAngle && sectionAngleDiffs[i][j] >= -maxAngle)
					if(sectionDistances[i][j] <= maxJumpDist && getSectionIndexForEndPoint(i) != getSectionIndexForEndPoint(j)) {
						sectionConnections.add(j);
					}
					else { // check if it comes close to middle of any other section
						boolean j_isOdd = (((double)j/2.0 - Math.floor(j/2.0)) > 0.1); // only check odd j values (second end of section)
						if(j_isOdd && !sectionConnections.contains(j-1) && j-1 != i) {  // also make sure the other end point was not already obtained
							int sectIndex = (int) Math.floor(j/2);
							Location loc = endPointLocs[i];
							double distToTrace = allFaultSectionPrefData.get(sectIndex).getFaultTrace().minDistToLine(loc);
							if(distToTrace < maxJumpDist) {
								String sectName = allFaultSectionPrefData.get(sectIndex).getFaultTrace().getName();
								System.out.println(endPointNames[i]+" is close ("+Math.round(distToTrace)+"k m) to the middle of trace "+sectName);
							}
						}
					}
			sectionConnectionsList.add(sectionConnections);
/*
			System.out.print("\n"+i+"\t"+endPointNames[i]+"\thas "+sectionConnections.size()+"\t");
			for(int k=0; k<sectionConnections.size(); k++) System.out.print(sectionConnections.get(k)+",");
			System.out.print("\n");
*/
		}
	}
	
	
	   
	/**
	 * For each section, this adds neighboring sections as links until the ends are reached, at which 
	 * time this end-to-end link is saved if it doesn't already exist.  All branches are followed. For example,
	 * three sections in a "Y" shape would lead to two end-to-end links, and four sections in an "X" shape would 
	 * lead to four end-to-end links.  The result is put into endTEndSectLinksList, an ArrayList of ArrayList<Integer>
	 * objects (where the latter lists all the section end points in the list).
	 */
    private void computeEndToEndSectLinksList() {
    	endToEndSectLinksList  = new ArrayList<ArrayList<Integer>>();
    	
    	System.out.println("sum_sections = "+numSections);
    	
    	int oldNum=0;
        for(int sect=0; sect<numSections; sect++) {
//        for(int sect=68; sect<69; sect++) {
//      	System.out.println("sect = "+sect+"  "+allFaultSectionPrefData.get(sect).getSectionName());
//        	System.out.println("\n\nfirst path");
    		ArrayList<ArrayList> firstConnectionsList = new ArrayList<ArrayList>();
    		int startPtIndex1 = sect*2;
    		ArrayList<Integer> currentList1 = new ArrayList<Integer>();
    		currentList1.add(startPtIndex1);
    		addConnections(startPtIndex1, currentList1, firstConnectionsList);
//    		System.out.println("firstConnectionsList="+firstConnectionsList);
    		
//        	System.out.println("second path");
    		ArrayList<ArrayList> secondConnectionsList = new ArrayList<ArrayList>();
    		int startPtIndex2 = sect*2+1;
    		ArrayList<Integer> currentList2 = new ArrayList<Integer>();
    		currentList2.add(startPtIndex2);
    		addConnections(startPtIndex2, currentList2, secondConnectionsList);
//    		System.out.println("secondConnectionsList="+secondConnectionsList);
    		
    		// now stitch together all combinations
    		int num=0, numRemoved=0;
			for(int j=0; j<secondConnectionsList.size(); j++) {
				ArrayList<Integer> secondList = secondConnectionsList.get(j);
				for(int i=0; i<firstConnectionsList.size();i++) {
					num += 1;
					ArrayList<Integer> firstList = firstConnectionsList.get(i);
					ArrayList<Integer> stitchedList = new ArrayList<Integer>();
        			for(int k= firstList.size()-1; k >=0; k--) stitchedList.add(firstList.get(k));
    				stitchedList.addAll(secondList);
/* this works!
    				if(linkedSectionsList.contains(stitchedList))
    					System.out.println(num+" is a Duplicate Here !!!!!!!!!!!!!!!!!!!!");
*/
    				// reverse the list so we can check that one too
    				ArrayList<Integer> reversedList = new ArrayList<Integer>();
    				for(int n=stitchedList.size()-1; n>=0; n--) reversedList.add(stitchedList.get(n));
    				
    				// now add if we don't already have this
    				if(!endToEndSectLinksList.contains(stitchedList) && !endToEndSectLinksList.contains(reversedList))
    					endToEndSectLinksList.add(stitchedList);
    				else
    					numRemoved += 1;
    			}
    		}
		
			int numNew = endToEndSectLinksList.size()-oldNum;
			/*    write out contents of the list
			System.out.println("\n"+numNew+" in list for "+
    				allFaultSectionPrefData.get(sect).getSectionName()+" (section "+sect+"), "+numRemoved+" removed as duplicates  ******************");
			for(int k=oldNum; k<endToEndSectLinksList.size(); k++) {
				System.out.println(k);
				ArrayList<Integer> list = endToEndSectLinksList.get(k);
				for(int l=0; l<list.size();l++)
					System.out.println(endPointNames[list.get(l)]);
			}
			*/
			oldNum = endToEndSectLinksList.size();
    	}
/*
        System.out.println("endToEndSectLinksList=");
        for(int i=0;i<endToEndSectLinksList.size(); i++)
        	System.out.println(i+"\t"+endToEndSectLinksList.get(i));
*/	
    }
    
    
    private void computeSectionClusters() {
    	sectionClusterList = new ArrayList<OldSectionCluster>();
    	// duplicate the following because it will get modified 
    	ArrayList<ArrayList<Integer>> tempEndToEndSectList = (ArrayList<ArrayList<Integer>>)endToEndSectLinksList.clone();

    	int clusterCounter=0;
    	while(tempEndToEndSectList.size() > 0) {
//System.out.println("Working on cluster "+clusterCounter);
//    		System.out.println("sectionClusterList.size()="+sectionClusterList.size()+";  tempEndToEndSectList.size()"+tempEndToEndSectList.size());
    		OldSectionCluster cluster = new OldSectionCluster();
    		tempEndToEndSectList = cluster.CreateCluster(tempEndToEndSectList, subSectionPrefDataList,minNumSubSectInRup);  // this removes the ones it takes from the list passed in
    		sectionClusterList.add(cluster);
    		clusterCounter +=1;
    	}
System.out.println("sectionClusterList.size()="+sectionClusterList.size());
    }
    
    

    private void testClusters() {
    	// make sure that each section endpoint is part of one and only one cluster
    	System.out.println("Testing clusters:");
    	boolean allGood = true;
//    	for(int i=0; i<numSectEndPts; i++) {
        for(int i=0; i<numSectEndPts; i++) {
    		int sum =0;
    		for(int j=0;j<this.sectionClusterList.size(); j++) {
//    		for(int j=0;j<6; j++) {
    			ArrayList<Integer> indices = sectionClusterList.get(j).getSectionIndicesInCluster();
//    			System.out.println(indices);
    			if(indices.contains(new Integer(i)))
    				sum+=1;
    		}
    		if(sum !=1) {
    			System.out.println("sectEndPt "+i+" exists in "+sum+" clusters");
    			allGood = false;
    		}
    	}
    	System.out.println("\tallGood="+allGood);
    }

    
    


    /*
    private void computeSectionClusters() {
    	
    	ArrayList<Integer> test = new ArrayList<Integer> ();
    	test.add(new Integer(2));
    	if(test.contains(new Integer(2))) System.out.println("It Works!!!!!!!!!!");
    	
    	sectionClusterList = new ArrayList<ArrayList<Integer>>();
    	// add the first end-to-end link as the first cluster
    	ArrayList<Integer> firstCluster = (ArrayList<Integer>)endToEndSectLinksList.get(0).clone();
    	sectionClusterList.add(firstCluster);
//    	System.out.println("endToEndSectLinksList.size()="+endToEndSectLinksList.size());
//    	System.out.println("endToEndSectLinksList.get(0)="+endToEndSectLinksList.get(0));
    	 
    	for(int i=1; i< endToEndSectLinksList.size();i++) {
//    		System.out.println("endToEndSectLinksList.get("+i+")="+endToEndSectLinksList.get(i));
    		boolean newCluster = true;
    		boolean done = false;
    		ArrayList<Integer> endToEndLink = endToEndSectLinksList.get(i);
    		// loop over clusters to see if this link is part of one (shares at least one section)
    		for(int j=0; j<sectionClusterList.size() && !done; j++) {
    			ArrayList<Integer> cluster = sectionClusterList.get(j);
    			// loop over sections in the link
    			for(int k=0; k<endToEndLink.size() && !done; k++) {
    				if(cluster.contains(endToEndLink.get(k))) { // if the section index is in this cluster add the link to the cluster
//    					System.out.println("Got one!");
    					for(int l=0; l<endToEndLink.size(); l++)
    						if (!cluster.contains(endToEndLink.get(l))) cluster.add(endToEndLink.get(l));
    					newCluster = false;
    					done = true;
    				}
    			}
    			
    		}
    		if(newCluster) sectionClusterList.add((ArrayList<Integer>)endToEndLink.clone());
    	}

		System.out.println("Num Clusters = "+sectionClusterList.size());
    	for(int cl=0;cl< sectionClusterList.size(); cl++)
    		System.out.println("\t"+cl+" has"+sectionClusterList.get(cl).size()+" sections");
    		
    	System.out.println("sectionClusterList=");
        for(int i=0;i<sectionClusterList.size(); i++)
        	System.out.println(i+"\t"+sectionClusterList.get(i));
 

    }
    */
    
    private void addConnections(Integer endPtID, ArrayList currentList, ArrayList<ArrayList> finalList) {
    	ArrayList<Integer> sectionConnections = sectionConnectionsList.get(endPtID);
    	
//    	System.out.println("Connections for "+endPtID+" ("+endPointNames[endPtID]+") are: ");
//    	for(int temp=0;temp<sectionConnections.size();temp++) System.out.println("\t"+sectionConnections.get(temp)+" ("+endPointNames[sectionConnections.get(temp).intValue()]+")");
    	
    	if(sectionConnections.size() == 0) {  // no more connections, so add it to the final list
    		finalList.add((ArrayList)currentList.clone());
    	//	System.out.println("\tDONE");
    	}
    	else {
    	//	System.out.println(sectionConnections.size()+" connections for "+this.endPointNames[endPtID]);
    		for(int i=0; i< sectionConnections.size(); i++) {
    			int connectedPtIndex = sectionConnections.get(i).intValue();
    			int otherPtIndex;
    			if(connectedPtIndex  % 2 != 0) // if the index is odd (last point)
    				otherPtIndex = connectedPtIndex-1;
    			else
    				otherPtIndex = connectedPtIndex+1;
    			
    			// check total direction change between 1st and this new section & skip if
    			int firstPt = ((Integer)currentList.get(0)).intValue();
    			double totalStrikeChange = Math.abs(sectionAngleDiffs[firstPt][connectedPtIndex]);
    			if(totalStrikeChange > maxTotStrikeChange) {
    				finalList.add((ArrayList)currentList.clone());
//    				System.out.println("NOTE - total strike became too large between "+endPointNames[firstPt]+" and "+endPointNames[connectedPtIndex]);
    				continue;
    			}
    			
    			// quit also if the list already has this point (two sections looping around on each other)
    			if(currentList.contains(new Integer(connectedPtIndex))) {
    				finalList.add((ArrayList)currentList.clone());
//    				System.out.println("NOTE - quit due to looping "+endPointNames[firstPt]+" and "+endPointNames[connectedPtIndex]);
    				continue;
    			}
    			ArrayList newCurrentList = (ArrayList) currentList.clone();
    			newCurrentList.add(connectedPtIndex);
    			newCurrentList.add(otherPtIndex);
    	//		System.out.println("\tadded "+endPointNames[otherPtIndex]+" and "+endPointNames[connectedPtIndex]+" to "+
    	//				endPointNames[endPtID]+"  TOTAL STRIKE CHANGE = "+totalStrikeChange);
    	//		counter+=1;
    	//		if(counter<100)
    			addConnections(otherPtIndex, newCurrentList, finalList);
    		}
    	}
    }

	
	private int getSectionIndexForEndPoint(int endPointIndex) {
		if(endPointIndex % 2 != 0) return (endPointIndex-1)/2;  // test to see if it's odd
		else return endPointIndex/2;
	}
	
	
	// Note that this produces erroneous zig-zag plot for traces that have multiple lats for a given lon 
	// (functions force x values to monotonically increase)
	public void plotAllTraces(double maxDist, double minAngle, double maxAngle) {
		for(int i=0;i<numSectEndPts;i++)
			for(int j=0;j<numSectEndPts;j++)
				if(sectionDistances[i][j] <= maxDist && i != j) 
					if(sectionAngleDiffs[i][j] >= minAngle && sectionAngleDiffs[i][j] <= maxAngle) {
						FaultTrace ftA = this.allFaultSectionPrefData.get(getSectionIndexForEndPoint(i)).getFaultTrace();
						FaultTrace ftB = this.allFaultSectionPrefData.get(getSectionIndexForEndPoint(j)).getFaultTrace();
//						if (allFaultSectionPrefData.get(indexB).getSectionName().equals("Burnt Mtn")) System.out.println("Burnt Mtn index ="+allFaultSectionPrefData.get(indexB).getFaultTrace().toString());
//						boolean flag=false; if (allFaultSectionPrefData.get(indexB).getSectionName().equals("Burnt Mtn")) flag = true;
						plotTraces(ftA, ftB);
					}
	}
	
	
	// Note that this produces erroneous zig-zag plot for traces that have multiple lats for a given lon 
	// (functions force x values to monotonically increase)
	public void plotAllSections(ArrayList<Integer> link) {
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
		double minLat=1000, maxLat=-1000, minLon=1000, maxLon=-1000;
		String name = new String();
		for(int j=0; j<link.size(); j+=2) {
			int sectIndex = getSectionIndexForEndPoint(link.get(j).intValue());
			FaultTrace ft = allFaultSectionPrefData.get(sectIndex).getFaultTrace();
			name += allFaultSectionPrefData.get(sectIndex).getSectionName() +"+";
			for(int l=0; l<ft.size();l++) {
				Location loc = ft.get(l);
				func.set(loc.getLongitude(), loc.getLatitude());
				if(loc.getLongitude()<minLon) minLon = loc.getLongitude();
				if(loc.getLongitude()>maxLon) maxLon = loc.getLongitude();
				if(loc.getLatitude()<minLat) minLat = loc.getLatitude();
				if(loc.getLatitude()>maxLat) maxLat = loc.getLatitude();
			}
		}
		func.setName(name);
		ArrayList funcs = new ArrayList();
		funcs.add(func);
		GraphiWindowAPI_Impl graph = new GraphiWindowAPI_Impl(funcs, "");  
		// make the axis range equal
		if((maxLat-minLat) < (maxLon-minLon)) maxLat = minLat  + (maxLon-minLon);
		else maxLon = minLon + (maxLat-minLat);
		graph.setAxisRange(minLon, maxLon, minLat, maxLat);

	}

	public void plotAllEndToEndLinks() {
		for(int i=0;i<endToEndSectLinksList.size();i++)
			plotAllSections(endToEndSectLinksList.get(i));
	}
	
	public void plotAllClusters() {
		for(int i=0;i<sectionClusterList.size();i++) {
			ArrayList<Integer> indices = sectionClusterList.get(i).getSectionIndicesInCluster();
			if(indices.size()>6)
				plotAllSections(indices);
		}
	}

	
	
	public void writeSectionEndpointDistances() {
		
		try{
			FileWriter fw = new FileWriter("/Users/field/workspace/OpenSHA/scratchJavaDevelopers/ned/rupsInFaultSystem/sectionEndpointDistances.txt");
			
			int num = numSectEndPts;
			String outputString = new String();
			outputString += "\t";
			for(int i=0;i<num;i++) outputString += endPointNames[i]+"\t";
			outputString += "\n";
			fw.write(outputString);
			/* */
			for(int i=0;i<num;i++) {
//				System.out.print(i);
				outputString = new String();
				outputString += endPointNames[i]+"\t";
				for(int j=0;j<num;j++) {
					String distString = new Double(Math.round(sectionDistances[i][j])).toString()+"\t";
					outputString += distString;
					if(sectionDistances[i][j] <= 5 && i != j) System.out.println(endPointNames[i]+"\t"+endPointNames[j]+"\t"+
							Math.round(sectionDistances[i][j])+"\t"+Math.round(sectionAngleDiffs[i][j]));
				}
				outputString += "\n";
				fw.write(outputString);
			}

			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}
		
//		System.out.print(output);

	}
	
	
	/**
	 * This computes the distance from each section endpoint to the closest distance on all other section, but
	 * only if that point on the second section is not an endpoint.  This will only keep those that are withing
	 * distThresh
	 */
	public void writeSectionDistances(double distThresh) {
		
		try{
			FileWriter fw = new FileWriter("/Users/field/workspace/OpenSHA/dev/scratch/ned/rupsInFaultSystem/sectionDistances.txt");
			
			int num = allFaultSectionPrefData.size();
			String outputString = new String();
			outputString += "Section Distances\n";
			for(int i=0;i<num;i++) {
				FaultSectionPrefData data1 = allFaultSectionPrefData.get(i);
				FaultTrace trace1 = data1.getFaultTrace();
				for(int j=i+1; j<num; j++) {
					FaultSectionPrefData data2 = allFaultSectionPrefData.get(j);
					FaultTrace trace2 = data2.getFaultTrace();
					
					double minDist = Double.MAX_VALUE;
					double d1 = LocationUtils.horzDistance(trace1.get(0), trace2.get(trace2.getNumLocations()-1));
					if(d1<minDist) minDist=d1;
					double d2 = LocationUtils.horzDistance(trace1.get(0), trace2.get(0));
					if(d2<minDist) minDist=d2;
					double d3 = LocationUtils.horzDistance(trace1.get(trace1.getNumLocations()-1), trace2.get(trace2.getNumLocations()-1));
					if(d3<minDist) minDist=d3;
					double d4 = LocationUtils.horzDistance(trace1.get(trace1.getNumLocations()-1), trace2.get(0));
					if(d4<minDist) minDist=d4;
				
					double minDist2 = trace2.getMinDistance(trace1, 1.0);
					
					if(minDist2<minDist-1.0 && minDist2<distThresh) {
						String string = data1.getSectionName()+"\t--->\t"+data2.getSectionName()+"\t"+minDist2+"\n";
						outputString += string;
						System.out.print(string);

					}
						
				}
				fw.write(outputString);
			}

			fw.close();
		}catch(Exception e) {
			e.printStackTrace();
		}

	}

	
	
	
	
	public void plotTraces(FaultTrace ft1, FaultTrace ft2) {
		ArbitrarilyDiscretizedFunc ft1_func = new ArbitrarilyDiscretizedFunc();
		ft1_func.setName(ft1.getName());
		ArbitrarilyDiscretizedFunc ft2_func = new ArbitrarilyDiscretizedFunc();
		ft2_func.setName(ft2.getName());
		double minLat=1000, maxLat=-1000, minLon=1000, maxLon=-1000;
		for(int l=0; l<ft1.size();l++) {
			Location loc = ft1.get(l);
			ft1_func.set(loc.getLongitude(), loc.getLatitude());
			if(loc.getLongitude()<minLon) minLon = loc.getLongitude();
			if(loc.getLongitude()>maxLon) maxLon = loc.getLongitude();
			if(loc.getLatitude()<minLat) minLat = loc.getLatitude();
			if(loc.getLatitude()>maxLat) maxLat = loc.getLatitude();
		}
		for(int l=0; l<ft2.size();l++) {
			Location loc = ft2.get(l);
			ft2_func.set(loc.getLongitude(), loc.getLatitude());
			if(loc.getLongitude()<minLon) minLon = loc.getLongitude();
			if(loc.getLongitude()>maxLon) maxLon = loc.getLongitude();
			if(loc.getLatitude()<minLat) minLat = loc.getLatitude();
			if(loc.getLatitude()>maxLat) maxLat = loc.getLatitude();
		}
		ArrayList ft_funcs = new ArrayList();
		ft_funcs.add(ft1_func);
		ft_funcs.add(ft2_func);
		GraphiWindowAPI_Impl sr_graph = new GraphiWindowAPI_Impl(ft_funcs, "");  
		// make the axis range equal
		if((maxLat-minLat) < (maxLon-minLon)) maxLat = minLat  + (maxLon-minLon);
		else maxLon = minLon + (maxLat-minLat);
		sr_graph.setAxisRange(minLon, maxLon, minLat, maxLat);
	}
	
	
    /**
     * This returns the change in strike direction in going from this azimuth1 to azimuth2,
     * where these azimuths are assumed to be defined between -180 and 180 degrees.
     * The output is between -180 and 180 degrees.
     * @return
     */
    private double getStrikeDirectionDifference(double azimuth1, double azimuth2) {
    	double diff = azimuth2 - azimuth1;
    	if(diff>180)
    		return diff-360;
    	else if (diff<-180)
    		return diff+360;
    	else
    		return diff;
     }

    /**
     * This reverses the given azimuth (assumed to be between -180 and 180 degrees).
     * The output is between -180 and 180 degrees.
     * @return
     */

    private double reverseAzimuth(double azimuth) {
    	if(azimuth<0) return azimuth+180;
    	else return azimuth-180;
     }
    
    
 	
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		long startTime=System.currentTimeMillis();
		OldCreateRupturesFromSections createRups = new OldCreateRupturesFromSections(10, 45, 60, 7, 2);
		ArrayList<ArrayList<Integer>> rupList = createRups.getRupList();
		System.out.println(rupList.get(0));
		int runtime = (int)(System.currentTimeMillis()-startTime)/1000;
		System.out.println("Run took "+runtime+" seconds");
//		createRups.plotAllClusters();
//		createRups.plotAllEndToEndLinks();
//		createRups.writeBurntMtTrace();
//		createRups.plotAllTraces(5, -45, 45);
//		createRups.writeSectionDistances();
		
		

	}
	

}
