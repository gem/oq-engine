package scratch.matt.calc;

import java.io.FileWriter;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.region.SitesInGriddedRegion;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.WarningParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.commons.util.FileUtils;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.PointEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.step.STEP_BackSiesDataAdditionObject;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.attenRelImpl.depricated.BA_2006_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.util.SiteTranslator;


public class STEP_HazardDataSet implements ParameterChangeWarningListener{


	private boolean willSiteClass = true;
	//private boolean willSiteClass = false;
	private AttenuationRelationship attenRel;
	//public  String STEP_BG_FILE_NAME = RegionDefaults.backgroundHazardPath;
	//private static final String STEP_HAZARD_OUT_FILE_NAME = RegionDefaults.outputHazardPath;
	public static final double IML_VALUE = Math.log(0.126);
	private static final double SA_PERIOD = 1;
	public static final String STEP_AFTERSHOCK_OBJECT_FILE = RegionDefaults.STEP_AftershockObjectFile;
	private DecimalFormat locFormat = new DecimalFormat("0.0000");
	private STEP_main stepMain ;


	public STEP_HazardDataSet(boolean includeWillsSiteClass){
		this.willSiteClass = includeWillsSiteClass;
	}

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		STEP_HazardDataSet step = new STEP_HazardDataSet(false);
		//read the aftershock file
		/*try {
			ArrayList stepAftershockList = (ArrayList)FileUtils.loadFile(STEP_AFTERSHOCK_OBJECT_FILE);
		} catch (FileNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}*/
		//while(true)
		step.runSTEP();
		System.out.println("STEP is finito!");

	}



	public void runSTEP(){
		//1. create step main
		runStepmain();
		System.out.println("STEP earthquake rates are done.");
		
		//2. 
		createShakeMapAttenRelInstance();

		//3.why not use the region of STEP_main.bgGrid???
		SitesInGriddedRegion region = getDefaultRegion();//
//		System.out.println("getNumGridLocs=" + region.getNumGridLocs());	
//		for(Location loc:region.getGridLocationsList()){
//			System.out.println("loc=" +loc.getLatitude() + "," + loc.getLongitude());
//		}
		
		//4. calc probability values
		double[] stepBothProbVals = calcStepProbValues(region);
		
		//5. output
		saveProbValues2File(stepBothProbVals,region);
		
		//5.1. backup aftershocks
		ArrayList stepAftershockList= stepMain.getSTEP_AftershockForecastList();
		//saving the STEP_Aftershock list object to the file, why not do it in stepMain?
		synchronized(stepAftershockList){
			try {
				FileUtils.saveObjectInFile(STEP_AFTERSHOCK_OBJECT_FILE, stepAftershockList);
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}


	/**
	 * 
	 */
	public void runStepmain() {
		stepMain = new STEP_main();
		//1. step main
		stepMain.calc_STEP();		
	}

	/**
	 * @return
	 */
	public SitesInGriddedRegion getDefaultRegion() {
//		try {
		  GriddedRegion eggr = 
			  new GriddedRegion(
					  new Location(RegionDefaults.searchLatMin, RegionDefaults.searchLongMin),
					  new Location(RegionDefaults.searchLatMax, RegionDefaults.searchLongMax),
					  RegionDefaults.gridSpacing, new Location(0,0));
			return new SitesInGriddedRegion(eggr);
//		} catch (RegionConstraintException e) {			
//			e.printStackTrace();
//		}
		//return null;
	}

	/**
	 * @param region
	 * @return
	 */
	public double[] calcStepProbValues(SitesInGriddedRegion region ) {
		region.addSiteParams(attenRel.getSiteParamsIterator());
		//getting the Attenuation Site Parameters Liat
		ListIterator it = attenRel.getSiteParamsIterator();
		//creating the list of default Site Parameters, so that site parameter values can be filled in
		//if Site params file does not provide any value to us for it.
		ArrayList defaultSiteParams = new ArrayList();
		SiteTranslator siteTrans= new SiteTranslator();
		while(it.hasNext()){
			//adding the clone of the site parameters to the list
			ParameterAPI tempParam = (ParameterAPI)((ParameterAPI)it.next()).clone();
			//getting the Site Param Value corresponding to the Will Site Class "DE" for the seleted IMR  from the SiteTranslator
			siteTrans.setParameterValue(tempParam, siteTrans.WILLS_DE, Double.NaN);
			defaultSiteParams.add(tempParam);
		}
		if(willSiteClass){
			region.setDefaultSiteParams(defaultSiteParams);
			region.setSiteParamsForRegionFromServlet(true);
		}
		//read background hazard values from file
		double[] bgVals = loadBgProbValues(region,RegionDefaults.backgroundHazardPath);
		//get hazards values from new events
		double[] probVal = this.clacProbVals(attenRel, region, stepMain.getSourceList());
		//combining the backgound and Addon dataSet and wrinting the result to the file
		STEP_BackSiesDataAdditionObject addStepData = new STEP_BackSiesDataAdditionObject();
		return  addStepData.addDataSet(bgVals,probVal);

	}

	/**
	 * 
	 */
	public void createShakeMapAttenRelInstance(){
		// make the imr
		//attenRel = new ShakeMap_2003_AttenRel(this);
		attenRel = new BA_2006_AttenRel(this);
		// set the im as PGA
		//attenRel.setIntensityMeasure(((ShakeMap_2003_AttenRel)attenRel).PGA_Param.NAME);
		//attenRel.setIntensityMeasure(((ShakeMap_2003_AttenRel)attenRel).SA_Param.NAME, SA_PERIOD);
		attenRel.setParamDefaults();
	    attenRel.setIntensityMeasure(SA_Param.NAME);
	    attenRel.getParameter(PeriodParam.NAME).setValue(SA_PERIOD);
//		attenRel.setIntensityMeasure(((BA_2006_AttenRel)attenRel).SA_Param.NAME, SA_PERIOD);

	}
	//}



	/**
	 * craetes the output xyz files
	 * @param probVals : Probablity values ArrayList for each Lat and Lon
	 * @param fileName : File to create
	 */
	private void saveProbValues2File(double[] probVals,SitesInGriddedRegion sites){
		int size = probVals.length;
		LocationList locList = sites.getRegion().getNodeList();
		int numLocations = locList.size();

		try{
			FileWriter fr = new FileWriter(RegionDefaults.outputHazardPath);
			for(int i=0;i<numLocations;++i){
				Location loc = locList.get(i);
				// System.out.println("Size of the Prob ArrayList is:"+size);
				fr.write(locFormat.format(loc.getLatitude())+"    " + locFormat.format(loc.getLongitude())+"      "+convertToProb(probVals[i])+"\n");
			}
			fr.close();
		}catch(IOException ee){
			ee.printStackTrace();
		}
	}

	private double convertToProb(double rate){
		return (1-Math.exp(-1*rate*RegionDefaults.forecastLengthDays));
	}

	/**
	 * returns the prob for the file( fileName)
	 * 
	 * number and order of locations should match those
	 * in grid loactions and the hypMagFreqAtLocs in SETP_main
	 * 
	 * @param fileName : Name of the file from which we collect the values
	 */
	public double[] loadBgProbValues(SitesInGriddedRegion sites,String fileName){
		BackGroundRatesGrid bgGrid = stepMain.getBgGrid();
		STEP_main.log("numSites =" + sites.getRegion().getNodeCount() + " fileName=" + fileName);		
		double[] vals = new double[sites.getRegion().getNodeCount()];	
		 HashMap<String,Double> valuesMap = new  HashMap<String,Double>();
		try{
			ArrayList fileLines = FileUtils.loadFile(fileName);
			ListIterator it = fileLines.listIterator();
			//STEP_main.log("fileLines.size() =" + fileLines.size());
			//int i=0;
			while(it.hasNext()){
				//if(i >= numSites) break;
				StringTokenizer st = new StringTokenizer((String)it.next());
				String latstr =st.nextToken().trim();
				String lonstr =st.nextToken().trim();
				String val =st.nextToken().trim();
				// get lat and lon
				double lon =  Double.parseDouble(lonstr );
				double lat =  Double.parseDouble(latstr);
				//STEP_main.log("lat =" + lat + " lon=" + lon);
				Location loc = new Location(lat,lon,BackGroundRatesGrid.DEPTH);
				double temp =0;
				if(!val.equalsIgnoreCase("NaN")){
					temp=(new Double(val)).doubleValue();
					//vals[i++] = convertToRate(temp);
					//vals[index] = convertToRate(temp);
				} else{
					temp=(new Double(Double.NaN)).doubleValue();
					//vals[i++] = convertToRate(temp);
					//vals[index] = convertToRate(temp);
				}
				valuesMap.put(bgGrid.getKey4Location(loc), temp);
			}
			//convert to an array in the order of the region grids locations
			for(int i = 0; i < sites.getRegion().getNodeCount(); i++){
				Location loc = sites.getRegion().locationForIndex(i);
				vals[i] = valuesMap.get(bgGrid.getKey4Location(loc));
				//STEP_main.log(">> vals[" + i + "] =" + vals[i]  );
			}
		}catch(Exception e){
			e.printStackTrace();
		}
		return vals;
	}


	/**
	 * @param prob
	 * @return
	 */
	private double convertToRate(double prob){
		return (-1*Math.log(1-prob)/RegionDefaults.forecastLengthDays);
	}
	
	/**
	 * HazardCurve Calculator for the STEP
	 * @param imr : ShakeMap_2003_AttenRel for the STEP Calculation
	 * @param sites
	 * @param eqkRupForecast : STEP Forecast
	 * @returns the ArrayList of Probability values for the given region
	 *           --in the same order of the region grids
	 */
	public double[] clacProbVals(AttenuationRelationship imr,SitesInGriddedRegion sites,
			ArrayList sourceList){

		double[] probVals = new double[sites.getRegion().getNodeCount()];
		double MAX_DISTANCE = 500;

		// declare some varibles used in the calculation
		double qkProb, distance;
		int k,i;
		try{
			// get total number of sources
			int numSources = sourceList.size();

			// this boolean will tell us whether a source was actually used
			// (e.g., all could be outside MAX_DISTANCE)
			boolean sourceUsed = false;

			int numSites = sites.getRegion().getNodeCount();
			int numSourcesSkipped =0;
			long startCalcTime = System.currentTimeMillis();

			for(int j=0; j< numSites;++j){
				sourceUsed = false;
				double hazVal =1;
				double condProb =0;
				Site site = sites.getSite(j);
				imr.setSite(site);
				//adding the wills site class value for each site
				// String willSiteClass = willSiteClassVals[j];
				//only add the wills value if we have a value available for that site else leave default "D"
				//if(!willSiteClass.equals("NA"))
				//imr.getSite().getParameter(imr.WILLS_SITE_NAME).setValue(willSiteClass);
				//else
				// imr.getSite().getParameter(imr.WILLS_SITE_NAME).setValue(imr.WILLS_SITE_D);

				// loop over sources
				for(i=0;i < numSources ;i++) {
					// get the ith source
					ProbEqkSource source = (ProbEqkSource)sourceList.get(i);
					// compute it's distance from the site and skip if it's too far away
					distance = source.getMinDistance(sites.getSite(j));
					if(distance > MAX_DISTANCE){
						++numSourcesSkipped;
						//update progress bar for skipped ruptures
						continue;
					}
					// indicate that a source has been used
					sourceUsed = true;
					hazVal *= (1.0 - imr.getTotExceedProbability((PointEqkSource)source,IML_VALUE));
				}

				// finalize the hazard function
				if(sourceUsed) {
					//System.out.println("HazVal:"+hazVal);
					hazVal = 1-hazVal;
				} else {
					hazVal = 0.0;
				}
				//System.out.println("HazVal: "+hazVal);
				probVals[j]=this.convertToRate(hazVal);
			}
		}catch(Exception e){
			e.printStackTrace();
		}

		return probVals;
	}
	
	
	


	/**
	 *  Function that must be implemented by all Listeners for
	 *  ParameterChangeWarnEvents.
	 *
	 * @param  event  The Event which triggered this function call
	 */
	public void parameterChangeWarning( ParameterChangeWarningEvent e ){

		String S =  " : parameterChangeWarning(): ";

		WarningParameterAPI param = e.getWarningParameter();

		//System.out.println(b);
		param.setValueIgnoreWarning(e.getNewValue());

	}

	public STEP_main getStepMain() {
		return stepMain;
	}

	public void setStepMain(STEP_main stepMain) {
		this.stepMain = stepMain;
	}

	public AttenuationRelationship getAttenRel() {
		return attenRel;
	}  
	
	
}
