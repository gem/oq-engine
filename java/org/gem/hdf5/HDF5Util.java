package org.gem.hdf5;

import javax.swing.tree.DefaultMutableTreeNode;

import ncsa.hdf.hdf5lib.HDF5Constants;
import ncsa.hdf.object.Dataset;
import ncsa.hdf.object.Datatype;
import ncsa.hdf.object.Group;
import ncsa.hdf.object.h5.H5Datatype;
import ncsa.hdf.object.h5.H5File;

/**
 * Contains utility functions for reading and writing 5D matrices to HDF5 files.
 *
 */
public class HDF5Util
{

	/**
	 * 64-bit float data type.
	 */
	private static Datatype DOUBLE_DT = new H5Datatype(Datatype.CLASS_FLOAT, 8, Datatype.NATIVE, Datatype.NATIVE);
	private static int DEFAULT_GZIP_COMPRESSION = 0;  // No compression

	/**
	 * Write a 5D matrix to the specified file path using default compression
	 * 		(no compression).
	 * @param path Destination path for the HDF5 matrix output file.
	 * @param matrixDesc Description of the matrix
	 * @param dims An array defining the dimensions of the matrix. For example:
	 * 		an array of {10, 10, 10, 10, 5} indicates a 10x10x10x10x5 array
	 * 		(with 50000 elements).
	 * @param matrix 5D matrix to write to the file
	 * @throws Exception
	 */
	public static void writeMatrix(String path, String matrixDesc,
			long [] dims, double[][][][][] matrix) throws Exception
	{
		writeMatrix(path, matrixDesc, dims, matrix, DEFAULT_GZIP_COMPRESSION);
	}

	/**
	 * Write a 5D matrix to the specified file path.
	 * @param path Destination path for the HDF5 matrix output file.
	 * @param matrixDesc Description of the matrix
	 * @param dims An array defining the dimensions of the matrix. For example:
	 * 		an array of {10, 10, 10, 10, 5} indicates a 10x10x10x10x5 array
	 * 		(with 50000 elements).
	 * @param matrix 5D matrix to write to the file
	 * @param gzipLevel Level of gzip compression. Valid compression levels are
	 * 		1-9; use 0 or a negative value for no compression.
	 * @throws Exception
	 */
	private static void writeMatrix(String path, String matrixDesc,
			long [] dims, double[][][][][] matrix, int gzipLevel) throws Exception
	{
		H5File output = new H5File(path, HDF5Constants.H5F_ACC_RDWR);
		output.createNewFile();
		output.open();

		Group root = getRootGroup(output);

		output.createScalarDS(matrixDesc, root, DOUBLE_DT, dims, null, null, gzipLevel, matrix);

		output.close();
	}

	/**
	 * Read a 5D matrix from the specified file.
	 * @param path Path to an HDF5 file containing a 5D matrix.
	 * @return 5D double array
	 * @throws Exception
	 */
	public static double [][][][][] readMatrix(String path) throws Exception
	{
		H5File input = new H5File(path, HDF5Constants.H5F_ACC_RDONLY);

		input.open();

		Group root = getRootGroup(input);

		Dataset dataset = (Dataset) root.getMemberList().get(0);
		dataset.read();

		return readMatrix(dataset);
	}

	private static double[][][][][] readMatrix(Dataset dataset) throws OutOfMemoryError, Exception
	{
		long[] maxDims = dataset.getMaxDims();
		long[] selectedDims = dataset.getSelectedDims();

		// copy maxDims to selectedDims, then read the data
		for (int i = 0; i < maxDims.length; i++)
		{
			selectedDims[i] = maxDims[i];
		}

		// this gives us the entire matrix flattened into a 1 dimensional array
		double[] data = (double[])dataset.getData();

		return reshape(data, maxDims);
	}

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
			throw new HDF5Exception(
					"array length does not match request shape (or vice versa)");
		}

		// now reshape:
		double[][][][][] reshaped = new double[(int) shape[0]][(int) shape[1]]
				[(int) shape[2]][(int) shape[3]][(int) shape[4]];

		int arrayIndex = 0;

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
							reshaped[i][j][k][l][m] = array[arrayIndex];
							arrayIndex++;
						}
					}
				}
			}
		}
		return reshaped;
	}
}