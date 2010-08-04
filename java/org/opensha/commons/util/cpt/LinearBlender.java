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

package org.opensha.commons.util.cpt;

import java.awt.Color;

public class LinearBlender implements Blender {

	/**
	 * Constructs a blender which interpolates linearly between the smallColor
	 * and BigColor
	 */
	public LinearBlender() {

	}

	/**
	 * Linearly interpolates a new color between smallColor and bigColor with a
	 * bias in range[0,1] For example bias = .5 means a value between half of
	 * smallColor and half of bigColor
	 */
	public int[] blend(int smallR, int smallG, int smallB, int bigR, int bigG,
			int bigB, float bias) {
		// TODO Auto-generated method stub
		int rgb[] = new int[3];
		
		rgb[0] = this.blend(smallR, bigR, bias);
		rgb[1] = this.blend(smallG, bigG, bias);
		rgb[2] = this.blend(smallB, bigB, bias);
		
		return rgb;
	}
	
	private int blend(int small, int big, float bias) {
		float blend = (float)big * bias + (1f - bias) * (float)small;
		return (int)(blend + 0.5);
	}

	public Color blend(Color small, Color big, float bias) {
		int rgb[] = this.blend(small.getRed(), small.getGreen(), small.getBlue(), big.getRed(), big.getGreen(), big.getBlue(), bias);
		return new Color(rgb[0], rgb[1], rgb[2]);
	}

}
