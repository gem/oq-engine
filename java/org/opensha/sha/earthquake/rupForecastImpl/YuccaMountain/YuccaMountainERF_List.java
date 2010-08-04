/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.YuccaMountain;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.estimate.DiscreteValueEstimate;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.IntegerParameter;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.TreeBranchWeightsParameter;
import org.opensha.commons.param.estimate.EstimateConstraint;
import org.opensha.commons.param.estimate.EstimateParameter;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.ERF_EpistemicList;
import org.opensha.sha.earthquake.EqkRupForecastAPI;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;

/**
 * Yucca Mountain ERF List that iterates over all logic tree branches
 * 
 * @author vipingupta
 *
 */
public class YuccaMountainERF_List  extends ERF_EpistemicList{
	public static final String  NAME = new String("Yucca Mountain ERF Epistemic List");
	protected YuccaMountainERF yuccaMountainERF = new YuccaMountainERF();
	private final static double DURATION_DEFAULT = 30;


	private final static double DELTA_MAG = 0.1;

	private String FAULT_LOGIC_TREE_FILENAME = "org/opensha/sha/earthquake/rupForecastImpl/YuccaMountain/FaultsLogicTree.txt";
	private String BACKGROUND_LOGIC_TREE_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/YuccaMountain/BackgroundLogicTree.txt";

	private final static String MAG="Mag-";
	private final static String MOMENT_RATE="MomentRate-";
	private final static String BACKGROUND = "Background";

	// This hashmap saves Background MFD corresponding to each CumRate
	private HashMap<Double, GutenbergRichterMagFreqDist> backgroundOptions;
	private final static String BACKGROUND1_PARAM_NAME = "Wt for Min Cum Rate Option";
	private final static String BACKGROUND2_PARAM_NAME = "Wt for Pref Cum Rate Option";
	private final static String BACKGROUND3_PARAM_NAME = "Wt for Max Cum Rate Option";
	
	//	 For num realizations parameter
	private final static String NUM_REALIZATIONS_PARAM_NAME ="Num Realizations";
	private Integer DEFAULT_NUM_REALIZATIONS_VAL= new Integer(1000);
	private int NUM_REALIZATIONS_MIN = 1;
	private int NUM_REALIZATIONS_MAX = 10000;
	private final static String NUM_REALIZATIONS_PARAM_INFO = "Number of Monte Carlo ERF realizations";
	IntegerParameter numRealizationsParam;

	private EstimateConstraint discreteValueEstimateConstraint;
	
	
	private double bckPrefCumRate, bckMinCumRate, bckMaxCumRate;


	public YuccaMountainERF_List() {

		// number of Monte carlo realizations
		numRealizationsParam = new IntegerParameter(NUM_REALIZATIONS_PARAM_NAME,NUM_REALIZATIONS_MIN,
				NUM_REALIZATIONS_MAX, DEFAULT_NUM_REALIZATIONS_VAL);
		numRealizationsParam.setInfo(NUM_REALIZATIONS_PARAM_INFO);
		adjustableParams.addParameter(numRealizationsParam);

		// constraint that only allows Min/Max/Pref Estimate
		ArrayList<String> allowedEstimates = new ArrayList<String>();
		allowedEstimates.add(DiscreteValueEstimate.NAME);
		discreteValueEstimateConstraint = new EstimateConstraint(allowedEstimates);

		fillFaultsLogicTree();

		addBackgroundBranches();
		// Backgroud is MagFreqDistParameter
		//ArrayList<String> allowedMagDists = new ArrayList<String>();
		//allowedMagDists.add(GutenbergRichterMagFreqDist.NAME);
		//paramList.addParameter(new MagFreqDistParameter(BACKGROUND, allowedMagDists));

		// create the time-ind timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
		timeSpan.setDuration(DURATION_DEFAULT);
	}




	/**
	 * Fill the logic tree branches in faults
	 *
	 */
	private void fillFaultsLogicTree() {
		try {
			ArrayList<String> faultBranchesLines = FileUtils.loadJarFile(FAULT_LOGIC_TREE_FILENAME);

			for(int i=14; i<faultBranchesLines.size(); ) {
				// get the source name
				String sourceCodeNameLine = faultBranchesLines.get(i);
				StringTokenizer st = new StringTokenizer(sourceCodeNameLine);
				String srcCode = st.nextToken();		
				++i;
				++i;
				String paramName = MAG+srcCode;
				DiscreteValueEstimate magEstimate = getDiscreteValueEstimate(faultBranchesLines, i);
				EstimateParameter magParam = new EstimateParameter(paramName,  this.discreteValueEstimateConstraint, null, magEstimate);
				this.adjustableParams.addParameter(magParam);

				i+=4;
				paramName = MOMENT_RATE+srcCode;
				DiscreteValueEstimate moRateEstimate = getDiscreteValueEstimate(faultBranchesLines, i);
				EstimateParameter moRateParam = new EstimateParameter(paramName,  this.discreteValueEstimateConstraint, null, moRateEstimate);
				this.adjustableParams.addParameter(moRateParam);
				i+=3;
			}

		}catch(Exception e) {
			e.printStackTrace();
		}
	}

	/**
	 * Get DiscreteValue Estimate based on lines in files
	 * 
	 * @param faultBranchesLines
	 * @param lineIndex
	 * @return
	 */
	private DiscreteValueEstimate getDiscreteValueEstimate(ArrayList<String> faultBranchesLines, 
			int lineIndex) {
		
		StringTokenizer tokenizer = new StringTokenizer(faultBranchesLines.get(lineIndex));
		double prefMag = Double.parseDouble(tokenizer.nextToken());
		double prefWt = Double.parseDouble(tokenizer.nextToken());
		tokenizer = new StringTokenizer(faultBranchesLines.get(++lineIndex));
		double minMag = Double.parseDouble(tokenizer.nextToken());
		double minWt = Double.parseDouble(tokenizer.nextToken());
		tokenizer = new StringTokenizer(faultBranchesLines.get(++lineIndex));
		double maxMag = Double.parseDouble(tokenizer.nextToken());
		double maxWt = Double.parseDouble(tokenizer.nextToken());
		ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
		func.set(minMag, minWt);
		func.set(prefMag, prefWt);
		func.set(maxMag, maxWt);
		return new DiscreteValueEstimate(func, true);
	}


	/**
	 * Add Background logic tree branches
	 *
	 */
	private void addBackgroundBranches() {
		backgroundOptions = new HashMap<Double, GutenbergRichterMagFreqDist>();
		
		try {
			ArrayList<String> backgroundLines = FileUtils.loadJarFile(BACKGROUND_LOGIC_TREE_FILE_NAME);
			int index=0;
			double prefWt=0, minWt=0, maxWt=0;
			for(int i=8; i<backgroundLines.size(); ++i) {
				String line = backgroundLines.get(i);
				StringTokenizer tokenizer = new StringTokenizer(line);
				double cumRate = Double.parseDouble(tokenizer.nextToken());
				double bValue = Double.parseDouble(tokenizer.nextToken());
				double minMag = Double.parseDouble(tokenizer.nextToken());
				double maxMag = Double.parseDouble(tokenizer.nextToken());
				double weight = Double.parseDouble(tokenizer.nextToken());	
				int numMag =  (int)Math.round((maxMag-minMag)/DELTA_MAG)+1;
				GutenbergRichterMagFreqDist grMFD = 
					new GutenbergRichterMagFreqDist(bValue, cumRate, minMag, maxMag, numMag);
				backgroundOptions.put(cumRate, grMFD);
				if(index == 0) {
					bckPrefCumRate = cumRate;
					prefWt = weight;
				} else if(index==1) {
					bckMinCumRate = cumRate;
					minWt = weight;
				} else if(index==2) {
					bckMaxCumRate = cumRate;
					maxWt = weight;
				}
				
				++index;
			}
			
			ParameterList backgroundParamList = new ParameterList();
			backgroundParamList.addParameter(new DoubleParameter(BACKGROUND1_PARAM_NAME, 0.0, 1.0, new Double(minWt)));
			backgroundParamList.addParameter(new DoubleParameter(BACKGROUND2_PARAM_NAME, 0.0, 1.0,new Double(prefWt)));
			backgroundParamList.addParameter(new DoubleParameter(BACKGROUND3_PARAM_NAME, 0.0, 1.0, new Double(maxWt)));
			
			this.adjustableParams.addParameter(new TreeBranchWeightsParameter(BACKGROUND, backgroundParamList));
		}catch(Exception e) {
			e.printStackTrace();
		}
	}


	/**
	 * Return the name for this class
	 *
	 * @return : return the name for this class
	 */
	public String getName(){
		return NAME;
	}


	/**
	 * get the number of Eqk Rup Forecasts in this list
	 * @return : number of eqk rup forecasts in this list
	 */
	public int getNumERFs() {
		return (Integer)numRealizationsParam.getValue();
	}
	
	/**
	 * Return the vector containing the Double values with
	 * relative weights for each ERF
	 * @return : ArrayList of Double values
	 */
	public ArrayList getRelativeWeightsList() {
		ArrayList<Double> weightList = new ArrayList<Double>();
		int numERFs = getNumERFs();
		for(int i=0; i<numERFs; ++i) weightList.add(getERF_RelativeWeight(i));
		return weightList;
	}


	/**
	 * Get the ERF in the list with the specified index. 
	 * It returns the updated forecast
	 * Index can range from 0 to getNumERFs-1
	 * 
	 * 
	 * @param index : index of Eqk rup forecast to return
	 * @return
	 */
	public EqkRupForecastAPI getERF(int index) {
		Iterator<String> it = this.adjustableParams.getParameterNamesIterator();
		while(it.hasNext()) {
			String paramName = it.next();
			
			// Background
			if(paramName.equalsIgnoreCase(BACKGROUND)) {
				ParameterList paramList = (ParameterList)adjustableParams.getValue(paramName);
				// min/max/prob background
				double minProb = (Double)paramList.getValue(BACKGROUND1_PARAM_NAME);
				double prefProb = (Double)paramList.getValue(BACKGROUND2_PARAM_NAME);
				double maxProb = (Double)paramList.getValue(BACKGROUND3_PARAM_NAME);
				ArbitrarilyDiscretizedFunc func = new ArbitrarilyDiscretizedFunc();
				func.set(this.bckMinCumRate, minProb);
				func.set(this.bckPrefCumRate, prefProb);
				func.set(this.bckMaxCumRate, maxProb);
				DiscreteValueEstimate backgroundEstimate =  new DiscreteValueEstimate(func, true);
				double randomValue = backgroundEstimate.getRandomValue();
				//System.out.println("Background:"+randomValue);
				yuccaMountainERF.setBackgroundMFD(this.backgroundOptions.get(randomValue));
				continue;
			}
			
			// do for all faults
			Object value = adjustableParams.getValue(paramName);
			if(!(value instanceof DiscreteValueEstimate)) continue;
			DiscreteValueEstimate estimate = (DiscreteValueEstimate)value;
			double randomValue = estimate.getRandomValue();
			
			//System.out.println(paramName+"\t"+randomValue);
			
		
			// Mag
			if(paramName.startsWith(MAG)) {
				String faultName = paramName.substring(MAG.length());
				yuccaMountainERF.setMeanMagForSource(faultName, randomValue);
			}
			// Moment Rate
			if(paramName.startsWith(MOMENT_RATE)) {
				String faultName = paramName.substring(MOMENT_RATE.length());
				yuccaMountainERF.setMomentRateForSource(faultName, randomValue);
			}
		}
		yuccaMountainERF.getTimeSpan().setDuration(this.timeSpan.getDuration());
		yuccaMountainERF.updateForecast();
		return yuccaMountainERF;
	}


	/**
	 * get the weight of the ERF at the specified index. 
	 * It always returns 1 because we are doing Monte Carlo simulations
	 * 
	 * @param index : index of ERF
	 * @return : relative weight of ERF
	 */
	public double getERF_RelativeWeight(int index) {
		return 1;
	}



	public static void main(String[] args) {
		YuccaMountainERF_List ymEpistemicList = new YuccaMountainERF_List();
		int numERFs = ymEpistemicList.getNumERFs();
		System.out.println("Num Branches="+numERFs);
		for(int i=0; i<5; ++i) {
			ymEpistemicList.getERF(i);
		}

	}
}
