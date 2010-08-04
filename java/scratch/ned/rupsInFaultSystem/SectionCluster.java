package scratch.ned.rupsInFaultSystem;

import java.util.ArrayList;
import java.util.HashMap;

import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;

/**
 * @author field
 *
 */
public class SectionCluster extends ArrayList<Integer> {
	
	ArrayList<FaultSectionPrefData> subSectionPrefDataList;
	ArrayList<Integer> allSubSectionsIdList = null;
	ArrayList<ArrayList<Integer>> subSectionConnectionsListList;
	ArrayList<ArrayList<Integer>> rupListIndices;			// elements here are subsection IDs
	int minNumSubSectInRup;
	int numRupsAdded;
	double maxAzimuthChange, maxTotAzimuthChange;
	double[][] subSectionAzimuths;
	
	public SectionCluster(ArrayList<FaultSectionPrefData> subSectionPrefDataList, int minNumSubSectInRup, 
			ArrayList<ArrayList<Integer>> subSectionConnectionsListList, double[][] subSectionAzimuths,
			double maxAzimuthChange, double maxTotAzimuthChange) {
		this.minNumSubSectInRup = minNumSubSectInRup;
		this.subSectionPrefDataList = subSectionPrefDataList;
		this.subSectionConnectionsListList = subSectionConnectionsListList;
		this.subSectionAzimuths = subSectionAzimuths;
		this.maxAzimuthChange = maxAzimuthChange;
		this.maxTotAzimuthChange = maxTotAzimuthChange;
	}
	
	
	/**
	 * This returns the number of subsections in the cluster
	 * @return
	 */
	public int getNumSubSections() {
		return this.size();
	}
	
	
	/**
	 * This returns the IDs of all the subsections in the cluster
	 * @return
	 */
	public ArrayList<Integer> getAllSubSectionsIdList() {
		if(allSubSectionsIdList==null) computeAllSubSectionsIdList();
		return allSubSectionsIdList;
	}
	
	
	private void computeAllSubSectionsIdList() {
		allSubSectionsIdList = new ArrayList<Integer>();
		for(int i=0; i<size();i++) allSubSectionsIdList.add(subSectionPrefDataList.get(get(i)).getSectionId());
	}
	
	
	public int getNumRuptures() {
		if(rupListIndices== null)  computeRupList();
//		return rupListIndices.size();
		return numRupsAdded;
	}
	
		
	public ArrayList<ArrayList<Integer>> getRuptures() {
//		return new ArrayList<ArrayList<Integer>>();
		/**/
		  if(rupListIndices== null)  computeRupList();
		  // now convert to holding subsection IDs
		  ArrayList<ArrayList<Integer>> rupList = new ArrayList<ArrayList<Integer>>();
		  for(int i=0;i<rupListIndices.size();i++) {
			  ArrayList<Integer> rup = rupListIndices.get(i);
			  ArrayList<Integer> newRup  = new ArrayList<Integer>();
			  for(int j=0;j<rup.size();j++)
				  newRup.add(subSectionPrefDataList.get(rup.get(j)).getSectionId());
			  rupList.add(newRup);
		  }
		  return rupList;
		  
	}
	
	public ArrayList<ArrayList<Integer>> getRupturesByIndices() {
		  if(rupListIndices== null)
			  computeRupList();
		  return rupListIndices;
	}

	
	int rupCounterProgress =1000000;
	int rupCounterProgressIncrement = 1000000;
	  
	
	private void addRuptures(ArrayList<Integer> list) {
		int subSectIndex = list.get(list.size()-1);
		int lastSubSect;
		if(list.size()>1)
			lastSubSect = list.get(list.size()-2);
		else
			lastSubSect = -1;   // bogus index because subSectIndex is first in list
		
		// loop over branches at the present subsection
		ArrayList<Integer> branches = subSectionConnectionsListList.get(subSectIndex);
		for(int i=0; i<branches.size(); i++) { 
			Integer newSubSect = branches.get(i);

			// avoid looping back on self or to previous subSection
			if(list.contains(newSubSect) || newSubSect == lastSubSect) continue;
			
			// debugging stuff:
/*			if(list.size()>1)
				System.out.println("lastSubSect=\t"+lastSubSect+"\t"+this.subSectionPrefDataList.get(lastSubSect).getName());
			System.out.println("subSectIndex=\t"+subSectIndex+"\t"+this.subSectionPrefDataList.get(subSectIndex).getName());
			System.out.println("newSubSect=\t"+newSubSect+"\t"+this.subSectionPrefDataList.get(newSubSect).getName());
*/	
			/*
			// check the azimuth change
			if(list.size()>2) { // make sure there are enough points to compute an azimuth change (change 2 to 3 to get previousAzimuth below)
				double newAzimuth = subSectionAzimuths[subSectIndex][newSubSect];
				double lastAzimuth = subSectionAzimuths[lastSubSect][subSectIndex];
//				double previousAzimuth = subSectionAzimuths[list.get(list.size()-3)][lastSubSect];
				double newLastAzimuthDiff = Math.abs(getAzimuthDifference(newAzimuth,lastAzimuth));
//				double newPreviousAzimuthDiff = Math.abs(getAzimuthDifference(newAzimuth,previousAzimuth));
//				System.out.println("newAzimuth=\t"+(int)newAzimuth+"\t"+subSectIndex+"\t"+newSubSect);
//				System.out.println("lastAzimuth=\t"+(int)lastAzimuth+"\t"+lastSubSect+"\t"+subSectIndex);
//				System.out.println("previousAzimuth=\t"+(int)previousAzimuth+"\t"+list.get(list.size()-3)+"\t"+lastSubSect);
//				System.out.println("newLastAzimuthDiff=\t"+(int)newLastAzimuthDiff);
//				System.out.println("newPreviousAzimuthDiff=\t"+(int)newPreviousAzimuthDiff);

//				if(newLastAzimuthDiff<maxAzimuthChange && newPreviousAzimuthDiff>=maxAzimuthChange) {
				if(newLastAzimuthDiff<maxAzimuthChange) {
//					ArrayList<Integer> lastRup = rupListIndices.get(rupListIndices.size()-1);
//					if(lastRup.get(lastRup.size()-1) == lastSubSect) {
						//stop it from going down bad branch, and remove previous rupture since it headed this way
//						System.out.println("removing: "+rupListIndices.get(rupListIndices.size()-1));
//						rupListIndices.remove(rupListIndices.size()-1);
//						numRupsAdded -= 1;
						continue;						
//					}
				}
			}
*/
			ArrayList<Integer> newList = (ArrayList<Integer>)list.clone();
			newList.add(newSubSect);
			if(newList.size() >= minNumSubSectInRup)  {// it's a rupture
				rupListIndices.add(newList);
				numRupsAdded += 1;
				// show progress
				if(numRupsAdded >= rupCounterProgress) {
					System.out.println(numRupsAdded);
					rupCounterProgress += rupCounterProgressIncrement;
				}
//				System.out.println("adding: "+newList);
				// Debugging exist after 100 ruptures
//				if(numRupsAdded>100) return;
			}
			
			// Iterate
			addRuptures(newList);
//				  System.out.println("\tadded "+this.subSectionPrefDataList.get(subSect).getName());
		}
	}

	
	private void computeRupList() {
//		System.out.println("Cluster: "+this);
		rupListIndices = new ArrayList<ArrayList<Integer>>();
		// loop over every subsection as the first in the rupture
		int progress = 0;
		int progressIncrement = 5;
		numRupsAdded=0;
		System.out.print("% Done:\t");
//		for(int s=0;s<size();s++) {
		for(int s=0;s<1;s++) {	// Debugging: only compute ruptures from first subsection
			// show progress
			if(s*100/size() > progress) {
				System.out.print(progress+"\t");
				progress += progressIncrement;
			}
			ArrayList<Integer> subSectList = new ArrayList<Integer>();
			int subSectIndex = get(s);
			subSectList.add(subSectIndex);
			addRuptures(subSectList);
//			System.out.println(rupList.size()+" ruptures after subsection "+s);
		}
		System.out.print("\n");

		// now filter out duplicates (which would exist in reverse order) & change from containing indices to IDs
		ArrayList<ArrayList<Integer>> newRupList = new ArrayList<ArrayList<Integer>>();
		for(int r=0; r< rupListIndices.size();r++) {
			ArrayList<Integer> rup = rupListIndices.get(r);
			ArrayList<Integer> reverseRup = new ArrayList<Integer>();
			for(int i=rup.size()-1;i>=0;i--) reverseRup.add(rup.get(i));
			if(!newRupList.contains(reverseRup)) { // keep if we don't already have
				newRupList.add(rup);
			}
		}
		rupListIndices = newRupList;
		numRupsAdded = rupListIndices.size();
	}
	
	  
	  public void writeRuptureSubsectionNames(int index) {
		  ArrayList<Integer> rupture = rupListIndices.get(index);
		  System.out.println("Rutpure "+index);
		  for(int i=0; i<rupture.size(); i++ ) {
			  System.out.println("\t"+this.subSectionPrefDataList.get(rupture.get(i)).getName());
		  }
		  
	  }
	  
	    /**
	     * This returns the change in strike direction in going from this azimuth1 to azimuth2,
	     * where these azimuths are assumed to be defined between -180 and 180 degrees.
	     * The output is between -180 and 180 degrees.
	     * @return
	     */
	    public static double getAzimuthDifference(double azimuth1, double azimuth2) {
	    	double diff = azimuth2 - azimuth1;
	    	if(diff>180)
	    		return diff-360;
	    	else if (diff<-180)
	    		return diff+360;
	    	else
	    		return diff;
	     }

}