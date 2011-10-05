package org.gem.hdf5;

import static org.junit.Assert.*;

import java.io.File;
import java.util.Arrays;

import ncsa.hdf.hdf5lib.exceptions.HDF5LibraryException;

import org.junit.Test;
import org.junit.AfterClass;
import org.junit.BeforeClass;

import static org.gem.hdf5.HDF5Util.reshape;
import static org.gem.hdf5.HDF5Util.readMatrix;
import static org.gem.hdf5.HDF5Util.writeMatrix;

public class HDF5UtilTest 
{

	public static final String H5_FILE = "test_5d_array.h5";
	public static final String H5_FILE_COMPRESSED =
			"test_5d_array_compressed.h5";
	public static final String INVALID_HDF5_FILE =
			"java_tests/data/invalid_hdf5_file.h5";
	public static final long[] SAMPLE_5D_ARRAY_SHAPE = {2, 2, 2, 2, 2};
	public static final double[][][][][] SAMPLE_5D_ARRAY = 
		{
			{
				{
					{{0, 2}, {4, 6}},
					{{8, 10}, {12, 14}}
				},
				{
					{{16, 18}, {20, 22}},
					{{24, 26}, {28, 30}}
				}
			},
			{
				{
					{{32, 34}, {36, 38}},
					{{40, 42}, {44, 46}}
				},
				{
					{{48, 50}, {52, 54}},
					{{56, 58}, {60, 62}}
				}
			}
		};
	
	@BeforeClass
	public static void setUpBeforeClass() throws Exception
	{
		// If any test files exist from a previous test run,
		// clear them out so we can write new files in the tests:
		new File(H5_FILE).delete();
		new File(H5_FILE_COMPRESSED).delete();
	}

	@AfterClass
	public static void tearDownAfterClass() throws Exception
	{
		new File(H5_FILE).delete();
		new File(H5_FILE_COMPRESSED).delete();
	}

	@Test(expected=HDF5Exception.class)
	public void testReshapeTooFewDims() throws HDF5Exception
	{
		long[] tooFew = {1, 2, 3, 4};
		reshape(null, tooFew);
	}

	@Test(expected=HDF5Exception.class)
	public void testReshapeTooManyDims() throws HDF5Exception
	{
		long[] tooMany = {1, 2, 3, 4, 5, 6};
		reshape(null, tooMany);
	}

	@Test(expected=HDF5Exception.class)
	public void testReshapeLengthDoesNotMatchShape() throws HDF5Exception
	{
		long[] shape = {1, 2, 3, 4, 5};
		double[] data = new double[119];
		
		// data should have a length == 120
		reshape(data, shape);
	}

	@Test
	public void testReshapeWithGoodInput() throws HDF5Exception
	{
		long[] shape = SAMPLE_5D_ARRAY_SHAPE;  // 5d array, 2x2x2x2x2
		double[][][][][] expected = SAMPLE_5D_ARRAY;
		double[] testInput = new double[32];

		// build the test input (a flattened version of the expected 5d array)
		for (int i = 0; i < testInput.length; i++)
		{
			testInput[i] = i * 2;
		}

		assertTrue(Arrays.deepEquals(expected, reshape(testInput, shape)));
	}

	/**
	 * Write a matrix to a file, read it from file, and compare the matrix to
	 * the original.
	 */
	@Test
	public void testWriteAndReadMatrix() throws Exception
	{
		writeMatrix(H5_FILE, "test description",
			    SAMPLE_5D_ARRAY_SHAPE, SAMPLE_5D_ARRAY, 0);
		double[][][][][] expected = SAMPLE_5D_ARRAY;
		
		assertTrue(Arrays.deepEquals(expected, readMatrix(H5_FILE)));
	}
	
	/**
	 * Write a matrix to a file (compressed), read it from file, and compare the
	 * matrix to the original.
	 */
	@Test
	public void testWriteAndReadMatrixCompressed() throws Exception
	{
		writeMatrix(H5_FILE_COMPRESSED, "test description",
			    SAMPLE_5D_ARRAY_SHAPE, SAMPLE_5D_ARRAY, 0);
		double[][][][][] expected = SAMPLE_5D_ARRAY;
		
		assertTrue(Arrays.deepEquals(expected, readMatrix(H5_FILE_COMPRESSED)));
	}

	/**
	 * Try to read a text file as HDF5 and watch it crash and burn.
	 */
	@Test(expected=HDF5LibraryException.class)
	public void testReadMatrixInvalidHDF5File() throws Exception
	{
		readMatrix(INVALID_HDF5_FILE);
	}
}