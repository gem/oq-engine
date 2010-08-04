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

package org.opensha.commons.util.binFile;

public class BinaryMesh2DCalculator {
	
	public static final int FAST_XY = 0;
	public static final int FAST_YX = 1;
	
	public static final int TYPE_SHORT = 0;
	public static final int TYPE_INT = 1;
	public static final int TYPE_LONG = 2;
	public static final int TYPE_FLOAT = 3;
	public static final int TYPE_DOUBLE = 4;
	
	protected long nx;
	protected long ny;
	private int numType;
	
	private long maxFilePos;
	
	private int meshOrder = FAST_XY;
	
	private int numBytesPerPoint;
	
	public BinaryMesh2DCalculator(int numType, long nx, long ny) {
		
		if (numType == TYPE_SHORT) {
			numBytesPerPoint = 2;
		} else if (numType == TYPE_INT || numType == TYPE_FLOAT) {
			numBytesPerPoint = 4;
		} else if (numType == TYPE_LONG || numType == TYPE_DOUBLE) {
			numBytesPerPoint = 8;
		}
		
		this.nx = nx;
		this.ny = ny;
		
		this.maxFilePos = calcMaxFilePos();
		
		this.numType = numType;
	}
	
	public long calcMeshIndex(long x, long y) {
		if (meshOrder == FAST_XY) {
			return nx * y + x;
		} else { // FAST_YX
			return ny * x + y;
		}
	}
	
	public long calcFileIndex(long x, long y) {
		return numBytesPerPoint * this.calcMeshIndex(x, y);
	}
	
	public long getNX() {
		return nx;
	}

	public void setNX(int nx) {
		this.nx = nx;
		maxFilePos = calcMaxFilePos();
	}

	public long getNY() {
		return ny;
	}

	public void setNY(int ny) {
		this.ny = ny;
		maxFilePos = calcMaxFilePos();
	}

	public long getMaxFilePos() {
		return maxFilePos;
	}
	
	private long calcMaxFilePos() {
		return (nx - 1) * (ny - 1) * numBytesPerPoint;
	}

	public int getMeshOrder() {
		return meshOrder;
	}

	public void setMeshOrder(int meshOrder) {
		this.meshOrder = meshOrder;
	}
	
	public int getType() {
		return numType;
	}

}
