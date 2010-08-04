package org.opensha.commons.geo;

import Jama.EigenvalueDecomposition;
import Jama.Matrix;

/**
 * Add comments here
 *
 *
 * @author Peter Powers
 * @version $Id:$
 */
public final class PlaneUtils {
    
	// TODO needs:
	//	-- conversion to use Location
	//	-- speed test to use apache.commons.math.Vector3d etc.
	
    // fixed unit normal vectors
	/** <b>x</b>-axis unit normal vector [1,0,0]*/ 
    public static final double[] VX_UNIT_NORMAL = { 1.0, 0.0, 0.0 };
	/** <b>y</b>-axis unit normal vector [0,1,0]*/ 
    public static final double[] VY_UNIT_NORMAL = { 0.0, 1.0, 0.0 };
	/** <b>z</b>-axis unit normal vector [0,0,1]*/ 
    public static final double[] VZ_UNIT_NORMAL = { 0.0, 0.0, 1.0 };

    // hidden constructor
    private PlaneUtils() {
    }
    
    
    /** Calculates a triangle centroid by averaging the x, y, and z values of
     * three vertices. Accepts a 2D double array of triangle vertices with the
     * form:<br/><br/>
     * <div align="center"><b><pre>
     * [ [ x1 y1 z1 ]
     *   [ x2 y2 z2 ]
     *   [ x3 y3 z3 ] ]</pre></b></div>
     * <br/>
     * and returns a 1D double array with the form:<br/><br/>
     * <div align="center"><b>| x y z |</b></div>
     * @param verticesIn 2D triangle vertex array.
     * @return double[x,y,z] centroid array.
     *    
     */    
    public static double[] getCentroid(double[][] verticesIn) {
        double centroid[] = new double[3];
        for (int i=0; i<3; i++) {
            centroid[i] = 0.0;
            for (int j=0 ; j<3; j++) {
                centroid[i] += verticesIn[j][i];
            }
            centroid[i] /= 3;
        }
        return centroid;
    }

    
    /** Same as <CODE>centroid()</CODE> except that the centroid is recast
     * as a <CODE>long[]</CODE>.
     * @param verticesIn 2D triangle vertex array.
     * @return double[x,y,z] centroid array.
     */    
    public static long[] getCentroidLong(double[][] verticesIn) {

        // get centroid based on float values
        double[] input = PlaneUtils.getCentroid(verticesIn);
        
        // recast float centroid as long centroid
        long[] centroid = new long[3];
        for (int i=0; i<3; i++) {
            //centroid[i] = (new Double(input[i])).longValue();
            centroid[i] = (long)input[i]; // alternate recast 
        }
        return centroid;
    }

    // doublecheck strike and dip at some point to make sure reference frame is correct (x is E-W)
    
    /** 
     * Calculates the strike and dip of a triangular surface as defined by its
     * vertices. Accepts a 2D double array of triangle vertices with the form:
     * <br/><br/>
     * <div align="center"><b><pre>
     * [ [ x1 y1 z1 ]
     *   [ x2 y2 z2 ]
     *   [ x3 y3 z3 ] ]</pre></b></div>
     * <br/>
     * Values returned follow the <I>right-hand-rule</I> (downdip direction is
     * always to the right of strike direction).<br/>
     * <br/>
     * <CODE>strikeAndDip</CODE> solves the classic <i>three-point-problem</i>
     * from structural geology using elementary vector math. The method first
     * uses the input vertices to define two lines (vectors <b>u</b>,<b>v</b>) 
     * that lie in the plane of interest. The cross product of <b>u</b> and 
     * <b>v</b> yields a third vector, <b>N</b>, that is normal to the plane of 
     * interest:<br/>
     * <br/>
     * <div align="center"><b>u</b> x <b>v</b> = <b>N</b></div>
     * <br/>
     * Since strike and dip are independent in space, the cross product of
     * a unit normal vector, <b>n</b> (0<b>i</b>,0<b>j</b>,1<b>k</b>), for a 
     * horizontal surface and <b>N</b> yields the horizontal strike vector of 
     * the plane of interest:<br/>
     * <br/>
     * <div align="center"><b>strike</b> = <b>n</b> x <b>N</b></div>
     * <br/>
     * Above, <b>N</b> is converted to positive-up if necessary so that a
     * right-hand-rule compliant strike and dip results. From the x and y
     * componenets of <b>N</b>, <CODE>strikeAndDip</CODE> calculates a strike
     * direction. Lastly, using the definition of a cross-product, the method
     * finds the dip of the plane of interest:<br/>
     * <br/>
     * <div align="center">
     * |<b>N</b> x <b>n</b>| = |<b>N</b>||<b>n</b>|sin(theta)
     * </div><br/>
     * where |<b>n</b>| = 1, so:<br/>
     * <br/>
     * <div align="center">
     * sin<sup>-1</sup>( |<b>strike</b>| / |<b>N</b>| ) = theta
     * </div><br/>
     * If a triangle turns out to be a horizontal plane, [0,0] is returned.<br/>
     * <br/>
     * @param verticesIn 2D triangle vertex array.
     * @return double[strike,dip] array.
     */    
    public static double[] getStrikeAndDip(double[][] verticesIn) {
        
        // initialize result
        double[] strikeDip = new double[2];
        
        // need the normal to the plane of interest
        double[] vNormal = getNormalVector(verticesIn);

        // get strike vector by finding cross product of unit z (n) vector and
        // normal to plane  :  n = 0i + 0j + 1k
        double[] vStrike = new double[3];
        vStrike = getCrossProduct(VZ_UNIT_NORMAL,vNormal,false);

        // calculate strike in degrees (0 to 360) 
        strikeDip[0] = calculateStrike(vStrike);
        
        // calculate dip by dividing magnitude vStrike by magnitude
        // VZ_UNIT_NORMAL(=1) and magnitude vN and taking the arcsin.
        strikeDip[1] = Math.toDegrees(Math.asin(getMagnitude(vStrike) / getMagnitude(vNormal)));
       
        return strikeDip;
    }
    
	/**
	 * Calculates the strike and dip of a trianglular surface as defined by
	 * three <code>Location</code>s. Internally, the three <code>Location</code>
	 * s are transformed to vertices in a local cartesian coordinate system and
	 * {@linkplain #getStrikeAndDip(double[][])} is called.<br/>
	 * <br/>
	 * Note that the results of this method are undefined for 
	 * <code>Location</code> arguments that span #177;180&#176;.
	 * 
	 * @param loc1
	 * @param loc2
	 * @param loc3
	 * @return the strike and dip of the plane defined by the supplied
	 *         <code>Location</code>s
	 * @throws IllegalArgumentException if <code>Location</code> arguments are
	 *         separated more than 1&#176; in latitude or longitude
	 * @see #getStrikeAndDip(double[][])
	 */
	public static double[] getStrikeAndDip(Location loc1, Location loc2,
			Location loc3) {
		
		double dLat12 = loc2.getLatitude() - loc1.getLatitude();
		double dLat13 = loc3.getLatitude() - loc1.getLatitude();
		double dLat23 = loc3.getLatitude() - loc2.getLatitude();
		double dLon12 = loc2.getLongitude() - loc1.getLongitude();
		double dLon13 = loc3.getLongitude() - loc1.getLongitude();
		double dLon23 = loc3.getLongitude() - loc2.getLongitude();
		
		if (dLat12 > 1 || dLat13 > 1 || dLat23 > 1 || dLon12 > 1 || dLon13 > 1
			|| dLon23 > 1) {
			throw new IllegalArgumentException(
				"Supplied Locations are more than 1 degree apart.");
		}
		
		double[][] vertices = new double[][] {
			{ 0.0, 0.0, -loc1.getDepth() },
			{ deltaLonKM(loc1, loc2), deltaLatKM(loc1, loc2), -loc2.getDepth() },
			{ deltaLonKM(loc1, loc3), deltaLatKM(loc1, loc3), -loc3.getDepth() } };

		return getStrikeAndDip(vertices);
	}

	private static double deltaLonKM(Location loc1, Location loc2) {
		double dLon = loc2.getLongitude() - loc1.getLongitude();
		double avgLat = (loc2.getLatitude() + loc1.getLatitude()) / 2;
		Location loc = new Location(avgLat, 0);
		return dLon / GeoTools.degreesLonPerKm(loc);
	}

	private static double deltaLatKM(Location loc1, Location loc2) {
		double dLat = loc2.getLatitude() - loc1.getLatitude();
		double avgLat = (loc2.getLatitude() + loc1.getLatitude()) / 2;
		Location loc = new Location(avgLat, 0);
		return dLat / GeoTools.degreesLatPerKm(loc);
	}
    
	public static void main(String[] args) {
		Location l1,l2,l3;
		double[] sd;
		
		l1 = new Location(0,0,0);
		l2 = new Location(1,1,0);
		l3 = new Location(0,1,110);
		sd = getStrikeAndDip(l1, l2, l3);
		System.out.println("Strike: " + sd[0] + " Dip: " + sd[1]);

		l1 = new Location(45,0,0);
		l2 = new Location(46,1,0);
		l3 = new Location(45,1,110);
		sd = getStrikeAndDip(l1, l2, l3);
		System.out.println("Strike: " + sd[0] + " Dip: " + sd[1]);

		l1 = new Location(89,0,0);
		l2 = new Location(90,1,0);
		l3 = new Location(89,1,110);
		sd = getStrikeAndDip(l1, l2, l3);
		System.out.println("Strike: " + sd[0] + " Dip: " + sd[1]);

		// southern hemisphere
		
		l1 = new Location(-1,-1,0);
		l2 = new Location(0,0,0);
		l3 = new Location(-1,0,110);
		sd = getStrikeAndDip(l1, l2, l3);
		System.out.println("Strike: " + sd[0] + " Dip: " + sd[1]);

		// reverse 1 and 2 above
		l1 = new Location(0,0,0);
		l2 = new Location(-1,-1,0);
		l3 = new Location(-1,0,110);
		sd = getStrikeAndDip(l1, l2, l3);
		System.out.println("Strike: " + sd[0] + " Dip: " + sd[1]);

		l1 = new Location(-46,-1,0);
		l2 = new Location(-45,0,0);
		l3 = new Location(-46,0,110);
		sd = getStrikeAndDip(l1, l2, l3);
		System.out.println("Strike: " + sd[0] + " Dip: " + sd[1]);

		// reverse 1 and 2 above
		l1 = new Location(-45,0,0);
		l2 = new Location(-46,-1,0);
		l3 = new Location(-46,0,110);
		sd = getStrikeAndDip(l1, l2, l3);
		System.out.println("Strike: " + sd[0] + " Dip: " + sd[1]);

		l1 = new Location(-89,0,0);
		l2 = new Location(-90,-1,0);
		l3 = new Location(-89,0,110);
		sd = getStrikeAndDip(l1, l2, l3);
		System.out.println("Strike: " + sd[0] + " Dip: " + sd[1]);

	}
	public static double[] getStrikeAndDip(double[] cosinesIn) {
        
		// initialize result
		double[] strikeDip = new double[2];

		// get strike vector by finding cross product of unit z (n) vector and
		// normal to plane  :  n = 0i + 0j + 1k
		double[] vStrike = new double[3];
		vStrike = getCrossProduct(VZ_UNIT_NORMAL,cosinesIn,false);

		// calculate strike in degrees (0 to 360) 
		strikeDip[0] = calculateStrike(vStrike);
        
		// calculate dip by dividing magnitude vStrike by magnitude
		// VZ_UNIT_NORMAL(=1) and magnitude vN and taking the arcsin.
		strikeDip[1] = Math.toDegrees(Math.asin(getMagnitude(vStrike) / getMagnitude(cosinesIn)));
       
		return strikeDip;
	}
    
    /**Calculates a slip vector from strike, dip, and rake information provided.
	 * @param strike
	 * @param dip
	 * @param rake
	 * @return double[x,y,z] array for slip vector. 
	 */
	public static double[] getSlipVector(double[] strikeDipRake) {
    	// start with y-axis unit normal on a horizontal plane
    	double[] startVector = VY_UNIT_NORMAL;
    	// rotate rake amount about z-axis (negative axial rotation)
    	double[] rakeRotVector = vectorMatrixMultiply(zAxisRotMatrix(-strikeDipRake[2]),startVector);
    	// rotate dip amount about y-axis (negative axial rotation)
		double[] dipRotVector = vectorMatrixMultiply(yAxisRotMatrix(-strikeDipRake[1]),rakeRotVector);
		// rotate strike amount about z-axis (positive axial rotation)
		double[] strikeRotVector = vectorMatrixMultiply(zAxisRotMatrix(strikeDipRake[0]),dipRotVector);
    	return strikeRotVector;
    }
    
    
    /** Calculates the strike of a horizontal vector.
     * <br/><font color="#D05625">Note: the <code>java.lang.Math.atan2</code> method 
     * will return unit circle polar coordinates (positive-CCW) when supplied 
     * with [y,x] but will return an azimuth (positive-CW) away
     * from the positive y-axis.</font>
     * @param xyVector 1D double[x,y] array of vector components.
     * @return strike of input vector.
     */
    public static double calculateStrike(double[] xyVector) {
        double strike = Math.toDegrees(Math.atan2(xyVector[0], xyVector[1]));
        if (strike<0) strike += 360.0;
        return strike;
    }
    
    
    /**Calculates the direction cosines for a plane defined by 3 vertices.
     * Returns the unit normal vector to the plane.
	 * @param verticesIn double[][] array of triangle vertices.
	 * @return double[x,y,z] array of direction cosines.
	 */    
    public static double[] getDirectionCosines(double[][] verticesIn) {
        // need the normal to the plane of interest and dump it into cosines array
        double[] cosines = getNormalVector(verticesIn);
        // normalize vector for cosines
        normalizeVector(cosines);
        return cosines;
    }
    
    
	/**Calculates the direction cosines for a plane defined by strike and dip.
	 * Returns the unit normal vector to the plane.
	 * @param strikeAndDip double[strike,dip] data in degrees.
	 * @return double[x,y,z] array of direction cosines.
	 */    
    public static double[] getDirectionCosines(double[] strikeAndDip) {
    	double strike = Math.toRadians(strikeAndDip[0]);
    	double dip = Math.toRadians(strikeAndDip[1]);
    	// use updip direction for no particular reason
    	double dipDir = Math.toRadians(strikeAndDip[0] - 90.0);
    	
    	double[] v1 = { Math.sin(strike) , Math.cos(strike), 0.0 };
    	double[] v2 = { Math.cos(dip)*Math.sin(dipDir), Math.cos(dip)*Math.cos(dipDir) , Math.sin(dip) };
    	
    	// get the cross-product or normal vector and normalize
    	double[] cosines = getCrossProduct(v1,v2,true);
    	normalizeVector(cosines);
    	return cosines;
    }
    
    
	/**Normalizes the vector/array passed as argument.
	 * @param v double[x,y,z] vector.
	 */
    public static void normalizeVector(double[] v) {
    	double vectorMagnitude = getMagnitude(v);
    	for (int i=0;i<3;i++) {
    		v[i] = v[i]/vectorMagnitude;
    	}
    }
    
    
    /**Computes the positive upward normal vector of a triangular surface defined by
     * three vertices.
	 * @param verticesIn 2D double array of triangle vertices.
	 * @return double[x,y,z] array.
	 */
	public static double[] getNormalVector(double[][] verticesIn) {

        // initialize vectors
        double[] vs = new double[3];
        double[] vt = new double[3];
        double[] vN = new double[3];

        // create two vectors from vertices using 1st point as origin
        // vs = v2-v1     vt = v3-v1
        for (int i=0; i<3; i++) {
            vs[i] = verticesIn[1][i] - verticesIn[0][i];
            vt[i] = verticesIn[2][i] - verticesIn[0][i];
        }
        
        // find the positive up normal vector to the surface of interest
        vN = getCrossProduct(vs,vt,true);
        return vN;
    }

    
    /** Returns the cross product of two vectors in component form. 
     * @param v1 1D [x,y,z] array of vector components.
     * @param v2 1D [x,y,z] array of vector components.
     * @param up if true, returns a vector that is positive up (i.e. reverses operation).
     * @return double[x,y,z] array of vector components.
     */
    public static double[] getCrossProduct(double[] v1, double[] v2, boolean up) {
        double[] xProduct = new double[3];
        xProduct[0] = v1[1]*v2[2] - v1[2]*v2[1];
        xProduct[1] = v1[2]*v2[0] - v1[0]*v2[2];
        xProduct[2] = v1[0]*v2[1] - v1[1]*v2[0];
        if ((up == true) && (xProduct[2]<0)) {
            xProduct[0] *= -1;
            xProduct[1] *= -1;
            xProduct[2] *= -1;
        }
        return xProduct;
    }

    
	/**Computes the angle between two vectors. Calculates the inverse cosine of the dot
     * product divided by the magnitudes of the two vectors
	 * @param v1 1D double[x,y,z] array of vector components.
	 * @param v2 1D double[x,y,z] array of vector components.
	 * @return angle between two vectors in radians.
	 */
	public static double getVectorInterangle (double[] v1, double[] v2) {
        // get dot product, divide by vector magnitudes, take acos
        // could use cross prodect but dp is computationally less expensive;
        // result is in radians
        double angle = Math.acos((getDotProduct(v1,v2)) / (getMagnitude(v1)*getMagnitude(v2)));
        return angle;
    }
    
    
	/**Computes the minimum(acute) angle between two vectors. Finds vector interangle and
	 * subtracts PI/2 if necessary
	 * @param v1 1D double[x,y,z] array of vector components.
	 * @param v2 1D double[x,y,z] array of vector components.
	 * @return minimum(acute) angle between two vectors in radians.
	 */
    public static double getMinVectorInterangle(double[] v1, double[] v2) {
        double angle = getVectorInterangle(v1,v2);
        if (angle > (Math.PI/2.0)) angle -= Math.PI/2.0;
        return angle;
    }
    
    
    /**Computes the scalar(dot) product of two vectors.
	 * @param v1 1D double[x,y,z] array of vector components.
	 * @param v2 1D double[x,y,z] array of vector components.
	 * @return scalar product.
	 */
	public static double getDotProduct (double[] v1, double[] v2) {
        double dp = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2];
        return dp;
    }
    
    
    /** Returns the scalar magnitude of a vector. 
     * @param v 1D [x,y,z] array of vector components.
     * @return magnitude of input vector.
     */
    public static double getMagnitude(double[] v) {
        double mag = (Math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]));
        return mag;
    }
    
    
    /**Computes the location in a 3D data array closest to a point of interest.
	 * @param xyzDimensions int[x,y,z] array describing volume of interest.
	 * @param xyzOrigins long[x,y,z] array describing orgin of volume of interest.
	 * @param xyzInterval int[x,y,z] array describing distance between data points.
	 * @param xyzPoint double[x,y,z] array describing point of interest.
	 * @return int[x,y,z] array of point in data array.
	 */
	public static int[] getNearestNeighbor(int[] xyzDimensions, long[] xyzOrigins,
                                           int[] xyzInterval, double[] xyzPoint) {
        int[] nn = new int[3];

        // NOTE: need to invert zPoint value for our left-handed, positive-down
        //       coordinate system. z is negative-down in tSurf files.
        double[] xyzPointInv = {xyzPoint[0], xyzPoint[1], xyzPoint[2]*-1};
        
        // check to see if point[] is out of bounds
        for (int i=0; i<3; i++) {
            long min = xyzOrigins[i];
            long max = xyzOrigins[i] + ((xyzDimensions[i]-1) * xyzInterval[i]);
            if ((xyzPointInv[i] < min) || (xyzPointInv[i] > max)) {
                nn[0] = -1; nn[1] = -1; nn[2] = -1;
                return nn;
            }
            long inboundsLength = (long)xyzPointInv[i] - min;
            int dataLocation = (int)((inboundsLength / xyzInterval[i]) + 1);
            // need to add 1 so that correct data position gets returned
            if ((inboundsLength % xyzInterval[i]) >= (xyzInterval[i]/2)) {
                dataLocation += 1;
            }
            nn[i] = dataLocation;
        }
        return nn;
    }
    
    
    /**Given a stress tensor, method returns principal stresses and the direction
     * cosines for each principal stress. Method performs an Eigenvalue decomposition
     * for eigenvalues and eigenvectors.
	 * @param stressTensor double[i][j] array of stress tensor components.
	 * @return double[4][3] array - first row is principal stresses; rows
	 * 2-4 are x,y, and z direction cosines respectively.
	 */
	public static double[][] getPrincipalStresses (double[][] stressTensor) {
        // 3x4 matrix
        //      -stresses(3)
        //      -x direction cosines
        //      -y direction cosines
        //      -z direction cosines
        // direction cosines of each axis are row values of 3D rotation matrix
        double[][] out = new double[4][3];
        Matrix stress = new Matrix(stressTensor);
        EigenvalueDecomposition stressEig = stress.eig();
        double[][] stresses = stressEig.getD().getArray();
        double[][] rotations = stressEig.getV().getArray();
        // load stresses into first row of out matrix
        for (int i=0; i<3; i++) {
            out[0][i] = stresses[i][i];
        }
        // load directions into rows 2-4
        for (int j=1; j<4; j++) {
            for (int k=0; k<3; k++) {
                out[j][k] = rotations[j-1][k];
            }
        }
        return out;
    }

    
    /**Calculates the traction on a plane that results from an imposed stress tensor. 
     * A traction, or force, on a plane is equivalent to the vector product of
     * a stress tensor and the direction cosines of the plane of interest.
	 * @param stressTensor double[i][j] array of stress tensor components.
	 * @param cosines double[x,y,z] of direction cosines.
	 * @return double[x,y,z] force on plane provided.
	 */
	public static double[] getTraction(double[][] stressTensor, double[] cosines) {
        double[] traction = new double[3];
        for (int i=0; i<3; i++) {
            traction[i] = (stressTensor[i][0]*cosines[0]) + 
                          (stressTensor[i][1]*cosines[1]) + 
                          (stressTensor[i][2]*cosines[2]);
        }
        return traction;
    }
 
	
	/** Calculates shear and normal stresses from a traction on a plane of interest.
	 * Result is simply normal (tension or compression) stress and shear (always positive) stress
	 * and does not account for dominant slip direction on the plane of interest.
	 * @param stressTensor double[i][j] array of stress tensor components.
	 * @param cosines double[x,y,z] of direction cosines.
	 * @return double[normalStress,shearStress]
	 */
	public static double[] getStresses(double[][] stressTensor, double[] cosines){
		// get traction, find angle between the plane of interest and the traction to resolve shear
		// and normal stress componenets
		double[] traction = getTraction(stressTensor,cosines);
		double theta = PlaneUtils.getVectorInterangle(cosines,traction);
		double tractionMagnitude = PlaneUtils.getMagnitude(traction);
		// calculate separate stress components
		
		double normalStress = tractionMagnitude*(Math.cos(theta));
		double shearStress = tractionMagnitude*(Math.sin(theta));
		//double normalStress = tractionMagnitude*(Math.cos(theta))*(Math.cos(theta));
		//double shearStress = tractionMagnitude*(Math.sin(theta))*(Math.cos(theta));
		
		
		// ??
		//if (theta < (Math.PI/2.0)) shearStress *= -1.0;

		double[] stresses = {normalStress,shearStress};
		return stresses;
	}
	
	
	/** Calculates shear and normal stresses from a traction on a plane of interest.
	 * Result returns normal stress (tension or compression) and shear stress change relative
	 * to dominant slip vector on plane of interest.
	 * @param stressTensor double[i][j] array of stress tensor components.
	 * @param cosines double[x,y,z] of direction cosines.
	 * @param slipVector double[x,y,z] of slip direction on plane of interest.
	 * @return double[normalStress,shearStress]
	 */
	public static double[] getNormalAndShearStress(double[][] stressTensor, double[] cosines, double[] slipVector){
		// get traction
		double[] traction = getTraction(stressTensor,cosines);
		double tractionMagnitude = PlaneUtils.getMagnitude(traction);
		// find angle between the plane of interest and the traction
		double theta = PlaneUtils.getVectorInterangle(cosines,traction);
		// calculate separate stress components
		double normalStressMag = tractionMagnitude*(Math.cos(theta));
		double shearStressMag = tractionMagnitude*(Math.sin(theta));
		
		// get actual shear stress contribution
		// start be getting the (P X T) X P product (gives direction of shear stress)
		double[] shearVector = PlaneUtils.getCrossProduct(PlaneUtils.getCrossProduct(cosines,traction,false),cosines,false);
		// get angle between shear stress and slip vector
		double phi = PlaneUtils.getVectorInterangle(slipVector,shearVector);
		// scale shear stress
		shearStressMag = shearStressMag*Math.cos(phi);
		
		// if phi > 90 then shear stress change is negative
		
		// correct for tension or compression
		//shearStressMag *= -1.0;
		///if (theta > (Math.PI/2.0)) shearStressMag *= -1.0;
		
		double[] stresses = {normalStressMag,shearStressMag};
		return stresses;
	}


	/** Calculates Coulomb failure stress. Expects shear and nnormal stress and an effective
	 * coefficient of friction.
	 * @param normalStress double
	 * @param shearStress double
	 * @param friction effeective coefficient of friction (mu')
	 * @return double Coulomb failure stress
	 */
	public static double calculateCoulomb(double normalStress, double shearStress, double friction) {
		//double coulomb = (shearStress - (normalStress*friction))/100000.0;
		double coulomb = (shearStress - (-normalStress*friction));
		return coulomb;
	}
	
	
    /** Axial rotation of a coordinate pair (vector) using a rotation matrix.
     *  Method used for horizontal rotations (about z-axis).
     * <br/>
     * <div align="center"><b><br/>
     * |x'| = | cos&#952; sin&#952;||x|<br/>
     * |y'| = |-sin&#952; cos&#952;||y|<br/>
     * </div></b>
     * @param coordinates (as doubles) coordinates to be rotated.
     * @param theta amount of rotation in degrees.
     * @return a double[] array of rotated coordinates as doubles.
     */
    /*public static double[] rotateCoordinates(double xCoord, double yCoord, double theta) {
        double[] rotCoord = new double[2];
        double thetaRad = Math.toRadians(theta);
        rotCoord[0] = (xCoord*(Math.cos(thetaRad))) + (yCoord*(Math.sin(thetaRad)));
        rotCoord[1] = (xCoord*(-Math.sin(thetaRad))) + (yCoord*(Math.cos(thetaRad)));
        return rotCoord;
    }*/

	public static double[] rotateCoordinates(double[] coords, double theta) {
		// fill dummy z variable as if 3D rotation
		double[] xyz = {coords[0],coords[1],0.0};
		double[] rotCoord = vectorMatrixMultiply(zAxisRotMatrix(theta),xyz);
		double[] out = {rotCoord[0],rotCoord[1]};
		return out;
	}
    
    
	/**Returns a rotation matrix about the x axis in a right-handed coordinate system for a given theta.
	 * Note that these are coordinate transformations and that a positive (anticlockwise) rotation
	 * of a vector is the same as a negative rotation of the reference frame. 
	 * @param theta axial rotation in degrees. 
	 * @return double[][] rotation matrix.
	 */
	public static double[][] xAxisRotMatrix(double theta) {
		double thetaRad = Math.toRadians(theta);
		double[][] rotMatrix= {{ 1.0 ,                 0.0 ,                0.0 },
							   { 0.0 ,  Math.cos(thetaRad) , Math.sin(thetaRad) },
							   { 0.0 , -Math.sin(thetaRad) , Math.cos(thetaRad) }};
		return rotMatrix;
	}
 
 
	/**Returns a rotation matrix about the y axis in a right-handed coordinate system for a given theta.
	 * Note that these are coordinate transformations and that a positive (anticlockwise) rotation
	 * of a vector is the same as a negative rotation of the reference frame. 
	 * @param theta axial rotation in degrees. 
	 * @return double[][] rotation matrix.
	 */
	public static double[][] yAxisRotMatrix(double theta) {
		double thetaRad = Math.toRadians(theta);
		double[][] rotMatrix= {{ Math.cos(thetaRad) , 0.0 , -Math.sin(thetaRad) },
							   {                0.0 , 1.0 ,                 0.0 },
							   { Math.sin(thetaRad) , 0.0 ,  Math.cos(thetaRad) }};
		return rotMatrix;
	}
 
 
	/**Returns a rotation matrix about the z axis in a right-handed coordinate system for a given theta.
	 * Note that these are coordinate transformations and that a positive (anticlockwise) rotation
	 * of a vector is the same as a negative rotation of the reference frame. 
	 * @param theta axial rotation in degrees. 
	 * @return double[][] rotation matrix.
	 */
	public static double[][] zAxisRotMatrix(double theta) {
		double thetaRad = Math.toRadians(theta);
		double[][] rotMatrix= {{  Math.cos(thetaRad) , Math.sin(thetaRad) , 0.0 },
							   { -Math.sin(thetaRad) , Math.cos(thetaRad) , 0.0 },
		      			       {                 0.0 ,                0.0 , 1.0 }};
		return rotMatrix;
	}
 
 
    /** Rotates a 3D tensor about the z-axis(vertical) 
	 * @param tensorData double[][] tensor data array.
	 * @param theta degrees to rotate anticlockwise about z-axis.
	 * @return double[][] rotated tensor.
	 */
	public static double[][] rotateTensor(double[][] tensorData, double theta) {
    	double thetaRad = Math.toRadians(theta);
      	Matrix rotationMatrix = new Matrix(zAxisRotMatrix(theta));
    	// calculated rotated stress tensor via t = RTR-t
    	Matrix rotatedTensor = rotationMatrix.times(new Matrix(tensorData)).times(rotationMatrix.transpose());
    	
    	return rotatedTensor.getArray();
    }
   
    
    /** Multiplies the vector provided with a matrix. Useful for rotations.
	 * @param matrix double[][] matrix (likely one of the rotation matrices from this class).
	 * @param vector double[x,y,z] to be modified. 
	 */
	public static double[] vectorMatrixMultiply(double[][] matrix, double[] vector) {
		double[] rotatedVector = new double[3];
    	for (int i=0;i<3;i++) {
			rotatedVector[i] = vector[0]*matrix[i][0] + vector[1]*matrix[i][1] + vector[2]*matrix[i][2];
		}
		return rotatedVector;
    }
    
    
    /**Calculates a fault area based on moment magnitude. Method uses relations of Wells and
     * Coppersmith(1994) and returns 1 dimension of a fault patch (assumes a square rupture).
	 * @param magnitude Moment magnitude.
	 * @return length of one side of a square rupture patch.
	 */
	// calculate fault patch size from magnitude
    public static double faultAreaFromMagnitude(double magnitude) {
        double faultArea = Math.pow(10.0,((magnitude-4.07)/0.98));
        double faultDimension = Math.sqrt(faultArea);
        return faultDimension;
    }


	/**Calculates a fault slip based on moment magnitude. Method uses relations of Wells and
	 * Coppersmith(1994).
	 * @param magnitude Moment magnitude.
	 * @return slip amount. 
	 */
    // calculate fault slip from magnitude returns value in meters
    public static double faultSlipFromMagnitude(double magnitude) {
        double faultSlip = Math.pow(10.0,((magnitude-6.93)/0.82));
        return faultSlip;
    }
    
    
    /**Calculates strike- and dip-slip components of a rupture. Given the amount of slip
     * and rake of a rupture, method will return the +/- components of the slip vector
	 * @param slip fault slip amount.
	 * @param rake direction of slip.
	 * @return double[strike-slip,dip-slip] array.
	 */
	// calculate Okada strike and dip slip components
    // turns out we don't need to do any checking for rake interval b/c
    // rake is given from 0 to +/-180 which correctly resolves slip directions
    public static double[] okadaSlipComponents(double slip, double rake) {
        double slipComponents[] = new double[2];
        // strike slip component
        slipComponents[0] = slip*Math.cos(Math.toRadians(rake));
        // dip slip component
        slipComponents[1] = slip*Math.sin(Math.toRadians(rake));
        return slipComponents;
    }


    
}
