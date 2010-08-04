package org.opensha.commons.data;

import static org.junit.Assert.*;

import java.io.File;
import java.io.IOException;

import org.junit.Test;
import org.opensha.commons.exceptions.InvalidRangeException;
import org.opensha.commons.util.FileUtils;

public class TestEvenlyDiscretizedXYZ_DataSet {

	private static final int ncols = 10;
	private static final int nrows = 5;
	private static final double minX = 0.5;
	private static final double minY = 1.5;
	private static final double gridSpacing = 0.15;
	
	@Test
	public void testConstructors() {
		EvenlyDiscretizedXYZ_DataSet data = new EvenlyDiscretizedXYZ_DataSet(ncols, nrows, minX, minY, gridSpacing);
		
		assertTrue("ncols not set correctly", ncols == data.getNumX());
		assertTrue("nrows not set correctly", nrows == data.getNumY());
		
//		double maxX = minX + gridSpacing * (ncols-1);
		double maxX = 1.85;
		double maxY = 2.1;
		
		assertEquals("maxX not set correctly", maxX, data.getMaxX(), 0.00000001);
		assertEquals("maxY not set correctly", maxY, data.getMaxY(), 0.00000001);
	}
	
	@Test
	public void testAddValue() {
		EvenlyDiscretizedXYZ_DataSet data = new EvenlyDiscretizedXYZ_DataSet(ncols, nrows, minX, minY, gridSpacing);
		try {
			data.addValue(0, minY, 0);
			fail("Should throw InvalidRangeException because x less than minX");
		} catch (InvalidRangeException e) {}
		
		try {
			data.addValue(minX, 0, 0);
			fail("Should throw InvalidRangeException because y less than minY");
		} catch (InvalidRangeException e) {}
		
		try {
			data.addValue(data.getMaxX() + 1, minY, 0);
			fail("Should throw InvalidRangeException because x greater than maxX");
		} catch (InvalidRangeException e) {}
		
		try {
			data.addValue(minX, data.getMaxY() + 1, 0);
			fail("Should throw InvalidRangeException because y greater than maxY");
		} catch (InvalidRangeException e) {}
		
		data.addValue(minX, minY, 0.35);
		assertEquals("addValue didn't work", 0.35, data.getVal(minX, minY), 0.0000001);
		assertEquals("addValue didn't work", 0.35, data.getVal(0, 0), 0.0000001);
		
		data.addValue(minX + 0.06, minY + 0.06, 0.35);
		assertEquals("addValue didn't work", 0.35, data.getVal(minX, minY), 0.0000001);
		assertEquals("addValue didn't work", 0.35, data.getVal(0, 0), 0.0000001);
		
		data.addValue(minX + gridSpacing - 0.06, minY + gridSpacing - 0.06, 0.35);
		assertEquals("addValue didn't work", 0.35, data.getVal(minX + gridSpacing, minY + gridSpacing), 0.0000001);
		assertEquals("addValue didn't work", 0.35, data.getVal(1, 1), 0.0000001);
	}
	
	@Test
	public void testBinaryIO() throws IOException {
		File tempDir = FileUtils.createTempDir();
		String fileNamePrefix = tempDir.getAbsolutePath() + File.separator + "data";
		EvenlyDiscretizedXYZ_DataSet data = new EvenlyDiscretizedXYZ_DataSet(ncols, nrows, minX, minY, gridSpacing);
		
		for (int row=0; row<nrows; row++) {
			for (int col=0; col<ncols; col++) {
				data.addValue(col, row, Math.random());
			}
		}
		
		data.writeXYZBinFile(fileNamePrefix);
		
		EvenlyDiscretizedXYZ_DataSet newData = EvenlyDiscretizedXYZ_DataSet.readXYZBinFile(fileNamePrefix);
		
		for (int row=0; row<nrows; row++) {
			for (int col=0; col<ncols; col++) {
				double origVal = data.getVal(col, row);
				double newVal = newData.getVal(col, row);
				
				assertEquals("", origVal, newVal, 0.00001);
			}
		}
		
		for (File file : tempDir.listFiles()) {
			file.delete();
		}
		tempDir.delete();
	}

}
