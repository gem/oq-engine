package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.BufferedInputStream;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.StringTokenizer;

import lombok.patcher.scripts.ScriptBuilder.ExitEarlyBuilder;

import org.opensha.commons.exceptions.ConstraintException;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranch;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranchingLevel;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.imr.attenRelImpl.BA_2008_AttenRel;
import org.opensha.sha.imr.param.IntensityMeasureParams.DampingParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.ComponentParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncLevelParam;
import org.opensha.sha.imr.param.OtherParams.SigmaTruncTypeParam;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;
import org.opensha.sha.imr.param.SiteParams.Vs30_Param;
import org.opensha.sha.util.TectonicRegionType;

public class GmpeLogicTreeData {
	
	// hash map of gmpe logic tree
	private HashMap<TectonicRegionType,GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTreeHashMap;
	
	// comment line identifier
	private static String comment = "#";
	
	// package for gmpe
	private String packageName = "org.opensha.sha.imr.attenRelImpl.";
	
	// for debugging
	private static Boolean D = false;
	
	public GmpeLogicTreeData(String gmpeInputFile, String component, String intensityMeasureType,
			double period, double damping, String truncType, double truncLevel, String stdType,
			double vs30) {
		try {
			// instatiate hash map of gmpe logic tree
			gmpeLogicTreeHashMap = new HashMap<TectonicRegionType,GemLogicTree<ScalarIntensityMeasureRelationshipAPI>>();

			String sRecord = null;

			String activeShallowGmpeNames = null;
			String activeShallowGmpeWeights = null;

			String stableShallowGmpeNames = null;
			String stableShallowGmpeWeights = null;

			String subductionInterfaceGmpeNames = null;
			String subductionInterfaceGmpeWeights = null;

			String subductionIntraSlabGmpeNames = null;
			String subductionIntraSlabGmpeWeights = null;

			// open file
			File file = new File(gmpeInputFile);
			FileInputStream oFIS = new FileInputStream(file.getPath());
			BufferedInputStream oBIS = new BufferedInputStream(oFIS);
			BufferedReader oReader = new BufferedReader(new InputStreamReader(oBIS));

			if(D) System.out.println("\n\n");
			if(D) System.out.println("GMPE Logic Tree structure");

			sRecord = oReader.readLine();
			// start reading the file
			while(sRecord!=null){

				// skip comments or empty lines
				while(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()){
					sRecord = oReader.readLine();
					continue;
				}

				// if gmpes for Active shallow crust are defined
				if(sRecord.trim().equalsIgnoreCase(TectonicRegionType.ACTIVE_SHALLOW.toString())){

					// read names
					sRecord = oReader.readLine();
					while(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()){
						sRecord = oReader.readLine();
						continue;
					}
					activeShallowGmpeNames = sRecord.trim();

					if(D) System.out.println("Gmpes for "+TectonicRegionType.ACTIVE_SHALLOW+": "+activeShallowGmpeNames);

					// read weights
					sRecord = oReader.readLine();
					while(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()){
						sRecord = oReader.readLine();
						continue;
					}
					activeShallowGmpeWeights = sRecord.trim();

					if(D) System.out.println("Gmpes weights: "+activeShallowGmpeWeights);
				}

				// if gmpes for stable continental crust are defined
				else if(sRecord.trim().equalsIgnoreCase(TectonicRegionType.STABLE_SHALLOW.toString())){

					// read names
					sRecord = oReader.readLine();
					while(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()){
						sRecord = oReader.readLine();
						continue;
					}
					stableShallowGmpeNames = sRecord.trim();

					if(D) System.out.println("Gmpes for "+TectonicRegionType.STABLE_SHALLOW+": "+stableShallowGmpeNames);

					// read weights
					sRecord = oReader.readLine();
					while(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()){
						sRecord = oReader.readLine();
						continue;
					}
					stableShallowGmpeWeights = sRecord.trim();

					if(D) System.out.println("Gmpes weights: "+stableShallowGmpeWeights);
				}

				// if gmpes for subduction interface are defined
				else if(sRecord.trim().equalsIgnoreCase(TectonicRegionType.SUBDUCTION_INTERFACE.toString())){

					// read names
					sRecord = oReader.readLine();
					while(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()){
						sRecord = oReader.readLine();
						continue;
					}
					subductionInterfaceGmpeNames = sRecord.trim();

					if(D) System.out.println("Gmpes for "+TectonicRegionType.SUBDUCTION_INTERFACE+": "+subductionInterfaceGmpeNames);

					// read weights
					sRecord = oReader.readLine();
					while(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()){
						sRecord = oReader.readLine();
						continue;
					}
					subductionInterfaceGmpeWeights = sRecord.trim();

					if(D) System.out.println("Gmpes weights: "+subductionInterfaceGmpeWeights);

				}

				// if gmpes for subduction intraslab are defined
				else if(sRecord.trim().equalsIgnoreCase(TectonicRegionType.SUBDUCTION_SLAB.toString())){

					// read names
					sRecord = oReader.readLine();
					while(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()){
						sRecord = oReader.readLine();
						continue;
					}
					subductionIntraSlabGmpeNames = sRecord.trim();

					if(D) System.out.println("Gmpes for "+TectonicRegionType.SUBDUCTION_SLAB+": "+subductionIntraSlabGmpeNames);

					// read weights
					sRecord = oReader.readLine();
					while(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()){
						sRecord = oReader.readLine();
						continue;
					}
					subductionIntraSlabGmpeWeights = sRecord.trim();

					if(D) System.out.println("Gmpes weights: "+subductionIntraSlabGmpeWeights);

				}

				// continue reading until next keyword is found or end of file
				// skip comments or empty lines
				while((sRecord = oReader.readLine())!=null){
					if(sRecord.trim().startsWith(comment) || sRecord.replaceAll(" ","").isEmpty()) continue;
					else if(sRecord.trim().equalsIgnoreCase(TectonicRegionType.ACTIVE_SHALLOW.toString()) ||
						sRecord.trim().equalsIgnoreCase(TectonicRegionType.STABLE_SHALLOW.toString()) ||
						sRecord.trim().equalsIgnoreCase(TectonicRegionType.SUBDUCTION_INTERFACE.toString()) ||
						sRecord.trim().equalsIgnoreCase(TectonicRegionType.SUBDUCTION_SLAB.toString())) break;
				}


			}// end if sRecord!=null

			// create logic tree structure for gmpe in active shallow region
			if(activeShallowGmpeNames!=null){
				// add logic tree to logic tree list
				gmpeLogicTreeHashMap.put(TectonicRegionType.ACTIVE_SHALLOW,createGmpeLogicTree(activeShallowGmpeNames, activeShallowGmpeWeights, component, intensityMeasureType, period, damping, truncType, truncLevel, stdType, vs30));

			} // end active shallow

			// create logic tree structure for gmpe in stable shallow region
			if(stableShallowGmpeNames!=null){
				// add logic tree to logic tree list
				gmpeLogicTreeHashMap.put(TectonicRegionType.STABLE_SHALLOW, createGmpeLogicTree(stableShallowGmpeNames, stableShallowGmpeWeights, component, intensityMeasureType, period, damping, truncType, truncLevel, stdType, vs30));
			} // end stable shallow

			// create logic tree structure for gmpe in subduction interface
			if(subductionInterfaceGmpeNames!=null){
				// add logic tree to logic tree list
				gmpeLogicTreeHashMap.put(TectonicRegionType.SUBDUCTION_INTERFACE, createGmpeLogicTree(subductionInterfaceGmpeNames, subductionInterfaceGmpeWeights, component, intensityMeasureType, period, damping, truncType, truncLevel, stdType, vs30));
			}

			// create logic tree structure for gmpe in subduction intraslab
			if(subductionIntraSlabGmpeNames!=null){
				// add logic tree to logic tree list
				gmpeLogicTreeHashMap.put(TectonicRegionType.SUBDUCTION_SLAB, createGmpeLogicTree(subductionIntraSlabGmpeNames, subductionIntraSlabGmpeWeights, component, intensityMeasureType, period, damping, truncType, truncLevel, stdType, vs30));
			}
		} catch(IOException e) {
			IOException ioe = new IOException("ERF file not found. Program stops.", e);
			e.printStackTrace();
			System.exit(-1);
		} // catch
	} // constructor
	
	/**
	 * create logic tree from string of names and string of weights
	 */
	private GemLogicTree<ScalarIntensityMeasureRelationshipAPI> createGmpeLogicTree(String gmpeNames, String gmpeWeights, String component, String intensityMeasureType,
			double period, double damping, String truncType, double truncLevel, String stdType,
			double vs30) {
		
	    ParameterChangeWarningEvent event = null;
		
		StringTokenizer name = new StringTokenizer(gmpeNames);
    	
		StringTokenizer weight = new StringTokenizer(gmpeWeights);
    	
    	if(name.countTokens()!=weight.countTokens()){
    		System.out.println("Number of gmpes do not corresponds to number of weights!");
    		System.out.println("Check your input!");
    		System.out.println("Execution stopped!");
    		System.exit(0);
    	}
    	
    	// create logic tree
    	GemLogicTree<ScalarIntensityMeasureRelationshipAPI> gmpeLogicTree
    	 = new GemLogicTree<ScalarIntensityMeasureRelationshipAPI>();
    	
    	// create branching level
        GemLogicTreeBranchingLevel branchingLevel = new GemLogicTreeBranchingLevel(1,"Gmpe Uncertainties",-1);
        
        // define branch
        GemLogicTreeBranch branch = null;
        
    	// number of branches
    	int numBranch = name.countTokens();
    	
    	// loop over branches
    	for(int i=0;i<numBranch;i++){
    		
    		// gmpe name
    		String gmpeName = name.nextToken();
    		
    		// gmpe weight
    		double gmpeWeight = Double.parseDouble(weight.nextToken());
    		
    		branch = new GemLogicTreeBranch((i+1), gmpeName, gmpeWeight);
    		
    		branchingLevel.addBranch(branch);
    		
    	}
    	
    	// add branching level to logic tree
    	gmpeLogicTree.addBranchingLevel(branchingLevel);

    	// create hashtable with gmpe
    	Hashtable<String,ScalarIntensityMeasureRelationshipAPI> gmpeHashTable = new Hashtable<String,ScalarIntensityMeasureRelationshipAPI>();
    	// loop over branches
    	for(int i=0;i<numBranch;i++){
    		
    		// gmpe name
    		String gmpeName = gmpeLogicTree.getBranchingLevel(0).getBranch(i).getBranchingValue();
    		
    		// get the Gmpe Class
            Class cl = null;
            try {
	            cl = Class.forName(packageName+gmpeName);
            } catch(ClassNotFoundException e) {
            	e = new ClassNotFoundException("Program stops!\nGMPE class not not found: \'" + packageName+gmpeName, e);
            	// TODO: Use log4j
	            e.printStackTrace();
	            System.exit(-1);
            }
    		
    		// get the constructor
    		Constructor cstr = null;
            try {
	            cstr = cl.getConstructor( new Class[] {ParameterChangeWarningListener.class});
            } catch(NoSuchMethodException e) {
            	// Should never happen. If yes:
	            // TODO: use log4j
            	System.out.println("Strange error. Stop of program:");
	            e.printStackTrace();
	            System.exit(-1);
            }
    		
    		// create an instance of the class
    		AttenuationRelationship ar = null;
            try {
	            ar = (AttenuationRelationship) cstr.newInstance(ParameterChangeWarningListener(event));
            } catch(IllegalAccessException e) {
            	// Should never happen. If yes:
	            // TODO: use log4j
            	System.out.println("Strange error. Stop of program:");
	            e.printStackTrace();
	            System.exit(-1);
            } catch(InstantiationException e) {
	            // TODO: use log4j
            	System.out.println("Correct this or report this error to the OpenGEM group. Stop of program:");
	            e.printStackTrace();
	            System.exit(-1);
            } catch(InvocationTargetException e) {
	            // TODO: use log4j
            	System.out.println("Correct this or report this error to the OpenGEM group. Stop of program:");
	            e.printStackTrace();
	            System.exit(-1);
            } catch(IllegalArgumentException e) {
	            // TODO: use log4j
            	System.out.println("Correct this or report this error to the OpenGEM group. Stop of program:");
	            e.printStackTrace();
	            System.exit(-1);            	
            }
            
    		
    		// set defaults parameters
    		ar.setParamDefaults();
    		
    		// set component
    		// first check if the chosen component is allowed
    		if(ar.getParameter(ComponentParam.NAME).isAllowed(component)){
    			ar.getParameter(ComponentParam.NAME).setValue(component);
    		}
    		else{
    	        System.out.println("The chosen component: "+component+" is not supported by "+gmpeName);
    	        System.out.println("The supported components are the following: ");
    	        System.out.println(ar.getParameter(ComponentParam.NAME).getConstraint());
    	        System.out.println("Check your input file!");
    	        System.out.println("Execution stopped.");
    	        System.exit(0);
//    	        InputStreamReader inp = new InputStreamReader(System.in);
//    	        BufferedReader br = new BufferedReader(inp);
//    			System.out.println("The chosen component: "+component+" is not allowed for "+gmpeName);
//    			System.out.println("The component param has the following constrains:");
//    			System.out.println(ar.getParameter(ComponentParam.NAME).getConstraint());
//    			System.out.println("Type one of the allowed values:");
//    			ar.getParameter(ComponentParam.NAME).setValue(br.readLine());
    		}
    		
    		// set intensity measure type
    		if(ar.getSupportedIntensityMeasuresList().containsParameter(intensityMeasureType)){
    			ar.setIntensityMeasure(intensityMeasureType);
    		}
    		else{
    	        System.out.println("The chosen intensity measure type: "+intensityMeasureType+" is not supported by "+gmpeName);
    	        System.out.println("The supported types are the following: ");
    	        System.out.println(ar.getSupportedIntensityMeasuresList().toString());
    	        System.out.println("Check your input file!");
    	        System.out.println("Execution stopped.");
    	        System.exit(0);
    		}
    		
    		// if SA set period and damping
    		if(intensityMeasureType.equalsIgnoreCase(SA_Param.NAME)){
    			
    			// period
    			if(ar.getParameter(PeriodParam.NAME).isAllowed(period)){
    				ar.getParameter(PeriodParam.NAME).setValue(period);
    			}
        		else{
        			System.out.println("The chosen period: "+period+" is not supported by "+gmpeName);
        			System.out.println("The allowed values are the following: ");
        			System.out.println(ar.getParameter(PeriodParam.NAME).getConstraint());
        			System.out.println("Check your input file");
        			System.out.println("Execution stopped.");
        			System.exit(0);
        		}
    			
    			// damping
    			if(ar.getParameter(DampingParam.NAME).isAllowed(damping)){
    				ar.getParameter(DampingParam.NAME).setValue(damping);
    			}
        		else{
        			System.out.println("The chosen damping: "+damping+" is not supported by "+gmpeName);
        			System.out.println("The allowed values are the following: ");
        			System.out.println(ar.getParameter(DampingParam.NAME).getConstraint());
        			System.out.println("Check your input file");
        			System.out.println("Execution stopped.");
        			System.exit(0);
        		}
    			
    		}
    		
    		// set gmpe truncation type
			if(ar.getParameter(SigmaTruncTypeParam.NAME).isAllowed(truncType)){
				ar.getParameter(SigmaTruncTypeParam.NAME).setValue(truncType);
			}
    		else{
    			System.out.println("The chosen truncation type: "+truncType+" is not supported.");
    			System.out.println("The allowed values are the following: ");
    			System.out.println(ar.getParameter(SigmaTruncTypeParam.NAME).getConstraint());
    			System.out.println("Check your input file");
    			System.out.println("Execution stopped.");
    			System.exit(0);
    		}
			
			// set gmpe truncation level
			if(ar.getParameter(SigmaTruncLevelParam.NAME).isAllowed(truncLevel)){
				ar.getParameter(SigmaTruncLevelParam.NAME).setValue(truncLevel);
			}
    		else{
    			System.out.println("The chosen truncation level: "+truncLevel+" is not supported.");
    			System.out.println("The allowed values are the following: ");
    			System.out.println(ar.getParameter(SigmaTruncLevelParam.NAME).getConstraint());
    			System.out.println("Check your input file");
    			System.out.println("Execution stopped.");
    			System.exit(0);
    		}
			
			// set standard deviation type
			if(ar.getParameter(StdDevTypeParam.NAME).isAllowed(stdType)){
				ar.getParameter(StdDevTypeParam.NAME).setValue(stdType);
			}
    		else{
    			System.out.println("The chosen standard deviation type: "+stdType+" is not supported by "+gmpeName);
    			System.out.println("The allowed values are the following: ");
    			System.out.println(ar.getParameter(StdDevTypeParam.NAME).getConstraint());
    			System.out.println("Check your input file");
    			System.out.println("Execution stopped.");
    			System.exit(0);
    		}
    		
    		// set vs30 value
			if(ar.getParameter(Vs30_Param.NAME).isAllowed(vs30)){
				ar.getParameter(Vs30_Param.NAME).setValue(vs30);
			}
    		else{
    			System.out.println("The chosen vs30 value: "+vs30+" is not valid");
    			System.out.println("The allowed values are the following: ");
    			System.out.println(ar.getParameter(Vs30_Param.NAME).getConstraint());
    			System.out.println("Check your input file");
    			System.out.println("Execution stopped.");
    			System.exit(0);
    		}
			
			// set end-branch mapping
			gmpeLogicTree.getEBMap().put(Integer.toString(gmpeLogicTree.getBranchingLevel(0).getBranch(i).getRelativeID()), ar);
    	}
    	
    	return gmpeLogicTree;
	}
	
	private static ParameterChangeWarningListener ParameterChangeWarningListener(
			ParameterChangeWarningEvent event) {
		return null;
	}
	
	public HashMap<TectonicRegionType,GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> getGmpeLogicTreeHashMap(){
		return this.gmpeLogicTreeHashMap;
	}
	
}
