/*******************************************************************************
 * Copyright 2009 OpenSHA.org in partnership with
 * the Southern California Earthquake Center (SCEC, http://www.scec.org)
 * at the University of Southern California and the UnitedStates Geological
 * Survey (USGS; http://www.usgs.gov)
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ******************************************************************************/

package org.opensha.commons.util.interp;

/*
Java class to implement a bicubic interpolator
      by Ken Perlin @ NYU, 1998.

You have my permission to use freely, as long as you keep the attribution. - Ken Perlin

Note: this Bicubic.html file also works as a legal Bicubic.java file. If you save the source under that name, you can just run javac on it.
Why does this class exist?

    I created this class because I needed to evaluate a fairly expensive function over x,y many times. It turned out that I was able to rewrite the function as a sum of a "low frequency" part that only varied slowly, and a much less expensive "high frequency" part that just contained the details.

    I used the bicubic patches as follows: First I presampled the low frequency part on a coarse grid. During the inner loop of the evaluation, I used this bicubic approximation, and then added in the high frequency part. Through this approach I was able to speed up the computation by a large factor. 

What does the class do?

    If you provide a 4x4 grid of values (ie: all the corners in a 3x3 arrangement of square tiles), this class creates an object that will interpolate a Catmull-Rom spline to give you the value within any point of the center tile.

    If you want to create a spline surface, you can make a two dimensional array of such objects, arranged so that adjoining objects overlap by one grid point. 

The class provides a constructor and a method:

    Bicubic(double[][] G)

        Given 16 values on the grid [-1,0,1,2] X [-1,0,1,2], calculate bicubic coefficients. 

    double eval(double x, double y)

        Given a point in the square [0,1] X [0,1], return a value. 

Algorithm:

    f(x,y) = X * M * G * MT * YT , where:

        X = (x3 x2 x 1) ,
        Y = (y3 y2 y 1) ,
        M is the Catmull-Rom basis matrix. 

    The constructor Bicubic() calculates the matrix C = M * G * MT

    The method eval(x,y) calculates the value X * C * YT 

*/

public class BicubicInterpolation2D {

	static double[][] M = {             // Catmull-Rom basis matrix
		{-0.5,  1.5, -1.5, 0.5},
		{ 1  , -2.5,  2  ,-0.5},
		{-0.5,  0  ,  0.5, 0  },
		{ 0  ,  1  ,  0  , 0  }
	};

	double[][] C = new double[4][4];    // coefficients matrix

	public BicubicInterpolation2D(double[][] G) {
		double[][] T = new double[4][4];

		for (int i = 0 ; i < 4 ; i++)    // T = G * MT
			for (int j = 0 ; j < 4 ; j++)
				for (int k = 0 ; k < 4 ; k++)
					T[i][j] += G[i][k] * M[j][k];

		for (int i = 0 ; i < 4 ; i++)    // C = M * T
			for (int j = 0 ; j < 4 ; j++)
				for (int k = 0 ; k < 4 ; k++)
					C[i][j] += M[i][k] * T[k][j];
	}

	double[] X3 = C[0], X2 = C[1], X1 = C[2], X0 = C[3];

	public double eval(double x, double y) {
		return x*(x*(x*(y * (y * (y * X3[0] + X3[1]) + X3[2]) + X3[3])
				+ (y * (y * (y * X2[0] + X2[1]) + X2[2]) + X2[3]))
				+    (y * (y * (y * X1[0] + X1[1]) + X1[2]) + X1[3]))
				+       (y * (y * (y * X0[0] + X0[1]) + X0[2]) + X0[3]);
	}
	
	public static void main(String args[]) {
		double G[][] = new double[4][4];
		
		for (int x=0; x<4; x++) {
			for (int y=0; y<4; y++) {
				G[x][y] = x*y;
				System.out.print(G[x][y] + " ");
			}
			System.out.println();
			System.out.println();
		}
		
		BicubicInterpolation2D interp = new BicubicInterpolation2D(G);
		
		System.out.println();
		System.out.println(interp.eval(0.37, 0.5));
	}
}
