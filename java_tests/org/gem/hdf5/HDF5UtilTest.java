package org.gem.hdf5;

import static org.junit.Assert.*;

import java.util.Arrays;

import org.junit.Test;

import static org.gem.hdf5.HDF5Util.reshape;

public class HDF5UtilTest {
	
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
	
	

}
