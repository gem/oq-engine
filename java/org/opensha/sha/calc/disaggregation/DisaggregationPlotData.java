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

package org.opensha.sha.calc.disaggregation;

import java.io.Serializable;

/**
 * Class represents data required to make a Disaggregation plot
 * 
 * @author kevin
 *
 */
public class DisaggregationPlotData implements Serializable {
	
	private double maxContrEpsilonForGMT_Plot;

	private double[] mag_center, mag_binEdges;
	private double[] dist_center, dist_binEdges;
	
	private int NUM_E = 8;
	private double[][][] pdf3D;

	public DisaggregationPlotData(double[] mag_center, double[] mag_binEdges, double[] dist_center,
			double[] dist_binEdges, double maxContrEpsilonForGMT_Plot, int numE, double[][][] pdf3D) {
		this.mag_center = mag_center;
		this.mag_binEdges = mag_binEdges;
		this.dist_center = dist_center;
		this.dist_binEdges = dist_binEdges;
		this.maxContrEpsilonForGMT_Plot = maxContrEpsilonForGMT_Plot;
		this.NUM_E = numE;
		this.pdf3D = pdf3D;
	}

	public double[] getMag_center() {
		return mag_center;
	}

	public void setMag_center(double[] mag_center) {
		this.mag_center = mag_center;
	}

	public double[] getMag_binEdges() {
		return mag_binEdges;
	}

	public void setMag_binEdges(double[] mag_binEdges) {
		this.mag_binEdges = mag_binEdges;
	}

	public double[] getDist_center() {
		return dist_center;
	}

	public void setDist_center(double[] dist_center) {
		this.dist_center = dist_center;
	}

	public double[] getDist_binEdges() {
		return dist_binEdges;
	}

	public void setDist_binEdges(double[] dist_binEdges) {
		this.dist_binEdges = dist_binEdges;
	}

	public int getNUM_E() {
		return NUM_E;
	}

	public void setNUM_E(int num_e) {
		NUM_E = num_e;
	}

	public double[][][] getPdf3D() {
		return pdf3D;
	}

	public void setPdf3D(double[][][] pdf3D) {
		this.pdf3D = pdf3D;
	}

	public double getMaxContrEpsilonForGMT_Plot() {
		return maxContrEpsilonForGMT_Plot;
	}

	public void setMaxContrEpsilonForGMT_Plot(
			double maxContrEpsilonForGMT_Plot) {
		this.maxContrEpsilonForGMT_Plot = maxContrEpsilonForGMT_Plot;
	}

}
