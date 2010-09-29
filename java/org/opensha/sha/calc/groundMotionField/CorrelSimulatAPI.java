package org.opensha.sha.calc.groundMotionField;

import Jama.Matrix;

public interface CorrelSimulatAPI {

	/**
	 * 
	 * @return
	 */
	public Matrix getCholeskyLowTriangMtx();
	
	/**
	 * 
	 * @return
	 */
	public double[][] getGaussRndVector();

}
