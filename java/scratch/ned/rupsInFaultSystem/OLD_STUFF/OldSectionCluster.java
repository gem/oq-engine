package scratch.ned.rupsInFaultSystem.OLD_STUFF;

import java.util.ArrayList;
import java.util.HashMap;

import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;


/**
 * TO DO
 * 
 * The equals() method of MultipleSectionRupIDs will break down if there is a multi-path for the 
 * rupture with the same endpoints and num sections involved.
 * @author field
 *
 */
public class OldSectionCluster {
	
	ArrayList<ArrayList<Integer>> localEndToEndSectLinksList;
	ArrayList<Integer> allSectEndPtsInCluster;
	ArrayList<ArrayList<FaultSectionPrefData>> subSectionPrefDataList;
	ArrayList<Integer> allSubSectionsIdList;
	ArrayList<ArrayList<Integer>> rupList;
	int minNumSubSectInRup;
	
	/**
	 * 
	 * @return
	 */
	public ArrayList<Integer> getSectionIndicesInCluster() {
		ArrayList<Integer> sectIndices = new ArrayList<Integer>();
		for(int i=0; i<localEndToEndSectLinksList.size();i++) {
			ArrayList<Integer> endToEndLink = localEndToEndSectLinksList.get(i);
//			System.out.println("endToEndLink="+endToEndLink);
			for(int j=0; j< endToEndLink.size(); j++) {
				Integer linkInt = endToEndLink.get(j);
				if(!sectIndices.contains(linkInt)) // keep out duplicates
					sectIndices.add(linkInt);
			}
		}
//		System.out.println("sectIndices="+sectIndices);
		return sectIndices;
	}
	
	
	/**
	 * 
	 * @param endToEndSectLinksList
	 * @return
	 */
	public ArrayList<ArrayList<Integer>> CreateCluster(ArrayList<ArrayList<Integer>> endToEndSectLinksList, 
			ArrayList<ArrayList<FaultSectionPrefData>> subSectionPrefDataList, int minNumSubSectInRup) {
		
		this.subSectionPrefDataList = subSectionPrefDataList;
		this.minNumSubSectInRup = minNumSubSectInRup;
		
		// make hashmap of endToEndSectLinksList to make it easier to remove those used from what's passed back
		HashMap<Integer, ArrayList<Integer>> endToEndLinkdListHashMap = new HashMap<Integer, ArrayList<Integer>>();
		for(int i=0;i<endToEndSectLinksList.size();i++)
			endToEndLinkdListHashMap.put(new Integer(i), endToEndSectLinksList.get(i));
		
		allSectEndPtsInCluster = new ArrayList<Integer>();
		
		ArrayList<Integer> linkIndicesToKeep = new ArrayList<Integer>();
		
		// add the first endToEndLink
		allSectEndPtsInCluster.addAll(endToEndSectLinksList.get(0));
		linkIndicesToKeep.add(0);
		
		// now find the indices of the others
		for(int i=1; i<endToEndSectLinksList.size(); i++) { // need double loop to make all connections
//System.out.println("\tlink "+i+" of "+endToEndSectLinksList.size());
			for(int j=1; j<endToEndSectLinksList.size(); j++) {
				ArrayList<Integer> endToEndLink = endToEndSectLinksList.get(j);
				for(int k=0; k<endToEndLink.size(); k++) {
					if(allSectEndPtsInCluster.contains(endToEndLink.get(k))) { // it's part of this cluster
						if(!linkIndicesToKeep.contains(j)) {  // make sure we don't already have it
							linkIndicesToKeep.add(j);
							for(int l=0;l<endToEndLink.size();l++) {
								Integer linkInt = endToEndLink.get(l);
								if(!allSectEndPtsInCluster.contains(linkInt)) // add it only if it's not already there
									allSectEndPtsInCluster.add(linkInt);								
							}
						}
						break;  // exit loop over endToEndLink Integers
					}
				}
			}	
		}
		
		localEndToEndSectLinksList = new ArrayList<ArrayList<Integer>>();
		for(int i=0; i<linkIndicesToKeep.size();i++)
			localEndToEndSectLinksList.add(endToEndSectLinksList.get(linkIndicesToKeep.get(i).intValue()));
//		System.out.println("localEndToEndSectLinksList.size()="+localEndToEndSectLinksList.size());
		
		ArrayList<ArrayList<Integer>> unusedEndToEndSectLinksList = new ArrayList<ArrayList<Integer>>();
		for(int i=1; i<endToEndSectLinksList.size();i++)
			if(!linkIndicesToKeep.contains(i))
				unusedEndToEndSectLinksList.add(endToEndLinkdListHashMap.get(new Integer(i)));
		
		// compute subsection data
		computeSubsectionData();
		
		return unusedEndToEndSectLinksList;
	}
	
	/**
	 * This returns the number of subsections in the cluster
	 * @return
	 */
	public int getNumSubSections() {
		return allSubSectionsIdList.size();
	}
	
	/**
	 * This returns the IDs of all the subsections in the cluster
	 * @return
	 */
	public ArrayList<Integer> getAllSubSectionsIdList() {
		return allSubSectionsIdList;
	}
	
	
	private void computeSubsectionData() {
		allSubSectionsIdList = new ArrayList<Integer>();
		int sectionIndex;
		for(int i=0; i< allSectEndPtsInCluster.size();i+=2) {
			sectionIndex = allSectEndPtsInCluster.get(i).intValue()/2; // convert from endpoint index to section index
//			System.out.println("sectionIndex="+sectionIndex);
			ArrayList<FaultSectionPrefData> prefSubsectDataForSection = subSectionPrefDataList.get(sectionIndex);
			for(int k=0; k< prefSubsectDataForSection.size();k++) {
//				System.out.println(prefSubsectDataForSection.get(k).getSectionId());
				allSubSectionsIdList.add(prefSubsectDataForSection.get(k).getSectionId());
			}
		}
	}
	
	public ArrayList<ArrayList<Integer>> getRuptures() {
		  if(rupList== null)
			  computeRupList();
		  return rupList;
	}

	
	
	private void computeRupList() {
		
		int sectionIndex;

		// Make HashMap giving a unique integer for each subsection ID, where the key is the latter
		HashMap<Integer, Integer> indexForSubsectionID = new HashMap<Integer, Integer>();
		int index=0;
//		ArrayList<Integer> keys = new ArrayList<Integer>();
		ArrayList<Integer> sectIndicesInCluster = getSectionIndicesInCluster();
		for(int i=0; i<sectIndicesInCluster.size();i+=2) {
			sectionIndex = sectIndicesInCluster.get(i).intValue()/2; // convert from endpoint index to section index
			ArrayList<FaultSectionPrefData> prefSubsectDataForSection = subSectionPrefDataList.get(sectionIndex);
			for(int k=0; k< prefSubsectDataForSection.size();k++) {
				Integer key = prefSubsectDataForSection.get(k).getSectionId();
//				keys.add(key);
				indexForSubsectionID.put(key, index); // is this the correct order?
				index +=1;
			}
		}
		
		/* check this hashmap
		System.out.println("key and value for indexForSubsectionID hashmap:");
		for(int i=0; i<keys.size();i++)
			System.out.println("\t"+keys.get(i)+"\t"+indexForSubsectionID.get(keys.get(i))); // the key should be this index
		*/
		// create a 2D array of ArrayList<ArrayList<Integer>> that will hold the ruptures for each combination
		// of subsection endpoints
		//int[][] numSubsectInRup = new int[indexForSubsectionID.size()][indexForSubsectionID.size()];
		int numSS = indexForSubsectionID.size();
		ArrayList<ArrayList<Integer>>[][] rupsForSubSectEndpoints = new ArrayList[numSS][numSS];
		
		
		rupList = new ArrayList<ArrayList<Integer>>();
		// loop over each end-to-end link list
		for(int l=0; l<localEndToEndSectLinksList.size();l++) {
//System.out.println("\tWorking on Rups for link "+l+" of "+localEndToEndSectLinksList.size());
			// get the list of subsection IDs for this end-to-end link
			ArrayList<Integer> endToEndLink = localEndToEndSectLinksList.get(l);
			ArrayList<Integer> endToEndSubsectionIDs = new ArrayList<Integer>();
			for(int i=0; i< endToEndLink.size();i+=2) {
				sectionIndex = endToEndLink.get(i).intValue()/2; // convert from endpoint index to section index
				ArrayList<FaultSectionPrefData> prefSubsectDataForSection = subSectionPrefDataList.get(sectionIndex);
				for(int k=0; k< prefSubsectDataForSection.size();k++) {
					endToEndSubsectionIDs.add(prefSubsectDataForSection.get(k).getSectionId());
				}
			}
			// now create each MultipleSectionRupIDs object
			for(int numSubSectInRup=minNumSubSectInRup;numSubSectInRup<=endToEndSubsectionIDs.size();numSubSectInRup++) {
				for(int s=0;s<endToEndSubsectionIDs.size()-numSubSectInRup+1;s++) {
//					if(l==0) System.out.println("s="+s+"\tnumSubSectInRup="+numSubSectInRup);
					ArrayList<Integer> id_list = new ArrayList<Integer>();
					for(int t=0;t<numSubSectInRup;t++) id_list.add(endToEndSubsectionIDs.get(s+t));
					
					// now we need to determine if we already have this rupture
					int firstIndex = indexForSubsectionID.get(id_list.get(0));
					int lastIndex  = indexForSubsectionID.get(id_list.get(id_list.size()-1));
					
					// get the list of  rupts from the HashMap
					ArrayList<ArrayList<Integer>> rups = rupsForSubSectEndpoints[firstIndex][lastIndex];
					if(rups == null){ // check this first for speed
						rupList.add(id_list);
						ArrayList<ArrayList<Integer>> newList = new ArrayList<ArrayList<Integer>>();
						newList.add(id_list);
						rupsForSubSectEndpoints[firstIndex][lastIndex] = newList;
						rupsForSubSectEndpoints[lastIndex][firstIndex] = newList;
						continue; // or break?
					}
					// create reverse order list since we will need to check that as well
					ArrayList<Integer> id_list_reversed = new ArrayList<Integer>();
					for(int n=id_list.size()-1;n>=0;n--) id_list_reversed.add(id_list.get(n));
					if(!rups.contains(id_list) && !rups.contains(id_list_reversed)) {
						rupList.add(id_list);
						ArrayList<ArrayList<Integer>> list = rupsForSubSectEndpoints[firstIndex][lastIndex];
						list.add(id_list);
					}
					//else do nothing
					
					// OLD WAY
//					if(!rupList.contains(id_list)) rupList.add(id_list);
					
				}
			}
/*
			int predNum = endToEndSubsectionIDs.size()*(endToEndSubsectionIDs.size()+1)/2;
			if(l==0) {
				System.out.println("localEndToEndSectLinksList.size()="+localEndToEndSectLinksList.size());
				System.out.println("endToEndLink="+endToEndLink);
				System.out.println("endToEndSubsectionIDs="+endToEndSubsectionIDs);
				System.out.println("endToEndSubsectionIDs.size()="+endToEndSubsectionIDs.size());
				System.out.println("numRup = "+rupList.size()+"\t"+predNum);  // only check the first since none for this are duplicates
			}
*/
		}
	}
	
	
}