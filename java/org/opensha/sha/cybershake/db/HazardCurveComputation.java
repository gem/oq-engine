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

package org.opensha.sha.cybershake.db;

import java.sql.SQLException;
import java.util.ArrayList;

import org.opensha.commons.data.function.ArbDiscrEmpiricalDistFunc;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;

public class HazardCurveComputation {


	private static final double CUT_OFF_DISTANCE = 200;
	private PeakAmplitudesFromDBAPI peakAmplitudes;
	private ERF2DBAPI erfDB;
	private SiteInfo2DBAPI siteDB;
	private Runs2DB runs2db;
	public static final double CONVERSION_TO_G = 980;

	//	private ArrayList<ProgressListener> progressListeners = new ArrayList<ProgressListener>();

	public HazardCurveComputation(DBAccess db){
		peakAmplitudes = new PeakAmplitudesFromDB(db);
		erfDB = new ERF2DB(db);
		siteDB = new SiteInfo2DB(db);
		runs2db = new Runs2DB(db);
	}



	/**
	 * 
	 * @returns the List of supported Peak amplitudes
	 */
	public ArrayList<CybershakeIM> getSupportedSA_PeriodStrings(){

		return peakAmplitudes.getSupportedIMs();
	}

	/**
	 * 
	 * @returns the List of supported Peak amplitudes for a given site, ERF ID, SGT Var ID, and Rup Var ID
	 */
	public ArrayList<CybershakeIM> getSupportedSA_PeriodStrings(int runID){

		return peakAmplitudes.getSupportedIMs(runID);
	}

	/**
	 * Computes the Hazard Curve at the given site 
	 * @param imlVals
	 * @param site
	 * @param erfName
	 * @param srcId
	 * @param rupId
	 * @param imType
	 */
	public DiscretizedFuncAPI computeDeterministicCurve(ArrayList<Double> imlVals, String site,int erfId, int sgtVariation, int rvid,
			int srcId,int rupId,CybershakeIM imType){
		CybershakeRun run = getRun(site, erfId, sgtVariation, rvid);
		if (run == null)
			return null;
		else
			return computeDeterministicCurve(imlVals, run, srcId, rupId, imType);
	}

	private CybershakeRun getRun(String site, int erfID, int sgtVarID, int rupVarID) {
		int siteID = siteDB.getSiteId(site);
		ArrayList<CybershakeRun> runIDs = runs2db.getRuns(siteID, erfID, sgtVarID, rupVarID, null, null, null, null);
		if (runIDs == null || runIDs.size() < 0)
			return null;
		return runIDs.get(0);
	}

	/**
	 * Computes the Hazard Curve at the given runID 
	 * @param imlVals
	 * @param runID
	 * @param srcId
	 * @param rupId
	 * @param imType
	 */
	public DiscretizedFuncAPI computeDeterministicCurve(ArrayList<Double> imlVals, int runID,
			int srcId,int rupId,CybershakeIM imType){
		CybershakeRun run = runs2db.getRun(runID);
		if (run == null)
			return null;
		else
			return computeDeterministicCurve(imlVals, run, srcId, rupId, imType);
	}


	/**
	 * Computes the Hazard Curve at the given run 
	 * @param imlVals
	 * @param run
	 * @param srcId
	 * @param rupId
	 * @param imType
	 */
	public DiscretizedFuncAPI computeDeterministicCurve(ArrayList<Double> imlVals, CybershakeRun run,
			int srcId,int rupId,CybershakeIM imType){

		DiscretizedFuncAPI hazardFunc = new ArbitrarilyDiscretizedFunc();
		int numIMLs  = imlVals.size();
		for(int i=0; i<numIMLs; ++i) hazardFunc.set((imlVals.get(i)).doubleValue(), 1.0);

		int runID = run.getRunID();

		double qkProb = erfDB.getRuptureProb(run.getERFID(), srcId, rupId);
		ArbDiscrEmpiricalDistFunc function = new ArbDiscrEmpiricalDistFunc();
		ArrayList<Integer> rupVariations = peakAmplitudes.getRupVarationsForRupture(run.getERFID(), srcId, rupId);
		int size = rupVariations.size();
		for(int i=0;i<size;++i){
			int rupVarId =  rupVariations.get(i);
			double imVal = peakAmplitudes.getIM_Value(runID, srcId, rupId, rupVarId, imType);
			function.set(imVal/CONVERSION_TO_G,1);
		}
		setIMLProbs(imlVals,hazardFunc, function.getNormalizedCumDist(), qkProb);

		for(int j=0; j<numIMLs; ++j) 
			hazardFunc.set(hazardFunc.getX(j),(1-hazardFunc.getY(j)));

		return hazardFunc;
	}

	/**
	 * Computes the Hazard Curve at the given site 
	 * @param imlVals
	 * @param site
	 * @param erfName
	 * @param imType
	 */
	public DiscretizedFuncAPI computeHazardCurve(ArrayList<Double> imlVals, String site,String erfName,int sgtVariation, int rvid, CybershakeIM imType){
		int erfId = erfDB.getInserted_ERF_ID(erfName);
		System.out.println("for erfname: " + erfName + " found ERFID: " + erfId + "\n");
		return computeHazardCurve(imlVals, site, erfId, sgtVariation, rvid, imType);
	}

	/**
	 * Computes the Hazard Curve at the given site 
	 * @param imlVals
	 * @param site
	 * @param erfName
	 * @param imType
	 */
	public DiscretizedFuncAPI computeHazardCurve(ArrayList<Double> imlVals, String site,int erfId,int sgtVariation, int rvid, CybershakeIM imType){
		CybershakeRun run = getRun(site, erfId, sgtVariation, rvid);
		if (run == null)
			return null;
		else
			return computeHazardCurve(imlVals, run, imType);
	}

	/**
	 * Computes the Hazard Curve at the given site 
	 * @param imlVals
	 * @param site
	 * @param erfName
	 * @param imType
	 */
	public DiscretizedFuncAPI computeHazardCurve(ArrayList<Double> imlVals, int runID, CybershakeIM imType){
		CybershakeRun run = runs2db.getRun(runID);
		if (run == null)
			return null;
		else
			return computeHazardCurve(imlVals, run, imType);
	}

	/**
	 * Computes the Hazard Curve at the given site 
	 * @param imlVals
	 * @param site
	 * @param erfName
	 * @param imType
	 */
	public DiscretizedFuncAPI computeHazardCurve(ArrayList<Double> imlVals, CybershakeRun run, CybershakeIM imType){
		DiscretizedFuncAPI hazardFunc = new ArbitrarilyDiscretizedFunc();
		int siteID = run.getSiteID();
		int erfID = run.getERFID();
		int runID = run.getRunID();
		int numIMLs  = imlVals.size();
		for(int i=0; i<numIMLs; ++i) hazardFunc.set((imlVals.get(i)).doubleValue(), 1.0);

		ArrayList<Integer> srcIdList = siteDB.getSrcIdsForSite(siteID, erfID);
		int numSrcs = srcIdList.size();
		for(int srcIndex =0;srcIndex<numSrcs;++srcIndex){
			//			updateProgress(srcIndex, numSrcs);
			System.out.println("Source " + srcIndex + " of " + numSrcs + ".");
			int srcId = srcIdList.get(srcIndex);
			ArrayList<Integer> rupIdList = siteDB.getRupIdsForSite(siteID, erfID, srcId);
			int numRupSize = rupIdList.size();
			for(int rupIndex = 0;rupIndex<numRupSize;++rupIndex){
				int rupId = rupIdList.get(rupIndex);
				double qkProb = erfDB.getRuptureProb(erfID, srcId, rupId);
				ArbDiscrEmpiricalDistFunc function = new ArbDiscrEmpiricalDistFunc();
				ArrayList<Double> imVals;
				try {
					imVals = peakAmplitudes.getIM_Values(runID, srcId, rupId, imType);
				} catch (SQLException e) {
					return null;
				}
				for (double val : imVals) {
					function.set(val/CONVERSION_TO_G,1);
				}
				//				ArrayList<Integer> rupVariations = peakAmplitudes.getRupVarationsForRupture(erfId, srcId, rupId);
				//				int size = rupVariations.size();
				//				for(int i=0;i<size;++i){
				//					int rupVarId =  rupVariations.get(i);
				//					double imVal = peakAmplitudes.getIM_Value(siteId, erfId, sgtVariation, rvid, srcId, rupId, rupVarId, imType);
				//					function.set(imVal/CONVERSION_TO_G,1);
				//				}
				setIMLProbs(imlVals,hazardFunc, function.getNormalizedCumDist(), qkProb);
			}
		}

		for(int j=0; j<numIMLs; ++j) 
			hazardFunc.set(hazardFunc.getX(j),(1-hazardFunc.getY(j)));

		return hazardFunc;
	}

	public static DiscretizedFuncAPI setIMLProbs( ArrayList<Double> imlVals,DiscretizedFuncAPI hazFunc,
			ArbitrarilyDiscretizedFunc normalizedFunc, double rupProb) {
		// find prob. for each iml value
		int numIMLs  = imlVals.size();
		for(int i=0; i<numIMLs; ++i) {
			double iml = (imlVals.get(i)).doubleValue();
			double prob=0;
			if(iml < normalizedFunc.getMinX()) prob = 0;
			else if(iml > normalizedFunc.getMaxX()) prob = 1;
			else prob = normalizedFunc.getInterpolatedY(iml);
			//System.out.println(iml + "\t" + prob);
			hazFunc.set(i, hazFunc.getY(i)*Math.pow(1-rupProb,1-prob));
		}
		return hazFunc;
	}

	public PeakAmplitudesFromDBAPI getPeakAmpsAccessor() {
		return peakAmplitudes;
	}

	//    public void addProgressListener(ProgressListener listener) {
	//    	progressListeners.add(listener);
	//    }
	//	
	//    public void removeProgressListener(ProgressListener listener) {
	//    	progressListeners.remove(listener);
	//    }
	//    
	//    private void updateProgress(int current, int total) {
	//    	for (ProgressListener listener : progressListeners) {
	//    		listener.setProgress(current, total);
	//    	}
	//    }
}
