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
	// magnitude frequency distribution bin width
	private static Double mfdBinWidth = null;
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
	
	//************************ parameters for area source ********************//
	// include area source
	private static Boolean includeAreaSource = null;
	// area source rupture model
	private static String areaSourceRuptureModel = null;
	// area source discretization
	private static Double areaSourceDiscretization = null;
	// area source magnitude scaling relationship
	private static String areaSourceMagAreaRel = null;
	
	//************************** parameters for grid source *******************//
	// include grid source
	private static Boolean includeGridSource = null;
	// grid source rupture model
	private static String gridSourceRuptureModel = null;
	// grid source magnitude scaling relationship
	private static String gridSourceMagAreaRel = null;
	
	//************************* parameters for fault source *******************//
	// include fault source
	private static Boolean includeFaultSource = null;
	// fault rupture offset
	private static Double faultSourceRuptureOffset = null;
	// fault surface discretization
	private static Double faultSourceSurfaceDiscretization = null;
	// fault source magnitude scaling relationship
	private static String faultSourceMagAreaRel = null;
	// fault source magnitude scaling sigma
	private static Double faultSourceMagSigma = null;
	// fault source rupture aspect ratio
	private static Double faultSourceRuptureAspectRatio = null;
	// fault source rupture floating type
	private static String faultSourceRuptureFloatingType = null;
	
	//************************* parameters for subduction fault source *******************//
	// include subduction fault source
	private static Boolean includeSubductionFaultSource = null;
	// subduction fault rupture offset
	private static Double subductionFaultSourceRuptureOffset = null;
	// subduction fault surface discretization
	private static Double subductionFaultSourceSurfaceDiscretization = null;
	// subduction fault source magnitude scaling relationship
	private static String subductionFaultSourceMagAreaRel = null;
	// subduction fault source magnitude scaling sigma
	private static Double subductionFaultSourceMagSigma = null;
	// subduction fault source rupture aspect ratio
	private static Double subductionFaultSourceRuptureAspectRatio = null;
	// subduction fault source rupture floating type
	private static String subductionFaultSourceRuptureFloatingType = null;

	// results type
	private static String resultType = null;
	
	// probability of exceedance
	private static Double probExc = null;
	// region boundary
	private static LocationList regionBoundary = null;
	// grid spacing
	private static Double gridSpacing = null;
	
	// calculation model
	private static String calculationMode = null;

	// number of samples
	private static Integer numHazCurve = null;
	
	// number of treads for calculation
	private static Integer numThreads = null;
	
	// comment line identifier
	private static String comment = "#";
	
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
		System.out.println("xxr configFile = " + configFile);
		try {
			System.out.println("xxr ClassLoader-Resource-Path = " + this.getClass().getClassLoader().getResource(configFile).getPath());
		} catch (NullPointerException e) {
			System.out.println("xxr this.getClass().getClassLoader().getResource(configFile) = " + this.getClass().getClassLoader().getResource(configFile));
		}
        File file = new File(configFile);
		//File file = new File(this.getClass().getClassLoader().getResource(configFile).getPath());
        FileInputStream oFIS = new FileInputStream(file.getPath());
        BufferedInputStream oBIS = new BufferedInputStream(oFIS);
        BufferedReader oReader = new BufferedReader(new InputStreamReader(oBIS));
        
        // rnead erf logic tree file
        // skip comment lines
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.erfLogicTreeFile = sRecord.trim();
        
        // read GMPEs logic tree file
        // skip comment lines
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.gmpeLogicTreeFile = sRecord.trim();
        
        // read output directory path
        // skip comment lines
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.outputDir = sRecord.trim();
        
        // read minimum magnitude
        // skip comment lines
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.minMag = Double.parseDouble(sRecord.trim());
        
        // read investigation time
        // skip comment lines
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.investigationTime = Double.parseDouble(sRecord.trim());
        
        // read maximum distance
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.maxDistance = Double.parseDouble(sRecord.trim());
        
        // read MFD bin width
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.mfdBinWidth = Double.parseDouble(sRecord.trim());
        
        // read component
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.component = sRecord.trim();
        
        // read intensity measure type
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.intensityMeasureType = sRecord.trim();
        
        // read period
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.period = Double.parseDouble(sRecord.trim());
        
        // read damping
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.damping = Double.parseDouble(sRecord.trim());
        
        // read intensity measure levels
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        st = new StringTokenizer(sRecord);
        int numGMV = st.countTokens();
        for(int i=0;i<numGMV;i++) this.imlList.set(Math.log(Double.parseDouble(st.nextToken())), 1.0);
        
        // read truncation type
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.truncationType = sRecord.trim();
        
        // read truncation level
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.truncationLevel = Double.parseDouble(sRecord.trim());
        
        // read standard deviation type
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.standardDeviationType = sRecord.trim();
    
        // read reference vs30
        // skip comment lines
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.vs30Reference = Double.parseDouble(sRecord.trim());
        
        //************************ read params for area source **************//
        
        // read include area source
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        if(sRecord.trim().equalsIgnoreCase("yes")){
        	this.includeAreaSource = true;
        }
        else{
        	this.includeAreaSource = false;
        }
        
        // read area source rupture model
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.areaSourceRuptureModel = sRecord.trim();
        
        // read area source discretization   
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.areaSourceDiscretization = Double.parseDouble(sRecord.trim());
        
        // read mag-area scaling relationship
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.areaSourceMagAreaRel = sRecord.trim();
        
        //********************* read params for grid source *****************//
        
        // read include grid sources
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        if(sRecord.trim().equalsIgnoreCase("yes")){
        	this.includeGridSource = true;
        }
        // xxr: this case should also be considered (actually only this case):
        if(Boolean.parseBoolean(sRecord.trim())) {
        	includeGridSource = true;
        }
        else{
        	this.includeGridSource = false;
        }
        
        // read grid source rupture model
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.gridSourceRuptureModel = sRecord.trim();
        
        // read grid source mag-area relationship
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.gridSourceMagAreaRel = sRecord.trim();
        
        //********************** read params for fault source ****************//
        
        // read include fault source
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        if(sRecord.trim().equalsIgnoreCase("yes")){
        	this.includeFaultSource = true;
        }
        // xxr: this case should also be considered (actually only this case):
        if(Boolean.parseBoolean(sRecord.trim())) {
        	includeFaultSource = true;
        }
        else{
        	this.includeFaultSource = false;
        }
        
        // fault rupture offset
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.faultSourceRuptureOffset = Double.parseDouble(sRecord.trim());
        
        // fault surface discretization
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.faultSourceSurfaceDiscretization = Double.parseDouble(sRecord.trim());
        
        // fault mag-area rel
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.faultSourceMagAreaRel = sRecord.trim();
        
        // fault mag-area rel sigma
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.faultSourceMagSigma = Double.parseDouble(sRecord.trim());

        // fault rupture aspect ratio
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.faultSourceRuptureAspectRatio = Double.parseDouble(sRecord.trim());
        
        // fault rupture floating type
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.faultSourceRuptureFloatingType = sRecord.trim();
        
        //********************** read params for subduction fault source ****************//
        
        // read include fault source
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        if(sRecord.trim().equalsIgnoreCase("yes")){
        	this.includeSubductionFaultSource = true;
        }
        // xxr: this case should also be considered (actually only this case):
        if(Boolean.parseBoolean(sRecord.trim())) {
        	includeSubductionFaultSource = true;
        }
        else{
        	this.includeSubductionFaultSource = false;
        }
        
        // rupture offset
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.subductionFaultSourceRuptureOffset = Double.parseDouble(sRecord.trim());
        
        // surface discretization
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.subductionFaultSourceSurfaceDiscretization = Double.parseDouble(sRecord.trim());
        
        // mag-area rel
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.subductionFaultSourceMagAreaRel = sRecord.trim();
        
        // mag-area rel sigma
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.subductionFaultSourceMagSigma = Double.parseDouble(sRecord.trim());

        // rupture aspect ratio
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.subductionFaultSourceRuptureAspectRatio = Double.parseDouble(sRecord.trim());
        
        // rupture floating type
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.subductionFaultSourceRuptureFloatingType = sRecord.trim();
        
        // read result type
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.resultType = sRecord.trim();
        
        // if hazard map
        if(this.resultType.equalsIgnoreCase(ResultTypeParams.MEAN_GROUND_MOTION_MAP.toString())){
        	
        	// read probability of exceedance
            while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
            	continue;
            this.probExc = Double.parseDouble(sRecord.trim());
            
            // read region boundary
            while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
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
        	System.out.println(this.resultType+" is not supported! Check the configuration file for RESULT TYPE");
        	System.out.println("Execution stopped.");
        	System.exit(0);
        }
        
        // calculation mode
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.calculationMode = sRecord.trim();
        
        // read number of samples to be generated
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.numHazCurve = Integer.parseInt(sRecord.trim());
        
        
        // read number of threads
        while((sRecord=oReader.readLine()).trim().startsWith(comment)  || sRecord.replaceAll(" ","").isEmpty())
        	continue;
        this.numThreads = Integer.parseInt(sRecord.trim());
        
        
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

	public static Boolean getIncludeGridSource() {
		return includeGridSource;
	}

	public static String getGridSourceRuptureModel() {
		return gridSourceRuptureModel;
	}

	public static String getGridSourceMagAreaRel() {
		return gridSourceMagAreaRel;
	}

	public static Boolean getIncludeFaultSource() {
		return includeFaultSource;
	}

	public static Double getFaultSourceRuptureOffset() {
		return faultSourceRuptureOffset;
	}

	public static Double getFaultSourceSurfaceDiscretization() {
		return faultSourceSurfaceDiscretization;
	}

	public static String getFaultSourceMagAreaRel() {
		return faultSourceMagAreaRel;
	}

	public static Double getFaultSourceMagSigma() {
		return faultSourceMagSigma;
	}

	public static Double getFaultSourceRuptureAspectRatio() {
		return faultSourceRuptureAspectRatio;
	}

	public static String getFaultSourceRuptureFloatingType() {
		return faultSourceRuptureFloatingType;
	}

	public static Boolean getIncludeSubductionFaultSource() {
		return includeSubductionFaultSource;
	}

	public static Double getSubductionFaultSourceRuptureOffset() {
		return subductionFaultSourceRuptureOffset;
	}

	public static Double getSubductionFaultSourceSurfaceDiscretization() {
		return subductionFaultSourceSurfaceDiscretization;
	}

	public static String getSubductionFaultSourceMagAreaRel() {
		return subductionFaultSourceMagAreaRel;
	}

	public static Double getSubductionFaultSourceMagSigma() {
		return subductionFaultSourceMagSigma;
	}

	public static Double getSubductionFaultSourceRuptureAspectRatio() {
		return subductionFaultSourceRuptureAspectRatio;
	}

	public static String getSubductionFaultSourceRuptureFloatingType() {
		return subductionFaultSourceRuptureFloatingType;
	}

	public static String getCalculationMode() {
		return calculationMode;
	}

}
