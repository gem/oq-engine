/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.analysis;

import java.util.ArrayList;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.EvenlyDiscretizedFunc;
import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.Region;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.UCERF2;
import org.opensha.sha.gui.infoTools.GraphWindow;
import org.opensha.sha.gui.infoTools.PlotCurveCharacterstics;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;

/**
 * This class is used to generate MFDs for NoCal and SoCal Regions. These MFDs were depicted
 * in UCERF2 report. An email was sent to Ned that listed steps to generated the MFD figures.
 *  
 * This accepts a region and hence can be used to generate MFDs for any region.
 * 
 * @author vipingupta
 *
 */
public class NoCalSoCalMFDsPlotter extends LogicTreeMFDsPlotter {
	private final static String NO_CAL_PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/logicTreeMFDs/NoCal/";
	private final static String SO_CAL_PATH = "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_3/data/logicTreeMFDs/SoCal/";
	private final static double MIN_MAG = UCERF2.MIN_MAG-UCERF2.DELTA_MAG/2;
	private final static double MAX_MAG = UCERF2.MAX_MAG-UCERF2.DELTA_MAG/2;
	private final static int NUM_MAG = UCERF2.NUM_MAG;
	
	private Region region;
	IncrementalMagFreqDist aFaultsMFD, bFaultsMFD, nonCA_B_FaultsMFD, cZonesMFD, bckMFD;
	
	/**
	 * Set the region for which MFDs need to be calculated
	 * @param region
	 */
	public NoCalSoCalMFDsPlotter (Region region) {
		this.region = region;
	}
	
	/**
	 * Get A_Faults MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_A_FaultsMFD(UCERF2 ucerf2) {
		aFaultsMFD = new IncrementalMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		ucerf2.getTotal_A_FaultsProb(aFaultsMFD, region);
		convertProbToPoissonRates(aFaultsMFD, ucerf2.getTimeSpan().getDuration());
		return aFaultsMFD;
	}
	
	/**
	 * Get B_Faults Char MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_B_FaultsCharMFD(UCERF2 ucerf2) {
		bFaultsMFD = new IncrementalMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		ucerf2.getTotal_B_FaultsProb(bFaultsMFD, region);
		convertProbToPoissonRates(bFaultsMFD, ucerf2.getTimeSpan().getDuration());
		return bFaultsMFD;
	}
	
	/**
	 * Get B_Faults GR MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_B_FaultsGR_MFD(UCERF2 ucerf2) {
		IncrementalMagFreqDist cumMFD = new IncrementalMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		return cumMFD;
	}

	/**
	 * Get Non CA B_Faults MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_NonCA_B_FaultsMFD(UCERF2 ucerf2) {
		nonCA_B_FaultsMFD = new IncrementalMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		ucerf2.getTotal_NonCA_B_FaultsProb(nonCA_B_FaultsMFD, region);
		convertProbToPoissonRates(nonCA_B_FaultsMFD, ucerf2.getTimeSpan().getDuration());
		return nonCA_B_FaultsMFD;
	}
	
	/**
	 * It assumes here that this method is called after calling getMFDs for all source types
	 * Get Total MFD. 
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotalMFD(UCERF2 ucerf2) {
		SummedMagFreqDist totMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		totMFD.addIncrementalMagFreqDist(this.aFaultsMFD);
		totMFD.addIncrementalMagFreqDist(this.bFaultsMFD);
		totMFD.addIncrementalMagFreqDist(this.nonCA_B_FaultsMFD);
		totMFD.addIncrementalMagFreqDist(this.getTotal_BackgroundMFD(ucerf2));
		totMFD.addIncrementalMagFreqDist(this.getTotal_C_ZoneMFD(ucerf2));
		return totMFD;
	}
	
	/**
	 * Get Observed Cum MFD
	 * 
	 * @param ucerf2
	 * @return
	 */
	protected  ArrayList<EvenlyDiscretizedFunc> getObsCumMFD(UCERF2 ucerf2) {
		if(region instanceof CaliforniaRegions.RELM_NOCAL_GRIDDED) return ucerf2.getObsCumNoCalMFD();
		else if (region instanceof CaliforniaRegions.RELM_SOCAL_GRIDDED) return ucerf2.getObsCumSoCalMFD();
		else if (region == null ) return super.getObsCumMFD(ucerf2);
		else throw new RuntimeException("Unsupported region");
	}
	
	/**
	 * Get C-Zones MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_C_ZoneMFD(UCERF2 ucerf2) {
		if(cZonesMFD==null) {
			cZonesMFD = new IncrementalMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
			ucerf2.getTotal_C_ZoneProb(cZonesMFD, region);
			convertProbToPoissonRates(cZonesMFD, ucerf2.getTimeSpan().getDuration());
		}
		return cZonesMFD;
	}
	
	/**
	 * Get Background MFD
	 * @param ucerf2
	 * @return
	 */
	protected IncrementalMagFreqDist getTotal_BackgroundMFD(UCERF2 ucerf2) {
		if(bckMFD == null) {
			bckMFD = new IncrementalMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
			ucerf2.getTotal_BackgroundMFD(bckMFD, region);
		}
		return bckMFD;
	}
	

	/**
	 * Get Observed Incr MFD
	 * 
	 * @param ucerf2
	 * @return
	 */
	protected  ArrayList<ArbitrarilyDiscretizedFunc> getObsIncrMFD(UCERF2 ucerf2) {
		if(region instanceof CaliforniaRegions.RELM_NOCAL_GRIDDED) return ucerf2.getObsIncrNoCalMFD();
		else if (region instanceof CaliforniaRegions.RELM_SOCAL_GRIDDED) return ucerf2.getObsIncrSoCalMFD();
		else throw new RuntimeException("Unsupported region");
	}
	
	/**
	 * Convert Probs to Poisson rates
	 * 
	 * @param incrMFD
	 * @param duration
	 */
	private void convertProbToPoissonRates(IncrementalMagFreqDist cumMFD, double duration) {
		for(int i=0; i <cumMFD.getNum();i++){
			cumMFD.set(i,-Math.log(1-cumMFD.getY(i))/duration);
	
		}
	}
	
	
	/**
	 * Read MFDs from the text files and plot them using JFreeChart.
	 * 
	 * It assumes that MFDs have been pre-computed and written to a file. To genrate the file,
	 * we can use the merhod generateMFDsData() in parent class.
	 * 
	 * The main() method clarifies how files can be generated and how MFDs can be plotted.
	 * 
	 *
	 */
	private void plotCumMFDs(String path) {
		
		readMFDsFromFile(path+A_FAULTS_MFD_FILENAME, this.aFaultMFDsList, false);
		//for(int i=0; i<aFaultMFDsList.size(); ++i)
			//System.out.println(aFaultMFDsList.get(i).getCumRate(6.5));
		readMFDsFromFile(path+B_FAULTS_CHAR_MFD_FILENAME, this.bFaultCharMFDsList, false);
		readMFDsFromFile(path+B_FAULTS_GR_MFD_FILENAME, this.bFaultGRMFDsList, false);
		readMFDsFromFile(path+NON_CA_B_FAULTS_MFD_FILENAME, this.nonCA_B_FaultsMFDsList, false);
		readMFDsFromFile(path+TOT_MFD_FILENAME, this.totMFDsList, false);
	
		ucerf2.updateForecast();
		IncrementalMagFreqDist bckMFD = this.getTotal_BackgroundMFD(ucerf2);
		IncrementalMagFreqDist cZonesMFD = this.getTotal_C_ZoneMFD(ucerf2);
		funcs  = new ArrayList();
		plottingFeaturesList = new ArrayList<PlotCurveCharacterstics>();
		
		// Avg MFDs
		SummedMagFreqDist avgAFaultMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG,NUM_MAG);
		SummedMagFreqDist avgBFaultCharMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG,NUM_MAG);
		SummedMagFreqDist avgBFaultGRMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG,NUM_MAG);
		SummedMagFreqDist avgNonCA_B_FaultsMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		SummedMagFreqDist avgTotMFD = new SummedMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAG);
		
		doWeightedSum(null, null, avgAFaultMFD, avgBFaultCharMFD, avgBFaultGRMFD, avgNonCA_B_FaultsMFD, avgTotMFD);
		
		// Add to function list
		//System.out.println(avgAFaultMFD.toString());
		//System.out.println(avgBFaultCharMFD.toString());
		//System.out.println(avgNonCA_B_FaultsMFD.toString());
		//System.out.println(bckMFD.toString());
		//System.out.println(cZonesMFD.toString());
		//System.out.println(avgTotMFD.toString());
		
		/*for(int i=0; i<avgTotMFD.getNum(); ++i) {
			if(Double.isInfinite(avgTotMFD.getY(i))) avgTotMFD.set(i, 100);
		}*/
		
		addToFuncList(avgAFaultMFD, "Average A-Fault MFD", PLOT_CHAR1);
		addToFuncList(avgBFaultCharMFD, "Average  B-Fault MFD", PLOT_CHAR3);
		addToFuncList(avgNonCA_B_FaultsMFD, "Average Non-CA B-Fault MFD", PLOT_CHAR10);
		addToFuncList(bckMFD, "Average Background MFD", PLOT_CHAR5);
		addToFuncList(cZonesMFD, "Average C-Zones MFD", PLOT_CHAR6);
	
		
		//Karen's observed data
		ArrayList obsMFD = getObsCumMFD(ucerf2);
		String metadata="Average Total MFD, M6.5 Cum Ratio = "+avgTotMFD.getCumRate(6.5)/((EvenlyDiscretizedFunc)obsMFD.get(0)).getY(6.5);

		addToFuncList(avgTotMFD, metadata, PLOT_CHAR4);
		
		
		// historical best fit cum dist
		//funcs.add(eqkRateModel2ERF.getObsBestFitCumMFD(includeAfterShocks));
		funcs.add(obsMFD.get(0));
		this.plottingFeaturesList.add(PLOT_CHAR7);
		// historical cum dist
		funcs.addAll(obsMFD);
		this.plottingFeaturesList.add(PLOT_CHAR8);
		this.plottingFeaturesList.add(PLOT_CHAR8);
		this.plottingFeaturesList.add(PLOT_CHAR8);
		
		GraphWindow graphWindow= new GraphWindow(this);
	    graphWindow.setPlotLabel("Mag Freq Dist");
	    graphWindow.plotGraphUsingPlotPreferences();
	    graphWindow.setVisible(true);
		
	}
	
	/**
	 * Cum rate at 6.5
	 * @param mfd
	 * @return
	 */
	protected double getCumRateAt6_5(IncrementalMagFreqDist mfd) {
		return mfd.getCumRate(6.5);
	}
	
	/**
	 * 
	 * @param mfd
	 */
	private void addToFuncList(IncrementalMagFreqDist mfd, String metadata, 
			PlotCurveCharacterstics curveCharateristic) {
		mfd.setInfo(metadata);
		funcs.add(mfd);
		this.plottingFeaturesList.add(curveCharateristic);
	}
	
	/**
	 * Min Mag
	 * @return
	 */
	protected double getMinMag() {
		return MIN_MAG;
	}
	
	/**
	 * Max Mag
	 * @return
	 */
	protected double getMaxMag() {
		return MAX_MAG;
	}
	
	/**
	 * Get num Mag
	 * @return
	 */
	protected int getNumMags() {
		return NUM_MAG;
	}
	
	public static void main(String args[]) {
		//NoCalSoCalMFDsPlotter plotter = new NoCalSoCalMFDsPlotter(new EvenlyGriddedNoCalRegion());
		//plotter.generateMFDsData(NoCalSoCalMFDsPlotter.NO_CAL_PATH);
		//plotter.plotCumMFDs(NoCalSoCalMFDsPlotter.NO_CAL_PATH);
		NoCalSoCalMFDsPlotter plotter = new NoCalSoCalMFDsPlotter(new CaliforniaRegions.RELM_SOCAL_GRIDDED());
		plotter.generateMFDsData(NoCalSoCalMFDsPlotter.SO_CAL_PATH);
		//plotter.plotCumMFDs(NoCalSoCalMFDsPlotter.SO_CAL_PATH);
	}
	
}
