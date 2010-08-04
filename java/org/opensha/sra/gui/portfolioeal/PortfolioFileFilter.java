package org.opensha.sra.gui.portfolioeal;

import java.io.File;

import javax.swing.filechooser.FileFilter;

/**
 * The filter for portfolio file extensions.
 * 
 * @author Jeremy Leakakos
 * 
 */
public class PortfolioFileFilter extends FileFilter {

	/**
	 * This method is the accept method overwritten from FileFilter.  It is used to filter out all
	 * but the portfolio file extensions.
	 * 
	 * @param f The file having its extension looked at.
	 * @return True if the file has the proper extension, and false if it has a wrong
	 * extension.
	 */
	@Override
	public boolean accept(File f) {
		boolean retval = false;
		if ( f.isDirectory() ) { 
			retval = true;
		}
		String extension = getExtension(f);
		
		// Change "Something" in <code>extension.equals("Something")<code> to the file type for portfolios.
		if ( extension.equals("csv") ) {
			retval = true;
		}
		return retval;
	}

	/**
	 * This method is the filter description for the JFileChooser.
	 * 
	 * @return The filter name used in the file chooser 
	 */
	@Override
	public String getDescription() {
		return "Portfolio Files (*.csv)";
	}
	
	/**
	 * This method pulls out the extension from a file.
	 * 
	 * @param f The file to find the extension of
	 * @return the file extension
	 */
	private String getExtension( File f ) {
		String[] array = f.getName().split("\\.");
		return array[array.length -1];
	}

}
