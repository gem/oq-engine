package org.opensha.sha.calc.groundMotionField;

import java.util.ArrayList;

import org.opensha.commons.data.ArbDiscretizedXYZ_DataSet;
import org.opensha.commons.geo.Location;
import org.opensha.commons.geo.LocationUtils;

import Jama.CholeskyDecomposition;
import Jama.Matrix;

public class CorrelSimulSpat implements CorrelSimulatAPI {

	// Covariance matrix 
	private double[][] covMtx;
	
	// Lower triangular matrix computed with Choleski decomposition
	private Matrix lowTriMtx; 
	
	// Vector of gaussian random variables
	private double[][] gaussRndVec; 
	
	// Intra-event sigma
	private double sigmaIntra;
	
	// Period
	private double period; 
	
	// Debug and checking flag
	private boolean D = false;
	
	/**
	 * 
	 */
	public CorrelSimulSpat(ArbDiscretizedXYZ_DataSet dats, double sigma, double T) {
		
		this.sigmaIntra = sigma;
		this.period = T;
		
		// Instantiate the covariance matrix of the residuals
		ArrayList<Double> xList = dats.getX_DataSet();
		ArrayList<Double> yList = dats.getY_DataSet();
		
		// Number of points
		int npnt = dats.getX_DataSet().size();
		
		// Instantiate the covariance matrix of residuals
		double[][] covMtx = new double[npnt][npnt];
		
		// Create the covariance matrix of the residuals
		double minCov =  1e10;
		double maxCov = -1e10;
		for (int i=0; i<npnt; i++){
			for (int j=i; j<npnt; j++ ){
				
				// Location 1
				Location loc1 = new Location(yList.get(i).doubleValue(),xList.get(i));
				Location loc2 = new Location(yList.get(j).doubleValue(),xList.get(j));
				
				// Compute distance between the two locations
//				double dist = RelativeLocation.getHorzDistance(loc1,loc2);
				double dist = LocationUtils.horzDistance(loc1,loc2);
				
				// >>> Compute spatial correlation <<< 
				
				// Using Crowley et al. (2008) - According to the authors (see page
				// 74) their equation 2.7 provides the correlation of the residuals.
				// Note that the residuals have mean = 0; thus the correlation and 
				// covariance between i,j are the same (see 
				// covMtx[i][j] = (1 - Math.pow((1-Math.exp(-Math.sqrt(0.6*dist))),2)) / sigma;
				
				// Using Jayaram and Baker (2009): Their formula (20) provides the 
				// correlation between normalized intra-residuals (that are zero-mean random
				// variables - see pag. 2 of Jayaram and Baker (2009)) 
				// According to Hsu (1997) - "Probability, random variables, & random 
				// processes" pag. 85:
				// Cov(X,Y) = Correlation(XY) - E(X)E(Y) 
				// in our case E(X) and E(Y) should be equal to 0. Thus (in this particular case):
				// Cov(X,Y) = Correlation(XY)
				double range;
				if (T<1.0){
					range = 8.5+17.2*T;
				} else {
					range = 22.0+3.7*T;
				}
				
				covMtx[i][j] = Math.exp(-3*dist/(range));
				// We now multiply the intraevent normalized residuals by the intraevent standard deviation 
				// in order to get the intraevent residuals (see Jayaram and Baker (2009) eq.(11))  
				covMtx[j][i] = covMtx[i][j] * sigma;
				
				// Checkings 
				if (covMtx[i][j] > maxCov) maxCov = covMtx[i][j];
				if (covMtx[i][j] < minCov) minCov = covMtx[i][j];
				
				// Writing info for debugging
				if (D)
					if (i == 3) System.out.printf(" %8.5f %8.5f %8.5f %8.5f dist: %8.3f cov: %8.4f\n",
						loc1.getLongitude(),loc1.getLatitude(),loc2.getLongitude(),loc2.getLatitude(),dist,covMtx[i][j]);
			}
		}
		
		// Store the correlation matrix
		this.covMtx = covMtx;
		//System.out.println("Correlation matrix: min="+minCov+" max="+maxCov);
		
		// Print info for debugging
		if (D) {
			System.out.println("Covariance matrix");
			for (int i=0; i<npnt; i++) System.out.printf("%9.6f ",xList.get(i)); System.out.println("");
			for (int i=0; i<npnt; i++){
				for (int j=0; j<npnt; j++ ){
					System.out.printf("%9.6f ",covMtx[i][j]);
				}
				System.out.printf("\n");
			}
		}
		
		// Now I follow the method described in :
		// 
		// Fang, J. and Tacher, L. (2003) " An efficient and accurate algorithm for generating 
		// spatially-correlated random fields". Commun. Numer. Meth. Engng., 19:801-808. 
		// (see page 804)
		// 
		// See also "Multivariate normal distribution" in Wikipedia
		//
		
		// Compute the Choleski decomposition of the covariance matrix
		Matrix mtx = new Matrix(covMtx);
		CholeskyDecomposition choDec = mtx.chol();
		
		// Get the lower triangular matrix
		this.lowTriMtx = choDec.getL();
		
		// Initialize the random gaussian vector
		initGaussRndVector();
	}
	
	/**
	 * 
	 * @param mtx								Lower triangular matrix 
	 */
	public void setGaussRndVector(Matrix mtx) {
		this.lowTriMtx = mtx;
	}
	
	/**
	 * This method creates a new standard gaussian random vector eventually to be used 
	 * for generating the final realization
	 *
	 */
	public void initGaussRndVector() {
		
		int npnt = this.covMtx.length;
		double[][] gaussVal = new double[npnt][1];
		
		// Generate one realization of a vector of uncorrelated standard gaussian variables.
		RandomGaussGenerator rndGen = new RandomGaussGenerator();
	
		// Generate random number
		for (int i=0; i< npnt; i++){	
			gaussVal[i][0] = rndGen.boxMullerTransform();
		}
		
		// Update the standard gaussian random vector
		this.gaussRndVec = gaussVal;
		
	}
	
	/**
	 * This method gives the the lower triangular matrix obtained by applying the Cholesky
	 * decomposition to the covariance matrix.
	 * 
	 * @return lowTriMtx						Lower triangular matrix from Cholesky decomposition
	 * 											of the covariance matrix
	 */
	public Matrix getCholeskyLowTriangMtx() {
		return this.lowTriMtx;
	}

	/**
	 * 
	 */
	public double[][] getGaussRndVector() {
		return this.gaussRndVec;
	}

}
