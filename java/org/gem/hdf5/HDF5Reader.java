package org.gem.hdf5;

import ncsa.hdf.hdf5lib.HDF5Constants;
import ncsa.hdf.object.Dataset;
import ncsa.hdf.object.Group;
import ncsa.hdf.object.h5.H5File;

import static org.gem.hdf5.HDF5Util.getRootGroup;
import static org.gem.hdf5.HDF5Util.reshape;

public class HDF5Reader
{

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
}
