package org.opensha.sha.calc.groundMotionField;

import Jama.Matrix;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.ListIterator;

import org.opensha.commons.data.Site;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.commons.param.DependentParameterAPI;
import org.opensha.commons.param.DoubleDiscreteParameter;
import org.opensha.commons.param.ParameterAPI;
import org.opensha.commons.param.event.ParameterChangeWarningEvent;
import org.opensha.commons.param.event.ParameterChangeWarningListener;
import org.opensha.gem.GEM1.commons.UnoptimizedDeepCopy;
import org.opensha.sha.calc.stochasticEventSet.SeismHist;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.param.IntensityMeasureParams.PGA_Param;
import org.opensha.sha.imr.param.IntensityMeasureParams.PeriodParam;
import org.opensha.sha.imr.param.IntensityMeasureParams.SA_Param;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;

/**
 * This class generates a set of multi-scenario shake maps. It contains two MultiScenario Shake map 
 * objects. The first include the set of shake maps representative of the ground motion  
 *
 * @author marcop
 *
 */
public class GemMultiSSMCalculator implements Runnable {
	
	private Thread threads[];
	private int startLoop, endLoop, curLoop, numThreads;
	private MultiScenarioShakeMap mssm; // This a container for the shake maps relative to one event
	private MultiScenarioShakeMap mssmPGA; // This is a container for the shake maps for different events
	private AttenuationRelationship imr; 
	private SeismHist sh; 
	private ArrayList<Site> sites; 
	private ArrayList<Double> per;
	private boolean intpercorFull = true;
	private boolean spatCorr = true;
	private String outDir; 
	
	/**
	 * 
	 */
	private class mapsRange {
		public int start, end;
	}
	
	/**
	 * This is a multi-thread based multi-scenario shake map calculator. 
	 * @param nproc	 	Number of processors
	 * @param imr 		Intensity measure relationship to be used for scenario generation 
	 * @param shHist 	Array of seismicity histories. Each seismicity history contains a list of 
	 * 					ruptures  
	 * @param sites		List of sites where to calculate the ground motion	
	 */
	public GemMultiSSMCalculator (int nproc,AttenuationRelationship imr,ArrayList<SeismHist> shHist,
			ArrayList<Site> sites, String outDir) {
		
		this.numThreads = nproc;
		this.sites = sites;
		this.imr = imr;
		this.sh = new SeismHist();
		this.threads = new Thread[nproc];
		this.startLoop = this.curLoop = 0;
		this.outDir = outDir;

		// -----------------------------------------------------------------------------------------
		//                         Create a single seismicity history by merging all the computed sh  
		for (int i=0; i<shHist.size(); i++){
			for (int j=0; j<shHist.get(i).getNumRuptures();j++){
			//for (int j=0; j<3;j++){
				this.sh.addEvent(shHist.get(i).getTimeOcc().get(j),shHist.get(i).getRupture(j));
			}
		}
		System.out.println("Num ruptures: "+sh.getRuptures().size());
		this.endLoop = sh.getRuptures().size();	
		
		// 
		ArrayList<Double> x = new ArrayList<Double>();
		ArrayList<Double> y = new ArrayList<Double>();
		for (int i = 0; i<sites.size(); i++){
			x.add(sites.get(i).getLocation().getLongitude());
			y.add(sites.get(i).getLocation().getLatitude());
		}
		
		// -----------------------------------------------------------------------------------------
		//                                    Get the list of periods available for the selected IMR
		this.per = new ArrayList<Double>();
		ListIterator<ParameterAPI<?>> it = imr.getSupportedIntensityMeasuresIterator();
	    while(it.hasNext()){
	    	DependentParameterAPI tempParam = (DependentParameterAPI)it.next();
	    	if (tempParam.getName().equalsIgnoreCase(SA_Param.NAME)){
	    		ListIterator it1 = tempParam.getIndependentParametersIterator();
	    		while(it1.hasNext()){
	    			ParameterAPI independentParam = (ParameterAPI)it1.next();
	    			if (independentParam.getName().equalsIgnoreCase(PeriodParam.NAME)){
	    				ArrayList<Double> saPeriodVector = ((DoubleDiscreteParameter)independentParam).getAllowedDoubles();
	    				for (int h=0; h<saPeriodVector.size(); h++){
	    					if (h == 0 && saPeriodVector.get(h)>0.0){
	    						per.add(0.0);
	    					}
	    					this.per.add(saPeriodVector.get(h));
	    				}
	    			}
	    		}
	    	}
	    }
	    
	    // -------------------------------------------------- ATTENTION!!!!!!!!!!!!!!!!!!
	    this.per = new ArrayList<Double>();
	    this.per.add(0.0);
	    // -------------------------------------------------- ATTENTION!!!!!!!!!!!!!!!!!!

	    // -----------------------------------------------------------------------------------------
		//                                          Instantiate the Multi Scenario Shake Map objects
		// 1 - Number of sites
		// 2 - Number of scenario shake maps
		// 3 - TODO revise this parameter
		// 4 - List of GMPE periods 
	    mssm 		= new MultiScenarioShakeMap(sites.size(),per.size(),1,per);
		mssmPGA 	= new MultiScenarioShakeMap(sites.size(),sh.getNumRuptures(),1,null);
		mssm.set_Xlist(x);
		mssm.set_Ylist(y);
		mssmPGA.set_Xlist(x);
		mssmPGA.set_Ylist(y);
	}
	
	/**
	 * 
	 * @return
	 */
	private synchronized mapsRange loopGetRange(){
		if (curLoop >= endLoop) return null;
		// 
		mapsRange r = new mapsRange();	
		r.start = curLoop;
		// Distribute hazard calculation to the different threads
		curLoop += (endLoop-startLoop)/numThreads+1;		
		r.end = (curLoop<endLoop)?curLoop:endLoop;		
		return r;
	}
	
	/**
	 * 
	 * @param start
	 * @param end
	 * @throws IOException
	 * @throws ParameterException
	 * @throws RegionConstraintException
	 */
	private void loopDoRange (int start, int end) throws IOException, ParameterException {
		
		MultiScenarioShakeMap xxx;
		double iEeps;
		double[][] rndVec = null;
		int cev = 0;
		int threadN = (start-startLoop)/(end-start);
		
		// Create local ScalarIntensityMeasureRelationshipAPI and ArrayList<Double> objects
		UnoptimizedDeepCopy udp = new UnoptimizedDeepCopy();
		AttenuationRelationship imrLoc = (AttenuationRelationship) UnoptimizedDeepCopy.copy(imr);
		ArrayList<Double> perLoc = (ArrayList<Double>) UnoptimizedDeepCopy.copy(per);
		ArrayList<Site> sitesLoc = (ArrayList<Site>) UnoptimizedDeepCopy.copy(sites);
		
		// Create a MultiScenarioShakemap object
		xxx = new MultiScenarioShakeMap(mssm.getX().size(),per.size(),1,per);
		xxx.set_Xlist(mssm.getX());
		xxx.set_Ylist(mssm.getY());
		
		// Open buffer
		String filename = outDir+"events_list_"+start+"_"+end+".txt";
		BufferedWriter outList = new BufferedWriter(new FileWriter(filename));

		// Loop over the assigned events
		for (int i=start; i<end; i+=1) {

			Iterator<Double> iterT = perLoc.iterator();
			int cnt = 0;
			boolean store = true;
			
			// Compute the shake maps for all the periods contained in the 'per' ArrayList
			while (iterT.hasNext() && store) {

				// Get period value
				double T = iterT.next();

				// Set the period for spectral acceleration calculation
				if (T>0) {
					imrLoc.setIntensityMeasure(SA_Param.NAME);
					imrLoc.getParameter(PeriodParam.NAME).setValue(T);
				} else {
					imrLoc.setIntensityMeasure(PGA_Param.NAME);
				}

				// Create scenario shake map  
				ScenarioShakeMap01 shkmap = new ScenarioShakeMap01();

				// Set the correlation between spectral periods. In case intpercorFull is 'true'
				// we assume that the motion at different periods is totally correlated. As a
				// consequence, we store the random intra-event epsilon and we use it to
				// generate the shake maps for periods greater than 0 (i.e. PGA).
				if (intpercorFull) {
					iEeps = 0.0;
					if (T > 1.e-8){
						shkmap.setRndIeEps(false);
						shkmap.setiEeps(iEeps);
					}
				} else {
					shkmap.setRndIeEps(true);	
				}	
				shkmap.calculateScenarioShakeMap(imrLoc,sh.getRupture(i),sitesLoc,spatCorr);

				// Storing the intra-event epsilon for successive calculations
				if (T < 1.e-8) iEeps = shkmap.getiEeps();

				// Calculate spatial correlation and add it to the shake map
				if (spatCorr){

					// Get intra-event correlation
					StdDevTypeParam stdDevParam = (StdDevTypeParam)imr.getParameter(
							StdDevTypeParam.NAME);
					stdDevParam.setValue(StdDevTypeParam.STD_DEV_TYPE_INTRA);
					double sigmaintra = imrLoc.getStdDev();

					// Create the spatial correlation simulator
					CorrelSimulSpat corSim = new CorrelSimulSpat(shkmap.getDats(),sigmaintra,T);

					// Calculate the lower triangular matrix
					Matrix lowTriMtx = corSim.getCholeskyLowTriangMtx();

					// Calculate the vector of standard gaussian values
					if (T < 1.e-8) {
						rndVec = corSim.getGaussRndVector();
					}

					// Calculate the spatial correlation shake map
					ScenarioShakeMap01 scMtx = shkmap.generateSpatCorrMtx(lowTriMtx, rndVec, 
							sigmaintra);

					// Add spatial correlation to the shake map
					shkmap.addSpatialCorrelation(scMtx);
				}

				if (cnt == 0){
					ArrayList<Double> vls = shkmap.get_array_Z();
					double vlsMax = -1e10; 
					double vlsTmp;
					for (int k=0; k < vls.size(); k++){
						vlsTmp = vls.get(k);
						if (vlsTmp > vlsMax) vlsMax = vlsTmp;
					}
					// If the threshold is very low w take all the shakemaps
					// if (vlsMax < 1e-5) store = false;
				}

				// Store the information relative to this layer
				//System.out.println("--"+Collections.max(shkmap.get_array_Z()));
				xxx.setScenarioShakeMap(cnt,shkmap.get_array_Z());
				cnt++;
			}

			// Create the multi-spectral scenario shake map for EQRM
			if (store) { 
				
				String fileName = String.format("marmara_hazard_ev%d.txt",i);
				xxx.writeEQRMfile(outDir,fileName);
								
				// Update the list 
				outList.write(String.format("%s,%.2f \n",fileName,sh.getRupture(i).getMag()));
				
				// Store the PGA Scenario Shake Map
				// TODO Note: this implementation assumes that the first shake map is the one 
				// containing the PGA shake map
				mssmPGA.setScenarioShakeMap(i,xxx.getScenarioShakeMap(0));
			}
			System.out.printf("thrd: %3d event: %-5d/%d \n",
					(start-startLoop)/(end-start),(i-start),(end-start));

		}	

		// Close buffer
		outList.close();
	}
	
	/**
	 * 
	 */
	public void run() {
		mapsRange range;
		while ( (range=loopGetRange())!=null){
			try {
				loopDoRange(range.start,range.end);
			} catch (ParameterException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			} catch (IOException e) {
				// TODO Auto-generated catch block
				e.printStackTrace();
			}
		}
	}
	
	/**
	 * This method launch the calculation an returns a MultiScenarioShakeMap object with all the PGA
	 * scenario shake maps generated
	 * 
	 * @return
	 */
	public MultiScenarioShakeMap getValues(){
		for(int i=0;i<numThreads;i++){
			threads[i] = new Thread(this);
			threads[i].start();
		}
		for(int i=0;i<numThreads;i++){
			try{
				threads[i].join();
			} catch (InterruptedException iex) {}
		}
		return mssmPGA;
	}
	
	/**
	 * 
	 * @param event
	 * @return
	 */
	private static ParameterChangeWarningListener ParameterChangeWarningListener (
			ParameterChangeWarningEvent event) {
		return null;
	}
	

}
