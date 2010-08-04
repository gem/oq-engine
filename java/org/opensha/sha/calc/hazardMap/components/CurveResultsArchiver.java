package org.opensha.sha.calc.hazardMap.components;

import java.io.File;
import java.io.IOException;

import org.opensha.commons.data.function.ArbitrarilyDiscretizedFunc;
import org.opensha.commons.metadata.XMLSaveable;

/**
 * This interface defines a mechanism for storing hazard curve results. Initially this will probably
 * just have one implementation, storing hazard curves to files. In the future, you may want to have
 * this write the values to a database
 * 
 * @author kevin
 *
 */
public interface CurveResultsArchiver extends XMLSaveable {
	
	/**
	 * This stores the curve for the given site.
	 * 
	 * @param curve - the curve itself
	 * @param meta - curve metadata
	 * @throws IOException 
	 */
	public void archiveCurve(ArbitrarilyDiscretizedFunc curve, CurveMetadata meta) throws IOException;
	
	/**
	 * Returns true if the given curve has already been calculated and archived
	 * 
	 * @param meta
	 * @param xVals
	 * @return
	 */
	public boolean isCurveCalculated(CurveMetadata meta, ArbitrarilyDiscretizedFunc xVals);
	
	/**
	 * Return the store dir if applicable (null otherwise) for this archiver.
	 * 
	 * @return
	 */
	public File getStoreDir();
}
