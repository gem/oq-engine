/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final;

import java.util.ArrayList;
import java.util.Iterator;

import org.opensha.commons.calc.FaultMomentCalc;
import org.opensha.refFaultParamDb.vo.FaultSectionPrefData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.SegRateConstraint;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.SegmentTimeDepData;
import org.opensha.sha.faultSurface.SimpleFaultData;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;

/**
 * @author Vipin Gupta and Ned Field
 *
 */
public class FaultSegmentData implements java.io.Serializable {
	private ArrayList sectionToSegmentData;
	
	 /* The following is an ArrayList of ArrrayLists of SimpleFaultData 
	    (same as sectionToSegmentData except the fact that this contains 
	    ArrayList of SimpleFaultData instead of FaultSectionPrefData)*/
	private ArrayList simpleFaultDataList;
	private boolean aseisReducesArea;
	private double totalArea, totalMoRate, totalMoRateIgnoringAseis, totalLength;
	private double[] segArea, segOrigArea, segLength, segMoRate, segMoRateIgnoringAseis, segSlipRate, segSlipRateStdDev; 
	private String[] segName, sectionsInSegString;
	private String faultName;
	private ArrayList<SegRateConstraint> segRates;
	private ArrayList<SegmentTimeDepData> segTimeDepDataList;

	
	/**
  	 * Description: This class contains data for one or more contiguous fault segments, 
  	 * where each segment is composed of one or more contiguous fault sections 
  	 * (or FaultSectionPrefData objects).  This class also provides various derived data.
  	 * Note that areas (or slip rates if aseisReducesArea is false)  will be reduced by any 
  	 * non-zero fault-section aseimicity factors; the same is true for any values derived 
  	 * from these.  Segment slip rates represent a weight-average over the sections, where
  	 * the weights are section areas (and aseismicity factors are applied as specified).
  	 * All data provided in the get methods are in SI units, which generally differs from the
  	 * units in the input.
  	 * 
  	 * This has special treatment for the San Jacinto and Elsinore faults, where the overlapping sections are
  	 * removed when creating the combined gridded surface.  Specifically, the sections containing "stepover" in the
  	 * name are not included if both stepovers are included in the list of segments.  This only influences what's
  	 * returned from the getCombinedGriddedSurface(*) methods.
  	 * 
  	 * @param sectionToSegmentData - an ArrayList containing N ArrayLists (one for each segment), 
  	 * where the arrayList for each segment contains some number of FaultSectionPrefData objects.
  	 * It is assumed that these are in proper order such that concatenating the FaultTraces will produce
  	 * a total FaultTrace with locations in the proper order.
  	 * @param aseisReducesArea - if true apply asiesmicFactor as reduction of area, otherwise it reduces slip rate
  	 * @
  	 */
	public FaultSegmentData(ArrayList sectionToSegmentData, String[] segNames, boolean aseisReducesArea, 
			String faultName, ArrayList<SegRateConstraint> segRateConstraints,
			ArrayList<SegmentTimeDepData> segTimeDepDataList) {
		//if(recurInterval!=null && (recurInterval.length!=sectionToSegmentData.size()))
			//	throw new RuntimeException ("Number of recurrence intervals should  equal  number of segments");
		this.segTimeDepDataList = segTimeDepDataList;
		this.segRates = segRateConstraints;
		this.faultName = faultName;
		this.sectionToSegmentData = sectionToSegmentData;	
		this.aseisReducesArea = aseisReducesArea;
		calcAll();
		if(segNames==null) this.segName = this.sectionsInSegString;
		else this.segName = segNames;
	}
	
	/**
	 * an ArrayList containing N ArrayLists (one for each segment), 
  	 * where the arrayList for each segment contains some number of FaultSectionPrefData objects.
  	 * It is assumed that these are in proper order such that concatenating the FaultTraces will produce
  	 * a total FaultTrace with locations in the proper order.
  	 * 
	 * @return
	 */
	public ArrayList getSectionToSegmentData() {
		return this.sectionToSegmentData;
	}
	
	/**
	 * This returns the name of the fault.
	 * @return
	 */
	public String getFaultName() {
		return faultName;
	}
	
	/**
	 * Get the total area of all segments combined (note that this 
	 * is reduced by any non-zero aseismicity factors if aseisReducesArea is true)
	 * @return area in SI units (meters squared)
	 */
	public double getTotalArea() {
		return totalArea;
	}
	
	/**
	 * Get the number of segments in this model
	 * @return
	 */
	public int getNumSegments() {
		return sectionToSegmentData.size();
	}
	
	/**
	 * Get segment area by index - SI units (note that this is reduce by any 
	 * non-zero aseismicity factors if aseisReducesArea is true)
	 * @param index
	 * @return area in SI units (meters squared) 
	 */
	public double getSegmentArea(int index) {
		return segArea[index];
	}
	
	/**
	 * Get original segment area by index - SI units (note that this is NOT reduce by any 
	 * aseismicity factors)
	 * @param index
	 * @return area in SI units (meters squared) 
	 */
	public double getOrigSegmentArea(int index) {
		return segOrigArea[index];
	}
	
	
	
	/**
	 * Get original segment down-dip-width - SI units (note that this is NOT reduce by any 
	 * aseismicity factors)
	 * @param index
	 * @return down dip width in SI units (meters) 
	 */
	public double getOrigSegmentDownDipWidth(int index) {
		return segOrigArea[index]/segLength[index];
	}
	
	
	/**
	 * Get segment length by index.  Note that this is not reduced if aseisReducesArea.
	 * @param index
	 * @return length in SI units (meters)
	 */
	public double getSegmentLength(int index) {
		return this.segLength[index];
	}
	
	/**
	 * This returns the average aseismcity factor for the ith segment
	 * @param index
	 * @return
	 */
	public double getAveSegAseisFactor(int index) {
		return 1.0 - segMoRate[index]/segMoRateIgnoringAseis[index];
	}
	
	/**
	 * Get total length of all segments combined.    Note that this is not reduced if aseisReducesArea.
	 * 
	 * @return length in SI units (meters)
	 */
	public double getTotalLength() {
		return this.totalLength;
	}
	
	/**
	 * Get segment slip rate by index (note that this is reduce by any non-zero 
	 * aseismicity factors if aseisReducesArea is false)
	 * @param index
	 * @return slip rate in SI units (m/sec)
	 */
	public double getSegmentSlipRate(int index) {
		return segSlipRate[index];
	}
	
	/**
	 * Get Standard deviation for the slip rate by index
	 * @param index
	 * @return
	 */
	public double getSegSlipRateStdDev(int index) {
		return this.segSlipRateStdDev[index];
	}
	
	/**
	 * Get Time Dependent data for specified segment index
	 * 
	 * @param index
	 * @return
	 */
	public SegmentTimeDepData getSegTimeDependentData(int index) {
		return this.segTimeDepDataList.get(index);
	}
	
	public double getSegCalYearOfLastEvent(int index) {return segTimeDepDataList.get(index).getLastEventCalendarYr(); }
	
	public double getSegAperiodicity(int index) {return segTimeDepDataList.get(index).getAperiodicity(); }
	
	public double getSegAveSlipInLastEvent(int index) {return segTimeDepDataList.get(index).getSlip(); }
	
	/**
	 * Get total ave slip rate - wt averaged by area (note that this is reduce by  
	 * any non-zero aseismicity factors if aseisReducesArea is false)
	 * @param index
	 * @return slip rate in SI units (m/sec)
	 */
	public double getTotalAveSlipRate() {
		return totalMoRate/(totalArea*FaultMomentCalc.SHEAR_MODULUS);
	}
	
	/**
	 * Computes the mean recur interval for a segment (as 1/getSegRateMean(segIndex)). 
	 * 
	 * @param index
	 * @return recur int in years
	 */
	public double getRecurInterval(int segIndex) {
		ArrayList<SegRateConstraint> segmentConstraints = getSegRateConstraints(segIndex);
		if(segmentConstraints.size()==0) return Double.NaN;
		else {
			SegRateConstraint meanSegmentConstraint = SegRateConstraint.getWeightMean(segmentConstraints);
			return 1.0/meanSegmentConstraint.getMean();
		}
	}

	/**
	 * Get the  rates for the sepcified segment index. Returns an empty arrayList in case there
	 * are no rates for this segment.
	 *  
	 * @param index
	 * @return
	 */
	public ArrayList<SegRateConstraint> getSegRateConstraints(int index) {
		ArrayList<SegRateConstraint> segmentConstraints = new ArrayList<SegRateConstraint>();
		for(int i=0; segRates!=null && i<segRates.size(); ++i) {
			if(segRates.get(i).getSegIndex()==index) segmentConstraints.add(segRates.get(i));
		}
		return segmentConstraints;
	}
	
	/**
	 * This returns the standard deviation of the mean segment rate (wt averaged if more than
	 * one constraint on the segment).  
	 * 
	 * @param index
	 * @return recur int in years
	 */
	public double getSegRateStdDevOfMean(int index) {
		ArrayList<SegRateConstraint> segmentConstraints = getSegRateConstraints(index);
		if(segmentConstraints.size()==0) return Double.NaN;
		else {
			SegRateConstraint meanSegmentConstraint = SegRateConstraint.getWeightMean(segmentConstraints);
			return meanSegmentConstraint.getStdDevOfMean();
		}
	}
	
	/**
	 * This returns the mean segment rate (wt averaged if more than
	 * one constraint on the segment).  
	 * 
	 * @param index
	 * @return recur int in years
	 */
	public double getSegRateMean(int index) {
		ArrayList<SegRateConstraint> segmentConstraints = getSegRateConstraints(index);
		if(segmentConstraints.size()==0) return Double.NaN;
		else {
			SegRateConstraint meanSegmentConstraint = SegRateConstraint.getWeightMean(segmentConstraints);
			return meanSegmentConstraint.getMean();
		}
	}
	
	/**
	 * This returns the lower 95% confidence of segment rate (highest value is returned if more than
	 * one value on the segment).  
	 * 
	 * @param index
	 */
	public double getSegLower95Conf(int index) {
		ArrayList<SegRateConstraint> segmentConstraints = getSegRateConstraints(index);
		if(segmentConstraints.size()==0) return Double.NaN;
		else {
			double lower95Conf = Double.MIN_VALUE;
			for(int i=0; i<segmentConstraints.size(); ++i)
				if(segmentConstraints.get(i).getLower95Conf()>lower95Conf)
					lower95Conf = segmentConstraints.get(i).getLower95Conf();
			return lower95Conf;
		}
	}
	
	/**
	 * This returns the upper 95% confidence of segment rate (lowest value is returned if more than
	 * one value on the segment).  
	 * 
	 * @param index
	 */
	public double getSegUpper95Conf(int index) {
		ArrayList<SegRateConstraint> segmentConstraints = getSegRateConstraints(index);
		if(segmentConstraints.size()==0) return Double.NaN;
		else {
			double upper95Conf = Double.MAX_VALUE;
			for(int i=0; i<segmentConstraints.size(); ++i)
				if(segmentConstraints.get(i).getUpper95Conf()<upper95Conf)
					upper95Conf = segmentConstraints.get(i).getUpper95Conf();
			return upper95Conf;
		}
	}
	
	/**
	 * Computes the standard deviation of the mean recur interval for a segment 
	 * (using standard error propagation from getSegRateStdDevOfMean and getSegRateMean).  
	 * 
	 * @param index
	 * @return recur int in years
	 */
	public double getRecurIntervalSigma(int index) {
		ArrayList<SegRateConstraint> segmentConstraints = getSegRateConstraints(index);
		if(segmentConstraints.size()==0) return Double.NaN;
		else {
			SegRateConstraint meanSegmentConstraint = SegRateConstraint.getWeightMean(segmentConstraints);
			return meanSegmentConstraint.getStdDevOfMean()/Math.pow(meanSegmentConstraint.getMean(),2);
		}
	}
	/**
	 * Get the segment Rates
	 * 
	 * @return
	 */
	public ArrayList<SegRateConstraint> getSegRateConstraints() {
		return this.segRates;
	}
	
	/**
	 * Get segment moment rate by index (note that this 
	 * is reduce by any non-zero aseismicity factors)
	 * @param index
	 * @return moment rate in SI units
	 */
	public double getSegmentMomentRate(int index) {
		return segMoRate[index];
	}
	
	/**
	 * Get total Moment rate for all segments combined (note that this 
	 * is reduce by any non-zero aseismicity factors)
	 * @return total moment rate in SI units
	 */
	public double getTotalMomentRate() {
		return totalMoRate;
	}
	
	/**
	 * Get the average aseismicity factor (computed as final total moment rate
	 * divided by original total moment rate)
	 * @return total moment rate in SI units
	 */
	public double getTotalAveAseismicityFactor() {
		double aseisFactor =  1- totalMoRate/totalMoRateIgnoringAseis;
		if(aseisFactor<0) aseisFactor=0;
		return aseisFactor;
	}

	/**
	 * Get segment name by index
	 * @param index
	 * @return
	 */
	public String getSegmentName(int index) {
		return this.segName[index];
	}
	
	/**
	 * Get segment name as a concatenated String of section names by index
	 * @param index
	 * @return
	 */
	public String getSectionsInSeg(int index) {
		return this.sectionsInSegString[index];
	}
	
	/**
	 * Get an array of all segment names
	 * @return
	 */
	public String[] getSegmentNames() {
		return this.segName;
	}
	
	
	/**
	 * Get a list of FaultSectionPrefData for selected fault model 
	 * (Not sure if this is the best place for this because the info 
	 * can be accessed from a returned FaultSegmentData object)
	 * @param faultModel
	 * @param deformationModelId
	 * @return
	 */
	public ArrayList getPrefFaultSectionDataList() {
		ArrayList faultSectionList = new ArrayList();
		for(int i=0; i<sectionToSegmentData.size(); ++i) {
			ArrayList prefDataList = (ArrayList)sectionToSegmentData.get(i);
			faultSectionList.addAll(prefDataList);
		}
		return faultSectionList;
	}
	
	
	/**
	 * Get StirlingGriddedSurface for ALL Segments. 
	 * It stitches together the segments and returns the resulting surface.
	 * It changes the DDW with the user provided increase factor
	 *  
	 * 
	 * @return
	 */
	public StirlingGriddedSurface getCombinedGriddedSurface(double gridSpacing, double increaseDDW_Factor) {		
		int segIndices[] = new int[this.getNumSegments()];
		for(int i=0; i<segIndices.length; ++i) segIndices[i] = i;
		return getCombinedGriddedSurface(segIndices, gridSpacing, increaseDDW_Factor);
		
	}
	
	/**
	 * Get StirlingGriddedSurface for selected Segment indices. 
	 * It stitches together the segments and returns the resulting surface.
	 * It changes the DDW with the user provided increase factor
	 *  
	 * @param segIndex List of Segment index to be included in the surface. The indices can have value from 0 to (getNumSegments()-1)
	 * @return
	 */
	public StirlingGriddedSurface getCombinedGriddedSurface(int []segIndex, double gridSpacing, double increaseDDW_Factor) {
		ArrayList<SimpleFaultData> simpleFaultDataCloneList = new ArrayList<SimpleFaultData>();
		int lastSegmentIndex = getNumSegments()-1;
		
		// determine whether stepover needs to be fixed
		boolean fixStepOver = false;
		if(faultName.equals("San Jacinto") || faultName.equals("Elsinore"))
			for(int i=0; i<segIndex.length-1; ++i) 
				if(segIndex[i] == 1 && segIndex[i+1] == 2) fixStepOver = true;  // both segments 1 & 2 used
		
		// undo fix if unsegmented model was chosen
		if(fixStepOver) {
			int numSectionsOnSeg1 = ((ArrayList)this.simpleFaultDataList.get(2)).size();
			if(numSectionsOnSeg1 == 1) fixStepOver = false;
		}
		
		
		for(int i=0; i<segIndex.length; ++i) {
			if(segIndex[i]<0 || segIndex[i]>lastSegmentIndex) throw new RuntimeException ("Segment indices should can have value from  0 to "+lastSegmentIndex);
			
			ArrayList<SimpleFaultData> sectionData = (ArrayList)this.simpleFaultDataList.get(segIndex[i]);
			for(int index=0; index<sectionData.size(); ++index) {
				SimpleFaultData simpleFaultDataClone = sectionData.get(index).clone();
				simpleFaultDataClone.setLowerSeismogenicDepth(simpleFaultDataClone.getUpperSeismogenicDepth() +
						(simpleFaultDataClone.getLowerSeismogenicDepth() -simpleFaultDataClone.getUpperSeismogenicDepth())* increaseDDW_Factor);
				
				// if fixStepOver, then skip second section (index=1) of first segment and first section (index=0) of second segment
				if(fixStepOver && segIndex[i]==1 && index == 1) continue;
				if(fixStepOver && segIndex[i]==2 && index == 0) continue;
				
				simpleFaultDataCloneList.add(simpleFaultDataClone);
			}
		}
		return  new StirlingGriddedSurface(simpleFaultDataCloneList, gridSpacing);
	}
	
	
	/**
	 * Get StirlingGriddedSurface for selected Segment indices. It stitches together the segments and returns the resulting surface
	 *  
	 * @param segIndex List of Segment index to be included in the surface. The indices can have value from 0 to (getNumSegments()-1)
	 * @return
	 */
	public StirlingGriddedSurface getCombinedGriddedSurface(int[] segIndex, double gridSpacing) {
		ArrayList<SimpleFaultData> simpleFaultData = new ArrayList<SimpleFaultData>();
		int lastSegmentIndex = getNumSegments()-1;
		
		// determine whether stepover needs to be fixed
		boolean fixStepOver = false;
		if(faultName.equals("San Jacinto") || faultName.equals("Elsinore"))
			for(int i=0; i<segIndex.length-1; ++i) 
				if(segIndex[i] == 1 && segIndex[i+1] == 2) fixStepOver = true;  // both segments 1 & 2 used
		
		// undo fix if unsegmented model was chosen
		if(fixStepOver) {
			int numSectionsOnSeg1 = ((ArrayList)this.simpleFaultDataList.get(2)).size();
			if(numSectionsOnSeg1 == 1) fixStepOver = false;
		}
	
/*		
		if(faultName.equals("Elsinore")) {
			for(int i=0; i<segIndex.length; ++i) System.out.print(segIndex[i]+"("+getSegmentName(segIndex[i])+";"+
					((ArrayList)this.simpleFaultDataList.get(segIndex[i])).size()+")+");
			System.out.print("\n");
		}
*/
		for(int i=0; i<segIndex.length; ++i) {
			if(segIndex[i]<0 || segIndex[i]>lastSegmentIndex) throw new RuntimeException ("Segment indices should can have value from  0 to "+lastSegmentIndex);

			if(fixStepOver && segIndex[i]==1) {
//				System.out.println("Fix: using only first simpleFaultData for segment "+i+" of "+faultName);
				simpleFaultData.add((SimpleFaultData) ((ArrayList)this.simpleFaultDataList.get(segIndex[i])).get(0));
			}
			else if(fixStepOver && segIndex[i]==2) {
//				System.out.println("Fix: using only second simpleFaultData for segment "+i+" of "+faultName+" (has "+((ArrayList)this.simpleFaultDataList.get(segIndex[i])).size()+")+");
				simpleFaultData.add((SimpleFaultData) ((ArrayList)this.simpleFaultDataList.get(segIndex[i])).get(1));
			}
			else
				simpleFaultData.addAll((ArrayList)this.simpleFaultDataList.get(segIndex[i]));
		}
		return  new StirlingGriddedSurface(simpleFaultData, gridSpacing);
	}
	

	
	
	
	/**
	 * Get StirlingGriddedSurface for ALL Segments. 
	 * It stitches together the segments and returns the resulting surface
	 *  
	 * 
	 * @return
	 */
	public StirlingGriddedSurface getCombinedGriddedSurface(double gridSpacing) {
		int segIndices[] = new int[this.getNumSegments()];
		for(int i=0; i<segIndices.length; ++i) segIndices[i] = i;
		return getCombinedGriddedSurface(segIndices, gridSpacing);
	}

	
	/**
	 * Get Ave rake for the ALL Segments
	 * 
	 * 
	 * @return
	 */
	public double getAveRake() {
		int segIndices[] = new int[this.getNumSegments()];
		for(int i=0; i<segIndices.length; ++i) segIndices[i] = i;
		return getAveRake(segIndices);
	}
	
	/**
	 * Get Ave rake for the selected Segments. Rake is weighted by area of the segments
	 * 
	 * @param segIndex List of Segment index to be included for caluclating Avg rake. The indices can have value from 0 to (getNumSegments()-1)
	 * @return
	 */
	public double getAveRake(int []segIndex) {
		int lastSegmentIndex = getNumSegments()-1;
		double totRake=0, totArea=0, area;
		for(int i=0; i<segIndex.length; ++i) {
			if(segIndex[i]<0 || segIndex[i]>lastSegmentIndex) throw new RuntimeException ("Segment indices should can have value from  0 to "+lastSegmentIndex);
			ArrayList<FaultSectionPrefData> faultSectionPrefDataList =  (ArrayList)this.sectionToSegmentData.get(segIndex[i]);
			for(int j=0; j<faultSectionPrefDataList.size(); ++j) {
				area = faultSectionPrefDataList.get(j).getLength()*faultSectionPrefDataList.get(j).getDownDipWidth();
				totArea+=area;
				totRake+=(area*faultSectionPrefDataList.get(j).getAveRake()); // weight the rake by section area
			}
		}
		double rake = totRake/totArea;
		double tolerance = 1e-6;
		//System.out.println(this.faultName+","+rake);
		if(rake>180 && (rake-180 < tolerance)) rake=180;
		return rake;
	}
	
	
	/**
	 * Calculate  Stuff
	 * @return
	 */
	private void calcAll() {
		totalArea=0;
		totalMoRate=0;
		totalMoRateIgnoringAseis=0;
		segArea = new double[sectionToSegmentData.size()];
		segOrigArea=new double[sectionToSegmentData.size()];
		segLength = new double[sectionToSegmentData.size()];
		segMoRate = new double[sectionToSegmentData.size()];
		segMoRateIgnoringAseis = new double[sectionToSegmentData.size()];
		segSlipRate = new double[sectionToSegmentData.size()];
		segSlipRateStdDev = new double[sectionToSegmentData.size()];
		sectionsInSegString = new String[sectionToSegmentData.size()];
		simpleFaultDataList = new ArrayList();
		// fill in segName, segArea and segMoRate
		for(int seg=0;seg<sectionToSegmentData.size();seg++) {
			segArea[seg]=0;
			segOrigArea[seg]=0;
			segLength[seg]=0;
			segMoRate[seg]=0;
			segMoRateIgnoringAseis[seg]=0;
			double stdDevTotal = 0;
			ArrayList segmentDatum = (ArrayList) sectionToSegmentData.get(seg);
			Iterator it = segmentDatum.iterator();
			sectionsInSegString[seg]="";
			ArrayList<SimpleFaultData> simpleFaultData = new ArrayList<SimpleFaultData>();
			while(it.hasNext()) {
				FaultSectionPrefData sectData = (FaultSectionPrefData) it.next();
				simpleFaultData.add(sectData.getSimpleFaultData(aseisReducesArea));
				if(it.hasNext()) sectionsInSegString[seg]+=sectData.getSectionName()+" + ";
				else sectionsInSegString[seg]+=sectData.getSectionName();
				//set the area & moRate
				segLength[seg]+= sectData.getLength()*1e3;  // converted to meters
				double ddw = sectData.getDownDipWidth()*1e3; // converted to meters
				double area = ddw*sectData.getLength()*1e3; // converted to meters-squared
				double slipRate = sectData.getAveLongTermSlipRate()*1e-3;  // converted to m/sec
				double alpha = 1.0 - sectData.getAseismicSlipFactor();  // reduction factor
				segMoRateIgnoringAseis[seg] += FaultMomentCalc.getMoment(area,slipRate); // SI units
				segOrigArea[seg] +=  area;
				if(aseisReducesArea) {
					segArea[seg] += area*alpha;
					stdDevTotal += (sectData.getSlipRateStdDev()/sectData.getAveLongTermSlipRate())*area*alpha;
					segMoRate[seg] += FaultMomentCalc.getMoment(area*alpha,slipRate); // SI units
				}
				else {
					segArea[seg] +=  area;// meters-squared
					stdDevTotal += (sectData.getSlipRateStdDev()/sectData.getAveLongTermSlipRate())*area;
					segMoRate[seg] += FaultMomentCalc.getMoment(area,slipRate*alpha); // SI units
				}
			}
			simpleFaultDataList.add(simpleFaultData);
			// segment slip rate is an average weighted by the section areas
			segSlipRate[seg] = FaultMomentCalc.getSlip(segArea[seg], segMoRate[seg]);
			this.segSlipRateStdDev[seg] = (stdDevTotal/segArea[seg])*segSlipRate[seg];
			totalArea+=segArea[seg];
			totalMoRate+=segMoRate[seg];
			totalMoRateIgnoringAseis+=segMoRateIgnoringAseis[seg];
			totalLength+=segLength[seg];
		}
//		if(faultName.equals("San Jacinto") || faultName.equals("Elsinore"))
//				System.out.println(faultName+"\tnumSegments="+this.getNumSegments());
		return ;
	}
	
}
