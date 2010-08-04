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

import static org.junit.Assert.*;

import org.junit.Test;
import org.opensha.commons.util.binFile.BinaryMesh2DCalculator;

public class BinaryMesh2DTest {
	
	BinaryMesh2DCalculator singleRow;
	BinaryMesh2DCalculator singleCol;
	BinaryMesh2DCalculator rect;
	BinaryMesh2DCalculator rect_fast_yx;

	public BinaryMesh2DTest() {
		singleRow = new BinaryMesh2DCalculator(BinaryMesh2DCalculator.TYPE_FLOAT, 10, 1);
		singleCol = new BinaryMesh2DCalculator(BinaryMesh2DCalculator.TYPE_FLOAT, 1, 10);
		rect = new BinaryMesh2DCalculator(BinaryMesh2DCalculator.TYPE_FLOAT, 7, 11);
		rect_fast_yx = new BinaryMesh2DCalculator(BinaryMesh2DCalculator.TYPE_FLOAT, 7, 11);
		rect_fast_yx.setMeshOrder(BinaryMesh2DCalculator.FAST_YX);
	}
	
	@Test
	public void testSingleRow() {
		for (int x=0; x<singleRow.getNX(); x++) {
			long ind = singleRow.calcMeshIndex(x, 0);
			assertTrue(ind == x);
			long fInd = singleRow.calcFileIndex(x, 0);
			assertTrue(fInd == (ind * 4));
		}
	}
	
	@Test
	public void testSingleCol() {
		for (int y=0; y<singleCol.getNY(); y++) {
			long ind = singleCol.calcMeshIndex(0, y);
			assertTrue(ind == y);
			long fInd = singleCol.calcFileIndex(0, y);
			assertTrue(fInd == (ind * 4));
		}
	}
	
	@Test
	public void testRect() {
		for (int x=0; x<rect.getNX(); x++) {
			for (int y=0; y<rect.getNY(); y++) {
				long ind = rect.calcMeshIndex(x, y);
				assertTrue(ind == (x + y*rect.getNX()));
				long fInd = rect.calcFileIndex(x, y);
				assertTrue(fInd == (ind * 4));
			}
		}
	}
	
	@Test
	public void testRectYX() {
		for (int x=0; x<rect_fast_yx.getNX(); x++) {
			for (int y=0; y<rect_fast_yx.getNY(); y++) {
				long ind = rect_fast_yx.calcMeshIndex(x, y);
				assertTrue(ind == (y + x*rect.getNY()));
				long fInd = rect_fast_yx.calcFileIndex(x, y);
				assertTrue(fInd == (ind * 4));
			}
		}
	}

}
