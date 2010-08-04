/**
 * 
 */
package org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.MeanUCERF2;


import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.EventObject;
import java.util.HashMap;
import java.util.Iterator;

import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.Ellsworth_B_WG02_MagAreaRel;
import org.opensha.commons.calc.magScalingRelations.magScalingRelImpl.HanksBakun2002_MagAreaRel;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.ValueWeight;
import org.opensha.commons.data.region.CaliforniaRegions;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.param.BooleanParameter;
import org.opensha.commons.param.DoubleParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.ParameterList;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.refFaultParamDb.vo.DeformationModelSummary;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.EqkSourceAPI;
import org.opensha.sha.earthquake.ProbEqkRupture;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.EmpiricalModel;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.FaultSegmentData;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UCERF2;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.UnsegmentedSource;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.A_Faults.A_FaultSegmentedSourceGenerator;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.analysis.ParamOptions;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.A_FaultsFetcher;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.NonCA_FaultsFetcher;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.data.finalReferenceFaultParamDb.DeformationModelSummaryFinal;
import org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_Final.griddedSeis.NSHMP_GridSourceGenerator;
import org.opensha.sha.earthquake.util.EqkSourceNameComparator;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.magdist.SummedMagFreqDist;



/**
 * This was checked to make sure this is equal to the mean of what is returned from the 
 * UCERF2 Epistemic List.  
 * 
 * 
 * @author 
 *
 */
public class MeanUCERF2 extends EqkRupForecast {
	//for Debug purposes
	protected static String  C = new String("MeanUCERF2");
	protected boolean D = true;

	// name of this ERF
	public final static String NAME = new String("WGCEP (2007) UCERF2 - Single Branch");

//	ArrayList allSourceNames;


	// various summed MFDs
	protected SummedMagFreqDist bFaultSummedMFD, aFaultSummedMFD;
	protected IncrementalMagFreqDist totBackgroundMFD, cZoneSummedMFD, nonCA_B_FaultsSummedMFD;

	// background seismicity inlcude/exclude param
	public final static String BACK_SEIS_INFO = new String ("Background includes C Zones here");
	protected StringParameter backSeisParam;

	// background seismicity treated as param
	protected StringParameter backSeisRupParam;

	// For rupture offset length along fault parameter
	public final static String RUP_OFFSET_PARAM_NAME ="Rupture Offset";
	protected Double DEFAULT_RUP_OFFSET_VAL= new Double(UCERF2.RUP_OFFSET);
	protected final static String RUP_OFFSET_PARAM_UNITS = "km";
	protected final static String RUP_OFFSET_PARAM_INFO = "Length of offset for floating ruptures";
	public final static double RUP_OFFSET_PARAM_MIN = 1;
	public final static double RUP_OFFSET_PARAM_MAX = 100;
	protected DoubleParameter rupOffsetParam;
	
	// Floater Type param
	protected StringParameter floaterTypeParam;
	
	// for Cybershake Correction
	public final static String CYBERSHAKE_DDW_CORR_PARAM_NAME ="Apply CyberShake DDW Corr";
	public final static Boolean CYBERSHAKE_DDW_CORR_PARAM_DEFAULT= new Boolean(false);
	protected final static String CYBERSHAKE_DDW_CORR_PARAM_INFO = "Apply Down Dip Width Correction";
	protected BooleanParameter cybershakeDDW_CorrParam;

	
	// Probability Model Param
	public final static String PROB_MODEL_WGCEP_PREF_BLEND = "WGCEP Preferred Blend";
	public final static String PROB_MODEL_DEFAULT = PROB_MODEL_WGCEP_PREF_BLEND;
	protected StringParameter probModelParam;
	
	// Time duration
	protected final static double DURATION_DEFAULT = 30;
	protected final static double DURATION_MIN = 1;
	protected final static double DURATION_MAX = 100;

	//start time
	protected final static int START_TIME_DEFAULT = 2007;
	protected final static int START_TIME_MIN = 2007;
	protected final static int START_TIME_MAX = 2107;

	// 
	protected CaliforniaRegions.RELM_GRIDDED region = new CaliforniaRegions.RELM_GRIDDED();

	protected EmpiricalModel empiricalModel = new EmpiricalModel();

	
	protected ArrayList<UnsegmentedSource> bFaultSources;
	protected ArrayList<UnsegmentedSource> aFaultUnsegmentedSources;
	protected ArrayList<FaultRuptureSource> aFaultSegmentedSources;
	protected ArrayList<ProbEqkSource> nonCA_bFaultSources;
	protected ArrayList<ProbEqkSource> allSources;
	
	protected ArrayList<String> aFaultsBranchParamNames; // parameters that are adjusted for A_Faults
	protected ArrayList<ParamOptions> aFaultsBranchParamValues; // paramter values and their weights for A_Faults
	protected int lastParamIndex;
	
	
	protected HashMap<String, SummedMagFreqDist> sourceMFDMapping;
	protected HashMap<String, Double> sourceRakeMapping;
	protected HashMap<String, StirlingGriddedSurface> sourceGriddedSurfaceMapping;

	protected NSHMP_GridSourceGenerator nshmp_gridSrcGen = new NSHMP_GridSourceGenerator();
	protected UCERF2 ucerf2 = new UCERF2();
//	protected DeformationModelSummaryDB_DAO defModelSummaryDAO = new DeformationModelSummaryDB_DAO(DB_AccessAPI.dbConnection);
	protected DeformationModelSummaryFinal defModelSummaryFinal = new DeformationModelSummaryFinal();
	protected NonCA_FaultsFetcher nonCA_B_Faultsfetcher = new NonCA_FaultsFetcher();

	// whether we need to calculate MFDs for verification purposes
	protected boolean calcSummedMFDs = false;
	
	
	protected final static String A_FAULTS_POISS_FILENAME= "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/MeanUCERF2/Segmented_5km_Poiss.txt";
	protected final static String A_FAULTS_EMPIRICAL_FILENAME= "org/opensha/sha/earthquake/rupForecastImpl/WGCEP_UCERF_2_Final/MeanUCERF2/Segmented_5km_Emp.txt";

	/**
	 *
	 * No argument constructor
	 */
	public MeanUCERF2() {

		// create and add adj params
		initAdjParams();

		// set param defaults
		setParamDefaults();

		// put parameters in the parameter List object	
		createParamList();

//		create the timespan parameter, to allow the user to set the timespan to be
		//time independent or time dependent.
		setTimespanParameter();

		// add the change listener to parameters so that forecast can be updated
		// whenever any paramater changes
		//faultModelParam.addParameterChangeListener(this);
		rupOffsetParam.addParameterChangeListener(this);
		backSeisParam.addParameterChangeListener(this);
		backSeisRupParam.addParameterChangeListener(this);
		this.cybershakeDDW_CorrParam.addParameterChangeListener(this);
		this.probModelParam.addParameterChangeListener(this);
		this.floaterTypeParam.addParameterChangeListener(this);
		this.parameterChangeFlag = true;
	}

	/**
	 * This intializes the adjustable parameters
	 */
	private void initAdjParams() {

		// NOTE THAT VALUES SET IN THE CONSTRUCTORS ARE OVER RIDDEN BY CALLING THE setParamDefaults()
		// NETHOD AT THE END

		// background seismicity include/exclude  
		ArrayList<String> backSeisOptionsStrings = new ArrayList<String>();
		backSeisOptionsStrings.add(UCERF2.BACK_SEIS_EXCLUDE);
		backSeisOptionsStrings.add(UCERF2.BACK_SEIS_INCLUDE);
		backSeisOptionsStrings.add(UCERF2.BACK_SEIS_ONLY);
		backSeisParam = new StringParameter(UCERF2.BACK_SEIS_NAME, backSeisOptionsStrings, UCERF2.BACK_SEIS_DEFAULT);
		backSeisParam.setInfo(BACK_SEIS_INFO);
		
		// backgroud treated as point sources/finite sources
		ArrayList<String> backSeisRupStrings = new ArrayList<String>();
		backSeisRupStrings.add(UCERF2.BACK_SEIS_RUP_POINT);
		backSeisRupStrings.add(UCERF2.BACK_SEIS_RUP_FINITE);
		backSeisRupStrings.add(UCERF2.BACK_SEIS_RUP_CROSSHAIR);
		backSeisRupParam = new StringParameter(UCERF2.BACK_SEIS_RUP_NAME, backSeisRupStrings, UCERF2.BACK_SEIS_RUP_DEFAULT);


		// rup offset
		rupOffsetParam = new DoubleParameter(RUP_OFFSET_PARAM_NAME,RUP_OFFSET_PARAM_MIN,
				RUP_OFFSET_PARAM_MAX,RUP_OFFSET_PARAM_UNITS,DEFAULT_RUP_OFFSET_VAL);
		rupOffsetParam.setInfo(RUP_OFFSET_PARAM_INFO);


		cybershakeDDW_CorrParam = new BooleanParameter(CYBERSHAKE_DDW_CORR_PARAM_NAME, CYBERSHAKE_DDW_CORR_PARAM_DEFAULT);
		cybershakeDDW_CorrParam.setInfo(CYBERSHAKE_DDW_CORR_PARAM_INFO);
		
		// Floater Type Param
		ArrayList<String> floaterTypes = new ArrayList<String>();
		floaterTypes.add(UCERF2.FULL_DDW_FLOATER);
		floaterTypes.add(UCERF2.STRIKE_AND_DOWNDIP_FLOATER);
		floaterTypes.add(UCERF2.CENTERED_DOWNDIP_FLOATER);
		floaterTypeParam = new StringParameter(UCERF2.FLOATER_TYPE_PARAM_NAME, floaterTypes, UCERF2.FLOATER_TYPE_PARAM_DEFAULT);

		
		// Probability Model Param
		ArrayList<String> probModelOptions = new ArrayList<String>();
		probModelOptions.add(PROB_MODEL_WGCEP_PREF_BLEND);
		probModelOptions.add(UCERF2.PROB_MODEL_POISSON);
		probModelOptions.add(UCERF2.PROB_MODEL_BPT);
		probModelOptions.add(UCERF2.PROB_MODEL_EMPIRICAL);
		probModelParam = new StringParameter(UCERF2.PROB_MODEL_PARAM_NAME, probModelOptions, PROB_MODEL_DEFAULT);
		probModelParam.setInfo(UCERF2.PROB_MODEL_PARAM_INFO);
	}


	// Set default value for parameters
	public void setParamDefaults() {
		backSeisParam.setValue(UCERF2.BACK_SEIS_DEFAULT);
		// backgroud treated as point sources/finite soource
		backSeisRupParam.setValue(UCERF2.BACK_SEIS_RUP_DEFAULT);
		// rup offset
		rupOffsetParam.setValue(DEFAULT_RUP_OFFSET_VAL);
		// floater type
		floaterTypeParam.setValue(UCERF2.FLOATER_TYPE_PARAM_DEFAULT);
		cybershakeDDW_CorrParam.setValue(CYBERSHAKE_DDW_CORR_PARAM_DEFAULT);
		probModelParam.setValue(PROB_MODEL_DEFAULT);

	}

	/**
	 * Put parameters in theParameterList
	 */
	private void createParamList() {
		adjustableParams = new ParameterList();
		adjustableParams.addParameter(rupOffsetParam);		
		adjustableParams.addParameter(floaterTypeParam);
		adjustableParams.addParameter(backSeisParam);	
		if(!backSeisParam.getValue().equals(UCERF2.BACK_SEIS_EXCLUDE))
			adjustableParams.addParameter(backSeisRupParam);
		adjustableParams.addParameter(cybershakeDDW_CorrParam);
		adjustableParams.addParameter(probModelParam);		
	}


	/**
	 * Returns the  ith earthquake source
	 *
	 * @param iSource : index of the source needed
	 */
	public ProbEqkSource getSource(int iSource) {
//		return this.aFaultSegmentedSources.get(114);
		/**/
		if(iSource<allSources.size()) // everything but the grid sources
			return (ProbEqkSource) allSources.get(iSource);
		else {
			if(this.backSeisRupParam.getValue().equals(UCERF2.BACK_SEIS_RUP_CROSSHAIR)) {
				return nshmp_gridSrcGen.getCrosshairGriddedSource(iSource - allSources.size(), timeSpan.getDuration());				
			}
			else {
/*/ Debugging 
				Location locOfInterest = new Location(37,-121.4);
				int indexOfInterest = nshmp_gridSrcGen.getNearestLocationIndex(locOfInterest);
				if((iSource - allSources.size()) == indexOfInterest) {
					System.out.println("indexOfInterest= "+indexOfInterest+"\t"+locOfInterest.toString()+"\t"+
							nshmp_gridSrcGen.getGridLocation(indexOfInterest)+"\tsrcIndex="+iSource);
//					ProbEqkSource src = nshmp_gridSrcGen.getRandomStrikeGriddedSource(iSource - allSources.size(), timeSpan.getDuration());
//					for(int r=0; r<src.getNumRuptures(); r++)
//						System.out.println(src.getRupture(r).getMag()+"\t"+src.getRupture(r).getMeanAnnualRate(timeSpan.getDuration()));
				}
// Debugging */
				return nshmp_gridSrcGen.getRandomStrikeGriddedSource(iSource - allSources.size(), timeSpan.getDuration());
			}
		}
	}

	/**
	 * Get the number of earthquake sources
	 *
	 * @return integer
	 */
	public int getNumSources(){
//		return 1;
		/**/
		if(backSeisParam.getValue().equals(UCERF2.BACK_SEIS_INCLUDE) ||
				backSeisParam.getValue().equals(UCERF2.BACK_SEIS_ONLY))
			return allSources.size() + nshmp_gridSrcGen.getNumSources();
		else return allSources.size();
		
	}
	

	/**
	 * Get the list of all earthquake sources.
	 *
	 * @return ArrayList of Prob Earthquake sources
	 */
	public ArrayList  getSourceList(){
		ArrayList sourceList = new ArrayList();
		sourceList.addAll(allSources);
		
		boolean isBackground = backSeisParam.getValue().equals(UCERF2.BACK_SEIS_INCLUDE) ||
				backSeisParam.getValue().equals(UCERF2.BACK_SEIS_ONLY);
		
		if( isBackground &&
				this.backSeisRupParam.getValue().equals(UCERF2.BACK_SEIS_RUP_CROSSHAIR))
			sourceList.addAll(nshmp_gridSrcGen.getAllCrosshairGriddedSources(timeSpan.getDuration()));
		else if(isBackground)
			sourceList.addAll(nshmp_gridSrcGen.getAllRandomStrikeGriddedSources(timeSpan.getDuration()));

		return sourceList;
	}



	/**
	 * Return the name for this class
	 *
	 * @return : return the name for this class
	 */
	public String getName(){
		return NAME;
	}


	/* NOTE that Summed MFDs are only calculated when 
	 calcSummedMFDs  flag is set to True*/
	
	/**
	 * This includes the time dependence (if applied)
	 */
	private IncrementalMagFreqDist getTotal_B_FaultsMFD() {
		return this.bFaultSummedMFD;
	}

	private IncrementalMagFreqDist getTotal_NonCA_B_FaultsMFD() {
		return this.nonCA_B_FaultsSummedMFD;
	}
	
	/**
	 * This includes the time dependence (if applied)
	 */
	private IncrementalMagFreqDist getTotal_A_FaultsMFD() {
		return this.aFaultSummedMFD;
	}

	private IncrementalMagFreqDist getTotal_BackgroundMFD() {
		return this.totBackgroundMFD;

	}

	private IncrementalMagFreqDist getTotal_C_ZoneMFD() {
		return this.cZoneSummedMFD;
	}


	/**
	 * This includes the time dependence (if applied)
	 */
	public IncrementalMagFreqDist getTotalMFD() {
		SummedMagFreqDist totalMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG, UCERF2.NUM_MAG);
		totalMFD.addIncrementalMagFreqDist(bFaultSummedMFD);
		totalMFD.addIncrementalMagFreqDist(aFaultSummedMFD);
		totalMFD.addIncrementalMagFreqDist(totBackgroundMFD);
		totalMFD.addIncrementalMagFreqDist(cZoneSummedMFD);
		totalMFD.addIncrementalMagFreqDist(nonCA_B_FaultsSummedMFD);
		return totalMFD;
	}

	/**
	 * update the forecast
	 **/

	public void updateForecast() {
		if(this.parameterChangeFlag)  {
			
			String backSeis = (String)backSeisParam.getValue();
			allSources = new ArrayList<ProbEqkSource>();
			if(calcSummedMFDs) { // IF MFDs need to be calculated for verification purposes
				ucerf2.setTimeSpan(this.timeSpan);
				ucerf2.updateForecast();
				cZoneSummedMFD = ucerf2.getTotal_C_ZoneMFD();
				totBackgroundMFD = ucerf2.getTotal_BackgroundMFD();
				nonCA_B_FaultsSummedMFD = ucerf2.getTotal_NonCA_B_FaultsMFD();
			}

			
//			long startTime, endTime;
//			double totTime;

			// if "background only" is not selected
			if(!backSeis.equalsIgnoreCase(UCERF2.BACK_SEIS_ONLY)) {
//				startTime = System.currentTimeMillis();
				mkA_FaultSources();
//				endTime = System.currentTimeMillis();
//				totTime = ((double)(endTime-startTime))/1000.0;
//				System.out.println("A_Flt source runtime = "+totTime);
			
//				startTime = System.currentTimeMillis();
				mkB_FaultSources();
//				endTime = System.currentTimeMillis();
//				totTime = ((double)(endTime-startTime))/1000.0;
//				System.out.println("B_Flt source runtime = "+totTime);
				
//				startTime = System.currentTimeMillis();
				mkNonCA_B_FaultSources();
//				endTime = System.currentTimeMillis();
//				totTime = ((double)(endTime-startTime))/1000.0;
//				System.out.println("NonCA_B_Flt source runtime = "+totTime);
				
				// sort the arrays alphabetically
				Collections.sort(aFaultSegmentedSources, new EqkSourceNameComparator());
				Collections.sort(aFaultUnsegmentedSources, new EqkSourceNameComparator());
				Collections.sort(bFaultSources, new EqkSourceNameComparator());
				Collections.sort(nonCA_bFaultSources, new EqkSourceNameComparator());
				
				// add to the master list
				allSources.addAll(this.aFaultSegmentedSources);
				allSources.addAll(this.aFaultUnsegmentedSources);
				allSources.addAll(this.bFaultSources);
				allSources.addAll(nonCA_bFaultSources);
					
			}
			
			// if background sources are included
			if(backSeis.equalsIgnoreCase(UCERF2.BACK_SEIS_INCLUDE) || 
					backSeis.equalsIgnoreCase(UCERF2.BACK_SEIS_ONLY)) {
				String backSeisRup = (String)this.backSeisRupParam.getValue();
				if(backSeisRup.equalsIgnoreCase(UCERF2.BACK_SEIS_RUP_POINT)) {
					nshmp_gridSrcGen.setAsPointSources(true);
					//allSources.addAll(nshmp_gridSrcGen.getAllRandomStrikeGriddedSources(timeSpan.getDuration()));
					
				} else if(backSeisRup.equalsIgnoreCase(UCERF2.BACK_SEIS_RUP_FINITE)) {
					nshmp_gridSrcGen.setAsPointSources(false);
					//allSources.addAll(nshmp_gridSrcGen.getAllRandomStrikeGriddedSources(timeSpan.getDuration()));

				} else { // Cross hair ruptures
					nshmp_gridSrcGen.setAsPointSources(false);
					//allSources.addAll(nshmp_gridSrcGen.getAllCrosshairGriddedSources(timeSpan.getDuration()));

				}
				
				// Add C-zone sources
				allSources.addAll(nshmp_gridSrcGen.getAllFixedStrikeSources(timeSpan.getDuration()));
			}
			
		}
		parameterChangeFlag = false;
	}
	
	/**
	 * Make A_Fault Sources
	 *
	 */
	private void mkA_FaultSources() {
		String probModel = (String)this.probModelParam.getValue();		
		double duration = this.timeSpan.getDuration();
		double rupOffset = (Double)this.rupOffsetParam.getValue();
		boolean cybershakeDDW_Corr = (Boolean)this.cybershakeDDW_CorrParam.getValue();
/*
		// read from pre-genearated A-Faults files
		if(probModel.equalsIgnoreCase(UCERF2.PROB_MODEL_POISSON)
				&& rupOffset==5 && !cybershakeDDW_Corr && !calcSummedMFDs) {
			aFaultSegmentedSources = (ArrayList<FaultRuptureSource>)FileUtils.loadObjectFromURL(FileUtils.class.getResource("/"+A_FAULTS_POISS_FILENAME));
			for(int i=0; i<aFaultSegmentedSources.size(); ++i)
				aFaultSegmentedSources.get(i).setDuration(duration);
		}  else if(probModel.equalsIgnoreCase(UCERF2.PROB_MODEL_EMPIRICAL)
				&& rupOffset==5 && !cybershakeDDW_Corr && !calcSummedMFDs) {
			aFaultSegmentedSources = (ArrayList<FaultRuptureSource>)FileUtils.loadObjectFromURL(FileUtils.class.getResource("/"+A_FAULTS_EMPIRICAL_FILENAME));
			for(int i=0; i<aFaultSegmentedSources.size(); ++i)
				aFaultSegmentedSources.get(i).setDuration(duration);
		} else { 
*/	
			// DO For Segmented sources
			fillAdjustableParamsForA_Faults();
			sourceMFDMapping = new HashMap<String, SummedMagFreqDist>();
			sourceRakeMapping = new  HashMap<String, Double> ();
			sourceGriddedSurfaceMapping = new HashMap<String, StirlingGriddedSurface>();
			findBranches(0,1);
			aFaultSegmentedSources = new ArrayList<FaultRuptureSource>();
			if(calcSummedMFDs) aFaultSummedMFD = new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG, UCERF2.NUM_MAG); 
			// iterate over all rupture sources
			Iterator<String> it = sourceMFDMapping.keySet().iterator();
			while(it.hasNext()) {
				String name = it.next();
				if(calcSummedMFDs) aFaultSummedMFD.addIncrementalMagFreqDist(sourceMFDMapping.get(name));
				FaultRuptureSource faultRupSrc = new FaultRuptureSource(sourceMFDMapping.get(name), 
						sourceGriddedSurfaceMapping.get(name),
						sourceRakeMapping.get(name),
						duration);
				faultRupSrc.setName(name);
				//System.out.println("*******"+name+"\n"+sourceMFDMapping.get(name));
				aFaultSegmentedSources.add(faultRupSrc);
			}
//		}
		//FileUtils.saveObjectInFile(this.A_FAULTS_POISS_FILENAME, aFaultSegmentedSources);
		//FileUtils.saveObjectInFile(this.A_FAULTS_EMPIRICAL_FILENAME, aFaultSegmentedSources);
		// make unsegmnted A-Fault Sources
		mkUnsegmentedA_FaultSources();
		
//		for(int i=0; i<aFaultSegmentedSources.size();i++)
//			System.out.println(i+"\t"+aFaultSegmentedSources.get(i).getName());
	}

	private void mkUnsegmentedA_FaultSources() {
		double rupOffset = ((Double)this.rupOffsetParam.getValue()).doubleValue();
		double empiricalModelWt=0.0;
		double duration = this.timeSpan.getDuration();
		String probModel = (String)this.probModelParam.getValue();
		if(probModel.equals(UCERF2.PROB_MODEL_BPT) || probModel.equals(UCERF2.PROB_MODEL_POISSON) ) empiricalModelWt = 0;
		else if(probModel.equals(UCERF2.PROB_MODEL_EMPIRICAL)) empiricalModelWt = 1;
		else if(probModel.equals(PROB_MODEL_WGCEP_PREF_BLEND)) empiricalModelWt = 0.3;

		// DO for unsegmented sources
		aFaultUnsegmentedSources = new ArrayList<UnsegmentedSource>();
		A_FaultsFetcher aFaultsFetcher = ucerf2.getA_FaultsFetcher();
		// get deformation model summaries
		DeformationModelSummary defModelSummary2_1 = defModelSummaryFinal.getDeformationModel("D2.1");
		DeformationModelSummary defModelSummary2_2 = defModelSummaryFinal.getDeformationModel("D2.2");
		DeformationModelSummary defModelSummary2_3 = defModelSummaryFinal.getDeformationModel("D2.3");
		
		double wt = 0.5;
		aFaultsFetcher.setDeformationModel(defModelSummary2_1, true);
		ArrayList<FaultSegmentData> faultSegmentList = aFaultsFetcher.getFaultSegmentDataList(true);
		ArrayList<Double> moRateList = new ArrayList<Double>();
		for(int i=0; i<faultSegmentList.size(); ++i)
			moRateList.add(wt*faultSegmentList.get(i).getTotalMomentRate());
		wt = 0.2;
		aFaultsFetcher.setDeformationModel(defModelSummary2_2, true);
		faultSegmentList = aFaultsFetcher.getFaultSegmentDataList(true);
		for(int i=0; i<faultSegmentList.size(); ++i) {
			double newMoRate = moRateList.get(i) + wt*faultSegmentList.get(i).getTotalMomentRate();
			moRateList.set(i, newMoRate);
		}
		wt = 0.3;
		aFaultsFetcher.setDeformationModel(defModelSummary2_3, true);
		faultSegmentList = aFaultsFetcher.getFaultSegmentDataList(true);
	
		boolean ddwCorr = (Boolean)cybershakeDDW_CorrParam.getValue();
		int floaterType = this.getFloaterType();
		for(int i=0; i<faultSegmentList.size(); ++i) {
			double newMoRate = moRateList.get(i) + wt*faultSegmentList.get(i).getTotalMomentRate();
			moRateList.set(i, newMoRate);
			UnsegmentedSource unsegmentedSource = new UnsegmentedSource(faultSegmentList.get(i),  
					empiricalModel, rupOffset, 0.0, 0.0,  0.1, empiricalModelWt,  
					duration, moRateList.get(i), 0, ddwCorr, floaterType, Double.NaN);
			aFaultUnsegmentedSources.add(unsegmentedSource);
			//			System.out.println(source.getName());
			if(calcSummedMFDs) {
				int numRups = unsegmentedSource.getNumRuptures();
				double mag, rate;
				for(int rupIndex=0; rupIndex<numRups; ++rupIndex) {
					ProbEqkRupture rup = unsegmentedSource.getRupture(rupIndex);
					mag = rup.getMag();
					rate = rup.getMeanAnnualRate(duration);
					aFaultSummedMFD.add(mag, rate); // apply weight of unsegmented model
				}
			}
		}
		
	}
	
	/**
	 * Get the Types of floaters desired
	 * @param floaterType - FULL_DDW_FLOATER (0) = only along strike ( rupture full DDW); 
	 *                      STRIKE_AND_DOWNDIP_FLOATER (1) = float along strike and down dip;
	 *                      CENTERED_DOWNDIP_FLOATER (2) = float along strike & centered down dip

	 * @return
	 */
	protected int getFloaterType() {
		String floaterType = (String)floaterTypeParam.getValue();
		if(floaterType.equalsIgnoreCase(UCERF2.FULL_DDW_FLOATER)) return UnsegmentedSource.FULL_DDW_FLOATER;
		else if(floaterType.equalsIgnoreCase(UCERF2.STRIKE_AND_DOWNDIP_FLOATER)) return UnsegmentedSource.STRIKE_AND_DOWNDIP_FLOATER;
		else if(floaterType.equalsIgnoreCase(UCERF2.CENTERED_DOWNDIP_FLOATER)) return UnsegmentedSource.CENTERED_DOWNDIP_FLOATER;
		throw new RuntimeException("Unsupported Floating ruptures option");
	}
	
	/**
	 * Calculate MFDs
	 * 
	 * @param paramIndex
	 * @param weight
	 */
	private void findBranches(int paramIndex, double weight) {
		ParamOptions options = this.aFaultsBranchParamValues.get(paramIndex);
		String paramName = this.aFaultsBranchParamNames.get(paramIndex);
		int numValues = options.getNumValues();
		for(int i=0; i<numValues; ++i) {
			double newWt;
			if(ucerf2.getAdjustableParameterList().containsParameter(paramName)) {
				ucerf2.getParameter(paramName).setValue(options.getValue(i));	
				newWt = weight * options.getWeight(i);
			} else {
				if(i==0) newWt=weight;
				else return;
			}
			if(paramIndex==lastParamIndex) { // if it is last paramter in list, make A_Faults
				mkA_FaultSegmentedSourceGenerators(newWt);
			} else { // recursion 
				findBranches(paramIndex+1, newWt);
			}
		}
	}
	
	
	private void mkA_FaultSegmentedSourceGenerators(double weight) {
		//System.out.println(weight);
		double relativeA_PrioriWeight = ((Double)ucerf2.getParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME).getValue()).doubleValue();
		double relativeSegRateWeight = UCERF2.REL_SEG_RATE_WT_PARAM_DEFAULT;
		double magSigma  = UCERF2.MAG_SIGMA_DEFAULT;
		double magTruncLevel = UCERF2.TRUNC_LEVEL_DEFAULT;
		boolean isAseisReducesArea = true;
		double meanMagCorrection = UCERF2.MEAN_MAG_CORRECTION_DEFAULT;
		boolean wtedInversion = true;
		ParameterList rupModels = (ParameterList) (this.ucerf2.getParameter(UCERF2.SEGMENTED_RUP_MODEL_TYPE_NAME).getValue());
		boolean ddwCorr = (Boolean)cybershakeDDW_CorrParam.getValue();

		
		A_FaultsFetcher aFaultsFetcher = ucerf2.getA_FaultsFetcher();
		DeformationModelSummary defModelSummary = defModelSummaryFinal.getDeformationModel((String)ucerf2.getParameter(UCERF2.DEFORMATION_MODEL_PARAM_NAME).getValue());
		aFaultsFetcher.setDeformationModel(defModelSummary, false);
		
		// this gets a list of FaultSegmentData objects (one for each A fault, and for the deformation model previously set)
		ArrayList aFaultSegmentData = aFaultsFetcher.getFaultSegmentDataList(isAseisReducesArea);

		double duration = timeSpan.getDuration();
		double startYear = Double.NaN, aperiodicity = Double.NaN;
		boolean isSegDependentAperiodicity = false;
		String probModel = (String)ucerf2.getParameter(UCERF2.PROB_MODEL_PARAM_NAME).getValue();
		
		if(probModel.equals(UCERF2.PROB_MODEL_BPT)) { // for time dependence
			startYear = this.timeSpan.getStartTimeYear();
			isSegDependentAperiodicity = false;
			aperiodicity = ((Double)ucerf2.getParameter(UCERF2.APERIODICITY_PARAM_NAME).getValue()).doubleValue();
		}
		
		ParameterAPI param = ucerf2.getParameter(UCERF2.REL_A_PRIORI_WT_PARAM_NAME);
		
		double minA_FaultRate1, minA_FaultRate2;
		if(((Double)param.getValue()).doubleValue()==1e10) {
			minA_FaultRate1 = 0.0;
			minA_FaultRate2 = 0.0;	
		} else {
			minA_FaultRate1 = UCERF2.MIN_A_FAULT_RATE_1_DEFAULT;
			minA_FaultRate2 = UCERF2.MIN_A_FAULT_RATE_2_DEFAULT;	
		}
		
		String slipModel = A_FaultSegmentedSourceGenerator.TAPERED_SLIP_MODEL;
		double totMoRateReduction = 0.1;
		
		for(int i=0; i<aFaultSegmentData.size(); ++i) {
			FaultSegmentData segmentData = (FaultSegmentData) aFaultSegmentData.get(i);
			ValueWeight[] aPrioriRates = aFaultsFetcher.getAprioriRupRates(segmentData.getFaultName(), (String)rupModels.getValue(segmentData.getFaultName()));

			// set the min-rate constraint and correct bogus, indicator rates in aPrioriRates
			double minRates[] = new double[aPrioriRates.length];
			double minRateFrac1 = minA_FaultRate1; // for unknown ruptures
			double minRateFrac2 = minA_FaultRate2; // for unlikely ruptures
			double minRate = Double.MAX_VALUE;
			for(int rup=0; rup<aPrioriRates.length; rup++) // find minimum, ignoring values less than zero which are indicators
				if(aPrioriRates[rup].getValue() < minRate && aPrioriRates[rup].getValue() >= 0) minRate = aPrioriRates[rup].getValue();
			for(int rup=0; rup<aPrioriRates.length; rup++) {
				double rate = aPrioriRates[rup].getValue();
				if(rate >= 0) minRates[rup] = minRate*minRateFrac1; // treat it as unknowns
				else if (rate == -1) {
					minRates[rup] = minRate*minRateFrac1;
					aPrioriRates[rup].setValue(0.0);   // over ride bogus indicator value with zero
				}
				else if (rate == -2) {
					minRates[rup] = minRate*minRateFrac2;
					aPrioriRates[rup].setValue(0.0);   // over ride bogus indicator value with zero
				}
				else 
					throw new RuntimeException("Problem with a-priori rates for fault "+segmentData.getFaultName());
//				System.out.println(rup+"  "+(float)minRates[rup]+"  "+segmentData.getFaultName());
			}

			A_FaultSegmentedSourceGenerator aFaultSourceGenerator = new A_FaultSegmentedSourceGenerator(segmentData, 
					ucerf2.getMagAreaRelationship(), slipModel, aPrioriRates, magSigma, 
					magTruncLevel, totMoRateReduction, meanMagCorrection,minRates, 
					wtedInversion, relativeSegRateWeight, relativeA_PrioriWeight);
			ArrayList<FaultRuptureSource> sources = new ArrayList<FaultRuptureSource>();
			if(probModel.equals(UCERF2.PROB_MODEL_POISSON)) // time Independent
				sources.addAll(aFaultSourceGenerator.getTimeIndependentSources(duration));
			else if(probModel.equals(UCERF2.PROB_MODEL_BPT)) 
				sources.addAll(aFaultSourceGenerator.getTimeDependentSources(duration, startYear, aperiodicity, isSegDependentAperiodicity));
			 else // Empirical Model
				sources.addAll(aFaultSourceGenerator.getTimeDepEmpiricalSources(duration, empiricalModel));
			
			String faultName = segmentData.getFaultName();
			for(int srcIndex=0; srcIndex<sources.size(); ++srcIndex) {
				FaultRuptureSource source  = sources.get(srcIndex);
				String key = faultName +";"+source.getName();
				if(!sourceMFDMapping.containsKey(key)) {
					sourceMFDMapping.put(key, new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG, UCERF2.NUM_MAG));

					sourceRakeMapping.put(key, aFaultSourceGenerator.getAveRakeForSource(srcIndex));
					this.sourceGriddedSurfaceMapping.put(key, aFaultSourceGenerator.getCombinedGriddedSurfaceForSource(srcIndex, ddwCorr));

// Debugging tests:		
/*
 StirlingGriddedSurface surf = 		aFaultSourceGenerator.getCombinedGriddedSurfaceForSource(srcIndex, ddwCorr);
 
 if(faultName.equals("San Jacinto") && srcIndex==17 ){
	 FaultTrace ft = surf.getFaultTrace();
	 for(int loc=0; loc <ft.size(); loc++)
		 System.out.println((float)ft.getLocationAt(loc).getLatitude()+"\t"+(float)ft.getLocationAt(loc).getLongitude());
//	 aFaultSourceGenerator.writeSegmentsInSource(srcIndex);
 }
 */
 //if(faultName.equals("San Jacinto")) System.out.println(srcIndex+"\t"+key+"\t"+surf.getLocation(0, 0).toString()+"\t"+surf.getLocation(0, surf.getNumCols()-1).toString());
 //System.out.println(key+"\t"+surf.getLocation(0, 0).toString()+"\t"+surf.getLocation(0, surf.getNumCols()-1).toString());

				}
				SummedMagFreqDist mfd = sourceMFDMapping.get(key);
				int numRups = source.getNumRuptures();
				for(int rupIndex=0; rupIndex<numRups; ++rupIndex) {
					ProbEqkRupture rupture = source.getRupture(rupIndex);
					mfd.add(rupture.getMag(), rupture.getMeanAnnualRate(duration)*weight);
				}
			}
		}
	}
	
	
	/**
	 * Paramters that are adjusted in the runs
	 *
	 */
	private void fillAdjustableParamsForA_Faults() {
		if(ucerf2.getAdjustableParameterList().containsParameter(UCERF2.SEG_DEP_APERIODICITY_PARAM_NAME))
			ucerf2.getParameter(UCERF2.SEG_DEP_APERIODICITY_PARAM_NAME).setValue(new Boolean(false));
		this.aFaultsBranchParamNames = new ArrayList<String>();
		this.aFaultsBranchParamValues = new ArrayList<ParamOptions>();
		
		// Deformation model
		aFaultsBranchParamNames.add(UCERF2.DEFORMATION_MODEL_PARAM_NAME);
		ParamOptions options = new ParamOptions();
		options.addValueWeight("D2.1", 0.5);
		options.addValueWeight("D2.2", 0.2);
		options.addValueWeight("D2.3", 0.3);
		aFaultsBranchParamValues.add(options);
		
		// Mag Area Rel
		aFaultsBranchParamNames.add(UCERF2.MAG_AREA_RELS_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(Ellsworth_B_WG02_MagAreaRel.NAME, 0.5);
		options.addValueWeight(HanksBakun2002_MagAreaRel.NAME, 0.5);
		aFaultsBranchParamValues.add(options);
		
		// A-Fault solution type
		aFaultsBranchParamNames.add(UCERF2.RUP_MODEL_TYPE_NAME);
		options = new ParamOptions();
		options.addValueWeight(UCERF2.SEGMENTED_A_FAULT_MODEL, 0.9);
		aFaultsBranchParamValues.add(options);
		
		// Apriori wt param
		aFaultsBranchParamNames.add(UCERF2.REL_A_PRIORI_WT_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(1e-4), 0.5);
		options.addValueWeight(new Double(1e10), 0.5);
		aFaultsBranchParamValues.add(options);
		
		
		// Prob Model
		
		aFaultsBranchParamNames.add(UCERF2.PROB_MODEL_PARAM_NAME);
		options = new ParamOptions();
		// see the option chosen for Prob Model
		String probModel = (String)this.probModelParam.getValue();
		if(probModel.equals(UCERF2.PROB_MODEL_BPT)){
			options.addValueWeight(UCERF2.PROB_MODEL_BPT, 1.0);
		} else if (probModel.equals(UCERF2.PROB_MODEL_POISSON) ) {
			options.addValueWeight(UCERF2.PROB_MODEL_POISSON, 1.0);
		}
		else if(probModel.equals(UCERF2.PROB_MODEL_EMPIRICAL)) {
			options.addValueWeight(UCERF2.PROB_MODEL_EMPIRICAL, 1.0);
		}
		else if(probModel.equals(PROB_MODEL_WGCEP_PREF_BLEND)) {
			options.addValueWeight(UCERF2.PROB_MODEL_BPT, 0.7);
			options.addValueWeight(UCERF2.PROB_MODEL_EMPIRICAL, 0.3);
		}
		aFaultsBranchParamValues.add(options);
		
		//	BPT parameter setting
		aFaultsBranchParamNames.add(UCERF2.APERIODICITY_PARAM_NAME);
		options = new ParamOptions();
		options.addValueWeight(new Double(0.3), 0.2);
		options.addValueWeight(new Double(0.5), 0.5);
		options.addValueWeight(new Double(0.7), 0.3);
		aFaultsBranchParamValues.add(options);
		
		lastParamIndex = aFaultsBranchParamNames.size()-1;
	}


	
	/**
	 * Make B-Faults sources and caluculate B-Faults Total Summed MFD
	 */
	private void mkB_FaultSources() {
		A_FaultsFetcher aFaultsFetcher = ucerf2.getA_FaultsFetcher();
		B_FaultsFetcherForMeanUCERF bFaultsFetcher = new B_FaultsFetcherForMeanUCERF(aFaultsFetcher, true);
		bFaultSources = new ArrayList<UnsegmentedSource> ();
		double rupOffset = ((Double)this.rupOffsetParam.getValue()).doubleValue();
		double empiricalModelWt=0.0;
		
		String probModel = (String)this.probModelParam.getValue();
		if(probModel.equals(UCERF2.PROB_MODEL_BPT) || probModel.equals(UCERF2.PROB_MODEL_POISSON) ) empiricalModelWt = 0;
		else if(probModel.equals(UCERF2.PROB_MODEL_EMPIRICAL)) empiricalModelWt = 1;
		else if(probModel.equals(PROB_MODEL_WGCEP_PREF_BLEND)) empiricalModelWt = 0.3;
		
		double duration = this.timeSpan.getDuration();
		double wt = 0.5;
		boolean ddwCorr = (Boolean)cybershakeDDW_CorrParam.getValue();
		int floaterType = this.getFloaterType();
		
//		System.out.println("getB_FaultsCommonConnOpts, wt="+wt);
		ArrayList<FaultSegmentData> faultSegDataList = bFaultsFetcher.getB_FaultsCommonConnOpts();
		addToB_FaultSources(rupOffset, empiricalModelWt, duration, wt, faultSegDataList, ddwCorr, floaterType);
		
		wt=1.0;
//		System.out.println("getB_FaultsCommonNoConnOpts, wt="+wt);
		faultSegDataList  = bFaultsFetcher.getB_FaultsCommonNoConnOpts();
		addToB_FaultSources(rupOffset, empiricalModelWt, duration, wt, faultSegDataList, ddwCorr, floaterType);
		
		wt=0.25;
//		System.out.println("getB_FaultsUniqueToF2_1ConnOpts, wt="+wt);
		faultSegDataList  = bFaultsFetcher.getB_FaultsUniqueToF2_1ConnOpts();
		addToB_FaultSources(rupOffset, empiricalModelWt, duration, wt, faultSegDataList, ddwCorr, floaterType);
		
		wt=0.5;
//		System.out.println("getB_FaultsUniqueToF2_1NoConnOpts, wt="+wt);
		faultSegDataList  = bFaultsFetcher.getB_FaultsUniqueToF2_1NoConnOpts();
		addToB_FaultSources(rupOffset, empiricalModelWt, duration, wt, faultSegDataList, ddwCorr, floaterType);
		
		wt=0.25;
//		System.out.println("getB_FaultsUniqueToF2_2ConnOpts, wt="+wt);
		faultSegDataList  = bFaultsFetcher.getB_FaultsUniqueToF2_2ConnOpts();
		addToB_FaultSources(rupOffset, empiricalModelWt, duration, wt, faultSegDataList, ddwCorr, floaterType);
		
		wt=0.5;
//		System.out.println("getB_FaultsUniqueToF2_2NoConnOpts, wt="+wt);
		faultSegDataList  = bFaultsFetcher.getB_FaultsUniqueToF2_2NoConnOpts();
		addToB_FaultSources(rupOffset, empiricalModelWt, duration, wt, faultSegDataList, ddwCorr, floaterType);
		
		wt=0.75;
//		System.out.println("getB_FaultsCommonWithUniqueConnOpts, wt="+wt);
		faultSegDataList  = bFaultsFetcher.getB_FaultsCommonWithUniqueConnOpts();
		addToB_FaultSources(rupOffset, empiricalModelWt, duration, wt, faultSegDataList, ddwCorr, floaterType);
		
		// Now calculate the B-Faults total MFD
		if(calcSummedMFDs) bFaultSummedMFD= new SummedMagFreqDist(UCERF2.MIN_MAG, UCERF2.MAX_MAG, UCERF2.NUM_MAG);
		
		double mag, rate;
		for(int srcIndex=0; srcIndex<bFaultSources.size(); ++srcIndex) {
			UnsegmentedSource source = bFaultSources.get(srcIndex);
			//System.out.println(source.getName());
			if(calcSummedMFDs) {
				int numRups = source.getNumRuptures();
				for(int rupIndex=0; rupIndex<numRups; ++rupIndex) {
					ProbEqkRupture rup = source.getRupture(rupIndex);
					mag = rup.getMag();
					rate = rup.getMeanAnnualRate(duration);
					bFaultSummedMFD.add(mag, rate);
				}
			}
		}
	}

	/**
	 * MAe sources from FaultSegmentData List and to bFaultList
	 * @param rupOffset
	 * @param empiricalModelWt
	 * @param duration
	 * @param wt
	 * @param faultSegDataList
	 */
	private void addToB_FaultSources(double rupOffset, double empiricalModelWt, double duration, double wt, 
			ArrayList<FaultSegmentData> faultSegDataList, boolean ddwCorr, int floaterType) {
		for(int i=0; i<faultSegDataList.size(); ++i) {
			if(faultSegDataList.get(i).getFaultName().equalsIgnoreCase("Mendocino")) continue;
//			System.out.println("\t"+faultSegDataList.get(i).getFaultName()+"\t"+wt);
			bFaultSources.add(new UnsegmentedSource(faultSegDataList.get(i), 
					empiricalModel,  rupOffset,  wt, 
					empiricalModelWt, duration, ddwCorr, floaterType, Double.NaN));
		}
	}
	
	/**
	 * Make Non-CA B-Faults Sources
	 *
	 */
	private void mkNonCA_B_FaultSources() {
		double magSigma  = UCERF2.MAG_SIGMA_DEFAULT;
		double magTruncLevel = UCERF2.TRUNC_LEVEL_DEFAULT;
		double duration = timeSpan.getDuration();
		double rupOffset = ((Double)this.rupOffsetParam.getValue()).doubleValue();

		EmpiricalModel empiricalModel  = null;
		if(this.probModelParam.getValue().equals(UCERF2.PROB_MODEL_EMPIRICAL)) empiricalModel = this.empiricalModel;
		nonCA_bFaultSources = nonCA_B_Faultsfetcher.getSources(UCERF2.NON_CA_SOURCES_FILENAME, duration, magSigma, magTruncLevel,rupOffset, empiricalModel);
	}
	

	/**
	 * Creates the timespan object based on if it is time dependent or time independent model.
	 */
	private void setTimespanParameter() {
		if (this.probModelParam.getValue().equals(UCERF2.PROB_MODEL_BPT) ||
				probModelParam.getValue().equals(PROB_MODEL_WGCEP_PREF_BLEND)) {
			// create the time-dep timespan object with start time and duration in years
			timeSpan = new TimeSpan(TimeSpan.YEARS, TimeSpan.YEARS);
			// set duration
			timeSpan.setDuractionConstraint(DURATION_MIN, DURATION_MAX);
			timeSpan.setDuration(DURATION_DEFAULT);
			// set the start year 
			timeSpan.setStartTimeConstraint(TimeSpan.START_YEAR, START_TIME_MIN, START_TIME_MAX);
			timeSpan.setStartTime(START_TIME_DEFAULT);

			timeSpan.addParameterChangeListener(this);
		}
		else {
			// create the time-ind timespan object with start time and duration in years
			timeSpan = new TimeSpan(TimeSpan.NONE, TimeSpan.YEARS);
			timeSpan.setDuration(DURATION_DEFAULT);
			timeSpan.addParameterChangeListener(this);

		}
	}

	/**
	 *  This is the main function of this interface. Any time a control
	 *  paramater or independent paramater is changed by the user in a GUI this
	 *  function is called, and a paramater change event is passed in.
	 *
	 *  This sets the flag to indicate that the sources need to be updated
	 *
	 * @param  event
	 */
	public void parameterChange(ParameterChangeEvent event) {
		super.parameterChange(event);
		String paramName = event.getParameterName();
		if(paramName.equalsIgnoreCase(RUP_OFFSET_PARAM_NAME)) {
			
		} else if(paramName.equalsIgnoreCase(UCERF2.PROB_MODEL_PARAM_NAME)) {
			createParamList();
			setTimespanParameter();
			timeSpanChange(new EventObject(timeSpan));
		} else if (paramName.equalsIgnoreCase(UCERF2.BACK_SEIS_NAME)) {
			createParamList();
		} else if(paramName.equalsIgnoreCase(UCERF2.BACK_SEIS_RUP_NAME)) { 

		} 
		parameterChangeFlag = true;
	}


	/**
	 *  
	 *
	 * @param  event  The Event which triggered this function call
	 */
	public void timeSpanChange(EventObject event) {
		parameterChangeFlag = true;
	}
	

	public void writeB_FaultMgt67probs() {
		for(int isrc=0; isrc<bFaultSources.size(); isrc++) {
			UnsegmentedSource source = bFaultSources.get(isrc);
			System.out.println(source.getName()+"\t"+source.computeTotalProbAbove(6.7));
		}
	}

	public void writeFaultSourceSurfaceOutlines() {
		ArrayList<EqkSourceAPI> allFltSources = new ArrayList<EqkSourceAPI>();
		allFltSources.addAll(aFaultSegmentedSources);
		allFltSources.addAll(aFaultUnsegmentedSources);
		allFltSources.addAll(bFaultSources);
		allFltSources.addAll(nonCA_bFaultSources);
		try {
			FileWriter fw = new FileWriter("meanUCERF2_FltSrcSurfOutln.txt");
			for(int isrc=0; isrc<allFltSources.size(); isrc++) {
				EqkSourceAPI source = allFltSources.get(isrc);
				LocationList locList = source.getSourceSurface().getSurfacePerimeterLocsList();
				System.out.println("# "+source.getName());
				fw.write("# "+source.getName()+"\n");
				for(int i=0;i<locList.size();i++) {
					Location loc = locList.get(i);
//					System.out.println((float)loc.getLatitude()+"\t"+(float)loc.getLongitude()+"\t"+(float)loc.getDepth());
					fw.write((float)loc.getLatitude()+"\t"+(float)loc.getLongitude()+"\t"+(float)loc.getDepth()+"\n");
				}
			}
			fw.close();
	    }
		catch (FileNotFoundException ex) {
		}
		catch (IOException ex) {
		}
	}
	
	/**
	 * This was written to verify that this class is identical to org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2
	 * 
	 * The test was passed
	 * 
	 * This test is no longer valid because the sources have since been sorted by name here 
	 * (although you could comment out this sorting in the updataForecast() method)
	 */
	public void testFinalMeanUCERF2() {
		
		MeanUCERF2 meanFinalUCERF2 = new MeanUCERF2();
		meanFinalUCERF2.calcSummedMFDs  =false;
		meanFinalUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		meanFinalUCERF2.updateForecast();
		
		org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2 oldMeanUCERF2 = new org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2();
		oldMeanUCERF2.calcSummedMFDs  =false;
		oldMeanUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		oldMeanUCERF2.updateForecast();
		
		System.out.println("OLD numSrc ="+oldMeanUCERF2.getNumSources());
		System.out.println("NEW numSrc ="+meanFinalUCERF2.getNumSources());
		
		int numSrc = oldMeanUCERF2.getNumSources();
		
		for(int i=0; i<numSrc;i++) {
			System.out.println("src "+i);
			int numRup = oldMeanUCERF2.getNumRuptures(i);
			if(numRup != meanFinalUCERF2.getNumRuptures(i))
				System.out.println("Error: Number of ruptures differs for source "+i);
			for(int r=0; r<numRup; r++) {
				ProbEqkRupture oldRup = oldMeanUCERF2.getRupture(i, r);
				ProbEqkRupture newRup = meanFinalUCERF2.getRupture(i, r);
				double fractDiff = Math.abs((oldRup.getProbability()-newRup.getProbability())/newRup.getProbability());
				if(fractDiff > 0.01)
					System.out.println("DIFFERENCE: "+fractDiff+" at src "+i+" and rup "+r);
//				System.out.println(fractDiff);
				
			}
		}
	}

	
	/**
	 * This tests this class after the resorting of sources was done to 
	 * make sure the number of sources and total rate hadn't changed
	 * (everything looks good).
	 */
	public void testResortedSources() {
		
		// New ERF
		MeanUCERF2 meanFinalUCERF2 = new MeanUCERF2();
		meanFinalUCERF2.calcSummedMFDs  =false;
		meanFinalUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		meanFinalUCERF2.updateForecast();
		
		// Old ERF
		org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2 oldMeanUCERF2 = new org.opensha.sha.earthquake.rupForecastImpl.WGCEP_UCERF_2_3.MeanUCERF2.MeanUCERF2();
		oldMeanUCERF2.calcSummedMFDs  =false;
		oldMeanUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		oldMeanUCERF2.updateForecast();
		
		System.out.println("OLD numSrc ="+oldMeanUCERF2.getNumSources());
		System.out.println("NEW numSrc ="+meanFinalUCERF2.getNumSources());
		
		int numSrc = oldMeanUCERF2.getNumSources();
		
		double totRateOld=0, totRateNew=0;
		for(int i=0; i<numSrc;i++) {
			System.out.println("src "+i);
			
			for(int r=0; r<oldMeanUCERF2.getNumRuptures(i); r++)
				totRateOld += oldMeanUCERF2.getRupture(i, r).getMeanAnnualRate(DURATION_DEFAULT);

			for(int r=0; r<meanFinalUCERF2.getNumRuptures(i); r++)
				totRateNew += meanFinalUCERF2.getRupture(i, r).getMeanAnnualRate(DURATION_DEFAULT);
		}
		System.out.println("OLD tot rate ="+totRateOld);
		System.out.println("NEW tot rate ="+totRateNew);
	}
	
	

	// this is temporary for testing purposes
	public static void main(String[] args) {
		MeanUCERF2 meanFinalUCERF2 = new MeanUCERF2();
		meanFinalUCERF2.calcSummedMFDs  =false;
		meanFinalUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
		meanFinalUCERF2.updateForecast();

		
//		MeanUCERF2 meanUCERF2 = new MeanUCERF2();
//		meanUCERF2.testResortedSources();
		
//		meanUCERF2.testFinalMeanUCERF2();
		
//		long startTime = System.currentTimeMillis();
//		MeanUCERF2 meanUCERF2 = new MeanUCERF2();
//		meanUCERF2.calcSummedMFDs  =false;
//		meanUCERF2.setParameter(UCERF2.BACK_SEIS_NAME, UCERF2.BACK_SEIS_EXCLUDE);
//		meanUCERF2.setParameter(UCERF2.PROB_MODEL_PARAM_NAME, UCERF2.PROB_MODEL_POISSON);
//		meanUCERF2.getTimeSpan().setDuration(30.0);
//		meanUCERF2.setParameter(UCERF2.FLOATER_TYPE_PARAM_NAME, UCERF2.CENTERED_DOWNDIP_FLOATER);
//		meanUCERF2.updateForecast();
//		long endTime = System.currentTimeMillis();
//		double totTime = ((double)(endTime-startTime))/1000.0;
//		System.out.println("runtime = "+totTime);
//		meanUCERF2.writeB_FaultMgt67probs();
//		meanUCERF2.writeFaultSourceSurfaceOutlines();
//		for(int src=0; src<meanUCERF2.getNumSources(); src++)
//			System.out.println(src+"\t"+meanUCERF2.getSource(src).getName());
		/*
		System.out.println(meanUCERF2.getTotal_A_FaultsMFD().getCumRateDistWithOffset());
		System.out.println(meanUCERF2.getTotal_B_FaultsMFD().getCumRateDistWithOffset());
		System.out.println(meanUCERF2.getTotal_C_ZoneMFD().getCumRateDistWithOffset());
		System.out.println(meanUCERF2.getTotal_NonCA_B_FaultsMFD().getCumRateDistWithOffset());
		System.out.println(meanUCERF2.getTotal_BackgroundMFD().getCumRateDistWithOffset());
		System.out.println(meanUCERF2.getTotalMFD().getCumRateDistWithOffset());
		*/
	}
}