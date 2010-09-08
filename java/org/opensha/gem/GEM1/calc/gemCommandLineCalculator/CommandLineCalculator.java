package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.StringTokenizer;

import org.opensha.commons.data.Site;
import org.opensha.commons.data.TimeSpan;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.geo.BorderType;
import org.opensha.commons.geo.GriddedRegion;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationList;
import org.opensha.commons.geo.Region;
import org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeHazard;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTree;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranch;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeBranchingLevel;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeRule;
import org.opensha.gem.GEM1.calc.gemLogicTree.GemLogicTreeRuleParam;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepository;
import org.opensha.gem.GEM1.calc.gemOutput.GEMHazardCurveRepositoryList;
import org.opensha.gem.GEM1.commons.UnoptimizedDeepCopy;
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.gem.GEM1.util.DistanceParams;
import org.opensha.gem.GEM1.util.IMLListParams;
import org.opensha.gem.GEM1.util.SiteParams;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GriddedRegionPoissonEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMFaultSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMPointSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSubductionFaultSourceData;
import org.opensha.sha.faultSurface.FaultTrace;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class CommandLineCalculator {

	// configuration data
	private CalculatorConfigData calcConfig;
	// array list containing mean groun motion map
	private ArrayList<Double> meanGroundMotionMap;
	// array list of sites
	private ArrayList<Site> sites;

	// keyword
	private static String MONTE_CARLO = "Monte Carlo";
	private static String FULL_CALCULATION = "Full Calculation";
	private static String MEAN_GROUND_MOTION_MAP = "Mean ground motion map";

	// for debugging
	private static Boolean D = false;


	public CommandLineCalculator(String calcConfigFile) throws IOException{

		// load calculation configuration data
		calcConfig = new CalculatorConfigData(calcConfigFile);

		// initialize container for output results
		// mean ground motion map
		meanGroundMotionMap = new ArrayList<Double>();

		// initialize site array
		sites = createSiteList(calcConfig);

	}

	/**
	 * This is the main method that do the calculations. According to the specifications in the
	 * configuration file the method will do the required calculations.
	 * At the moment the only implemented calculation is for mean ground motion map using a Monte Carlo
	 * approach.
	 * @throws SecurityException
	 * @throws IllegalArgumentException
	 * @throws IOException
	 * @throws ClassNotFoundException
	 * @throws InstantiationException
	 * @throws IllegalAccessException
	 * @throws NoSuchMethodException
	 * @throws InvocationTargetException
	 */
	public void doCalculation() throws SecurityException, IllegalArgumentException, IOException, ClassNotFoundException, InstantiationException, IllegalAccessException, NoSuchMethodException, InvocationTargetException{

		long startTimeMs = System.currentTimeMillis();

		if(calcConfig.getCalculationMode().equalsIgnoreCase(MONTE_CARLO)){

			if(calcConfig.getResultType().equalsIgnoreCase(MEAN_GROUND_MOTION_MAP)){

				// do calculation
				doCalculationThroughMonteCarloApproach();

				// save mean ground motion map
				saveMeanGroundMotionMapToGMTAsciiFile();

			}
			else{
				System.out.println("Result type: "+calcConfig.getResultType()+" non recognized. Check the configuration file!");
				System.out.println("Execution stopped!");
				System.exit(0);
			}

		}
		else if(calcConfig.getCalculationMode().equalsIgnoreCase(FULL_CALCULATION)){

			// do calculation
			doFullCalculation();

			// save mean ground motion map
			saveMeanGroundMotionMapToGMTAsciiFile();

		}
		else{
			System.out.println("Calculation mode: "+calcConfig.getCalculationMode()+" non recognized. Check the configuration file!");
			System.out.println("Execution stopped!");
			System.exit(0);
		}

        long taskTimeMs  = System.currentTimeMillis( ) - startTimeMs;
        
        System.out.println("Wall clock time (including time for saving output files)");
        // 1h = 60*60*10^3 ms
        System.out.printf("hours  : %6.3f\n",taskTimeMs/(60*60*Math.pow(10, 3)));
        // 1 min = 60*10^3 ms
        System.out.printf("minutes: %6.3f\n",taskTimeMs/(60*Math.pow(10, 3)));




	}

	private void doCalculationThroughMonteCarloApproach() throws IOException, SecurityException, IllegalArgumentException, ClassNotFoundException, InstantiationException, IllegalAccessException, NoSuchMethodException, InvocationTargetException{

		System.out.println("Performing calculation through Monte Carlo Approach.\n");

	    // load ERF logic tree data
	    ErfLogicTreeData erfLogicTree = new ErfLogicTreeData(calcConfig.getErfLogicTreeFile());

	    // load GMPE logic tree data
	    GmpeLogicTreeData gmpeLogicTree = new GmpeLogicTreeData(calcConfig.getGmpeLogicTreeFile(),calcConfig.getComponent(),calcConfig.getIntensityMeasureType(),
	    		                               calcConfig.getPeriod(), calcConfig.getDamping(), calcConfig.getTruncationType(), calcConfig.getTruncationLevel(),
	    		                               calcConfig.getStandardDeviationType(), calcConfig.getVs30Reference());
   
		// instantiate the repository for the results
		GEMHazardCurveRepositoryList hcRepList = new GEMHazardCurveRepositoryList();

		// number of hazard curves to be generated for each point
		int numHazCurves = calcConfig.getNumHazCurve();

	    // loop over number of hazard curves to be generated
	    for(int i=0;i<numHazCurves;i++){

	    	System.out.println("Realization number: "+(i+1)+", of: "+numHazCurves);

	    	// do calculation
			GemComputeHazard compHaz = new GemComputeHazard(
					calcConfig.getNumThreads(), 
					sites, 
					sampleGemLogicTreeERF(erfLogicTree.getErfLogicTree(),calcConfig), 
					sampleGemLogicTreeGMPE(gmpeLogicTree.getGmpeLogicTreeHashMap()),
					calcConfig.getImlList(),
					calcConfig.getMaxDistance() );

			// store results
			hcRepList.add(compHaz.getValues(),Integer.toString(i));

	    }

	    // save hazard curves
	    if (D) saveHazardCurves(calcConfig.getOutputDir(), hcRepList);

	    // calculate mean hazard map for the given prob of exceedance
		meanGroundMotionMap = hcRepList.getMeanGrounMotionMap(calcConfig.getProbExc());
	}

	private void doFullCalculation() throws IOException, SecurityException, IllegalArgumentException, ClassNotFoundException, InstantiationException, IllegalAccessException, NoSuchMethodException, InvocationTargetException{

		System.out.println("Performing full calculation. \n");

	    // load ERF logic tree data
	    ErfLogicTreeData erfLogicTree = new ErfLogicTreeData(calcConfig.getErfLogicTreeFile());

	    // load GMPE logic tree data
	    GmpeLogicTreeData gmpeLogicTree = new GmpeLogicTreeData(calcConfig.getGmpeLogicTreeFile(),calcConfig.getComponent(),calcConfig.getIntensityMeasureType(),
	    		                               calcConfig.getPeriod(), calcConfig.getDamping(), calcConfig.getTruncationType(), calcConfig.getTruncationLevel(),
	    		                               calcConfig.getStandardDeviationType(), calcConfig.getVs30Reference());


	    // compute ERF logic tree end-branch models
	    HashMap<String,ArrayList<GEMSourceData>> endBranchModels = computeErfLogicTreeEndBrancheModels(erfLogicTree.getErfLogicTree());
	    // print info
	    System.out.println("ERF logic tree end branch models (total number: "+endBranchModels.keySet().size()+").\n");
	    Iterator<String> erfEndBranchLabelIter = endBranchModels.keySet().iterator();
	    while(erfEndBranchLabelIter.hasNext()){

	    	String erfEndBranchLabel = erfEndBranchLabelIter.next();
	    	System.out.println("End branch label: "+erfEndBranchLabel+"\n");

	    }


		// compute gmpe logic tree end-branch models
		HashMap<String,HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>> gmpeEndBranchModel = computeGmpeLogicTreeEndBrancheModels(gmpeLogicTree.getGmpeLogicTreeHashMap());
		// print info
		System.out.println("GMPE logic tree end branch models (total number: "+gmpeEndBranchModel.keySet().size()+").\n");
		Iterator<String> gmpeEndBranchLabelIter = gmpeEndBranchModel.keySet().iterator();
		while(gmpeEndBranchLabelIter.hasNext()){

			String gmpeEndBranchLabel = gmpeEndBranchLabelIter.next();	
			System.out.println("End branch label: "+gmpeEndBranchLabel);

			Iterator<TectonicRegionType> trtIter = gmpeEndBranchModel.get(gmpeEndBranchLabel).keySet().iterator();
			while(trtIter.hasNext()){

				TectonicRegionType trt = trtIter.next();

				System.out.println("                  Tectonic region type: "+trt.toString()+
						" --> GMPE: "+gmpeEndBranchModel.get(gmpeEndBranchLabel).get(trt).getName());

			}
			System.out.println("\n");

		}

		// instantiate the repository for the results
		GEMHazardCurveRepositoryList hcRepList = new GEMHazardCurveRepositoryList();

	    // loop over ERF end-branch models
	    Iterator<String> endBranchLabels = endBranchModels.keySet().iterator();
	    while(endBranchLabels.hasNext()){

	    	// current erf end-branch model label
	    	String erfLabel = endBranchLabels.next();
	    	System.out.println("Processing end-branch model: "+erfLabel);

	    	// instantiate GEM1ERF with the source model corresponding
	    	// to the current label
	    	GEM1ERF erf = new GEM1ERF(endBranchModels.get(erfLabel));

			// set ERF parameters
			setGEM1ERFParams(erf, calcConfig);

			// loop over GMPE end-branch models
			Iterator<String> gmpeEndBranchLabels = gmpeEndBranchModel.keySet().iterator();
			while(gmpeEndBranchLabels.hasNext()){

				String gmpeLabel = gmpeEndBranchLabels.next();

				System.out.println("Processing gmpe end-branch model: "+gmpeLabel);

		    	// do calculation
				GemComputeHazard compHaz = new GemComputeHazard(
						calcConfig.getNumThreads(), 
						sites, 
						erf, 
						gmpeEndBranchModel.get(gmpeLabel),
						calcConfig.getImlList(),
						calcConfig.getMaxDistance() );

				// store results
				hcRepList.add(compHaz.getValues(),erfLabel+"-"+gmpeLabel);

			}

		    // calculate mean hazard map for the given prob of exceedance
			meanGroundMotionMap = hcRepList.getMeanGroundMotionMap(calcConfig.getProbExc(),erfLogicTree.getErfLogicTree(),gmpeLogicTree.getGmpeLogicTreeHashMap());


	    }


	}

	/**
	 * @param gmpeLogicTreeHashMap: this is an hash map relating a set of tectonic settings with a set of logic trees
	 * for gmpes. The idea is the user can define, for each tectonic setting, a different logic tree for the gmpes.
	 * @return an hash map relating an end branch label with an hash map
	 * that relates different tectonic settings with different gmpes.
	 * For instance if there are two logic tree for gmpes:
	 * Stable Region (branch 1: D&M2008, weight: 0.5; branch 2: M&P2008, weight: 0.5)
	 * Active Region (branch 1: B&A2008, weight: 0.5; branch 2: C&B2008, weight: 0.5)
	 * then the method will result in a hash map containing four end branch labels:
	 * Stable Region_1-ActiveRegion_1 (referring to an hash map: {(Stable Region: D&M2008),(Active Region: B&A2008)}
	 * Stable Region_1-ActiveRegion_2 (referring to an hash map: {(Stable Region: D&M2008),(Active Region: C&B2008)}
	 * Stable Region_2-ActiveRegion_1 (referring to an hash map: {(Stable Region: M&P2008),(Active Region: B&A2008)}
	 * Stable Region_2-ActiveRegion_2 (referring to an hash map: {(Stable Region: M&P2008),(Active Region: C&B2008)}
	 * NOTE: the major assumption in this method is that the logic tree for the Gmpes contains only one branching level.
	 */
	private HashMap<String,HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>> computeGmpeLogicTreeEndBrancheModels(HashMap<TectonicRegionType,GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTreeHashMap){

		// make deep copy
		HashMap<TectonicRegionType,GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> gmpeLogicTreeHashMapCopy = 
			(HashMap<TectonicRegionType,GemLogicTree<ScalarIntensityMeasureRelationshipAPI>>) UnoptimizedDeepCopy.copy(gmpeLogicTreeHashMap);

		// hash map containing gmpe end branch models
		HashMap<String,HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>> endBranchModels = 
			new HashMap<String,HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>>();

		// tectonic region types
		Iterator<TectonicRegionType> trtIter = gmpeLogicTreeHashMapCopy.keySet().iterator();
		ArrayList<TectonicRegionType> trtList = new ArrayList<TectonicRegionType>();
		while(trtIter.hasNext()) trtList.add(trtIter.next());

		// load gmpe models from first tectonic region type
		if(endBranchModels.isEmpty()){

			// number of branches for the first tectonic region type
			int numBranch = gmpeLogicTreeHashMapCopy.get(trtList.get(0)).getBranchingLevel(0).getBranchList().size();

			// loop over branches
			for(int i=0;i<numBranch;i++){

				// get current branch
				GemLogicTreeBranch branch = gmpeLogicTreeHashMapCopy.get(trtList.get(0)).getBranchingLevel(0).getBranch(i);

				// define label from branch ID number
				String label = trtList.get(0)+"_"+Integer.toString(branch.getRelativeID());

				// get gmpe
				ScalarIntensityMeasureRelationshipAPI gmpe = gmpeLogicTreeHashMapCopy.get(trtList.get(0)).getEBMap().get(Integer.toString(branch.getRelativeID()));

				HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI> newHashMap = new
					HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>();

				newHashMap.put(trtList.get(0), gmpe);

				// save in the hash map
                endBranchModels.put(label, newHashMap);

			}

			// remove processed tectonic setting 
			gmpeLogicTreeHashMapCopy.remove(trtList.get(0));
			trtList.remove(0);

		}


		if(!endBranchModels.isEmpty()){

			// while there are additional tectonic settings
			while(!gmpeLogicTreeHashMapCopy.keySet().isEmpty()){

				// loop over current end branch models
				Iterator<String> endBranchModelLabels = endBranchModels.keySet().iterator();
				ArrayList<String> labels = new ArrayList<String>();
				while(endBranchModelLabels.hasNext()) labels.add(endBranchModelLabels.next());
				for(String label: labels){

					// number of branches in the first branching level of the current tectonic setting
					int numBranch = gmpeLogicTreeHashMapCopy.get(trtList.get(0)).getBranchingLevel(0).getBranchList().size();

					// loop over branches
					for(int i=0;i<numBranch;i++){

						// get current branch
						GemLogicTreeBranch branch = gmpeLogicTreeHashMapCopy.get(trtList.get(0)).getBranchingLevel(0).getBranch(i);

						// new label
						String newLabel = label+"-"+trtList.get(0)+"_"+branch.getRelativeID();

						// get gmpe
						ScalarIntensityMeasureRelationshipAPI gmpe = gmpeLogicTreeHashMapCopy.get(trtList.get(0)).getEBMap().get(Integer.toString(branch.getRelativeID()));


						// add tectonic setting - gmpe
						// current end branch model
						HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI> newHashMap = new HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>();
						// copy previous entries
						Iterator<TectonicRegionType> iterTrt = endBranchModels.get(label).keySet().iterator();
						while(iterTrt.hasNext()){
							TectonicRegionType trt = iterTrt.next();
							ScalarIntensityMeasureRelationshipAPI ar =  endBranchModels.get(label).get(trt);
							newHashMap.put(trt, ar);
						}
						// add new entry
						newHashMap.put(trtList.get(0), gmpe);

						// add new entry in the end branch hash map
						endBranchModels.put(newLabel, newHashMap);

					}

					// from the hash map remove the entry corresponding
					// to the current model
					endBranchModels.remove(label);

				} // end loop over current end-branch models

				// remove processed tectonic setting
				gmpeLogicTreeHashMapCopy.remove(trtList.get(0));
				trtList.remove(0);			

			} // end while !gmpeLogicTreeHashMapCopy.keySet().isEmpty()

		} // end if !endBranchModels.isEmpty()

		return endBranchModels;

	}

	private HashMap<String, ArrayList<GEMSourceData>> computeErfLogicTreeEndBrancheModels(GemLogicTree<ArrayList<GEMSourceData>> erfLogicTree) throws IOException{

		// make deep copy
		GemLogicTree<ArrayList<GEMSourceData>> erfLogicTreeCopy = (GemLogicTree<ArrayList<GEMSourceData>>) UnoptimizedDeepCopy.copy(erfLogicTree);

		HashMap<String,ArrayList<GEMSourceData>> endBranchModels = new HashMap<String,ArrayList<GEMSourceData>>();

		// load source models from first branching level
		if(endBranchModels.isEmpty()){

			// number of branches in the first branching level
			int numBranch = erfLogicTreeCopy.getBranchingLevel(0).getBranchList().size();

			// loop over branches of the first branching level
			for(int i=0;i<numBranch;i++){

				// get current branch
				GemLogicTreeBranch branch = erfLogicTreeCopy.getBranchingLevel(0).getBranch(i);

				// define label from branch ID number
				String label = Integer.toString(branch.getRelativeID());

				// read the corresponding source model
				ArrayList<GEMSourceData> srcList = new InputModelData(branch.getNameInputFile(),calcConfig.getMfdBinWidth()).getSourceList();

				// save in the hash map
                endBranchModels.put(label, srcList);

			}

			// remove processed branching level
			erfLogicTreeCopy.getBranchingLevelsList().remove(0);

		}

		// if the hash map already contains the models from the
		// first branching levels go through the remaining 
		// branching levels (if they exist) and create the new models
		if(!endBranchModels.isEmpty()){

			// while there are additional branching levels
			while(!erfLogicTreeCopy.getBranchingLevelsList().isEmpty()){

				// loop over current end branch models
				Iterator<String> endBranchModelLabels = endBranchModels.keySet().iterator();
				ArrayList<String> labels = new ArrayList<String>();
				while(endBranchModelLabels.hasNext()) labels.add(endBranchModelLabels.next());
				for(String label: labels){

					// current end branch model
					ArrayList<GEMSourceData> srcList = endBranchModels.get(label);

					// from the current end branch model create
					// models corresponding to the branches in
					// the first branching level of the current logic tree

					// number of branches in the first branching level
					int numBranch = erfLogicTreeCopy.getBranchingLevel(0).getBranchList().size();

					// loop over branches of the first branching level
					for(int i=0;i<numBranch;i++){

						// get current branch
						GemLogicTreeBranch branch = erfLogicTreeCopy.getBranchingLevel(0).getBranch(i);

						// new label
						String newLabel = label+"_"+branch.getRelativeID();

						// new source model
						ArrayList<GEMSourceData> newSrcList = applyRuleToSourceList(srcList, branch.getRule());

						// add new entry
						endBranchModels.put(newLabel, newSrcList);

					}

					// from the hash map remove the entry corresponding
					// to the current model
					endBranchModels.remove(label);

				} // end loop over current end-branch models

				// remove processed branching level
				erfLogicTreeCopy.getBranchingLevelsList().remove(0);			

			} // end while !erfLogicTreeCopy.getBranchingLevelsList().isEmpty()

		} // end if !endBranchModels.isEmpty()

		return endBranchModels;

	}

	private void saveMeanGroundMotionMapToGMTAsciiFile() throws IOException{

		String outfile = calcConfig.getOutputDir()+"meanGroundMotionMap_"+calcConfig.getProbExc()*100+"%_"+calcConfig.getInvestigationTime()+"yr"+".dat";

		FileOutputStream oOutFIS = new FileOutputStream(outfile);
        BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
        BufferedWriter oWriter = new BufferedWriter(new OutputStreamWriter(oOutBIS));
        
        // loop over grid points
        for(int i=0;i<sites.size();i++){
        	
        	double lon = sites.get(i).getLocation().getLongitude();
        	double lat = sites.get(i).getLocation().getLatitude();
        	double gmv = meanGroundMotionMap.get(i);
        	
        	oWriter.write(String.format("%+8.4f %+7.4f %7.4e \n",lon,lat,gmv));
        	
        }
        
        oWriter.close();
        oOutBIS.close();
        oOutFIS.close();

	}




	private static void saveHazardCurves(String dirName, GEMHazardCurveRepositoryList hazardCurves) throws IOException{

		String outfile = dirName+"hazardCurves"+".dat";

		FileOutputStream oOutFIS = new FileOutputStream(outfile);
        BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
        BufferedWriter oWriter = new BufferedWriter(new OutputStreamWriter(oOutBIS));
       
        // first line contains ground motion values
		// loop over ground motion values
        oWriter.write(String.format("%8s %8s "," "," "));
		for(int igmv=0;igmv<hazardCurves.getHcRepList().get(0).getGmLevels().size();igmv++){
			double gmv = hazardCurves.getHcRepList().get(0).getGmLevels().get(igmv);
			gmv = Math.exp(gmv);
			oWriter.write(String.format("%7.4e ",gmv));
		}
		oWriter.write("\n");

        // loop over grid points
		for(int igp=0;igp<hazardCurves.getHcRepList().get(0).getNodesNumber();igp++){

			// loop over hazard curve realizations
			for(int ihc=0;ihc<hazardCurves.getHcRepList().size();ihc++){

				double lat = hazardCurves.getHcRepList().get(0).getGridNode().get(igp).getLocation().getLatitude();
				double lon = hazardCurves.getHcRepList().get(0).getGridNode().get(igp).getLocation().getLongitude();
				oWriter.write(String.format("%+8.4f %+7.4f ",lon,lat));

				GEMHazardCurveRepository hcRep = hazardCurves.getHcRepList().get(ihc);

				// loop over ground motion values
				for(int igmv=0;igmv<hcRep.getGmLevels().size();igmv++){
					double probEx = hcRep.getProbExceedanceList(igp)[igmv];
					oWriter.write(String.format("%7.4e ",probEx));
				}
				oWriter.write("\n");

			}

		}
        oWriter.close();
        oOutBIS.close();
        oOutFIS.close();

	}


	private static void saveFractiles(String dirName, double probLevel, GEMHazardCurveRepository fractile) throws IOException{

		String outfile = dirName+"hazardCurves_"+probLevel+".dat";

		FileOutputStream oOutFIS = new FileOutputStream(outfile);
        BufferedOutputStream oOutBIS = new BufferedOutputStream(oOutFIS);
        BufferedWriter oWriter = new BufferedWriter(new OutputStreamWriter(oOutBIS));
       
        // first line contains ground motion values
		// loop over ground motion values
        oWriter.write(String.format("%8s %8s "," "," "));
		for(int igmv=0;igmv<fractile.getGmLevels().size();igmv++){
			double gmv = fractile.getGmLevels().get(igmv);
			gmv = Math.exp(gmv);
			oWriter.write(String.format("%7.4e ",gmv));
		}
		oWriter.write("\n");

        // loop over grid points
		for(int igp=0;igp<fractile.getNodesNumber();igp++){

			double lat = fractile.getGridNode().get(igp).getLocation().getLatitude();
			double lon = fractile.getGridNode().get(igp).getLocation().getLongitude();
			oWriter.write(String.format("%+8.4f %+7.4f ",lon,lat));

				// loop over ground motion values
				for(int igmv=0;igmv<fractile.getGmLevels().size();igmv++){
					double probEx = fractile.getProbExceedanceList(igp)[igmv];
					oWriter.write(String.format("%7.4e ",probEx));
				}
				oWriter.write("\n");
		}
        oWriter.close();
        oOutBIS.close();
        oOutFIS.close();

	}

	private static ArrayList<Site> createSiteList(CalculatorConfigData calcConfig){

	    // arraylist of sites storing locations where hazard curves must be calculated
	    ArrayList<Site> sites = new ArrayList<Site>();

	    // create gridded region from borders coordinates and grid spacing
	    GriddedRegion gridReg = new GriddedRegion(calcConfig.getRegionBoundary(),BorderType.MERCATOR_LINEAR,calcConfig.getGridSpacing(),null);

	    // get list of locations in the region
	    LocationList locList = gridReg.getNodeList();

	    // store locations as sites
	    Iterator<Location> iter = locList.iterator();
	    while(iter.hasNext()) sites.add(new Site(iter.next()));

	    // return array list of sites
		return sites;
	}

	private static GEM1ERF sampleGemLogicTreeERF(GemLogicTree<ArrayList<GEMSourceData>> ltERF, CalculatorConfigData calcConfig) throws IOException{


		// erf to be returned
		GEM1ERF erf = null;

		// array list of sources that will contain the samples sources
		ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();

		// number of branching levels in the logic tree
		int numBranchingLevels = ltERF.getBranchingLevelsList().size();



		// sample first branching level to get the starting source model
		int branchNumber = ltERF.sampleBranchingLevel(0);

		// get the corresponding branch (the -1 is needed because branchNumber is the
		// number of the branch (starting from 1) and not the index of the branch
		GemLogicTreeBranch branch = ltERF.getBranchingLevel(0).getBranch(branchNumber-1);

		if(branch.getNameInputFile()!=null){

			// read input file model
			InputModelData inputModelData = new InputModelData(branch.getNameInputFile(),calcConfig.getMfdBinWidth());

			// load sources
			srcList = inputModelData.getSourceList();

		}
		else{
			System.out.println("The first branching level of the ERF logic tree does not contain a source model!!");
			System.out.println("Please correct your input!");
			System.out.println("Execution stopped!");
			System.exit(0);
		}

		// loop over sources
		// source index
		int sourceIndex = 0;
		for(GEMSourceData src: srcList){

			// for each source, loop over remaining branching levels and apply uncertainties
			for(int i=1;i<numBranchingLevels;i++){

				// sample the current branching level
				branchNumber = ltERF.sampleBranchingLevel(i);

				// get the sampled branch
				branch = ltERF.getBranchingLevel(i).getBranch(branchNumber-1);

				if(branch.getRule()!=null){

					// at the moment we apply rules to all source typologies. In the future we may want
					// to apply some filter (i.e. apply rule to this source type only...)

					// if area source
    				if(src instanceof GEMAreaSourceData){
    					
    					// replace the old source with the new source accordingly to the rule
    					srcList.set(sourceIndex, applyRuleToAreaSource((GEMAreaSourceData)src, branch.getRule()));
    					
    				}
    				
    				// if point source
    				if(src instanceof GEMPointSourceData){
    					
    					// replace the old source with the new source accordingly to the rule
    					srcList.set(sourceIndex, applyRuleToPointSource((GEMPointSourceData)src, branch.getRule()));
    					
    				}
    				
    				// if fault source
    				if(src instanceof GEMFaultSourceData){
    					
    					// replace the old source with the new  source accordingly to the rule
    					srcList.set(sourceIndex, applyRuleToFaultSource((GEMFaultSourceData)src, branch.getRule()));
    					
    				}
    				
    				// if subduction source
    				if(src instanceof GEMSubductionFaultSourceData){
    					
    					// replace the old source with the new  source accordingly to the rule
    					srcList.set(sourceIndex, applyRuleToSubductionFaultSource((GEMSubductionFaultSourceData)src, branch.getRule()));
    					
    				}
    				
                } // end if rule is defined
				else{

					System.out.println("No rule is defined at branching level: "+i);
					System.out.println("Please correct your input!");
					System.out.println("Execution stopped!");
					System.exit(0);

				} // end if no rule is defined

			} // end loop over branching levels

			sourceIndex = sourceIndex + 1;

		} // end loop over sources

		// instantiate ERF
		erf = new GEM1ERF(srcList);

		// set ERF parameters
		setGEM1ERFParams(erf, calcConfig);

		return erf;
	}

	/**
	 * This method applies an "uncertainty" rule to an area source data object
	 * @param areaSrc: source data object subject to uncertainty
	 * @param rule: GEMLogicTreeRule specifing parameter uncertainty
	 * @return: a new GEMAreaSourceData object with the parameter subject to the uncertainty
	 * changed according to the rule. In case the rule is not recognized 
	 * an error is thrown and execution stops
	 */
	private static GEMAreaSourceData applyRuleToAreaSource(GEMAreaSourceData areaSrc, GemLogicTreeRule rule){

		// define new area source
		GEMAreaSourceData newAreaSrc = areaSrc;

		// if uncertainties on GR Mmax or GR b value
		if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.mMaxGRRelative.toString()) || 
				rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.bGRRelative.toString())){

			// loop over mfds
			// mfd index
			int mfdIndex = 0;
			for(IncrementalMagFreqDist mfd: areaSrc.getMagfreqDistFocMech().getMagFreqDistList()){

				if (mfd instanceof GutenbergRichterMagFreqDist){

					// new mfd
					GutenbergRichterMagFreqDist newMfdGr = null;

					// uncertainties on Mmax
					if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.mMaxGRRelative.toString())){
						newMfdGr = applyMmaxGrRelative((GutenbergRichterMagFreqDist)mfd, rule.getVal(), areaSrc.getName());
					}
					// uncertainties on b value
					else if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.bGRRelative.toString())){
						newMfdGr = applybGrRelative((GutenbergRichterMagFreqDist)mfd, rule.getVal(), areaSrc.getName());
					}

					// substitute old mfd with new mfd
					newAreaSrc.getMagfreqDistFocMech().getMagFreqDistList()[mfdIndex] = newMfdGr;

				} // end if mfd is GR

				mfdIndex = mfdIndex + 1;
			} // end loop over mfds

			// return new area source
			return newAreaSrc;

		} // end if rule == mMaxGRRelative || == bGRRelative
		else{
			System.out.println("Rule: "+rule.getRuleName().toString()+" not supported.");
			System.out.println("Check your input. Execution is stopped.");
			System.exit(0);
		}

		return null;
	}

	/**
	 * This method applies an "uncertainty" rule to a point source data object
	 * @param pntSrc: source data object subject to uncertainty
	 * @param rule: GEMLogicTreeRule specifing parameter uncertainty
	 * @return: a new GEMPointSourceData object with the parameter subject to the uncertainty
	 * changed according to the rule. In case the rule is not recognized 
	 * an error is thrown and execution stops
	 */
	private static GEMPointSourceData applyRuleToPointSource(GEMPointSourceData pntSrc, GemLogicTreeRule rule){

		// new point source
		GEMPointSourceData newPntSource = pntSrc;

		// if uncertainties on GR Mmax or GR b value
		if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.mMaxGRRelative.toString()) || 
				rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.bGRRelative.toString())){

			// loop over mfds
			// mfd index
			int mfdIndex = 0;
			for(IncrementalMagFreqDist mfd: pntSrc.getHypoMagFreqDistAtLoc().getMagFreqDistList()){

				if(mfd instanceof GutenbergRichterMagFreqDist){

					GutenbergRichterMagFreqDist newMfdGr = null;

					// create new mfd by applying rule
					if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.mMaxGRRelative.toString())){
						newMfdGr = applyMmaxGrRelative((GutenbergRichterMagFreqDist)mfd, rule.getVal(), pntSrc.getName());
					}
					else if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.bGRRelative.toString())){
						newMfdGr = applybGrRelative((GutenbergRichterMagFreqDist)mfd, rule.getVal(), pntSrc.getName());
					}

					// substitute old mfd with new mfd
					newPntSource.getHypoMagFreqDistAtLoc().getMagFreqDistList()[mfdIndex] = newMfdGr;

				} // end if mfd is GR

				mfdIndex = mfdIndex + 1;
			} // end loop over mfd

			return newPntSource;

		} // end if rule == mMaxGRRelative || == bGRRelative
		else{
			System.out.println("Rule: "+rule.getRuleName().toString()+" not supported.");
			System.out.println("Check your input. Execution is stopped.");
			System.exit(0);
		}



		return null;
	}

	/**
	 * This method applies an "uncertainty" rule to a fault source data object
	 * @param faultSrc: source data object subject to uncertainty
	 * @param rule: GEMLogicTreeRule specifing parameter uncertainty
	 * @return: a new GEMFaultSourceData object with the parameter subject to the uncertainty
	 * changed according to the rule. In case the rule is not recognized 
	 * an error is thrown and execution stops
	 */
	private static GEMFaultSourceData applyRuleToFaultSource(GEMFaultSourceData faultSrc, GemLogicTreeRule rule){

		// if uncertainties on GR Mmax or GR b value
		if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.mMaxGRRelative.toString()) || 
				rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.bGRRelative.toString())){

			// mfd
			IncrementalMagFreqDist mfd = faultSrc.getMfd();

			if(mfd instanceof GutenbergRichterMagFreqDist){

				GutenbergRichterMagFreqDist newMfdGr = null;

				// create new mfd by applying rule
				if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.mMaxGRRelative.toString())){
					newMfdGr = applyMmaxGrRelative((GutenbergRichterMagFreqDist)mfd, rule.getVal(), faultSrc.getName());
				}
				else if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.bGRRelative.toString())){
					newMfdGr = applybGrRelative((GutenbergRichterMagFreqDist)mfd, rule.getVal(), faultSrc.getName());
				}

				// return new fault source with new mfd
				return new GEMFaultSourceData(faultSrc.getID(), faultSrc.getName(), faultSrc.getTectReg(), 
						newMfdGr, faultSrc.getTrace(), faultSrc.getDip(), 
						faultSrc.getDip(), faultSrc.getSeismDepthLow(), faultSrc.getSeismDepthUpp(), faultSrc.getFloatRuptureFlag());

			}// end if mfd is GR
			// if the uncertainty do not apply return the unchanged object
			else{
				return faultSrc;
			}

		} // end if rule == mMaxGRRelative || == bGRRelative
		else{
			System.out.println("Rule: "+rule.getRuleName().toString()+" not supported.");
			System.out.println("Check your input. Execution is stopped.");
			System.exit(0);
		}

		return null;
	}

	/**
	 * This method applies an "uncertainty" rule to a subduction source data object
	 * @param subFaultSrc: source data object subject to uncertainty
	 * @param rule: GEMLogicTreeRule specifing parameter uncertainty
	 * @return: a new GEMSubductionSourceData object with the parameter subject to uncertainty
	 * changed according to the rule. In case the rule is not recognized 
	 * an error is thrown and execution stops
	 */
	private static GEMSubductionFaultSourceData applyRuleToSubductionFaultSource(GEMSubductionFaultSourceData subFaultSrc, GemLogicTreeRule rule){

		// if uncertainties on GR Mmax or GR b value
		if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.mMaxGRRelative.toString()) || 
				rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.bGRRelative.toString())){

			// mfd
			IncrementalMagFreqDist mfd = subFaultSrc.getMfd();

			if(mfd instanceof GutenbergRichterMagFreqDist){

				GutenbergRichterMagFreqDist newMfdGr = null;

				// create new mfd by applying rule
				if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.mMaxGRRelative.toString())){
					newMfdGr = applyMmaxGrRelative((GutenbergRichterMagFreqDist)mfd, rule.getVal(), subFaultSrc.getName());
				}
				else if(rule.getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.bGRRelative.toString())){
					newMfdGr = applybGrRelative((GutenbergRichterMagFreqDist)mfd, rule.getVal(), subFaultSrc.getName());
				}

				// return new subduction fault source with the new mfd
				return new GEMSubductionFaultSourceData(subFaultSrc.getID(), subFaultSrc.getName(), subFaultSrc.getTectReg(),
						subFaultSrc.getTopTrace(), subFaultSrc.getBottomTrace(), 
						subFaultSrc.getRake(), newMfdGr, subFaultSrc.getFloatRuptureFlag());

			} // end if mfd is GR	
			// if uncertainty does not apply return unchanged object
			else{
				return subFaultSrc;
			}

		}// end if rule == mMaxGRRelative || == bGRRelative
		else{
			System.out.println("Rule: "+rule.getRuleName().toString()+" not supported.");
			System.out.println("Check your input. Execution is stopped.");
			System.exit(0);
		}

		return null;
	}

	private static ArrayList<GEMSourceData> applyRuleToSourceList(ArrayList<GEMSourceData> srcList, GemLogicTreeRule rule){

		ArrayList<GEMSourceData> newSrcList = new ArrayList<GEMSourceData>();

		for(GEMSourceData src:srcList){

			if(src instanceof GEMAreaSourceData){
				newSrcList.add(applyRuleToAreaSource((GEMAreaSourceData)src,rule));
			}
			else if(src instanceof GEMPointSourceData){
				newSrcList.add(applyRuleToPointSource((GEMPointSourceData)src,rule));
			}
			else if(src instanceof GEMFaultSourceData){
				newSrcList.add(applyRuleToFaultSource((GEMFaultSourceData)src,rule));
			}
			else if(src instanceof GEMSubductionFaultSourceData){
				newSrcList.add(applyRuleToSubductionFaultSource((GEMSubductionFaultSourceData)src,rule));
			}

		}

		return newSrcList;

	}

	/**
	 * 
	 * @param mfdGR: original magnitude frequency distribution
	 * @param deltaMmax: uncertainty on maximum magnitude
	 * @param areaSrc: source
	 * @return
	 */
	private static GutenbergRichterMagFreqDist applyMmaxGrRelative(GutenbergRichterMagFreqDist mfdGR, double deltaMmax, String sourceName){

		// minimum magnitude
		double mMin = mfdGR.getMagLower();
		// b value
		double bVal = mfdGR.get_bValue();
		// total moment rate
		double totMoRate = mfdGR.getTotalMomentRate();
		// deltaM
		double deltaM = mfdGR.getDelta();

		// calculate new mMax value
		// old mMax value
		double mMax = mfdGR.getMagUpper();
		// add uncertainty value (deltaM/2 is added because mMax 
		// refers to bin center
		mMax = mMax+deltaM/2+deltaMmax;
		// round mMax with respect to deltaM
		mMax = Math.round(mMax/deltaM)*deltaM;
		// move back to bin center
		mMax = mMax-deltaM/2;
		//System.out.println("New mMax: "+mMax);

		if(mMax - mMin>=deltaM){

			// calculate number of magnitude values
			int numVal = (int)Math.round((mMax-mMin)/deltaM + 1);

			// create new GR mfd
			GutenbergRichterMagFreqDist newMfdGr = new GutenbergRichterMagFreqDist(mMin,numVal,deltaM);
			newMfdGr.setAllButTotCumRate(mMin, mMax, totMoRate, bVal);

			// return new mfd
			return newMfdGr;


		}
		else{
			// stop execution and return null
			System.out.println("Uncertaintiy value: "+deltaMmax+" on maximum magnitude for source: "+sourceName+" give maximum magnitude smaller than minimum magnitude!");
			System.out.println("Check your input. Execution stopped.");
			return null;
		}

	}

	private static GutenbergRichterMagFreqDist applybGrRelative(GutenbergRichterMagFreqDist mfdGR, double deltaB, String sourceName){

		// minimum magnitude
		double mMin = mfdGR.getMagLower();
		// maximum magnitude
		double mMax = mfdGR.getMagUpper();
		// b value
		double bVal = mfdGR.get_bValue();
		// total moment rate
		double totMoRate = mfdGR.getTotalMomentRate();
		// deltaM
		double deltaM = mfdGR.getDelta();

		// calculate new b value
		bVal = bVal + deltaB;

		if(bVal>=0.0){

			// calculate number of magnitude values
			int numVal = (int)Math.round((mMax-mMin)/deltaM + 1);

			// create new GR mfd
			GutenbergRichterMagFreqDist newMfdGr = new GutenbergRichterMagFreqDist(mMin,numVal,deltaM);
			newMfdGr.setAllButTotCumRate(mMin, mMax, totMoRate, bVal);

			// return new mfd
			return newMfdGr;

		}
		else{
			System.out.println("Uncertaintiy value: "+deltaB+" on b value for source: "+sourceName+" give b value smaller than 0!");
			System.out.println("Check your input. Execution stopped!");
			System.exit(0);
			return null;
		}

	}

	/**
	 * Set the GEM1ERF params given the parameters defined in
	 * @param erf: erf for which parameters have to be set
	 * @param calcConfig: calculator configuration obejct containing parameters
	 * for the ERF
	 */
	private static void setGEM1ERFParams(GEM1ERF erf, CalculatorConfigData calcConfig){

		// set minimum magnitude
		erf.setParameter(GEM1ERF.MIN_MAG_NAME, calcConfig.getMinMag());

		// set time span
		TimeSpan timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
		timeSpan.setDuration(calcConfig.getInvestigationTime());
		erf.setTimeSpan(timeSpan);

		// params for area source
		// set inclusion of area sources in the calculation
		erf.setParameter(GEM1ERF.INCLUDE_AREA_SRC_PARAM_NAME, calcConfig.getIncludeAreaSource());
		// set rupture type
		erf.setParameter(GEM1ERF.AREA_SRC_RUP_TYPE_NAME, calcConfig.getAreaSourceRuptureModel());
		// set area discretization
		erf.setParameter(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME, calcConfig.getAreaSourceDiscretization());
		// set mag-scaling relationship
		erf.setParameter(GEM1ERF.AREA_SRC_MAG_SCALING_REL_PARAM_NAME, calcConfig.getAreaSourceMagAreaRel());

		// params for grid source
		// inclusion of grid sources in the calculation
		erf.setParameter(GEM1ERF.INCLUDE_GRIDDED_SEIS_PARAM_NAME, calcConfig.getIncludeGridSource());
		// rupture model
		erf.setParameter(GEM1ERF.GRIDDED_SEIS_RUP_TYPE_NAME, calcConfig.getGridSourceRuptureModel());
		// mag-scaling relationship
		erf.setParameter(GEM1ERF.GRIDDED_SEIS_MAG_SCALING_REL_PARAM_NAME, calcConfig.getGridSourceMagAreaRel());

		// params for fault source
		// inclusion of fault sources in the calculation
		erf.setParameter(GEM1ERF.INCLUDE_FAULT_SOURCES_PARAM_NAME, calcConfig.getIncludeFaultSource());
		// rupture offset
		erf.setParameter(GEM1ERF.FAULT_RUP_OFFSET_PARAM_NAME, calcConfig.getFaultSourceRuptureOffset());
		// surface discretization
		erf.setParameter(GEM1ERF.FAULT_DISCR_PARAM_NAME, calcConfig.getFaultSourceSurfaceDiscretization());
		// mag-scaling relationship
		erf.setParameter(GEM1ERF.FAULT_MAG_SCALING_REL_PARAM_NAME, calcConfig.getFaultSourceMagAreaRel());
		// mag-scaling sigma
		erf.setParameter(GEM1ERF.FAULT_SCALING_SIGMA_PARAM_NAME, calcConfig.getFaultSourceMagSigma());
		// rupture aspect ratio
		erf.setParameter(GEM1ERF.FAULT_RUP_ASPECT_RATIO_PARAM_NAME, calcConfig.getFaultSourceRuptureAspectRatio());
		// rupture floating type
		erf.setParameter(GEM1ERF.FAULT_FLOATER_TYPE_PARAM_NAME, calcConfig.getFaultSourceRuptureFloatingType());

		// params for subduction fault
		// inclusion of fault sources in the calculation
		erf.setParameter(GEM1ERF.INCLUDE_SUBDUCTION_SOURCES_PARAM_NAME, calcConfig.getIncludeSubductionFaultSource());
		// rupture offset
		erf.setParameter(GEM1ERF.SUB_RUP_OFFSET_PARAM_NAME, calcConfig.getSubductionFaultSourceRuptureOffset());
		// surface discretization
		erf.setParameter(GEM1ERF.SUB_DISCR_PARAM_NAME, calcConfig.getSubductionFaultSourceSurfaceDiscretization());
		// mag-scaling relationship
		erf.setParameter(GEM1ERF.SUB_MAG_SCALING_REL_PARAM_NAME, calcConfig.getSubductionFaultSourceMagAreaRel());
		// mag-scaling sigma
		erf.setParameter(GEM1ERF.SUB_SCALING_SIGMA_PARAM_NAME, calcConfig.getSubductionFaultSourceMagSigma());
		// rupture aspect ratio
		erf.setParameter(GEM1ERF.SUB_RUP_ASPECT_RATIO_PARAM_NAME, calcConfig.getSubductionFaultSourceRuptureAspectRatio());
		// rupture floating type
		erf.setParameter(GEM1ERF.SUB_FLOATER_TYPE_PARAM_NAME, calcConfig.getSubductionFaultSourceRuptureFloatingType());

		// update
		erf.updateForecast();

	}

	private static HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI> sampleGemLogicTreeGMPE(HashMap<TectonicRegionType,GemLogicTree<ScalarIntensityMeasureRelationshipAPI>> listLtGMPE){

		HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI> hm = new HashMap<TectonicRegionType,ScalarIntensityMeasureRelationshipAPI>();

		// loop over tectonic regions
		Iterator<TectonicRegionType> iter = listLtGMPE.keySet().iterator();
		while(iter.hasNext()){

			// get tectonic region type
			TectonicRegionType trt = iter.next();

			// get corresponding logic tree
			GemLogicTree<ScalarIntensityMeasureRelationshipAPI> ltGMPE = (GemLogicTree<ScalarIntensityMeasureRelationshipAPI>) listLtGMPE.get(trt);

			// sample the first branching level
			int branch = ltGMPE.sampleBranchingLevel(0);

			// select the corresponding gmpe from the end-branch mapping
			ScalarIntensityMeasureRelationshipAPI gmpe = ltGMPE.getEBMap().get(Integer.toString(branch));

			hm.put(trt, gmpe);
		}

		return hm;

	}

	
	
	// for testing
	public static void main(String[] args) throws IOException, SecurityException, IllegalArgumentException, ClassNotFoundException, InstantiationException, IllegalAccessException, NoSuchMethodException, InvocationTargetException{
		
		System.out.println("xxr: user directory to put the file CalculatorConfig.inp -> " + System.getProperty("user.dir"));
		CommandLineCalculator clc = new CommandLineCalculator("CalculatorConfig.inp");
		
		clc.doCalculation();
		
//		clc.doCalculationThroughMonteCarloApproach();
		
//		clc.saveMeanGroundMotionMapToGMTAsciiFile();
		
		System.exit(0);
		
	}

//	/**
//	 * @param args
//	 * @throws IOException 
//	 * @throws IllegalAccessException 
//	 * @throws InstantiationException 
//	 * @throws ClassNotFoundException 
//	 * @throws NoSuchMethodException 
//	 * @throws SecurityException 
//	 * @throws InvocationTargetException 
//	 * @throws IllegalArgumentException 
//	 */
//	public static void main(String[] args) throws IOException, ClassNotFoundException, InstantiationException, IllegalAccessException, SecurityException, NoSuchMethodException, IllegalArgumentException, InvocationTargetException {
//
//		
//		// calculator configuration file
//		String calculatorConfigFile = "CalculatorConfig.inp";
//		
//	    // read configuration file
//	    CalculatorConfigData calcConfig = new CalculatorConfigData(calculatorConfigFile);
//	    
//	    
//	    
//	    // read ERF logic tree file
//	    ErfLogicTreeData erfLogicTree = new ErfLogicTreeData(calcConfig.getErfLogicTreeFile());
//	    
//	    // print to standard output the erf logic tree structure
//	    // just to be sure that input file is read correctly
//	    erfLogicTree.getErfLogicTree().printGemLogicTreeStructure();
//	    
//	    // read GMPE logic tree file and set gmpe logic tree
//	    GmpeLogicTreeData gmpeLogicTree = new GmpeLogicTreeData(calcConfig.getGmpeLogicTreeFile(),calcConfig.getComponent(),calcConfig.getIntensityMeasureType(),
//	    		                               calcConfig.getPeriod(), calcConfig.getDamping(), calcConfig.getTruncationType(), calcConfig.getTruncationLevel(),
//	    		                               calcConfig.getStandardDeviationType(), calcConfig.getVs30Reference());
//	    
//    	// get logic tree for each tectonic type and print the structure to standard output
//	    // again to check that the input file is read correctly
//	    Iterator<TectonicRegionType> tecRegTypeIter =  gmpeLogicTree.getGmpeLogicTreeHashMap().keySet().iterator();
//	    while(tecRegTypeIter.hasNext()){
//	    	TectonicRegionType trt = tecRegTypeIter.next();
//	    	System.out.println("Gmpe Logic Tree for "+trt);
//	    	gmpeLogicTree.getGmpeLogicTreeHashMap().get(trt).printGemLogicTreeStructure();
//	    } 
//   
//		// instantiate the repository for the results
//		GEMHazardCurveRepositoryList hcRepList = new GEMHazardCurveRepositoryList();
//	    
//		// get list of sites where hazard curves have to be calculated
//		ArrayList<Site> locs = createSiteList(calcConfig);
//		
//	    // loop over number of hazard curves to be generated
//	    for(int i=0;i<calcConfig.getNumHazCurve();i++){
//
//	    	// do calculation
//			GemComputeHazard compHaz = new GemComputeHazard(
//					calcConfig.getNumThreads(), 
//					locs, 
//					sampleGemLogicTreeERF(erfLogicTree.getErfLogicTree(),calcConfig), 
//					sampleGemLogicTreeGMPE(gmpeLogicTree.getGmpeLogicTreeHashMap()),
//					calcConfig.getImlList(),
//					calcConfig.getMaxDistance() );
//			
//			// store results
//			hcRepList.add(compHaz.getValues(),Integer.toString(i));
//	    	
//	    }
//	    
//		// save hazard curves
//		saveHazardCurves(calcConfig.getOutputDir(),hcRepList);
//		
//		// calculate fractiles (median)
//		GEMHazardCurveRepository fractile = hcRepList.getQuantiles(0.5);
//		// save
//		saveFractiles(calcConfig.getOutputDir(), 0.5, fractile);
//		
//		// calculate fractiles (1st quartile)
//		fractile = hcRepList.getQuantiles(0.25);
//		// save
//		saveFractiles(calcConfig.getOutputDir(), 0.25, fractile);
//		
//		// calculate fractiles (3rd quartile)
//		fractile = hcRepList.getQuantiles(0.75);
//		// save
//		saveFractiles(calcConfig.getOutputDir(), 0.75, fractile);
//		
//		System.exit(0);
//	    
//	    
//	    
//
//	} // end main
	
}
