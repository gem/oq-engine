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

package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.A_Faults;

import java.awt.Color;
import java.util.ArrayList;

import org.opensha.commons.calc.MomentMagCalc;
import org.opensha.commons.data.function.ArbDiscrEmpiricalDistFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.sha.earthquake.calc.recurInterval.BPT_DistCalc;
import org.opensha.sha.gui.controls.PlotColorAndLineTypeSelectorControlPanel;
import org.opensha.sha.gui.infoTools.GraphiWindowAPI_Impl;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;


/**
 * <p>Title: WG02_QkProbCalc </p>
 * <p>Description: 
 * <p>Copyright: Copyright (c) 2002</p>
 * <p>Company: </p>
 * @author Ned Field
 * @date July, 2007
 * @version 1.0
 */


public class WG02_QkSimulations {
	
	//for Debug purposes
	private static String C = new String("WG02_QkSimulations");
	private final static boolean D = false;
	
	//name for this classs
	protected String NAME = "WG02_QkSimulations";
		
	private double[] eventYear, segRate;
	private int[] eventIndex;
	private int[][] rupInSeg;
	double segAlpha[];
	
	

	/*
	 * This monte carlo simulates events.  This sets the time of rupture first rupture for all
	 * segments at year=0 (other methods here assume this).
	 */
	public void computeSimulatedEvents(double[] rupRate, double[] segMoRate, 
			double alpha, int[][] rupInSeg, int numEvents) {
		segAlpha = new double[segMoRate.length];
		for(int i=0;i<segMoRate.length;i++) segAlpha[i] = alpha;
		computeSimulatedEvents(rupRate, segMoRate, segAlpha, rupInSeg, numEvents);
	}

	
	
	/*
	 * This monte carlo simulates events.  This sets the time of rupture first rupture for all
	 * segments at year=0 (other methods here assume this).
	 */
	public void computeSimulatedEvents(double[] rupRate, double[] segMoRate, 
			double[] segAlpha, int[][] rupInSeg, int numEvents) {
		
		this.rupInSeg = rupInSeg; // needed by other methods.
		this.segAlpha = segAlpha;
		
		// compute segRates from rupRates
		segRate = getSegRateFromRupRate(rupRate, rupInSeg);   // also needed by other methods
		
		eventIndex = new int[numEvents];
		eventYear = new double[numEvents];
//		WG02_QkProbCalc calc = new WG02_QkProbCalc();

		int numSeg = segRate.length;
		double deltaYear = 1.0;
		double year = 0.0;
		double[] segTimeOfLast = new double[numSeg];  // initialized at zero, which is what we want
		double[] segTimeSinceLast = new double[numSeg];
		double[] rupProbs;
		int numSimEvents = 0, rupIndex;
		int progressReportIncrement = numEvents/10;
		int progressReportAt = progressReportIncrement;
		while(numSimEvents < numEvents) {
			year += deltaYear;
			for(int s=0; s<numSeg; s++)
				segTimeSinceLast[s] = year - segTimeOfLast[s];
			rupProbs = WG02_QkProbCalc.getRupProbs(segRate, rupRate, segMoRate, segAlpha, segTimeSinceLast, deltaYear, rupInSeg);
			rupIndex =getRandomEvent(rupProbs);
			if (rupIndex > -1) {  // got an event
				eventYear[numSimEvents] = year;
				eventIndex[numSimEvents] = rupIndex;
				for(int s=0; s<numSeg; s++)
					if(rupInSeg[s][rupIndex] == 1) segTimeOfLast[s] = year;
				if(D)
					System.out.println(numSimEvents+"   "+(float)eventYear[numSimEvents]+"   "+eventIndex[numSimEvents]);
				numSimEvents+= 1;
				if(numSimEvents == progressReportAt) { // does this slow things down?
					int perc = 100*progressReportAt/numEvents;
					System.out.println(perc+" Percent Done");
					progressReportAt += progressReportIncrement;
				} 
			}
		}
	}

	
	public ArbDiscrEmpiricalDistFunc getCDF_ofSegRecurIntervals(int ithSeg)  {
		ArbDiscrEmpiricalDistFunc func = new ArbDiscrEmpiricalDistFunc();
		int numRup=0, rupIndex;
		double yearLast= 0;  // all segments ruptured at year zero 
		for(int i=0;i<eventIndex.length;i++)
			if(rupInSeg[ithSeg][eventIndex[i]] == 1) {
				func.set(eventYear[i]-yearLast,1);
				yearLast=eventYear[i];
			}
		return func;
	}
		
	/**
	 * 
	 * @param ithSeg
	 * @param binWidth - the historgram bin widths
	 * @return
	 */
	public EvenlyDiscretizedFunc getPDF_ofSegRecurIntervals(int ithSeg, double binWidth)  {
		// Find max interval
		double maxInt = 0, interval, yearLast=0;
		int numInts=0;
		for(int i=0;i<eventIndex.length;i++)
			if(rupInSeg[ithSeg][eventIndex[i]] == 1) {
				interval =eventYear[i]-yearLast;
				if(interval >maxInt) maxInt = interval;
				numInts+=1;
				yearLast = eventYear[i];
			}
		double min = binWidth/2;
		int num = Math.round((float)((maxInt-min)/binWidth))+1;
		EvenlyDiscretizedFunc func = new EvenlyDiscretizedFunc(min,num,binWidth);
		func.setTolerance(1.1*binWidth); // make the tolerance anything larger than delta
		yearLast= 0;  // all segments ruptured at year zero 
		double yAddOn = 1/(numInts*binWidth);  // add for each contribution to get PDF
		for(int i=0;i<eventIndex.length;i++)
			if(rupInSeg[ithSeg][eventIndex[i]] == 1) {
				interval =eventYear[i]-yearLast;
				func.set(interval,func.getY(interval)+yAddOn);
				yearLast=eventYear[i];
			}
		return func;
		
	}
	
	/**
	 * 
	 * @param ithRup
	 * @return
	 */
	public double getSimAveRupRate(int ithRup){
		int numRup=0;
		double yearFirst = -1;
		double yearLast= -1;
		for(int i=0;i<eventIndex.length;i++)
			if(eventIndex[i] == ithRup) {
				numRup += 1;
				if(numRup == 1) yearFirst = eventYear[i];
				yearLast = eventYear[i];
			}
		if(numRup == 0) return 0.0;
		else return (numRup-1)/(yearLast-yearFirst);
	}
	
	
	
	/**
	 * 
	 * @param ithSeg
	 * @return
	 */
	public double getSimAveSegRate(int ithSeg){
		int numRup=0, rupIndex;
		double yearFirst = 0;  // assumes all segments ruptured at year zero
		double yearLast= -1;
		for(int i=0;i<eventIndex.length;i++)
			if(rupInSeg[ithSeg][eventIndex[i]] == 1) {
				numRup += 1;
//				if(numRup == 1) yearFirst = eventYear[i];
				yearLast = eventYear[i];
			}
		if(numRup == 0) return 0.0;
		else return numRup/(yearLast-yearFirst);
	}

	
	
	/**
	 * 
	 * @param ithSeg
	 * @return
	 */
	public double getSimMoRate(double[] rupMag){
		double totMoment = 0;
		for(int i=0;i<eventIndex.length;i++) totMoment += MomentMagCalc.getMoment(rupMag[eventIndex[i]]);
		double moRate = totMoment/eventYear[eventYear.length-1];
		
		totMoment = 0;
		for(int i=0;i<eventIndex.length-1;i++) totMoment += MomentMagCalc.getMoment(rupMag[eventIndex[i]]);
		double moRate2 = totMoment/eventYear[eventYear.length-1];
		System.out.println("MoRateRange:"+(float)moRate2+"   "+(float)moRate);
		
		return moRate;
	}

	/**
	 * This chooses a random event from the prob[] array passed in, giving
	 * back the index of the chosen event.  
	 * -1 is returned if no event is sampled (which can occur if the sum
	 * of all probs is not 1.0).
	 * @return
	 */
	public static int getRandomEvent(double[] prob) {
		double prandProb = Math.random();
		double sum=0;
		for(int i=0; i< prob.length; i++) {
			if(prandProb>=sum && prandProb < sum+prob[i]) return i;
			sum += prob[i];
		}
		// nothing found
		return -1;
	}
	
	private double[] getSegRateFromRupRate(double[] rupRate, int[][] rupInSeg) {
		double[] segRate = new double[rupInSeg.length];
		for(int i=0; i<segRate.length; i++)
			for(int j=0; j<rupRate.length;j++)
				segRate[i] += rupInSeg[i][j]*rupRate[j];
		return segRate;
	}
	
	
	/*
	 * This tests results against those obtained from the WGCEP-2002 Fortran code (single branch 
	 * for N. SAF done by Ned Field in Feb of 2006; see his "Neds0206TestOutput.txt" file).
	 */
	public void testWithWG02_SingleSegRups() {
		
		double[] segMoRate  = {4.74714853E+24,5.62020641E+24,1.51106804E+25,1.06885024E+25};  // cgs units!
		double[] segAlpha = {0.2,0.5,0.8,0.5};
//		double[] segAlpha = {0.5,0.5,0.5,0.5};
		double[] segMag = {7.16886,7.24218,7.52195,7.37158};
		double[] segRate = new double[segMoRate.length];
		for(int i=0;i<segRate.length;i++) {
			segRate[i] = segMoRate[i]/(MomentMagCalc.getMoment(segMag[i])*10000000);
//			System.out.println("seg "+i+" rate = "+segRate[i]);
		}
		double[] rupRate = {segRate[0],segRate[1],segRate[2],segRate[3],0,0,0,0,0,0};
		double[] rupMag = {7.16886,7.24218,7.52195,7.37158,7.5081,7.70524,7.75427,7.81611,7.87073,7.94943};
		int[][] rupInSeg = {
				// 1,2,3,4,5,6,7,8,9,10
				{1,0,0,0,0,0,0,0,0,0}, // seg 1
				{0,1,0,0,0,0,0,0,0,0}, // seg 2
				{0,0,1,0,0,0,0,0,0,0}, // seg 3
				{0,0,0,1,0,0,0,0,0,0}  // seg 4
		};
		
		System.out.println("Starting Simulation Test");
		long startTime = System.currentTimeMillis();
		int numSim =1000;
		this.computeSimulatedEvents(rupRate, segMoRate, segAlpha, rupInSeg, numSim);
		double timeTaken = (double) (System.currentTimeMillis()-startTime) / 1000.0;
		System.out.println("Done w/ "+numSim+" events in "+(float)timeTaken+" seconds");
		
		System.out.println("Segment Rate From Recur. Int. CDF:");
		for(int i=0;i<segRate.length;i++) {
			ArbDiscrEmpiricalDistFunc cdf = this.getCDF_ofSegRecurIntervals(i);
			System.out.println("ratio="+ (float)(getSimAveSegRate(i)*cdf.getMean())+
					";  cdfRate="+(float)(1/cdf.getMean())+"; simSegRate="+
					(float)getSimAveSegRate(i)+"; numEvents="+cdf.getSumOfAllY_Values());
		}
		
		
		System.out.println("Rup rates: orig, sim, and sim/orig");
		for(int i=0;i<rupRate.length;i++) {
			double simRate = getSimAveRupRate(i);
			System.out.println((float)rupRate[i]+"   "+(float)simRate+"   "+(float)(simRate/rupRate[i]));
		}

		System.out.println("Seg rates: orig, sim, and sim/orig");
		for(int i=0;i<segRate.length;i++) {
			double simRate = getSimAveSegRate(i);
			System.out.println((float)segRate[i]+"   "+(float)simRate+"   "+(float)(simRate/segRate[i]));
		}
		
		double totMoRate = 0;
		for(int i=0;i<rupRate.length;i++) totMoRate += rupRate[i]*MomentMagCalc.getMoment(rupMag[i]);
		System.out.println("Tot Moment rates: orig, sim, and sim/orig");
		double simMoRate = this.getSimMoRate(rupMag);
		System.out.println((float)totMoRate+"   "+(float)simMoRate+"   "+(float)(simMoRate/totMoRate));

		plotSegmentRecurIntPDFs();
	}
		
	
	public void plotSegmentRecurIntPDFs() {
		BPT_DistCalc calc = new BPT_DistCalc();
		for(int i=0; i<rupInSeg.length;i++) {
			ArrayList funcList = new ArrayList();
			double mri = 1/segRate[i];
			int num = (int)(segAlpha[i]*10/0.05);
			calc.setAll(mri,segAlpha[i],0.05*mri,num);
			funcList.add(calc.getPDF());
			double binWidth = Math.round(mri/10); // 10 bins before the mean
			funcList.add(this.getPDF_ofSegRecurIntervals(i,binWidth));
			String title = "Simulated and Expected BPT Dist for seg "+i;
			ArrayList<PlotCurveCharacterstics> plotChars = new ArrayList<PlotCurveCharacterstics>();
			plotChars.add(new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,Color.RED, 2));
			plotChars.add(new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.HISTOGRAM,Color.GRAY, 2));
			GraphiWindowAPI_Impl graph = new GraphiWindowAPI_Impl(funcList,title,plotChars);
			graph.setPlottingFeatures(plotChars);
			graph.setPlotLabelFontSize(24);
			graph.setY_AxisLabel("");
			graph.setX_AxisLabel("Segment Recurrence Interval");
			graph.setAxisAndTickLabelFontSize(20);
			graph.setAxisRange(0,mri*5,0,(1.1*calc.getPDF().getMaxY()));
		}
	}

	
	public void plotSegmentRecurIntPDFs(String[] segName) {
		BPT_DistCalc calc = new BPT_DistCalc();
		for(int i=0; i<rupInSeg.length;i++) {
			ArrayList funcList = new ArrayList();
			double mri = 1/segRate[i];
			int num = (int)(segAlpha[i]*10/0.05);
			calc.setAll(mri,segAlpha[i],0.05*mri,num);
			funcList.add(calc.getPDF());
			double binWidth = Math.round(mri/10); // 10 bins before the mean
			funcList.add(this.getPDF_ofSegRecurIntervals(i,binWidth));
			String title = "PDF for "+segName[i];
			ArrayList<PlotCurveCharacterstics> plotChars = new ArrayList<PlotCurveCharacterstics>();
			plotChars.add(new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.SOLID_LINE,Color.RED, 4));
			plotChars.add(new PlotCurveCharacterstics(PlotColorAndLineTypeSelectorControlPanel.HISTOGRAM,Color.GRAY, 2));
			GraphiWindowAPI_Impl graph = new GraphiWindowAPI_Impl(funcList,title,plotChars);
			graph.setPlotLabelFontSize(24);
			graph.setY_AxisLabel("");
			graph.setX_AxisLabel("Segment Recurrence Interval");
			graph.setAxisAndTickLabelFontSize(20);
			graph.setAxisRange(0,mri*5,0,(1.1*calc.getPDF().getMaxY()));
		}
	}
	
	public void wg02_haywardRC_simulation() {
		
		String[] segName = {"HS","HN","RC"};
		double[] segMoRate  = {52.54,34.89,62.55};  // these are just lengths, as slip rate and DDW are constant across segments
		double alpha = 0.5;
		double[] rupRate = {1.28e-3,1.02e-3,3.32e-3,2.16e-3,0.32e-3,0.44e-3};
		double[] rupMag = {7.00,6.82,7.07,7.22,7.27,7.46};

		int[][] rupInSeg = {
				// 1,2,3,4,5,6
				{1,0,0,1,0,1}, // seg 1
				{0,1,0,1,1,1}, // seg 2
				{0,0,1,0,1,1}, // seg 3
		};
		double[] segRate = this.getSegRateFromRupRate(rupRate,rupInSeg);
		/*
		// check above segment rates
		System.out.println("Testing segment rates:");
		double[] testSegRate = this.getSegRateFromRupRate(rupRate,rupInSeg);
		for(int i=0; i<testSegRate.length; i++)
			System.out.println(i+"th seg rate:  "+testSegRate[i]);
		*/

		System.out.println("Starting Simulation Test");
		long startTime = System.currentTimeMillis();
		int numSim =20000;
		computeSimulatedEvents(rupRate, segMoRate, alpha, rupInSeg, numSim);
		double timeTaken = (double) (System.currentTimeMillis()-startTime) / 1000.0;
		System.out.println("Done w/ "+numSim+" events in "+(float)timeTaken+" seconds");
		
		System.out.println("Rup rates: orig, sim, and sim/orig");
		for(int i=0;i<rupRate.length;i++) {
			double simRate = getSimAveRupRate(i);
			System.out.println((float)rupRate[i]+"   "+(float)simRate+"   "+(float)(simRate/rupRate[i]));
		}

		System.out.println("Seg rates: orig, sim, and sim/orig");
		for(int i=0;i<segRate.length;i++) {
			double simRate = getSimAveSegRate(i);
			System.out.println((float)segRate[i]+"   "+(float)simRate+"   "+(float)(simRate/segRate[i]));
		}
		
		double totMoRate = 0;
		for(int i=0;i<rupRate.length;i++) totMoRate += rupRate[i]*MomentMagCalc.getMoment(rupMag[i]);
		System.out.println("Tot Moment rates: orig, sim, and sim/orig");
		double simMoRate = this.getSimMoRate(rupMag);
		System.out.println((float)totMoRate+"   "+(float)simMoRate+"   "+(float)(simMoRate/totMoRate));
		
		plotSegmentRecurIntPDFs(segName);
	}
	
	
	/*
	 * This tests results against those obtained from the WGCEP-2002 Fortran code (single branch 
	 * for N. SAF done by Ned Field in Feb of 2006; see his "Neds0206TestOutput.txt" file).
	 */
	public void testWithWG02_values() {
		
		double[] segMoRate  = {4.74714853E+24,5.62020641E+24,1.51106804E+25,1.06885024E+25};
		double[] segAlpha = {0.2,0.5,0.8,0.5};
//		double[] segAlpha = {0.5,0.5,0.5,0.5};
		double[] segT_Last = {96, 96, 96, 96};
		double duration = 30;
		double[] segRate = {0.00466746464,0.00432087015,0.004199435,0.004199435};
		double[] rupRate = {0.00145604357,0.000706832856,0.,0.,0.000505269971,0.,0.00109066791,0.,0.000402616395,0.00270615076};
		double[] rupMag = {7.16886,7.24218,7.52195,7.37158,7.5081,7.70524,7.75427,7.81611,7.87073,7.94943};
		int[][] rupInSeg = {
				// 1,2,3,4,5,6,7,8,9,10
				{1,0,0,0,1,0,0,1,0,1}, // seg 1
				{0,1,0,0,1,1,0,1,1,1}, // seg 2
				{0,0,1,0,0,1,1,1,1,1}, // seg 3
				{0,0,0,1,0,0,1,0,1,1} // seg 4
		};
		
		// check above segment rates
		System.out.println("Testing segment rates:");
		double[] testSegRate = this.getSegRateFromRupRate(rupRate,rupInSeg);
		for(int i=0; i<segRate.length; i++)
			System.out.println(segRate[i]+"  "+testSegRate[i]+"  "+(segRate[i]/testSegRate[i]));

/*		
		// test the getRandomEvent(*)method
		System.out.println("Testing getRandomEvent(*) method:");
		WG02_QkProbCalc calc = new WG02_QkProbCalc();
		calc.computeProbs(segRate,rupRate,segMoRate,alpha,segT_Last,duration,rupInSeg);
		double[] rupProb = calc.getRupProbs();
		double[] simEventsProb = new double[rupRate.length];
		int totNum = 1000000;
		int numEvents = 0, numTry;
		int simEvent;
		System.out.println("Starting");
		for(numTry =0; numEvents<totNum; numTry++) {
			simEvent = WG02_QkSimulations.getRandomEvent(rupProb);
			if(simEvent > -1) {
				simEventsProb[simEvent] += 1.0;
				numEvents+=1;
			}
		}
		System.out.println("Done");
		for(int i=0; i<rupProb.length; i++) simEventsProb[i] = simEventsProb[i]/(double)(numTry-1);

		for(int i=0; i<rupProb.length; i++)
			System.out.println((float)rupProb[i]+"   "+(float)simEventsProb[i]+"   "+
					(float)(simEventsProb[i]/rupProb[i]));
*/
		
		// now test the simulation
		System.out.println("Starting Simulation Test");
		long startTime = System.currentTimeMillis();
		int numSim =1000;
		this.computeSimulatedEvents(rupRate, segMoRate, segAlpha, rupInSeg, numSim);
		double timeTaken = (double) (System.currentTimeMillis()-startTime) / 1000.0;
		System.out.println("Done w/ "+numSim+" events in "+(float)timeTaken+" seconds");
		
		System.out.println("Rup rates: orig, sim, and sim/orig");
		for(int i=0;i<rupRate.length;i++) {
			double simRate = getSimAveRupRate(i);
			System.out.println((float)rupRate[i]+"   "+(float)simRate+"   "+(float)(simRate/rupRate[i]));
		}

		System.out.println("Seg rates: orig, sim, and sim/orig");
		for(int i=0;i<segRate.length;i++) {
			double simRate = getSimAveSegRate(i);
			System.out.println((float)segRate[i]+"   "+(float)simRate+"   "+(float)(simRate/segRate[i]));
		}
		
		
		double totMoRate = 0;
		for(int i=0;i<rupRate.length;i++) totMoRate += rupRate[i]*MomentMagCalc.getMoment(rupMag[i]);
		System.out.println("Tot Moment rates: orig, sim, and sim/orig");
		double simMoRate = this.getSimMoRate(rupMag);
		System.out.println((float)totMoRate+"   "+(float)simMoRate+"   "+(float)(simMoRate/totMoRate));


		plotSegmentRecurIntPDFs();
	}
	
	
	/*
	 * This tests results against those obtained from the WGCEP-2002 Fortran code (single branch 
	 * for SAF done by Ned Field in Feb of 2006; see his "Neds0206TestOutput.txt" file).  Results
	 * are within 0.5%.

	 */
	public static void main(String args[]) {
		
		WG02_QkSimulations qkSim = new WG02_QkSimulations();
//		qkSim.testWithWG02_values();
//		qkSim.testWithWG02_SingleSegRups();
		qkSim.wg02_haywardRC_simulation();
	}
}

