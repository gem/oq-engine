package org.opensha.gem.GEM1.calc.gemCommandLineCalculator;

import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.BufferedWriter;
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
import org.opensha.gem.GEM1.util.CpuParams;
import org.opensha.gem.GEM1.util.DistanceParams;
import org.opensha.gem.GEM1.util.IMLListParams;
import org.opensha.gem.GEM1.util.SiteParams;
import org.opensha.sha.earthquake.ProbEqkSource;
import org.opensha.sha.earthquake.griddedForecast.MagFreqDistsForFocalMechs;
import org.opensha.sha.earthquake.rupForecastImpl.GriddedRegionPoissonEqkSource;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.GEM1ERF;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMAreaSourceData;
import org.opensha.sha.earthquake.rupForecastImpl.GEM1.SourceData.GEMSourceData;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.ScalarIntensityMeasureRelationshipAPI;
import org.opensha.sha.magdist.GutenbergRichterMagFreqDist;
import org.opensha.sha.magdist.IncrementalMagFreqDist;
import org.opensha.sha.util.TectonicRegionType;

public class CommandLineCalculator {

	/**
	 * @param args
	 * @throws IOException 
	 * @throws IllegalAccessException 
	 * @throws InstantiationException 
	 * @throws ClassNotFoundException 
	 * @throws NoSuchMethodException 
	 * @throws SecurityException 
	 * @throws InvocationTargetException 
	 * @throws IllegalArgumentException 
	 */
	public static void main(String[] args) throws IOException, ClassNotFoundException, InstantiationException, IllegalAccessException, SecurityException, NoSuchMethodException, IllegalArgumentException, InvocationTargetException {
		
//		/Users/damianomonelli/Documents/Workspace/OpenSHA/src/org/opensha/gem/GEM1/data/command_line_input_files/CalculatorConfig.inp
		
		// calculator configuration file
		String calculatorConfigFile = "/Users/damianomonelli/Documents/Workspace/OpenSHA/src/org/opensha/gem/GEM1/data/command_line_input_files/CalculatorConfig.inp";
	    
	    // read configuration file
	    CalculatorConfigData calcConfig = new CalculatorConfigData(calculatorConfigFile);
	    
	    // read ERF logic tree file
	    ErfLogicTreeData erfLogicTree = new ErfLogicTreeData(calcConfig.getErfLogicTreeFile());
	    
	    // print to standard output the erf logic tree structure
	    // just to be sure that input file is read correctly
	    erfLogicTree.getErfLogicTree().printGemLogicTreeStructure();
	    
	    // read GMPE logic tree file and set gmpe logic tree
	    GmpeLogicTreeData gmpeLogicTree = new GmpeLogicTreeData(calcConfig.getGmpeLogicTreeFile(),calcConfig.getComponent(),calcConfig.getIntensityMeasureType(),
	    		                               calcConfig.getPeriod(), calcConfig.getDamping(), calcConfig.getTruncationType(), calcConfig.getTruncationLevel(),
	    		                               calcConfig.getStandardDeviationType(), calcConfig.getVs30Reference());
	    
    	// get logic tree for each tectonic type and print the structure to standard output
	    // again to check that the input file is read correctly
	    Iterator<TectonicRegionType> tecRegTypeIter =  gmpeLogicTree.getGmpeLogicTreeHashMap().keySet().iterator();
	    while(tecRegTypeIter.hasNext()){
	    	TectonicRegionType trt = tecRegTypeIter.next();
	    	System.out.println("Gmpe Logic Tree for "+trt);
	    	gmpeLogicTree.getGmpeLogicTreeHashMap().get(trt).printGemLogicTreeStructure();
	    } 
   
		// instantiate the repository for the results
		GEMHazardCurveRepositoryList hcRepList = new GEMHazardCurveRepositoryList();
	    
		// get list of sites where hazard curves have to be calculated
		ArrayList<Site> locs = createLocList(calcConfig);
		
	    // loop over number of hazard curves to be generated
	    for(int i=0;i<calcConfig.getNumHazCurve();i++){

	    	// do calculation
			GemComputeHazard compHaz = new GemComputeHazard(
					calcConfig.getNumThreads(), 
					locs, 
					sampleGemLogicTreeERF(erfLogicTree.getErfLogicTree(),calcConfig), 
					sampleGemLogicTreeGMPE(gmpeLogicTree.getGmpeLogicTreeHashMap()),
					calcConfig.getImlList(),
					calcConfig.getMaxDistance() );
			
			// store results
			hcRepList.add(compHaz.getValues(),Integer.toString(i));
	    	
	    }
	    
		// save hazard curves
		saveHazardCurves(calcConfig.getOutputDir(),hcRepList);
		
		// calculate fractiles (median)
		GEMHazardCurveRepository fractile = hcRepList.getQuantiles(0.5);
		// save
		saveFractiles(calcConfig.getOutputDir(), 0.5, fractile);
		
		// calculate fractiles (1st quartile)
		fractile = hcRepList.getQuantiles(0.25);
		// save
		saveFractiles(calcConfig.getOutputDir(), 0.25, fractile);
		
		// calculate fractiles (3rd quartile)
		fractile = hcRepList.getQuantiles(0.75);
		// save
		saveFractiles(calcConfig.getOutputDir(), 0.75, fractile);
		
		System.exit(0);
	    
	    
	    

	} // end main
	
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
	
	private static ArrayList<Site> createLocList(CalculatorConfigData calcConfig){
		
	    // arraylist of sites storing locations where hazard curves must be calculated
	    ArrayList<Site> locs = new ArrayList<Site>();
		
	    // create gridded region from borders coordinates and grid spacing
	    GriddedRegion gridReg = new GriddedRegion(calcConfig.getRegionBoundary(),BorderType.MERCATOR_LINEAR,calcConfig.getGridSpacing(),null);
	    
	    // get list of locations in the region
	    LocationList locList = gridReg.getNodeList();

	    // store locations as sites
	    Iterator<Location> iter = locList.iterator();
	    while(iter.hasNext()) locs.add(new Site(iter.next()));
		
	    // return array list of sites
		return locs;
	}
	
	private static GEM1ERF sampleGemLogicTreeERF(GemLogicTree<ArrayList<GEMSourceData>> ltERF, CalculatorConfigData calcConfig) throws IOException{
		
		// erf
		GEM1ERF erf = null;
		
		// array list of sources
		ArrayList<GEMSourceData> srcList = new ArrayList<GEMSourceData>();
		
		// number of branching levels
		int numBranchingLevels = ltERF.getBranchingLevelsList().size();
		
		// get source model from first branching level
		// sample branch from first branching level
		int branchNumber = ltERF.sampleBranchingLevel(0);
		
		// get the corresponding branch (the -1 is needed because branchNumber is the
		// number of the branch (starting from 1) and not the index of the branch
		GemLogicTreeBranch branch = ltERF.getBranchingLevel(0).getBranch(branchNumber-1);
		
		if(branch.getNameInputFile()!=null){
			
			// read input file model
			InputModelData inputModelData = new InputModelData(branch.getNameInputFile(),calcConfig.getMinMag(),calcConfig.getMfdBinWidth());
			
			// load sources
			srcList = inputModelData.getSourceList();
			
//			// loop over sources and print total moment rate for each source
//			System.out.println("Sources before sampling");
//			for(int is=0;is<srcList.size();is++){
//				GEMAreaSourceData src = (GEMAreaSourceData) srcList.get(is);
//				System.out.println("Name: "+srcList.get(is).getName()+", total moment rate: "+src.getMagfreqDistFocMech().getFirstMagFreqDist().getTotalMomentRate());
//			}
			
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
				
				// get a sample of the corresponding branching level
				branchNumber = ltERF.sampleBranchingLevel(i);
				
				// get the sampled branch
				branch = ltERF.getBranchingLevel(i).getBranch(branchNumber-1);
				
				if(branch.getRule()!=null){
					
					// apply rule
					// uncertainty on maximum magnitude
	    			if(branch.getRule().getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.mMaxGRRelative.toString())){
	    				
	    				if(src instanceof GEMAreaSourceData){
	    					
	    					//System.out.println("Applying mMaxRule");
	    					
	    					// define area source
	    					GEMAreaSourceData areaSrc = (GEMAreaSourceData)src;
	    					
	    					// loop over mfds
	    					// mfd index
	    					int mfdIndex = 0;
	    					for(IncrementalMagFreqDist mfd: areaSrc.getMagfreqDistFocMech().getMagFreqDistList()){
	    						
	    						if (mfd instanceof GutenbergRichterMagFreqDist){
	    							
	    							GutenbergRichterMagFreqDist mfdGR = (GutenbergRichterMagFreqDist)mfd;
	    							
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
	    							//System.out.println("Old mMax: "+mMax);
	    							// add uncertainty value (deltaM/2 is added because mMax 
	    							// refers to bin center
	    							mMax = mMax+deltaM/2+branch.getRule().getVal();
	    							// round mMax with respect to deltaM
	    							mMax = Math.round(mMax/deltaM)*deltaM;
	    							// move back to bin center
	    							mMax = mMax-deltaM/2;
	    							//System.out.println("New mMax: "+mMax);
	    							
	    							if(mMax - mMin>=deltaM){
	    								
	    								// calculate number of magnitude values
	    								int numVal = (int)((mMax-mMin)/deltaM + 1);
		    							
		    							// create new GR mfd
		    							GutenbergRichterMagFreqDist newMfdGr = new GutenbergRichterMagFreqDist(mMin,numVal,deltaM);
		    							newMfdGr.setAllButTotCumRate(mMin, mMax, totMoRate, bVal);
		    							
		    							// substitute old mfd with new mfd
		    							areaSrc.getMagfreqDistFocMech().getMagFreqDistList()[mfdIndex] = newMfdGr;
		    							
		    							
	    							}
	    							else{
	    								System.out.println("Uncertaintiy value: "+branch.getRule().getVal()+" on maximum magnitude for source: "+areaSrc.getName()+" give maximum magnitude smaller than minimum magnitude!");
	    								System.out.println("In this case uncertainties are not taken into account.");
	    								System.out.println("Execution continues but be aware of that!");
	    							}
	    							
	    							
	    							
	    						} // end if mfd is GR
	    						else{
	    							System.out.println("mMaxRelative rule is supported only for GR mfd!");
	    	    					System.out.println("Please correct your input!");
	    	    					System.out.println("Execution stopped!");
	    	    					System.exit(0);
	    						} // end if not GR
	    						
	    						mfdIndex = mfdIndex + 1;
	    					} // end loop over mfds
	    					
	    					// replace the old area source with the new area source
	    					srcList.set(sourceIndex, areaSrc);
	    					
	    				} // end if area source
	    				else{
	    					System.out.println("Source "+src.getClass().getName()+" not supported!");
	    					System.out.println("Please correct your input!");
	    					System.out.println("Execution stopped!");
	    					System.exit(0);
	    				} // end if not area source
	    				
	    			} // end if mMaxRule
	    			// uncertainties on GR b value
	    			else if(branch.getRule().getRuleName().toString().equalsIgnoreCase(GemLogicTreeRuleParam.bGRRelative.toString())){
	    				
	    				if(src instanceof GEMAreaSourceData){
	    					
	    					// define area source
	    					GEMAreaSourceData areaSrc = (GEMAreaSourceData)src;
	    					
	    					// loop over mfds
	    					// mfd index
	    					int mfdIndex = 0;
	    					for(IncrementalMagFreqDist mfd: areaSrc.getMagfreqDistFocMech().getMagFreqDistList()){
	    						
	    						if (mfd instanceof GutenbergRichterMagFreqDist){
	    							
	    							GutenbergRichterMagFreqDist mfdGR = (GutenbergRichterMagFreqDist)mfd;
	    							
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
	    							bVal = bVal + branch.getRule().getVal();
	    							
	    							if(bVal>=0.0){
	    								
	    								// calculate number of magnitude values
	    								int numVal = (int)((mMax-mMin)/deltaM + 1);
		    							
		    							// create new GR mfd
		    							GutenbergRichterMagFreqDist newMfdGr = new GutenbergRichterMagFreqDist(mMin,numVal,deltaM);
		    							newMfdGr.setAllButTotCumRate(mMin, mMax, totMoRate, bVal);
		    							
		    							// substitute old mfd with new mfd
		    							areaSrc.getMagfreqDistFocMech().getMagFreqDistList()[mfdIndex] = newMfdGr;
		    							
		    							
	    							}
	    							else{
	    								System.out.println("Uncertaintiy value: "+branch.getRule().getVal()+" on b value for source: "+areaSrc.getName()+" give b value smaller than 0!");
	    								System.out.println("In this case uncertainties are not taken into account.");
	    								System.out.println("Execution continues but be aware of that!");
	    							}
	    							
	    							
	    							
	    						} // end if mfd is GR
	    						else{
	    							System.out.println("bGRRelative rule is supported only for GR mfd!");
	    	    					System.out.println("Please correct your input!");
	    	    					System.out.println("Execution stopped!");
	    	    					System.exit(0);
	    						} // end if not GR
	    						
	    						mfdIndex = mfdIndex + 1;
	    					} // end loop over mfds
	    					
	    					// replace the old area source with the new area source
	    					srcList.set(sourceIndex, areaSrc);
	    					
	    				} // end if area source
	    				else{
	    					System.out.println("Source "+src.getClass().getName()+" not supported!");
	    					System.out.println("Please correct your input!");
	    					System.out.println("Execution stopped!");
	    					System.exit(0);
	    				} // end if not area source
	    			} // end if uncertainty on GR b value
	    			else{
	    				System.out.println("Rule: "+branch.getRule().getRuleName().toString()+" not supported!");
						System.out.println("Please correct your input!");
						System.out.println("Execution stopped!");
						System.exit(0);
	    			}// end if not a recognized rule
					
				}// end if rule is defined
				else{
					System.out.println("No rule is defined at branching level: "+i);
					System.out.println("Please correct your input!");
					System.out.println("Execution stopped!");
					System.exit(0);
				}
				// end if no rule is defined
				
			} // end loop over branching levels
			
			sourceIndex = sourceIndex + 1;
		} // end loop over sources
		
//		System.out.println("Sources after sampling");
//		for(int is=0;is<srcList.size();is++){
//			GEMAreaSourceData src = (GEMAreaSourceData) srcList.get(is);
//			System.out.println("Name: "+srcList.get(is).getName()+", total moment rate: "+src.getMagfreqDistFocMech().getFirstMagFreqDist().getTotalMomentRate());
//		}
		
		// instantiate ERF
		erf = new GEM1ERF(srcList);
		
		// set ERF parameters
		
		// set time span
		TimeSpan timeSpan = new TimeSpan(TimeSpan.NONE,TimeSpan.YEARS);
		timeSpan.setDuration(calcConfig.getInvestigationTime());
		erf.setTimeSpan(timeSpan);
		
		// set inclusion of area sources in the calculation
		erf.setParameter(GEM1ERF.INCLUDE_AREA_SRC_PARAM_NAME, calcConfig.getIncludeAreaSource());
		// set rupture type
		erf.setParameter(GEM1ERF.AREA_SRC_RUP_TYPE_NAME, calcConfig.getAreaSourceRuptureModel());
		// set area discretization
		erf.setParameter(GEM1ERF.AREA_SRC_DISCR_PARAM_NAME, calcConfig.getAreaSourceDiscretization());
		// set mag-scaling relationship
		erf.setParameter(GEM1ERF.AREA_SRC_MAG_SCALING_REL_PARAM_NAME, calcConfig.getAreaSourceMagAreaRel());
		
		// update
		erf.updateForecast();
		
		return erf;
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

}
