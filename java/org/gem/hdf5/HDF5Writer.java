package org.gem.hdf5;


import java.io.File;

import ncsa.hdf.hdf5lib.HDF5Constants;
import ncsa.hdf.object.Dataset;
import ncsa.hdf.object.Datatype;
import ncsa.hdf.object.Group;
import ncsa.hdf.object.h5.H5Datatype;
import ncsa.hdf.object.h5.H5File;

import static org.gem.hdf5.HDF5Util.getRootGroup;

public abstract class HDF5Writer
{
	private static Datatype DOUBLE_DT = new H5Datatype(Datatype.CLASS_FLOAT, 8, Datatype.NATIVE, Datatype.NATIVE);
	private static int DEFAULT_GZIP_COMPRESSION = 0;  // No compression
	
	/**
	 * Write a 5D matrix to the specified file path (using default compression).
	 * @param path Destination path for the HDF5 matrix output file.
	 * @param matrixLabel
	 * @param dims An array defining the dimensions of the matrix. For example:
	 * 		an array of {10, 10, 10, 10, 5} indicates a 10x10x10x10x5 array
	 * 		(with 50000 elements).
	 * @param matrix
	 * @throws Exception
	 */
	public static void writeMatrix(String path, String matrixLabel,
			long [] dims, double[][][][][] matrix) throws Exception
	{
		writeMatrix(path, matrixLabel, dims, matrix, DEFAULT_GZIP_COMPRESSION);
	}
	
	/**
	 * Write a 5D matrix to the specified file path.
	 * @param path Destination path for the HDF5 matrix output file.
	 * @param matrixLabel
	 * @param dims An array defining the dimensions of the matrix. For example:
	 * 		an array of {10, 10, 10, 10, 5} indicates a 10x10x10x10x5 array
	 * 		(with 50000 elements).
	 * @param matrix
	 * @param gzipLevel Level of gzip compression. Valid compression levels are
	 * 		1-9; use 0 or a negative value for no compression.
	 * @throws Exception
	 */
	public static void writeMatrix(String path, String matrixLabel,
			long [] dims, double[][][][][] matrix, int gzipLevel) throws Exception
	{
		H5File output = new H5File(path, HDF5Constants.H5F_ACC_RDWR);
		output.createNewFile();
		if (output.open() == -1)
		{
			throw new Exception("Unable to open file");
		}
		
		Group root = getRootGroup(output);

		output.createScalarDS(matrixLabel, root, DOUBLE_DT, dims, null, null, gzipLevel, matrix);

		output.close();
	}
}
