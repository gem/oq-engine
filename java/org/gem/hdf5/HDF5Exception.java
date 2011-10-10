package org.gem.hdf5;

/**
 * Basic Exception type for HDF5-related errors.
 *
 */
public class HDF5Exception extends Exception {

	public HDF5Exception(String string) {
		super(string);
	}

	public HDF5Exception(Exception e) {
		super(e);
	}

}
