package org.opensha.sra.calc;

import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.data.function.DiscretizedFuncAPI;

import org.opensha.sra.fragility.FragilityModel;
import org.opensha.sra.vulnerability.AbstractVulnerability;

import Jama.Matrix;

/**
 * <strong>Title</strong>: LossCurveCalculator<br />
 * <strong>Description</strong>: Computes a loss curve (in the form of an 
 * <code>ArbitrarilyDiscretizedFunc</code> by using the given hazFunc and 
 * vulnModel. A loss curve represents the expected loss incurred by a structure 
 * at predefined intensity measure levels (damage factors) given a particular
 * hazard forecast model.
 * 
 * @author <a href="mailto:emartinez@usgs.gov">Eric Martinez</code>
 *
 */
public class LossCurveCalculator {
   
	/**
	 * Creates a new Calculator
	 *
	 */
	public LossCurveCalculator() {
	
	}
	
	/**
	 * Generates a loss curve based on the given <code>hazFunc</code> and 
	 * <code>curVulnModel</code>.
	 * 
	 * @param hazFunc An <code>ArbitrarilyDiscretizedFunc</code> representing
	 * the hazard curve.
	 * @param curVulnModel The vulnerability model to use for calculation
	 * purposes.
	 * @return The loss curves associated with the given <code>hazFunc</code>
	 * and <code>curVulnModel</code>.
	 */
	public ArbitrarilyDiscretizedFunc getLossCurve(
			ArbitrarilyDiscretizedFunc hazFunc,
			AbstractVulnerability curVulnModel) {
		
		ArbitrarilyDiscretizedFunc lossCurve = new ArbitrarilyDiscretizedFunc();
		// Get the damage factors (these will be x values later)...
		double[] dfs = curVulnModel.getDEMDFVals();
		
		// Get the probabilities of exceedance (hazard curve)...
		ListIterator<Double> iter = hazFunc.getYValuesIterator();
		ArrayList<Double> pelist = new ArrayList<Double>();
		while(iter.hasNext())
			pelist.add((Double) iter.next());
		
		pelist = diffIt(pelist);
		
		Matrix PEMatrix = new Matrix(pelist.size(), 1);
		for(int i = 0; i < pelist.size(); ++i)
			PEMatrix.set(i, 0, pelist.get(i));
		
		// Get the DEM
		Matrix DEMMatrix = new Matrix(curVulnModel.getDEMMatrix());
		
		Matrix result = DEMMatrix.times(PEMatrix);
		
		for(int i = 0; i < dfs.length; ++i)
			lossCurve.set(dfs[i], result.get(i, 0));
		
		return lossCurve;
	}
	
	/**
	 * 
	 * @param hazFunc
	 * @param fragilityFunc
	 * @return
	 */
	public double getLossExceedance(ArbitrarilyDiscretizedFunc hazFunc,
			ArbitrarilyDiscretizedFunc fragilityFunc) {
		
		int numIMLs = fragilityFunc.getNum();
		
//		System.out.println("numIMLs: " + numIMLs);
		
		if (numIMLs != hazFunc.getNum())
			throw new IllegalArgumentException("X-Values must match for hazard curve and fragility curve.");
		
		Matrix hazMatrix = new Matrix(1, numIMLs);
		Matrix fragMatrix = new Matrix(numIMLs, 1);
		
		ArrayList<Double> hazFuncVals = new ArrayList<Double>();
		ListIterator<Double> iter = hazFunc.getYValuesIterator();
		while (iter.hasNext())
			hazFuncVals.add((Double) iter.next());
		hazFuncVals = diffIt(hazFuncVals);
		
		for (int i=0; i<numIMLs; i++) {
			hazMatrix.set(0, i, hazFuncVals.get(i));
			fragMatrix.set(i, 0, fragilityFunc.getY(i));
		}
		
		Matrix result = hazMatrix.times(fragMatrix);
		
//		System.out.println("rows: " + result.getRowDimension() + ", cols: " + result.getColumnDimension());
		
		return result.get(0, 0);
	}
	
	/**
	 * Differences the values stored in </code>vals</code> as follows:<br />
	 * <pre>
	 * 	rtn[i] = vals[i] - vals[i-1], for 1 < i < vals.length
	 * </pre><br />
	 * (That is if <code>vals</code> were an array...)
	 * @param vals The values to difference
	 * @return The differenced array.
	 */
	public static ArrayList<Double> diffIt(ArrayList<Double> vals) {
		ArrayList<Double> rtn = new ArrayList<Double>();
		int i = 1;
		for(i=1; i < vals.size(); ++i)
			rtn.add( Math.abs( vals.get(i) - vals.get(i-1) ) );
		rtn.add(vals.get(--i));
		return rtn;
	}
	
	public static void main(String args[]) {
		ArbitrarilyDiscretizedFunc hazFunc = new ArbitrarilyDiscretizedFunc();
		ArbitrarilyDiscretizedFunc fragilityFunc = new ArbitrarilyDiscretizedFunc();
		
		for (double x=0; x<3; x+=0.1) {
			hazFunc.set(x, Math.random());
			fragilityFunc.set(x, Math.random());
		}
		
		LossCurveCalculator calc = new LossCurveCalculator();
		calc.getLossExceedance(hazFunc, fragilityFunc);
	}

}
