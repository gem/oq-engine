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
	private static String calculationModel = null;

	// number of samples
	private static Integer numHazCurve = null;
	
	// number of treads for calculation
	private static Integer numThreads = null;
	
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
		File file = new File(this.getClass().getClassLoader().getResource(configFile).getPath());
        FileInputStream oFIS = new FileInputStream(file.getPath());
        BufferedInputStream oBIS = new BufferedInputStream(oFIS);
        BufferedReader oReader = new BufferedReader(new InputStreamReader(oBIS));
        
        // read erf logic tree file
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
        
        // read MFD bin width
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.mfdBinWidth = Double.parseDouble(sRecord);
        
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
        
        //************************ read params for area source **************//
        
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
        
        //********************* read params for grid source *****************//
        
        // read include grid sources
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        if(sRecord.equalsIgnoreCase("yes")){
        	this.includeGridSource = true;
        }
        else{
        	this.includeGridSource = false;
        }
        
        // read grid source rupture model
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.gridSourceRuptureModel = sRecord;
        
        // read grid source mag-area relationship
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.gridSourceMagAreaRel = sRecord;
        
        //********************** read params for fault source ****************//
        
        // read include fault source
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        if(sRecord.equalsIgnoreCase("yes")){
        	this.includeFaultSource = true;
        }
        else{
        	this.includeFaultSource = false;
        }
        
        // fault rupture offset
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.faultSourceRuptureOffset = Double.parseDouble(sRecord);
        
        // fault surface discretization
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.faultSourceSurfaceDiscretization = Double.parseDouble(sRecord);
        
        // fault mag-area rel
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.faultSourceMagAreaRel = sRecord;
        
        // fault mag-area rel sigma
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.faultSourceMagSigma = Double.parseDouble(sRecord);

        // fault rupture aspect ratio
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.faultSourceRuptureAspectRatio = Double.parseDouble(sRecord);
        
        // fault rupture floating type
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.faultSourceRuptureFloatingType = sRecord;
        
        //********************** read params for subduction fault source ****************//
        
        // read include fault source
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        if(sRecord.equalsIgnoreCase("yes")){
        	this.includeSubductionFaultSource = true;
        }
        else{
        	this.includeSubductionFaultSource = false;
        }
        
        // rupture offset
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.subductionFaultSourceRuptureOffset = Double.parseDouble(sRecord);
        
        // surface discretization
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.subductionFaultSourceSurfaceDiscretization = Double.parseDouble(sRecord);
        
        // mag-area rel
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.faultSourceMagAreaRel = sRecord;
        
        // mag-area rel sigma
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.subductionFaultSourceMagSigma = Double.parseDouble(sRecord);

        // rupture aspect ratio
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.subductionFaultSourceRuptureAspectRatio = Double.parseDouble(sRecord);
        
        // rupture floating type
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.subductionFaultSourceRuptureFloatingType = sRecord;
        
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
        
        // calculation mode
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.calculationModel = sRecord;
        
        // read number of samples to be generated
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.numHazCurve = Integer.parseInt(sRecord);
        
        
        // read number of threads
        while((sRecord=oReader.readLine()).contains(comment.subSequence(0, comment.length()))  || sRecord.isEmpty())
        	continue;
        this.numThreads = Integer.parseInt(sRecord);
        
        
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
