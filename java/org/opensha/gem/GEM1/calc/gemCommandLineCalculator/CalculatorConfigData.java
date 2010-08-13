package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.StringTokenizer;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.gem.GEM1.util.ResultTypeParams;

/**
 * This object reads configuration file for the command line calculator
 * @author damianomonelli
 *
 */
public class CalculatorConfigData {
	
	// ERF logic tree file
	private static String erfLogicTreeFile = null;
	// GMPEs logic tree file
	private static String gmpeLogicTreeFile = null;
	// output directory path
	private static String outputDir = null;
	// minimum (moment) magnitude
	private static Double minMag = null;
	// investigation time (years)
	private static Double investigationTime = null;
	// maximum distance
	private static Double maxDistance = null;
	// component
	private static String component = null;
	// intensity measure type
	private static String intensityMeasureType = null;
	// period
	private static Double period = null;
	// damping
	private static Double damping = null;
	// intensity measure levels
	private ArbitrarilyDiscretizedFunc imlList = null;
	// gmpe truncation type
	private static String truncationType = null;
	// truncation level
	private static Double truncationLevel = null;
	// standard deviation type
	private static String standardDeviationType = null;
	// reference Vs30 value (m/s)
	private static Double vs30Reference = null;
	// include area source
	private static Boolean includeAreaSource = null;
	// area source rupture model
	private static String areaSourceRuptureModel = null;
	// area source discretization
	private static Double areaSourceDiscretization = null;
	// area source magnitude scaling relationship
	private static String areaSourceMagAreaRel = null;
	// magnitude frequency distribution bin width
	private static Double mfdBinWidth = null;
	// number of treads for calculation
	private static Integer numThreads = null;
	// results type
	private static String resultType = null;
	
	// probability of exceedance
	private static Double probExc = null;
	// region boundary
	private static LocationList regionBoundary = null;
	// grid spacing
	private static Double gridSpacing = null;

	// number of samples
	private static Integer numHazCurve = null;
	
	// comment line identifier
	private static String comment = "//";
	
	/**
	 * 
	 * @param configFile: configuration file name
	 * @throws IOException 
	 */
	public CalculatorConfigData(String configFile) throws IOException{
		
		this.imlList = new ArbitrarilyDiscretizedFunc();
		
        String sRecord = null;
        StringTokenizer st = null;
		
		// open file
		File file = new File(configFile);
        FileInputStream oFIS = new FileInputStream(file.getPath());
        BufferedInputStream oBIS = new BufferedInputStream(oFIS);
        BufferedReader oReader = new BufferedReader(new InputStreamReader(oBIS));
        
        // skip comment lines
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.erfLogicTreeFile = sRecord;
        
        // read GMPEs logic tree file
        // skip comment lines
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.gmpeLogicTreeFile = sRecord;
        
        // read output directory path
        // skip comment lines
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.outputDir = sRecord;
        
        // read minimum magnitude
        // skip comment lines
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.minMag = Double.parseDouble(sRecord);
        
        // read investigation time
        // skip comment lines
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.investigationTime = Double.parseDouble(sRecord);
        
        // read maximum distance
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.maxDistance = Double.parseDouble(sRecord);
        
        // read component
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.component = sRecord;
        
        // read intensity measure type
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.intensityMeasureType = sRecord;
        
        // read period
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.period = Double.parseDouble(sRecord);
        
        // read damping
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.damping = Double.parseDouble(sRecord);
        
        // read intensity measure levels
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        st = new StringTokenizer(sRecord);
        int numGMV = st.countTokens();
        for(int i=0;i<numGMV;i++) this.imlList.set(Math.log(Double.parseDouble(st.nextToken())), 1.0);
        
        // read truncation type
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.truncationType = sRecord;
        
        // read truncation level
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.truncationLevel = Double.parseDouble(sRecord);
        
        // read standard deviation type
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.standardDeviationType = sRecord;
    
        // read reference vs30
        // skip comment lines
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.vs30Reference = Double.parseDouble(sRecord);
        
        // read include area source
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        if(sRecord.equalsIgnoreCase("yes")){
        	this.includeAreaSource = true;
        }
        else{
        	this.includeAreaSource = false;
        }
        
        // read area source rupture model
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.areaSourceRuptureModel = sRecord;
        
        // read area source discretization   
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.areaSourceDiscretization = Double.parseDouble(sRecord);
        
        // read mag-area scaling relationship
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.areaSourceMagAreaRel = sRecord;
        
        // read MFD bin width
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.mfdBinWidth = Double.parseDouble(sRecord);
        
        // read number of threads
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.numThreads = Integer.parseInt(sRecord);
        
        // read result type
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.resultType = sRecord;
        
        // if hazard map
        if(this.resultType.equalsIgnoreCase(ResultTypeParams.HAZARD_MAP.toString())){
        	
        	// read probability of exceedance
            while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
            	continue;
            this.probExc = Double.parseDouble(sRecord);
            
            // read region boundary
            while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
            	continue;
            st = new StringTokenizer(sRecord);
            // number of vertices
            int numVert = (st.countTokens()-1)/2;
            this.regionBoundary = new LocationList();
            for(int i=0;i<numVert;i++){
            	this.regionBoundary.add(new Location(Double.parseDouble(st.nextToken()),Double.parseDouble(st.nextToken())));
            }
            
            // read grid spacing
            this.gridSpacing = Double.parseDouble(st.nextToken());
        	
        }
        else{
        	System.out.println(this.resultType+" is not supported!");
        	System.out.println("Execution stopped.");
        	System.exit(0);
        }
        
        // read number of samples to be generated
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.numHazCurve = Integer.parseInt(sRecord);
        
        
        // close file
		oFIS.close();
		oBIS.close();
		oReader.close();
		
	}

	public static String getComponent() {
		return component;
	}

	public static Double getDamping() {
		return damping;
	}

	public static String getTruncationType() {
		return truncationType;
	}

	public static String getStandardDeviationType() {
		return standardDeviationType;
	}

	public ArbitrarilyDiscretizedFunc getImlList() {
		return imlList;
	}

	public static String getErfLogicTreeFile() {
		return erfLogicTreeFile;
	}

	public static String getGmpeLogicTreeFile() {
		return gmpeLogicTreeFile;
	}

	public static String getOutputDir() {
		return outputDir;
	}

	public static Double getMinMag() {
		return minMag;
	}

	public static Double getInvestigationTime() {
		return investigationTime;
	}

	public static String getIntensityMeasureType() {
		return intensityMeasureType;
	}

	public static Double getPeriod() {
		return period;
	}

	public static Double getTruncationLevel() {
		return truncationLevel;
	}

	public static Double getVs30Reference() {
		return vs30Reference;
	}

	public static Double getMfdBinWidth() {
		return mfdBinWidth;
	}

	public static Integer getNumThreads() {
		return numThreads;
	}

	public static String getResultType() {
		return resultType;
	}

	public static Double getProbExc() {
		return probExc;
	}

	public static Double getGridSpacing() {
		return gridSpacing;
	}

	public static Double getMaxDistance() {
		return maxDistance;
	}

	public static LocationList getRegionBoundary() {
		return regionBoundary;
	}

	public static Integer getNumHazCurve() {
		return numHazCurve;
	}

	public static Boolean getIncludeAreaSource() {
		return includeAreaSource;
	}

	public static String getAreaSourceRuptureModel() {
		return areaSourceRuptureModel;
	}

	public static Double getAreaSourceDiscretization() {
		return areaSourceDiscretization;
	}

	public static String getAreaSourceMagAreaRel() {
		return areaSourceMagAreaRel;
	}

}
