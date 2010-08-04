package scratch.matt.calc;

import java.io.FileWriter;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.ListIterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
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


public class STEP_DamageState implements ParameterChangeWarningListener{

	
	private boolean willSiteClass = true;
	//private boolean willSiteClass = false;
	private AttenuationRelationship attenRel;
	private static final String STEP_BG_FILE_NAME = RegionDefaults.backgroundHazardPath;
	private static final String STEP_HAZARD_OUT_FILE_NAME = RegionDefaults.outputHazardPath;
	private static final String STEP_HAZCURVE_OUT_FILE_NAME = RegionDefaults.outputHazCurvePath;
	private static final double IML_VALUE = Math.log(1);
	private static final double SA_PERIOD = 1;
	private static final String STEP_AFTERSHOCK_OBJECT_FILE = RegionDefaults.STEP_AftershockObjectFile;
	private DecimalFormat locFormat = new DecimalFormat("0.0000");
	private static final double[] IM_LEVEL_LIST = { 0.0025,0.00375,0.00563,0.00844,0.0127,0.019,0.0285,0.0427,0.0641,0.0961,0.144,0.216,0.324,0.487,0.73,1.09,1.64,2.46,3.69,5.54};
	//private static final double[] IM_LEVEL_LIST = {.0961,.144};
	private double[][] hazCurveList;
	private static final int NUM_LEVELS = 20;
	
	public STEP_DamageState(boolean includeWillsSiteClass){
		this.willSiteClass = includeWillsSiteClass;
	}
	
	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		 System.out.println(" DS STEP Starting.");
		STEP_DamageState step = new STEP_DamageState(false);
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
		   step.runDSSTEP();
		   System.out.println(" DS STEP is finito!");
	
	}


	
	private void runDSSTEP(){
	  STEP_main stepMain = new STEP_main();
	  System.out.println(" DS STEP earthquake rates are done.");
	  createShakeMapAttenRelInstance();
	  SitesInGriddedRegion sites = null;
//	try {
		  GriddedRegion eggr = 
			  new GriddedRegion(
					  new Location(32.5,-124.8),
					  new Location(42.2,-112.4),
					  0.1, new Location(0,0));
		  sites = new SitesInGriddedRegion(eggr);
//	} catch (RegionConstraintException e) {
//		// TODO Auto-generated catch block
//		e.printStackTrace();
//	}
	  
	  
		  sites.addSiteParams(attenRel.getSiteParamsIterator());
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
        siteTrans.setParameterValue(tempParam,siteTrans.WILLS_DE,Double.NaN);
        defaultSiteParams.add(tempParam);
      }
      if(willSiteClass){
    	  sites.setDefaultSiteParams(defaultSiteParams);
    	  sites.setSiteParamsForRegionFromServlet(true);
      }
      
      // create the list of im levels for the hazard curve.
      ArbitrarilyDiscretizedFunc probCurve = new ArbitrarilyDiscretizedFunc();
	  for(int i=0;i<NUM_LEVELS;++i){
	      probCurve.set(Math.log(IM_LEVEL_LIST[i]),1);
	      //System.out.println("probCurve init: "+probCurve.getY(i)+" "+i);
	  }
	  
      double[] bgVals = getBGVals(sites.getRegion().getNodeCount(),STEP_BG_FILE_NAME);
      double[] probVal = this.getProbVals(attenRel, sites, stepMain.getSourceList(), probCurve);

      //combining the backgound and Addon dataSet and wrinting the result to the file
      STEP_BackSiesDataAdditionObject addStepData = new STEP_BackSiesDataAdditionObject();
      double[] stepBothProbVals = addStepData.addDataSet(bgVals,probVal);
      createFile(stepBothProbVals,sites);
      createHazCurveFile(hazCurveList, sites);
      ArrayList stepAftershockList= stepMain.getSTEP_AftershockForecastList();
      //saving the STEP_Aftershock list object to the file
      try {
		FileUtils.saveObjectInFile(STEP_AFTERSHOCK_OBJECT_FILE, stepAftershockList);
	} catch (IOException e) {
		// TODO Auto-generated catch block
		e.printStackTrace();
	}
	}
	
	
	private void createShakeMapAttenRelInstance(){
		 // make the imr
	      //attenRel = new ShakeMap_2003_AttenRel(this);
	      attenRel = new BA_2006_AttenRel(this);
	            // set the im as PGA
	      //attenRel.setIntensityMeasure(((ShakeMap_2003_AttenRel)attenRel).PGA_Param.NAME);
	      //attenRel.setIntensityMeasure(((ShakeMap_2003_AttenRel)attenRel).SA_Param.NAME, SA_PERIOD);
	      attenRel.setParamDefaults();
	      attenRel.setIntensityMeasure(SA_Param.NAME);
	      attenRel.getParameter(PeriodParam.NAME).setValue(SA_PERIOD);
//	      attenRel.setIntensityMeasure(((BA_2006_AttenRel)attenRel).SA_Param.NAME, SA_PERIOD);
	      
	}
	//}
	
	

	 /**
	   * craetes the output xyz files
	   * @param probVals : Probablity values ArrayList for each Lat and Lon
	   * @param fileName : File to create
	   */
	  private void createFile(double[] probVals,SitesInGriddedRegion sites){
	    int size = probVals.length;
	    LocationList locList = sites.getRegion().getNodeList();
	    int numLocations = locList.size();
	    
	    try{
		      FileWriter fr = new FileWriter(STEP_HAZARD_OUT_FILE_NAME);
		      for(int i=0;i<numLocations;++i){
		    	  Location loc = locList.get(i);
		    	  // System.out.println("Size of the Prob ArrayList is:"+size);
		    	  fr.write(locFormat.format(loc.getLatitude())+"    "+locFormat.format(loc.getLongitude())+"      "+convertToProb(probVals[i])+"\n");
		      }
		      fr.close();
	    }catch(IOException ee){
	      ee.printStackTrace();
	    }
	  }
	  
	  
	  /**
	   * craetes the output xyz files
	   * @param probVals : Probablity values ArrayList for each Lat and Lon
	   * @param fileName : File to create
	   */
	  private void createHazCurveFile(double[][] hazCurveList,SitesInGriddedRegion sites){
	    int size = hazCurveList.length;
	    LocationList locList = sites.getRegion().getNodeList();
	    int numLocations = locList.size();
	    
	    try{
		      FileWriter fr = new FileWriter(STEP_HAZCURVE_OUT_FILE_NAME);
		      for(int i=0;i<numLocations;++i){
		    	  Location loc = locList.get(i);
		    	  // System.out.println("Size of the Prob ArrayList is:"+size);
		    	  fr.write(locFormat.format(loc.getLatitude())+"    "+locFormat.format(loc.getLongitude()));
		    	  for(int k=0;k<NUM_LEVELS;++k)
		    		  fr.write(" "+convertToProb(hazCurveList[i][k]));
		    	  fr.write("\n");
		      };
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
	   * @param fileName : Name of the file from which we collect the values
	   */
	  private double[] getBGVals(int numSites,String fileName){
		double[] vals = new double[numSites];
	    try{
	      ArrayList fileLines = FileUtils.loadFile(fileName);
	      ListIterator it = fileLines.listIterator();
	      int i=0;
	      while(it.hasNext()){
	        StringTokenizer st = new StringTokenizer((String)it.next());
	        st.nextToken();
	        st.nextToken();
	        String val =st.nextToken().trim();
	        double temp =0;
	        if(!val.equalsIgnoreCase("NaN")){
	          temp=(new Double(val)).doubleValue();
	          vals[i++] = convertToRate(temp);
	        }
	        else{
	          temp=(new Double(Double.NaN)).doubleValue();
	          vals[i++] = convertToRate(temp);
	        }
	      }
	    }catch(Exception e){
	      e.printStackTrace();
	    }
	    return vals;
	  }
	  
	  
	  private double convertToRate(double prob){
		  return (-1*Math.log(1-prob)/RegionDefaults.forecastLengthDays);
	  }
	  /**
	   * HazardCurve Calculator for the STEP
	   * @param imr : ShakeMap_2003_AttenRel for the STEP Calculation
	   * @param region
	   * @param eqkRupForecast : STEP Forecast
	   * @returns the ArrayList of Probability values for the given region
	   */
	  private double[] getProbVals(AttenuationRelationship imr,SitesInGriddedRegion sites,
	                                     ArrayList sourceList, ArbitrarilyDiscretizedFunc probCurve){

	    double[] probVals = new double[sites.getRegion().getNodeCount()];
	    double MAX_DISTANCE = 500;
	    double invProb;
	   
	    

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
	      hazCurveList = new double[numSites][20];
	      double[] totInvProb =  new double[20];
	      
	      

	      for(int j=0;j<numSites;++j){
	        double hazVal =1;
	        double condProb =0;
	        for(int d=0;d<NUM_LEVELS;++d)
		    	  totInvProb[d] = 1.0;
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
	          //if(j==2210){
		      //  	System.out.println(j);
		      //  }

	          hazVal *= (1.0 - imr.getTotExceedProbability((PointEqkSource)source,IML_VALUE));
	          
	          // number of ruptures w/in the source, need to do for each M represented
	          int numRup = source.getNumRuptures();
	          //if(j==2210){
		      //  	System.out.println(j);
		      //  }

	          for(int n=0;n<numRup;++n)
	          {
	        	  imr.setEqkRupture(source.getRupture(n));
	        	  qkProb = source.getRupture(n).getProbability();
	          		// get the complete hazard curve for the set values
	        	  imr.getExceedProbabilities(probCurve);
	        	  for (int kk=0;kk<NUM_LEVELS;++kk){
		        	  //invProb = 1.0 - probCurve.getY(kk);
		        	  //totInvProb[kk] *= invProb;
		        	  totInvProb[kk] *= Math.pow(1-qkProb,(probCurve.getY(kk)));
		        	 // hazFunction.set(k,hazFunction.getY(k)*Math.pow(1-qkProb,condProbFunc.getY(k)));
		          }
	          }
	          
	          
	          
	        }

	        // finalize the hazard function
	        if(sourceUsed) {
	          //System.out.println("HazVal:"+hazVal);
	          hazVal = 1-hazVal;
	          for(i=0;i<NUM_LEVELS;i++)
	          {
	        	  invProb = 1 - totInvProb[i];
	        	  probCurve.set(i,invProb);
	        	  //System.out.println("invProb"+invProb);
	          }
	        }
	        else{
	          hazVal = 0.0;
	          for(i=0;i<NUM_LEVELS;i++)
	          {      
	        	  probCurve.set(i,0.0);
	          }
	        }
	        //System.out.println("HazVal: "+hazVal);
	        
	        // fill the matrix of hazard values
	        probVals[j]=this.convertToRate(hazVal);
	        
	        //if(j==2210){
	        //	System.out.println(j);
	        //}
	        for(i=0;i<NUM_LEVELS;i++)
	        {
		        //System.out.println("probCurve: "+probCurve.getY(i)+" "+j+" "+i);
	        	hazCurveList[j][i] = this.convertToRate(probCurve.getY(i));
	        	//System.out.println("HazCurve: "+hazCurveList[j][i]);
	        }
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
}
