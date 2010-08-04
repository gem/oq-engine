package scratch.bbradley;
//package org.opensha.sha.earthquake.rupforecastImpl.NewZealand_ERF;

import java.io.IOException;
import java.util.ArrayList;
import java.util.StringTokenizer;

import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.geo.Location;
import org.opensha.commons.param.StringParameter;
import org.opensha.commons.param.event.ParameterChangeEvent;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.EqkRupForecast;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.FaultRuptureSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.faultSurface.EvenlyGriddedSurface;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.faultSurface.StirlingGriddedSurface;
import org.opensha.sha.magdist.GaussianMagFreqDist;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;

/**
 * <p>Title: New Zealand Eqk Rup Forecast</p>
 * <p>Description: .
 * Preliminary version  Has been developed by modifying the input files
 * WGCEP_UCERF1_EqkRupForecast.java and YuccaMountainERF.java.
 * </p>
 * <p>Copyright: Copyright (c) 2009</p>
 * <p>Company: </p>
 * @author : Brendon Bradley
 * @Date : May, 2009
 * @version 1.0
 */

public class NewZealandERFv1 extends EqkRupForecast {

	//for Debug purposes
	private static String  C = new String("NZ_ERF");
	private boolean D = false;
	// name of this ERF
	public final static String NAME = new String("NewZealand_ERF - unverified");


//	private final static String FAULT_SOURCE_FILENAME = "org/opensha/sha/earthquake/rupForecastImpl/NewZealand/NZ_FLTmodel.txt";
//	private final static String BG_FILE_NAME = "org/opensha/sha/earthquake/rupForecastImpl/NewZealand/NZ_BKmodel.txt";
//	private final static String FAULT_SOURCE_FILENAME = "scratch/bbradley/NZ_FLTmodeldraft.txt";
//	private final static String BG_FILE_NAME = "scratch/bbradley/NZ_BKmodeldraft.txt";
	private final static String FAULT_SOURCE_FILENAME = "scratch/bbradley/NZ_FLTmodel0909.txt";
	private final static String BG_FILE_NAME = "scratch/bbradley/NZ_BKmodeldraft.txt";
	
	// Min/Max/Num Mags for Mag Freq Dist for making fault sources
	private final static double MIN_MAG = 5.0;
	private final static double MAX_MAG = 9.0;
	private final static int NUM_MAGS = 41;

	// Default Grid Spacing for making Evenly Gridded Surface
	private final static double DEFAULT_GRID_SPACING = 1.0;


	public final static String BACK_SEIS_NAME = new String ("Background Seismicity");
	public final static String BACK_SEIS_INCLUDE = new String ("Include");
	public final static String BACK_SEIS_EXCLUDE = new String ("Exclude");
	private StringParameter backSeisParam;

	private int numBkSources = 0;
	private ArrayList<String> bkSourceNames = new ArrayList<String>();
	private ArrayList<Location> bkSourceLocation = new ArrayList<Location>();
	private ArrayList<IncrementalMagFreqDist> bkMagFD = new ArrayList<IncrementalMagFreqDist>();
	private ArrayList<Double> bkRake = new ArrayList<Double>(); 
	private ArrayList<Double> bkDip = new ArrayList<Double>(); 
	private ArrayList<Double> bkMinMag = new ArrayList<Double>(); 
		
	private ArrayList<String> sourceNames = new ArrayList<String>();
	private ArrayList<Double> sourceMags = new ArrayList<Double>();
	private ArrayList<Double> sourceSigmas = new ArrayList<Double>();
	private ArrayList<Double> sourceRakes = new ArrayList<Double>();
	private ArrayList<Double> sourceMoRates = new ArrayList<Double>();
	private ArrayList<EvenlyGriddedSurface> sourceGriddedSurface = new ArrayList<EvenlyGriddedSurface>();

	private ArrayList<ProbEqkSource> allSources = new ArrayList<ProbEqkSource>();



	public NewZealandERFv1(){
		/*
		 * note: Had to move timeSpan object up before creation of the fault sources since timeSpan is 
		 * needed in the background pointEqkSource object definition
		 */
		//create the timespan object with start time and duration in years
		timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
		timeSpan.addParameterChangeListener(this);
		timeSpan.setDuration(50);
		
		createFaultSurfaces();
		createBackRegion();
		initAdjParams();
	}


	/*
	 * Initialize the adjustable parameters
	 */
	private void initAdjParams(){	

		ArrayList<String> backSeisOptionsStrings = new ArrayList<String>();
		backSeisOptionsStrings.add(BACK_SEIS_INCLUDE);
		backSeisOptionsStrings.add(BACK_SEIS_EXCLUDE);

		backSeisParam = new StringParameter(BACK_SEIS_NAME,backSeisOptionsStrings,BACK_SEIS_INCLUDE);
		backSeisParam.addParameterChangeListener(this);

		adjustableParams.addParameter(backSeisParam);
	}


	/**
	 * Make Background sources
	 */

	private void createBackRegion(){
		try {
			ArrayList<String> fileLines = FileUtils.loadJarFile(BG_FILE_NAME);
			int size = fileLines.size();
			int j=4;
			String sourceName = fileLines.get(j);
			StringTokenizer st = new StringTokenizer(sourceName);
			String srcCode = st.nextToken();
			int srcCodeLength = srcCode.length();
			String sourceNameString = sourceName.substring(srcCodeLength);

			for(int i=5;i<size;++i){ 
				++numBkSources;
				String magDistInfo  = fileLines.get(i);
				st = new StringTokenizer(magDistInfo);
				double aVal = Double.parseDouble(st.nextToken().trim());
				double bVal = Double.parseDouble(st.nextToken().trim());
				double minMag = Double.parseDouble(st.nextToken().trim());
				double maxMag = Double.parseDouble(st.nextToken().trim());
				int numMag = Integer.parseInt(st.nextToken().trim());
				double totCumRate = Double.parseDouble(st.nextToken().trim());
				double lat = Double.parseDouble(st.nextToken().trim());
				double lon = Double.parseDouble(st.nextToken().trim());
				double depth = Double.parseDouble(st.nextToken().trim());
				double rake  = Double.parseDouble(st.nextToken().trim());
				double dip   = Double.parseDouble(st.nextToken().trim());
				IncrementalMagFreqDist backgroundMagDist = new GutenbergRichterMagFreqDist(bVal,totCumRate,minMag,maxMag,numMag);
				Location bckLocation = new Location(lat,lon,depth);
				
				this.bkSourceNames.add("backgroundSource"+numBkSources);
				this.bkSourceLocation.add(bckLocation);
				this.bkMagFD.add(backgroundMagDist);
				this.bkRake.add(rake);
				this.bkDip.add(dip);
				this.bkMinMag.add(minMag);
			}


		}catch(IOException e){
			e.printStackTrace();
		}
	}
	
	private void mkBackRegion(){
		for(int srcIndex=0; srcIndex<bkSourceNames.size(); ++srcIndex) {
			PointEqkSource rupSource = new PointEqkSource(this.bkSourceLocation.get(srcIndex),this.bkMagFD.get(srcIndex),
					timeSpan.getDuration(),this.bkRake.get(srcIndex),this.bkDip.get(srcIndex),this.bkMinMag.get(srcIndex));
			allSources.add(rupSource);
		}
	}


	/**
	 * Set Mean Mag for a fault source
	 * 
	 * @param sourceName
	 * @param mag
	 */
	public void setMeanMagForSource(String sourceName, double mag) {
		int srcIndex = sourceNames.indexOf(sourceName);
		this.sourceMags.set(srcIndex, mag);
		parameterChangeFlag = true;
	}

	/**
	 * Set Moment Rate for a fault source
	 * 
	 * @param sourceName
	 * @param momentRate
	 */
	public void setMomentRateForSource(String sourceName, double momentRate) {
		int srcIndex = sourceNames.indexOf(sourceName);
		this.sourceMoRates.set(srcIndex, momentRate);
		parameterChangeFlag = true;
	}
	

	/**
	 * 
	 * Read the file and create fault surfaces
	 *
	 */
	private void createFaultSurfaces(){
		try {
			ArrayList<String> fileLines = FileUtils.loadJarFile(FAULT_SOURCE_FILENAME);
			int size = fileLines.size();
			for(int i=7;i<size;++i){ 
				String sourceName = fileLines.get(i);
				if(sourceName.trim().equals(""))
					continue;
				StringTokenizer st = new StringTokenizer(sourceName);
				String srcCode = st.nextToken();
				++i;
				String sourceDipInfo = fileLines.get(i);
				st = new StringTokenizer(sourceDipInfo);
				double dip = Double.parseDouble(st.nextToken().trim());
				double rake = Double.parseDouble(st.nextToken().trim());
				double upperSeis = Double.parseDouble(st.nextToken().trim());
				double lowerSeis = Double.parseDouble(st.nextToken().trim());
				
				++i;
				String sourceMFD = fileLines.get(i);
				st = new StringTokenizer(sourceMFD);
				double meanMag = Double.parseDouble(st.nextToken().trim());
				double sigma = Double.parseDouble(st.nextToken().trim());
				double seisMomentRate = Double.parseDouble(st.nextToken().trim());
				++i;
				String numSourceLoc = fileLines.get(i);
				st = new StringTokenizer(numSourceLoc);
				int numSourceLocations = Integer.parseInt(st.nextToken().trim());			//replaced "Integer.parseInt(fileLines.get(i));"
				FaultTrace fltTrace = new FaultTrace(srcCode);
				int numLinesDone = i;
				for(i=i+1;i<=(numLinesDone+numSourceLocations);++i){
					String location = fileLines.get(i);
					st = new StringTokenizer(location);
					double lon = Double.parseDouble(st.nextToken().trim());
					double lat = Double.parseDouble(st.nextToken().trim());
					fltTrace.add(new Location(lat,lon));
				}
				--i;
				EvenlyGriddedSurface surface = new StirlingGriddedSurface(fltTrace, dip,upperSeis,lowerSeis,DEFAULT_GRID_SPACING);
				sourceNames.add(srcCode);
				this.sourceMags.add(meanMag);
				this.sourceMoRates.add(seisMomentRate);
				this.sourceRakes.add(rake);
				this.sourceSigmas.add(sigma);
				this.sourceGriddedSurface.add(surface);
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}

	}

	/**
	 * Make Fault Sources
	 *
	 */
	private void mkFaultSources() {
		for(int srcIndex=0; srcIndex<sourceNames.size(); ++srcIndex) {
			EvenlyGriddedSurface surface = this.sourceGriddedSurface.get(srcIndex);
			IncrementalMagFreqDist magDist = new GaussianMagFreqDist(MIN_MAG, MAX_MAG, NUM_MAGS,
					this.sourceMags.get(srcIndex), this.sourceSigmas.get(srcIndex), 
					this.sourceMoRates.get(srcIndex));
			FaultRuptureSource rupSource = new FaultRuptureSource(magDist,surface,sourceRakes.get(srcIndex),timeSpan.getDuration());
			rupSource.setName(sourceNames.get(srcIndex));
			allSources.add(rupSource);
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
		this.parameterChangeFlag = true;
	}

	@Override
	public int getNumSources() {
		return allSources.size();
	}

	@Override
	public ProbEqkSource getSource(int source) {
		// TODO Auto-generated method stub
		return (ProbEqkSource)allSources.get(source);
	}

	@Override
	public ArrayList getSourceList() {
		// TODO Auto-generated method stub
		return allSources;
	}

	public String getName() {
		// TODO Auto-generated method stub
		return NAME;
	}

	/**
	 * Update the fault Sources with the change in duration.
	 */
	public void updateForecast() {
		// make sure something has changed
		if(parameterChangeFlag) {
			allSources = new ArrayList<ProbEqkSource>();
			mkFaultSources();
			String bgVal = (String)backSeisParam.getValue();
			if(bgVal.equals(BACK_SEIS_INCLUDE)){
				mkBackRegion();
			}
		}
		parameterChangeFlag = false;
	}
}
