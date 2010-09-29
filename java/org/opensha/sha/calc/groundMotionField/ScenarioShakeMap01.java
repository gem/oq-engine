package org.opensha.sha.calc.groundMotionField;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;

import org.opensha.commons.data.ArbDiscretizedXYZ_DataSet;
import org.opensha.commons.data.Site;
import org.opensha.commons.data.XYZ_DataSetAPI;
import org.opensha.commons.exceptions.ParameterException;
import org.opensha.sha.earthquake.EqkRupture;
import org.opensha.sha.imr.AttenuationRelationship;
import org.opensha.sha.imr.param.OtherParams.StdDevTypeParam;

import Jama.Matrix;

/**
 * 
 * 
 * @author marcop
 *
 */
public class ScenarioShakeMap01 {

	private ArbDiscretizedXYZ_DataSet dats; 
	protected static boolean D = false; 
	private double iEeps = 0.0;
	private boolean rndIeEps = true;
	
	public double getiEeps() {
		return iEeps;
	}

	public void setiEeps(double iEeps) {
		this.iEeps = iEeps;
	}

	public boolean isRndIeEps() {
		return rndIeEps;
	}

	public void setRndIeEps(boolean rndIeEps) {
		this.rndIeEps = rndIeEps;
	}

	/**
	 * Basic constructor
	 * 
	 */
	public ScenarioShakeMap01(){
		this.dats = new ArbDiscretizedXYZ_DataSet();
	}
	
	/**
	 * This constructor creates a scenario shake map starting
	 * from the content of an arbitrarily discretized XYZ data set
	 * 
	 * @param arbds							Arbitrarily discretized XYZ data set
	 */
	public ScenarioShakeMap01(ArbDiscretizedXYZ_DataSet arbds){
		this.dats = arbds;
	}

	/**
	 * This method returns the Array list of Z values (i.e. shaking values)
	 * contained in the shake map
	 * 
	 * @return 								Array list of ground motion parameters
	 */
	public ArrayList<Double> get_array_Z(){
		return this.dats.getZ_DataSet();
	}
	
	/**
	 * This method returns the Array list of X values (i.e. shaking values)
	 * contained in the shake map
	 * 
	 * @return 								Array list of ground motion parameters
	 */
	public ArrayList<Double> get_array_X(){
		return this.dats.getX_DataSet();
	}
	
	/**
	 * This method returns the Array list of Y values (i.e. shaking values)
	 * contained in the shake map
	 * 
	 * @return 								Array list of ground motion parameters
	 */
	public ArrayList<Double> get_array_Y(){
		return this.dats.getY_DataSet();
	}
	
	/**
	 * Calculate the scenario shake map
	 * 
	 * @param imr							Intensity measure relationship 
	 * @param rup							Rupture
	 * @param sites							Sites where to calculate the Scenario shake map
	 * @return gmDeltaInter					Inter-event deviation in
	 * @throws ParameterException			
	 */
	public void calculateScenarioShakeMap(AttenuationRelationship imr, EqkRupture rup, 
			ArrayList<Site> sites, boolean spatCorr) 
	throws ParameterException
	{
		
		// Create a scenario shake maps calculator
		ScenarioShakeMapCalculator ssmc = new ScenarioShakeMapCalculator();
	
		// Set the standard deviation deviation parameter types: if spatial correlation is computed 
		// the standard deviation used to generate ground motion values is the inter-event sigma
		// otherwise we use the total sigma 
		StdDevTypeParam stdDevParam = (StdDevTypeParam)imr.getParameter(StdDevTypeParam.NAME);
		if (spatCorr){
			stdDevParam.setValue(StdDevTypeParam.STD_DEV_TYPE_INTER);
		} else {
			stdDevParam.setValue(StdDevTypeParam.STD_DEV_TYPE_TOTAL);
		}
		double sigmaINTER = imr.getStdDev();
			
		// Create and populate arrays with IMRs and weights (the getScenarioShakeMapData method 
		// asks for these two objects) 
		ArrayList imrArr = new ArrayList();
		ArrayList<Double> imrWei = new ArrayList<Double>();
		imrArr.add(imr); imrWei.add(1.0);
		
		// Get the scenario (we calculate the median values):
	    // 1 - ArrayList selectedAttenRels
		// 2 - ArrayList attenRelWts,
		// 3 - SitesInGriddedRectangularRegion griddedRegionSites
		// 4 - EqkRupture rupture,
		// 5 - boolean isProbAtIML
		// 6 - double value - This should be random!!!
		XYZ_DataSetAPI xyz = ssmc.getScenarioShakeMapData(imrArr,imrWei,sites,rup,false,0.5);
		this.dats = (ArbDiscretizedXYZ_DataSet) xyz;
		
		// Create the final shake map taking into account GM inter-event variability
		RandomGaussGenerator rndGen = new RandomGaussGenerator();
		if (rndIeEps) {
			iEeps = rndGen.boxMullerTransform();
		} 
		double gmDeltaInter = sigmaINTER * iEeps;
		
		// Add the inter-event variability
		ArrayList<Double> zzz = new ArrayList<Double>();
		for (int j=0;j<xyz.getZ_DataSet().size();j++){
			double val = ((xyz.getZ_DataSet().get(j))).doubleValue();
			double tempVal = Math.exp(val+gmDeltaInter);
			zzz.add(j,new Double(tempVal));
		}
		
		// Update the scenario shake map object 
		this.dats.setXYZ_DataSet(xyz.getX_DataSet(), xyz.getY_DataSet(), zzz);
	}
	
	/**
	 * Generate the spatial correlation to be added to the scenario shake map
	 * 
	 * @param imr								Attenuation relationship	
 	 *
	 */
	public ScenarioShakeMap01 generateSpatCorrMtx(Matrix triMtx,double[][] rndGauss, double sigma){
		
		// Number of points
		int npnt = this.dats.getX_DataSet().size();
		
		// X and Y values of the nodes where we calculate the ground motion values 
		ArrayList<Double> xList = this.dats.getX_DataSet();
		ArrayList<Double> yList = this.dats.getY_DataSet();
		
		// Multiply the vector of standard gaussian values by the intra event strandard deviation
		for (int i=0; i<rndGauss.length; i++){
			rndGauss[i][0] = rndGauss[i][0]*sigma;
		}
	
		// Complete the multiplication 'triMtx*gaussVal' 
		Matrix prd = triMtx.times(new Matrix(rndGauss));
		
		// Find min and max of the final vector
		double tmpMin =  1e10;
		double tmpMax = -1e10;
		for (int i=0; i<prd.getRowDimension(); i++){
			if (prd.get(i,0)>tmpMax) tmpMax = prd.get(i,0);
			if (prd.get(i,0)<tmpMin) tmpMin = prd.get(i,0);
		}
		//System.out.println("Final matrix min: "+tmpMin+" max: "+tmpMax);
		
		// Final matrix
		double[][] res = prd.getArray();
		
		// Return the matrix with intra-event variability
		ArrayList<Double> xout = new ArrayList<Double>();
		ArrayList<Double> yout = new ArrayList<Double>();
		ArrayList<Double> zout = new ArrayList<Double>();
		
		// Update the array list to be used in the generation of the scenario shake map containing 
		// the spatial correlation of ground motion
		for (int i=0; i<npnt; i++){
			xout.add(xList.get(i));
			yout.add(yList.get(i));
			zout.add(res[i][0]);
		}
		
		// Create the output shake map containing the intra event variability
		ScenarioShakeMap01 shkIEV = new ScenarioShakeMap01(new ArbDiscretizedXYZ_DataSet(xout,yout,
				zout));
		return shkIEV;
	}
	
	/**
	 * This method adds to a scenario shake map the spatial correlation
	 * component.
	 * 
	 * @param shkSC				Scenario shake maps object containing  
	 */
	public void addSpatialCorrelation(ScenarioShakeMap01 shkSC){
		
		// Input uncorrelated ground motion values  
		ArrayList<Double> zVal = this.dats.getZ_DataSet();
		ArrayList<Double> zsc = shkSC.get_array_Z();
		
		// Number of points 
		int numDat = zVal.size();
		
		// Instantiate output 
		ArrayList<Double> zzz = new ArrayList<Double>();
		ArrayList<Double> crr = new ArrayList<Double>();

		// Add the spatial correlation to the computed shake map
		for (int j=0;j<numDat;j++){
			
			// Add inter-event spatial correlation
			double val = Math.exp(Math.log(zVal.get(j)) + zsc.get(j)); 
			zzz.add(j, new Double(val));
		}
		
		// Update the scenario shake map 
		this.dats.setXYZ_DataSet(this.dats.getX_DataSet(), this.dats.getY_DataSet(), zzz);
	}
	
	/**
	 * 
	 * @return					Returns the arbitrarily discretized XYZ
	 */
	public ArbDiscretizedXYZ_DataSet getDats() {
		return dats;
	}

	/**
	 * 
	 * @param dats				Set the arbitrarily discretized XYZ in the shake map
	 * 							object
	 */
	public void setDats(ArbDiscretizedXYZ_DataSet dats) {
		this.dats = dats;
	}

	/**
	 * This method creates an output ASCII file with the information describing
	 * a scenario shake map
	 * 
	 * @throws IOException 
	 *  
	 */
	public void writeASCIIFile(String outDir, int idxsh, int idx, EqkRupture rup) throws IOException{
		
		// Open buffer
		String filename = outDir+String.format("shkmap_%05d_%05d_m%05.2f.dat",idxsh,idx,rup.getMag());
		//System.out.println("Creating file "+filename);
		BufferedWriter out = new BufferedWriter(new FileWriter(filename));
		
		// Create array lists 
		ArrayList<Double> xval = this.dats.getX_DataSet();
		ArrayList<Double> yval = this.dats.getY_DataSet();
		ArrayList<Double> zval = this.dats.getZ_DataSet();
		
		// Write data
		for (int i=0; i<xval.size(); i++){
			out.write(String.format("%8.5f %8.5f %8.5f\n",xval.get(i),yval.get(i),zval.get(i)));
		}
		
		// Close buffer
		out.close();
	}
	
}
