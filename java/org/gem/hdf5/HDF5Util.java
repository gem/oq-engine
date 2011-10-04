package org.gem.hdf5;

import javax.swing.tree.DefaultMutableTreeNode;

import ncsa.hdf.object.Group;
import ncsa.hdf.object.h5.H5File;

public class HDF5Util {

	/**
	 * Get the root Group from an HDF5 file.
	 * @param h5file An open hdf5 file handle.
	 * @return Group
	 */
	public static Group getRootGroup(H5File h5file)
	{
		return (Group)((DefaultMutableTreeNode)h5file.getRootNode()).getUserObject();
	}

	/**
	 * Reshape a 1D array into a 5D array, given specific shape/dimensions.
	 * @param array Flattened array
	 * @param shape Defines the shape of the output. For example, a shape of
	 * 		{1, 2, 3, 4, 5} defines a 1x2x3x4x5 array (containing 120
	 * 		elements).
	 * @return reshaped 5D array
	 * @throws HDF5Exception
	 */
	public static double[][][][][] reshape(double [] array, long[] shape) throws HDF5Exception
	{
		// Validity checks:
		if (shape.length != 5)
		{
			throw new HDF5Exception("invalid shape; must be 5 dimensional");
		}

		// next, validate the array length against the requested shape
		int expectedLength = 1;
		for (long s: shape)
		{
			expectedLength *= s;
		}
		
		if (expectedLength != array.length)
		{
			throw new HDF5Exception("array length does not match request shape (or vice versa)");
		}
		
		// now actually reshape:
		double[][][][][] reshaped = new double[(int) shape[0]][(int) shape[1]]
				[(int) shape[2]][(int) shape[3]][(int) shape[4]];
		
		int arrayCursor = 0;

		for (int i = 0; i < shape[0]; i++)
		{
			for (int j = 0; j < shape[1]; j++)
			{
				for (int k = 0; k < shape[2]; k++)
				{
					for (int l = 0; l < shape[3]; l++)
					{
						for (int m = 0; m < shape[4]; m++)
						{
							reshaped[i][j][k][l][m] = array[arrayCursor];
							arrayCursor++;
						}
					}
				}
			}
		}
		
		return reshaped;
	}
}
