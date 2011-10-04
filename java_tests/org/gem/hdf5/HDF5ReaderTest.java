package org.gem.hdf5;

import static org.junit.Assert.*;

import java.io.File;
import java.util.Arrays;

import ncsa.hdf.hdf5lib.exceptions.HDF5LibraryException;

import org.junit.Test;
import org.junit.Before;
import org.junit.After;

import static org.gem.hdf5.HDF5Reader.readMatrix;
import static org.gem.hdf5.HDF5UtilTest.SAMPLE_5D_ARRAY;
import static org.gem.hdf5.HDF5UtilTest.SAMPLE_5D_ARRAY_SHAPE;
import static org.gem.hdf5.HDF5Writer.writeMatrix;

public class HDF5ReaderTest
{

	private static final String TEST_FILE_PATH = "test_5d_array.h5";
	private static final String INVALID_HDF5_FILE =
			"java_tests/data/invalid_hdf5_file.h5";
	
	@Before
	public void setUp() throws Exception
	{
		writeMatrix(TEST_FILE_PATH, "", SAMPLE_5D_ARRAY_SHAPE, SAMPLE_5D_ARRAY, 0);
	}
	
	@After
	public void tearDown() throws Exception
	{
		File testFile = new File(TEST_FILE_PATH);
		testFile.delete();
	}
	
	@Test
	public void testReadMatrixFromFile() throws Exception
	{
		double[][][][][] expected = SAMPLE_5D_ARRAY;
		
		Arrays.deepEquals(expected, readMatrix(TEST_FILE_PATH));
	}
	
	@Test(expected=HDF5LibraryException.class)
	public void testReadMatrixInvalidHDF5File() throws Exception
	{
		readMatrix(INVALID_HDF5_FILE);
	}

}
