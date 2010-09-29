package org.opensha.sha.calc.groundMotionField;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;

import org.opensha.commons.geo.Location;
import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.gem.GEM1.commons.IMLLis;

public class MultiScenarioShakeMap {

	private ArrayList<Double> xval; // X values 
	private ArrayList<Double> yval; // Y values
	private Double[][] zval; // Arrax of shaking values - 1st index node - 2nd index map
	private int numSH; // Number of seismic histories 
	private ArrayList<Double> periodList;
	private boolean D = false; 
	
	/**
	 * Constructor
	 * 
	 * @param nCols	Number of columns (i.e. number of nodes composing the scenario shake maps)
	 * @param nMaps	Number of scenario shake maps to be stored
	 * @param numSH Number of 
	 * @param perList List of the GMPE period values (used only if the mssm contains several 
	 * 		Sa(T) shakemaps of the same event)      
	 */
	public MultiScenarioShakeMap(int nCols, int nMaps, int numSH, ArrayList<Double> perList) {
		this.xval = new ArrayList<Double>();
		this.yval = new ArrayList<Double>();
		this.zval = new Double[nCols][nMaps];
		this.numSH = numSH;
		this.periodList = perList;
	}
	
	/**
	 * 
	 * @return
	 */
	public ArrayList<Double> getPeriodList() {
		return periodList;
	}

	/**
	 * 
	 * @param period
	 */
	public void setPeriodList(ArrayList<Double> period) {
		this.periodList = period;
	}

	/**
	 * Returns a list of X coordinates of the nodes in the Multiscenario shake map
	 * @return
	 */
	public ArrayList<Double> getX() {
		return this.xval;
	}
	
	/**
	 *  Returns a list of Y coordinates of the nodes in the Multiscenario shake map
	 * @return
	 */
	public ArrayList<Double> getY() {
		return this.yval;
	}
	
	/**
	 * This method update the MultiScenarioShakeMap container. In case of a MultiScenarioShakeMap
	 * used to store the ScenarioShakeMaps referring to a single event and computed considering 
	 * distinct periods the index indicate the period (in increasing order). 
	 * 
	 * @param idx Index of the layer to update 
	 * @param zzz Array List with the Z values of a scenario shake map to include in the 'idx' 
	 * 		layer
	 */
	public void setScenarioShakeMap(int idx, ArrayList<Double> zzz){
		Iterator<Double> iter = zzz.iterator();
		int cnt = 0; 
		while (iter.hasNext()) {
			this.zval[cnt][idx] = iter.next();
			cnt++;
		}
	}
	
	/**
	 * Set the list of X values (Longitudes)??????
	 * 
	 * @param xval
	 */
	public void set_Xlist(ArrayList<Double> xval){
		this.xval = xval;
	}
	
	/**
	 * Set the list of Y values (Longitudes)???????
	 * 
	 * @param yval
	 */
	public void set_Ylist(ArrayList<Double> yval){
		this.yval = yval;
	}
	
	/**
	 * Provides the list of intensity measure values computed at the node with index idx.
	 *  
	 * @param idx
	 * @return
	 */
	public ArrayList<Double> getListAtNode(int idx){
		
		// Create a new array list containing the updated list of 
		// Z values
		ArrayList<Double> tmp = new ArrayList<Double>();
		for (int i=0; i<this.zval[0].length; i++){
			tmp.add(this.zval[idx][i]);
		}
		
		// Return tmp
		return tmp;
	}
	
	/**
	 * This method returns an ArrayList of values representing the scenario shake map with index idx.
	 * 
	 * @param idx
	 * @return
	 */
	public ArrayList<Double> getScenarioShakeMap(int idx){
		ArrayList<Double> out = new ArrayList<Double>();
		for (int i = 0; i < this.xval.size(); i++){
			out.add(this.zval[i][idx]);
		}
		return out;
	}
	
	/**
	 * Calculates a hazard map on each node of the multiscenario grid
	 * 
	 * @param iml								List of intensity measure levels
	 */
	@Deprecated
	public ArrayList<Double> computeHazardMap(ArbitrarilyDiscretizedFunc iml, double pex) {

		// 
		System.out.println("This multi-scenario shake map contains "+this.zval.length+" shake maps");
		
		// Create a collector for the computed list of values 
		ArrayList<Double> imValues = new ArrayList<Double>();
		
		// Cycle between the grid nodes and compute the hazard curves
		for (int i=0; i<this.xval.size(); i++){
			
			int node = 5;
			if (i == node) System.out.println("Site:"+this.xval.get(i)+" "+this.yval.get(i));
			
			// Info
			if ((Math.abs(Math.round(i/50.0)*50.0-i))<1.0e-3) System.out.printf("Node %5d of %5d \n",i,this.xval.size());
			
			// Create an arbitrarily discretized function 
			// ArbitrarilyDiscretizedFunc disfun = iml.deepClone();
	
			// Get the intensity measure values at the node
			ArrayList<Double> res = new ArrayList<Double>();
			
			for (int j=0; j<this.zval[0].length; j++){
				res.add(this.zval[i][j]);
			}
			
			// Reorder the values in ascending order
			Collections.sort(res);
			
			// Results iterator
			Iterator<Double> iter = res.iterator();
			
			// Number of ground motion values computed at the site 
			int nel = res.size();
			
			// Fin min and max values of GM 
			double gmMin = Collections.min(res);
			double gmMax = Collections.max(res);
			IMLLis imll = new IMLLis(gmMin,gmMax,40,"n");
			imll.expX_Values();
			ArbitrarilyDiscretizedFunc disfun = imll.getArbDisFun();
			
			// Compute the probability of exceedance for the values of GM contained in the Arbitrarily 
			// discretized function previously defined 
			if (D) System.out.println("");
			for (int j=0; j<disfun.getNum(); j++){	
				
				// Set the counter
				int cnt = 0;
				
				// Instantiate the iterator
				double gmThreshold = disfun.getX(j);
				iter = res.iterator();
				double gm = iter.next(); if (gm < gmThreshold) cnt++;
				
				// Find the number of non-exceedances
				while (iter.hasNext() && gm < gmThreshold) {
					gm = iter.next();
					cnt++;
				}

				// Compute the probability of exceedance
				double prbPoi = 1.0;
				if (cnt < nel) {	
					double argA = Double.parseDouble(Integer.toString(cnt));
					double argB = Double.parseDouble(Integer.toString(nel));
					double argC = Double.parseDouble(Integer.toString(this.numSH));
					prbPoi = 1.0 - Math.exp((argA-argB)/argC); 
					if (D) System.out.printf("A: %6.1f B: %6.1f C: %6.1f prb: %8.6f\n",argA,argB,argC,prbPoi);
				} else {
					prbPoi = 0.0;
				}
				
				// Update the arbitrarily discretized function
				disfun.set(j,prbPoi);
				
				// 
				//if (D) System.out.printf("%8.5f %8.5f %d \n",disfun.get(j).getX(),disfun.get(j).getY(),cnt);
				
				// Writes the hazard curve
				if (i == node){
					System.out.printf("%8.5f %8.5f %5d %5d\n",disfun.get(j).getX(),disfun.get(j).getY(),cnt,nel,this.numSH);
				}
				
			}
		
			// Compute the ground motion with a fixed probability of exceedance
			double val = 0.0;
			if ( pex < disfun.getY(disfun.getNum()-1) ){
				val = disfun.getMaxX();
			} else if ( pex > disfun.getY(0) ){
				val = disfun.getX(0);
			} else {
				val = disfun.getFirstInterpolatedX(pex);
			}
			
			// Updates the collector 
			imValues.add(val);
			if (D) System.out.println("-- "+val+" max gm:"+Collections.max(res));

		}
		
		//
		return imValues;
	}
	
	/**
	 * Calculates the hazard curves on each node of the multiscenario grid
	 * 
	 * @param iml List of intensity measure levels
	 */
	@Deprecated
	public ArrayList<ArbitrarilyDiscretizedFunc> computeHazardCurves(ArbitrarilyDiscretizedFunc iml) {
		
		System.out.println("This multiscenarioshakemap contains "+this.zval.length+" shake maps");
		
		// Get the intensity measure values at the node
		ArrayList<ArbitrarilyDiscretizedFunc> outCurves = new ArrayList<ArbitrarilyDiscretizedFunc>();
		
		// Cycle between the grid nodes and compute the hazard curves
		for (int i=0; i<this.xval.size(); i++){
			
			// Info
			if ((Math.abs(Math.round(i/50.0)*50.0-i))<1.0e-3) System.out.printf("Node %5d of %5d \n",i,this.xval.size());
			
			// Create an arbitrarily discretized function 
			ArbitrarilyDiscretizedFunc disfun = iml.deepClone();
			
			// Get the intensity measure values at the node
			ArrayList<Double> res = new ArrayList<Double>();
			
			for (int j=0; j<this.zval[0].length; j++){
				res.add(this.zval[i][j]);
			}
			
			// Reorder the values in ascending order
			Collections.sort(res);
	
			// Results iterator
			Iterator<Double> iter = res.iterator();
			
			// Number of ground motion values computed at the site 
			int nel = res.size();
			
			// Compute the probability of exceedance for the values of GM contained in the Arbitrarily 
			// discretized function previously defined 
			for (int j=0; j<disfun.getNum(); j++){	
				
				// Set the counter
				int cnt = 0;
				
				// Instantiate the iterator
				iter = res.iterator();
				double gm = iter.next(); if (gm < disfun.getX(j)) cnt++;
				
				// Find the number of non-exceedances
				double gmThreshold = disfun.getX(j);
				while (iter.hasNext() && gm < gmThreshold) {
					//System.out.println(gm+"< "+gmThreshold);
					gm = iter.next();
					cnt++;
				}

				// Compute the probability of exceedance
				double prbPoi = 1.0;
				if (cnt < nel) {	
					double argA = Double.parseDouble(Integer.toString(cnt));
					double argB = Double.parseDouble(Integer.toString(nel));
					double argC = Double.parseDouble(Integer.toString(this.numSH));
					prbPoi = 1.0 - Math.exp((argA-argB)/argC); 
				} else {
					prbPoi = 0.0;
				}
				
				// Update the arbitrarily discretized function
				disfun.set(j,prbPoi);
			}
			
			// Update the hazard curves collector
			outCurves.add(disfun);
			
		}
		return outCurves;
	}
	
	/**
	 * Creates an ASCII input file with the Scenario Shake Map. The format of the file is compatible
	 * with EQRM.
	 * 
	 * @param outDir 							Output directory
	 * @param fileName							File name 
	 * @throws IOException 
	 */
	public void writeEQRMfile(String outDir, String fileName) throws IOException {
		
		// Number of times a line must be repeated 
		int lineRep = 8;
		
		// Open buffer
		String filename = outDir+fileName;
		
		//System.out.println(filename);
		
		// Create the buffer writer
		BufferedWriter out = new BufferedWriter(new FileWriter(filename));
		
		// Write the file header 
		out.write(String.format("%%\n%% haz\n"));
	
		// Write the period header
		for (int i=0; i<this.periodList.size(); i++) {
			out.write(String.format("%.3f",this.periodList.get(i)));
			if (i< this.periodList.size()-1) out.write(String.format(" "));
		}
		out.write(String.format("\n"));
		
		// Write data
		for (int i=0; i<xval.size(); i++){
			for (int k=0;k<lineRep; k++){
				for (int j=0; j<this.zval[0].length; j++){
					out.write(String.format("%.5f",zval[i][j]));
					if (j < this.zval[0].length-1) out.write(String.format(" "));
				}
				out.write(String.format("\n"));
			}
		}
		
		// Close buffer
		out.close();	
	}
	
	/**
	 * Return the index of the nearest node given values of longitude and latitude.
	 * @param lon
	 * @param lat
	 * @return
	 */
	public int getNearestNodeId(double lon, double lat){
		double mindst = 1e10;
		double tmpdst = 0.0;
		int idx = -1;
		for (int i = 0; i < this.xval.size(); i++){
			tmpdst = Math.pow((lon-this.xval.get(i)),2.0) + Math.pow((lat-this.yval.get(i)),2.0);
			if (tmpdst < mindst) {
				mindst = tmpdst;
				idx = i;
			}
		}
		return idx;
	}
	
	/**
	 * 
	 * @param idx
	 * @return
	 */
	public Location getLocation(int idx){
		//System.out.println(this.yval.get(idx)+" "+this.xval.get(idx));
		return new Location(this.yval.get(idx),this.xval.get(idx));
	}
	
	/**
	 * This method compares the hazard curves obtained for selected nodes of the shakemaps to the
	 * hazard curves computed using the classical methodology.
	 * 
	 * WARNING: for the time being the time span used to calculate the probability of exceedance 
	 * 			is hard coded to 50 years.
	 * 
	 * @param i
	 * @param adf
	 * @param time
	 */
	public ArbitrarilyDiscretizedFunc getHazardCurve(int i, ArbitrarilyDiscretizedFunc adf, double historyDuration){
		
		System.out.printf("Node %d lon: %7.3f lat: %7.3f \n",i, this.xval.get(i),this.yval.get(i));
		System.out.printf("Number of GM values: %d \n",this.getListAtNode(i).size());
		
		// Get the list of IM values computed at site 'i' in a time period 'historyDuration'
		ArrayList<Double> val = this.getListAtNode(i);
		
		// Sort the list in ascending order
		Collections.sort(val);
		
		// Create and populate the new arbitrarily discretized function
		ArbitrarilyDiscretizedFunc xxx = new ArbitrarilyDiscretizedFunc();
		for (int j=0; j<val.size(); j++){
			xxx.set(Math.log(val.get(j)),(double) val.size()-j);
		}

		// Compute for each IML the number of exceedances and the probability of 
		// exceedance in 50 years
		double prb, nex;
		System.out.println("time "+historyDuration);
		for (int j=0; j<adf.getNum(); j++){
			double y = adf.getX(j);
			if (y>xxx.getMinX() && y<xxx.getMaxX()) {
				nex = xxx.getInterpolatedY(y);
				prb = 1.0-Math.exp(-nex/historyDuration*50.0);
				adf.set(y,prb);
			} else if (y<xxx.getMinX()) {
				nex = val.size();
				prb = 1.0-Math.exp(-nex/historyDuration*50.0);
				adf.set(y,prb);
			} else {
				nex = 0.0;
				adf.set(y,0.0);
			}
			System.out.printf("%7.3f %7.3f %7.3f\n",Math.exp(adf.getX(j)),nex,adf.getY(j));
		}
		return adf;
	}
	
	/**
	 * 
	 * @param outdir
	 * @throws IOException  
	 */
	public void createASCIIShakeMaps(String outdir) throws IOException {
		for (int i=0; i<this.zval[0].length; i++){
			String outFile = String.format("shkmap%04d.dat",i);
			System.out.println("writing to file: "+outFile);
			BufferedWriter outBuf = new BufferedWriter(new FileWriter(outdir+outFile));
			for (int j=0; j<this.zval.length; j++){
				outBuf.write(String.format("%+7.4f %+6.4f %6.4e\n",
						this.xval.get(j), 
						this.yval.get(j),
						this.zval[j][i]
						));
			}
			outBuf.close();
		}
	}
	
}
