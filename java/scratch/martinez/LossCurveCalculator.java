package scratch.martinez;

import java.util.ArrayList;
import java.util.ListIterator;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;

import scratch.martinez.VulnerabilityModels.VulnerabilityModel;
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
			VulnerabilityModel curVulnModel) {
		
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

}
